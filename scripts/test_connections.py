"""
اسکریپت تست اتصال‌های پایه.

این اسکریپت اتصال به دیتابیس، Redis و API‌های خارجی را تست می‌کند.
"""

import asyncio
import logging
import sys
import os
from datetime import datetime

# افزودن مسیر پروژه به PYTHONPATH
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# تنظیم لاگر
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("test_connections")

# استفاده از ماژول‌های پروژه
from app.db.session import get_session, close_db_engine
from app.services.redis_service import RedisService
from app.services.twitter.client import TwitterAPIClient
from app.services.analyzer.claude_client import ClaudeClient


async def test_database_connection():
    """تست اتصال به دیتابیس"""
    logger.info("Testing database connection...")
    try:
        # استفاده از context manager برای مدیریت چرخه حیات نشست
        async with get_session() as session:
            from sqlalchemy import text
            result = await session.execute(text("SELECT 1"))
            value = result.scalar()
            assert value == 1
            logger.info("✅ Database connection successful!")
            return True
    except Exception as e:
        logger.error(f"❌ Database connection failed: {e}")
        return False


async def test_redis_connection():
    """تست اتصال به Redis"""
    logger.info("Testing Redis connection...")
    try:
        redis_service = RedisService()
        await redis_service.connect()

        # تست عملیات پایه
        test_key = "test_key"
        test_value = {"test": "value", "timestamp": datetime.now().isoformat()}

        # تست نوشتن
        result = await redis_service.set_cache(test_key, test_value, expire=60)
        assert result == True

        # تست خواندن
        read_value = await redis_service.get_cache(test_key)
        assert read_value["test"] == "value"

        # تست حذف
        delete_result = await redis_service.delete_cache(test_key)
        assert delete_result == True

        # بستن اتصال
        await redis_service.disconnect()

        logger.info("✅ Redis connection successful!")
        return True
    except Exception as e:
        logger.error(f"❌ Redis connection failed: {e}")
        return False


async def test_twitter_api():
    """تست اتصال به Twitter API"""
    logger.info("Testing Twitter API connection...")
    try:
        twitter_client = TwitterAPIClient()

        # تست جستجوی ساده
        response = await twitter_client.search_tweets(
            query="test",
            query_type="Latest",
            cursor=""
        )

        # بررسی پاسخ
        tweets = response.tweets
        logger.info(f"Received {len(tweets)} tweets from Twitter API")

        # بستن اتصال
        await twitter_client.close()

        logger.info("✅ Twitter API connection successful!")
        return True
    except Exception as e:
        logger.error(f"❌ Twitter API connection failed: {e}")
        return False


async def test_claude_api():
    """تست اتصال به Claude API"""
    logger.info("Testing Claude API connection...")
    try:
        claude_client = ClaudeClient()

        # تست ساده تحلیل احساسات
        result = await claude_client.analyze_sentiment(
            "این یک متن آزمایشی برای تست اتصال به API کلود است.",
            language="fa"
        )

        # بررسی پاسخ
        logger.info(f"Claude API sentiment result: {result}")

        # بستن اتصال
        await claude_client.close()

        logger.info("✅ Claude API connection successful!")
        return True
    except Exception as e:
        logger.error(f"❌ Claude API connection failed: {e}")
        return False


async def main():
    """تابع اصلی"""
    logger.info("Starting connection tests...")

    try:
        # تست همه اتصال‌ها
        db_result = await test_database_connection()
        redis_result = await test_redis_connection()
        twitter_result = await test_twitter_api()
        claude_result = await test_claude_api()

        # نتیجه کلی
        all_passed = db_result and redis_result and twitter_result and claude_result

        if all_passed:
            logger.info("🎉 All connections tests passed!")
        else:
            logger.warning("⚠️ Some connection tests failed!")

        # نمایش خلاصه
        logger.info("Connection Tests Summary:")
        logger.info(f"Database: {'✅ PASS' if db_result else '❌ FAIL'}")
        logger.info(f"Redis: {'✅ PASS' if redis_result else '❌ FAIL'}")
        logger.info(f"Twitter API: {'✅ PASS' if twitter_result else '❌ FAIL'}")
        logger.info(f"Claude API: {'✅ PASS' if claude_result else '❌ FAIL'}")
    finally:
        # آزادسازی صریح منابع دیتابیس قبل از پایان برنامه
        await close_db_engine()
        logger.info("All database resources released.")


if __name__ == "__main__":
    # استفاده از asyncio.run برای مدیریت صحیح event loop
    asyncio.run(main())