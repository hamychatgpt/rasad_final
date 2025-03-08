"""
مدل‌های مربوط به توییت‌ها.

این ماژول مدل‌های Pydantic مربوط به توییت‌ها را تعریف می‌کند.
"""

from pydantic import BaseModel, Field
from typing import List, Dict, Optional, Any
from datetime import datetime


class TweetFilterParams(BaseModel):
    """پارامترهای فیلتر برای جستجوی توییت‌ها"""
    query: Optional[str] = None
    sentiment: Optional[str] = None
    keywords: Optional[List[str]] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    min_importance: Optional[float] = None
    sort_by: Optional[str] = "date"  # date, importance, sentiment
    skip: int = 0
    limit: int = 100


class UserResponse(BaseModel):
    """مدل پاسخ کاربر توییتر"""
    user_id: str
    username: str
    display_name: Optional[str] = None
    followers_count: Optional[int] = None
    following_count: Optional[int] = None
    verified: Optional[bool] = None
    profile_image_url: Optional[str] = None

    class Config:
        orm_mode = True


class TweetResponse(BaseModel):
    """مدل پاسخ توییت"""
    id: int
    tweet_id: str
    content: str
    created_at: Optional[datetime] = None
    language: Optional[str] = None
    user: Optional[UserResponse] = None
    sentiment_label: Optional[str] = None
    sentiment_score: Optional[float] = None
    importance_score: Optional[float] = None
    is_processed: bool
    is_analyzed: bool
    entities: Optional[Dict[str, Any]] = None

    class Config:
        orm_mode = True


class KeywordCreate(BaseModel):
    """مدل ایجاد کلیدواژه"""
    text: str
    is_active: bool = True
    priority: int = 1
    description: Optional[str] = None


class KeywordResponse(BaseModel):
    """مدل پاسخ کلیدواژه"""
    id: int
    text: str
    is_active: bool
    priority: int
    description: Optional[str] = None
    created_at: datetime

    class Config:
        orm_mode = True