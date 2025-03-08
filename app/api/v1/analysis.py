"""
اندپوینت‌های تحلیل و گزارش‌گیری.

این ماژول اندپوینت‌های مربوط به تحلیل توییت‌ها و تولید گزارش‌ها را فراهم می‌کند.
"""

from fastapi import APIRouter, Depends, HTTPException, Query, status, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any

from app.db.session import get_db
from app.db.models import Tweet, User, Keyword, TweetKeyword, Topic, TweetTopic, AppUser
from app.schemas.analysis import (
    AnalysisResponse, AnalysisRequest, ReportResponse, ReportRequest,
    SentimentDistribution, TopicDistribution
)
from app.core.security import get_current_user
from app.services.analyzer.analyzer import TweetAnalyzer
from app.services.analyzer.claude_client import ClaudeClient
from app.services.analyzer.cost_manager import CostManager
from app.services.analyzer.wave_detector import WaveDetector

router = APIRouter(prefix="/analysis", tags=["analysis"])


async def get_analyzer(db: AsyncSession = Depends(get_db)) -> TweetAnalyzer:
    """
    وابستگی برای دریافت یک نمونه از TweetAnalyzer.

    Args:
        db (AsyncSession): نشست دیتابیس

    Returns:
        TweetAnalyzer: یک نمونه از TweetAnalyzer
    """
    claude_client = ClaudeClient()
    cost_manager = CostManager(db)
    wave_detector = WaveDetector(db)

    analyzer = TweetAnalyzer(
        db_session=db,
        claude_client=claude_client,
        cost_manager=cost_manager,
        wave_detector=wave_detector
    )

    await analyzer.initialize()

    return analyzer


@router.post("/tweet/{tweet_id}", response_model=AnalysisResponse)
async def analyze_tweet(
        tweet_id: int,
        db: AsyncSession = Depends(get_db),
        current_user: AppUser = Depends(get_current_user),
        analyzer: TweetAnalyzer = Depends(get_analyzer)
):
    """
    تحلیل یک توییت.

    Args:
        tweet_id (int): شناسه توییت
        db (AsyncSession): نشست دیتابیس
        current_user (AppUser): کاربر فعلی
        analyzer (TweetAnalyzer): سرویس تحلیل

    Returns:
        AnalysisResponse: نتایج تحلیل

    Raises:
        HTTPException: در صورت یافت نشدن توییت
    """
    # یافتن توییت
    stmt = select(Tweet).where(Tweet.id == tweet_id)
    result = await db.execute(stmt)
    tweet = result.scalar_one_or_none()

    if not tweet:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="توییت یافت نشد",
        )

    # تحلیل توییت
    analysis_result = await analyzer.analyze_tweet(tweet_id)

    # تبدیل به فرمت پاسخ
    response = AnalysisResponse(
        tweet_id=tweet_id,
        content=tweet.content,
        sentiment=analysis_result.get("sentiment", {}),
        topics=analysis_result.get("topics", []),
        main_topic=analysis_result.get("main_topic", ""),
        keywords=analysis_result.get("keywords", []),
        is_analyzed=analysis_result.get("is_analyzed", False),
        analysis_date=datetime.utcnow()
    )

    return response


@router.post("/batch", response_model=List[AnalysisResponse])
async def analyze_batch(
        request: AnalysisRequest,
        background_tasks: BackgroundTasks,
        db: AsyncSession = Depends(get_db),
        current_user: AppUser = Depends(get_current_user),
        analyzer: TweetAnalyzer = Depends(get_analyzer)
):
    """
    تحلیل دسته‌ای توییت‌ها.

    Args:
        request (AnalysisRequest): درخواست تحلیل
        background_tasks (BackgroundTasks): تسک‌های پس‌زمینه
        db (AsyncSession): نشست دیتابیس
        current_user (AppUser): کاربر فعلی
        analyzer (TweetAnalyzer): سرویس تحلیل

    Returns:
        List[AnalysisResponse]: نتایج تحلیل
    """
    # بررسی وجود توییت‌ها
    stmt = select(Tweet).where(Tweet.id.in_(request.tweet_ids))
    result = await db.execute(stmt)
    tweets = result.scalars().all()

    found_ids = [tweet.id for tweet in tweets]
    missing_ids = [tid for tid in request.tweet_ids if tid not in found_ids]

    if missing_ids:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"توییت‌ها با شناسه‌های {missing_ids} یافت نشدند",
        )

    # اگر تحلیل در پس‌زمینه درخواست شده باشد
    if request.run_in_background:
        # افزودن تسک تحلیل به تسک‌های پس‌زمینه
        background_tasks.add_task(analyzer.batch_analyze_tweets, request.tweet_ids)

        # برگرداندن پاسخ فوری
        return [
            AnalysisResponse(
                tweet_id=tweet.id,
                content=tweet.content,
                sentiment={
                    "label": tweet.sentiment_label,
                    "score": tweet.sentiment_score
                } if tweet.sentiment_label else {},
                topics=[],
                main_topic="",
                keywords=[],
                is_analyzed=tweet.is_analyzed,
                analysis_date=datetime.utcnow()
            )
            for tweet in tweets
        ]

    # تحلیل دسته‌ای
    analysis_results = await analyzer.batch_analyze_tweets(request.tweet_ids)

    # تبدیل به فرمت پاسخ
    responses = []
    for tweet in tweets:
        # یافتن نتیجه تحلیل مربوطه
        result = next((r for r in analysis_results if r.get("tweet_id") == tweet.id), {})

        response = AnalysisResponse(
            tweet_id=tweet.id,
            content=tweet.content,
            sentiment=result.get("sentiment", {}),
            topics=[],  # تحلیل دسته‌ای معمولاً موضوعات را استخراج نمی‌کند
            main_topic="",
            keywords=[],
            is_analyzed=result.get("is_analyzed", False),
            analysis_date=datetime.utcnow()
        )

        responses.append(response)

    return responses


