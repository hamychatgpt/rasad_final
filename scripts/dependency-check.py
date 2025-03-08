#!/usr/bin/env python
"""
اسکریپت بررسی سازگاری وابستگی‌ها.

این اسکریپت وابستگی‌های نصب شده را بررسی می‌کند و موارد بالقوه ناسازگار را گزارش می‌دهد.
همچنین بررسی می‌کند که آیا پایتون مورد استفاده حداقل نسخه مورد نیاز را دارد.
"""

import sys
import pkg_resources
import platform
from importlib.metadata import version, PackageNotFoundError
import importlib
import subprocess


def check_python_version():
    """بررسی نسخه پایتون"""
    print("بررسی نسخه پایتون...")
    
    # نسخه فعلی پایتون
    current_version = sys.version_info
    print(f"نسخه پایتون فعلی: {current_version.major}.{current_version.minor}.{current_version.micro}")
    
    # حداقل نسخه موردنیاز
    min_version = (3, 10, 0)
    recommended_version = (3, 11, 0)
    
    if current_version < min_version:
        print(f"⚠️ هشدار: پایتون {current_version.major}.{current_version.minor} قدیمی است. حداقل نسخه 3.10 نیاز است.")
    elif current_version < recommended_version:
        print(f"✓ پایتون {current_version.major}.{current_version.minor} قابل قبول است، اما پایتون 3.11 توصیه می‌شود.")
    else:
        print(f"✓ پایتون {current_version.major}.{current_version.minor} مطلوب است.")


def read_requirements(filename="requirements.txt"):
    """خواندن وابستگی‌ها از فایل requirements.txt"""
    requirements = []
    try:
        with open(filename, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#'):
                    # حذف قسمت‌های بعد از # (کامنت‌ها)
                    if '#' in line:
                        line = line[:line.find('#')].strip()
                    # حذف قسمت‌های بعد از ; (محدودیت‌های محیطی)
                    if ';' in line:
                        line = line[:line.find(';')].strip()
                    requirements.append(line)
    except FileNotFoundError:
        print(f"⚠️ فایل {filename} یافت نشد!")
    return requirements


def check_installed_packages(required_packages):
    """بررسی پکیج‌های نصب شده"""
    print("\nبررسی پکیج‌های نصب شده...")
    
    missing_packages = []
    wrong_version_packages = []
    
    for package in required_packages:
        # جدا کردن نام پکیج و نسخه
        if "==" in package:
            package_name, required_version = package.split("==")
        else:
            package_name = package
            required_version = None
        
        # حذف قسمت‌های اضافی مانند [standard]
        if "[" in package_name:
            package_name = package_name[:package_name.find("[")]
        
        try:
            # بررسی نسخه پکیج
            installed_version = version(package_name)
            if required_version and installed_version != required_version:
                wrong_version_packages.append(
                    (package_name, installed_version, required_version)
                )
            else:
                print(f"✓ {package_name}{f' (نسخه {installed_version})' if installed_version else ''}")
        
        except PackageNotFoundError:
            missing_packages.append(package_name)
    
    # گزارش مشکلات
    if missing_packages:
        print("\n⚠️ پکیج‌های نصب نشده:")
        for package in missing_packages:
            print(f"  - {package}")
    
    if wrong_version_packages:
        print("\n⚠️ پکیج‌هایی با نسخه متفاوت:")
        for package, installed, required in wrong_version_packages:
            print(f"  - {package}: نصب شده {installed}, مورد نیاز {required}")


def check_module_imports():
    """بررسی import‌های ماژول‌های اصلی"""
    print("\nبررسی import‌های ماژول‌های اصلی...")
    
    core_modules = [
        "fastapi", "pydantic", "sqlalchemy", "httpx", "redis", 
        "asyncpg", "jwt", "pandas", "numpy"
    ]
    
    for module in core_modules:
        try:
            importlib.import_module(module)
            print(f"✓ {module} با موفقیت import شد")
        except ImportError as e:
            print(f"❌ خطا در import ماژول {module}: {e}")


def check_database_connection():
    """بررسی پیکربندی دیتابیس"""
    print("\nبررسی پیکربندی دیتابیس...")
    
    try:
        # بررسی وجود فایل .env
        from dotenv import load_dotenv
        import os
        
        load_dotenv()
        db_params = {
            "POSTGRES_SERVER": os.getenv("POSTGRES_SERVER"),
            "POSTGRES_USER": os.getenv("POSTGRES_USER"),
            "POSTGRES_PASSWORD": "***" if os.getenv("POSTGRES_PASSWORD") else None,
            "POSTGRES_DB": os.getenv("POSTGRES_DB")
        }
        
        missing_params = [k for k, v in db_params.items() if v is None]
        
        if missing_params:
            print(f"⚠️ پارامترهای دیتابیس در فایل .env موجود نیستند: {', '.join(missing_params)}")
        else:
            print(f"✓ پارامترهای دیتابیس در فایل .env یافت شدند")
            print(f"  - سرور: {db_params['POSTGRES_SERVER']}")
            print(f"  - کاربر: {db_params['POSTGRES_USER']}")
            print(f"  - دیتابیس: {db_params['POSTGRES_DB']}")
    
    except ImportError:
        print("❌ خطا در بارگذاری تنظیمات دیتابیس. ماژول dotenv نصب نشده است.")


def check_api_configurations():
    """بررسی پیکربندی API‌ها"""
    print("\nبررسی پیکربندی API‌ها...")
    
    try:
        from dotenv import load_dotenv
        import os
        
        load_dotenv()
        api_keys = {
            "TWITTER_API_KEY": "***" if os.getenv("TWITTER_API_KEY") else None,
            "CLAUDE_API_KEY": "***" if os.getenv("CLAUDE_API_KEY") else None
        }
        
        missing_keys = [k for k, v in api_keys.items() if v is None]
        
        if missing_keys:
            print(f"⚠️ کلیدهای API در فایل .env موجود نیستند: {', '.join(missing_keys)}")
        else:
            print(f"✓ کلیدهای API در فایل .env یافت شدند")
    
    except ImportError:
        print("❌ خطا در بارگذاری تنظیمات API. ماژول dotenv نصب نشده است.")


def main():
    """تابع اصلی"""
    print("="*50)
    print("بررسی سازگاری وابستگی‌های پروژه رصد")
    print("="*50)
    
    # بررسی نسخه پایتون
    check_python_version()
    
    # خواندن وابستگی‌ها
    requirements = read_requirements()
    
    # بررسی پکیج‌های نصب شده
    check_installed_packages(requirements)
    
    # بررسی import‌های ماژول
    check_module_imports()
    
    # بررسی پیکربندی‌ها
    check_database_connection()
    check_api_configurations()
    
    print("\n" + "="*50)
    print("بررسی سازگاری به پایان رسید")
    print("="*50)


if __name__ == "__main__":
    main()
