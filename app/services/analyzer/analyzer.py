"""
سرویس تحلیل توییت‌ها.

این ماژول سرویس اصلی تحلیل توییت‌ها را پیاده‌سازی می‌کند که شامل تحلیل احساسات،
شناسایی موضوعات، تشخیص موج‌ها و تولید گزارش‌های تحلیلی است.
"""

import logging
import json
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple, Union
import asyncio
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import update, and_, or_, func, desc
import math

from app.config import settings
from app.db.models import Tweet, User, Keyword, Topic, TweetTopic, Alert, ApiUsage
from app.services.analyzer.claude_client import ClaudeClient
from app.services.analyzer.cost_manager import CostManager, ApiType, AnalysisType
from app.services.analyzer.wave_detector import WaveDetector

logger = logging.getLogger(__name__)


class TweetAnalyzer:
    """
    سرویس تحلیل توییت‌ها

    این کلاس سرویس اصلی تحلیل توییت‌ها را پیاده‌سازی می‌کند که شامل تحلیل احساسات،
    شناسایی موضوعات، تشخیص موج‌ها و تولید گزارش‌های تحلیلی است.

    Attributes:
        db_session (AsyncSession): نشست دیتابیس
        claude_client (ClaudeClient): کلاینت Claude API
        cost_manager (CostManager): مدیریت هزینه API
        wave_detector (WaveDetector): تشخیص موج‌های توییتری
        batch_size (int): اندازه دسته برای پردازش توییت‌ها
    """

    def __init__(
            self,
            db_session: AsyncSession,
            claude_client: ClaudeClient = None,
            cost_manager: CostManager = None,
            wave_detector: WaveDetector = None,
            batch_size: int = 50
    ):
        """
        مقداردهی اولیه سرویس تحلیل

        Args:
            db_session (AsyncSession): نشست دیتابیس
            claude_client (ClaudeClient, optional): کلاینت Claude API
            cost_manager (CostManager, optional): مدیریت هزینه API
            wave_detector (WaveDetector, optional): تشخیص موج‌ها
            batch_size (int): اندازه دسته برای پردازش توییت‌ها
        """
        self.db_session = db_session
        self.claude_client = claude_client or ClaudeClient()
        self.cost_manager = cost_manager or CostManager(db_session)
        self.wave_detector = wave_detector or WaveDetector(db_session)
        self.batch_size = batch_size or settings.ANALYZER_BATCH_SIZE
        logger.info(f"TweetAnalyzer initialized with batch size: {self.batch_size}")

    async def initialize(self) -> None:
        """
        مقداردهی اولیه و اتصال به سرویس‌ها
        """
        # مقداردهی مدیریت هزینه
        await self.cost_manager.initialize()
        logger.info("TweetAnalyzer initialization completed")

    async def close(self) -> None:
        """
        بستن اتصالات و آزادسازی منابع
        """
        await self.claude_client.close()
        logger.info("TweetAnalyzer closed")

    async def analyze_tweet(self, tweet_id: int) -> Dict[str, Any]:
        """
        تحلیل یک توییت

        Args:
            tweet_id (int): شناسه توییت

        Returns:
            Dict[str, Any]: نتایج تحلیل

        Raises:
            ValueError: اگر توییت یافت نشود
        """
        # دریافت توییت از دیتابیس
        stmt = select(Tweet).where(Tweet.id == tweet_id)
        result = await self.db_session.execute(stmt)
        tweet = result.scalar_one_or_none()

        if not tweet:
            raise ValueError(f"Tweet with ID {tweet_id} not found")

        # بررسی اینکه آیا توییت قبلاً تحلیل شده است
        if tweet.is_analyzed and tweet.sentiment_score is not None:
            logger.info(f"Tweet {tweet_id} already analyzed, returning existing results")
            return {
                "tweet_id": tweet.id,
                "sentiment": {
                    "label": tweet.sentiment_label,
                    "score": tweet.sentiment_score
                },
                "is_analyzed": True
            }

        logger.info(f"Analyzing tweet {tweet_id}")

        # استفاده از Claude API برای تحلیل احساسات
        text = tweet.content
        language = tweet.language or "auto"

        # انتخاب مدل بهینه براساس طول متن و اهمیت
        is_important = tweet.importance_score is not None and tweet.importance_score > 0.7
        model, estimation = self.cost_manager.select_optimal_model(
            AnalysisType.SENTIMENT,
            len(text),
            is_important=is_important
        )

        # بهتر است از claude_client استفاده کنیم
        sentiment_result = await self.claude_client.analyze_sentiment(text, language)

        # ثبت استفاده از API
        await self.cost_manager.record_usage(
            api_type=ApiType.CLAUDE,
            operation="analyze_sentiment",
            tokens_in=estimation["tokens_in"],
            tokens_out=estimation["tokens_out"],
            cost=estimation["estimated_cost"]
        )

        # استخراج نتایج
        sentiment_label = sentiment_result.get("sentiment", "neutral")
        sentiment_score = sentiment_result.get("score", 0.0)

        # تحلیل موضوعات اگر توییت مهم باشد
        topics_result = {}
        if is_important:
            # تحلیل موضوعات
            topics_result = await self.claude_client.extract_topics(text, language)

            # ثبت استفاده از API
            topic_model, topic_estimation = self.cost_manager.select_optimal_model(
                AnalysisType.TOPICS,
                len(text),
                is_important=is_important
            )

            await self.cost_manager.record_usage(
                api_type=ApiType.CLAUDE,
                operation="extract_topics",
                tokens_in=topic_estimation["tokens_in"],
                tokens_out=topic_estimation["tokens_out"],
                cost=topic_estimation["estimated_cost"]
            )

            # ذخیره موضوعات در دیتابیس
            if "topics" in topics_result:
                for topic_data in topics_result.get("topics", []):
                    topic_title = topic_data.get("title")
                    if topic_title:
                        # بررسی وجود موضوع
                        stmt = select(Topic).where(Topic.name == topic_title)
                        result = await self.db_session.execute(stmt)
                        topic = result.scalar_one_or_none()

                        if not topic:
                            # ایجاد موضوع جدید
                            topic = Topic(
                                name=topic_title,
                                description=topic_data.get("keywords", [])[:10]
                                # استفاده از کلیدواژه‌ها به عنوان توضیحات
                            )
                            self.db_session.add(topic)
                            await self.db_session.flush()

                        # ایجاد ارتباط بین توییت و موضوع
                        tweet_topic = TweetTopic(
                            tweet_id=tweet.id,
                            topic_id=topic.id,
                            relevance_score=topic_data.get("relevance", 1.0)
                        )
                        self.db_session.add(tweet_topic)

        # به‌روزرسانی توییت با نتایج تحلیل
        tweet.sentiment_label = sentiment_label
        tweet.sentiment_score = sentiment_score
        tweet.is_analyzed = True

        # ذخیره تغییرات
        await self.db_session.commit()

        # برگرداندن نتایج
        return {
            "tweet_id": tweet.id,
            "sentiment": {
                "label": sentiment_label,
                "score": sentiment_score,
                "explanation": sentiment_result.get("explanation", "")
            },
            "topics": topics_result.get("topics", []),
            "main_topic": topics_result.get("main_topic", ""),
            "keywords": topics_result.get("keywords", []),
            "is_analyzed": True
        }

    async def batch_analyze_tweets(self, tweet_ids: List[int]) -> List[Dict[str, Any]]:
        """
        تحلیل دسته‌ای توییت‌ها

        Args:
            tweet_ids (List[int]): لیست شناسه‌های توییت‌ها

        Returns:
            List[Dict[str, Any]]: نتایج تحلیل
        """
        if not tweet_ids:
            return []

        logger.info(f"Batch analyzing {len(tweet_ids)} tweets")

        # دریافت توییت‌ها از دیتابیس
        stmt = select(Tweet).where(Tweet.id.in_(tweet_ids))
        result = await self.db_session.execute(stmt)
        tweets = result.scalars().all()

        if not tweets:
            logger.warning("No tweets found for batch analysis")
            return []

        # جداسازی توییت‌های تحلیل شده و نشده
        analyzed_tweets = [t for t in tweets if t.is_analyzed and t.sentiment_score is not None]
        unanalyzed_tweets = [t for t in tweets if not t.is_analyzed or t.sentiment_score is None]

        logger.info(f"Found {len(analyzed_tweets)} already analyzed tweets and {len(unanalyzed_tweets)} to analyze")

        # اگر همه توییت‌ها قبلاً تحلیل شده‌اند، نتایج موجود را برمی‌گردانیم
        if not unanalyzed_tweets:
            return [
                {
                    "tweet_id": tweet.id,
                    "sentiment": {
                        "label": tweet.sentiment_label,
                        "score": tweet.sentiment_score
                    },
                    "is_analyzed": True
                }
                for tweet in analyzed_tweets
            ]

        # بررسی بودجه قبل از تحلیل
        budget_status = await self.cost_manager.check_budget()
        if budget_status["is_exhausted"]:
            logger.warning("Daily budget exhausted, using cheaper analysis or skipping")
            # می‌توانیم تحلیل محدودتری انجام دهیم یا درخواست را رد کنیم

        # استخراج متون و زبان‌ها
        texts = [tweet.content for tweet in unanalyzed_tweets]

        # تعیین زبان غالب
        language_counts = {}
        for tweet in unanalyzed_tweets:
            lang = tweet.language or "auto"
            language_counts[lang] = language_counts.get(lang, 0) + 1

        dominant_language = max(language_counts.items(), key=lambda x: x[1])[0] if language_counts else "auto"

        # تخمین هزینه و انتخاب مدل بهینه
        model, estimation = self.cost_manager.select_optimal_model(
            AnalysisType.SENTIMENT,
            sum(len(text) for text in texts),
            is_batch=True,
            items_count=len(texts)
        )

        # تحلیل دسته‌ای احساسات
        sentiment_results = await self.claude_client.analyze_batch(
            texts,
            analysis_type="sentiment",
            language=dominant_language
        )

        # ثبت استفاده از API
        await self.cost_manager.record_usage(
            api_type=ApiType.CLAUDE,
            operation="batch_analyze_sentiment",
            tokens_in=estimation["tokens_in"],
            tokens_out=estimation["tokens_out"],
            cost=estimation["estimated_cost"]
        )

        # به‌روزرسانی توییت‌ها با نتایج تحلیل
        results = []

        for i, tweet in enumerate(unanalyzed_tweets):
            # یافتن نتیجه مربوطه
            result = None
            for res in sentiment_results:
                if res.get("index") == i:
                    result = res
                    break

            if not result or "sentiment" not in result:
                logger.warning(f"No valid result found for tweet {tweet.id}")
                continue

            # استخراج نتایج
            sentiment_data = result.get("sentiment", {})
            sentiment_label = sentiment_data.get("sentiment", "neutral")
            sentiment_score = sentiment_data.get("score", 0.0)

            # به‌روزرسانی توییت
            tweet.sentiment_label = sentiment_label
            tweet.sentiment_score = sentiment_score
            tweet.is_analyzed = True

            # افزودن به نتایج
            results.append({
                "tweet_id": tweet.id,
                "sentiment": {
                    "label": sentiment_label,
                    "score": sentiment_score,
                    "confidence": sentiment_data.get("confidence", 0.0)
                },
                "is_analyzed": True
            })

        # ذخیره تغییرات
        await self.db_session.commit()

        # ترکیب نتایج توییت‌های از قبل تحلیل شده
        for tweet in analyzed_tweets:
            results.append({
                "tweet_id": tweet.id,
                "sentiment": {
                    "label": tweet.sentiment_label,
                    "score": tweet.sentiment_score
                },
                "is_analyzed": True
            })

        logger.info(f"Completed batch analysis for {len(results)} tweets")
        return results

    async def process_analysis_queue(self, batch_size: int = None) -> int:
        """
        پردازش توییت‌های صف تحلیل

        Args:
            batch_size (int, optional): اندازه دسته. اگر مشخص نشود، از مقدار پیش‌فرض استفاده می‌شود.

        Returns:
            int: تعداد توییت‌های تحلیل شده
        """
        batch_size = batch_size or self.batch_size
        logger.info(f"Processing analysis queue with batch size {batch_size}")

        # دریافت توییت‌های پردازش شده اما تحلیل نشده
        stmt = select(Tweet.id).where(
            Tweet.is_processed == True,
            Tweet.is_analyzed == False
        ).order_by(
            Tweet.importance_score.desc().nullslast(),
            Tweet.created_at.desc()
        ).limit(batch_size)

        result = await self.db_session.execute(stmt)
        tweet_ids = [row[0] for row in result.fetchall()]

        if not tweet_ids:
            logger.info("No tweets found in analysis queue")
            return 0

        # تحلیل دسته‌ای توییت‌ها
        results = await self.batch_analyze_tweets(tweet_ids)

        return len(results)

    async def run_analyzer(self, sleep_time: int = 60) -> None:
        """
        اجرای تحلیلگر به صورت مداوم

        Args:
            sleep_time (int): زمان انتظار بین دسته‌ها به ثانیه
        """
        logger.info(f"Starting continuous tweet analyzer with sleep time {sleep_time}s")

        try:
            while True:
                # بررسی بودجه
                budget_status = await self.cost_manager.check_budget()
                if budget_status["is_exhausted"]:
                    logger.warning("Daily budget exhausted, sleeping longer...")
                    await asyncio.sleep(sleep_time * 5)  # انتظار طولانی‌تر در صورت اتمام بودجه
                    continue

                # پردازش صف تحلیل
                analyzed_count = await self.process_analysis_queue()

                if analyzed_count > 0:
                    logger.info(f"Analyzed {analyzed_count} tweets from queue")

                    # اجرای تشخیص موج بعد از تحلیل توییت‌ها
                    if analyzed_count >= 20:  # اگر تعداد کافی توییت تحلیل شده باشد
                        try:
                            alerts = await self.detect_waves_and_alert()
                            if alerts:
                                logger.info(f"Created {len(alerts)} alerts from detected waves")
                        except Exception as e:
                            logger.error(f"Error detecting waves: {e}")

                    # انتظار کوتاه بین دسته‌ها
                    await asyncio.sleep(max(1, sleep_time // 10))
                else:
                    # اگر توییتی برای تحلیل نبود، انتظار طولانی‌تر
                    logger.debug("No tweets to analyze, sleeping...")
                    await asyncio.sleep(sleep_time)

        except asyncio.CancelledError:
            logger.info("Tweet analyzer task cancelled")
        except Exception as e:
            logger.error(f"Error in tweet analyzer: {e}")
            raise

    async def generate_report(
            self,
            keywords: Optional[List[str]] = None,
            hours_back: int = 24,
            include_tweets: bool = True
    ) -> Dict[str, Any]:
        """
        تولید گزارش تحلیلی

        Args:
            keywords (Optional[List[str]]): کلیدواژه‌ها برای فیلتر کردن
            hours_back (int): تعداد ساعات برای بررسی
            include_tweets (bool): آیا توییت‌های مهم در گزارش گنجانده شوند؟

        Returns:
            Dict[str, Any]: گزارش تحلیلی
        """
        logger.info(f"Generating report for the past {hours_back} hours")

        # محاسبه زمان شروع و پایان
        end_time = datetime.utcnow()
        start_time = end_time - timedelta(hours=hours_back)

        # شرط زمانی
        time_condition = and_(
            Tweet.created_at >= start_time,
            Tweet.created_at <= end_time,
            Tweet.is_analyzed == True
        )

        # شرط کلیدواژه
        keyword_condition = None
        if keywords:
            # دریافت شناسه‌های کلیدواژه‌ها
            stmt = select(Keyword.id).where(Keyword.text.in_(keywords))
            result = await self.db_session.execute(stmt)
            keyword_ids = [row[0] for row in result.fetchall()]

            if keyword_ids:
                # توییت‌هایی که با این کلیدواژه‌ها مرتبط هستند
                from sqlalchemy import exists
                keyword_condition = exists().where(
                    and_(
                        TweetKeyword.tweet_id == Tweet.id,
                        TweetKeyword.keyword_id.in_(keyword_ids)
                    )
                )

        # ترکیب شرط‌ها
        if keyword_condition:
            query_condition = and_(time_condition, keyword_condition)
        else:
            query_condition = time_condition

        # دریافت آمار کلی
        stmt = select(
            func.count(),
            func.avg(Tweet.sentiment_score),
            func.count().filter(Tweet.sentiment_label == "positive"),
            func.count().filter(Tweet.sentiment_label == "negative"),
            func.count().filter(Tweet.sentiment_label == "neutral"),
            func.count().filter(Tweet.sentiment_label == "mixed")
        ).where(query_condition)

        result = await self.db_session.execute(stmt)
        row = result.fetchone()

        total_tweets = row[0] or 0
        avg_sentiment = row[1] or 0
        positive_count = row[2] or 0
        negative_count = row[3] or 0
        neutral_count = row[4] or 0
        mixed_count = row[5] or 0

        # محاسبه توزیع احساسات
        sentiment_distribution = {}
        if total_tweets > 0:
            sentiment_distribution = {
                "positive": positive_count / total_tweets,
                "negative": negative_count / total_tweets,
                "neutral": neutral_count / total_tweets,
                "mixed": mixed_count / total_tweets
            }

        # دریافت توییت‌های مهم
        important_tweets = []
        if include_tweets and total_tweets > 0:
            stmt = select(Tweet).where(query_condition).order_by(
                Tweet.importance_score.desc().nullslast()
            ).limit(10)

            result = await self.db_session.execute(stmt)
            tweets = result.scalars().all()

            important_tweets = [
                {
                    "id": tweet.id,
                    "tweet_id": tweet.tweet_id,
                    "content": tweet.content,
                    "user_id": tweet.user_id,
                    "sentiment_label": tweet.sentiment_label,
                    "sentiment_score": tweet.sentiment_score,
                    "importance_score": tweet.importance_score,
                    "created_at": tweet.created_at.isoformat() if tweet.created_at else None
                }
                for tweet in tweets
            ]

        # دریافت موضوعات اصلی
        top_topics = []
        stmt = select(
            Topic.name,
            func.count(TweetTopic.tweet_id).label("count"),
            func.avg(TweetTopic.relevance_score).label("avg_relevance")
        ).join(
            TweetTopic, Topic.id == TweetTopic.topic_id
        ).join(
            Tweet, Tweet.id == TweetTopic.tweet_id
        ).where(
            query_condition
        ).group_by(
            Topic.name
        ).order_by(
            func.count(TweetTopic.tweet_id).desc()
        ).limit(5)

        result = await self.db_session.execute(stmt)
        topics = result.fetchall()

        top_topics = [
            {
                "name": row[0],
                "count": row[1],
                "percentage": row[1] / total_tweets if total_tweets > 0 else 0,
                "avg_relevance": row[2]
            }
            for row in topics
        ]

        # ایجاد گزارش نهایی
        report = {
            "timeframe": {
                "start": start_time.isoformat(),
                "end": end_time.isoformat(),
                "hours": hours_back
            },
            "keywords": keywords,
            "summary": {
                "total_tweets": total_tweets,
                "avg_sentiment": avg_sentiment,
                "sentiment_distribution": sentiment_distribution
            },
            "top_topics": top_topics,
            "important_tweets": important_tweets
        }

        logger.info(f"Report generated with {total_tweets} tweets")
        return report

    async def detect_waves_and_alert(
            self,
            keywords: Optional[List[str]] = None,
            hours_back: int = 6,
            min_importance: float = 3.0
    ) -> List[Dict[str, Any]]:
        """
        تشخیص موج‌های توییتری و ایجاد هشدار

        Args:
            keywords (Optional[List[str]]): کلیدواژه‌ها برای فیلتر کردن
            hours_back (int): تعداد ساعات برای بررسی
            min_importance (float): حداقل امتیاز اهمیت برای ایجاد هشدار

        Returns:
            List[Dict[str, Any]]: لیست هشدارهای ایجاد شده
        """
        logger.info(f"Detecting waves and creating alerts for past {hours_back} hours")

        # استفاده از wave_detector برای تشخیص موج‌ها و ایجاد هشدار
        alerts = await self.wave_detector.run_detection_and_create_alerts(
            keywords=keywords,
            hours_back=hours_back,
            min_importance=min_importance
        )

        return alerts