"""
اندپوینت‌های تنظیمات سیستم.

این ماژول اندپوینت‌های مربوط به تنظیمات سیستم را فراهم می‌کند.
"""

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Dict, Any, Optional

from app.db.session import get_db
from app.db.models import AppUser
from app.core.security import get_current_user, get_current_superuser
from app.schemas.settings import SystemSettings, ApiUsageResponse
from app.services.analyzer.cost_manager import CostManager, ApiType
from app.config import settings as app_settings

router = APIRouter(prefix="/settings", tags=["settings"])


async def get_cost_manager(db: AsyncSession = Depends(get_db)) -> CostManager:
    """
    وابستگی برای دریافت یک نمونه از CostManager.

    Args:
        db (AsyncSession): نشست دیتابیس

    Returns:
        CostManager: یک نمونه از CostManager
    """
    cost_manager = CostManager(db)
    await cost_manager.initialize()
    return cost_manager


@router.get("/", response_model=SystemSettings)
async def get_settings(current_user: AppUser = Depends(get_current_user)):
    """
    دریافت تنظیمات سیستم.

    Args:
        current_user (AppUser): کاربر فعلی

    Returns:
        SystemSettings: تنظیمات سیستم
    """
    # بازیابی تنظیمات از app_settings
    settings = SystemSettings(
        project_name=app_settings.PROJECT_NAME,
        debug=app_settings.DEBUG,
        daily_budget=app_settings.DAILY_BUDGET,
        analyzer_batch_size=app_settings.ANALYZER_BATCH_SIZE,
        twitter_api_base_url=app_settings.TWITTER_API_BASE_URL,
        claude_model=app_settings.CLAUDE_MODEL
    )

    return settings


@router.put("/", response_model=SystemSettings)
async def update_settings(
        settings_update: SystemSettings,
        db: AsyncSession = Depends(get_db),
        current_user: AppUser = Depends(get_current_superuser)
):
    """
    به‌روزرسانی تنظیمات سیستم.

    Args:
        settings_update (SystemSettings): تنظیمات جدید
        db (AsyncSession): نشست دیتابیس
        current_user (AppUser): کاربر فعلی (باید مدیر سیستم باشد)

    Returns:
        SystemSettings: تنظیمات به‌روزرسانی شده
    """
    # به‌روزرسانی تنظیمات در app_settings
    app_settings.PROJECT_NAME = settings_update.project_name
    app_settings.DEBUG = settings_update.debug
    app_settings.DAILY_BUDGET = settings_update.daily_budget
    app_settings.ANALYZER_BATCH_SIZE = settings_update.analyzer_batch_size
    app_settings.TWITTER_API_BASE_URL = settings_update.twitter_api_base_url
    app_settings.CLAUDE_MODEL = settings_update.claude_model

    # توجه: در یک محیط واقعی، این تنظیمات باید در یک مکان دائمی ذخیره شوند
    # (مانند فایل تنظیمات یا دیتابیس)

    return settings_update


@router.get("/budget", response_model=Dict[str, Any])
async def get_budget_status(
        db: AsyncSession = Depends(get_db),
        current_user: AppUser = Depends(get_current_user),
        cost_manager: CostManager = Depends(get_cost_manager)
):
    """
    دریافت وضعیت بودجه API.

    Args:
        db (AsyncSession): نشست دیتابیس
        current_user (AppUser): کاربر فعلی
        cost_manager (CostManager): مدیریت هزینه

    Returns:
        Dict[str, Any]: وضعیت بودجه
    """
    # بررسی وضعیت بودجه
    budget_status = await cost_manager.check_budget()

    return budget_status


@router.put("/budget", response_model=Dict[str, Any])
async def update_budget(
        daily_budget: float,
        db: AsyncSession = Depends(get_db),
        current_user: AppUser = Depends(get_current_superuser),
        cost_manager: CostManager = Depends(get_cost_manager)
):
    """
    به‌روزرسانی بودجه روزانه API.

    Args:
        daily_budget (float): بودجه روزانه جدید
        db (AsyncSession): نشست دیتابیس
        current_user (AppUser): کاربر فعلی (باید مدیر سیستم باشد)
        cost_manager (CostManager): مدیریت هزینه

    Returns:
        Dict[str, Any]: وضعیت بودجه
    """
    # اعتبارسنجی مقدار بودجه
    if daily_budget <= 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="بودجه روزانه باید مقداری مثبت باشد",
        )

    # به‌روزرسانی بودجه
    budget_status = await cost_manager.update_daily_budget(daily_budget)

    return budget_status


@router.get("/api-usage", response_model=ApiUsageResponse)
async def get_api_usage(
        days: int = 7,
        db: AsyncSession = Depends(get_db),
        current_user: AppUser = Depends(get_current_superuser),
        cost_manager: CostManager = Depends(get_cost_manager)
):
    """
    دریافت آمار استفاده از API.

    Args:
        days (int): تعداد روزهای اخیر
        db (AsyncSession): نشست دیتابیس
        current_user (AppUser): کاربر فعلی (باید مدیر سیستم باشد)
        cost_manager (CostManager): مدیریت هزینه

    Returns:
        ApiUsageResponse: آمار استفاده از API
    """
    # دریافت آمار استفاده روزانه
    daily_usage = await cost_manager.get_daily_usage(days)

    # محاسبه مجموع هزینه‌ها
    total_claude_cost = sum(item.get("cost", 0) for item in daily_usage.get("claude", []))
    total_twitter_cost = sum(item.get("cost", 0) for item in daily_usage.get("twitter", []))

    return ApiUsageResponse(
        daily_usage=daily_usage,
        total_cost={
            "claude": total_claude_cost,
            "twitter": total_twitter_cost,
            "total": total_claude_cost + total_twitter_cost
        },
        period_days=days
    )