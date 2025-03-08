"""
مدل‌های داده‌ای ORM.

این ماژول مدل‌های داده‌ای SQLAlchemy را برای نگاشت بین موجودیت‌های توییتر و دیتابیس تعریف می‌کند.
"""

from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, ForeignKey, Text, Index, JSON, Table
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid

Base = declarative_base()


class Tweet(Base):
    """
    مدل داده‌ای برای ذخیره‌سازی توییت‌ها

    Attributes:
        id (int): شناسه اولیه
        tweet_id (str): شناسه توییت در توییتر
        content (str): متن توییت
        created_at (datetime): زمان ایجاد توییت
        language (str): زبان توییت
        retweet_count (int): تعداد ریتوییت‌ها
        like_count (int): تعداد لایک‌ها
        reply_count (int): تعداد پاسخ‌ها
        quote_count (int): تعداد نقل قول‌ها
        user_id (str): شناسه کاربر نویسنده
        sentiment_score (float): امتیاز احساسات (بین -1 تا 1)
        sentiment_label (str): برچسب احساسات (مثبت، منفی، خنثی)
        importance_score (float): امتیاز اهمیت
        is_processed (bool): آیا توییت پردازش شده است؟
        is_analyzed (bool): آیا توییت تحلیل عمیق شده است؟
    """
    __tablename__ = "tweets"

    id = Column(Integer, primary_key=True)
    tweet_id = Column(String(255), unique=True, index=True)
    content = Column(Text, nullable=False)
    created_at = Column(DateTime, index=True)
    language = Column(String(10), index=True)
    retweet_count = Column(Integer, default=0)
    like_count = Column(Integer, default=0)
    reply_count = Column(Integer, default=0)
    quote_count = Column(Integer, default=0)
    user_id = Column(String(255), ForeignKey("users.user_id"), index=True)
    sentiment_score = Column(Float, nullable=True)
    sentiment_label = Column(String(20), nullable=True, index=True)
    importance_score = Column(Float, nullable=True, index=True)
    is_processed = Column(Boolean, default=False, index=True)
    is_analyzed = Column(Boolean, default=False, index=True)
    entities = Column(JSON, nullable=True)  # ذخیره هشتگ‌ها، منشن‌ها و URL‌ها
    created_at_internal = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # روابط
    user = relationship("User", back_populates="tweets")
    keywords = relationship("TweetKeyword", back_populates="tweet")
    topics = relationship("TweetTopic", back_populates="tweet")
    alerts = relationship("Alert", foreign_keys="Alert.related_tweet_id", back_populates="related_tweet")

    # شاخص‌های مرکب
    __table_args__ = (
        Index('idx_tweet_sentiment_created', sentiment_label, created_at),
        Index('idx_tweet_importance_created', importance_score, created_at),
    )

    def __repr__(self):
        return f"<Tweet(id={self.id}, tweet_id={self.tweet_id})>"


class User(Base):
    """
    مدل داده‌ای برای ذخیره‌سازی کاربران

    Attributes:
        id (int): شناسه اولیه
        user_id (str): شناسه کاربر در توییتر
        username (str): نام کاربری
        display_name (str): نام نمایشی
        description (str): بیوگرافی
        followers_count (int): تعداد دنبال‌کنندگان
        following_count (int): تعداد دنبال شوندگان
        tweet_count (int): تعداد توییت‌ها
        verified (bool): آیا کاربر تأیید شده است؟
        profile_image_url (str): آدرس تصویر پروفایل
        location (str): موقعیت مکانی
        influence_score (float): امتیاز تأثیرگذاری
        created_at (datetime): زمان ایجاد حساب کاربری
    """
    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    user_id = Column(String(255), unique=True, index=True)
    username = Column(String(255), index=True)
    display_name = Column(String(255))
    description = Column(Text)
    followers_count = Column(Integer, default=0)
    following_count = Column(Integer, default=0)
    tweet_count = Column(Integer, default=0)
    verified = Column(Boolean, default=False)
    profile_image_url = Column(String(1024))
    location = Column(String(255))
    influence_score = Column(Float, nullable=True, index=True)
    created_at = Column(DateTime, nullable=True)
    created_at_internal = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # روابط
    tweets = relationship("Tweet", back_populates="user")

    def __repr__(self):
        return f"<User(id={self.id}, username={self.username})>"


class Keyword(Base):
    """
    مدل داده‌ای برای ذخیره‌سازی کلیدواژه‌ها

    Attributes:
        id (int): شناسه اولیه
        text (str): متن کلیدواژه
        is_active (bool): آیا کلیدواژه فعال است؟
        priority (int): اولویت کلیدواژه
        description (str): توضیحات کلیدواژه
    """
    __tablename__ = "keywords"

    id = Column(Integer, primary_key=True)
    text = Column(String(255), unique=True, index=True)
    is_active = Column(Boolean, default=True, index=True)
    priority = Column(Integer, default=1)
    description = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # روابط
    tweets = relationship("TweetKeyword", back_populates="keyword")

    def __repr__(self):
        return f"<Keyword(id={self.id}, text={self.text})>"


