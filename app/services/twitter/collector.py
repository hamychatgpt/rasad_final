"""
سرویس جمع‌آوری توییت.

این ماژول سرویس اصلی برای جمع‌آوری توییت‌ها، پردازش و ذخیره آنها در دیتابیس
و انتقال آنها به صف پردازش را فراهم می‌کند.
"""

import asyncio
import json
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Set, Any, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import insert, update, func
from sqlalchemy.dialects.postgresql import insert as pg_insert

from app.services.twitter.client import TwitterAPIClient
from app.services.twitter.models import Tweet as TweetModel, TwitterUser
from app.db.models import Tweet, User, Keyword, TweetKeyword
from app.services.redis_service import RedisService

logger = logging.getLogger(__name__)


class TweetCollector:
    """
    سرویس جمع‌آوری توییت‌ها

    این کلاس عملیات جمع‌آوری توییت‌ها بر اساس کلیدواژه‌ها، ذخیره‌سازی آنها در دیتابیس
    و ارسال آنها به صف پردازش را انجام می‌دهد.

    Attributes:
        twitter_client (TwitterAPIClient): کلاینت Twitter API
        db_session (AsyncSession): نشست دیتابیس
        redis_service (RedisService): سرویس Redis برای مدیریت صف‌ها و کش
    """

    def __init__(
            self,
            twitter_client: TwitterAPIClient,
            db_session: AsyncSession,
            redis_service: RedisService
    ):
        """
        مقداردهی اولیه سرویس جمع‌آوری توییت

        Args:
            twitter_client (TwitterAPIClient): کلاینت Twitter API
            db_session (AsyncSession): نشست دیتابیس
            redis_service (RedisService): سرویس Redis
        """
        self.twitter_client = twitter_client
        self.db_session = db_session
        self.redis_service = redis_service
        logger.info("TweetCollector initialized")

    async def collect_by_keywords(
            self,
            keywords: List[str],
            days_back: int = 1,
            max_tweets: int = 10000,
            save_to_db: bool = True
    ) -> List[Dict[str, Any]]:
        """
        جمع‌آوری توییت‌ها بر اساس کلیدواژه‌ها

        Args:
            keywords (List[str]): لیست کلیدواژه‌ها
            days_back (int): تعداد روزهای قبل برای جستجو
            max_tweets (int): حداکثر تعداد توییت‌ها
            save_to_db (bool): ذخیره در دیتابیس

        Returns:
            List[Dict[str, Any]]: لیست توییت‌های جمع‌آوری شده
        """
        logger.info(f"Starting collection for {len(keywords)} keywords, looking back {days_back} days")

        # ساخت عبارت جستجو (ترکیب کلیدواژه‌ها با OR)
        query = " OR ".join([f'"{keyword}"' for keyword in keywords])

        # محاسبه بازه زمانی
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days_back)

        date_query = (
            f"{query} "
            f"since:{start_date.strftime('%Y-%m-%d_%H:%M:%S_UTC')} "
            f"until:{end_date.strftime('%Y-%m-%d_%H:%M:%S_UTC')}"
        )

        collected_tweets = []
        unique_tweet_ids = set()
        unique_user_ids = set()
        cursor = ""
        retry_count = 0

        # جمع‌آوری توییت‌ها تا رسیدن به حداکثر یا اتمام نتایج
        while len(collected_tweets) < max_tweets and retry_count < 5:
            try:
                logger.info(f"Fetching tweets with cursor: {cursor}")

                # جستجوی توییت‌ها
                response = await self.twitter_client.search_tweets(
                    query=date_query,
                    query_type="Latest",
                    cursor=cursor
                )

                # بررسی وجود نتایج
                tweets = response.tweets

                if not tweets:
                    logger.info("No more tweets found")

                    # اگر توییت کافی جمع‌آوری نشده و بازه زمانی کوتاه است، افزایش بازه زمانی
                    if len(collected_tweets) < max_tweets and days_back < 7:
                        days_back += 1
                        start_date = end_date - timedelta(days=days_back)
                        date_query = (
                            f"{query} "
                            f"since:{start_date.strftime('%Y-%m-%d_%H:%M:%S_UTC')} "
                            f"until:{end_date.strftime('%Y-%m-%d_%H:%M:%S_UTC')}"
                        )
                        cursor = ""
                        logger.info(f"Increasing time range to {days_back} days")
                        continue
                    else:
                        break

                # پردازش توییت‌ها
                for tweet_data in tweets:
                    tweet_id = tweet_data.get("id")

                    # رد کردن توییت‌های تکراری
                    if tweet_id in unique_tweet_ids:
                        continue

                    unique_tweet_ids.add(tweet_id)
                    collected_tweets.append(tweet_data)

                    # جمع‌آوری شناسه کاربران برای پردازش بعدی
                    user_id = tweet_data.get("author", {}).get("id")
                    if user_id:
                        unique_user_ids.add(user_id)

                # بررسی وجود صفحه بعدی
                cursor = response.next_cursor
                if not cursor:
                    logger.info("No more pages available")
                    break

                # لاگ پیشرفت
                logger.info(f"Collected {len(collected_tweets)} tweets so far")

                # رعایت محدودیت‌های API
                await asyncio.sleep(1)

            except Exception as e:
                logger.error(f"Error collecting tweets: {e}")
                retry_count += 1
                await asyncio.sleep(5)

        logger.info(
            f"Collection completed. Total tweets: {len(collected_tweets)}, unique users: {len(unique_user_ids)}")

        # ذخیره توییت‌ها در دیتابیس
        if save_to_db and collected_tweets:
            await self._save_tweets_to_db(collected_tweets, keywords)

            # جمع‌آوری اطلاعات کاربران به صورت دسته‌ای
            if unique_user_ids:
                await self._collect_user_profiles(list(unique_user_ids))

        return collected_tweets

    async def collect_user_tweets(
            self,
            username: str,
            days_back: int = 7,
            max_tweets: int = 200,
            save_to_db: bool = True
    ) -> List[Dict[str, Any]]:
        """
        جمع‌آوری توییت‌های یک کاربر مشخص

        Args:
            username (str): نام کاربری
            days_back (int): تعداد روزهای قبل برای فیلتر
            max_tweets (int): حداکثر تعداد توییت‌ها
            save_to_db (bool): ذخیره در دیتابیس

        Returns:
            List[Dict[str, Any]]: لیست توییت‌های جمع‌آوری شده
        """
        logger.info(f"Collecting tweets for user @{username}, looking back {days_back} days")

        collected_tweets = []
        cursor = ""

        while len(collected_tweets) < max_tweets:
            try:
                # دریافت توییت‌های کاربر
                response = await self.twitter_client.get_user_tweets(
                    username=username,
                    include_replies=False,
                    cursor=cursor
                )

                tweets = response.tweets

                if not tweets:
                    logger.info(f"No more tweets found for user @{username}")
                    break

                # فیلتر کردن بر اساس تاریخ
                cutoff_date = datetime.now() - timedelta(days=days_back)

                for tweet_data in tweets:
                    # تبدیل داده توییت به مدل پایتونیک
                    tweet = TweetModel.model_validate(tweet_data)

                    if tweet.created_at >= cutoff_date:
                        collected_tweets.append(tweet_data)

                        if len(collected_tweets) >= max_tweets:
                            break

                # بررسی وجود صفحه بعدی
                cursor = response.next_cursor
                if not cursor:
                    break

                logger.info(f"Collected {len(collected_tweets)} tweets for @{username} so far")

                # رعایت محدودیت‌های API
                await asyncio.sleep(1)

            except Exception as e:
                logger.error(f"Error collecting user tweets for @{username}: {e}")
                break

        logger.info(f"Completed collection for user @{username}. Total tweets: {len(collected_tweets)}")

        # ذخیره توییت‌ها در دیتابیس
        if save_to_db and collected_tweets:
            # ابتدا اطلاعات کاربر را ذخیره می‌کنیم
            user_info = await self.twitter_client.get_user_info(username)
            if user_info.user:
                await self._save_user_to_db(user_info.user)

            # سپس توییت‌ها را ذخیره می‌کنیم
            await self._save_tweets_to_db(collected_tweets, [])

        return collected_tweets

    async def _save_tweets_to_db(self, tweets_data: List[Dict[str, Any]], keywords: List[str]) -> None:
        """
        ذخیره توییت‌ها در دیتابیس

        Args:
            tweets_data (List[Dict[str, Any]]): لیست داده‌های توییت
            keywords (List[str]): لیست کلیدواژه‌ها
        """
        logger.info(f"Saving {len(tweets_data)} tweets to database")

        new_tweet_ids = []

        # ذخیره کلیدواژه‌ها یا بازیابی آنها اگر قبلاً ذخیره شده‌اند
        keyword_models = {}
        for keyword_text in keywords:
            # بررسی وجود کلیدواژه در دیتابیس
            stmt = select(Keyword).where(Keyword.text == keyword_text)
            result = await self.db_session.execute(stmt)
            keyword = result.scalar_one_or_none()

            if not keyword:
                # ایجاد کلیدواژه جدید
                keyword = Keyword(text=keyword_text)
                self.db_session.add(keyword)
                await self.db_session.flush()

            keyword_models[keyword_text] = keyword

        # پردازش و ذخیره هر توییت
        for tweet_data in tweets_data:
            # تبدیل به مدل پایتونیک
            try:
                tweet_model = TweetModel.model_validate(tweet_data)
            except Exception as e:
                logger.warning(f"Error validating tweet data: {e}")
                continue

            # بررسی وجود توییت در دیتابیس
            stmt = select(Tweet).where(Tweet.tweet_id == tweet_model.id)
            result = await self.db_session.execute(stmt)
            existing_tweet = result.scalar_one_or_none()

            if existing_tweet:
                logger.debug(f"Tweet {tweet_model.id} already exists, updating")
                # بروزرسانی آمار توییت
                existing_tweet.retweet_count = tweet_model.retweet_count
                existing_tweet.like_count = tweet_model.like_count
                existing_tweet.reply_count = tweet_model.reply_count
                existing_tweet.quote_count = tweet_model.quote_count
                continue

            # استخراج entities توییت اگر وجود داشته باشد
            entities = None
            if "entities" in tweet_data:
                try:
                    entities = json.dumps(tweet_data["entities"])
                except:
                    pass

            # ایجاد مدل توییت
            tweet = Tweet(
                tweet_id=tweet_model.id,
                content=tweet_model.text,
                created_at=tweet_model.created_at,
                language=tweet_model.lang,
                retweet_count=tweet_model.retweet_count,
                like_count=tweet_model.like_count,
                reply_count=tweet_model.reply_count,
                quote_count=tweet_model.quote_count,
                user_id=tweet_model.author.id,
                entities=entities,
                is_processed=False,
                is_analyzed=False
            )

            self.db_session.add(tweet)

            # فلاش برای دریافت ID
            await self.db_session.flush()

            new_tweet_ids.append(tweet.id)

            # ارتباط توییت با کلیدواژه‌ها
            tweet_text = tweet_model.text.lower()
            for keyword_text, keyword_model in keyword_models.items():
                if keyword_text.lower() in tweet_text:
                    tweet_keyword = TweetKeyword(
                        tweet_id=tweet.id,
                        keyword_id=keyword_model.id
                    )
                    self.db_session.add(tweet_keyword)

        # ذخیره تغییرات
        await self.db_session.commit()

        logger.info(f"Saved {len(new_tweet_ids)} new tweets to database")

        # انتقال توییت‌ها به صف پردازش
        if new_tweet_ids:
            await self.redis_service.add_to_processing_queue(new_tweet_ids)
            logger.info(f"Added {len(new_tweet_ids)} tweets to processing queue")

    async def _collect_user_profiles(self, user_ids: List[str], batch_size: int = 100) -> None:
        """
        جمع‌آوری پروفایل کاربران به صورت دسته‌ای

        Args:
            user_ids (List[str]): لیست شناسه‌های کاربران
            batch_size (int): اندازه هر دسته
        """
        logger.info(f"Collecting profiles for {len(user_ids)} users")

        # تقسیم شناسه‌ها به دسته‌های کوچکتر
        for i in range(0, len(user_ids), batch_size):
            batch = user_ids[i:i + batch_size]

            try:
                # دریافت اطلاعات کاربران
                user_data = await self.twitter_client.get_users_batch(batch)
                users = user_data.users

                if not users:
                    logger.warning(f"No user data returned for batch {i // batch_size + 1}")
                    continue

                # ذخیره هر کاربر در دیتابیس
                for user in users:
                    await self._save_user_to_db(user)

                logger.info(f"Saved users from batch {i // batch_size + 1} to database")

                # رعایت محدودیت‌های API
                await asyncio.sleep(1)

            except Exception as e:
                logger.error(f"Error collecting user profiles for batch {i // batch_size + 1}: {e}")
                await asyncio.sleep(5)

    async def _save_user_to_db(self, user_data: Dict[str, Any]) -> Optional[User]:
        """
        ذخیره اطلاعات کاربر در دیتابیس

        Args:
            user_data (Dict[str, Any]): اطلاعات کاربر

        Returns:
            Optional[User]: مدل کاربر ذخیره شده یا None در صورت خطا
        """
        try:
            # تبدیل به مدل پایتونیک
            user_model = TwitterUser.model_validate(user_data)
        except Exception as e:
            logger.warning(f"Error validating user data: {e}")
            return None

        try:
            # استفاده از upsert برای ذخیره کاربر
            stmt = select(User).where(User.user_id == user_model.id)
            result = await self.db_session.execute(stmt)
            existing_user = result.scalar_one_or_none()

            if existing_user:
                # بروزرسانی اطلاعات کاربر
                existing_user.username = user_model.username
                existing_user.display_name = user_model.name
                existing_user.description = user_model.description
                existing_user.followers_count = user_model.followers
                existing_user.following_count = user_model.following
                existing_user.verified = user_model.is_verified
                existing_user.profile_image_url = user_model.profile_image_url
                existing_user.location = user_model.location

                # بروزرسانی زمان ایجاد اگر قبلاً ذخیره نشده
                if user_model.created_at and not existing_user.created_at:
                    existing_user.created_at = user_model.created_at

                await self.db_session.commit()
                logger.debug(f"Updated user @{existing_user.username} in database")
                return existing_user
            else:
                # ایجاد کاربر جدید
                user = User(
                    user_id=user_model.id,
                    username=user_model.username,
                    display_name=user_model.name,
                    description=user_model.description,
                    followers_count=user_model.followers,
                    following_count=user_model.following,
                    verified=user_model.is_verified,
                    profile_image_url=user_model.profile_image_url,
                    location=user_model.location,
                    created_at=user_model.created_at
                )

                self.db_session.add(user)
                await self.db_session.commit()

                logger.debug(f"Added new user @{user.username} to database")
                return user

        except Exception as e:
            logger.error(f"Error saving user to database: {e}")
            await self.db_session.rollback()
            return None

    async def get_active_keywords(self) -> List[str]:
        """
        دریافت لیست کلیدواژه‌های فعال از دیتابیس

        Returns:
            List[str]: لیست کلیدواژه‌های فعال
        """
        stmt = select(Keyword.text).where(Keyword.is_active == True).order_by(Keyword.priority.desc())
        result = await self.db_session.execute(stmt)
        return [row[0] for row in result.fetchall()]

    async def add_keyword(self, text: str, description: str = None, priority: int = 1) -> Keyword:
        """
        افزودن کلیدواژه جدید

        Args:
            text (str): متن کلیدواژه
            description (str): توضیحات کلیدواژه
            priority (int): اولویت کلیدواژه

        Returns:
            Keyword: کلیدواژه ایجاد شده
        """
        # بررسی وجود کلیدواژه
        stmt = select(Keyword).where(Keyword.text == text)
        result = await self.db_session.execute(stmt)
        existing = result.scalar_one_or_none()

        if existing:
            # بروزرسانی کلیدواژه موجود
            existing.is_active = True
            existing.priority = priority
            existing.description = description
            await self.db_session.commit()
            logger.info(f"Updated existing keyword: {text}")
            return existing

        # ایجاد کلیدواژه جدید
        keyword = Keyword(
            text=text,
            description=description,
            priority=priority,
            is_active=True
        )

        self.db_session.add(keyword)
        await self.db_session.commit()

        logger.info(f"Added new keyword: {text}")
        return keyword
