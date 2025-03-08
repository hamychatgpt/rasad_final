#!/usr/bin/env python
"""
اسکریپت راه‌اندازی سریع برای پروژه رصد.

این اسکریپت مراحل اساسی راه‌اندازی را انجام می‌دهد:
1. بررسی وجود فایل .env
2. بررسی اتصال به دیتابیس
3. ایجاد جداول دیتابیس
4. تست اتصال به Redis
5. تست اتصال به API‌های خارجی (اختیاری)
"""

import os
import sys
import asyncio
import logging
from typing import Dict, Any

# تنظیم لاگر
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("setup")


async def check_env_file() -> Dict[str, Any]:
    """بررسی وجود فایل .env و اطلاعات ضروری"""
    logger.info("Checking .env file...")
    
    env_file_path = ".env"
    env_example_path = ".env.example"
    
    # بررسی وجود فایل .env
    if not os.path.exists(env_file_path):
        if os.path.exists(env_example_path):
            logger.warning(f"No .env file found. Creating from {env_example_path}...")
            
            # کپی فایل .env.example به .env
            with open(env_example_path, 'r', encoding='utf-8') as example_file:
                content = example_file.read()
            
            with open(env_file_path, 'w', encoding='utf-8') as env_file:
                env_file.write(content)
                
            logger.info(f"Created .env file. Please edit it with your actual values.")
        else:
            logger.error("No .env or .env.example file found!")
            return {"success": False, "message": "Missing .env files"}
    
    # خواندن فایل .env
    env_vars = {}
    with open(env_file_path, 'r', encoding='utf-8') as env_file:
        for line in env_file:
            line = line.strip()
            if line and not line.startswith('#'):
                key, value = line.split('=', 1)
                env_vars[key.strip()] = value.strip().strip('"').strip("'")
    
    # بررسی وجود متغیرهای ضروری
    required_vars = [
        "POSTGRES_SERVER", "POSTGRES_USER", "POSTGRES_PASSWORD", "POSTGRES_DB",
        "REDIS_HOST", "REDIS_PORT",
        "TWITTER_API_KEY", "CLAUDE_API_KEY"
    ]
    
    missing_vars = [var for var in required_vars if var not in env_vars or not env_vars[var]]
    
    if missing_vars:
        logger.warning(f"Missing environment variables: {', '.join(missing_vars)}")
        return {"success": False, "message": f"Missing environment variables: {', '.join(missing_vars)}"}
    
    logger.info("All required environment variables found.")
    return {"success": True, "env_vars": env_vars}


async def setup_database() -> Dict[str, Any]:
    """بررسی اتصال به دیتابیس و ایجاد جداول"""
    logger.info("Setting up database...")
    
    try:
        # افزودن مسیر پروژه به PYTHONPATH
        if not "." in sys.path:
            sys.path.append(".")
        
        from app.db.session import get_db, create_tables
        
        # تست اتصال به دیتابیس
        try:
            logger.info("Testing database connection...")
            async for db_session in get_db():
                from sqlalchemy import text
                result = await db_session.execute(text("SELECT 1"))
                value = result.scalar()
                assert value == 1
                logger.info("Database connection successful!")
                break
        except Exception as e:
            logger.error(f"Database connection failed: {e}")
            return {"success": False, "message": f"Database connection error: {e}"}
        
        # ایجاد جداول
        try:
            logger.info("Creating database tables...")
            await create_tables()
            logger.info("Database tables created successfully!")
        except Exception as e:
            logger.error(f"Table creation failed: {e}")
            return {"success": False, "message": f"Table creation error: {e}"}
            
        return {"success": True}
    
    except ImportError as e:
        logger.error(f"Import error: {e}")
        return {"success": False, "message": f"Import error: {e}"}


async def test_redis_connection() -> Dict[str, Any]:
    """تست اتصال به Redis"""
    logger.info("Testing Redis connection...")
    
    try:
        from app.services.redis_service import RedisService
        
        redis_service = RedisService()
        await redis_service.connect()
        
        # تست عملیات پایه
        test_key = "test_key"
        test_value = {"test": "value"}
        
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
        
        logger.info("Redis connection successful!")
        return {"success": True}
    
    except Exception as e:
        logger.error(f"Redis connection failed: {e}")
        return {"success": False, "message": f"Redis connection error: {e}"}


