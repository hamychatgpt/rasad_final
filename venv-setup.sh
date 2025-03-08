# نصب Python 3.11 (بسته به سیستم‌عامل متفاوت است)

# Ubuntu/Debian
# sudo add-apt-repository ppa:deadsnakes/ppa
# sudo apt update
# sudo apt install python3.11 python3.11-venv python3.11-dev

# macOS با Homebrew
# brew install python@3.11

# Windows
# از وب‌سایت رسمی Python دانلود و نصب کنید

# ایجاد محیط مجازی
python3.11 -m venv venv

# فعال‌سازی محیط مجازی (Linux/macOS)
source venv/bin/activate

# فعال‌سازی محیط مجازی (Windows)
# venv\Scripts\activate

# ارتقاء pip و ابزارهای نصب
pip install --upgrade pip setuptools wheel

# نصب وابستگی‌ها
pip install -r requirements.txt

# بررسی نصب‌ها
pip list

# خروجی زیر را ببینید - می‌تواند کمک کند مطمئن شوید همه‌چیز درست نصب شده
# Package                   Version
# ------------------------- ---------
# fastapi                   0.108.0
# pydantic                  2.5.3
# sqlalchemy                2.0.23
# ...

# نسخه پایتون را تایید کنید
python --version
# باید نشان دهد: Python 3.11.x