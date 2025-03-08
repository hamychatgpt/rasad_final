# پروژه رصد: پلتفرم هوشمند پایش توییتر

پروژه رصد یک سیستم پیشرفته برای پایش، تحلیل و گزارش‌دهی فعالیت‌های توییتر است که با استفاده از هوش مصنوعی، توییت‌های مرتبط با کلیدواژه‌های خاص را جمع‌آوری، پردازش و تحلیل می‌کند. این سیستم به سازمان‌ها کمک می‌کند تا موج‌های انتقادی و فعالیت‌های مشکوک را سریعاً شناسایی کرده و بر اساس داده‌های دقیق، استراتژی‌های ارتباطی مناسب را اتخاذ کنند.

## معماری سیستم

سیستم از پنج ماژول اصلی تشکیل شده است:

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│  جمع‌آوری        │     │  پردازش         │     │  تحلیل          │
│  TwitterAPI.io  │────▶│  فیلترسازی      │────▶│  Claude API     │
│  وب‌هوک/وبسوکت   │     │  اولویت‌بندی     │     │  سیستم چندلایه‌ای │
└─────────────────┘     └─────────────────┘     └─────────────────┘
        ▲                        ▲                      │
        │                        │                      │
        └────────────────────────┼──────────────────────┘
                                 │                
                                 ▼
┌─────────────────┐     ┌─────────────────┐
│  فرانت‌اند       │◀────│  بک‌اند          │
│  داشبورد        │     │  REST API       │
│  مدیریت تنظیمات │     │  مدیریت کاربران │
└─────────────────┘     └─────────────────┘
```

### وضعیت فعلی پروژه

- **زیرساخت پایه**: 100% تکمیل شده
- **ماژول جمع‌آوری**: 100% تکمیل شده
- **ماژول پردازش**: 100% تکمیل شده
- **ماژول تحلیل**: 100% تکمیل شده
- **ماژول بک‌اند**: 30% تکمیل شده
- **ماژول فرانت‌اند**: 0% تکمیل شده

## مستندات جامع برای توسعه‌دهندگان

### 1. ساختار پروژه

```
/app                  # کد اصلی پروژه
  /api                # اندپوینت‌های API
    /v1               # نسخه 1 API
      /__init__.py    # فایل init برای پکیج
      /analysis.py    # اندپوینت‌های تحلیل
      /auth.py        # اندپوینت‌های احراز هویت
      /router.py      # روتر اصلی
      /settings.py    # اندپوینت‌های تنظیمات
      /services.py    # اندپوینت‌های مدیریت سرویس‌ها
      /tweets.py      # اندپوینت‌های توییت‌ها
      /waves.py       # اندپوینت‌های موج‌ها
  /core               # تابع‌های هسته‌ای
    /__init__.py      # فایل init برای پکیج
    /security.py      # ماژول‌های امنیتی
  /db                 # مدل‌ها و ارتباط با دیتابیس
    /models.py        # مدل‌های ORM
    /session.py       # مدیریت نشست دیتابیس
  /middlewares        # میدلورهای FastAPI
    /__init__.py      # فایل init برای پکیج
    /error_handler.py # میدلور مدیریت خطا
    /logging_middleware.py # میدلور ثبت وقایع
  /schemas            # مدل‌های Pydantic
    /__init__.py      # فایل init برای پکیج
    /analysis.py      # مدل‌های تحلیل
    /auth.py          # مدل‌های احراز هویت
    /settings.py      # مدل‌های تنظیمات
    /tweet.py         # مدل‌های توییت
    /wave.py          # مدل‌های موج
  /services           # سرویس‌های مختلف
    /analyzer         # سرویس‌های تحلیل
      /__init__.py    # فایل init برای پکیج
      /analyzer.py    # سرویس اصلی تحلیل
      /claude_client.py # کلاینت Claude API
      /cost_manager.py # مدیریت هزینه API
      /wave_detector.py # تشخیص موج‌ها
    /processor        # سرویس‌های پردازش
      /__init__.py    # فایل init برای پکیج
      /content_filter.py # فیلتر محتوا
      /tweet_processor.py # پردازش توییت‌ها
    /redis_service.py # سرویس Redis
    /twitter          # سرویس‌های ارتباط با توییتر
      /__init__.py    # فایل init برای پکیج
      /client.py      # کلاینت Twitter API
      /collector.py   # جمع‌آوری توییت‌ها
      /models.py      # مدل‌های Twitter API
  /config.py          # تنظیمات پروژه
  /main.py            # نقطه ورود اصلی برنامه