async def test_external_apis() -> Dict[str, Any]:
    """تست اتصال به API‌های خارجی (اختیاری)"""
    logger.info("Testing external APIs (optional)...")
    
    results = {"twitter": {"success": False}, "claude": {"success": False}}
    
    # تست Twitter API
    try:
        from app.services.twitter.client import TwitterAPIClient
        
        logger.info("Testing Twitter API...")
        twitter_client = TwitterAPIClient()
        
        # تست ساده
        response = await twitter_client.search_tweets(
            query="test",
            query_type="Latest",
            max_results=5
        )
        
        tweets = response.tweets
        logger.info(f"Received {len(tweets)} tweets from Twitter API")
        
        await twitter_client.close()
        
        results["twitter"] = {"success": True, "message": f"Retrieved {len(tweets)} tweets"}
        
    except Exception as e:
        logger.warning(f"Twitter API test failed: {e}")
        results["twitter"] = {"success": False, "message": str(e)}
    
    # تست Claude API
    try:
        from app.services.analyzer.claude_client import ClaudeClient
        
        logger.info("Testing Claude API...")
        claude_client = ClaudeClient()
        
        # تست ساده
        result = await claude_client.analyze_sentiment(
            "This is a test message for Claude API connection. I am happy today!",
            language="en"
        )
        
        logger.info(f"Claude API result: {result}")
        
        await claude_client.close()
        
        results["claude"] = {"success": True, "message": f"Analysis performed: {result.get('sentiment', 'unknown')}"}
        
    except Exception as e:
        logger.warning(f"Claude API test failed: {e}")
        results["claude"] = {"success": False, "message": str(e)}
    
    return results


async def check_admin_user() -> Dict[str, Any]:
    """بررسی وجود کاربر مدیر"""
    logger.info("Checking for admin user...")
    
    try:
        from app.db.session import get_db
        from app.db.models import AppUser
        from sqlalchemy.future import select
        
        async for db_session in get_db():
            stmt = select(AppUser).where(AppUser.is_superuser == True)
            result = await db_session.execute(stmt)
            admin_user = result.scalar_one_or_none()
            
            if admin_user:
                logger.info(f"Admin user found: {admin_user.email}")
                return {"success": True, "has_admin": True, "admin_email": admin_user.email}
            else:
                logger.warning("No admin user found. Please run scripts/create_admin.py to create one.")
                return {"success": True, "has_admin": False}
    
    except Exception as e:
        logger.error(f"Error checking admin user: {e}")
        return {"success": False, "message": str(e)}


async def main():
    """تابع اصلی راه‌اندازی"""
    logger.info("Starting Rasad quick setup...")
    
    # بررسی فایل .env
    env_result = await check_env_file()
    if not env_result["success"]:
        logger.error("Environment setup failed. Please fix the issues and try again.")
        return
    
    # راه‌اندازی دیتابیس
    db_result = await setup_database()
    if not db_result["success"]:
        logger.error("Database setup failed. Please fix the issues and try again.")
        return
    
    # تست اتصال به Redis
    redis_result = await test_redis_connection()
    if not redis_result["success"]:
        logger.warning("Redis connection failed. Some features may not work properly.")
    
    # بررسی وجود کاربر مدیر
    admin_result = await check_admin_user()
    
    # تست API‌های خارجی (اختیاری)
    api_results = await test_external_apis()
    
    # نمایش نتایج
    logger.info("\n" + "="*50)
    logger.info("SETUP RESULTS:")
    logger.info("-"*50)
    logger.info(f"Environment: {'✅ SUCCESS' if env_result['success'] else '❌ FAILED'}")
    logger.info(f"Database:    {'✅ SUCCESS' if db_result['success'] else '❌ FAILED'}")
    logger.info(f"Redis:       {'✅ SUCCESS' if redis_result['success'] else '❌ FAILED'}")
    logger.info(f"Admin User:  {'✅ EXISTS' if admin_result.get('has_admin', False) else '⚠️ NOT FOUND'}")
    logger.info(f"Twitter API: {'✅ SUCCESS' if api_results['twitter']['success'] else '⚠️ FAILED (optional)'}")
    logger.info(f"Claude API:  {'✅ SUCCESS' if api_results['claude']['success'] else '⚠️ FAILED (optional)'}")
    logger.info("="*50)
    
    # توصیه‌های بعدی
    logger.info("\nNext steps:")
    if not admin_result.get('has_admin', False):
        logger.info("1. Create an admin user with: python scripts/create_admin.py")
    
    logger.info(f"2. Start backend: uvicorn app.main:app {'--reload' if env_result.get('env_vars', {}).get('DEBUG') == 'True' else ''}")
    logger.info("3. Run services:")
    logger.info("   - Collector: python scripts/run_collector.py")
    logger.info("   - Processor: python scripts/run_processor.py")
    logger.info("   - Analyzer:  python scripts/run_analyzer.py")
    logger.info("4. Or run all services: python scripts/run_all.py")
    
    # اطلاعات اضافی
    if api_results['twitter']['success'] is False or api_results['claude']['success'] is False:
        logger.info("\nNote: External API test failures are not critical for setup,")
        logger.info("but they will affect the system's functionality.")
        logger.info("Please check your API keys in the .env file.")


if __name__ == "__main__":
    asyncio.run(main())
