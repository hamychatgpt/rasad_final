"""
مدل‌های داده Twitter API.

این ماژول مدل‌های Pydantic را برای داده‌های دریافتی و ارسالی به TwitterAPI.io تعریف می‌کند.
"""

from typing import List, Dict, Any, Optional
from datetime import datetime
from pydantic import BaseModel, Field, field_validator, model_validator, AnyHttpUrl


class TwitterUser(BaseModel):
    """
    مدل داده کاربر توییتر

    Attributes:
        id (str): شناسه کاربر
        username (str): نام کاربری (بدون @)
        url (Optional[str]): آدرس پروفایل کاربر
        name (Optional[str]): نام نمایشی کاربر
        is_verified (Optional[bool]): آیا کاربر تأیید شده است؟
        profile_image_url (Optional[str]): آدرس تصویر پروفایل
        description (Optional[str]): توضیحات پروفایل
        location (Optional[str]): موقعیت مکانی
        followers (Optional[int]): تعداد دنبال‌کنندگان
        following (Optional[int]): تعداد دنبال شوندگان
        created_at (Optional[datetime]): زمان ایجاد حساب کاربری
    """
    id: str
    username: str = Field(alias="userName")
    url: Optional[str] = None
    name: Optional[str] = None
    is_verified: Optional[bool] = Field(default=False, alias="isBlueVerified")
    profile_image_url: Optional[str] = Field(default=None, alias="profilePicture")
    description: Optional[str] = None
    location: Optional[str] = None
    followers: Optional[int] = None
    following: Optional[int] = None
    created_at: Optional[datetime] = Field(default=None, alias="createdAt")

    @field_validator('created_at', mode='before')
    @classmethod
    def parse_datetime(cls, value: Any) -> Optional[datetime]:
        """تبدیل رشته تاریخ به آبجکت datetime"""
        if not value:
            return None
        if isinstance(value, datetime):
            return value
        try:
            # فرمت تاریخ توییتر: "Thu Dec 13 08:41:26 +0000 2020"
            return datetime.strptime(value, "%a %b %d %H:%M:%S +0000 %Y")
        except ValueError:
            return None

    class Config:
        populate_by_name = True


class TweetEntity(BaseModel):
    """مدل داده برای entity‌های توییت (هشتگ‌ها، منشن‌ها، URL‌ها و...)"""
    hashtags: Optional[List[Dict[str, Any]]] = None
    urls: Optional[List[Dict[str, Any]]] = None
    user_mentions: Optional[List[Dict[str, Any]]] = Field(default=None, alias="user_mentions")
    media: Optional[List[Dict[str, Any]]] = None


class Tweet(BaseModel):
    """
    مدل داده توییت

    Attributes:
        id (str): شناسه توییت
        url (Optional[str]): آدرس توییت
        text (str): متن توییت
        created_at (datetime): زمان ایجاد توییت
        lang (Optional[str]): زبان توییت
        author (TwitterUser): کاربر نویسنده
        retweet_count (Optional[int]): تعداد ریتوییت‌ها
        reply_count (Optional[int]): تعداد پاسخ‌ها
        like_count (Optional[int]): تعداد لایک‌ها
        quote_count (Optional[int]): تعداد نقل قول‌ها
        is_reply (Optional[bool]): آیا توییت پاسخ است؟
        in_reply_to_id (Optional[str]): شناسه توییت پاسخ داده شده
        entities (Optional[TweetEntity]): entity‌های توییت
    """
    id: str
    url: Optional[str] = None
    text: str
    created_at: datetime = Field(alias="createdAt")
    lang: Optional[str] = None
    author: TwitterUser
    retweet_count: Optional[int] = Field(default=0, alias="retweetCount")
    reply_count: Optional[int] = Field(default=0, alias="replyCount")
    like_count: Optional[int] = Field(default=0, alias="likeCount")
    quote_count: Optional[int] = Field(default=0, alias="quoteCount")
    is_reply: Optional[bool] = Field(default=False, alias="isReply")
    in_reply_to_id: Optional[str] = Field(default=None, alias="inReplyToId")
    entities: Optional[TweetEntity] = None

    @field_validator('created_at', mode='before')
    @classmethod
    def parse_datetime(cls, value: Any) -> datetime:
        """تبدیل رشته تاریخ به آبجکت datetime"""
        if isinstance(value, datetime):
            return value
        try:
            # فرمت تاریخ توییتر: "Thu Dec 13 08:41:26 +0000 2020"
            return datetime.strptime(value, "%a %b %d %H:%M:%S +0000 %Y")
        except ValueError:
            # اگر در فرمت اصلی نبود، به عنوان datetime فرض می‌کنیم
            if isinstance(value, str):
                # برخی اوقات TwitterAPI.io تاریخ را در فرمت ISO برمی‌گرداند
                try:
                    return datetime.fromisoformat(value.replace('Z', '+00:00'))
                except ValueError:
                    pass
            # اگر هیچکدام از موارد بالا نبود، از زمان فعلی استفاده می‌کنیم
            return datetime.utcnow()

    class Config:
        populate_by_name = True


class TwitterSearchResponse(BaseModel):
    """مدل داده پاسخ جستجوی توییت"""
    data: Dict[str, Any]

    @model_validator(mode='after')
    def check_data_structure(self) -> 'TwitterSearchResponse':
        """بررسی ساختار داده برای اطمینان از وجود فیلدهای مورد نیاز"""
        if not self.data:
            self.data = {"tweets": [], "next_cursor": ""}
        if "tweets" not in self.data:
            self.data["tweets"] = []
        if "next_cursor" not in self.data:
            self.data["next_cursor"] = ""
        return self

    @property
    def tweets(self) -> List[Dict[str, Any]]:
        """دریافت لیست توییت‌ها"""
        return self.data.get("tweets", [])

    @property
    def next_cursor(self) -> str:
        """دریافت cursor بعدی برای صفحه‌بندی"""
        return self.data.get("next_cursor", "")

    @property
    def has_next_page(self) -> bool:
        """آیا صفحه بعدی وجود دارد؟"""
        return bool(self.next_cursor)


class TwitterUserResponse(BaseModel):
    """مدل داده پاسخ اطلاعات کاربر"""
    data: Optional[Dict[str, Any]] = None

    @property
    def user(self) -> Optional[Dict[str, Any]]:
        """دریافت اطلاعات کاربر"""
        return self.data


class TwitterUserBatchResponse(BaseModel):
    """مدل داده پاسخ اطلاعات دسته‌ای کاربران"""
    data: Optional[List[Dict[str, Any]]] = None

    @property
    def users(self) -> List[Dict[str, Any]]:
        """دریافت لیست کاربران"""
        return self.data or []


class TwitterError(BaseModel):
    """مدل داده خطای Twitter API"""
    status: str = "error"
    msg: str


class TwitterWebhookRule(BaseModel):
    """مدل داده قانون وب‌هوک Twitter"""
    tag: str
    value: str
    interval_seconds: int = Field(ge=100, le=86400)  # حداقل 100 ثانیه، حداکثر 24 ساعت


class TwitterWebhookResponse(BaseModel):
    """مدل داده پاسخ ایجاد/بروزرسانی وب‌هوک"""
    rule_id: Optional[str] = None
    status: str
    msg: Optional[str] = None
