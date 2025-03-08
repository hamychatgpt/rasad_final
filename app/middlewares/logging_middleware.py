"""
میان‌افزار ثبت وقایع.

این ماژول میان‌افزار لاگینگ را پیاده‌سازی می‌کند که تمام درخواست‌ها و پاسخ‌های HTTP را ثبت می‌کند.
"""

import time
import logging
import json
from typing import Callable
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

logger = logging.getLogger(__name__)


class LoggingMiddleware(BaseHTTPMiddleware):
    """
    میان‌افزار ثبت وقایع HTTP.

    این میان‌افزار اطلاعات درخواست‌ها و پاسخ‌های HTTP را ثبت می‌کند و زمان اجرای درخواست‌ها را محاسبه می‌کند.

    Attributes:
        app (ASGIApp): برنامه ASGI زیرین
    """

    def __init__(self, app: ASGIApp):
        """
        مقداردهی اولیه میان‌افزار لاگینگ.

        Args:
            app (ASGIApp): برنامه ASGI زیرین
        """
        super().__init__(app)
        logger.info("LoggingMiddleware initialized")

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """
        پردازش درخواست و ثبت اطلاعات آن.

        Args:
            request (Request): درخواست HTTP
            call_next (Callable): تابع پردازش درخواست بعدی

        Returns:
            Response: پاسخ HTTP
        """
        # ثبت اطلاعات درخواست
        start_time = time.time()

        # استخراج اطلاعات کاربر از هدر احراز هویت
        user_info = "Anonymous"
        if "authorization" in request.headers:
            # اگر توکن احراز هویت وجود دارد، اطلاعات کاربر را استخراج می‌کنیم
            # این پیاده‌سازی ساده‌ای است و بسته به نوع توکن و پیاده‌سازی احراز هویت ممکن است متفاوت باشد
            auth_header = request.headers["authorization"]
            if auth_header.startswith("Bearer "):
                user_info = "Authenticated"

        # ثبت اطلاعات درخواست
        request_info = {
            "method": request.method,
            "url": str(request.url),
            "path": request.url.path,
            "query_params": str(request.query_params),
            "client": request.client.host if request.client else "unknown",
            "user": user_info
        }

        # ثبت لاگ با سطح مناسب براساس مسیر
        if request.url.path == "/health":
            # مسیرهای بررسی سلامت را در سطح DEBUG ثبت می‌کنیم تا لاگ‌ها شلوغ نشوند
            logger.debug(f"Request: {json.dumps(request_info)}")
        else:
            logger.info(f"Request: {json.dumps(request_info)}")

        # فراخوانی میان‌افزار بعدی
        try:
            response = await call_next(request)

            # محاسبه زمان پردازش
            process_time = time.time() - start_time

            # افزودن هدر زمان پردازش
            response.headers["X-Process-Time"] = str(process_time)

            # ثبت اطلاعات پاسخ
            response_info = {
                "status_code": response.status_code,
                "process_time": process_time,
                "headers": dict(response.headers)
            }

            # ثبت لاگ با سطح مناسب براساس کد وضعیت
            if response.status_code >= 500:
                logger.error(f"Response: {json.dumps(response_info)}")
            elif response.status_code >= 400:
                logger.warning(f"Response: {json.dumps(response_info)}")
            elif request.url.path == "/health":
                logger.debug(f"Response: {json.dumps(response_info)}")
            else:
                logger.info(f"Response: {json.dumps(response_info)}")

            return response

        except Exception as e:
            # ثبت خطا
            process_time = time.time() - start_time
            logger.error(f"Error processing request: {e}", exc_info=True)

            # پرتاب مجدد خطا برای پردازش توسط میان‌افزار مدیریت خطا
            raise
