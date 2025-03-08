# پروژه رصد

پلتفرم هوشمند پایش، تحلیل و گزارش‌دهی فعالیت‌های توییتر مرتبط با سازمان‌ها یا موضوعات خاص.

## پیش‌نیازها

- Python 3.9+
- PostgreSQL
- Redis
- کلید API برای TwitterAPI.io
- کلید API برای Anthropic Claude

## نصب و راه‌اندازی

### 1. کلون کردن مخزن

```bash
git clone https://github.com/your-org/rasad.git
cd rasad

### 2. ایجاد محیط مجازی

```bash
# ایجاد محیط مجازی
python -m venv venv

# فعال‌سازی محیط مجازی در لینوکس/مک
source venv/bin/activate

# فعال‌سازی محیط مجازی در ویندوز
venv\Scripts\activate
```

### 3. نصب وابستگی‌ها

```bash
pip install -r requirements.txt
```

### 4. تنظیم فایل محیطی

فایل `.env.example` را به `.env` کپی کنید و مقادیر آن را با اطلاعات خود تنظیم کنید:

```bash
cp .env.example .env
# سپس فایل .env را با اطلاعات خود ویرایش کنید
```

### 5. ایجاد دیتابیس

```bash
# در PostgreSQL
createdb rasad
```

### 6. ایجاد کاربر مدیر سیستم

```bash
python scripts/create_admin.py
```

### 7. تست اتصال‌های پایه

```bash
python scripts/test_connections.py
```

## اجرای سیستم

### اجرای بک‌اند

```bash
cd app
uvicorn main:app --reload
```

بک‌اند در آدرس `http://localhost:8000` در دسترس خواهد بود. مستندات API در آدرس `http://localhost:8000/docs` قابل مشاهده است.

### اجرای فرانت‌اند ساده

```bash
cd frontend
python -m http.server
```

فرانت‌اند در آدرس `http://localhost:8000` در دسترس خواهد بود.

### اجرای سرویس‌های پس‌زمینه

#### اجرای تمام سرویس‌ها به صورت یکجا

```bash
python scripts/run_all.py
```

#### اجرای سرویس‌ها به صورت جداگانه

```bash
# جمع‌آوری کننده
python scripts/run_collector.py

# پردازشگر
python scripts/run_processor.py

# تحلیلگر
python scripts/run_analyzer.py
```

## اسکریپت ایجاد کاربر مدیر

فایل `scripts/create_admin.py` را ایجاد کنید:

```python
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
    db_session = await anext(get_db())
    
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
```

