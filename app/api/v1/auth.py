"""
اندپوینت‌های احراز هویت و مدیریت کاربران.

این ماژول اندپوینت‌های مربوط به ورود، ثبت‌نام، و مدیریت کاربران سیستم را فراهم می‌کند.
"""
from app.config import settings

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from datetime import timedelta

from app.db.session import get_db
from app.db.models import AppUser
from app.core.security import (
    get_password_hash, verify_password, create_access_token,
    get_current_user, get_current_superuser
)
from app.schemas.auth import UserCreate, UserUpdate, User, Token

router = APIRouter(prefix="/auth", tags=["authentication"])


@router.post("/login", response_model=Token)
async def login(
        form_data: OAuth2PasswordRequestForm = Depends(),
        db: AsyncSession = Depends(get_db)
):
    """
    ورود به سیستم و دریافت توکن JWT.

    Args:
        form_data (OAuth2PasswordRequestForm): فرم ورود
        db (AsyncSession): نشست دیتابیس

    Returns:
        Token: توکن دسترسی

    Raises:
        HTTPException: در صورت نامعتبر بودن نام کاربری یا رمز عبور
    """
    # جستجوی کاربر در دیتابیس
    stmt = select(AppUser).where(AppUser.email == form_data.username)
    result = await db.execute(stmt)
    user = result.scalar_one_or_none()

    # بررسی وجود کاربر و صحت رمز عبور
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="نام کاربری یا رمز عبور نادرست است",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # بررسی فعال بودن کاربر
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="حساب کاربری غیرفعال است",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # ایجاد توکن دسترسی
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.email},
        expires_delta=access_token_expires
    )

    return {"access_token": access_token, "token_type": "bearer"}


@router.post("/register", response_model=User)
async def register(
        user_in: UserCreate,
        db: AsyncSession = Depends(get_db),
        current_superuser: AppUser = Depends(get_current_superuser)
):
    """
    ثبت‌نام کاربر جدید (فقط مدیران سیستم).

    Args:
        user_in (UserCreate): اطلاعات کاربر جدید
        db (AsyncSession): نشست دیتابیس
        current_superuser (AppUser): کاربر فعلی (باید مدیر سیستم باشد)

    Returns:
        User: کاربر ایجاد شده

    Raises:
        HTTPException: در صورت تکراری بودن ایمیل
    """
    # بررسی تکراری نبودن ایمیل
    stmt = select(AppUser).where(AppUser.email == user_in.email)
    result = await db.execute(stmt)
    existing_user = result.scalar_one_or_none()

    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="این ایمیل قبلاً ثبت شده است",
        )

    # ایجاد کاربر جدید
    hashed_password = get_password_hash(user_in.password)
    user = AppUser(
        email=user_in.email,
        hashed_password=hashed_password,
        full_name=user_in.full_name,
        is_active=True,
        is_superuser=False  # کاربران جدید به صورت پیش‌فرض مدیر نیستند
    )

    db.add(user)
    await db.commit()
    await db.refresh(user)

    return user


@router.get("/me", response_model=User)
async def read_users_me(current_user: AppUser = Depends(get_current_user)):
    """
    دریافت اطلاعات کاربر فعلی.

    Args:
        current_user (AppUser): کاربر فعلی

    Returns:
        User: اطلاعات کاربر فعلی
    """
    return current_user


