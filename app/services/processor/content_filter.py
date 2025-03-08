"""
فیلتر محتوای توییت‌ها.

این ماژول کلاس‌های لازم برای فیلتر کردن توییت‌ها بر اساس محتوا،
تشخیص اسپم، و مرتبط بودن توییت‌ها با کلیدواژه‌ها را فراهم می‌کند.
"""

import re
import json
import math
import logging
from typing import Dict, List, Tuple, Union, Optional, Any, Set

logger = logging.getLogger(__name__)


class ContentFilter:
    """
    فیلتر کردن و پیش‌پردازش محتوای توییت‌ها

    این کلاس متدهای لازم برای تشخیص اسپم، محتوای نامناسب و
    بررسی مرتبط بودن توییت‌ها با کلیدواژه‌ها را فراهم می‌کند.

    Attributes:
        spam_patterns (List[str]): الگوهای تشخیص اسپم
        inappropriate_patterns (List[str]): الگوهای تشخیص محتوای نامناسب
        stopwords (List[str]): کلمات ایست برای پردازش متن
        persian_stopwords (List[str]): کلمات ایست فارسی
        spam_regex (List[re.Pattern]): الگوهای regex کامپایل شده برای اسپم
        inappropriate_regex (List[re.Pattern]): الگوهای regex کامپایل شده برای محتوای نامناسب
    """

    def __init__(self):
        """
        مقداردهی اولیه فیلتر محتوا
        """
        # الگوهای اسپم
        self.spam_patterns = [
            r'(?i)buy now',
            r'(?i)discount.*\d+%',
            r'(?i)click here.*http',
            r'(?i)limited time offer',
            r'(?i)make money fast',
            r'(?i)work from home',
            r'(?i)earn from home',
            r'(?i)\S+\.[a-z]{2,4}/\S+',  # لینک‌های مشکوک
            r'(?i)free.*download',
            r'(?i)download.*free',
            r'(?i)\$\d+/hour',
            r'(?i)\$\d+/day',
            r'(?i)casino.*online',
            r'(?i)online.*casino',
            r'(?i)bet.*online',
            r'(?i)online.*bet',
            r'(?i)loan.*apply',
            r'(?i)apply.*loan',
            r'(?i)investment.*opportunity',
            r'(?i)opportunity.*investment',
            # الگوهای فارسی
            r'(?i)کسب درآمد از خانه',
            r'(?i)کسب و کار اینترنتی',
            r'(?i)درآمد روزانه',
            r'(?i)شغل دوم',
            r'(?i)کلیک کنید و پولدار شوید',
            r'(?i)درآمد میلیونی',
            r'(?i)کسب درآمد دلاری',
            r'(?i)ثبت نام کنید و.*دریافت کنید'
        ]

        # الگوهای محتوای نامناسب - این بخش در پروژه واقعی با الگوهای دقیق پر می‌شود
        self.inappropriate_patterns = [
            r'(?i)profanity1',
            r'(?i)profanity2',
            r'(?i)profanity3',
            # الگوهای فارسی
            r'(?i)کلمه_نامناسب1',
            r'(?i)کلمه_نامناسب2',
            r'(?i)کلمه_نامناسب3'
        ]

        # کلمات ایست (برای حذف از متن در پیش‌پردازش)
        self.stopwords = [
            'a', 'an', 'the', 'and', 'or', 'but', 'is', 'are', 'was', 'were',
            'in', 'on', 'at', 'to', 'for', 'with', 'by', 'about', 'against',
            'of', 'from', 'as', 'into', 'during', 'before', 'after', 'above',
            'below', 'since', 'until', 'while', 'because', 'though', 'so',
            'than', 'that', 'this', 'these', 'those', 'then', 'just', 'now',
            'here', 'there'
        ]

        # کلمات ایست فارسی
        self.persian_stopwords = [
            'و', 'در', 'به', 'از', 'که', 'این', 'را', 'با', 'است', 'برای',
            'آن', 'یک', 'خود', 'تا', 'شد', 'بر', 'هم', 'نیز', 'ها', 'های',
            'می', 'شود', 'کرد', 'او', 'ما', 'اما', 'یا', 'باید', 'دارد',
            'اند', 'شده', 'مورد', 'آنها', 'بود', 'داد', 'چه', 'همه', 'چند',
            'هر', 'نمی', 'شما', 'آنان', 'بین', 'پس', 'پیش', 'بی', 'می‌شود',
            'می‌کند', 'می‌دهد', 'می‌گوید'
        ]

        # تبدیل الگوها به regex کامپایل شده برای عملکرد بهتر
        self.spam_regex = [re.compile(pattern) for pattern in self.spam_patterns]
        self.inappropriate_regex = [re.compile(pattern) for pattern in self.inappropriate_patterns]

        logger.info("ContentFilter initialized")

    def is_spam(self, text: str) -> bool:
        """
        بررسی اسپم بودن متن

        Args:
            text (str): متن توییت

        Returns:
            bool: True اگر اسپم باشد، False در غیر این صورت
        """
        if not text:
            return False

        # بررسی الگوهای اسپم
        for pattern in self.spam_regex:
            if pattern.search(text):
                logger.debug(f"Spam detected: '{text[:50]}...' matches pattern {pattern.pattern}")
                return True

        # بررسی تعداد تکرار حروف (مثلاً "aaaaaaa")
        if re.search(r'(.)\1{5,}', text):
            logger.debug(f"Spam detected: '{text[:50]}...' contains repeated characters")
            return True

        # بررسی تعداد لینک‌ها
        urls = re.findall(r'https?://\S+', text)
        if len(urls) > 2:
            logger.debug(f"Spam detected: '{text[:50]}...' contains {len(urls)} URLs")
            return True

        # بررسی نسبت حروف بزرگ (در متون انگلیسی)
        if re.search(r'[A-Z]', text):
            uppercase_ratio = sum(1 for c in text if c.isupper()) / len(text)
            if uppercase_ratio > 0.5 and len(text) > 10:
                logger.debug(f"Spam detected: '{text[:50]}...' has high uppercase ratio ({uppercase_ratio:.2f})")
                return True

        return False

    def is_inappropriate(self, text: str) -> bool:
        """
        بررسی نامناسب بودن متن

        Args:
            text (str): متن توییت

        Returns:
            bool: True اگر نامناسب باشد، False در غیر این صورت
        """
        if not text:
            return False

        for pattern in self.inappropriate_regex:
            if pattern.search(text):
                logger.debug(f"Inappropriate content detected: '{text[:50]}...' matches pattern {pattern.pattern}")
                return True

        return False

    def is_relevant(self, text: str, keywords: List[str]) -> bool:
        """
        بررسی مرتبط بودن متن با کلیدواژه‌ها

        Args:
            text (str): متن توییت
            keywords (List[str]): لیست کلیدواژه‌ها

        Returns:
            bool: True اگر مرتبط باشد، False در غیر این صورت
        """
        if not text or not keywords:
            return False

        text_lower = text.lower()

        for keyword in keywords:
            if keyword.lower() in text_lower:
                return True

        # بررسی موارد مشابه با فاصله (مثلاً کلیدواژه "آب و هوا" با "آب‌وهوا")
        cleaned_text = self.clean_text(text)

        for keyword in keywords:
            cleaned_keyword = self.clean_text(keyword)
            if cleaned_keyword in cleaned_text:
                return True

        return False

    def clean_text(self, text: str) -> str:
        """
        پاکسازی و نرمال‌سازی متن

        Args:
            text (str): متن اصلی

        Returns:
            str: متن پاکسازی شده
        """
        if not text:
            return ""

        # حذف لینک‌ها
        text = re.sub(r'https?://\S+', '', text)

        # حذف منشن‌ها (@username)
        text = re.sub(r'@\w+', '', text)

        # حذف هشتگ‌ها (#hashtag)
        text = re.sub(r'#\w+', '', text)

        # حذف کاراکترهای خاص
        text = re.sub(r'[^\w\s\u0600-\u06FF]', '', text)  # شامل کاراکترهای فارسی

        # حذف فاصله‌های اضافی
        text = re.sub(r'\s+', ' ', text)

        # تبدیل به حروف کوچک
        text = text.lower()

        # حذف فاصله‌های ابتدا و انتها
        return text.strip()

    def normalize_persian_text(self, text: str) -> str:
        """
        نرمال‌سازی متن فارسی

        Args:
            text (str): متن فارسی

        Returns:
            str: متن نرمال‌سازی شده
        """
        if not text:
            return ""

        # استانداردسازی کاراکترهای فارسی
        replacements = {
            'ي': 'ی',
            'ك': 'ک',
            '١': '1',
            '٢': '2',
            '٣': '3',
            '٤': '4',
            '٥': '5',
            '٦': '6',
            '٧': '7',
            '٨': '8',
            '٩': '9',
            '٠': '0',
            '‌': ' ',  # تبدیل نیم‌فاصله به فاصله
        }

        for old, new in replacements.items():
            text = text.replace(old, new)

        # حذف اعراب
        text = re.sub(r'[\u064B-\u065F\u0670]', '', text)

        return text

    def extract_keywords(self, text: str, max_keywords: int = 5) -> List[str]:
        """
        استخراج کلیدواژه‌های متن

        Args:
            text (str): متن توییت
            max_keywords (int): حداکثر تعداد کلیدواژه‌ها

        Returns:
            List[str]: لیست کلیدواژه‌های استخراج شده
        """
        if not text:
            return []

        # تمیزسازی متن
        clean = self.clean_text(text)

        # تقسیم به کلمات
        words = clean.split()

        # زبان متن
        is_persian = bool(re.search(r'[\u0600-\u06FF]', text))

        # انتخاب کلمات ایست مناسب
        stopwords = self.persian_stopwords if is_persian else self.stopwords

        # حذف کلمات ایست
        words = [word for word in words if word not in stopwords and len(word) > 2]

        # شمارش فراوانی کلمات
        word_freq = {}
        for word in words:
            word_freq[word] = word_freq.get(word, 0) + 1

        # مرتب‌سازی براساس فراوانی
        sorted_words = sorted(word_freq.items(), key=lambda x: x[1], reverse=True)

        # انتخاب کلیدواژه‌های پرتکرار
        top_keywords = [word for word, freq in sorted_words[:max_keywords]]

        return top_keywords

    def calculate_importance_score(self, tweet: Dict[str, Any]) -> float:
        """
        محاسبه امتیاز اهمیت توییت

        Args:
            tweet (Dict[str, Any]): دیکشنری اطلاعات توییت

        Returns:
            float: امتیاز اهمیت (0.0 تا 1.0)
        """
        if not tweet:
            return 0.0

        # امتیاز پایه
        score = 0.5

        # امتیاز براساس تعداد تعاملات
        engagement = (
                tweet.get('retweet_count', 0) * 2 +
                tweet.get('like_count', 0) +
                tweet.get('reply_count', 0) * 1.5 +
                tweet.get('quote_count', 0) * 1.2
        )

        # امتیاز براساس تعاملات (حداکثر 0.3)
        engagement_score = 0
        if engagement > 0:
            # لگاریتم طبیعی برای مقیاس‌بندی تعاملات
            engagement_score = min(0.3, 0.3 * (math.log(engagement + 1) / 10))

        score += engagement_score

        # امتیاز براساس تأیید شده بودن کاربر
        user = tweet.get('user', {})
        if user.get('verified', False):
            score += 0.1

        # امتیاز براساس تعداد فالوئرها
        followers = user.get('followers_count', 0)
        if followers > 0:
            # لگاریتم طبیعی برای مقیاس‌بندی تعداد فالوئرها
            follower_score = min(0.1, 0.1 * (math.log(followers + 1) / 10))
            score += follower_score

        # محدود کردن امتیاز به بازه 0.0 تا 1.0
        return min(1.0, max(0.0, score))

    def detect_language(self, text: str) -> str:
        """
        تشخیص زبان متن

        Args:
            text (str): متن توییت

        Returns:
            str: کد زبان (fa, en, etc.)
        """
        if not text:
            return "unknown"

        # بررسی کاراکترهای فارسی/عربی
        persian_chars = len(re.findall(r'[\u0600-\u06FF]', text))

        # بررسی کاراکترهای لاتین
        latin_chars = len(re.findall(r'[a-zA-Z]', text))

        if persian_chars > latin_chars:
            # تشخیص فارسی از عربی
            persian_specific = len(re.findall(r'[پچژگک]', text))
            arabic_specific = len(re.findall(r'[ثذضظةء]', text))

            if persian_specific > arabic_specific:
                return "fa"
            elif arabic_specific > persian_specific:
                return "ar"
            else:
                # در صورت عدم قطعیت، فارسی فرض می‌کنیم
                return "fa"
        elif latin_chars > 0:
            return "en"

        return "unknown"

    def calculate_sentiment_basic(self, text: str) -> Tuple[str, float]:
        """
        تحلیل ساده احساسات متن

        Args:
            text (str): متن توییت

        Returns:
            Tuple[str, float]: برچسب احساسات و امتیاز آن
        """
        if not text:
            return "neutral", 0.0

        # تشخیص زبان
        language = self.detect_language(text)

        # کلمات مثبت و منفی براساس زبان
        positive_words = {
            "en": ["good", "great", "excellent", "amazing", "awesome", "love", "like", "happy", "best", "wonderful"],
            "fa": ["خوب", "عالی", "عالیه", "محشر", "دوست", "عشق", "لذت", "خوشحال", "بهترین", "زیبا"]
        }

        negative_words = {
            "en": ["bad", "terrible", "awful", "hate", "dislike", "sad", "angry", "poor", "worst", "horrible"],
            "fa": ["بد", "افتضاح", "متنفر", "ناراحت", "عصبانی", "خشمگین", "ضعیف", "مزخرف", "بدترین", "زشت"]
        }

        # انتخاب دیکشنری کلمات براساس زبان
        pos_dict = positive_words.get(language, positive_words["en"])
        neg_dict = negative_words.get(language, negative_words["en"])

        # شمارش کلمات مثبت و منفی
        text_lower = text.lower()
        positive_count = sum(1 for word in pos_dict if word in text_lower)
        negative_count = sum(1 for word in neg_dict if word in text_lower)

        # محاسبه امتیاز
        total_count = positive_count + negative_count
        if total_count == 0:
            return "neutral", 0.0

        score = (positive_count - negative_count) / total_count

        # تعیین برچسب
        if score > 0.25:
            sentiment = "positive"
        elif score < -0.25:
            sentiment = "negative"
        else:
            sentiment = "neutral"

        return sentiment, score

    def extract_entities(self, text: str, entities_data: Optional[Dict[str, Any]] = None) -> Dict[str, List[str]]:
        """
        استخراج موجودیت‌های متن (هشتگ‌ها، منشن‌ها، URL‌ها)

        Args:
            text (str): متن توییت
            entities_data (Optional[Dict[str, Any]]): اطلاعات entities از Twitter API

        Returns:
            Dict[str, List[str]]: دیکشنری موجودیت‌های استخراج شده
        """
        entities = {
            "hashtags": [],
            "mentions": [],
            "urls": []
        }

        # اگر داده‌های entities از Twitter API موجود باشد، از آنها استفاده می‌کنیم
        if entities_data:
            # استخراج هشتگ‌ها
            if "hashtags" in entities_data:
                for hashtag in entities_data["hashtags"]:
                    if "text" in hashtag:
                        entities["hashtags"].append(hashtag["text"])

            # استخراج منشن‌ها
            if "user_mentions" in entities_data:
                for mention in entities_data["user_mentions"]:
                    if "screen_name" in mention:
                        entities["mentions"].append(mention["screen_name"])

            # استخراج URL‌ها
            if "urls" in entities_data:
                for url in entities_data["urls"]:
                    if "expanded_url" in url:
                        entities["urls"].append(url["expanded_url"])

        # اگر داده‌های entities موجود نبود، از regex استفاده می‌کنیم
        else:
            # استخراج هشتگ‌ها
            hashtags = re.findall(r'#(\w+)', text)
            entities["hashtags"] = hashtags

            # استخراج منشن‌ها
            mentions = re.findall(r'@(\w+)', text)
            entities["mentions"] = mentions

            # استخراج URL‌ها
            urls = re.findall(r'https?://\S+', text)
            entities["urls"] = urls

        return entities
