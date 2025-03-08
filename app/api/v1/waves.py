"""
اندپوینت‌های موج‌ها و هشدارها.

این ماژول اندپوینت‌های مربوط به تشخیص موج‌های توییتری و مدیریت هشدارها را فراهم می‌کند.
"""

from fastapi import APIRouter, Depends, HTTPException, Query, status, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import update, and_, or_, desc, func
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any

from app.db.session import get_db
from app.db.models import Alert, Tweet, AppUser
from app.schemas.wave import (
    AlertResponse, AlertFilterParams, WaveResponse, WaveDetectionRequest,
    WaveAnalysisResponse
)
from app.core.security import get_current_user
from app.services.analyzer.analyzer import TweetAnalyzer
from app.services.analyzer.wave_detector import WaveDetector

router = APIRouter(prefix="/waves", tags=["waves"])


async def get_wave_detector(db: AsyncSession = Depends(get_db)) -> WaveDetector:
    """
    وابستگی برای دریافت یک نمونه از WaveDetector.

    Args:
        db (AsyncSession): نشست دیتابیس

    Returns:
        WaveDetector: یک نمونه از WaveDetector
    """
    return WaveDetector(db)


async def get_analyzer(db: AsyncSession = Depends(get_db)) -> TweetAnalyzer:
    """
    وابستگی برای دریافت یک نمونه از TweetAnalyzer.

    Args:
        db (AsyncSession): نشست دیتابیس

    Returns:
        TweetAnalyzer: یک نمونه از TweetAnalyzer
    """
    # ایجاد وابستگی‌ها
    from app.services.analyzer.claude_client import ClaudeClient
    from app.services.analyzer.cost_manager import CostManager

    claude_client = ClaudeClient()
    cost_manager = CostManager(db)
    wave_detector = await get_wave_detector(db)

    analyzer = TweetAnalyzer(
        db_session=db,
        claude_client=claude_client,
        cost_manager=cost_manager,
        wave_detector=wave_detector
    )

    await analyzer.initialize()

    return analyzer


@router.get("/detect", response_model=List[WaveResponse])
async def detect_waves(
        keywords: Optional[List[str]] = Query(None),
        hours_back: int = 24,
        min_importance: float = 3.0,
        wave_type: Optional[str] = None,
        db: AsyncSession = Depends(get_db),
        current_user: AppUser = Depends(get_current_user),
        wave_detector: WaveDetector = Depends(get_wave_detector)
):
    """
    تشخیص موج‌های توییتری.

    Args:
        keywords (Optional[List[str]]): کلیدواژه‌ها برای فیلتر کردن
        hours_back (int): تعداد ساعات برای بررسی
        min_importance (float): حداقل امتیاز اهمیت
        wave_type (Optional[str]): نوع موج (volume, sentiment)
        db (AsyncSession): نشست دیتابیس
        current_user (AppUser): کاربر فعلی
        wave_detector (WaveDetector): سرویس تشخیص موج

    Returns:
        List[WaveResponse]: لیست موج‌های تشخیص داده شده
    """
    # تشخیص موج‌ها
    if wave_type == "volume":
        waves = await wave_detector.detect_volume_waves(keywords, hours_back)
    elif wave_type == "sentiment":
        waves = await wave_detector.detect_sentiment_waves(keywords, hours_back)
    else:
        waves = await wave_detector.detect_all_waves(keywords, hours_back)

    # فیلتر کردن براساس امتیاز اهمیت
    waves = [w for w in waves if w.get("importance_score", 0) >= min_importance]

    # تبدیل به فرمت پاسخ
    responses = []
    for wave in waves:
        response = WaveResponse(
            type=wave.get("type", "unknown"),
            start_time=wave.get("start_time"),
            end_time=wave.get("end_time"),
            tweet_count=wave.get("tweet_count", 0),
            growth_rate=wave.get("growth_rate", 0) if wave.get("type") == "volume" else None,
            sentiment_shift=wave.get("sentiment_shift", 0) if wave.get("type") == "sentiment" else None,
            avg_sentiment=wave.get("avg_sentiment", 0),
            sentiment_distribution=wave.get("sentiment_distribution", {}),
            importance_score=wave.get("importance_score", 0),
            related_keywords=wave.get("related_keywords", []),
            top_tweets=wave.get("top_tweets", [])[:5]  # فقط 5 توییت برتر
        )
        responses.append(response)

    return responses


