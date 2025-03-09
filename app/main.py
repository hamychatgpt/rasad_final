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
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse

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
from app.api.v1.services import router as services_router
from app.api.v1.router import router as api_router

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
    docs_url="/api/docs" if settings.DEBUG else None,  # تغییر مسیر داکس به /api/docs
    redoc_url="/api/redoc" if settings.DEBUG else None,  # تغییر مسیر redoc به /api/redoc
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

# تعیین مسیر پوشه فرانت‌اند
frontend_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "frontend")
logger.info(f"Frontend directory: {frontend_dir}")

# اضافه کردن مسیر استاتیک برای فایل‌های CSS و JS
app.mount("/static", StaticFiles(directory=os.path.join(frontend_dir, "app")), name="static")
app.mount("/js", StaticFiles(directory=os.path.join(frontend_dir, "app", "js")), name="js")
app.mount("/css", StaticFiles(directory=os.path.join(frontend_dir, "app", "css")), name="css")

# افزودن روتر اصلی API با پیشوند /api
app.include_router(
    api_router,
    prefix="/api"
)

# اندپوینت اصلی API برای سازگاری با نسخه‌های قبلی
@app.get("/api", response_class=JSONResponse)
async def api_root():
    return {
        "message": "به API سیستم رصد خوش آمدید",
        "version": "1.0.0",
        "status": "online"
    }

# تعریف مسیر ریشه برای سرو فایل index.html
@app.get("/", response_class=FileResponse, include_in_schema=False)
async def serve_frontend():
    index_path = os.path.join(frontend_dir, "app", "index.html")
    if os.path.exists(index_path):
        logger.info(f"Serving frontend index from: {index_path}")
        return FileResponse(index_path)
    else:
        logger.error(f"Frontend file not found at: {index_path}")
        # اگر فایل وجود نداشت، پیام خطا نمایش می‌دهیم
        return JSONResponse(
            status_code=404,
            content={
                "message": "فایل‌های فرانت‌اند یافت نشد",
                "error": f"فایل index.html در مسیر {index_path} وجود ندارد",
                "help": "لطفاً مطمئن شوید که پوشه frontend/app در مسیر صحیح قرار دارد"
            }
        )

# تعریف مسیر برای هر درخواست دیگر که با /api شروع نمی‌شود
@app.get("/{path:path}", response_class=FileResponse, include_in_schema=False)
async def serve_frontend_paths(path: str):
    # اگر مسیر با api شروع شود، آن را رد می‌کنیم
    if path.startswith("api"):
        raise HTTPException(status_code=404, detail="Not Found")
    
    # بررسی وجود فایل استاتیک
    static_file = os.path.join(frontend_dir, "app", path)
    if os.path.exists(static_file) and not os.path.isdir(static_file):
        logger.debug(f"Serving static file: {static_file}")
        return FileResponse(static_file)
    
    # در غیر این صورت index.html را برمی‌گردانیم (برای SPA)
    index_path = os.path.join(frontend_dir, "app", "index.html")
    if os.path.exists(index_path):
        logger.debug(f"Serving frontend index for path: {path}")
        return FileResponse(index_path)
    else:
        logger.error(f"Frontend file not found at: {index_path}")
        raise HTTPException(status_code=404, detail="Frontend files not found")