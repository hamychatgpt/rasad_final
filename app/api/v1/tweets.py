"""
اندپوینت‌های توییت‌ها.

این ماژول اندپوینت‌های مربوط به جستجو و مدیریت توییت‌ها را فراهم می‌کند.
"""

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import and_, or_, desc, func
from typing import List, Optional, Dict, Any

from app.db.session import get_db
from app.db.models import Tweet, User, Keyword, TweetKeyword
from app.schemas.tweet import TweetResponse, TweetFilterParams, KeywordCreate, KeywordResponse
from app.core.security import get_current_user
from app.db.models import AppUser

router = APIRouter(prefix="/tweets", tags=["tweets"])


@router.get("/", response_model=List[TweetResponse])
async def get_tweets(
        params: TweetFilterParams = Depends(),
        db: AsyncSession = Depends(get_db),
        current_user: AppUser = Depends(get_current_user)
):
    """
    دریافت لیست توییت‌ها با امکان فیلتر کردن.

    Args:
        params (TweetFilterParams): پارامترهای فیلتر
        db (AsyncSession): نشست دیتابیس
        current_user (AppUser): کاربر فعلی

    Returns:
        List[TweetResponse]: لیست توییت‌ها
    """
    # ایجاد query پایه
    query = select(Tweet).join(User, Tweet.user_id == User.user_id, isouter=True)

    # اعمال فیلترها
    filters = []

    # فیلتر براساس متن
    if params.query:
        filters.append(Tweet.content.ilike(f"%{params.query}%"))

    # فیلتر براساس احساسات
    if params.sentiment:
        filters.append(Tweet.sentiment_label == params.sentiment)

    # فیلتر براساس کلیدواژه‌ها
    if params.keywords:
        keyword_subquery = select(TweetKeyword.tweet_id).join(
            Keyword, TweetKeyword.keyword_id == Keyword.id
        ).where(Keyword.text.in_(params.keywords))
        filters.append(Tweet.id.in_(keyword_subquery))

    # فیلتر براساس بازه زمانی
    if params.start_date:
        filters.append(Tweet.created_at >= params.start_date)
    if params.end_date:
        filters.append(Tweet.created_at <= params.end_date)

    # فیلتر براساس امتیاز اهمیت
    if params.min_importance:
        filters.append(Tweet.importance_score >= params.min_importance)

    # ترکیب فیلترها
    if filters:
        query = query.where(and_(*filters))

    # مرتب‌سازی
    if params.sort_by == "date":
        query = query.order_by(desc(Tweet.created_at))
    elif params.sort_by == "importance":
        query = query.order_by(desc(Tweet.importance_score))
    elif params.sort_by == "sentiment":
        query = query.order_by(Tweet.sentiment_score.desc())
    else:
        query = query.order_by(desc(Tweet.created_at))

    # صفحه‌بندی
    query = query.offset(params.skip).limit(params.limit)

    # اجرای query
    result = await db.execute(query)
    tweets = result.scalars().all()

    # تبدیل به فرمت پاسخ
    return [
        TweetResponse(
            id=tweet.id,
            tweet_id=tweet.tweet_id,
            content=tweet.content,
            created_at=tweet.created_at,
            language=tweet.language,
            user=tweet.user,
            sentiment_label=tweet.sentiment_label,
            sentiment_score=tweet.sentiment_score,
            importance_score=tweet.importance_score,
            is_processed=tweet.is_processed,
            is_analyzed=tweet.is_analyzed,
            entities=tweet.entities
        )
        for tweet in tweets
    ]


