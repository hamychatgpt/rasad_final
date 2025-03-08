"""
اسکریپت اجرای تمام سرویس‌ها.

این اسکریپت تمام سرویس‌های اصلی پروژه را اجرا می‌کند.
"""

import asyncio
import logging
from datetime import datetime
import sys
import os

# افزودن مسیر پروژه به PYTHONPATH
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.db.session import get_db, create_tables
from app.services.redis_service import RedisService
from app.services.twitter.client import TwitterAPIClient
from app.services.twitter.collector import TweetCollector
from app.services.processor.content_filter import ContentFilter
from app.services.processor.tweet_processor import TweetProcessor
from app.services.analyzer.claude_client import ClaudeClient
from app.services.analyzer.cost_manager import CostManager
from app.services.analyzer.wave_detector import WaveDetector
from app.services.analyzer.analyzer import TweetAnalyzer

# تنظیم لاگر
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(f"logs/rasad_{datetime.now().strftime('%Y%m%d')}.log")
    ]
)
logger = logging.getLogger("rasad")


async def run_collector():
    """اجرای جمع‌آوری کننده"""
    logger.info("Starting tweet collector")

    # ایجاد اتصال‌ها
    db_session = await anext(get_db())
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
    finally:
        # بستن اتصال‌ها
        await redis_service.disconnect()


async def run_analyzer():
    """اجرای تحلیلگر"""
    logger.info("Starting tweet analyzer")

    # ایجاد اتصال‌ها
    db_session = await anext(get_db())
    claude_client = ClaudeClient()
    cost_manager = CostManager(db_session)
    await cost_manager.initialize()
    wave_detector = WaveDetector(db_session)

    # ایجاد تحلیلگر
    analyzer = TweetAnalyzer(
        db_session=db_session,
        claude_client=claude_client,
        cost_manager=cost_manager,
        wave_detector=wave_detector,
        batch_size=50
    )
    await analyzer.initialize()

    try:
        # اجرای تحلیلگر به صورت مداوم
        await analyzer.run_analyzer(sleep_time=60)
    except asyncio.CancelledError:
        logger.info("Tweet analyzer task cancelled")
    finally:
        # بستن اتصال‌ها
        await analyzer.close()


async def run_wave_detection():
    """اجرای تشخیص موج به صورت دوره‌ای"""
    logger.info("Starting wave detection")

    # ایجاد اتصال‌ها
    db_session = await anext(get_db())
    claude_client = ClaudeClient()
    cost_manager = CostManager(db_session)
    await cost_manager.initialize()
    wave_detector = WaveDetector(db_session)

    # ایجاد تحلیلگر
    analyzer = TweetAnalyzer(
        db_session=db_session,
        claude_client=claude_client,
        cost_manager=cost_manager,
        wave_detector=wave_detector
    )
    await analyzer.initialize()

    try:
        while True:
            # تشخیص موج‌ها و ایجاد هشدار
            logger.info("Running wave detection")
            try:
                alerts = await analyzer.detect_waves_and_alert(hours_back=6)
                logger.info(f"Created {len(alerts)} alerts from detected waves")
            except Exception as e:
                logger.error(f"Error detecting waves: {e}")

            # انتظار قبل از بررسی بعدی (هر 30 دقیقه)
            logger.info("Wave detection completed. Waiting for 30 minutes.")
            await asyncio.sleep(1800)  # 30 دقیقه

    except asyncio.CancelledError:
        logger.info("Wave detection task cancelled")
    finally:
        # بستن اتصال‌ها
        await analyzer.close()


async def main():
    """تابع اصلی"""
    logger.info("Starting Rasad System")

    # ایجاد جداول دیتابیس اگر وجود نداشته باشند
    logger.info("Creating database tables if needed")
    await create_tables()

    # ایجاد تسک‌ها
    logger.info("Creating service tasks")
    tasks = [
        run_collector(),
        run_processor(),
        run_analyzer(),
        run_wave_detection()
    ]

    # اجرای همه تسک‌ها
    try:
        logger.info("Running all services")
        await asyncio.gather(*tasks)
    except KeyboardInterrupt:
        logger.info("Received keyboard interrupt")
    except Exception as e:
        logger.error(f"Unhandled error in main: {e}", exc_info=True)
    finally:
        logger.info("Rasad System shutdown")


if __name__ == "__main__":
    # ایجاد پوشه لاگ اگر وجود نداشته باشد
    os.makedirs("logs", exist_ok=True)

    # اجرا در event loop
    asyncio.run(main())