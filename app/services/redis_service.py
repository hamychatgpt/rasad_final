"""
سرویس Redis.

این ماژول عملیات کش‌گذاری، صف‌بندی و pub/sub با استفاده از Redis را پیاده‌سازی می‌کند.
"""

import json
import logging
from typing import Any, Dict, List, Optional, Union
import redis.asyncio as redis
from redis.asyncio.client import Redis

from app.config import settings

logger = logging.getLogger(__name__)


class RedisService:
    """
    سرویس عملیات Redis

    این کلاس عملیات کش‌گذاری، صف‌بندی و pub/sub با استفاده از Redis را فراهم می‌کند.

    Attributes:
        redis_client (Redis): کلاینت ارتباط با Redis
    """

    def __init__(self, url: str = None):
        """
        مقداردهی اولیه سرویس Redis

        Args:
            url (str, optional): آدرس اتصال به Redis. اگر مشخص نشود، از تنظیمات استفاده می‌شود.
        """
        self.redis_url = url or settings.REDIS_URL
        self.redis_client = None
        logger.info(f"RedisService initialized with URL: {self.redis_url}")

    async def connect(self) -> None:
        """برقراری اتصال به Redis"""
        if self.redis_client is None:
            try:
                self.redis_client = await redis.from_url(
                    self.redis_url,
                    encoding="utf-8",
                    decode_responses=True
                )
                logger.info("Connected to Redis")
            except Exception as e:
                logger.error(f"Failed to connect to Redis: {e}")
                raise

    async def disconnect(self) -> None:
        """قطع اتصال از Redis"""
        if self.redis_client:
            await self.redis_client.close()
            self.redis_client = None
            logger.info("Disconnected from Redis")

    async def _get_client(self) -> Redis:
        """
        دریافت کلاینت Redis (با برقراری اتصال در صورت نیاز)

        Returns:
            Redis: کلاینت Redis
        """
        if self.redis_client is None:
            await self.connect()
        return self.redis_client

    async def set_cache(self, key: str, value: Any, expire: int = None) -> bool:
        """
        ذخیره‌سازی داده در کش

        Args:
            key (str): کلید کش
            value (Any): مقدار برای ذخیره‌سازی (تبدیل به JSON می‌شود)
            expire (int, optional): زمان انقضا به ثانیه

        Returns:
            bool: نتیجه عملیات
        """
        client = await self._get_client()
        try:
            serialized_value = json.dumps(value) if not isinstance(value, str) else value
            if expire:
                await client.setex(key, expire, serialized_value)
            else:
                await client.set(key, serialized_value)
            logger.debug(f"Set cache for key: {key}")
            return True
        except Exception as e:
            logger.error(f"Error setting cache for key {key}: {e}")
            return False

    async def get_cache(self, key: str) -> Optional[Any]:
        """
        دریافت داده از کش

        Args:
            key (str): کلید کش

        Returns:
            Optional[Any]: مقدار دریافت شده یا None اگر کلید وجود نداشته باشد
        """
        client = await self._get_client()
        try:
            value = await client.get(key)
            if value is None:
                return None

            try:
                # تلاش برای تبدیل به JSON
                return json.loads(value)
            except json.JSONDecodeError:
                # اگر JSON نباشد، به همان صورت رشته برگردانده شود
                return value

        except Exception as e:
            logger.error(f"Error getting cache for key {key}: {e}")
            return None

    async def delete_cache(self, key: str) -> bool:
        """
        حذف داده از کش

        Args:
            key (str): کلید کش

        Returns:
            bool: نتیجه عملیات
        """
        client = await self._get_client()
        try:
            await client.delete(key)
            logger.debug(f"Deleted cache for key: {key}")
            return True
        except Exception as e:
            logger.error(f"Error deleting cache for key {key}: {e}")
            return False

    async def add_to_queue(self, queue_name: str, item: Union[str, Dict, List]) -> bool:
        """
        افزودن آیتم به صف

        Args:
            queue_name (str): نام صف
            item (Union[str, Dict, List]): آیتم برای افزودن (تبدیل به JSON می‌شود)

        Returns:
            bool: نتیجه عملیات
        """
        client = await self._get_client()
        try:
            value = json.dumps(item) if not isinstance(item, str) else item
            await client.lpush(queue_name, value)
            logger.debug(f"Added item to queue: {queue_name}")
            return True
        except Exception as e:
            logger.error(f"Error adding to queue {queue_name}: {e}")
            return False

    async def get_from_queue(self, queue_name: str, timeout: int = 0) -> Optional[Any]:
        """
        دریافت آیتم از صف (منتظر می‌ماند اگر صف خالی باشد)

        Args:
            queue_name (str): نام صف
            timeout (int): زمان انتظار به ثانیه (0 = بی‌نهایت)

        Returns:
            Optional[Any]: آیتم دریافت شده یا None اگر timeout رخ دهد
        """
        client = await self._get_client()
        try:
            # استفاده از BRPOP برای انتظار آیتم جدید
            result = await client.brpop([queue_name], timeout=timeout)
            if result is None:
                return None

            queue, value = result

            try:
                # تلاش برای تبدیل به JSON
                return json.loads(value)
            except json.JSONDecodeError:
                # اگر JSON نباشد، به همان صورت رشته برگردانده شود
                return value

        except Exception as e:
            logger.error(f"Error getting from queue {queue_name}: {e}")
            return None

    async def add_to_processing_queue(self, tweet_ids: List[int]) -> bool:
        """
        افزودن توییت‌ها به صف پردازش

        Args:
            tweet_ids (List[int]): لیست شناسه‌های توییت

        Returns:
            bool: نتیجه عملیات
        """
        return await self.add_to_queue("processing_queue", tweet_ids)

    async def add_to_analysis_queue(self, tweet_ids: List[int]) -> bool:
        """
        افزودن توییت‌ها به صف تحلیل

        Args:
            tweet_ids (List[int]): لیست شناسه‌های توییت

        Returns:
            bool: نتیجه عملیات
        """
        return await self.add_to_queue("analysis_queue", tweet_ids)

    async def publish(self, channel: str, message: Union[str, Dict, List]) -> int:
        """
        انتشار پیام در یک کانال

        Args:
            channel (str): نام کانال
            message (Union[str, Dict, List]): پیام برای انتشار (تبدیل به JSON می‌شود)

        Returns:
            int: تعداد کلاینت‌های دریافت‌کننده
        """
        client = await self._get_client()
        try:
            value = json.dumps(message) if not isinstance(message, str) else message
            result = await client.publish(channel, value)
            logger.debug(f"Published message to channel: {channel}")
            return result
        except Exception as e:
            logger.error(f"Error publishing to channel {channel}: {e}")
            return 0

    async def subscribe(self, channel: str) -> redis.client.PubSub:
        """
        مشترک شدن در یک کانال

        Args:
            channel (str): نام کانال

        Returns:
            redis.client.PubSub: آبجکت PubSub
        """
        client = await self._get_client()
        try:
            pubsub = client.pubsub()
            await pubsub.subscribe(channel)
            logger.debug(f"Subscribed to channel: {channel}")
            return pubsub
        except Exception as e:
            logger.error(f"Error subscribing to channel {channel}: {e}")
            raise