@router.get("/count", response_model=Dict[str, Any])
async def get_tweets_count(
        params: TweetFilterParams = Depends(),
        db: AsyncSession = Depends(get_db),
        current_user: AppUser = Depends(get_current_user)
):
    """
    دریافت تعداد توییت‌ها با امکان فیلتر کردن.

    Args:
        params (TweetFilterParams): پارامترهای فیلتر
        db (AsyncSession): نشست دیتابیس
        current_user (AppUser): کاربر فعلی

    Returns:
        Dict[str, Any]: تعداد توییت‌ها و آمار احساسات
    """
    # ایجاد query پایه
    query = select(func.count(),
                   func.count().filter(Tweet.sentiment_label == "positive"),
                   func.count().filter(Tweet.sentiment_label == "negative"),
                   func.count().filter(Tweet.sentiment_label == "neutral"),
                   func.count().filter(Tweet.sentiment_label == "mixed")
                   ).select_from(Tweet)

    # اعمال فیلترها (مشابه با تابع get_tweets)
    filters = []

    # فیلتر براساس متن
    if params.query:
        filters.append(Tweet.content.ilike(f"%{params.query}%"))

    # فیلتر براساس احساسات
    if params.sentiment:
        filters.append(Tweet.sentiment_label == params.sentiment)

    # فیلتر براساس کلیدواژه‌ها
    if params.keywords:
        keyword_subquery = select(TweetKeyword.tweet_id).join(
            Keyword, TweetKeyword.keyword_id == Keyword.id
        ).where(Keyword.text.in_(params.keywords))
        filters.append(Tweet.id.in_(keyword_subquery))

    # فیلتر براساس بازه زمانی
    if params.start_date:
        filters.append(Tweet.created_at >= params.start_date)
    if params.end_date:
        filters.append(Tweet.created_at <= params.end_date)

    # فیلتر براساس امتیاز اهمیت
    if params.min_importance:
        filters.append(Tweet.importance_score >= params.min_importance)

    # ترکیب فیلترها
    if filters:
        query = query.where(and_(*filters))

    # اجرای query
    result = await db.execute(query)
    counts = result.fetchone()

    return {
        "total": counts[0],
        "sentiment_counts": {
            "positive": counts[1],
            "negative": counts[2],
            "neutral": counts[3],
            "mixed": counts[4]
        }
    }


@router.get("/{tweet_id}", response_model=TweetResponse)
async def get_tweet(
        tweet_id: int,
        db: AsyncSession = Depends(get_db),
        current_user: AppUser = Depends(get_current_user)
):
    """
    دریافت اطلاعات یک توییت.

    Args:
        tweet_id (int): شناسه توییت
        db (AsyncSession): نشست دیتابیس
        current_user (AppUser): کاربر فعلی

    Returns:
        TweetResponse: اطلاعات توییت

    Raises:
        HTTPException: در صورت یافت نشدن توییت
    """
    # دریافت توییت از دیتابیس
    stmt = select(Tweet).where(Tweet.id == tweet_id)
    result = await db.execute(stmt)
    tweet = result.scalar_one_or_none()

    if not tweet:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="توییت یافت نشد",
        )

    return TweetResponse(
        id=tweet.id,
        tweet_id=tweet.tweet_id,
        content=tweet.content,
        created_at=tweet.created_at,
        language=tweet.language,
        user=tweet.user,
        sentiment_label=tweet.sentiment_label,
        sentiment_score=tweet.sentiment_score,
        importance_score=tweet.importance_score,
        is_processed=tweet.is_processed,
        is_analyzed=tweet.is_analyzed,
        entities=tweet.entities
    )


@router.get("/keywords", response_model=List[KeywordResponse])
async def get_keywords(
        skip: int = 0,
        limit: int = 100,
        active_only: bool = False,
        db: AsyncSession = Depends(get_db),
        current_user: AppUser = Depends(get_current_user)
):
    """
    دریافت لیست کلیدواژه‌ها.

    Args:
        skip (int): تعداد آیتم‌های رد شده
        limit (int): حداکثر تعداد آیتم‌ها
        active_only (bool): فقط کلیدواژه‌های فعال
        db (AsyncSession): نشست دیتابیس
        current_user (AppUser): کاربر فعلی

    Returns:
        List[KeywordResponse]: لیست کلیدواژه‌ها
    """
    # ایجاد query پایه
    query = select(Keyword)

    # فیلتر براساس وضعیت فعال
    if active_only:
        query = query.where(Keyword.is_active == True)

    # صفحه‌بندی و مرتب‌سازی
    query = query.order_by(Keyword.priority.desc()).offset(skip).limit(limit)

    # اجرای query
    result = await db.execute(query)
    keywords = result.scalars().all()

    return [
        KeywordResponse(
            id=keyword.id,
            text=keyword.text,
            is_active=keyword.is_active,
            priority=keyword.priority,
            description=keyword.description,
            created_at=keyword.created_at
        )
        for keyword in keywords
    ]


