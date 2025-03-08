"""
مدل‌های داده احراز هویت.

این ماژول مدل‌های Pydantic مربوط به احراز هویت را تعریف می‌کند.
"""

from pydantic import BaseModel, EmailStr, Field, validator
from typing import Optional


class UserBase(BaseModel):
    """
    مدل پایه کاربر.

    Attributes:
        email (EmailStr): ایمیل کاربر
        full_name (str): نام کامل کاربر
    """
    email: EmailStr
    full_name: Optional[str] = None


class UserCreate(UserBase):
    """
    مدل ایجاد کاربر.

    Attributes:
        password (str): رمز عبور کاربر
    """
    password: str

    @validator('password')
    def password_strength(cls, v):
        """بررسی قدرت رمز عبور"""
        if len(v) < 8:
            raise ValueError('رمز عبور باید حداقل 8 کاراکتر باشد')
        if not any(c.isdigit() for c in v):
            raise ValueError('رمز عبور باید شامل حداقل یک عدد باشد')
        if not any(c.isalpha() for c in v):
            raise ValueError('رمز عبور باید شامل حداقل یک حرف باشد')
        return v


class UserUpdate(BaseModel):
    """
    مدل بروزرسانی کاربر.

    Attributes:
        email (EmailStr): ایمیل کاربر
        full_name (str): نام کامل کاربر
        password (str): رمز عبور جدید
        is_active (bool): وضعیت فعال بودن کاربر
    """
    email: Optional[EmailStr] = None
    full_name: Optional[str] = None
    password: Optional[str] = None
    is_active: Optional[bool] = None

    @validator('password')
    def password_strength(cls, v):
        """بررسی قدرت رمز عبور"""
        if v is None:
            return v
        if len(v) < 8:
            raise ValueError('رمز عبور باید حداقل 8 کاراکتر باشد')
        if not any(c.isdigit() for c in v):
            raise ValueError('رمز عبور باید شامل حداقل یک عدد باشد')
        if not any(c.isalpha() for c in v):
            raise ValueError('رمز عبور باید شامل حداقل یک حرف باشد')
        return v


class UserInDB(UserBase):
    """
    مدل کاربر در دیتابیس.

    Attributes:
        id (int): شناسه کاربر
        is_active (bool): وضعیت فعال بودن کاربر
        is_superuser (bool): وضعیت مدیر سیستم بودن کاربر
        hashed_password (str): رمز عبور هش شده
    """
    id: int
    is_active: bool
    is_superuser: bool
    hashed_password: str


class User(UserBase):
    """
    مدل کاربر.

    Attributes:
        id (int): شناسه کاربر
        is_active (bool): وضعیت فعال بودن کاربر
        is_superuser (bool): وضعیت مدیر سیستم بودن کاربر
    """
    id: int
    is_active: bool
    is_superuser: bool

    class Config:
        orm_mode = True


class Token(BaseModel):
    """
    مدل توکن دسترسی.

    Attributes:
        access_token (str): توکن دسترسی
        token_type (str): نوع توکن
    """
    access_token: str
    token_type: str


class TokenPayload(BaseModel):
    """
    مدل محتوای توکن.

    Attributes:
        sub (str): موضوع توکن (معمولاً ایمیل کاربر)
        exp (int): زمان انقضای توکن
    """
    sub: Optional[str] = None
    exp: Optional[int] = None


class LoginForm(BaseModel):
    """
    مدل فرم ورود.

    Attributes:
        username (str): نام کاربری (ایمیل)
        password (str): رمز عبور
    """
    username: str  # OAuth2 استاندارد از نام username استفاده می‌کند
    password: str


class ChangePasswordForm(BaseModel):
    """
    مدل فرم تغییر رمز عبور.

    Attributes:
        current_password (str): رمز عبور فعلی
        new_password (str): رمز عبور جدید
    """
    current_password: str
    new_password: str

    @validator('new_password')
    def password_strength(cls, v, values):
        """بررسی قدرت رمز عبور و متفاوت بودن با رمز فعلی"""
        if len(v) < 8:
            raise ValueError('رمز عبور جدید باید حداقل 8 کاراکتر باشد')
        if not any(c.isdigit() for c in v):
            raise ValueError('رمز عبور جدید باید شامل حداقل یک عدد باشد')
        if not any(c.isalpha() for c in v):
            raise ValueError('رمز عبور جدید باید شامل حداقل یک حرف باشد')
        if 'current_password' in values and v == values['current_password']:
            raise ValueError('رمز عبور جدید نباید با رمز عبور فعلی یکسان باشد')
        return v
