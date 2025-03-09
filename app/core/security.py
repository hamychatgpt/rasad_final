"""
سیستم امنیت و احراز هویت.

این ماژول توابع و کلاس‌های مربوط به امنیت و احراز هویت را پیاده‌سازی می‌کند.
"""

import jwt
from jwt.exceptions import InvalidTokenError
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from passlib.context import CryptContext
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, Union
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.config import settings
from app.db.session import get_db
from app.db.models import AppUser

# ایجاد نمونه OAuth2PasswordBearer برای استخراج توکن از هدر Authorization
oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl=f"{settings.API_V1_STR}/auth/login",
    auto_error=False  # عدم ایجاد خطای خودکار
)

# ایجاد نمونه CryptContext برای هش کردن و بررسی رمزهای عبور
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    بررسی صحت رمز عبور.

    Args:
        plain_password (str): رمز عبور ساده
        hashed_password (str): رمز عبور هش شده

    Returns:
        bool: نتیجه بررسی
    """
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """
    هش کردن رمز عبور.

    Args:
        password (str): رمز عبور ساده

    Returns:
        str: رمز عبور هش شده
    """
    return pwd_context.hash(password)


def create_access_token(
        data: Dict[str, Any],
        expires_delta: Optional[timedelta] = None
) -> str:
    """
    ایجاد توکن دسترسی JWT.

    Args:
        data (Dict[str, Any]): داده‌های توکن
        expires_delta (Optional[timedelta]): مدت زمان اعتبار توکن

    Returns:
        str: توکن JWT
    """
    to_encode = data.copy()

    # تعیین زمان انقضا
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)

    # افزودن زمان انقضا به داده‌های توکن
    to_encode.update({"exp": expire})

    # رمزنگاری توکن
    encoded_jwt = jwt.encode(
        to_encode,
        settings.SECRET_KEY,
        algorithm="HS256"
    )

    return encoded_jwt


def get_token_data(token: str) -> Dict[str, Any]:
    """
    استخراج داده‌های توکن JWT.

    Args:
        token (str): توکن JWT

    Returns:
        Dict[str, Any]: داده‌های توکن

    Raises:
        HTTPException: در صورت نامعتبر بودن توکن
    """
    try:
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=["HS256"]
        )
        return payload
    except InvalidTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="توکن نامعتبر است",
            headers={"WWW-Authenticate": "Bearer"},
        )


async def get_current_user(
        token: Optional[str] = Depends(oauth2_scheme),
        db: AsyncSession = Depends(get_db)
) -> AppUser:
    """
    فعلاً در حالت تست: دریافت کاربر فرضی بدون بررسی توکن.
    همیشه یک کاربر ادمین برمی‌گرداند.

    Args:
        token (Optional[str]): توکن JWT (نادیده گرفته می‌شود)
        db (AsyncSession): نشست دیتابیس

    Returns:
        AppUser: کاربر فرضی
    """
    # SECURITY WARNING: این تنها برای تست است!
    # بررسی وجود کاربر در دیتابیس
    stmt = select(AppUser).where(AppUser.is_superuser == True).limit(1)
    result = await db.execute(stmt)
    user = result.scalar_one_or_none()
    
    if user:
        return user
    
    # اگر کاربری یافت نشد، یک کاربر فرضی برمی‌گرداند
    return AppUser(
        id=1,  # این ID استفاده نمی‌شود
        email="admin@example.com",
        hashed_password="hashed_password",
        full_name="Admin User (Mock)",
        is_active=True,
        is_superuser=True
    )


async def get_current_superuser(current_user: AppUser = Depends(get_current_user)) -> AppUser:
    """
    فعلاً در حالت تست: دریافت سوپریوزر فرضی.
    همیشه کاربر فعلی را برمی‌گرداند.

    Args:
        current_user (AppUser): کاربر فعلی

    Returns:
        AppUser: همان کاربر فعلی
    """
    # در حالت تست، همه کاربران سوپریوزر هستند
    return current_user