@router.post("/detect_and_alert", response_model=List[Dict[str, Any]])
async def detect_waves_and_create_alerts(
        request: WaveDetectionRequest,
        db: AsyncSession = Depends(get_db),
        current_user: AppUser = Depends(get_current_user),
        analyzer: TweetAnalyzer = Depends(get_analyzer)
):
    """
    تشخیص موج‌ها و ایجاد هشدار.

    Args:
        request (WaveDetectionRequest): درخواست تشخیص موج
        db (AsyncSession): نشست دیتابیس
        current_user (AppUser): کاربر فعلی
        analyzer (TweetAnalyzer): سرویس تحلیل

    Returns:
        List[Dict[str, Any]]: لیست هشدارهای ایجاد شده
    """
    # تشخیص موج‌ها و ایجاد هشدار
    alerts = await analyzer.detect_waves_and_alert(
        keywords=request.keywords,
        hours_back=request.hours_back,
        min_importance=request.min_importance
    )

    return alerts


@router.post("/analyze_wave", response_model=WaveAnalysisResponse)
async def analyze_wave(
        wave_id: Dict[str, Any],
        db: AsyncSession = Depends(get_db),
        current_user: AppUser = Depends(get_current_user),
        analyzer: TweetAnalyzer = Depends(get_analyzer)
):
    """
    تحلیل عمیق یک موج.

    Args:
        wave_id (Dict[str, Any]): اطلاعات موج
        db (AsyncSession): نشست دیتابیس
        current_user (AppUser): کاربر فعلی
        analyzer (TweetAnalyzer): سرویس تحلیل

    Returns:
        WaveAnalysisResponse: نتیجه تحلیل موج
    """
    # استخراج داده‌های موج از ورودی
    wave_type = wave_id.get("type", "volume")
    start_time = wave_id.get("start_time")
    end_time = wave_id.get("end_time")
    related_keywords = wave_id.get("related_keywords", [])

    if not start_time or not end_time:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="زمان شروع و پایان موج باید مشخص شوند",
        )

    # تبدیل رشته‌های زمانی به datetime
    try:
        start_datetime = datetime.fromisoformat(start_time.replace('Z', '+00:00'))
        end_datetime = datetime.fromisoformat(end_time.replace('Z', '+00:00'))
    except:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="فرمت زمان نامعتبر است",
        )

    # دریافت توییت‌های این بازه زمانی
    stmt = select(Tweet).where(
        and_(
            Tweet.created_at >= start_datetime,
            Tweet.created_at <= end_datetime,
            Tweet.is_analyzed == True
        )
    ).order_by(Tweet.importance_score.desc().nullslast()).limit(100)

    result = await db.execute(stmt)
    tweets = result.scalars().all()

    if not tweets:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="هیچ توییتی در این بازه زمانی یافت نشد",
        )

    # تبدیل توییت‌ها به فرمت مورد نیاز برای تحلیل موج
    tweets_data = [
        {
            "id": tweet.id,
            "content": tweet.content,
            "user_id": tweet.user_id,
            "created_at": tweet.created_at.isoformat() if tweet.created_at else None,
            "sentiment_label": tweet.sentiment_label,
            "sentiment_score": tweet.sentiment_score,
            "importance_score": tweet.importance_score,
            "user": {
                "username": tweet.user.username if tweet.user else "unknown",
                "followers": tweet.user.followers_count if tweet.user else 0,
                "verified": tweet.user.verified if tweet.user else False
            } if tweet.user else {}
        }
        for tweet in tweets
    ]

    # استفاده از Claude API برای تحلیل عمیق موج
    wave_analysis = await analyzer.claude_client.analyze_wave(
        tweets=tweets_data,
        keywords=related_keywords,
        use_extended_thinking=True
    )

    # تبدیل به فرمت پاسخ
    response = WaveAnalysisResponse(
        main_topic=wave_analysis.get("main_topic", ""),
        summary=wave_analysis.get("summary", ""),
        is_coordinated=wave_analysis.get("is_coordinated", False),
        coordination_confidence=wave_analysis.get("coordination_confidence", 0),
        importance_score=wave_analysis.get("importance_score", 0),
        key_influencers=wave_analysis.get("key_influencers", []),
        reactionary=wave_analysis.get("reactionary", False),
        trigger_event=wave_analysis.get("trigger_event", ""),
        prediction=wave_analysis.get("prediction", ""),
        recommendations=wave_analysis.get("recommendations", []),
        sentiment_distribution=wave_analysis.get("sentiment_distribution", {}),
        analysis_confidence=wave_analysis.get("analysis_confidence", 0),
        extended_thinking=wave_analysis.get("extended_thinking", ""),
        analyzed_at=datetime.utcnow()
    )

    return response