/docks                # مستندات
/frontend             # فایل‌های فرانت‌اند
  /app                # اپلیکیشن فرانت‌اند
    /app.js           # کد جاوااسکریپت اصلی
    /index.html       # صفحه اصلی HTML
  /styles.css         # استایل‌های CSS

/scripts              # اسکریپت‌های کمکی
  /create_admin.py    # ایجاد کاربر مدیر
  /run_all.py         # اجرای همه سرویس‌ها
  /run_analyzer.py    # اجرای سرویس تحلیل
  /run_collector.py   # اجرای سرویس جمع‌آوری
  /run_processor.py   # اجرای سرویس پردازش
  /test_connections.py # تست اتصال‌ها
```

### 2. استراتژی توسعه فعلی

بر اساس فایل استراتژی، هدف فعلی توسعه، ایجاد "نسخه آزمایشی سریع" با تمرکز بر ایجاد رابط کاربری ساده برای مدیریت کلیدواژه‌ها، مشاهده وضعیت سیستم و آغاز استخراج داده است. فاز فعلی توسعه به شرح زیر است:

1. **تکمیل اندپوینت‌های API ضروری**
2. **توسعه فرانت‌اند اولیه**
3. **گسترش قابلیت‌های استخراج و مشاهده داده**
4. **تکمیل قابلیت‌های مدیریتی**
5. **پیاده‌سازی تحلیل‌های اولیه و هشدارها**
6. **بهبود تجربه کاربری و گزارش‌دهی**

فرانت‌اند اولیه باید شامل صفحات زیر باشد:
- صفحه ورود به سیستم
- داشبورد اصلی با نمایش آمار کلی
- صفحه مدیریت کلیدواژه‌ها
- صفحه نمایش و جستجوی توییت‌ها
- صفحه مشاهده و مدیریت هشدارها
- صفحه تنظیمات سیستم

### 3. تکنولوژی‌های اصلی و وابستگی‌ها

- **Backend**: Python 3.9+ با FastAPI
- **Frontend**: HTML/CSS/JS (با Bootstrap) - در آینده React
- **Database**: PostgreSQL با SQLAlchemy
- **Caching/Messaging**: Redis
- **External APIs**: 
  - TwitterAPI.io برای جمع‌آوری داده‌های توییتر
  - Claude API برای تحلیل‌های هوشمند
- **Deployment**: Docker (پیش‌بینی شده)

**وابستگی‌های اصلی Python**:
```
fastapi==0.108.0
uvicorn[standard]==0.25.0
pydantic==2.5.3
pydantic-settings==2.1.0
sqlalchemy==2.0.23
asyncpg==0.29.0
redis==5.0.1
httpx==0.26.0
pyjwt==2.8.0
passlib==1.7.4
bcrypt==4.1.2
pandas==2.1.4
numpy==1.26.2
```

### 4. سرویس‌ها و ماژول‌های اصلی

#### 4.1 ماژول جمع‌آوری (Collector)

کلاس‌های اصلی:
- `TwitterAPIClient`: ارتباط با TwitterAPI.io
- `TweetCollector`: مدیریت جمع‌آوری و ذخیره‌سازی توییت‌ها

نمونه استفاده:
```python
from app.db.session import get_db
from app.services.redis_service import RedisService
from app.services.twitter.client import TwitterAPIClient
from app.services.twitter.collector import TweetCollector

# ایجاد اتصال‌ها
db_session = await anext(get_db())
redis_service = RedisService()
await redis_service.connect()
twitter_client = TwitterAPIClient()

# ایجاد جمع‌آوری کننده
collector = TweetCollector(
    twitter_client=twitter_client,
    db_session=db_session,
    redis_service=redis_service
)

# جمع‌آوری توییت‌ها براساس کلیدواژه‌ها
keywords = await collector.get_active_keywords()
tweets = await collector.collect_by_keywords(
    keywords=keywords[:3],  # سه کلیدواژه اول
    days_back=2,
    max_tweets=500,
    save_to_db=True
)
```

#### 4.2 ماژول پردازش (Processor)

کلاس‌های اصلی:
- `ContentFilter`: فیلترینگ محتوا و تشخیص اسپم
- `TweetProcessor`: پردازش و محاسبه امتیاز اهمیت توییت‌ها

نمونه استفاده:
```python
from app.db.session import get_db
from app.services.redis_service import RedisService
from app.services.processor.content_filter import ContentFilter
from app.services.processor.tweet_processor import TweetProcessor

