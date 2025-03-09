"""
میان‌افزار دیباگ.

این ماژول میان‌افزارهایی برای کمک به دیباگ و رفع مشکلات را فراهم می‌کند.
"""

import logging
import json
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.middleware.cors import CORSMiddleware

logger = logging.getLogger(__name__)


class DetailedCORSMiddleware(CORSMiddleware):
    """
    میان‌افزار CORS با لاگ جزئیات بیشتر.
    
    این میان‌افزار علاوه بر CORS استاندارد، جزئیات بیشتری در لاگ ثبت می‌کند.
    """
    
    async def __call__(self, scope, receive, send):
        """اجرای میان‌افزار"""
        if scope["type"] != "http":
            return await super().__call__(scope, receive, send)
        
        request = Request(scope, receive)
        logger.info(f"CORS Request: {request.method} {request.url.path}")
        logger.info(f"CORS Request Origin: {request.headers.get('origin', 'No origin')}")
        logger.info(f"CORS Request Headers: {dict(request.headers)}")
        
        return await super().__call__(scope, receive, send)


class APIDebugMiddleware(BaseHTTPMiddleware):
    """
    میان‌افزار دیباگ API.
    
    این میان‌افزار جزئیات درخواست‌ها و پاسخ‌های API را ثبت می‌کند.
    """
    
    async def dispatch(self, request: Request, call_next):
        """پردازش درخواست و ثبت اطلاعات آن"""
        # فقط مسیرهای API را لاگ می‌کنیم
        if not request.url.path.startswith("/api/"):
            return await call_next(request)
        
        # ثبت اطلاعات درخواست
        logger.info(f"API Request: {request.method} {request.url.path}")
        logger.info(f"API Request Headers: {dict(request.headers)}")
        
        # فراخوانی میان‌افزار بعدی
        response = await call_next(request)
        
        # ثبت اطلاعات پاسخ
        logger.info(f"API Response Status: {response.status_code}")
        logger.info(f"API Response Headers: {dict(response.headers)}")
        
        # برای پاسخ‌های خطا، سعی می‌کنیم محتوا را لاگ کنیم
        if response.status_code >= 400:
            try:
                # بدنه پاسخ را کپی می‌کنیم
                body = b""
                async for chunk in response.body_iterator:
                    body += chunk
                
                # محتوا را لاگ می‌کنیم
                try:
                    body_text = body.decode()
                    logger.error(f"API Error Response Body: {body_text}")
                except:
                    logger.error(f"API Error Response Body (binary): {body}")
                
                # پاسخ جدید با همان محتوا می‌سازیم
                return Response(
                    content=body,
                    status_code=response.status_code,
                    headers=dict(response.headers),
                    media_type=response.media_type
                )
            except:
                logger.exception("Error logging response body")
        
        return response