@router.get("/alerts", response_model=List[AlertResponse])
async def get_alerts(
        params: AlertFilterParams = Depends(),
        db: AsyncSession = Depends(get_db),
        current_user: AppUser = Depends(get_current_user)
):
    """
    دریافت لیست هشدارها.

    Args:
        params (AlertFilterParams): پارامترهای فیلتر
        db (AsyncSession): نشست دیتابیس
        current_user (AppUser): کاربر فعلی

    Returns:
        List[AlertResponse]: لیست هشدارها
    """
    # ایجاد query پایه
    query = select(Alert)

    # اعمال فیلترها
    filters = []

    # فیلتر براساس نوع هشدار
    if params.alert_type:
        filters.append(Alert.alert_type == params.alert_type)

    # فیلتر براساس شدت
    if params.severity:
        filters.append(Alert.severity == params.severity)

    # فیلتر براساس وضعیت خوانده شدن
    if params.is_read is not None:
        filters.append(Alert.is_read == params.is_read)

    # فیلتر براساس بازه زمانی
    if params.start_date:
        filters.append(Alert.created_at >= params.start_date)
    if params.end_date:
        filters.append(Alert.created_at <= params.end_date)

    # ترکیب فیلترها
    if filters:
        query = query.where(and_(*filters))

    # مرتب‌سازی
    query = query.order_by(desc(Alert.created_at))

    # صفحه‌بندی
    query = query.offset(params.skip).limit(params.limit)

    # اجرای query
    result = await db.execute(query)
    alerts = result.scalars().all()

    # تبدیل به فرمت پاسخ
    return [
        AlertResponse(
            id=alert.id,
            title=alert.title,
            message=alert.message,
            severity=alert.severity,
            alert_type=alert.alert_type,
            related_tweet_id=alert.related_tweet_id,
            data=alert.data,
            is_read=alert.is_read,
            created_at=alert.created_at
        )
        for alert in alerts
    ]


@router.get("/alerts/{alert_id}", response_model=AlertResponse)
async def get_alert(
        alert_id: int,
        db: AsyncSession = Depends(get_db),
        current_user: AppUser = Depends(get_current_user)
):
    """
    دریافت اطلاعات یک هشدار.

    Args:
        alert_id (int): شناسه هشدار
        db (AsyncSession): نشست دیتابیس
        current_user (AppUser): کاربر فعلی

    Returns:
        AlertResponse: اطلاعات هشدار

    Raises:
        HTTPException: در صورت یافت نشدن هشدار
    """
    # دریافت هشدار از دیتابیس
    stmt = select(Alert).where(Alert.id == alert_id)
    result = await db.execute(stmt)
    alert = result.scalar_one_or_none()

    if not alert:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="هشدار یافت نشد",
        )

    return AlertResponse(
        id=alert.id,
        title=alert.title,
        message=alert.message,
        severity=alert.severity,
        alert_type=alert.alert_type,
        related_tweet_id=alert.related_tweet_id,
        data=alert.data,
        is_read=alert.is_read,
        created_at=alert.created_at
    )


@router.put("/alerts/{alert_id}/read", response_model=AlertResponse)
async def mark_alert_as_read(
        alert_id: int,
        db: AsyncSession = Depends(get_db),
        current_user: AppUser = Depends(get_current_user)
):
    """
    علامت‌گذاری هشدار به عنوان خوانده شده.

    Args:
        alert_id (int): شناسه هشدار
        db (AsyncSession): نشست دیتابیس
        current_user (AppUser): کاربر فعلی

    Returns:
        AlertResponse: اطلاعات به‌روزرسانی شده هشدار

    Raises:
        HTTPException: در صورت یافت نشدن هشدار
    """
    # یافتن هشدار
    stmt = select(Alert).where(Alert.id == alert_id)
    result = await db.execute(stmt)
    alert = result.scalar_one_or_none()

    if not alert:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="هشدار یافت نشد",
        )

    # به‌روزرسانی وضعیت خوانده شدن
    alert.is_read = True

    await db.commit()
    await db.refresh(alert)

    return AlertResponse(
        id=alert.id,
        title=alert.title,
        message=alert.message,
        severity=alert.severity,
        alert_type=alert.alert_type,
        related_tweet_id=alert.related_tweet_id,
        data=alert.data,
        is_read=alert.is_read,
        created_at=alert.created_at
    )