# ایجاد اتصال‌ها
db_session = await anext(get_db())
redis_service = RedisService()
await redis_service.connect()
content_filter = ContentFilter()

# ایجاد پردازشگر
processor = TweetProcessor(
    db_session=db_session,
    redis_service=redis_service,
    content_filter=content_filter
)

# پردازش توییت‌های نپردازش شده
processed, filtered = await processor.process_unprocessed_tweets(limit=100)
```

#### 4.3 ماژول تحلیل (Analyzer)

کلاس‌های اصلی:
- `ClaudeClient`: ارتباط با Claude API
- `CostManager`: مدیریت هزینه و بهینه‌سازی استفاده از API
- `WaveDetector`: تشخیص موج‌های توییتری
- `TweetAnalyzer`: تحلیل عمیق توییت‌ها

نمونه استفاده:
```python
from app.db.session import get_db
from app.services.analyzer.claude_client import ClaudeClient
from app.services.analyzer.cost_manager import CostManager
from app.services.analyzer.wave_detector import WaveDetector
from app.services.analyzer.analyzer import TweetAnalyzer

# ایجاد اتصال‌ها
db_session = await anext(get_db())
claude_client = ClaudeClient()
cost_manager = CostManager(db_session)
await cost_manager.initialize()
wave_detector = WaveDetector(db_session)

# ایجاد تحلیلگر
analyzer = TweetAnalyzer(
    db_session=db_session,
    claude_client=claude_client,
    cost_manager=cost_manager,
    wave_detector=wave_detector,
    batch_size=50
)
await analyzer.initialize()

# تحلیل یک توییت
result = await analyzer.analyze_tweet(tweet_id=123)

# تشخیص موج‌ها و ایجاد هشدار
alerts = await analyzer.detect_waves_and_alert(hours_back=6)
```

#### 4.4 ماژول بک‌اند (Backend API)

اندپوینت‌های اصلی:
- `/api/v1/auth`: احراز هویت و مدیریت کاربران
- `/api/v1/tweets`: جستجو و مدیریت توییت‌ها و کلیدواژه‌ها
- `/api/v1/analysis`: تحلیل توییت‌ها و گزارش‌گیری
- `/api/v1/waves`: تشخیص موج‌ها و مدیریت هشدارها
- `/api/v1/settings`: مدیریت تنظیمات سیستم
- `/api/v1/services`: مدیریت سرویس‌ها

### 5. مدل‌های داده

#### 5.1 مدل‌های دیتابیس (SQLAlchemy)

- `Tweet`: نگهداری اطلاعات توییت‌ها
- `User`: اطلاعات کاربران توییتر
- `Keyword`: کلیدواژه‌های جستجو
- `TweetKeyword`: ارتباط بین توییت‌ها و کلیدواژه‌ها
- `Topic`: موضوعات استخراج شده
- `TweetTopic`: ارتباط بین توییت‌ها و موضوعات
- `Alert`: هشدارهای سیستم
- `ApiUsage`: ثبت استفاده از API
- `AppUser`: کاربران سیستم

#### 5.2 مدل‌های API (Pydantic)

Schemas در پوشه `/app/schemas` برای:
- مدل‌های تحلیل (`analysis.py`)
- مدل‌های احراز هویت (`auth.py`)
- مدل‌های تنظیمات (`settings.py`)
- مدل‌های توییت (`tweet.py`)
- مدل‌های موج (`wave.py`)

### 6. معرفی API‌های خارجی

#### 6.1 TwitterAPI.io

سیستم از TwitterAPI.io برای جمع‌آوری داده‌های توییتر استفاده می‌کند. این API امکان جستجوی توییت‌ها، دریافت اطلاعات کاربران و مانیتورینگ کلیدواژه‌ها را فراهم می‌کند.

اندپوینت‌های اصلی مورد استفاده:
- جستجوی پیشرفته توییت: `GET /twitter/tweet/advanced_search`
- دریافت اطلاعات کاربر: `GET /twitter/user/info`
- دریافت اطلاعات دسته‌ای کاربران: `GET /twitter/user/batch_info_by_ids`
- دریافت توییت‌های کاربر: `GET /twitter/user/last_tweets`

#### 6.2 Claude API (Anthropic)

سیستم از API کلود برای تحلیل عمیق متون و تشخیص احساسات استفاده می‌کند.

سرویس‌های اصلی استفاده شده:
- Message API برای تحلیل متن
- استفاده از Extended Thinking برای تحلیل‌های عمیق‌تر
- بهینه‌سازی هزینه با انتخاب هوشمند مدل‌ها

### 7. روش‌های اجرا و دستورات مهم

#### 7.1 راه‌اندازی محیط توسعه

```bash
# کلون کردن مخزن
git clone https://github.com/your-org/rasad.git
cd rasad