class TweetKeyword(Base):
    """
    مدل داده‌ای برای ارتباط بین توییت‌ها و کلیدواژه‌ها

    Attributes:
        id (int): شناسه اولیه
        tweet_id (int): شناسه توییت
        keyword_id (int): شناسه کلیدواژه
        score (float): امتیاز ارتباط
    """
    __tablename__ = "tweet_keywords"

    id = Column(Integer, primary_key=True)
    tweet_id = Column(Integer, ForeignKey("tweets.id", ondelete="CASCADE"))
    keyword_id = Column(Integer, ForeignKey("keywords.id", ondelete="CASCADE"))
    score = Column(Float, default=1.0)
    created_at = Column(DateTime, default=datetime.utcnow)

    # روابط
    tweet = relationship("Tweet", back_populates="keywords")
    keyword = relationship("Keyword", back_populates="tweets")

    # شاخص یکتایی ترکیبی
    __table_args__ = (
        Index('idx_tweet_keyword_unique', tweet_id, keyword_id, unique=True),
    )

    def __repr__(self):
        return f"<TweetKeyword(tweet_id={self.tweet_id}, keyword_id={self.keyword_id})>"


class Topic(Base):
    """
    مدل داده‌ای برای ذخیره‌سازی موضوعات

    Attributes:
        id (int): شناسه اولیه
        name (str): نام موضوع
        description (str): توضیحات موضوع
    """
    __tablename__ = "topics"

    id = Column(Integer, primary_key=True)
    name = Column(String(255), unique=True, index=True)
    description = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # روابط
    tweets = relationship("TweetTopic", back_populates="topic")

    def __repr__(self):
        return f"<Topic(id={self.id}, name={self.name})>"


class TweetTopic(Base):
    """
    مدل داده‌ای برای ارتباط بین توییت‌ها و موضوعات

    Attributes:
        id (int): شناسه اولیه
        tweet_id (int): شناسه توییت
        topic_id (int): شناسه موضوع
        relevance_score (float): امتیاز ارتباط
    """
    __tablename__ = "tweet_topics"

    id = Column(Integer, primary_key=True)
    tweet_id = Column(Integer, ForeignKey("tweets.id", ondelete="CASCADE"))
    topic_id = Column(Integer, ForeignKey("topics.id", ondelete="CASCADE"))
    relevance_score = Column(Float, default=1.0)
    created_at = Column(DateTime, default=datetime.utcnow)

    # روابط
    tweet = relationship("Tweet", back_populates="topics")
    topic = relationship("Topic", back_populates="tweets")

    # شاخص یکتایی ترکیبی
    __table_args__ = (
        Index('idx_tweet_topic_unique', tweet_id, topic_id, unique=True),
    )

    def __repr__(self):
        return f"<TweetTopic(tweet_id={self.tweet_id}, topic_id={self.topic_id})>"


class Alert(Base):
    """
    مدل داده‌ای برای ذخیره‌سازی هشدارها

    Attributes:
        id (int): شناسه اولیه
        title (str): عنوان هشدار
        message (str): متن هشدار
        severity (str): شدت هشدار (high, medium, low)
        alert_type (str): نوع هشدار (volume_wave, sentiment_shift, etc.)
        related_tweet_id (int): شناسه توییت مرتبط
        data (JSON): داده‌های اضافی هشدار
        is_read (bool): آیا هشدار خوانده شده است؟
    """
    __tablename__ = "alerts"

    id = Column(Integer, primary_key=True)
    title = Column(String(255), nullable=False)
    message = Column(Text, nullable=False)
    severity = Column(String(20), index=True)
    alert_type = Column(String(50), index=True)
    related_tweet_id = Column(Integer, ForeignKey("tweets.id", ondelete="SET NULL"), nullable=True)
    data = Column(JSON, nullable=True)  # ذخیره اطلاعات اضافی
    is_read = Column(Boolean, default=False, index=True)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # روابط
    related_tweet = relationship("Tweet", foreign_keys=[related_tweet_id], back_populates="alerts")

    def __repr__(self):
        return f"<Alert(id={self.id}, title={self.title}, severity={self.severity})>"


class ApiUsage(Base):
    """
    مدل داده‌ای برای ثبت استفاده از API

    Attributes:
        id (int): شناسه اولیه
        date (datetime): تاریخ
        api_type (str): نوع API (twitter, claude)
        operation (str): نوع عملیات
        tokens_in (int): تعداد توکن‌های ورودی (برای Claude)
        tokens_out (int): تعداد توکن‌های خروجی (برای Claude)
        item_count (int): تعداد آیتم‌ها (برای Twitter)
        cost (float): هزینه تخمینی
    """
    __tablename__ = "api_usage"

    id = Column(Integer, primary_key=True)
    date = Column(DateTime, default=datetime.utcnow, index=True)
    api_type = Column(String(50), index=True)
    operation = Column(String(50), index=True)
    tokens_in = Column(Integer, default=0)
    tokens_out = Column(Integer, default=0)
    item_count = Column(Integer, default=0)
    cost = Column(Float, default=0.0)

    def __repr__(self):
        return f"<ApiUsage(date={self.date}, api_type={self.api_type}, cost=${self.cost:.4f})>"


class AppUser(Base):
    """
    مدل داده‌ای برای کاربران برنامه

    Attributes:
        id (int): شناسه اولیه
        email (str): ایمیل کاربر (نام کاربری)
        hashed_password (str): رمز عبور هش شده
        full_name (str): نام کامل
        is_active (bool): آیا کاربر فعال است؟
        is_superuser (bool): آیا کاربر ادمین است؟
    """
    __tablename__ = "app_users"

    id = Column(Integer, primary_key=True)
    email = Column(String(255), unique=True, index=True)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(255))
    is_active = Column(Boolean, default=True)
    is_superuser = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f"<AppUser(id={self.id}, email={self.email})>"
