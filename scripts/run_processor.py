"""
اسکریپت اجرای پردازشگر.

این اسکریپت سرویس پردازش توییت‌ها را اجرا می‌کند.
"""

import asyncio
import logging
from datetime import datetime
import sys
import os

# افزودن مسیر پروژه به PYTHONPATH
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.db.session import get_db
from app.services.redis_service import RedisService
from app.services.processor.content_filter import ContentFilter
from app.services.processor.tweet_processor import TweetProcessor

# تنظیم لاگر
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(f"logs/processor_{datetime.now().strftime('%Y%m%d')}.log")
    ]
)
logger = logging.getLogger("processor")


async def run_processor():
    """اجرای پردازشگر"""
    logger.info("Starting tweet processor")

    # ایجاد اتصال‌ها
    db_session = await anext(get_db())
    redis_service = RedisService()
    await redis_service.connect()
    content_filter = ContentFilter()

    # ایجاد پردازشگر
    processor = TweetProcessor(
        db_session=db_session,
        redis_service=redis_service,
        content_filter=content_filter
    )

    try:
        # اجرای پردازشگر به صورت مداوم
        await processor.run_processor(batch_size=50, sleep_time=30)
    except asyncio.CancelledError:
        logger.info("Tweet processor task cancelled")
    except Exception as e:
        logger.error(f"Unhandled error in tweet processor: {e}", exc_info=True)
    finally:
        # بستن اتصال‌ها
        await redis_service.disconnect()


if __name__ == "__main__":
    # ایجاد پوشه لاگ اگر وجود نداشته باشد
    os.makedirs("logs", exist_ok=True)

    # اجرا در event loop
    asyncio.run(run_processor())