# ایجاد محیط مجازی
python -m venv venv
source venv/bin/activate  # در لینوکس/مک
# venv\Scripts\activate  # در ویندوز

# نصب وابستگی‌ها
pip install -r requirements.txt

# تنظیم فایل .env
cp .env.example .env
# سپس فایل .env را با اطلاعات خود ویرایش کنید

# ایجاد دیتابیس و کاربر مدیر
python scripts/create_admin.py
```

#### 7.2 اجرای سرویس‌ها

```bash
# اجرای سرور API
uvicorn app.main:app --reload

# اجرای جمع‌آوری کننده
python scripts/run_collector.py

# اجرای پردازشگر
python scripts/run_processor.py

# اجرای تحلیلگر
python scripts/run_analyzer.py

# یا اجرای همه سرویس‌ها با هم
python scripts/run_all.py
```

#### 7.3 تست اتصال‌ها

```bash
python scripts/test_connections.py
```

### 8. راهنمای توسعه فرانت‌اند

فرانت‌اند فعلی شامل فایل‌های ساده HTML/CSS/JS در پوشه `/frontend` است. در فاز بعدی توسعه، هدف تکمیل این بخش با استفاده از Bootstrap و JavaScript است. صفحات اصلی شامل موارد زیر هستند:

1. **صفحه ورود**:
   - ورود با نام کاربری و رمز عبور
   - اتصال به API `/api/v1/auth/login`

2. **داشبورد اصلی**:
   - نمایش آمار کلی توییت‌ها و هشدارها
   - نمودار توزیع احساسات
   - اتصال به API‌های:
     - `/api/v1/tweets/count`
     - `/api/v1/waves/alerts`
     - `/api/v1/analysis/topics`

3. **صفحه توییت‌ها**:
   - نمایش لیست توییت‌ها
   - فیلتر و جستجو
   - اتصال به API `/api/v1/tweets`

4. **صفحه هشدارها**:
   - نمایش لیست هشدارها
   - فیلتر هشدارها براساس نوع و اهمیت
   - اتصال به API `/api/v1/waves/alerts`

5. **صفحه تنظیمات**:
   - مدیریت کلیدواژه‌ها
   - تنظیمات API
   - اتصال به API‌های:
     - `/api/v1/tweets/keywords`
     - `/api/v1/settings`

### 9. دستورالعمل‌های توسعه برای هوش مصنوعی و توسعه‌دهندگان

برای توسعه مؤثر این پروژه، باید اصول زیر را رعایت کنید:

1. **استفاده از Async/Await**:
   تمام کدهای مرتبط با دیتابیس، Redis و API‌های خارجی باید از الگوی async/await استفاده کنند.

2. **مدیریت خطا**:
   تمام درخواست‌های خارجی باید در بلوک try/except قرار گیرند و خطاها به درستی ثبت شوند.

3. **ساختار ورودی/خروجی**:
   - ورودی/خروجی API‌ها باید با مدل‌های Pydantic تعریف شوند
   - ورودی/خروجی تابع‌ها باید نوع (Type Hints) داشته باشند

4. **لاگینگ**:
   استفاده از logger برای ثبت جزئیات عملیات و خطاها

5. **سازگاری زبانی**:
   پشتیبانی از زبان فارسی و انگلیسی در همه جای سیستم

6. **استراتژی توسعه**:
   توسعه مرحله‌ای با تمرکز بر قابلیت‌های دارای اولویت بالا در مستندات استراتژی

### 10. نمونه کدهای اصلی

#### نمونه 1: اندپوینت احراز هویت

```python
@router.post("/login", response_model=Token)
async def login(
        form_data: OAuth2PasswordRequestForm = Depends(),
        db: AsyncSession = Depends(get_db)
):
    """
    ورود به سیستم و دریافت توکن JWT.

    Args:
        form_data (OAuth2PasswordRequestForm): فرم ورود
        db (AsyncSession): نشست دیتابیس

    Returns:
        Token: توکن دسترسی

    Raises:
        HTTPException: در صورت نامعتبر بودن نام کاربری یا رمز عبور
    """
    # جستجوی کاربر در دیتابیس
    stmt = select(AppUser).where(AppUser.email == form_data.username)
    result = await db.execute(stmt)
    user = result.scalar_one_or_none()

    # بررسی وجود کاربر و صحت رمز عبور
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="نام کاربری یا رمز عبور نادرست است",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # بررسی فعال بودن کاربر
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="حساب کاربری غیرفعال است",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # ایجاد توکن دسترسی
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.email},
        expires_delta=access_token_expires
    )

    return {"access_token": access_token, "token_type": "bearer"}