@router.post("/report", response_model=ReportResponse)
async def generate_report(
        request: ReportRequest,
        db: AsyncSession = Depends(get_db),
        current_user: AppUser = Depends(get_current_user),
        analyzer: TweetAnalyzer = Depends(get_analyzer)
):
    """
    تولید گزارش تحلیلی.

    Args:
        request (ReportRequest): درخواست گزارش
        db (AsyncSession): نشست دیتابیس
        current_user (AppUser): کاربر فعلی
        analyzer (TweetAnalyzer): سرویس تحلیل

    Returns:
        ReportResponse: گزارش تحلیلی
    """
    # تولید گزارش
    report = await analyzer.generate_report(
        keywords=request.keywords,
        hours_back=request.hours_back,
        include_tweets=request.include_tweets
    )

    # تبدیل به فرمت پاسخ
    response = ReportResponse(
        timeframe={
            "start": report["timeframe"]["start"],
            "end": report["timeframe"]["end"],
            "hours": report["timeframe"]["hours"]
        },
        keywords=report["keywords"],
        summary={
            "total_tweets": report["summary"]["total_tweets"],
            "avg_sentiment": report["summary"]["avg_sentiment"],
            "sentiment_distribution": SentimentDistribution(
                positive=report["summary"]["sentiment_distribution"].get("positive", 0),
                negative=report["summary"]["sentiment_distribution"].get("negative", 0),
                neutral=report["summary"]["sentiment_distribution"].get("neutral", 0),
                mixed=report["summary"]["sentiment_distribution"].get("mixed", 0)
            )
        },
        top_topics=[
            TopicDistribution(
                name=topic["name"],
                count=topic["count"],
                percentage=topic["percentage"]
            )
            for topic in report["top_topics"]
        ],
        important_tweets=report["important_tweets"] if request.include_tweets else [],
        generated_at=datetime.utcnow()
    )

    return response


@router.get("/topics", response_model=List[Dict[str, Any]])
async def get_topics(
        skip: int = 0,
        limit: int = 100,
        min_count: int = 5,
        db: AsyncSession = Depends(get_db),
        current_user: AppUser = Depends(get_current_user)
):
    """
    دریافت لیست موضوعات.

    Args:
        skip (int): تعداد آیتم‌های رد شده
        limit (int): حداکثر تعداد آیتم‌ها
        min_count (int): حداقل تعداد توییت‌های مرتبط
        db (AsyncSession): نشست دیتابیس
        current_user (AppUser): کاربر فعلی

    Returns:
        List[Dict[str, Any]]: لیست موضوعات و آمار آنها
    """
    # استخراج موضوعات به همراه تعداد توییت‌های مرتبط
    from sqlalchemy import func

    stmt = select(
        Topic.id,
        Topic.name,
        Topic.description,
        func.count(TweetTopic.tweet_id).label("tweet_count"),
        func.avg(TweetTopic.relevance_score).label("avg_relevance")
    ).join(
        TweetTopic, Topic.id == TweetTopic.topic_id
    ).group_by(
        Topic.id
    ).having(
        func.count(TweetTopic.tweet_id) >= min_count
    ).order_by(
        func.count(TweetTopic.tweet_id).desc()
    ).offset(skip).limit(limit)

    result = await db.execute(stmt)
    topics = result.fetchall()

    # تبدیل به فرمت پاسخ
    return [
        {
            "id": topic[0],
            "name": topic[1],
            "description": topic[2],
            "tweet_count": topic[3],
            "avg_relevance": topic[4]
        }
        for topic in topics
    ]