@router.post("/keywords", response_model=KeywordResponse)
async def create_keyword(
        keyword_in: KeywordCreate,
        db: AsyncSession = Depends(get_db),
        current_user: AppUser = Depends(get_current_user)
):
    """
    ایجاد کلیدواژه جدید.

    Args:
        keyword_in (KeywordCreate): اطلاعات کلیدواژه جدید
        db (AsyncSession): نشست دیتابیس
        current_user (AppUser): کاربر فعلی

    Returns:
        KeywordResponse: کلیدواژه ایجاد شده

    Raises:
        HTTPException: در صورت تکراری بودن کلیدواژه
    """
    # بررسی تکراری نبودن کلیدواژه
    stmt = select(Keyword).where(Keyword.text == keyword_in.text)
    result = await db.execute(stmt)
    existing_keyword = result.scalar_one_or_none()

    if existing_keyword:
        # اگر کلیدواژه وجود دارد، آن را فعال می‌کنیم
        if not existing_keyword.is_active:
            existing_keyword.is_active = True
            existing_keyword.priority = keyword_in.priority
            existing_keyword.description = keyword_in.description
            await db.commit()
            await db.refresh(existing_keyword)

        return KeywordResponse(
            id=existing_keyword.id,
            text=existing_keyword.text,
            is_active=existing_keyword.is_active,
            priority=existing_keyword.priority,
            description=existing_keyword.description,
            created_at=existing_keyword.created_at
        )

    # ایجاد کلیدواژه جدید
    keyword = Keyword(
        text=keyword_in.text,
        is_active=True,
        priority=keyword_in.priority,
        description=keyword_in.description
    )

    db.add(keyword)
    await db.commit()
    await db.refresh(keyword)

    return KeywordResponse(
        id=keyword.id,
        text=keyword.text,
        is_active=keyword.is_active,
        priority=keyword.priority,
        description=keyword.description,
        created_at=keyword.created_at
    )


@router.put("/keywords/{keyword_id}", response_model=KeywordResponse)
async def update_keyword(
        keyword_id: int,
        keyword_in: KeywordCreate,
        db: AsyncSession = Depends(get_db),
        current_user: AppUser = Depends(get_current_user)
):
    """
    به‌روزرسانی کلیدواژه.

    Args:
        keyword_id (int): شناسه کلیدواژه
        keyword_in (KeywordCreate): اطلاعات به‌روزرسانی
        db (AsyncSession): نشست دیتابیس
        current_user (AppUser): کاربر فعلی

    Returns:
        KeywordResponse: کلیدواژه به‌روزرسانی شده

    Raises:
        HTTPException: در صورت یافت نشدن کلیدواژه
    """
    # یافتن کلیدواژه
    stmt = select(Keyword).where(Keyword.id == keyword_id)
    result = await db.execute(stmt)
    keyword = result.scalar_one_or_none()

    if not keyword:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="کلیدواژه یافت نشد",
        )

    # به‌روزرسانی کلیدواژه
    keyword.text = keyword_in.text
    keyword.is_active = keyword_in.is_active
    keyword.priority = keyword_in.priority
    keyword.description = keyword_in.description

    await db.commit()
    await db.refresh(keyword)

    return KeywordResponse(
        id=keyword.id,
        text=keyword.text,
        is_active=keyword.is_active,
        priority=keyword.priority,
        description=keyword.description,
        created_at=keyword.created_at
    )


@router.delete("/keywords/{keyword_id}", response_model=Dict[str, Any])
async def delete_keyword(
        keyword_id: int,
        db: AsyncSession = Depends(get_db),
        current_user: AppUser = Depends(get_current_user)
):
    """
    حذف کلیدواژه.

    Args:
        keyword_id (int): شناسه کلیدواژه
        db (AsyncSession): نشست دیتابیس
        current_user (AppUser): کاربر فعلی

    Returns:
        Dict[str, Any]: پیام موفقیت

    Raises:
        HTTPException: در صورت یافت نشدن کلیدواژه
    """
    # یافتن کلیدواژه
    stmt = select(Keyword).where(Keyword.id == keyword_id)
    result = await db.execute(stmt)
    keyword = result.scalar_one_or_none()

    if not keyword:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="کلیدواژه یافت نشد",
        )

    # به جای حذف فیزیکی، فقط غیرفعال می‌کنیم
    keyword.is_active = False

    await db.commit()

    return {"message": "کلیدواژه با موفقیت غیرفعال شد"}