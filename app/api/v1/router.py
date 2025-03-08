"""
روتر اصلی API.

این ماژول روتر اصلی برای API نسخه 1 را تعریف می‌کند.
"""

from fastapi import APIRouter

from app.api.v1 import auth, tweets, analysis, waves, settings

# ایجاد روتر اصلی
router = APIRouter()

# افزودن روترهای اختصاصی
router.include_router(auth.router)
router.include_router(tweets.router)
router.include_router(analysis.router)
router.include_router(waves.router)
router.include_router(settings.router)



# اضافه کردن import جدید در فایل app/api/v1/router.py
from app.api.v1 import services

# اضافه کردن router جدید
router.include_router(services.router)