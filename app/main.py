"""
نقطه ورودی اصلی بک‌اند.

این ماژول نقطه ورودی اصلی برای برنامه FastAPI است که تنظیمات اولیه،
میان‌افزارها، روتر‌ها و وابستگی‌های برنامه را تعریف می‌کند.
"""

import logging
from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession
import os
from contextlib import asynccontextmanager

from app.config import settings
from app.db.session import get_db, create_tables
from app.middlewares.logging_middleware import LoggingMiddleware
from app.middlewares.error_handler import ErrorHandlerMiddleware
from app.core.security import get_current_user
from app.db.models import AppUser

# روترهای API
from app.api.v1.auth import router as auth_router
from app.api.v1.tweets import router as tweets_router
from app.api.v1.analysis import router as analysis_router
from app.api.v1.waves import router as waves_router
from app.api.v1.settings import router as settings_router

from sqlalchemy import select, text

# تنظیم لاگر
logging.basicConfig(
    level=logging.INFO if not settings.DEBUG else logging.DEBUG,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger("app")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    مدیریت چرخه حیات برنامه.

    این تابع عملیات‌های مورد نیاز برای راه‌اندازی و خاموش کردن برنامه را انجام می‌دهد.

    Args:
        app (FastAPI): نمونه برنامه FastAPI
    """
    # عملیات راه‌اندازی
    logger.info("Starting application...")

    # ایجاد جداول دیتابیس اگر وجود نداشته باشند
    await create_tables()
    logger.info("Database tables created or verified")

    # افزودن سرویس‌های خارجی به کانتکست اپلیکیشن
    app.state.twitter_client = None
    app.state.claude_client = None
    app.state.redis_service = None

    # راه‌اندازی سرویس‌های خارجی
    # TODO: پیاده‌سازی راه‌اندازی سرویس‌ها

    yield

    # عملیات خاموش کردن
    logger.info("Shutting down application...")

    # بستن اتصالات خارجی
    # TODO: پیاده‌سازی بستن اتصالات


# ایجاد برنامه FastAPI
app = FastAPI(
    title=settings.PROJECT_NAME,
    description="سیستم رصد - پلتفرم هوشمند برای پایش، تحلیل و گزارش‌دهی فعالیت‌های توییتر",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs" if settings.DEBUG else None,
    redoc_url="/redoc" if settings.DEBUG else None,
)

# افزودن میان‌افزارها
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(LoggingMiddleware)
app.add_middleware(ErrorHandlerMiddleware)

# افزودن روترها
app.include_router(auth_router, prefix=settings.API_V1_STR)
app.include_router(tweets_router, prefix=settings.API_V1_STR, dependencies=[Depends(get_current_user)])
app.include_router(analysis_router, prefix=settings.API_V1_STR, dependencies=[Depends(get_current_user)])
app.include_router(waves_router, prefix=settings.API_V1_STR, dependencies=[Depends(get_current_user)])
app.include_router(settings_router, prefix=settings.API_V1_STR, dependencies=[Depends(get_current_user)])


@app.get("/")
async def root():
    """
    مسیر ریشه برنامه.

    این مسیر برای بررسی در دسترس بودن برنامه استفاده می‌شود.

    Returns:
        Dict: پیام خوش‌آمدگویی و وضعیت برنامه
    """
    return {
        "message": f"به API سیستم رصد خوش آمدید",
        "version": "1.0.0",
        "status": "online"
    }


@app.get("/health")
async def health_check(db: AsyncSession = Depends(get_db)):
    """
    بررسی سلامت برنامه.

    این مسیر برای بررسی سلامت برنامه و اتصالات آن استفاده می‌شود.

    Args:
        db (AsyncSession): نشست دیتابیس

    Returns:
        Dict: وضعیت سلامت برنامه و اتصالات آن
    """
    health = {
        "status": "healthy",
        "database": "connected",
        "twitter_api": "unknown",
        "claude_api": "unknown",
        "redis": "unknown"
    }

    # بررسی اتصال دیتابیس
    try:
        # بررسی ساده اتصال دیتابیس
        await db.execute(select(text("1")))
    except Exception as e:
        health["database"] = "disconnected"
        health["status"] = "unhealthy"
        logger.error(f"Database health check failed: {e}")

    # بررسی سایر سرویس‌ها
    # TODO: پیاده‌سازی بررسی سلامت سایر سرویس‌ها

    return health


if __name__ == "__main__":
    import uvicorn

    host = os.getenv("HOST", "127.0.0.1")
    port = int(os.getenv("PORT", 8000))
    log_level = "info" if not settings.DEBUG else "debug"

    logger.info(f"Running application in {'debug' if settings.DEBUG else 'production'} mode")
    uvicorn.run("app.main:app", host=host, port=port, log_level=log_level, reload=settings.DEBUG)
