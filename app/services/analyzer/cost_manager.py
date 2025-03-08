"""
مدیریت هزینه API‌ها.

این ماژول عملیات مدیریت هزینه API‌های Claude و Twitter را فراهم می‌کند و
سیستم‌های انتخاب بهینه مدل و تخصیص بودجه را پیاده‌سازی می‌کند.
"""

import logging
import json
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
from enum import Enum
import asyncio
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import func, insert, update

from app.config import settings
from app.db.models import ApiUsage, Tweet

logger = logging.getLogger(__name__)

class ApiType(str, Enum):
    """انواع API‌های مورد استفاده"""
    CLAUDE = "claude"
    TWITTER = "twitter"


class ClaudeModel(str, Enum):
    """مدل‌های Claude API"""
    OPUS = "claude-3-opus-20240229"
    SONNET_3_7 = "claude-3-7-sonnet-20250219"
    SONNET_3_5 = "claude-3-5-sonnet-20241022"
    HAIKU = "claude-3-5-haiku-20241022"


class AnalysisType(str, Enum):
    """انواع تحلیل‌ها"""
    SENTIMENT = "sentiment"
    TOPICS = "topics"
    WAVE = "wave"
    BATCH = "batch"
    FULL = "full"


class CostManager:
    """
    مدیریت هزینه API‌ها

    این کلاس عملیات مدیریت هزینه API‌های Claude و Twitter را فراهم می‌کند و
    سیستم‌های انتخاب بهینه مدل و تخصیص بودجه را پیاده‌سازی می‌کند.

    Attributes:
        db_session (AsyncSession): نشست دیتابیس
        daily_budget (float): بودجه روزانه به دلار
        current_usage (Dict[str, float]): هزینه فعلی به تفکیک API
        model_prices (Dict[str, Dict[str, float]]): قیمت‌های مدل‌های مختلف
        token_estimation (Dict[str, Dict[str, Tuple[int, int]]]): تخمین تعداد توکن برای عملیات مختلف
    """

    def __init__(self, db_session: AsyncSession, daily_budget: float = None):
        """
        مقداردهی اولیه مدیریت هزینه

        Args:
            db_session (AsyncSession): نشست دیتابیس
            daily_budget (float, optional): بودجه روزانه به دلار. اگر مشخص نشود، از تنظیمات استفاده می‌شود.
        """
        self.db_session = db_session
        self.daily_budget = daily_budget or settings.DAILY_BUDGET
        self.current_usage = {
            ApiType.CLAUDE: 0.0,
            ApiType.TWITTER: 0.0
        }

        # قیمت‌های مدل‌های مختلف (دلار بر میلیون توکن)
        # قیمت‌ها براساس مستندات Anthropic در تاریخ مارس 2025
        self.model_prices = {
            ClaudeModel.OPUS: {
                "input": 15.0,  # $15 / MTok
                "output": 75.0   # $75 / MTok
            },
            ClaudeModel.SONNET_3_7: {
                "input": 3.0,   # $3 / MTok
                "output": 15.0   # $15 / MTok
            },
            ClaudeModel.SONNET_3_5: {
                "input": 3.0,   # $3 / MTok
                "output": 15.0   # $15 / MTok
            },
            ClaudeModel.HAIKU: {
                "input": 0.8,   # $0.8 / MTok
                "output": 4.0    # $4 / MTok
            }
        }

        # تخمین تعداد توکن برای عملیات مختلف (توکن ورودی، توکن خروجی)
        self.token_estimation = {
            AnalysisType.SENTIMENT: {
                "single": (400, 200),
                "batch_per_item": (100, 150)
            },
            AnalysisType.TOPICS: {
                "single": (500, 400),
                "batch_per_item": (150, 200)
            },
            AnalysisType.WAVE: {
                "base": (2000, 1000),
                "per_tweet": (50, 0),
                "with_thinking": (2000, 5000)
            },
            AnalysisType.FULL: {
                "single": (800, 600),
                "batch_per_item": (200, 300)
            }
        }

        logger.info(f"CostManager initialized with daily budget: ${self.daily_budget}")

    async def initialize(self) -> None:
        """
        مقداردهی اولیه و بارگذاری آمار فعلی از دیتابیس
        """
        # بارگذاری آمار امروز
        today = datetime.now().date()
        today_start = datetime.combine(today, datetime.min.time())
        today_end = datetime.combine(today, datetime.max.time())

        # بارگذاری هزینه امروز برای Claude
        stmt = select(func.sum(ApiUsage.cost)).where(
            ApiUsage.api_type == ApiType.CLAUDE,
            ApiUsage.date >= today_start,
            ApiUsage.date <= today_end
        )
        result = await self.db_session.execute(stmt)
        claude_cost = result.scalar() or 0.0

        # بارگذاری هزینه امروز برای Twitter
        stmt = select(func.sum(ApiUsage.cost)).where(
            ApiUsage.api_type == ApiType.TWITTER,
            ApiUsage.date >= today_start,
            ApiUsage.date <= today_end
        )
        result = await self.db_session.execute(stmt)
        twitter_cost = result.scalar() or 0.0

        self.current_usage = {
            ApiType.CLAUDE: claude_cost,
            ApiType.TWITTER: twitter_cost
        }

        logger.info(f"Current API usage loaded: Claude=${claude_cost:.2f}, Twitter=${twitter_cost:.2f}")

    async def record_usage(
        self,
        api_type: str,
        operation: str,
        tokens_in: int = 0,
        tokens_out: int = 0,
        item_count: int = 0,
        cost: float = None
    ) -> None:
        """
        ثبت استفاده از API

        Args:
            api_type (str): نوع API
            operation (str): نوع عملیات
            tokens_in (int): تعداد توکن‌های ورودی
            tokens_out (int): تعداد توکن‌های خروجی
            item_count (int): تعداد آیتم‌ها
            cost (float, optional): هزینه تخمینی. اگر مشخص نشود، محاسبه می‌شود.
        """
        # محاسبه هزینه اگر مشخص نشده باشد
        if cost is None:
            if api_type == ApiType.CLAUDE:
                # محاسبه هزینه براساس تعداد توکن و مدل پیش‌فرض
                model = settings.CLAUDE_MODEL
                model_price = self.model_prices.get(model, self.model_prices[ClaudeModel.SONNET_3_7])
                cost = (tokens_in * model_price["input"] + tokens_out * model_price["output"]) / 1_000_000
            elif api_type == ApiType.TWITTER:
                # هزینه تخمینی براساس تعداد آیتم‌ها
                cost = item_count * 0.0002  # تقریباً $0.2 برای هر 1000 آیتم

        # ثبت استفاده در دیتابیس
        usage = ApiUsage(
            date=datetime.now(),
            api_type=api_type,
            operation=operation,
            tokens_in=tokens_in,
            tokens_out=tokens_out,
            item_count=item_count,
            cost=cost
        )

        self.db_session.add(usage)
        await self.db_session.commit()

        # به‌روزرسانی هزینه فعلی
        self.current_usage[api_type] += cost

        logger.info(f"Recorded {api_type} API usage: operation={operation}, cost=${cost:.6f}")

    async def get_daily_usage(self, days: int = 7) -> Dict[str, List[Dict[str, Any]]]:
        """
        دریافت آمار استفاده روزانه

        Args:
            days (int): تعداد روزهای اخیر

        Returns:
            Dict[str, List[Dict[str, Any]]]: آمار استفاده روزانه به تفکیک API
        """
        # محاسبه تاریخ شروع
        start_date = datetime.now() - timedelta(days=days)

        # دریافت آمار Claude
        stmt = select(
            func.date(ApiUsage.date),
            func.sum(ApiUsage.cost),
            func.sum(ApiUsage.tokens_in),
            func.sum(ApiUsage.tokens_out)
        ).where(
            ApiUsage.api_type == ApiType.CLAUDE,
            ApiUsage.date >= start_date
        ).group_by(
            func.date(ApiUsage.date)
        ).order_by(
            func.date(ApiUsage.date)
        )

        result = await self.db_session.execute(stmt)
        claude_usage = [
            {
                "date": date.strftime("%Y-%m-%d"),
                "cost": float(cost),
                "tokens_in": int(tokens_in),
                "tokens_out": int(tokens_out)
            }
            for date, cost, tokens_in, tokens_out in result.fetchall()
        ]

        # دریافت آمار Twitter
        stmt = select(
            func.date(ApiUsage.date),
            func.sum(ApiUsage.cost),
            func.sum(ApiUsage.item_count)
        ).where(
            ApiUsage.api_type == ApiType.TWITTER,
            ApiUsage.date >= start_date
        ).group_by(
            func.date(ApiUsage.date)
        ).order_by(
            func.date(ApiUsage.date)
        )

        result = await self.db_session.execute(stmt)
        twitter_usage = [
            {
                "date": date.strftime("%Y-%m-%d"),
                "cost": float(cost),
                "item_count": int(item_count)
            }
            for date, cost, item_count in result.fetchall()
        ]

        return {
            "claude": claude_usage,
            "twitter": twitter_usage
        }

    async def check_budget(self) -> Dict[str, Any]:
        """
        بررسی وضعیت بودجه

        Returns:
            Dict[str, Any]: وضعیت بودجه
        """
        total_usage = sum(self.current_usage.values())
        remaining = self.daily_budget - total_usage
        percentage_used = (total_usage / self.daily_budget) * 100 if self.daily_budget > 0 else 100

        is_exhausted = total_usage >= self.daily_budget

        logger.info(f"Budget status: ${total_usage:.2f}/{self.daily_budget:.2f} ({percentage_used:.1f}%)")

        return {
            "total_budget": self.daily_budget,
            "total_usage": total_usage,
            "claude_usage": self.current_usage[ApiType.CLAUDE],
            "twitter_usage": self.current_usage[ApiType.TWITTER],
            "remaining": remaining,
            "percentage_used": percentage_used,
            "is_exhausted": is_exhausted
        }

    def select_optimal_model(
        self,
        analysis_type: str,
        text_length: int,
        is_batch: bool = False,
        items_count: int = 1,
        is_important: bool = False
    ) -> Tuple[str, Dict[str, Any]]:
        """
        انتخاب بهینه مدل Claude برای تحلیل

        Args:
            analysis_type (str): نوع تحلیل
            text_length (int): طول متن
            is_batch (bool): آیا تحلیل دسته‌ای است؟
            items_count (int): تعداد آیتم‌ها در تحلیل دسته‌ای
            is_important (bool): آیا این تحلیل اهمیت بالایی دارد؟

        Returns:
            Tuple[str, Dict[str, Any]]: مدل بهینه و اطلاعات تخمین هزینه
        """
        # تنظیم ضرایب براساس طول متن
        length_factor = 1.0
        if text_length > 10000:
            length_factor = 3.0
        elif text_length > 5000:
            length_factor = 2.0
        elif text_length > 1000:
            length_factor = 1.5

        # محاسبه تعداد توکن تخمینی
        tokens_in, tokens_out = 0, 0

        if analysis_type == AnalysisType.WAVE:
            # برای تحلیل موج، محاسبه براساس تعداد توییت‌ها
            base_in, base_out = self.token_estimation[AnalysisType.WAVE]["base"]
            tweet_tokens = self.token_estimation[AnalysisType.WAVE]["per_tweet"][0]
            thinking_out = self.token_estimation[AnalysisType.WAVE]["with_thinking"][1]

            tokens_in = base_in + (items_count * tweet_tokens)
            tokens_out = base_out

            # اگر از Extended Thinking استفاده می‌شود، توکن خروجی بیشتر است
            tokens_out += thinking_out

        elif is_batch:
            # برای تحلیل دسته‌ای، محاسبه براساس تعداد آیتم‌ها
            per_item_in, per_item_out = self.token_estimation.get(
                analysis_type, self.token_estimation[AnalysisType.SENTIMENT]
            )["batch_per_item"]

            tokens_in = per_item_in * items_count
            tokens_out = per_item_out * items_count

        else:
            # برای تحلیل تکی
            tokens_in, tokens_out = self.token_estimation.get(
                analysis_type, self.token_estimation[AnalysisType.SENTIMENT]
            )["single"]

        # اعمال ضریب طول متن
        tokens_in = int(tokens_in * length_factor)
        tokens_out = int(tokens_out * length_factor)

        # بررسی وضعیت بودجه
        total_usage = sum(self.current_usage.values())
        budget_factor = 1.0 - min(1.0, total_usage / self.daily_budget)

        # انتخاب مدل
        selected_model = None
        model_reason = ""

        if analysis_type == AnalysisType.WAVE or is_important:
            # برای تحلیل موج یا موارد مهم، همیشه از بهترین مدل استفاده می‌شود
            selected_model = ClaudeModel.SONNET_3_7
            model_reason = "تحلیل مهم یا موج"

        elif budget_factor < 0.2:
            # اگر بودجه کم است، از مدل ارزان‌تر استفاده می‌شود
            selected_model = ClaudeModel.HAIKU
            model_reason = "صرفه‌جویی در بودجه"

        elif text_length > 5000 or is_batch and items_count > 10:
            # برای متون طولانی یا دسته‌های بزرگ
            selected_model = ClaudeModel.SONNET_3_7
            model_reason = "متن طولانی یا دسته بزرگ"

        else:
            # برای موارد معمولی
            selected_model = ClaudeModel.SONNET_3_5
            model_reason = "تحلیل معمولی"

        # محاسبه هزینه تخمینی
        model_price = self.model_prices.get(selected_model)
        estimated_cost = (tokens_in * model_price["input"] + tokens_out * model_price["output"]) / 1_000_000

        logger.debug(
            f"Selected model {selected_model} for {analysis_type} analysis "
            f"(reason: {model_reason}, estimated cost: ${estimated_cost:.6f})"
        )

        return selected_model, {
            "tokens_in": tokens_in,
            "tokens_out": tokens_out,
            "estimated_cost": estimated_cost,
            "model": selected_model,
            "reason": model_reason
        }

    async def update_daily_budget(self, new_budget: float) -> Dict[str, Any]:
        """
        به‌روزرسانی بودجه روزانه

        Args:
            new_budget (float): بودجه روزانه جدید

        Returns:
            Dict[str, Any]: وضعیت جدید بودجه
        """
        self.daily_budget = max(0.01, new_budget)  # حداقل 1 سنت

        # ذخیره تنظیمات جدید (می‌تواند به مقدار settings در برنامه منتقل شود)
        settings.DAILY_BUDGET = self.daily_budget

        logger.info(f"Daily budget updated to: ${self.daily_budget}")

        # برگرداندن وضعیت فعلی
        return await self.check_budget()