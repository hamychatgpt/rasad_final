"""
مدل‌های مربوط به تحلیل.

این ماژول مدل‌های Pydantic مربوط به تحلیل توییت‌ها را تعریف می‌کند.
"""

from pydantic import BaseModel, Field
from typing import List, Dict, Optional, Any
from datetime import datetime


class SentimentData(BaseModel):
    """داده‌های احساسات"""
    label: str
    score: float
    confidence: Optional[float] = None
    explanation: Optional[str] = None


class TopicData(BaseModel):
    """داده‌های موضوع"""
    title: str
    relevance: float
    keywords: List[str]


class AnalysisResponse(BaseModel):
    """مدل پاسخ تحلیل توییت"""
    tweet_id: int
    content: str
    sentiment: SentimentData
    topics: List[TopicData] = []
    main_topic: Optional[str] = None
    keywords: List[str] = []
    is_analyzed: bool
    analysis_date: datetime


class AnalysisRequest(BaseModel):
    """مدل درخواست تحلیل توییت‌ها"""
    tweet_ids: List[int]
    run_in_background: bool = False


class SentimentDistribution(BaseModel):
    """توزیع احساسات"""
    positive: float
    negative: float
    neutral: float
    mixed: Optional[float] = 0.0


class TopicDistribution(BaseModel):
    """توزیع موضوعات"""
    name: str
    count: int
    percentage: float


class ReportTimeframe(BaseModel):
    """بازه زمانی گزارش"""
    start: str
    end: str
    hours: int


class ReportSummary(BaseModel):
    """خلاصه گزارش"""
    total_tweets: int
    avg_sentiment: float
    sentiment_distribution: SentimentDistribution


class ReportResponse(BaseModel):
    """مدل پاسخ گزارش تحلیلی"""
    timeframe: ReportTimeframe
    keywords: Optional[List[str]] = None
    summary: ReportSummary
    top_topics: List[TopicDistribution]
    important_tweets: List[Dict[str, Any]] = []
    generated_at: datetime


class ReportRequest(BaseModel):
    """مدل درخواست گزارش تحلیلی"""
    keywords: Optional[List[str]] = None
    hours_back: int = 24
    include_tweets: bool = True