"""
مدل‌های مربوط به تنظیمات.

این ماژول مدل‌های Pydantic مربوط به تنظیمات سیستم را تعریف می‌کند.
"""

from pydantic import BaseModel, Field
from typing import Dict, List, Any, Optional


class SystemSettings(BaseModel):
    """تنظیمات سیستم"""
    project_name: str
    debug: bool
    daily_budget: float
    analyzer_batch_size: int
    twitter_api_base_url: str
    claude_model: str


class ApiUsageResponse(BaseModel):
    """آمار استفاده از API"""
    daily_usage: Dict[str, List[Dict[str, Any]]]
    total_cost: Dict[str, float]
    period_days: int