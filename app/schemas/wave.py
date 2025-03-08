"""
مدل‌های مربوط به موج‌ها و هشدارها.

این ماژول مدل‌های Pydantic مربوط به موج‌های توییتری و هشدارها را تعریف می‌کند.
"""

from pydantic import BaseModel, Field
from typing import List, Dict, Optional, Any
from datetime import datetime


class AlertFilterParams(BaseModel):
    """پارامترهای فیلتر برای جستجوی هشدارها"""
    alert_type: Optional[str] = None
    severity: Optional[str] = None
    is_read: Optional[bool] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    skip: int = 0
    limit: int = 100


class AlertResponse(BaseModel):
    """مدل پاسخ هشدار"""
    id: int
    title: str
    message: str
    severity: str
    alert_type: str
    related_tweet_id: Optional[int] = None
    data: Optional[Dict[str, Any]] = None
    is_read: bool
    created_at: datetime

    class Config:
        orm_mode = True


class WaveResponse(BaseModel):
    """مدل پاسخ موج توییتری"""
    type: str
    start_time: str
    end_time: str
    tweet_count: int
    growth_rate: Optional[float] = None
    sentiment_shift: Optional[float] = None
    avg_sentiment: float
    sentiment_distribution: Dict[str, float]
    importance_score: float
    related_keywords: List[str] = []
    top_tweets: List[Dict[str, Any]] = []


class WaveDetectionRequest(BaseModel):
    """مدل درخواست تشخیص موج"""
    keywords: Optional[List[str]] = None
    hours_back: int = 6
    min_importance: float = 3.0


class WaveAnalysisResponse(BaseModel):
    """مدل پاسخ تحلیل موج"""
    main_topic: str
    summary: str
    is_coordinated: bool
    coordination_confidence: float
    importance_score: float
    key_influencers: List[str]
    reactionary: bool
    trigger_event: Optional[str] = None
    prediction: str
    recommendations: List[str]
    sentiment_distribution: Dict[str, float]
    analysis_confidence: float
    extended_thinking: Optional[str] = None
    analyzed_at: datetime