@router.put("/me", response_model=User)
async def update_user_me(
        user_in: UserUpdate,
        current_user: AppUser = Depends(get_current_user),
        db: AsyncSession = Depends(get_db)
):
    """
    به‌روزرسانی اطلاعات کاربر فعلی.

    Args:
        user_in (UserUpdate): اطلاعات به‌روزرسانی
        current_user (AppUser): کاربر فعلی
        db (AsyncSession): نشست دیتابیس

    Returns:
        User: اطلاعات به‌روزرسانی شده کاربر
    """
    # به‌روزرسانی اطلاعات کاربر
    if user_in.password:
        current_user.hashed_password = get_password_hash(user_in.password)
    if user_in.full_name:
        current_user.full_name = user_in.full_name
    if user_in.email:
        # بررسی تکراری نبودن ایمیل جدید
        if user_in.email != current_user.email:
            stmt = select(AppUser).where(AppUser.email == user_in.email)
            result = await db.execute(stmt)
            existing_user = result.scalar_one_or_none()

            if existing_user:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="این ایمیل قبلاً ثبت شده است",
                )

            current_user.email = user_in.email

    await db.commit()
    await db.refresh(current_user)

    return current_user


@router.get("/users", response_model=list[User])
async def read_users(
        skip: int = 0,
        limit: int = 100,
        db: AsyncSession = Depends(get_db),
        current_superuser: AppUser = Depends(get_current_superuser)
):
    """
    دریافت لیست کاربران (فقط مدیران سیستم).

    Args:
        skip (int): تعداد آیتم‌های رد شده
        limit (int): حداکثر تعداد آیتم‌ها
        db (AsyncSession): نشست دیتابیس
        current_superuser (AppUser): کاربر فعلی (باید مدیر سیستم باشد)

    Returns:
        list[User]: لیست کاربران
    """
    stmt = select(AppUser).offset(skip).limit(limit)
    result = await db.execute(stmt)
    users = result.scalars().all()

    return users


@router.get("/users/{user_id}", response_model=User)
async def read_user(
        user_id: int,
        db: AsyncSession = Depends(get_db),
        current_superuser: AppUser = Depends(get_current_superuser)
):
    """
    دریافت اطلاعات یک کاربر (فقط مدیران سیستم).

    Args:
        user_id (int): شناسه کاربر
        db (AsyncSession): نشست دیتابیس
        current_superuser (AppUser): کاربر فعلی (باید مدیر سیستم باشد)

    Returns:
        User: اطلاعات کاربر

    Raises:
        HTTPException: در صورت یافت نشدن کاربر
    """
    stmt = select(AppUser).where(AppUser.id == user_id)
    result = await db.execute(stmt)
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="کاربر یافت نشد",
        )

    return user


@router.put("/users/{user_id}", response_model=User)
async def update_user(
        user_id: int,
        user_in: UserUpdate,
        db: AsyncSession = Depends(get_db),
        current_superuser: AppUser = Depends(get_current_superuser)
):
    """
    به‌روزرسانی اطلاعات یک کاربر (فقط مدیران سیستم).

    Args:
        user_id (int): شناسه کاربر
        user_in (UserUpdate): اطلاعات به‌روزرسانی
        db (AsyncSession): نشست دیتابیس
        current_superuser (AppUser): کاربر فعلی (باید مدیر سیستم باشد)

    Returns:
        User: اطلاعات به‌روزرسانی شده کاربر

    Raises:
        HTTPException: در صورت یافت نشدن کاربر
    """
    # یافتن کاربر
    stmt = select(AppUser).where(AppUser.id == user_id)
    result = await db.execute(stmt)
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="کاربر یافت نشد",
        )

    # به‌روزرسانی اطلاعات کاربر
    if user_in.password:
        user.hashed_password = get_password_hash(user_in.password)
    if user_in.full_name is not None:
        user.full_name = user_in.full_name
    if user_in.email is not None:
        # بررسی تکراری نبودن ایمیل جدید
        if user_in.email != user.email:
            stmt = select(AppUser).where(AppUser.email == user_in.email)
            result = await db.execute(stmt)
            existing_user = result.scalar_one_or_none()

            if existing_user:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="این ایمیل قبلاً ثبت شده است",
                )

            user.email = user_in.email
    if user_in.is_active is not None:
        user.is_active = user_in.is_active
    if user_in.is_superuser is not None:
        user.is_superuser = user_in.is_superuser

    await db.commit()
    await db.refresh(user)

    return user