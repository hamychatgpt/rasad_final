"""
اسکریپت ایجاد کاربر مدیر سیستم.

این اسکریپت یک کاربر مدیر با دسترسی کامل ایجاد می‌کند.
"""

import asyncio
import sys
import os
import getpass

# افزودن مسیر پروژه به PYTHONPATH
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.db.session import get_db, create_tables
from app.db.models import AppUser
from app.core.security import get_password_hash
from sqlalchemy.future import select


async def create_admin_user():
    """ایجاد کاربر مدیر"""
    print("ایجاد کاربر مدیر سیستم")
    print("-----------------------\n")

    # ایجاد جداول دیتابیس اگر وجود نداشته باشند
    await create_tables()

    # دریافت اطلاعات کاربر
    email = input("ایمیل: ")
    full_name = input("نام کامل: ")
    password = getpass.getpass("رمز عبور: ")
    confirm_password = getpass.getpass("تکرار رمز عبور: ")

    # بررسی تطابق رمز عبور
    if password != confirm_password:
        print("\n❌ رمز عبور و تکرار آن مطابقت ندارند.")
        return

    # بررسی قدرت رمز عبور
    if len(password) < 8:
        print("\n❌ رمز عبور باید حداقل 8 کاراکتر باشد.")
        return

    # دریافت نشست دیتابیس
    async for session in get_db():
        db_session = session
        break

    # بررسی وجود کاربر
    stmt = select(AppUser).where(AppUser.email == email)
    result = await db_session.execute(stmt)
    existing_user = result.scalar_one_or_none()

    if existing_user:
        print(f"\n❌ کاربری با ایمیل {email} قبلاً وجود دارد.")
        return

    # ایجاد کاربر مدیر
    hashed_password = get_password_hash(password)
    user = AppUser(
        email=email,
        full_name=full_name,
        hashed_password=hashed_password,
        is_active=True,
        is_superuser=True
    )

    db_session.add(user)
    await db_session.commit()

    print(f"\n✅ کاربر مدیر {email} با موفقیت ایجاد شد.")


if __name__ == "__main__":
    asyncio.run(create_admin_user())