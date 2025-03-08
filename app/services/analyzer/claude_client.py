"""
کلاینت Claude API برای ارتباط با Anthropic Claude.

این ماژول ارتباط با API های Anthropic Claude را فراهم می‌کند و امکان ارسال
درخواست‌های تحلیل متن و دریافت پاسخ‌ها را فراهم می‌کند.
"""

import json
import logging
import httpx
from typing import Dict, List, Any, Optional, Union
from pydantic import BaseModel, Field

from app.config import settings

logger = logging.getLogger(__name__)


class ClaudeMessage(BaseModel):
    """مدل داده پیام برای درخواست به Claude API"""
    role: str
    content: Union[str, List[Dict[str, Any]]]


class ClaudeRequest(BaseModel):
    """مدل داده درخواست به Claude API"""
    model: str
    messages: List[ClaudeMessage]
    max_tokens: int = 4096
    temperature: float = 0.7
    system: Optional[str] = None


class ClaudeResponse(BaseModel):
    """مدل داده پاسخ از Claude API"""
    id: str
    type: str = "message"
    role: str = "assistant"
    content: List[Dict[str, Any]]
    model: str
    stop_reason: Optional[str] = None
    stop_sequence: Optional[str] = None
    usage: Dict[str, int]


class ClaudeClient:
    """
    کلاینت برای ارتباط با Anthropic Claude API

    این کلاس امکان ارتباط با API های Anthropic Claude را فراهم می‌کند و
    متدهای لازم برای ارسال درخواست‌های تحلیل متن و دریافت پاسخ‌ها را ارائه می‌دهد.

    Attributes:
        api_key (str): کلید API برای Anthropic Claude
        model (str): مدل پیش‌فرض Claude
        base_url (str): آدرس پایه API
        headers (Dict): هدرهای HTTP پیش‌فرض
        client (httpx.AsyncClient): کلاینت HTTP برای ارتباطات ناهمگام
    """

    def __init__(
            self,
            api_key: str = None,
            model: str = None,
            base_url: str = "https://api.anthropic.com/v1",
            timeout: float = 60.0
    ):
        """
        مقداردهی اولیه کلاینت Claude API

        Args:
            api_key (str, optional): کلید API برای Anthropic. اگر مشخص نشود، از تنظیمات استفاده می‌شود.
            model (str, optional): مدل پیش‌فرض Claude. اگر مشخص نشود، از تنظیمات استفاده می‌شود.
            base_url (str): آدرس پایه API.
            timeout (float): زمان انتظار برای پاسخ به ثانیه.
        """
        self.api_key = api_key or settings.CLAUDE_API_KEY
        self.model = model or settings.CLAUDE_MODEL
        self.base_url = base_url
        self.headers = {
            "x-api-key": self.api_key,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json"
        }
        self.client = httpx.AsyncClient(headers=self.headers, timeout=timeout)
        logger.info(f"ClaudeClient initialized with model: {self.model}")

    async def close(self):
        """بستن کلاینت HTTP"""
        await self.client.aclose()
        logger.debug("ClaudeClient connection closed")

    async def send_message(
            self,
            messages: List[Dict[str, Any]],
            system: Optional[str] = None,
            model: Optional[str] = None,
            max_tokens: int = 4096,
            temperature: float = 0.7
    ) -> ClaudeResponse:
        """
        ارسال پیام به Claude API

        Args:
            messages (List[Dict[str, Any]]): لیست پیام‌ها
            system (Optional[str]): دستورالعمل‌های سیستم
            model (Optional[str]): مدل Claude
            max_tokens (int): حداکثر تعداد توکن‌های پاسخ
            temperature (float): دمای تولید متن

        Returns:
            ClaudeResponse: پاسخ Claude API

        Raises:
            httpx.HTTPStatusError: در صورت خطای HTTP
            Exception: در صورت سایر خطاها
        """
        url = f"{self.base_url}/messages"

        request_data = ClaudeRequest(
            model=model or self.model,
            messages=[ClaudeMessage(**msg) for msg in messages],
            max_tokens=max_tokens,
            temperature=temperature,
            system=system
        )

        try:
            logger.debug(f"Sending request to Claude API: {request_data.model_dump_json()}")
            response = await self.client.post(
                url,
                json=request_data.model_dump(exclude_none=True),
                timeout=60.0
            )
            response.raise_for_status()
            data = response.json()

            # محاسبه هزینه برای ثبت در لاگ
            input_tokens = data.get("usage", {}).get("input_tokens", 0)
            output_tokens = data.get("usage", {}).get("output_tokens", 0)
            # قیمت‌های تقریبی برای Claude-3-7-Sonnet
            input_cost = input_tokens * 0.000003  # $3 / MTok
            output_cost = output_tokens * 0.000015  # $15 / MTok
            total_cost = input_cost + output_cost

            logger.info(
                f"Claude API response: model={data.get('model')}, "
                f"tokens={input_tokens}in/{output_tokens}out, "
                f"cost=${total_cost:.6f}"
            )

            return ClaudeResponse(**data)

        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP Error from Claude API: {e.response.status_code} - {e.response.text}")
            raise
        except Exception as e:
            logger.error(f"Error sending message to Claude API: {e}")
            raise

    async def analyze_sentiment(
            self,
            text: str,
            language: str = "auto",
            detailed: bool = False
    ) -> Dict[str, Any]:
        """
        تحلیل احساسات متن

        Args:
            text (str): متن برای تحلیل
            language (str): زبان متن ('fa', 'en', یا 'auto')
            detailed (bool): آیا تحلیل جزئیات بیشتری ارائه دهد؟

        Returns:
            Dict[str, Any]: نتایج تحلیل احساسات
        """
        system_prompt = """
        تو یک سیستم تحلیل احساسات متخصص هستی. وظیفه تو تحلیل احساسات متون فارسی و انگلیسی
        و تشخیص دقیق احساس غالب در متن است. پاسخ را فقط به صورت JSON بازگردان.
        """

        # تنظیم پیام بر اساس زبان
        language_hint = ""
        if language == "fa":
            language_hint = "این متن به زبان فارسی است."
        elif language == "en":
            language_hint = "این متن به زبان انگلیسی است."

        detail_level = "معمولی" if not detailed else "جزئیات بیشتر"

        user_message = f"""
        لطفاً احساس غالب در متن زیر را تحلیل کن. {language_hint}
        سطح جزئیات: {detail_level}

        متن: {text}

        لطفاً پاسخ را فقط به صورت JSON با ساختار زیر بازگردان:
        {{
            "sentiment": "positive/negative/neutral/mixed",
            "score": (عددی بین -1 تا 1),
            "confidence": (عددی بین 0 تا 1),
            "explanation": "توضیح مختصر دلیل این احساس"
        }}

        {
        'اگر سطح جزئیات بیشتر درخواست شده است، این فیلدها را هم اضافه کن:' if detailed else ''
        }
        {
        '"emotions": ["emotion1", "emotion2", ...], "intensity": (عددی بین 0 تا 1), "entities": [{"entity": "name", "sentiment": "positive/negative/neutral"}]' if detailed else ''
        }
        """

        messages = [
            {"role": "user", "content": user_message}
        ]

        response = await self.send_message(
            messages=messages,
            system=system_prompt,
            temperature=0.3  # دمای پایین برای نتایج قطعی‌تر
        )

        # استخراج پاسخ JSON
        try:
            # یافتن اولین بلاک متنی در پاسخ
            text_content = next((item["text"] for item in response.content if item["type"] == "text"), None)
            if not text_content:
                raise ValueError("پاسخ معتبری از Claude دریافت نشد")

            # تلاش برای پارس JSON از پاسخ
            # حذف تمام کاراکترهای قبل و بعد از JSON
            json_str = text_content.strip()
            # پیدا کردن شروع و پایان اولین JSON معتبر
            start_idx = json_str.find("{")
            end_idx = json_str.rfind("}") + 1
            if start_idx != -1 and end_idx != 0:
                json_str = json_str[start_idx:end_idx]

            result = json.loads(json_str)
            return result

        except (json.JSONDecodeError, ValueError) as e:
            logger.error(f"Error parsing sentiment analysis response: {e}")
            # برگرداندن یک نتیجه پیش‌فرض در صورت خطا
            return {
                "sentiment": "unknown",
                "score": 0,
                "confidence": 0,
                "explanation": "خطا در پردازش پاسخ"
            }

    async def extract_topics(
            self,
            text: str,
            language: str = "auto",
            max_topics: int = 5
    ) -> Dict[str, Any]:
        """
        استخراج موضوعات اصلی از متن

        Args:
            text (str): متن برای تحلیل
            language (str): زبان متن ('fa', 'en', یا 'auto')
            max_topics (int): حداکثر تعداد موضوعات

        Returns:
            Dict[str, Any]: موضوعات استخراج شده
        """
        system_prompt = """
        تو یک سیستم استخراج موضوع متخصص هستی. وظیفه تو تحلیل متون فارسی و انگلیسی
        و استخراج موضوعات اصلی و کلیدواژه‌های مهم است. پاسخ را فقط به صورت JSON بازگردان.
        """

        # تنظیم پیام بر اساس زبان
        language_hint = ""
        if language == "fa":
            language_hint = "این متن به زبان فارسی است."
        elif language == "en":
            language_hint = "این متن به زبان انگلیسی است."

        user_message = f"""
        لطفاً موضوعات اصلی در متن زیر را استخراج کن. {language_hint}
        حداکثر تعداد موضوعات: {max_topics}

        متن: {text}

        لطفاً پاسخ را فقط به صورت JSON با ساختار زیر بازگردان:
        {{
            "topics": [
                {{
                    "title": "عنوان موضوع",
                    "relevance": (عددی بین 0 تا 1),
                    "keywords": ["کلیدواژه1", "کلیدواژه2", ...]
                }},
                ...
            ],
            "main_topic": "موضوع اصلی کلی",
            "keywords": ["کلیدواژه1", "کلیدواژه2", ...]
        }}
        """

        messages = [
            {"role": "user", "content": user_message}
        ]

        response = await self.send_message(
            messages=messages,
            system=system_prompt,
            temperature=0.3
        )

        # استخراج پاسخ JSON
        try:
            # یافتن اولین بلاک متنی در پاسخ
            text_content = next((item["text"] for item in response.content if item["type"] == "text"), None)
            if not text_content:
                raise ValueError("پاسخ معتبری از Claude دریافت نشد")

            # تلاش برای پارس JSON از پاسخ
            json_str = text_content.strip()
            start_idx = json_str.find("{")
            end_idx = json_str.rfind("}") + 1
            if start_idx != -1 and end_idx != 0:
                json_str = json_str[start_idx:end_idx]

            result = json.loads(json_str)
            return result

        except (json.JSONDecodeError, ValueError) as e:
            logger.error(f"Error parsing topic extraction response: {e}")
            return {
                "topics": [],
                "main_topic": "unknown",
                "keywords": []
            }

    async def analyze_batch(
            self,
            texts: List[str],
            analysis_type: str = "sentiment",
            language: str = "auto"
    ) -> List[Dict[str, Any]]:
        """
        تحلیل دسته‌ای متون

        Args:
            texts (List[str]): لیست متون برای تحلیل
            analysis_type (str): نوع تحلیل ('sentiment', 'topics', 'full')
            language (str): زبان متون ('fa', 'en', یا 'auto')

        Returns:
            List[Dict[str, Any]]: نتایج تحلیل
        """
        system_prompt = """
        تو یک سیستم تحلیل متن هوشمند هستی. وظیفه تو تحلیل دسته‌ای متون فارسی و انگلیسی است.
        پاسخ را فقط به صورت JSON بازگردان و دقت کن که برای هر متن، یک آیتم در آرایه نتایج وجود داشته باشد.
        """

        # تنظیم پیام بر اساس نوع تحلیل و زبان
        language_hint = ""
        if language == "fa":
            language_hint = "این متون به زبان فارسی هستند."
        elif language == "en":
            language_hint = "این متون به زبان انگلیسی هستند."

        analysis_request = ""
        if analysis_type == "sentiment":
            analysis_request = "تحلیل احساسات (sentiment)"
        elif analysis_type == "topics":
            analysis_request = "استخراج موضوعات (topics)"
        elif analysis_type == "full":
            analysis_request = "تحلیل کامل (sentiment + topics)"

        # ساخت متن دسته‌ای
        batch_text = ""
        for i, text in enumerate(texts):
            batch_text += f"متن {i + 1}: {text}\n\n"

        user_message = f"""
        لطفاً تحلیل {analysis_request} را برای متون زیر انجام بده. {language_hint}

        {batch_text}

        لطفاً پاسخ را فقط به صورت JSON با ساختار زیر بازگردان:
        {{
            "results": [
                {{
                    "index": 0,
        """

        # تکمیل ساختار JSON براساس نوع تحلیل
        if analysis_type == "sentiment" or analysis_type == "full":
            user_message += """
                    "sentiment": {
                        "sentiment": "positive/negative/neutral/mixed",
                        "score": (عددی بین -1 تا 1),
                        "confidence": (عددی بین 0 تا 1)
                    },
            """

        if analysis_type == "topics" or analysis_type == "full":
            user_message += """
                    "topics": {
                        "main_topic": "موضوع اصلی",
                        "keywords": ["کلیدواژه1", "کلیدواژه2", ...]
                    },
            """

        user_message += """
                },
                ...
            ]
        }
        """

        messages = [
            {"role": "user", "content": user_message}
        ]

        # برای دسته‌های بزرگ، مدل قوی‌تر و توکن‌های بیشتری نیاز است
        model = self.model if len(texts) <= 10 else "claude-3-7-sonnet-20250219"
        max_tokens = 4096 if len(texts) <= 10 else 8192

        response = await self.send_message(
            messages=messages,
            system=system_prompt,
            model=model,
            max_tokens=max_tokens,
            temperature=0.3
        )

        # استخراج پاسخ JSON
        try:
            # یافتن اولین بلاک متنی در پاسخ
            text_content = next((item["text"] for item in response.content if item["type"] == "text"), None)
            if not text_content:
                raise ValueError("پاسخ معتبری از Claude دریافت نشد")

            # تلاش برای پارس JSON از پاسخ
            json_str = text_content.strip()
            start_idx = json_str.find("{")
            end_idx = json_str.rfind("}") + 1
            if start_idx != -1 and end_idx != 0:
                json_str = json_str[start_idx:end_idx]

            result = json.loads(json_str)
            return result.get("results", [])

        except (json.JSONDecodeError, ValueError) as e:
            logger.error(f"Error parsing batch analysis response: {e}")
            return [{"index": i, "error": "خطا در پردازش پاسخ"} for i in range(len(texts))]

    async def analyze_wave(
            self,
            tweets: List[Dict[str, Any]],
            keywords: List[str] = None,
            use_extended_thinking: bool = True
    ) -> Dict[str, Any]:
        """
        تحلیل عمیق یک موج توییتری

        Args:
            tweets (List[Dict[str, Any]]): لیست توییت‌ها
            keywords (List[str]): کلیدواژه‌های مرتبط با موج
            use_extended_thinking (bool): استفاده از Extended Thinking برای تحلیل عمیق‌تر

        Returns:
            Dict[str, Any]: نتایج تحلیل موج
        """
        system_prompt = """
        تو یک سیستم تحلیل موج شبکه‌های اجتماعی هستی. وظیفه تو تحلیل عمیق موج‌های توییتری در فضای مجازی است.
        سعی کن الگوهای توییت‌ها، منشا احتمالی موج، میزان تأثیرگذاری و روند پیش‌بینی شده را به دقت تحلیل کنی.
        پاسخ را به صورت JSON با ساختار مشخص شده بازگردان.
        """

        # خلاصه‌سازی توییت‌ها برای استفاده در پرامپت
        tweet_summaries = []
        for i, tweet in enumerate(tweets[:20]):  # حداکثر 20 توییت برای جلوگیری از طولانی شدن پرامپت
            tweet_text = tweet.get("content", "")
            username = tweet.get("user", {}).get("username", "کاربر ناشناس")
            engagement = tweet.get("retweet_count", 0) + tweet.get("like_count", 0)
            tweet_summary = f"توییت {i + 1}: @{username} - لایک/ریتوییت: {engagement} - {tweet_text[:100]}..."
            tweet_summaries.append(tweet_summary)

        tweets_count = len(tweets)
        keywords_text = ", ".join(keywords) if keywords else "نامشخص"

        user_message = f"""
        لطفاً موج توییتری زیر را تحلیل کن:

        تعداد کل توییت‌ها: {tweets_count}
        کلیدواژه‌های مرتبط: {keywords_text}

        نمونه توییت‌ها:
        {"\n".join(tweet_summaries)}

        موارد زیر را تحلیل کن:
        1. موضوع اصلی این موج چیست؟
        2. آیا این موج طبیعی به نظر می‌رسد یا احتمالاً هماهنگ شده است؟
        3. میزان اهمیت و تأثیرگذاری این موج چقدر است؟
        4. چه کاربرانی بیشترین تأثیر را در این موج داشته‌اند؟
        5. آیا این موج واکنشی به یک رویداد خاص است؟
        6. پیش‌بینی روند آینده این موج چیست؟

        لطفاً پاسخ را فقط به صورت JSON با ساختار زیر بازگردان:
        {{
            "main_topic": "موضوع اصلی موج",
            "summary": "خلاصه‌ای از ماهیت موج",
            "is_coordinated": true/false,
            "coordination_confidence": (عددی بین 0 تا 1),
            "importance_score": (عددی بین 0 تا 10),
            "key_influencers": ["کاربر1", "کاربر2", ...],
            "reactionary": true/false,
            "trigger_event": "رویداد محرک (اگر وجود دارد)",
            "prediction": "پیش‌بینی روند آینده",
            "recommendations": ["توصیه1", "توصیه2", ...],
            "sentiment_distribution": {{"positive": 0.x, "negative": 0.y, "neutral": 0.z}},
            "analysis_confidence": (عددی بین 0 تا 1)
        }}
        """

        messages = [
            {"role": "user", "content": user_message}
        ]

        # استفاده از مدل قوی‌تر و Extended Thinking
        model = "claude-3-7-sonnet-20250219"  # استفاده از بهترین مدل برای تحلیل موج

        # تنظیم درخواست با Extended Thinking در صورت نیاز
        request_params = {
            "messages": messages,
            "system": system_prompt,
            "model": model,
            "max_tokens": 4096,
            "temperature": 0.2  # دمای پایین برای نتایج قطعی‌تر
        }

        # اضافه کردن هدر Extended Thinking
        if use_extended_thinking:
            self.headers["anthropic-beta"] = "thinking-2025-04-15"
            request_params["thinking"] = {
                "type": "enabled",
                "budget_tokens": 6000
            }

        response = await self.send_message(**request_params)

        # حذف هدر Extended Thinking برای درخواست‌های بعدی
        if use_extended_thinking and "anthropic-beta" in self.headers:
            del self.headers["anthropic-beta"]

        # استخراج پاسخ JSON
        try:
            # یافتن اولین بلاک متنی در پاسخ
            text_content = next((item["text"] for item in response.content if item["type"] == "text"), None)
            if not text_content:
                raise ValueError("پاسخ معتبری از Claude دریافت نشد")

            # تلاش برای پارس JSON از پاسخ
            json_str = text_content.strip()
            start_idx = json_str.find("{")
            end_idx = json_str.rfind("}") + 1
            if start_idx != -1 and end_idx != 0:
                json_str = json_str[start_idx:end_idx]

            result = json.loads(json_str)

            # استخراج محتوای Extended Thinking اگر موجود بود
            thinking_content = next((item["thinking"] for item in response.content if item.get("type") == "thinking"),
                                    None)
            if thinking_content:
                result["extended_thinking"] = thinking_content

            return result

        except (json.JSONDecodeError, ValueError) as e:
            logger.error(f"Error parsing wave analysis response: {e}")
            return {
                "main_topic": "خطا در تحلیل موج",
                "summary": "خطا در پردازش پاسخ",
                "error": str(e),
                "analysis_confidence": 0
            }