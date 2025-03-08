"""
اسکریپت اجرای تحلیلگر.

این اسکریپت سرویس تحلیل توییت‌ها را اجرا می‌کند.
"""

import asyncio
import logging
from datetime import datetime
import sys
import os

# افزودن مسیر پروژه به PYTHONPATH
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.db.session import get_db
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
        logging.FileHandler(f"logs/analyzer_{datetime.now().strftime('%Y%m%d')}.log")
    ]
)
logger = logging.getLogger("analyzer")


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
    except Exception as e:
        logger.error(f"Unhandled error in tweet analyzer: {e}", exc_info=True)
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
    except Exception as e:
        logger.error(f"Unhandled error in wave detection: {e}", exc_info=True)
    finally:
        # بستن اتصال‌ها
        await analyzer.close()


if __name__ == "__main__":
    # ایجاد پوشه لاگ اگر وجود نداشته باشد
    os.makedirs("logs", exist_ok=True)


    # اجرای هر دو تسک در event loop
    async def main():
        # ایجاد تسک‌ها
        analyzer_task = asyncio.create_task(run_analyzer())
        wave_detector_task = asyncio.create_task(run_wave_detection())

        # انتظار برای پایان تسک‌ها
        await asyncio.gather(analyzer_task, wave_detector_task)


    # اجرا در event loop
    asyncio.run(main())