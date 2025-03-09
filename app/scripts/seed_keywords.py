"""
اسکریپت اضافه کردن چند کلیدواژه نمونه به دیتابیس.
"""

import asyncio
import sys
import os
from pathlib import Path

# اضافه کردن مسیر پروژه به PATH برای import
project_root = Path(__file__).parents[2]
sys.path.insert(0, str(project_root))

from sqlalchemy import select
from app.db.session import get_session, create_tables
from app.db.models import Keyword


async def add_sample_keywords():
    """
    اضافه کردن کلیدواژه‌های نمونه به دیتابیس
    """
    print("اضافه کردن کلیدواژه‌های نمونه به دیتابیس...")
    
    # ایجاد جداول اگر وجود نداشته باشند
    await create_tables()
    
    # کلیدواژه‌های نمونه برای اضافه کردن
    sample_keywords = [
        {"text": "ایران", "priority": 10, "description": "اخبار ایران", "is_active": True},
        {"text": "اقتصاد", "priority": 8, "description": "اقتصاد و بازار", "is_active": True},
        {"text": "سیاست", "priority": 9, "description": "اخبار سیاسی", "is_active": True},
        {"text": "ورزش", "priority": 7, "description": "اخبار ورزشی", "is_active": True},
        {"text": "فناوری", "priority": 6, "description": "فناوری و تکنولوژی", "is_active": True},
        {"text": "دولت", "priority": 8, "description": "اخبار دولت", "is_active": True},
        {"text": "آموزش", "priority": 5, "description": "آموزش و پرورش", "is_active": True},
        {"text": "سلامت", "priority": 7, "description": "سلامت و پزشکی", "is_active": True},
        {"text": "هنر", "priority": 4, "description": "هنر و فرهنگ", "is_active": True},
        {"text": "جامعه", "priority": 6, "description": "مسائل اجتماعی", "is_active": True},
    ]
    
    async with get_session() as session:
        # ابتدا بررسی کنیم کلیدواژه‌ها قبلاً وجود دارند یا خیر
        stmt = select(Keyword)
        result = await session.execute(stmt)
        existing_keywords = result.scalars().all()
        
        existing_texts = [k.text for k in existing_keywords]
        print(f"تعداد {len(existing_texts)} کلیدواژه از قبل موجود است:")
        for text in existing_texts:
            print(f"  - {text}")
        
        # اضافه کردن کلیدواژه‌های جدید
        added_count = 0
        for kw in sample_keywords:
            if kw["text"] not in existing_texts:
                keyword = Keyword(**kw)
                session.add(keyword)
                added_count += 1
        
        if added_count > 0:
            await session.commit()
            print(f"{added_count} کلیدواژه با موفقیت اضافه شد.")
        else:
            print("کلیدواژه جدیدی اضافه نشد.")


if __name__ == "__main__":
    asyncio.run(add_sample_keywords())