"""
اسکریپت اجرای جمع‌آوری کننده.

این اسکریپت سرویس جمع‌آوری توییت‌ها را اجرا می‌کند.
"""

import asyncio
import logging
from datetime import datetime
import sys
import os

# افزودن مسیر پروژه به PYTHONPATH
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.db.session import get_db, close_db_engine
from app.services.redis_service import RedisService
from app.services.twitter.client import TwitterAPIClient
from app.services.twitter.collector import TweetCollector

# تنظیم لاگر
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(f"logs/collector_{datetime.now().strftime('%Y%m%d')}.log")
    ]
)
logger = logging.getLogger("collector")


async def run_collector():
    """اجرای جمع‌آوری کننده"""
    logger.info("Starting tweet collector")
    
    try:
        # ایجاد اتصال‌ها
        async for session in get_db():
            db_session = session
            break
            
        redis_service = RedisService()
        await redis_service.connect()
        twitter_client = TwitterAPIClient()

        # ایجاد جمع‌آوری کننده
        collector = TweetCollector(
            twitter_client=twitter_client,
            db_session=db_session,
            redis_service=redis_service
        )

        try:
            # دریافت کلیدواژه‌های فعال
            keywords = await collector.get_active_keywords()
            logger.info(f"Found {len(keywords)} active keywords")

            # انتخاب تعداد کلیدواژه برای هر سری جمع‌آوری
            batch_size = 3
            hours_back = 2

            while True:
                # دریافت کلیدواژه‌های فعال (برای به‌روزرسانی)
                keywords = await collector.get_active_keywords()

                if not keywords:
                    logger.warning("No active keywords found")
                    await asyncio.sleep(300)  # 5 دقیقه انتظار
                    continue

                # جمع‌آوری براساس هر دسته کلیدواژه
                for i in range(0, len(keywords), batch_size):
                    batch_keywords = keywords[i:i + batch_size]
                    logger.info(f"Collecting tweets for keywords: {batch_keywords}")

                    try:
                        # جمع‌آوری توییت‌ها
                        tweets = await collector.collect_by_keywords(
                            keywords=batch_keywords,
                            days_back=hours_back,
                            max_tweets=500,
                            save_to_db=True
                        )

                        logger.info(f"Collected {len(tweets)} tweets for keywords {batch_keywords}")
                    except Exception as e:
                        logger.error(f"Error collecting tweets for keywords {batch_keywords}: {e}")

                    # انتظار بین هر دسته
                    await asyncio.sleep(10)

                # انتظار قبل از شروع دور بعدی
                logger.info(f"Completed collection cycle. Waiting for 15 minutes before next cycle.")
                await asyncio.sleep(900)  # 15 دقیقه انتظار

        except asyncio.CancelledError:
            logger.info("Tweet collector task cancelled")
        finally:
            # بستن اتصال‌ها
            await redis_service.disconnect()
            await twitter_client.close()
            
    except Exception as e:
        logger.error(f"Error in collector main function: {e}", exc_info=True)
    finally:
        # بستن اتصال دیتابیس به صورت صریح
        await close_db_engine()


if __name__ == "__main__":
    # ایجاد پوشه لاگ اگر وجود نداشته باشد
    os.makedirs("logs", exist_ok=True)

    # اجرا در event loop
    asyncio.run(run_collector())