"""
سیستم تشخیص موج‌های توییتری.

این ماژول الگوریتم‌ها و روش‌های تشخیص موج‌های توییتری را پیاده‌سازی می‌کند.
موج‌ها شامل افزایش ناگهانی حجم توییت‌ها یا تغییرات قابل توجه در احساسات هستند.
"""

import logging
import math
import json
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
import numpy as np
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import func, and_, or_, desc
import asyncio

from app.db.models import Tweet, Alert, User, Keyword, TweetKeyword

logger = logging.getLogger(__name__)


class WaveDetector:
    """
    تشخیص موج‌های توییتری

    این کلاس الگوریتم‌ها و روش‌های تشخیص موج‌های توییتری را پیاده‌سازی می‌کند.
    موج‌ها شامل افزایش ناگهانی حجم توییت‌ها یا تغییرات قابل توجه در احساسات هستند.

    Attributes:
        db_session (AsyncSession): نشست دیتابیس
        volume_threshold (float): آستانه تشخیص موج حجمی
        sentiment_threshold (float): آستانه تشخیص موج احساسی
        min_tweets (int): حداقل تعداد توییت برای تشخیص موج
        time_window (int): پنجره زمانی برای تحلیل موج به دقیقه
    """

    def __init__(
            self,
            db_session: AsyncSession,
            volume_threshold: float = 2.0,
            sentiment_threshold: float = 0.3,
            min_tweets: int = 10,
            time_window: int = 60  # دقیقه
    ):
        """
        مقداردهی اولیه تشخیص موج

        Args:
            db_session (AsyncSession): نشست دیتابیس
            volume_threshold (float): آستانه تشخیص موج حجمی (ضریب افزایش)
            sentiment_threshold (float): آستانه تشخیص موج احساسی (میزان تغییر)
            min_tweets (int): حداقل تعداد توییت برای تشخیص موج
            time_window (int): پنجره زمانی برای تحلیل موج به دقیقه
        """
        self.db_session = db_session
        self.volume_threshold = volume_threshold
        self.sentiment_threshold = sentiment_threshold
        self.min_tweets = min_tweets
        self.time_window = time_window
        logger.info("WaveDetector initialized")

    async def detect_volume_waves(
            self,
            keywords: Optional[List[str]] = None,
            hours_back: int = 24
    ) -> List[Dict[str, Any]]:
        """
        تشخیص موج‌های حجمی

        Args:
            keywords (Optional[List[str]]): کلیدواژه‌ها برای فیلتر کردن
            hours_back (int): تعداد ساعات برای بررسی

        Returns:
            List[Dict[str, Any]]: لیست موج‌های تشخیص داده شده
        """
        logger.info(f"Detecting volume waves for the past {hours_back} hours")

        # محاسبه زمان شروع و پایان
        end_time = datetime.utcnow()
        start_time = end_time - timedelta(hours=hours_back)

        # تقسیم زمان به بازه‌های time_window دقیقه‌ای
        time_windows = []
        window_start = start_time

        while window_start < end_time:
            window_end = window_start + timedelta(minutes=self.time_window)
            time_windows.append((window_start, min(window_end, end_time)))
            window_start = window_end

        # بررسی هر بازه زمانی
        volume_data = []
        prev_count = 0
        keyword_condition = None

        # ایجاد شرط کلیدواژه‌ها
        if keywords:
            # دریافت شناسه‌های کلیدواژه‌ها از دیتابیس
            stmt = select(Keyword.id).where(Keyword.text.in_(keywords))
            result = await self.db_session.execute(stmt)
            keyword_ids = [row[0] for row in result.fetchall()]

            if keyword_ids:
                # ایجاد شرط برای توییت‌هایی که با این کلیدواژه‌ها مرتبط هستند
                keyword_condition = Tweet.id.in_(
                    select(TweetKeyword.tweet_id).where(TweetKeyword.keyword_id.in_(keyword_ids))
                )

        # بررسی هر بازه زمانی
        for i, (window_start, window_end) in enumerate(time_windows):
            # شرط زمانی
            time_condition = and_(
                Tweet.created_at >= window_start,
                Tweet.created_at < window_end
            )

            # ترکیب شرط‌ها
            if keyword_condition:
                stmt_condition = and_(time_condition, keyword_condition)
            else:
                stmt_condition = time_condition

            # شمارش توییت‌ها در این بازه
            stmt = select(func.count()).where(stmt_condition)
            result = await self.db_session.execute(stmt)
            tweet_count = result.scalar() or 0

            # محاسبه نرخ تغییر
            if i > 0 and prev_count > 0:
                growth_rate = (tweet_count - prev_count) / prev_count if prev_count > 0 else 0
            else:
                growth_rate = 0

            volume_data.append({
                "start_time": window_start,
                "end_time": window_end,
                "tweet_count": tweet_count,
                "growth_rate": growth_rate
            })

            prev_count = tweet_count

        # تشخیص موج‌ها
        waves = []

        for i, data in enumerate(volume_data):
            # رد کردن بازه‌های با تعداد کم توییت
            if data["tweet_count"] < self.min_tweets:
                continue

            # بررسی افزایش ناگهانی نسبت به بازه قبلی
            if data["growth_rate"] >= self.volume_threshold:
                # دریافت توییت‌های این بازه
                time_condition = and_(
                    Tweet.created_at >= data["start_time"],
                    Tweet.created_at < data["end_time"]
                )

                if keyword_condition:
                    stmt_condition = and_(time_condition, keyword_condition)
                else:
                    stmt_condition = time_condition

                stmt = select(Tweet).where(stmt_condition).order_by(Tweet.importance_score.desc()).limit(100)
                result = await self.db_session.execute(stmt)
                tweets = result.scalars().all()

                # محاسبه اطلاعات احساسات
                sentiment_counts = {"positive": 0, "negative": 0, "neutral": 0, "mixed": 0}
                total_sentiment = 0

                for tweet in tweets:
                    sentiment_label = tweet.sentiment_label or "neutral"
                    sentiment_counts[sentiment_label] = sentiment_counts.get(sentiment_label, 0) + 1

                    # محاسبه میانگین احساسات
                    if tweet.sentiment_score is not None:
                        total_sentiment += tweet.sentiment_score

                # محاسبه متوسط احساسات
                avg_sentiment = total_sentiment / len(tweets) if tweets else 0

                # محاسبه توزیع احساسات
                total_tweets = sum(sentiment_counts.values())
                sentiment_distribution = {
                    label: count / total_tweets for label, count in sentiment_counts.items() if total_tweets > 0
                }

                # محاسبه امتیاز اهمیت موج
                importance_score = min(10, data["growth_rate"] * 2.5 + (data["tweet_count"] / 10))

                wave = {
                    "type": "volume",
                    "start_time": data["start_time"].isoformat(),
                    "end_time": data["end_time"].isoformat(),
                    "tweet_count": data["tweet_count"],
                    "growth_rate": data["growth_rate"],
                    "avg_sentiment": avg_sentiment,
                    "sentiment_distribution": sentiment_distribution,
                    "importance_score": importance_score,
                    "top_tweets": [
                        {
                            "id": tweet.id,
                            "tweet_id": tweet.tweet_id,
                            "content": tweet.content,
                            "user_id": tweet.user_id,
                            "importance_score": tweet.importance_score,
                            "sentiment_label": tweet.sentiment_label
                        }
                        for tweet in tweets[:20]  # فقط 20 توییت مهم
                    ]
                }

                # بررسی کلیدواژه‌های مرتبط
                if keywords:
                    wave["related_keywords"] = keywords

                waves.append(wave)

        logger.info(f"Detected {len(waves)} volume waves")
        return waves

    async def detect_sentiment_waves(
            self,
            keywords: Optional[List[str]] = None,
            hours_back: int = 24
    ) -> List[Dict[str, Any]]:
        """
        تشخیص موج‌های احساسی

        Args:
            keywords (Optional[List[str]]): کلیدواژه‌ها برای فیلتر کردن
            hours_back (int): تعداد ساعات برای بررسی

        Returns:
            List[Dict[str, Any]]: لیست موج‌های تشخیص داده شده
        """
        logger.info(f"Detecting sentiment waves for the past {hours_back} hours")

        # محاسبه زمان شروع و پایان
        end_time = datetime.utcnow()
        start_time = end_time - timedelta(hours=hours_back)

        # تقسیم زمان به بازه‌های time_window دقیقه‌ای
        time_windows = []
        window_start = start_time

        while window_start < end_time:
            window_end = window_start + timedelta(minutes=self.time_window)
            time_windows.append((window_start, min(window_end, end_time)))
            window_start = window_end

        # بررسی هر بازه زمانی
        sentiment_data = []
        prev_avg_sentiment = 0
        keyword_condition = None

        # ایجاد شرط کلیدواژه‌ها
        if keywords:
            # دریافت شناسه‌های کلیدواژه‌ها از دیتابیس
            stmt = select(Keyword.id).where(Keyword.text.in_(keywords))
            result = await self.db_session.execute(stmt)
            keyword_ids = [row[0] for row in result.fetchall()]

            if keyword_ids:
                # ایجاد شرط برای توییت‌هایی که با این کلیدواژه‌ها مرتبط هستند
                keyword_condition = Tweet.id.in_(
                    select(TweetKeyword.tweet_id).where(TweetKeyword.keyword_id.in_(keyword_ids))
                )

        # بررسی هر بازه زمانی
        for i, (window_start, window_end) in enumerate(time_windows):
            # شرط زمانی
            time_condition = and_(
                Tweet.created_at >= window_start,
                Tweet.created_at < window_end,
                Tweet.sentiment_score.isnot(None)  # فقط توییت‌هایی که امتیاز احساسات دارند
            )

            # ترکیب شرط‌ها
            if keyword_condition:
                stmt_condition = and_(time_condition, keyword_condition)
            else:
                stmt_condition = time_condition

            # شمارش توییت‌ها و میانگین احساسات در این بازه
            stmt = select(
                func.count(),
                func.avg(Tweet.sentiment_score)
            ).where(stmt_condition)

            result = await self.db_session.execute(stmt)
            row = result.fetchone()
            tweet_count = row[0] or 0
            avg_sentiment = row[1] or 0

            # محاسبه تغییر احساسات
            sentiment_shift = abs(avg_sentiment - prev_avg_sentiment) if i > 0 else 0

            sentiment_data.append({
                "start_time": window_start,
                "end_time": window_end,
                "tweet_count": tweet_count,
                "avg_sentiment": avg_sentiment,
                "sentiment_shift": sentiment_shift
            })

            prev_avg_sentiment = avg_sentiment

        # تشخیص موج‌ها
        waves = []

        for i, data in enumerate(sentiment_data):
            # رد کردن بازه‌های با تعداد کم توییت
            if data["tweet_count"] < self.min_tweets:
                continue

            # بررسی تغییر ناگهانی احساسات
            if data["sentiment_shift"] >= self.sentiment_threshold:
                # دریافت توییت‌های این بازه
                time_condition = and_(
                    Tweet.created_at >= data["start_time"],
                    Tweet.created_at < data["end_time"]
                )

                if keyword_condition:
                    stmt_condition = and_(time_condition, keyword_condition)
                else:
                    stmt_condition = time_condition

                stmt = select(Tweet).where(stmt_condition).order_by(Tweet.importance_score.desc()).limit(100)
                result = await self.db_session.execute(stmt)
                tweets = result.scalars().all()

                # محاسبه اطلاعات احساسات
                sentiment_counts = {"positive": 0, "negative": 0, "neutral": 0, "mixed": 0}

                for tweet in tweets:
                    sentiment_label = tweet.sentiment_label or "neutral"
                    sentiment_counts[sentiment_label] = sentiment_counts.get(sentiment_label, 0) + 1

                # محاسبه توزیع احساسات
                total_tweets = sum(sentiment_counts.values())
                sentiment_distribution = {
                    label: count / total_tweets for label, count in sentiment_counts.items() if total_tweets > 0
                }

                # محاسبه امتیاز اهمیت موج
                importance_score = min(10, data["sentiment_shift"] * 10 + (data["tweet_count"] / 20))

                wave = {
                    "type": "sentiment",
                    "start_time": data["start_time"].isoformat(),
                    "end_time": data["end_time"].isoformat(),
                    "tweet_count": data["tweet_count"],
                    "avg_sentiment": data["avg_sentiment"],
                    "sentiment_shift": data["sentiment_shift"],
                    "sentiment_distribution": sentiment_distribution,
                    "importance_score": importance_score,
                    "top_tweets": [
                        {
                            "id": tweet.id,
                            "tweet_id": tweet.tweet_id,
                            "content": tweet.content,
                            "user_id": tweet.user_id,
                            "importance_score": tweet.importance_score,
                            "sentiment_label": tweet.sentiment_label
                        }
                        for tweet in tweets[:20]  # فقط 20 توییت مهم
                    ]
                }

                # بررسی کلیدواژه‌های مرتبط
                if keywords:
                    wave["related_keywords"] = keywords

                waves.append(wave)

        logger.info(f"Detected {len(waves)} sentiment waves")
        return waves

    async def detect_all_waves(
            self,
            keywords: Optional[List[str]] = None,
            hours_back: int = 24
    ) -> List[Dict[str, Any]]:
        """
        تشخیص تمام انواع موج‌ها

        Args:
            keywords (Optional[List[str]]): کلیدواژه‌ها برای فیلتر کردن
            hours_back (int): تعداد ساعات برای بررسی

        Returns:
            List[Dict[str, Any]]: لیست تمام موج‌های تشخیص داده شده
        """
        # تشخیص موج‌های حجمی و احساسی
        volume_waves = await self.detect_volume_waves(keywords, hours_back)
        sentiment_waves = await self.detect_sentiment_waves(keywords, hours_back)

        # ترکیب نتایج
        all_waves = volume_waves + sentiment_waves

        # مرتب‌سازی براساس امتیاز اهمیت
        all_waves.sort(key=lambda x: x.get("importance_score", 0), reverse=True)

        logger.info(f"Detected {len(all_waves)} total waves")
        return all_waves

    async def create_alert_for_wave(self, wave: Dict[str, Any]) -> Optional[Alert]:
        """
        ایجاد هشدار برای موج

        Args:
            wave (Dict[str, Any]): اطلاعات موج

        Returns:
            Optional[Alert]: هشدار ایجاد شده
        """
        # تعیین نوع و شدت هشدار
        wave_type = wave.get("type", "unknown")
        importance_score = wave.get("importance_score", 0)

        # تعیین شدت هشدار
        if importance_score >= 7:
            severity = "high"
        elif importance_score >= 4:
            severity = "medium"
        else:
            severity = "low"

        # ساخت عنوان هشدار
        if wave_type == "volume":
            alert_type = "volume_wave"
            title = f"افزایش ناگهانی حجم توییت‌ها ({wave.get('tweet_count', 0)})"

            # بررسی کلیدواژه‌های مرتبط
            if "related_keywords" in wave and wave["related_keywords"]:
                title += f" مرتبط با {', '.join(wave['related_keywords'][:3])}"

        elif wave_type == "sentiment":
            alert_type = "sentiment_shift"

            sentiment_value = wave.get("avg_sentiment", 0)
            sentiment_description = "مثبت" if sentiment_value > 0 else "منفی"

            title = f"تغییر ناگهانی احساسات به سمت {sentiment_description}"

            # بررسی کلیدواژه‌های مرتبط
            if "related_keywords" in wave and wave["related_keywords"]:
                title += f" مرتبط با {', '.join(wave['related_keywords'][:3])}"
        else:
            alert_type = "unknown_wave"
            title = "موج ناشناخته توییتری"

        # ساخت پیام هشدار
        message = f"یک موج توییتری از نوع '{wave_type}' شناسایی شده است.\n"
        message += f"زمان شروع: {wave.get('start_time')}\n"
        message += f"زمان پایان: {wave.get('end_time')}\n"
        message += f"تعداد توییت‌ها: {wave.get('tweet_count')}\n"

        if wave_type == "volume":
            message += f"نرخ رشد: {wave.get('growth_rate', 0):.2f}\n"
        elif wave_type == "sentiment":
            message += f"میزان تغییر احساسات: {wave.get('sentiment_shift', 0):.2f}\n"
            message += f"متوسط احساسات: {wave.get('avg_sentiment', 0):.2f}\n"

        message += f"امتیاز اهمیت: {importance_score:.2f}/10\n"

        # افزودن کلیدواژه‌های مرتبط
        if "related_keywords" in wave and wave["related_keywords"]:
            message += f"کلیدواژه‌های مرتبط: {', '.join(wave['related_keywords'])}\n"

        # افزودن توزیع احساسات
        if "sentiment_distribution" in wave:
            message += "\nتوزیع احساسات:\n"
            for label, value in wave["sentiment_distribution"].items():
                message += f"- {label}: {value:.1%}\n"

        # یافتن یک توییت مرتبط برای نمایش
        related_tweet_id = None
        if "top_tweets" in wave and wave["top_tweets"]:
            related_tweet_id = wave["top_tweets"][0].get("id")

        # ذخیره اطلاعات اضافی در data
        data = {
            "wave_type": wave_type,
            "importance_score": importance_score,
            "tweet_count": wave.get("tweet_count"),
            "start_time": wave.get("start_time"),
            "end_time": wave.get("end_time"),
            "top_tweets": wave.get("top_tweets", [])[:10],  # حداکثر 10 توییت مهم
            "sentiment_distribution": wave.get("sentiment_distribution", {})
        }

        # ایجاد هشدار
        alert = Alert(
            title=title,
            message=message,
            severity=severity,
            alert_type=alert_type,
            related_tweet_id=related_tweet_id,
            data=data,
            is_read=False,
            created_at=datetime.utcnow()
        )

        self.db_session.add(alert)
        await self.db_session.commit()

        logger.info(f"Created alert for {wave_type} wave: {title}")
        return alert

    async def run_detection_and_create_alerts(
            self,
            keywords: Optional[List[str]] = None,
            hours_back: int = 6,
            min_importance: float = 3.0
    ) -> List[Dict[str, Any]]:
        """
        اجرای تشخیص و ایجاد هشدار برای موج‌های مهم

        Args:
            keywords (Optional[List[str]]): کلیدواژه‌ها برای فیلتر کردن
            hours_back (int): تعداد ساعات برای بررسی
            min_importance (float): حداقل امتیاز اهمیت برای ایجاد هشدار

        Returns:
            List[Dict[str, Any]]: لیست هشدارهای ایجاد شده
        """
        # تشخیص تمام موج‌ها
        all_waves = await self.detect_all_waves(keywords, hours_back)

        # ایجاد هشدار برای موج‌های مهم
        alerts = []

        for wave in all_waves:
            # بررسی امتیاز اهمیت
            if wave.get("importance_score", 0) >= min_importance:
                alert = await self.create_alert_for_wave(wave)
                if alert:
                    alerts.append({
                        "id": alert.id,
                        "title": alert.title,
                        "severity": alert.severity,
                        "alert_type": alert.alert_type,
                        "created_at": alert.created_at.isoformat()
                    })

        logger.info(f"Created {len(alerts)} alerts from {len(all_waves)} detected waves")
        return alerts