```

#### نمونه 2: تحلیل احساسات با Claude API

```python
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
        text_content = next((item["text"] for item in response.content if item["type"] == "text"), None)
        if not text_content:
            raise ValueError("پاسخ معتبری از Claude دریافت نشد")
        
        json_str = text_content.strip()
        start_idx = json_str.find("{")
        end_idx = json_str.rfind("}") + 1
        if start_idx != -1 and end_idx != 0:
            json_str = json_str[start_idx:end_idx]
        result = json.loads(json_str)
        return result
    except (json.JSONDecodeError, ValueError) as e:
        logger.error(f"Error parsing sentiment analysis response: {e}")
        return {
            "sentiment": "unknown",
            "score": 0,
            "confidence": 0,
            "explanation": "خطا در پردازش پاسخ"
        }
```

#### نمونه 3: تشخیص موج‌های توییتری

```python
async def detect_volume_waves(
        self,
        keywords: Optional[List[str]] = None,
        hours_back: int = 24
) -> List[Dict[str, Any]]:
    """
    تشخیص موج‌های حجمی

    Args:
        keywords (Optional[List[str]]): کلیدواژه‌ها برای فیلتر کردن
        hours_back (int): تعداد ساعات برای بررسی

    Returns:
        List[Dict[str, Any]]: لیست موج‌های تشخیص داده شده
    """
    logger.info(f"Detecting volume waves for the past {hours_back} hours")

    # محاسبه زمان شروع و پایان
    end_time = datetime.utcnow()
    start_time = end_time - timedelta(hours=hours_back)

    # تقسیم زمان به بازه‌های time_window دقیقه‌ای
    time_windows = []
    window_start = start_time

    while window_start < end_time:
        window_end = window_start + timedelta(minutes=self.time_window)
        time_windows.append((window_start, min(window_end, end_time)))
        window_start = window_end

    # بررسی هر بازه زمانی
    volume_data = []
    prev_count = 0
    keyword_condition = None

#### نمونه 3: تشخیص موج‌های توییتری (ادامه)

