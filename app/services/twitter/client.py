"""
کلاینت TwitterAPI.io برای ارتباط با API توییتر.

این ماژول ارتباط با TwitterAPI.io را فراهم می‌کند و امکان جمع‌آوری توییت‌ها،
اطلاعات کاربران و سایر داده‌های توییتر را فراهم می‌کند.
"""

import logging
import asyncio
from typing import Dict, List, Any, Optional, Union
from urllib.parse import urlencode
import httpx

from app.config import settings


from app.services.twitter.models import TwitterSearchResponse, TwitterUserResponse,TwitterUserBatchResponse, TwitterError, TwitterWebhookRule, TwitterWebhookResponse

logger = logging.getLogger(__name__)


class TwitterAPIClient:
    """
    کلاینت برای ارتباط با TwitterAPI.io

    این کلاس امکان ارتباط با API های TwitterAPI.io را فراهم می‌کند و
    متدهای لازم برای جمع‌آوری توییت‌ها، اطلاعات کاربران و سایر داده‌ها را ارائه می‌دهد.

    Attributes:
        api_key (str): کلید API برای TwitterAPI.io
        base_url (str): آدرس پایه API
        headers (Dict): هدرهای HTTP پیش‌فرض
        client (httpx.AsyncClient): کلاینت HTTP برای ارتباطات ناهمگام
    """

    def __init__(
            self,
            api_key: str = None,
            base_url: str = None,
            timeout: float = 30.0
    ):
        """
        مقداردهی اولیه کلاینت Twitter API

        Args:
            api_key (str, optional): کلید API برای TwitterAPI.io. اگر مشخص نشود، از تنظیمات استفاده می‌شود.
            base_url (str, optional): آدرس پایه API. اگر مشخص نشود، از تنظیمات استفاده می‌شود.
            timeout (float): زمان انتظار برای پاسخ به ثانیه
        """
        self.api_key = api_key or settings.TWITTER_API_KEY
        self.base_url = base_url or settings.TWITTER_API_BASE_URL
        self.headers = {"X-API-Key": self.api_key}
        self.client = httpx.AsyncClient(headers=self.headers, timeout=timeout)
        logger.info(f"TwitterAPIClient initialized with base URL: {self.base_url}")

    async def search_tweets(
            self,
            query: str,
            query_type: str = "Latest",
            cursor: str = "",
            max_results: int = 100
    ) -> TwitterSearchResponse:
        """
        جستجوی توییت بر اساس عبارت جستجو

        Args:
            query (str): عبارت جستجو
            query_type (str): نوع جستجو ("Latest" یا "Top")
            cursor (str): نشانگر صفحه‌بندی
            max_results (int): حداکثر نتایج درخواستی

        Returns:
            TwitterSearchResponse: آبجکت پاسخ حاوی نتایج جستجو و اطلاعات صفحه‌بندی

        Raises:
            httpx.HTTPStatusError: در صورت خطای HTTP
            Exception: در صورت سایر خطاها
        """
        url = f"{self.base_url}/twitter/tweet/advanced_search"
        params = {
            "query": query,
            "queryType": query_type,
            "cursor": cursor
        }

        try:
            logger.debug(f"Searching tweets with query: {query}, cursor: {cursor}")
            response = await self.client.get(url, params=params, timeout=45.0)
            response.raise_for_status()
            data = response.json()
            logger.debug(f"Found {len(data.get('data', {}).get('tweets', []))} tweets")
            return TwitterSearchResponse(data=data.get('data', {}))
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP Error: {e.response.status_code} - {e.response.text}")
            raise
        except Exception as e:
            logger.error(f"Error searching tweets: {e}")
            raise

    async def get_user_info(self, username: str) -> TwitterUserResponse:
        """
        دریافت اطلاعات کاربر بر اساس نام کاربری

        Args:
            username (str): نام کاربری توییتر

        Returns:
            TwitterUserResponse: آبجکت پاسخ حاوی اطلاعات کاربر

        Raises:
            httpx.HTTPStatusError: در صورت خطای HTTP
            Exception: در صورت سایر خطاها
        """
        url = f"{self.base_url}/twitter/user/info"
        params = {"userName": username}

        try:
            logger.debug(f"Getting user info for username: {username}")
            response = await self.client.get(url, params=params)
            response.raise_for_status()
            data = response.json()
            return TwitterUserResponse(data=data.get('data', {}))
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP Error: {e.response.status_code} - {e.response.text}")
            raise
        except Exception as e:
            logger.error(f"Error getting user info: {e}")
            raise

    async def get_users_batch(self, user_ids: List[str]) -> TwitterUserBatchResponse:
        """
        دریافت اطلاعات چندین کاربر به صورت دسته‌ای

        Args:
            user_ids (List[str]): لیست شناسه‌های کاربران

        Returns:
            TwitterUserBatchResponse: آبجکت پاسخ حاوی اطلاعات کاربران

        Raises:
            httpx.HTTPStatusError: در صورت خطای HTTP
            Exception: در صورت سایر خطاها
        """
        url = f"{self.base_url}/twitter/user/batch_info_by_ids"
        params = {"userIds": ",".join(user_ids)}

        try:
            logger.debug(f"Getting batch user info for {len(user_ids)} users")
            response = await self.client.get(url, params=params)
            response.raise_for_status()
            data = response.json()
            return TwitterUserBatchResponse(data=data.get('data', []))
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP Error: {e.response.status_code} - {e.response.text}")
            raise
        except Exception as e:
            logger.error(f"Error getting batch user info: {e}")
            raise

    async def get_user_tweets(
            self,
            username: str = None,
            user_id: str = None,
            include_replies: bool = False,
            cursor: str = ""
    ) -> TwitterSearchResponse:
        """
        دریافت توییت‌های اخیر یک کاربر

        Args:
            username (str, optional): نام کاربری توییتر
            user_id (str, optional): شناسه کاربر
            include_replies (bool): آیا پاسخ‌ها شامل شوند؟
            cursor (str): نشانگر صفحه‌بندی

        Returns:
            TwitterSearchResponse: آبجکت پاسخ حاوی توییت‌های کاربر

        Raises:
            ValueError: اگر هیچ یک از username یا user_id مشخص نشود
            httpx.HTTPStatusError: در صورت خطای HTTP
            Exception: در صورت سایر خطاها
        """
        if not username and not user_id:
            raise ValueError("Either username or user_id must be provided")

        url = f"{self.base_url}/twitter/user/last_tweets"
        params = {
            "includeReplies": include_replies,
            "cursor": cursor
        }

        if username:
            params["userName"] = username
        if user_id:
            params["userId"] = user_id

        try:
            logger.debug(f"Getting tweets for user: {username or user_id}")
            response = await self.client.get(url, params=params)
            response.raise_for_status()
            data = response.json()
            return TwitterSearchResponse(data=data.get('data', {}))
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP Error: {e.response.status_code} - {e.response.text}")
            raise
        except Exception as e:
            logger.error(f"Error getting user tweets: {e}")
            raise

    async def get_tweet_replies(
            self,
            tweet_id: str,
            since_time: Optional[int] = None,
            until_time: Optional[int] = None,
            cursor: str = ""
    ) -> TwitterSearchResponse:
        """
        دریافت پاسخ‌های یک توییت

        Args:
            tweet_id (str): شناسه توییت
            since_time (int, optional): زمان شروع به صورت تایم‌استمپ یونیکس
            until_time (int, optional): زمان پایان به صورت تایم‌استمپ یونیکس
            cursor (str): نشانگر صفحه‌بندی

        Returns:
            TwitterSearchResponse: آبجکت پاسخ حاوی پاسخ‌ها و اطلاعات صفحه‌بندی

        Raises:
            httpx.HTTPStatusError: در صورت خطای HTTP
            Exception: در صورت سایر خطاها
        """
        url = f"{self.base_url}/twitter/tweet/replies"
        params = {
            "tweetId": tweet_id,
            "cursor": cursor
        }

        if since_time:
            params["sinceTime"] = since_time
        if until_time:
            params["untilTime"] = until_time

        try:
            logger.debug(f"Getting replies for tweet: {tweet_id}")
            response = await self.client.get(url, params=params)
            response.raise_for_status()
            data = response.json()
            return TwitterSearchResponse(data=data.get('data', {}))
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP Error: {e.response.status_code} - {e.response.text}")
            raise
        except Exception as e:
            logger.error(f"Error getting tweet replies: {e}")
            raise

    async def setup_webhook(
            self,
            tag: str,
            value: str,
            interval_seconds: int = 300,
            webhook_url: Optional[str] = None
    ) -> TwitterWebhookResponse:
        """
        تنظیم وبهوک برای پایش خودکار

        Args:
            tag (str): برچسب قانون
            value (str): قانون فیلترینگ
            interval_seconds (int): فاصله زمانی بررسی (ثانیه)
            webhook_url (str, optional): آدرس وبهوک

        Returns:
            TwitterWebhookResponse: آبجکت پاسخ حاوی اطلاعات قانون ایجاد شده

        Raises:
            httpx.HTTPStatusError: در صورت خطای HTTP
            Exception: در صورت سایر خطاها
        """
        # اعتبارسنجی پارامترها
        rule = TwitterWebhookRule(
            tag=tag,
            value=value,
            interval_seconds=max(100, interval_seconds)
        )

        # ابتدا قانون را اضافه می‌کنیم
        add_rule_url = f"{self.base_url}/oapi/tweet_filter/add_rule"
        add_rule_payload = rule.model_dump()

        try:
            logger.info(f"Setting up webhook with tag: {tag}, value: {value}")
            response = await self.client.post(
                add_rule_url,
                json=add_rule_payload
            )
            response.raise_for_status()
            rule_response = response.json()

            # اگر وبهوک URL ارائه شده باشد، آن را ثبت می‌کنیم
            if webhook_url and rule_response.get("status") == "success":
                rule_id = rule_response.get("rule_id")
                register_url = f"{self.base_url}/oapi/tweet_filter/register_webhook"
                register_payload = {
                    "rule_id": rule_id,
                    "webhook_url": webhook_url
                }

                webhook_response = await self.client.post(
                    register_url,
                    json=register_payload
                )
                webhook_response.raise_for_status()
                logger.info(f"Webhook registered successfully for rule ID: {rule_id}")
                return TwitterWebhookResponse(**webhook_response.json())

            logger.info(f"Rule created with ID: {rule_response.get('rule_id')}")
            return TwitterWebhookResponse(**rule_response)

        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP Error: {e.response.status_code} - {e.response.text}")
            raise
        except Exception as e:
            logger.error(f"Error setting up webhook: {e}")
            raise

    async def close(self) -> None:
        """بستن کلاینت HTTP"""
        await self.client.aclose()
        logger.debug("TwitterAPIClient connection closed")
