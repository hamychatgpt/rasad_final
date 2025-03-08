"""
مدیریت نشست دیتابیس.

این ماژول ارتباط با دیتابیس و مدیریت نشست‌های SQLAlchemy را فراهم می‌کند.
"""

from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import sessionmaker

from app.config import settings
from app.db.models import Base

# ایجاد موتور SQLAlchemy با پشتیبانی از async
engine = create_async_engine(settings.SQLALCHEMY_DATABASE_URI, echo=settings.DEBUG)

# ایجاد کلاس sessionmaker برای ساخت نشست‌های async
async_session_factory = async_sessionmaker(
    engine, autocommit=False, autoflush=False, expire_on_commit=False
)


async def create_tables():
    """ایجاد جداول دیتابیس اگر وجود نداشته باشند"""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    وابستگی FastAPI برای دریافت نشست دیتابیس.

    این تابع به عنوان وابستگی در API‌ها استفاده می‌شود.

    Yields:
        AsyncSession: نشست دیتابیس
    """
    async with async_session_factory() as session:
        try:
            yield session
        finally:
            await session.close()


class DBSessionManager:
    """
    مدیریت نشست‌های دیتابیس.

    این کلاس امکان استفاده ساده‌تر از نشست‌های دیتابیس در سرویس‌ها را فراهم می‌کند.
    """

    @staticmethod
    async def get_db_session() -> AsyncSession:
        """
        ایجاد یک نشست دیتابیس جدید

        Returns:
            AsyncSession: نشست دیتابیس
        """
        session = async_session_factory()
        return session

    @staticmethod
    async def close_db_session(session: AsyncSession):
        """
        بستن نشست دیتابیس

        Args:
            session (AsyncSession): نشست دیتابیس
        """
        if session:
            await session.close()