```python
    # ایجاد شرط کلیدواژه‌ها
    if keywords:
        # دریافت شناسه‌های کلیدواژه‌ها از دیتابیس
        stmt = select(Keyword.id).where(Keyword.text.in_(keywords))
        result = await self.db_session.execute(stmt)
        keyword_ids = [row[0] for row in result.fetchall()]

        if keyword_ids:
            # ایجاد شرط برای توییت‌هایی که با این کلیدواژه‌ها مرتبط هستند
            keyword_condition = Tweet.id.in_(
                select(TweetKeyword.tweet_id).where(TweetKeyword.keyword_id.in_(keyword_ids))
            )

    # بررسی هر بازه زمانی
    for i, (window_start, window_end) in enumerate(time_windows):
        # شرط زمانی
        time_condition = and_(
            Tweet.created_at >= window_start,
            Tweet.created_at < window_end
        )

        # ترکیب شرط‌ها
        if keyword_condition:
            stmt_condition = and_(time_condition, keyword_condition)
        else:
            stmt_condition = time_condition

        # شمارش توییت‌ها در این بازه
        stmt = select(func.count()).where(stmt_condition)
        result = await self.db_session.execute(stmt)
        tweet_count = result.scalar() or 0

        # محاسبه نرخ تغییر
        if i > 0 and prev_count > 0:
            growth_rate = (tweet_count - prev_count) / prev_count if prev_count > 0 else 0
        else:
            growth_rate = 0

        volume_data.append({
            "start_time": window_start,
            "end_time": window_end,
            "tweet_count": tweet_count,
            "growth_rate": growth_rate
        })

        prev_count = tweet_count

    # تشخیص موج‌ها
    waves = []

    for i, data in enumerate(volume_data):
        # رد کردن بازه‌های با تعداد کم توییت
        if data["tweet_count"] < self.min_tweets:
            continue

        # بررسی افزایش ناگهانی نسبت به بازه قبلی
        if data["growth_rate"] >= self.volume_threshold:
            # محاسبه امتیاز اهمیت موج
            importance_score = min(10, data["growth_rate"] * 2.5 + (data["tweet_count"] / 10))
            
            # گردآوری اطلاعات موج
            wave = {
                "type": "volume",
                "start_time": data["start_time"].isoformat(),
                "end_time": data["end_time"].isoformat(),
                "tweet_count": data["tweet_count"],
                "growth_rate": data["growth_rate"],
                "importance_score": importance_score,
                # سایر اطلاعات موج...
            }
            
            waves.append(wave)

    logger.info(f"Detected {len(waves)} volume waves")
    return waves
```

#### نمونه 4: اندپوینت جستجوی توییت‌ها

```python
@router.get("/", response_model=List[TweetResponse])
async def get_tweets(
        params: TweetFilterParams = Depends(),
        db: AsyncSession = Depends(get_db),
        current_user: AppUser = Depends(get_current_user)
):
    """
    دریافت لیست توییت‌ها با امکان فیلتر کردن.

    Args:
        params (TweetFilterParams): پارامترهای فیلتر
        db (AsyncSession): نشست دیتابیس
        current_user (AppUser): کاربر فعلی

    Returns:
        List[TweetResponse]: لیست توییت‌ها
    """
    # ایجاد query پایه
    query = select(Tweet).join(User, Tweet.user_id == User.user_id, isouter=True)

    # اعمال فیلترها
    filters = []

    # فیلتر براساس متن
    if params.query:
        filters.append(Tweet.content.ilike(f"%{params.query}%"))

    # فیلتر براساس احساسات
    if params.sentiment:
        filters.append(Tweet.sentiment_label == params.sentiment)

    # فیلتر براساس کلیدواژه‌ها
    if params.keywords:
        keyword_subquery = select(TweetKeyword.tweet_id).join(
            Keyword, TweetKeyword.keyword_id == Keyword.id
        ).where(Keyword.text.in_(params.keywords))
        filters.append(Tweet.id.in_(keyword_subquery))

    # فیلتر براساس بازه زمانی
    if params.start_date:
        filters.append(Tweet.created_at >= params.start_date)
    if params.end_date:
        filters.append(Tweet.created_at <= params.end_date)

    # فیلتر براساس امتیاز اهمیت
    if params.min_importance:
        filters.append(Tweet.importance_score >= params.min_importance)

    # ترکیب فیلترها
    if filters:
        query = query.where(and_(*filters))

    # مرتب‌سازی
    if params.sort_by == "date":
        query = query.order_by(desc(Tweet.created_at))
    elif params.sort_by == "importance":
        query = query.order_by(desc(Tweet.importance_score))
    elif params.sort_by == "sentiment":
        query = query.order_by(Tweet.sentiment_score.desc())
    else:
        query = query.order_by(desc(Tweet.created_at))

    # صفحه‌بندی
    query = query.offset(params.skip).limit(params.limit)

    # اجرای query
    result = await db.execute(query)
    tweets = result.scalars().all()

    # تبدیل به فرمت پاسخ
    return [
        TweetResponse(
            id=tweet.id,
            tweet_id=tweet.tweet_id,
            content=tweet.content,
            created_at=tweet.created_at,
            language=tweet.language,
            user=tweet.user,
            sentiment_label=tweet.sentiment_label,
            sentiment_score=tweet.sentiment_score,
            importance_score=tweet.importance_score,
            is_processed=tweet.is_processed,
            is_analyzed=tweet.is_analyzed,
            entities=tweet.entities
        )
        for tweet in tweets
    ]
```

