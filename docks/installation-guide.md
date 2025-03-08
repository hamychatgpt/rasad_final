# راهنمای کامل با تفکیک دقیق نصب پکیج‌ها (سیستمی و محیط مجازی)

در این راهنما، به دقت مشخص می‌کنم که چه چیزی باید در سیستم عامل نصب شود و چه چیزی باید در محیط مجازی Python نصب شود.

## 1. نصب پکیج‌های سیستمی (خارج از محیط مجازی)

```bash
# به‌روزرسانی سیستم
sudo apt update && sudo apt upgrade -y

# نصب پیش‌نیازهای سیستمی اصلی
sudo apt install -y build-essential git curl wget

# نصب Python 3.11 و ابزارهای مورد نیاز
sudo apt install -y software-properties-common
sudo add-apt-repository ppa:deadsnakes/ppa -y
sudo apt update
sudo apt install -y python3.11 python3.11-venv python3.11-dev python3.11-distutils

# نصب کتابخانه‌های توسعه مورد نیاز برای پکیج‌های Python
sudo apt install -y libpq-dev  # برای asyncpg (درایور PostgreSQL)

# نصب PostgreSQL
sudo apt install -y postgresql postgresql-contrib

# نصب Redis
sudo apt install -y redis-server

# راه‌اندازی و فعال‌سازی سرویس‌ها
sudo systemctl start postgresql
sudo systemctl enable postgresql
sudo systemctl start redis-server
sudo systemctl enable redis-server
```

## 2. تنظیم دیتابیس PostgreSQL (خارج از محیط مجازی)

```bash
# ایجاد کاربر و دیتابیس
sudo -u postgres psql -c "CREATE USER rasaduser WITH PASSWORD 'rasadpassword';"
sudo -u postgres psql -c "CREATE DATABASE rasad OWNER rasaduser;"
sudo -u postgres psql -c "ALTER USER rasaduser WITH SUPERUSER;"
```

## 3. آماده‌سازی پروژه و محیط مجازی Python

```bash
# ایجاد مسیر پروژه
mkdir -p ~/projects
cd ~/projects

# کلون پروژه (جایگزین با روش انتقال فایل‌های خود)
git clone https://github.com/your-organization/rasad.git
cd rasad

# ایجاد محیط مجازی با Python 3.11
python3.11 -m venv venv

# فعال‌سازی محیط مجازی (مهم: تمام دستورات بعدی در محیط مجازی اجرا می‌شوند)
source venv/bin/activate
```

## 4. نصب پکیج‌های Python (داخل محیط مجازی)

پس از فعال‌سازی محیط مجازی، همه نصب‌های پکیج‌های Python داخل این محیط انجام می‌شوند:

```bash
# ارتقاء pip و ابزارهای پایه
pip install --upgrade pip setuptools wheel

# نصب همه وابستگی‌های پروژه از فایل requirements.txt
pip install -r requirements.txt
```

### محتوای فایل requirements.txt (داخل محیط مجازی نصب می‌شوند)

تمام این پکیج‌ها با دستور `pip install -r requirements.txt` به صورت خودکار داخل محیط مجازی نصب می‌شوند:

```
# زیرساخت اصلی
fastapi==0.108.0               
uvicorn[standard]==0.25.0      
pydantic==2.5.3                
pydantic-settings==2.1.0       
email-validator==2.1.0         
python-dotenv==1.0.0           
httpx==0.26.0                  

# دیتابیس و صف
sqlalchemy==2.0.23             
asyncpg==0.29.0                
redis==5.0.1                  
alembic==1.13.0                

# بهبود عملکرد
uvloop==0.19.0                 
orjson==3.9.10                 

# احراز هویت و امنیت
pyjwt==2.8.0                   
passlib==1.7.4                 
bcrypt==4.1.2                  
python-multipart==0.0.6        
python-jose[cryptography]==3.3.0

# تحلیل داده
numpy==1.26.2                  
pandas==2.1.4                  

# ابزارهای کمکی
python-dateutil==2.8.2         
typing-extensions==4.9.0       
loguru==0.7.2                  
tenacity==8.2.3                

# تست (اختیاری برای اجرا)
pytest==7.4.3                  
pytest-asyncio==0.23.2         
coverage==7.3.2                
```

## 5. تنظیم فایل .env و ساختارهای پروژه

```bash
# کپی فایل نمونه (همچنان در محیط مجازی هستید)
cp .env.example .env

# ویرایش فایل .env
nano .env

# ایجاد پوشه logs
mkdir -p logs
```

## 6. ایجاد جداول دیتابیس و کاربر مدیر

```bash
# همچنان در محیط مجازی هستید
python scripts/create_admin.py
```

## 7. تست اتصال‌ها

```bash
# همچنان در محیط مجازی هستید
python scripts/test_connections.py
```

## 8. اجرای سرویس‌ها (همه در محیط مجازی)

**هر سرویس باید در یک ترمینال جداگانه اجرا شود، و هر ترمینال باید محیط مجازی را فعال کند:**

### ترمینال 1: API سرور

```bash
cd ~/projects/rasad
source venv/bin/activate  # فعال‌سازی محیط مجازی
cd app
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

### ترمینال 2: همه سرویس‌ها یکجا

```bash
cd ~/projects/rasad
source venv/bin/activate  # فعال‌سازی محیط مجازی
python scripts/run_all.py
```

**یا اجرای جداگانه هر سرویس (هر کدام در یک ترمینال جداگانه):**

### ترمینال 2: جمع‌آوری داده

```bash
cd ~/projects/rasad
source venv/bin/activate  # فعال‌سازی محیط مجازی
python scripts/run_collector.py
```

### ترمینال 3: پردازش

```bash
cd ~/projects/rasad
source venv/bin/activate  # فعال‌سازی محیط مجازی
python scripts/run_processor.py
```

### ترمینال 4: تحلیل

```bash
cd ~/projects/rasad
source venv/bin/activate  # فعال‌سازی محیط مجازی
python scripts/run_analyzer.py
```

## نکات مهم

1. **همیشه محیط مجازی را فعال کنید**: هر دستور مرتبط با Python باید در محیط مجازی (`source venv/bin/activate`) اجرا شود.

2. **وابستگی‌های سیستمی vs پکیج‌های Python**:
   - **سیستمی**: Python 3.11، PostgreSQL، Redis، کتابخانه‌های توسعه (`apt install`)
   - **محیط مجازی**: تمام پکیج‌های Python لیست شده در requirements.txt (`pip install`)

3. **کلیدهای API**: مطمئن شوید کلیدهای معتبر TwitterAPI.io و Claude API را در فایل `.env` تنظیم کرده‌اید.

4. **منابع سیستمی**: این پروژه به حداقل 4GB RAM و 2 هسته CPU نیاز دارد.

5. **فایروال**: اگر از فایروال استفاده می‌کنید، پورت 8000 را باز کنید.

با این راهنما، تفکیک دقیق بین پکیج‌های سیستمی (نصب با apt) و پکیج‌های Python (نصب در محیط مجازی با pip) مشخص شده است.