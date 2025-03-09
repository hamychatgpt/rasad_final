"""
اندپوینت‌های توییت‌ها.

این ماژول اندپوینت‌های مربوط به جستجو و مدیریت توییت‌ها را فراهم می‌کند.
"""

import logging
logger = logging.getLogger(__name__)

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
from app.services.processor.content_filter import ContentFilter

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


"""
اندپوینت‌های توییت‌ها.

این ماژول اندپوینت‌های مربوط به جستجو و مدیریت توییت‌ها را فراهم می‌کند.
"""

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import JSONResponse
from fastapi.encoders import jsonable_encoder
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import and_, or_, desc, func
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta

from app.db.session import get_db
from app.db.models import Tweet, User, Keyword, TweetKeyword
from app.schemas.tweet import TweetResponse, TweetFilterParams, KeywordCreate, KeywordResponse
from app.core.security import get_current_user
from app.db.models import AppUser
from app.services.processor.content_filter import ContentFilter

router = APIRouter(prefix="/tweets", tags=["tweets"])

# تغییرات نیاز نیست در کل فایل اعمال شود. فقط توابع مورد نظر را با توابع جدید جایگزین می‌کنیم

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
    try:
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

        # لاگ برای دیباگ
        logger.info(f"Found {len(keywords)} keywords in database")

        # تبدیل به فرمت پاسخ
        response_data = [
            {
                "id": keyword.id,
                "text": keyword.text,
                "is_active": keyword.is_active,
                "priority": keyword.priority,
                "description": keyword.description,
                "created_at": keyword.created_at
            }
            for keyword in keywords
        ]
        
        # برگرداندن پاسخ دستی با هدرهای CORS صریح
        return JSONResponse(
            content=jsonable_encoder(response_data),
            headers={
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Methods": "GET, POST, PUT, DELETE, OPTIONS",
                "Access-Control-Allow-Headers": "Content-Type, Authorization",
            }
        )

    except Exception as e:
        # لاگ خطا برای دیباگ
        logger.exception(f"Error getting keywords: {str(e)}")
        
        # برگرداندن پاسخ خطا با هدرهای CORS صریح
        return JSONResponse(
            status_code=500,
            content={"detail": f"خطا در دریافت کلیدواژه‌ها: {str(e)}"},
            headers={
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Methods": "GET, POST, PUT, DELETE, OPTIONS",
                "Access-Control-Allow-Headers": "Content-Type, Authorization",
            }
        )

@router.get("/debug/keywords", response_model=Dict[str, Any])
async def debug_keywords(
    db: AsyncSession = Depends(get_db)
):
    """
    اندپوینت دیباگ برای بررسی وضعیت کلیدواژه‌ها.
    
    این اندپوینت اطلاعات دیباگ مختلف را برای تشخیص مشکل در API کلیدواژه‌ها برمی‌گرداند.
    
    Args:
        db (AsyncSession): نشست دیتابیس
    
    Returns:
        Dict[str, Any]: اطلاعات دیباگ
    """
    response = {
        "status": "ok",
        "timestamp": datetime.utcnow().isoformat(),
        "tables": {},
        "keywords": [],
        "errors": []
    }
    
    try:
        # بررسی وجود جدول keywords
        try:
            from sqlalchemy import inspect
            inspector = inspect(db.bind)
            tables = inspector.get_table_names()
            response["tables"]["all_tables"] = tables
            response["tables"]["keywords_exists"] = "keywords" in tables
        except Exception as e:
            response["errors"].append(f"Error checking tables: {str(e)}")
        
        # بررسی تعداد رکوردها در جدول keywords
        try:
            stmt = select(func.count()).select_from(Keyword)
            result = await db.execute(stmt)
            count = result.scalar() or 0
            response["tables"]["keywords_count"] = count
        except Exception as e:
            response["errors"].append(f"Error counting keywords: {str(e)}")
        
        # دریافت کلیدواژه‌ها
        try:
            stmt = select(Keyword).order_by(Keyword.priority.desc())
            result = await db.execute(stmt)
            keywords = result.scalars().all()
            
            response["keywords"] = [
                {
                    "id": keyword.id,
                    "text": keyword.text,
                    "is_active": keyword.is_active,
                    "priority": keyword.priority,
                    "description": keyword.description,
                    "created_at": keyword.created_at.isoformat() if keyword.created_at else None
                }
                for keyword in keywords
            ]
        except Exception as e:
            response["errors"].append(f"Error fetching keywords: {str(e)}")
    
    except Exception as e:
        response["status"] = "error"
        response["errors"].append(f"Unexpected error: {str(e)}")
    
    return response

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


