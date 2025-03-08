"""
مدیریت نشست دیتابیس.

این ماژول ارتباط با دیتابیس و مدیریت نشست‌های SQLAlchemy را فراهم می‌کند.
"""

from typing import AsyncGenerator, Optional
from contextlib import asynccontextmanager
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import NullPool
import logging

from app.config import settings
from app.db.models import Base

logger = logging.getLogger(__name__)

# تنظیم pool_pre_ping=True برای بررسی اتصال قبل از استفاده و 
# max_overflow=20 برای اجازه دادن به ایجاد اتصالات اضافی در زمان فشار بالا
engine = create_async_engine(
    settings.SQLALCHEMY_DATABASE_URI, 
    echo=settings.DEBUG,
    pool_pre_ping=True,
    max_overflow=20,
    pool_size=10,
    pool_timeout=30,
    pool_recycle=1800  # بازیابی اتصالات بعد از 30 دقیقه
)

# ایجاد کلاس sessionmaker برای ساخت نشست‌های async
async_session_factory = async_sessionmaker(
    engine, 
    expire_on_commit=False,
    class_=AsyncSession
)


async def create_tables():
    """ایجاد جداول دیتابیس اگر وجود نداشته باشند"""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


# Context manager برای استفاده در with
@asynccontextmanager
async def get_session():
    """
    Context manager برای دریافت نشست دیتابیس.
    
    این تابع را می‌توان با 'async with' استفاده کرد:
        async with get_session() as session:
            # استفاده از session
    """
    session = async_session_factory()
    try:
        yield session
    finally:
        await session.close()


# Generator برای استفاده در FastAPI Depends
async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    وابستگی FastAPI برای دریافت نشست دیتابیس.

    این تابع به عنوان وابستگی در API‌ها استفاده می‌شود.

    Yields:
        AsyncSession: نشست دیتابیس
    """
    async with get_session() as session:
        yield session


# تابع صریح برای بستن موتور دیتابیس و آزادسازی همه اتصالات
async def close_db_engine():
    """بستن موتور دیتابیس و آزادسازی تمام اتصالات"""
    logger.info("Closing database engine and releasing all connections...")
    await engine.dispose()
    logger.info("Database engine disposed.")