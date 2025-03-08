"""
میان‌افزار مدیریت خطا.

این ماژول میان‌افزار مدیریت خطا را پیاده‌سازی می‌کند که خطاهای برنامه را گرفته
و پاسخ‌های خطای مناسب را برمی‌گرداند.
"""
import logging
import traceback
import json
from typing import Callable, Dict, Any, Union
from fastapi import Request, Response, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

from app.config import settings  # اضافه کردن import مورد نیاز

logger = logging.getLogger(__name__)


class ErrorHandlerMiddleware(BaseHTTPMiddleware):
    """
    میان‌افزار مدیریت خطا.

    این میان‌افزار خطاهای برنامه را گرفته و پاسخ‌های خطای مناسب را برمی‌گرداند.

    Attributes:
        app (ASGIApp): برنامه ASGI زیرین
    """

    def __init__(self, app: ASGIApp):
        """
        مقداردهی اولیه میان‌افزار مدیریت خطا.

        Args:
            app (ASGIApp): برنامه ASGI زیرین
        """
        super().__init__(app)
        logger.info("ErrorHandlerMiddleware initialized")

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """
        پردازش درخواست و گرفتن خطاهای آن.

        Args:
            request (Request): درخواست HTTP
            call_next (Callable): تابع پردازش درخواست بعدی

        Returns:
            Response: پاسخ HTTP
        """
        try:
            # فراخوانی میان‌افزار بعدی
            return await call_next(request)

        except Exception as e:
            # ثبت خطا با اطلاعات کامل
            logger.error(f"Unhandled exception: {e}")
            logger.error(traceback.format_exc())

            # تهیه پاسخ خطا
            error_response = self._prepare_error_response(e)

            # برگرداندن پاسخ خطا
            return JSONResponse(
                status_code=error_response["status_code"],
                content={"detail": error_response["detail"]}
            )

    def _prepare_error_response(self, exception: Exception) -> Dict[str, Any]:
        """
        تهیه پاسخ خطای مناسب براساس نوع خطا.

        Args:
            exception (Exception): خطای رخ داده

        Returns:
            Dict[str, Any]: اطلاعات پاسخ خطا شامل کد وضعیت و جزئیات
        """
        exception_class = exception.__class__.__name__
        detail = str(exception)

        # تعیین کد وضعیت و پیام خطا براساس نوع خطا
        if hasattr(exception, "status_code"):
            # استفاده از کد وضعیت تعریف شده در خطا (مانند HTTPException)
            status_code = getattr(exception, "status_code")
        else:
            # تعیین کد وضعیت براساس نوع خطا
            status_code = self._get_status_code_for_exception(exception_class)

        # اگر در محیط توسعه هستیم، اطلاعات بیشتری ارائه می‌دهیم
        if settings.DEBUG:
            error_detail = {
                "error": exception_class,
                "detail": detail,
                "traceback": traceback.format_exc().split("\n")
            }
            detail = json.dumps(error_detail)
        else:
            # در محیط تولید، اطلاعات کمتری ارائه می‌دهیم
            if status_code == status.HTTP_500_INTERNAL_SERVER_ERROR:
                # در خطاهای داخلی، جزئیات را پنهان می‌کنیم
                detail = "خطای داخلی سرور رخ داده است"

        return {
            "status_code": status_code,
            "detail": detail
        }

    def _get_status_code_for_exception(self, exception_class: str) -> int:
        """
        تعیین کد وضعیت HTTP براساس نوع خطا.

        Args:
            exception_class (str): نام کلاس خطا

        Returns:
            int: کد وضعیت HTTP
        """
        # نگاشت انواع خطا به کدهای وضعیت HTTP
        exception_mappings = {
            # خطاهای احراز هویت و مجوز
            "AuthenticationError": status.HTTP_401_UNAUTHORIZED,
            "PermissionDenied": status.HTTP_403_FORBIDDEN,
            "NotAuthenticated": status.HTTP_401_UNAUTHORIZED,

            # خطاهای داده
            "ValidationError": status.HTTP_422_UNPROCESSABLE_ENTITY,
            "DoesNotExist": status.HTTP_404_NOT_FOUND,
            "IntegrityError": status.HTTP_409_CONFLICT,

            # خطاهای سرویس‌های خارجی
            "TwitterAPIError": status.HTTP_502_BAD_GATEWAY,
            "ClaudeAPIError": status.HTTP_502_BAD_GATEWAY,
            "RedisError": status.HTTP_503_SERVICE_UNAVAILABLE,

            # سایر خطاها
            "InvalidOperation": status.HTTP_400_BAD_REQUEST,
            "NotImplementedError": status.HTTP_501_NOT_IMPLEMENTED,
            "FileNotFoundError": status.HTTP_404_NOT_FOUND,
            "PermissionError": status.HTTP_403_FORBIDDEN,
            "TimeoutError": status.HTTP_504_GATEWAY_TIMEOUT
        }

        # برگرداندن کد وضعیت مناسب یا 500 به عنوان پیش‌فرض
        return exception_mappings.get(exception_class, status.HTTP_500_INTERNAL_SERVER_ERROR)