### 11. الگوهای طراحی و معماری

#### 11.1 معماری داده

- **الگوی داده‌های Layer**: جریان داده از جمع‌آوری به پردازش و سپس تحلیل
- **الگوی Repository**: ذخیره‌سازی و بازیابی داده با استفاده از SQLAlchemy
- **الگوی Domain Model**: استفاده از مدل‌های دامنه برای نمایش روابط بین موجودیت‌ها

#### 11.2 معماری سرویس

- **الگوی Microservice**: هر سرویس مسئولیت مشخصی دارد
- **الگوی Message Queue**: استفاده از Redis برای ارتباط بین سرویس‌ها
- **الگوی Facade**: استفاده از کلاس‌های اصلی سرویس برای سادگی استفاده

#### 11.3 معماری API

- **الگوی RESTful**: اندپوینت‌های API با رعایت اصول REST
- **الگوی Dependency Injection**: استفاده از Depends در FastAPI

### 12. نکات مهم برای توسعه‌دهندگان هوش مصنوعی

1. **پیاده‌سازی اندپوینت‌های جدید**:
   - همیشه از مدل‌های Pydantic برای اعتبارسنجی ورودی/خروجی استفاده کنید
   - اندپوینت‌ها باید برای پشتیبانی از زبان فارسی، UTF-8 را پشتیبانی کنند
   - برای هر اندپوینت، docstring کامل بنویسید

2. **الگوی توسعه روتر**:
   اندپوینت‌های جدید باید به روش زیر پیاده‌سازی شوند:

   ```python
   @router.get("/endpoint", response_model=ResponseModel)
   async def endpoint_function(
       param: ParamType,
       db: AsyncSession = Depends(get_db),
       current_user: AppUser = Depends(get_current_user)
   ):
       """
       توضیحات اندپوینت.
       """
       # پیاده‌سازی...
   ```

3. **مدیریت خطا**:
   همیشه از بلوک‌های try/except برای مدیریت خطاها و از HTTPException برای برگرداندن خطاهای HTTP استفاده کنید:

   ```python
   try:
       result = await service.do_something()
   except SomeException as e:
       logger.error(f"Error doing something: {e}")
       raise HTTPException(
           status_code=status.HTTP_400_BAD_REQUEST,
           detail=f"خطا در انجام عملیات: {str(e)}"
       )
   ```

4. **مدیریت منابع**:
   برای مدیریت اتصال‌ها، از context manager یا الگوی RAII استفاده کنید:

   ```python
   async with get_session() as session:
       # استفاده از session
   ```

5. **تست قبل از ادغام**:
   قبل از ادغام کد جدید، آن را با اسکریپت‌های تست موجود آزمایش کنید.

### 13. یادداشت‌های نهایی

اگر در هر بخش به کد کامل یا جزئیات بیشتری نیاز دارید، لطفاً درخواست کنید تا فایل‌های مرتبط ارسال شوند. این راهنما شامل اطلاعات کلی و نمونه‌های اصلی برای درک ساختار پروژه و نحوه توسعه آن است.

در فاز فعلی توسعه، تمرکز بر تکمیل فرانت‌اند اولیه و اندپوینت‌های ضروری API است. اگر به راهنمایی بیشتر درباره بخش خاصی نیاز دارید یا اگر به فایل‌های کامل خاصی نیاز دارید، لطفاً آن را درخواست کنید.

به یاد داشته باشید که در زمان توسعه، از قراردادهای نام‌گذاری و ساختار موجود پیروی کنید تا یکپارچگی پروژه حفظ شود. انتظار می‌رود که برای زبان فارسی، UTF-8 به درستی پشتیبانی شود و هدر مناسب و docstring‌ها در تمام فایل‌ها وجود داشته باشند.


## مستندات API و سرویس‌های خارجی

برای اطلاعات دقیق در مورد API‌ها و سرویس‌های خارجی استفاده شده در پروژه، به مستندات زیر مراجعه کنید:

- [مستندات TwitterAPI](twitter-api-optimized.md) - راهنمای استفاده از TwitterAPI.io
- [مستندات Anthropic API](anthropic-api-reference.md) - راهنمای استفاده از Claude API
- [راهنمای توسعه ماژول تحلیل](analyzer-guide.md)
- [راهنما و معرفی پروژه   ](rasad.md)



