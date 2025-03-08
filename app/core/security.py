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
    دریافت کاربر فعلی بر اساس توکن JWT.

    این تابع به عنوان وابستگی در مسیرهای API استفاده می‌شود و
    کاربر فعلی را بر اساس توکن JWT استخراج می‌کند.

    Args:
        token (Optional[str]): توکن JWT
        db (AsyncSession): نشست دیتابیس

    Returns:
        AppUser: کاربر فعلی

    Raises:
        HTTPException: در صورت عدم احراز هویت، نامعتبر بودن توکن یا یافت نشدن کاربر
    """
    # بررسی وجود توکن
    if token is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="احراز هویت الزامی است",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # استخراج داده‌های توکن
    token_data = get_token_data(token)

    # استخراج شناسه کاربر از توکن
    email = token_data.get("sub")
    if email is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="اطلاعات کاربر در توکن یافت نشد",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # جستجوی کاربر در دیتابیس
    stmt = select(AppUser).where(AppUser.email == email)
    result = await db.execute(stmt)
    user = result.scalar_one_or_none()

    # بررسی وجود کاربر
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="کاربر یافت نشد",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # بررسی فعال بودن کاربر
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="حساب کاربری غیرفعال است",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return user


async def get_current_superuser(current_user: AppUser = Depends(get_current_user)) -> AppUser:
    """
    دریافت مدیر سیستم فعلی.

    این تابع بررسی می‌کند که کاربر فعلی مدیر سیستم باشد.

    Args:
        current_user (AppUser): کاربر فعلی

    Returns:
        AppUser: مدیر سیستم فعلی

    Raises:
        HTTPException: در صورتی که کاربر فعلی مدیر سیستم نباشد
    """
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="دسترسی به این بخش نیاز به مجوز مدیر سیستم دارد"
        )

    return current_user
