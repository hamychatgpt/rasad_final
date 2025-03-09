#!/usr/bin/env python
"""
اسکریپت ایجاد داده‌های پیش‌فرض.

این اسکریپت داده‌های پیش‌فرض مانند کاربر مدیر و کلیدواژه‌های اولیه را ایجاد می‌کند.
"""

import asyncio
import logging
import sys
import os
from getpass import getpass

# افزودن مسیر پروژه به PYTHONPATH
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.db.session import get_db, create_tables
from app.db.models import Keyword, AppUser
from app.core.security import get_password_hash
from sqlalchemy.future import select
from sqlalchemy.ext.asyncio import AsyncSession

# تنظیم لاگر
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger("init_data")

# کلیدواژه‌های پیش‌فرض
DEFAULT_KEYWORDS = [
    {"text": "وزارت ارتباطات", "description": "اخبار مرتبط با ایران", "priority": 10},
    {"text": "فیلترینگ", "description": "اخبار فناوری و تکنولوژی", "priority": 8},
    {"text": "هوش مصنوعی", "description": "مطالب مرتبط با هوش مصنوعی", "priority": 9},

]

async def create_default_keywords(db: AsyncSession):
    """ایجاد کلیدواژه‌های پیش‌فرض"""
    logger.info("Creating default keywords...")
    
    # بررسی وجود کلیدواژه‌ها
    stmt = select(Keyword)
    result = await db.execute(stmt)
    existing_keywords = result.scalars().all()
    
    if existing_keywords:
        logger.info(f"Found {len(existing_keywords)} existing keywords. Skipping.")
        return
    
    # ایجاد کلیدواژه‌های پیش‌فرض
    for keyword_data in DEFAULT_KEYWORDS:
        keyword = Keyword(**keyword_data, is_active=True)
        db.add(keyword)
    
    await db.commit()
    logger.info(f"Created {len(DEFAULT_KEYWORDS)} default keywords.")

async def create_admin_user(db: AsyncSession, email: str, password: str, full_name: str):
    """ایجاد کاربر مدیر"""
    logger.info(f"Creating admin user: {email}...")
    
    # بررسی وجود کاربر مدیر
    stmt = select(AppUser).where(AppUser.is_superuser == True)
    result = await db.execute(stmt)
    admin_user = result.scalar_one_or_none()
    
    if admin_user:
        logger.info(f"Admin user already exists: {admin_user.email}")
        return
    
    # ایجاد کاربر مدیر
    hashed_password = get_password_hash(password)
    admin = AppUser(
        email=email,
        hashed_password=hashed_password,
        full_name=full_name,
        is_active=True,
        is_superuser=True
    )
    
    db.add(admin)
    await db.commit()
    logger.info(f"Admin user created successfully: {email}")

async def main():
    """تابع اصلی"""
    logger.info("Initializing default data...")
    
    # ایجاد جداول دیتابیس اگر وجود نداشته باشند
    await create_tables()
    
    # دریافت اطلاعات کاربر مدیر از ورودی
    email = input("Enter admin email (default: admin@example.com): ") or "admin@example.com"
    password = getpass("Enter admin password (default: admin123): ") or "admin123"
    full_name = input("Enter admin full name (default: System Admin): ") or "System Admin"
    
    async for db in get_db():
        # ایجاد کلیدواژه‌های پیش‌فرض
        await create_default_keywords(db)
        
        # ایجاد کاربر مدیر
        await create_admin_user(db, email, password, full_name)
        
        break
    
    logger.info("Default data initialization completed!")

if __name__ == "__main__":
    asyncio.run(main())