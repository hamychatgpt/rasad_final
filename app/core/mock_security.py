"""
سیستم احراز هویت موقت برای حالت تست.

این ماژول یک سیستم احراز هویت تقلبی برای مراحل توسعه فراهم می‌کند
که همیشه یک کاربر ادمین احراز هویت شده برمی‌گرداند.
"""

from typing import Optional
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.db.session import get_db
from app.db.models import AppUser

# کاربر فرضی برای استفاده در حالت بدون احراز هویت
MOCK_USER = AppUser(
    id=1,
    email="admin@example.com",
    hashed_password="hashed_password",
    full_name="Admin User",
    is_active=True,
    is_superuser=True
)

async def get_mock_current_user(db: AsyncSession = Depends(get_db)) -> AppUser:
    """
    وابستگی جایگزین برای حالت بدون احراز هویت.
    این تابع همیشه یک کاربر ادمین احراز هویت شده برمی‌گرداند.

    Args:
        db (AsyncSession): نشست دیتابیس (استفاده نمی‌شود)

    Returns:
        AppUser: کاربر فرضی احراز هویت شده
    """
    return MOCK_USER

# این تابع نیز همیشه همان کاربر ادمین را برمی‌گرداند
async def get_mock_current_superuser(current_user: AppUser = Depends(get_mock_current_user)) -> AppUser:
    """
    وابستگی جایگزین برای حالت بدون احراز هویت با دسترسی سوپریوزر.

    Args:
        current_user (AppUser): کاربر فعلی (از get_mock_current_user دریافت می‌شود)

    Returns:
        AppUser: کاربر فرضی با دسترسی سوپریوزر
    """
    return current_user