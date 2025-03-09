"""
سرویس پردازش توییت.

این ماژول سرویس اصلی برای پردازش توییت‌های جمع‌آوری شده،
فیلترینگ محتوا، محاسبه امتیاز اهمیت و آماده‌سازی برای تحلیل
توسط ماژول تحلیل را فراهم می‌کند.
"""

import asyncio
import json
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Tuple, Optional, Set, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import update, delete, func

from app.db.models import Tweet, User, Keyword, TweetKeyword
from app.services.redis_service import RedisService
# اصلاح مسیر واردسازی ContentFilter
from app.services.processor.content_filter import ContentFilter

logger = logging.getLogger(__name__)


class TweetProcessor:
    """
    سرویس پردازش توییت‌ها

    این کلاس عملیات پردازش توییت‌های جمع‌آوری شده، فیلترینگ محتوا،
    محاسبه امتیاز اهمیت و آماده‌سازی برای تحلیل را انجام می‌دهد.

    Attributes:
        db_session (AsyncSession): نشست دیتابیس
        redis_service (RedisService): سرویس Redis برای مدیریت صف‌ها
        content_filter (ContentFilter): فیلتر محتوا برای تشخیص اسپم و محتوای نامرتبط
    """

    def __init__(
            self,
            db_session: AsyncSession,
            redis_service: RedisService,
            content_filter: ContentFilter = None
    ):
        """
        مقداردهی اولیه سرویس پردازش توییت

        Args:
            db_session (AsyncSession): نشست دیتابیس
            redis_service (RedisService): سرویس Redis
            content_filter (ContentFilter, optional): فیلتر محتوا. اگر None باشد، یک نمونه جدید ایجاد می‌شود.
        """
        self.db_session = db_session
        self.redis_service = redis_service
        self.content_filter = content_filter or ContentFilter()
        logger.info("TweetProcessor initialized")

    async def process_tweets(self, tweet_ids: List[int]) -> Tuple[List[Tweet], List[Tweet]]:
        """
        پردازش توییت‌ها

        Args:
            tweet_ids (List[int]): لیست شناسه‌های توییت‌ها

        Returns:
            Tuple[List[Tweet], List[Tweet]]: توپل (توییت‌های پردازش شده، توییت‌های فیلتر شده)
        """
        if not tweet_ids:
            logger.warning("No tweet IDs provided for processing")
            return [], []

        logger.info(f"Processing {len(tweet_ids)} tweets")

        # دریافت توییت‌ها از دیتابیس
        stmt = select(Tweet).where(Tweet.id.in_(tweet_ids))
        result = await self.db_session.execute(stmt)
        tweets = result.scalars().all()

        if not tweets:
            logger.warning(f"No tweets found in database for the provided IDs")
            return [], []

        # دریافت کلیدواژه‌های فعال
        stmt = select(Keyword).where(Keyword.is_active == True)
        result = await self.db_session.execute(stmt)
        keywords = result.scalars().all()
        keyword_texts = [keyword.text for keyword in keywords]

        # لیست‌های توییت‌های پردازش شده و فیلتر شده
        processed_tweets = []
        filtered_tweets = []

        # پردازش هر توییت
        for tweet in tweets:
            # توییت‌های قبلاً پردازش شده را رد می‌کنیم
            if tweet.is_processed:
                continue

            # بررسی اسپم بودن توییت
            if self.content_filter.is_spam(tweet.content):
                logger.debug(f"Tweet {tweet.id} identified as spam")
                filtered_tweets.append(tweet)
                # حذف توییت از دیتابیس یا علامت‌گذاری آن می‌تواند اینجا انجام شود
                continue

            # بررسی نامناسب بودن محتوا
            if self.content_filter.is_inappropriate(tweet.content):
                logger.debug(f"Tweet {tweet.id} contains inappropriate content")
                filtered_tweets.append(tweet)
                continue

            # بررسی مرتبط بودن با کلیدواژه‌ها
            is_relevant = self.content_filter.is_relevant(tweet.content, keyword_texts)

            if not is_relevant and len(keyword_texts) > 0:
                logger.debug(f"Tweet {tweet.id} is not relevant to any keywords")
                filtered_tweets.append(tweet)
                continue

            # پردازش موفق توییت
            # محاسبه امتیاز اهمیت
            tweet_dict = {
                'retweet_count': tweet.retweet_count,
                'like_count': tweet.like_count,
                'reply_count': tweet.reply_count,
                'quote_count': tweet.quote_count
            }

            # افزودن اطلاعات کاربر اگر موجود باشد
            if tweet.user:
                tweet_dict['user'] = {
                    'verified': tweet.user.verified,
                    'followers_count': tweet.user.followers_count
                }

            importance_score = self.content_filter.calculate_importance_score(tweet_dict)

            # تعیین زبان
            language = tweet.language
            if not language:
                language = self.content_filter.detect_language(tweet.content)

            # محاسبه احساسات اولیه
            sentiment_label, sentiment_score = self.content_filter.calculate_sentiment_basic(tweet.content)

            # استخراج entities (هشتگ‌ها، منشن‌ها، URL‌ها)
            try:
                entities_dict = {}
                if tweet.entities:
                    if isinstance(tweet.entities, str):
                        entities_dict = json.loads(tweet.entities)
                    else:
                        entities_dict = tweet.entities

                entities = self.content_filter.extract_entities(tweet.content, entities_dict)
            except Exception as e:
                logger.error(f"Error extracting entities for tweet {tweet.id}: {e}")
                entities = self.content_filter.extract_entities(tweet.content)

            # بروزرسانی اطلاعات توییت
            tweet.language = language
            tweet.importance_score = importance_score
            tweet.sentiment_label = sentiment_label
            tweet.sentiment_score = sentiment_score
            tweet.is_processed = True

            # ذخیره entities به عنوان JSON اگر قبلاً ذخیره نشده باشد
            if not tweet.entities:
                tweet.entities = json.dumps(entities)

            processed_tweets.append(tweet)

            logger.debug(f"Successfully processed tweet {tweet.id}")

        # ذخیره تغییرات در دیتابیس
        if processed_tweets or filtered_tweets:
            await self.db_session.commit()

            # افزودن توییت‌های پردازش شده به صف تحلیل
            if processed_tweets:
                processed_ids = [tweet.id for tweet in processed_tweets]
                await self.redis_service.add_to_analysis_queue(processed_ids)
                logger.info(f"Added {len(processed_ids)} tweets to analysis queue")

        logger.info(f"Processed {len(processed_tweets)} tweets, filtered {len(filtered_tweets)} tweets")

        return processed_tweets, filtered_tweets

    async def process_queue(self, batch_size: int = 100, timeout: int = 0) -> Tuple[int, int]:
        """
        پردازش توییت‌ها از صف پردازش

        Args:
            batch_size (int): حداکثر تعداد توییت‌ها در هر دسته
            timeout (int): زمان انتظار برای صف به ثانیه (0 = بی‌نهایت)

        Returns:
            Tuple[int, int]: توپل (تعداد توییت‌های پردازش شده، تعداد توییت‌های فیلتر شده)
        """
        logger.info(f"Waiting for tweets in processing queue with timeout {timeout} seconds")

        try:
            # دریافت آیتم از صف با انتظار
            tweet_ids = await self.redis_service.get_from_queue("processing_queue", timeout)

            if not tweet_ids:
                logger.info("No tweets found in processing queue (timeout)")
                return 0, 0

            # محدود کردن تعداد توییت‌ها برای پردازش
            if len(tweet_ids) > batch_size:
                batch_ids = tweet_ids[:batch_size]
                # بازگرداندن باقیمانده به صف
                remaining_ids = tweet_ids[batch_size:]
                await self.redis_service.add_to_processing_queue(remaining_ids)
                logger.info(f"Processing {len(batch_ids)} tweets, returned {len(remaining_ids)} to queue")
            else:
                batch_ids = tweet_ids

            # پردازش دسته
            processed, filtered = await self.process_tweets(batch_ids)
            return len(processed), len(filtered)

        except Exception as e:
            logger.error(f"Error processing tweets from queue: {e}")
            return 0, 0

    async def get_unprocessed_tweets(self, limit: int = 100) -> List[Tweet]:
        """
        دریافت توییت‌های پردازش نشده از دیتابیس

        Args:
            limit (int): حداکثر تعداد توییت‌ها

        Returns:
            List[Tweet]: لیست توییت‌های پردازش نشده
        """
        stmt = select(Tweet).where(
            Tweet.is_processed == False
        ).order_by(
            Tweet.created_at.desc()
        ).limit(limit)

        result = await self.db_session.execute(stmt)
        return result.scalars().all()

    async def process_unprocessed_tweets(self, limit: int = 100) -> Tuple[int, int]:
        """
        پردازش توییت‌های پردازش نشده در دیتابیس

        Args:
            limit (int): حداکثر تعداد توییت‌ها

        Returns:
            Tuple[int, int]: توپل (تعداد توییت‌های پردازش شده، تعداد توییت‌های فیلتر شده)
        """
        # دریافت توییت‌های پردازش نشده
        unprocessed_tweets = await self.get_unprocessed_tweets(limit)

        if not unprocessed_tweets:
            logger.info("No unprocessed tweets found in database")
            return 0, 0

        # پردازش توییت‌ها
        tweet_ids = [tweet.id for tweet in unprocessed_tweets]
        processed, filtered = await self.process_tweets(tweet_ids)

        return len(processed), len(filtered)

    async def run_processor(self, batch_size: int = 100, sleep_time: int = 10) -> None:
        """
        اجرای پردازشگر به صورت مداوم

        Args:
            batch_size (int): حداکثر تعداد توییت‌ها در هر دسته
            sleep_time (int): زمان انتظار بین دسته‌ها به ثانیه
        """
        logger.info(f"Starting continuous tweet processor with batch size {batch_size}")

        try:
            while True:
                # ابتدا از صف برداشت می‌کنیم
                processed_queue, filtered_queue = await self.process_queue(batch_size, timeout=sleep_time)

                # اگر صف خالی بود، توییت‌های پردازش نشده در دیتابیس را پردازش می‌کنیم
                if processed_queue == 0 and filtered_queue == 0:
                    processed_db, filtered_db = await self.process_unprocessed_tweets(batch_size)

                    if processed_db > 0 or filtered_db > 0:
                        logger.info(f"Processed {processed_db} tweets from database, filtered {filtered_db}")
                    else:
                        # اگر هیچ توییتی برای پردازش نبود، کمی صبر می‌کنیم
                        logger.debug("No tweets to process, sleeping...")
                        await asyncio.sleep(sleep_time)
                else:
                    logger.info(f"Processed {processed_queue} tweets from queue, filtered {filtered_queue}")

        except asyncio.CancelledError:
            logger.info("Tweet processor task cancelled")
        except Exception as e:
            logger.error(f"Error in tweet processor: {e}")
            raise