@router.post("/keywords/extract", response_model=List[str])
async def extract_keywords_from_text(
    request: Dict[str, str],
    db: AsyncSession = Depends(get_db),
    current_user: AppUser = Depends(get_current_user)
):
    """
    استخراج خودکار کلیدواژه‌ها از متن.
    
    Args:
        request (Dict[str, str]): متن برای استخراج کلیدواژه‌ها
        db (AsyncSession): نشست دیتابیس
        current_user (AppUser): کاربر فعلی
    
    Returns:
        List[str]: لیست کلیدواژه‌های استخراج شده
    """
    text = request.get("text", "")
    max_keywords = int(request.get("max_keywords", 10))
    
    if not text:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="متن برای استخراج کلیدواژه ارائه نشده است",
        )
    
    # استفاده از ContentFilter برای استخراج کلیدواژه‌ها
    content_filter = ContentFilter()
    keywords = content_filter.extract_keywords(text, max_keywords=max_keywords)
    
    return keywords


@router.get("/keywords/stats", response_model=List[Dict[str, Any]])
async def get_keywords_stats(
    days: int = 7,
    db: AsyncSession = Depends(get_db),
    current_user: AppUser = Depends(get_current_user)
):
    """
    دریافت آمار استفاده از کلیدواژه‌ها.
    
    Args:
        days (int): تعداد روزهای اخیر
        db (AsyncSession): نشست دیتابیس
        current_user (AppUser): کاربر فعلی
    
    Returns:
        List[Dict[str, Any]]: آمار کلیدواژه‌ها
    """
    # محاسبه تاریخ شروع
    start_date = datetime.now() - timedelta(days=days)
    
    # استخراج تعداد توییت‌ها برای هر کلیدواژه
    stmt = select(
        Keyword.id,
        Keyword.text,
        func.count(TweetKeyword.tweet_id).label("tweet_count")
    ).outerjoin(
        TweetKeyword, Keyword.id == TweetKeyword.keyword_id
    ).outerjoin(
        Tweet, Tweet.id == TweetKeyword.tweet_id
    ).where(
        and_(
            Keyword.is_active == True,
            or_(
                Tweet.created_at >= start_date,
                Tweet.created_at == None
            )
        )
    ).group_by(
        Keyword.id, Keyword.text
    ).order_by(
        func.count(TweetKeyword.tweet_id).desc()
    )
    
    result = await db.execute(stmt)
    keywords_stats = []
    
    for row in result.fetchall():
        keyword_id, keyword_text, tweet_count = row
        
        # استخراج آمار احساسات برای هر کلیدواژه
        sentiment_stmt = select(
            Tweet.sentiment_label,
            func.count().label("count")
        ).join(
            TweetKeyword, Tweet.id == TweetKeyword.tweet_id
        ).where(
            and_(
                TweetKeyword.keyword_id == keyword_id,
                Tweet.created_at >= start_date,
                Tweet.sentiment_label != None
            )
        ).group_by(
            Tweet.sentiment_label
        )
        
        sentiment_result = await db.execute(sentiment_stmt)
        sentiment_stats = {
            row[0]: row[1] for row in sentiment_result.fetchall()
        }
        
        keywords_stats.append({
            "id": keyword_id,
            "text": keyword_text,
            "tweet_count": tweet_count,
            "sentiment_stats": sentiment_stats
        })
    
    return keywords_stats