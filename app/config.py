"""
ماژول تنظیمات پروژه رصد.

این ماژول تنظیمات و متغیرهای محیطی مورد نیاز پروژه را فراهم می‌کند.
از Pydantic Settings برای مدیریت و اعتبارسنجی تنظیمات استفاده می‌کند.
"""

import os
import secrets
from typing import List, Optional, Union
from pydantic import AnyHttpUrl, PostgresDsn, field_validator, ValidationInfo
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """
    تنظیمات پروژه رصد

    این کلاس تنظیمات پروژه را از متغیرهای محیطی خوانده و اعتبارسنجی می‌کند.
    """

    # تنظیمات عمومی
    PROJECT_NAME: str = "Rasad"
    API_V1_STR: str = "/api/v1"
    SECRET_KEY: str = os.getenv("SECRET_KEY", secrets.token_urlsafe(32))
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7
    DEBUG: bool = os.getenv("DEBUG", "False").lower() in ("true", "1", "t")

    # CORS
    CORS_ORIGINS: Union[str, List[AnyHttpUrl]] = os.getenv("CORS_ORIGINS",
                                                           "http://localhost,http://localhost:3000,http://localhost:8000,http://127.0.0.1:3000,http://127.0.0.1:8000")

    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def validate_cors_origins(cls, v: Union[str, List[str]]) -> List[str]:
        """اعتبارسنجی آدرس‌های CORS"""
        if isinstance(v, str):
            return [item.strip() for item in v.split(",")]
        return v

    # دیتابیس
    POSTGRES_SERVER: str = os.getenv("POSTGRES_SERVER", "localhost")
    POSTGRES_USER: str = os.getenv("POSTGRES_USER", "postgres")
    POSTGRES_PASSWORD: str = os.getenv("POSTGRES_PASSWORD", "postgres")
    POSTGRES_DB: str = os.getenv("POSTGRES_DB", "rasad")
    SQLALCHEMY_DATABASE_URI: Optional[str] = None

    @field_validator("SQLALCHEMY_DATABASE_URI", mode="before")
    @classmethod
    def assemble_db_connection(cls, v: Optional[str], info: ValidationInfo) -> str:
        """ساخت آدرس اتصال به دیتابیس"""
        if isinstance(v, str) and v:
            return v

        values = info.data
        return str(
            PostgresDsn.build(
                scheme="postgresql+asyncpg",
                username=values.get("POSTGRES_USER"),
                password=values.get("POSTGRES_PASSWORD"),
                host=values.get("POSTGRES_SERVER"),
                path=f"{values.get('POSTGRES_DB') or ''}",
            )
        )

    # Redis
    REDIS_HOST: str = os.getenv("REDIS_HOST", "localhost")
    REDIS_PORT: int = int(os.getenv("REDIS_PORT", "6379"))
    REDIS_URL: str = os.getenv("REDIS_URL", f"redis://{REDIS_HOST}:{REDIS_PORT}/0")

    # Twitter API
    TWITTER_API_KEY: str = os.getenv("TWITTER_API_KEY", "")
    TWITTER_API_BASE_URL: str = os.getenv("TWITTER_API_BASE_URL", "https://api.twitterapi.io")

    # Claude API
    CLAUDE_API_KEY: str = os.getenv("CLAUDE_API_KEY", "")
    CLAUDE_MODEL: str = os.getenv("CLAUDE_MODEL", "claude-3-7-sonnet-20250219")

    # تنظیمات تحلیل
    DAILY_BUDGET: float = float(os.getenv("DAILY_BUDGET", "10.0"))
    ANALYZER_BATCH_SIZE: int = int(os.getenv("ANALYZER_BATCH_SIZE", "50"))

    # تنظیمات سرویس‌ها
    SERVICE_RETRY_MAX: int = 3
    SERVICE_RETRY_DELAY: int = 5

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True


# ایجاد نمونه سراسری از تنظیمات
settings = Settings()
