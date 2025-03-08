# راهنمای توسعه ماژول فرانت‌اند پروژه رصد

## معرفی و هدف

ماژول فرانت‌اند بخش مهمی از پروژه رصد است که رابط کاربری سیستم را فراهم می‌کند. هدف اصلی در فاز فعلی، توسعه یک فرانت‌اند ساده و کاربردی با استفاده از HTML/CSS/JavaScript و Bootstrap است که با API‌های بک‌اند ارتباط برقرار کند.

## ساختار فعلی

```
/frontend
  /app
    /app.js           # کد جاوااسکریپت اصلی
    /index.html       # صفحه اصلی HTML
  /styles.css         # استایل‌های CSS
```

## تکنولوژی‌های اصلی

- **HTML5**: برای ساختار صفحات
- **CSS3 / Bootstrap 5.3.2**: برای استایل‌دهی و رسپانسیو بودن
- **JavaScript (ES6+)**: برای منطق سمت کلاینت
- **Fetch API**: برای ارتباط با اندپوینت‌های بک‌اند
- **Chart.js**: برای نمودارها و تجسم داده‌ها

## صفحات اصلی برای پیاده‌سازی

### 1. صفحه ورود (Login)

**فایل اصلی**: index.html (بخش loginForm)

**قابلیت‌های کلیدی**:
- فرم ورود با نام کاربری (ایمیل) و رمز عبور
- نمایش خطاهای احراز هویت
- ذخیره توکن JWT در localStorage

**API مرتبط**:
```
POST /api/v1/auth/login
```

**نمونه کد ارتباط با API**:
```javascript
async function handleLogin(event) {
    event.preventDefault();
    
    const username = document.getElementById('username').value;
    const password = document.getElementById('password').value;
    
    try {
        const response = await fetch(`${API_BASE_URL}/auth/login`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/x-www-form-urlencoded'
            },
            body: new URLSearchParams({
                'username': username,
                'password': password
            })
        });
        
        if (!response.ok) {
            throw new Error('نام کاربری یا رمز عبور نادرست است');
        }
        
        const data = await response.json();
        authToken = data.access_token;
        localStorage.setItem('authToken', authToken);
        
        // نمایش داشبورد بعد از ورود موفق
        showPage('dashboard');
    } catch (error) {
        document.getElementById('loginError').textContent = error.message;
        document.getElementById('loginError').style.display = 'block';
    }
}
```

### 2. داشبورد (Dashboard)

**فایل اصلی**: index.html (بخش dashboardContent)

**قابلیت‌های کلیدی**:
- نمایش آمار کلی (تعداد توییت‌ها، توزیع احساسات، هشدارهای فعال)
- نمایش آخرین هشدارها
- نمایش موضوعات برتر
- نمایش کلیدواژه‌های فعال
- نمایش وضعیت سرویس‌ها

**API‌های مرتبط**:
```
GET /api/v1/tweets/count
GET /api/v1/waves/alerts?limit=5&is_read=false
GET /api/v1/analysis/topics?limit=5
GET /api/v1/tweets/keywords?active_only=true
GET /api/v1/services/
```

**نمونه کد ارتباط با API**:
```javascript
async function loadDashboard() {
    try {
        // بارگیری آمار توییت‌ها
        const tweetsResponse = await fetch(`${API_BASE_URL}/tweets/count`, {
            headers: { 'Authorization': `Bearer ${authToken}` }
        });
        
        if (tweetsResponse.ok) {
            const tweetsData = await tweetsResponse.json();
            
            // بروزرسانی آمار در UI
            document.getElementById('totalTweetsValue').textContent = 
                tweetsData.total.toLocaleString();
                
            // محاسبه درصد احساسات
            const sentiments = tweetsData.sentiment_counts;
            const total = tweetsData.total || 1;
            const positivePercent = Math.round((sentiments.positive / total) * 100);
            
            document.getElementById('positiveSentimentValue').textContent = 
                positivePercent + '%';
        }
        
        // بارگیری سایر داده‌ها در اینجا...
    } catch (error) {
        console.error('Error loading dashboard:', error);
    }
}
```

### 3. صفحه توییت‌ها (Tweets)

**فایل اصلی**: index.html (بخش tweetsContent)

**قابلیت‌های کلیدی**:
- فرم جستجو و فیلتر (براساس متن، احساسات، کلیدواژه‌ها، و امتیاز اهمیت)
- نمایش لیست توییت‌ها با امکان مرتب‌سازی
- نمایش جزئیات توییت در یک مدال
- دکمه تحلیل برای تحلیل مجدد یک توییت
- صفحه‌بندی نتایج

**API‌های مرتبط**:
```
GET /api/v1/tweets
POST /api/v1/analysis/tweet/{tweet_id}
```

**نمونه کد ارتباط با API**:
```javascript
async function loadTweets(event) {
    if (event) event.preventDefault();
    
    try {
        // پارامترهای فیلتر
        const query = document.getElementById('searchQuery').value;
        const sentiment = document.getElementById('sentimentFilter').value;
        const minImportance = document.getElementById('importanceFilter').value;
        
        let url = `${API_BASE_URL}/tweets?limit=10`;
        if (query) url += `&query=${encodeURIComponent(query)}`;
        if (sentiment) url += `&sentiment=${sentiment}`;
        if (minImportance) url += `&min_importance=${minImportance}`;
        
        const response = await fetch(url, {
            headers: { 'Authorization': `Bearer ${authToken}` }
        });
        
        if (!response.ok) {
            throw new Error('خطا در بارگیری توییت‌ها');
        }
        
        const tweets = await response.json();
        
        // نمایش توییت‌ها در UI
        displayTweets(tweets);
    } catch (error) {
        console.error('Error loading tweets:', error);
    }
}

function displayTweets(tweets) {
    const container = document.getElementById('tweetsList');
    container.innerHTML = '';
    
    if (tweets.length === 0) {
        container.innerHTML = '<div class="text-center p-4">توییتی یافت نشد</div>';
        return;
    }
    
    // ایجاد کارت برای هر توییت
    tweets.forEach(tweet => {
        const card = document.createElement('div');
        card.className = 'tweet-card';
        
        // تعیین رنگ احساسات
        let sentimentClass = 'sentiment-neutral';
        if (tweet.sentiment_label === 'positive') sentimentClass = 'sentiment-positive';
        if (tweet.sentiment_label === 'negative') sentimentClass = 'sentiment-negative';
        if (tweet.sentiment_label === 'mixed') sentimentClass = 'sentiment-mixed';
        
        card.innerHTML = `
            <div class="tweet-user">${tweet.user ? tweet.user.username : 'ناشناس'}</div>
            <div class="tweet-date">${new Date(tweet.created_at).toLocaleString('fa-IR')}</div>
            <div class="tweet-content">${tweet.content}</div>
            <div class="tweet-footer">
                <span class="sentiment-badge ${sentimentClass}">
                    ${tweet.sentiment_label || 'نامشخص'}
                </span>
                <button class="btn btn-sm btn-outline-primary analyze-btn" 
                        data-tweet-id="${tweet.id}">
                    <i class="bi bi-pie-chart"></i> تحلیل
                </button>
            </div>
        `;
        
        container.appendChild(card);
    });
    
    // اضافه کردن event listener به دکمه‌های تحلیل
    document.querySelectorAll('.analyze-btn').forEach(button => {
        button.addEventListener('click', () => {
            const tweetId = button.dataset.tweetId;
            analyzeTweet(tweetId);
        });
    });
}
```

### 4. صفحه هشدارها (Alerts)

**فایل اصلی**: index.html (بخش alertsContent)

**قابلیت‌های کلیدی**:
- فیلتر هشدارها (براساس نوع، شدت، و وضعیت خوانده شدن)
- نمایش لیست هشدارها با رنگ‌بندی متناسب با شدت
- مشاهده جزئیات هشدار
- علامت‌گذاری هشدار به عنوان خوانده شده

**API‌های مرتبط**:
```
GET /api/v1/waves/alerts
PUT /api/v1/waves/alerts/{alert_id}/read
```

**نمونه کد ارتباط با API**:
```javascript
async function loadAlerts(event) {
    if (event) event.preventDefault();
    
    try {
        // پارامترهای فیلتر
        const alertType = document.getElementById('alertType').value;
        const severity = document.getElementById('alertSeverity').value;
        const isRead = document.getElementById('isReadFilter').value;
        
        let url = `${API_BASE_URL}/waves/alerts?limit=10`;
        if (alertType) url += `&alert_type=${alertType}`;
        if (severity) url += `&severity=${severity}`;
        if (isRead !== '') url += `&is_read=${isRead}`;
        
        const response = await fetch(url, {
            headers: { 'Authorization': `Bearer ${authToken}` }
        });
        
        if (!response.ok) {
            throw new Error('خطا در بارگیری هشدارها');
        }
        
        const alerts = await response.json();
        
        // نمایش هشدارها در UI
        displayAlerts(alerts);
    } catch (error) {
        console.error('Error loading alerts:', error);
    }
}

async function markAlertAsRead(alertId) {
    try {
        const response = await fetch(`${API_BASE_URL}/waves/alerts/${alertId}/read`, {
            method: 'PUT',
            headers: { 'Authorization': `Bearer ${authToken}` }
        });
        
        if (!response.ok) {
            throw new Error('خطا در به‌روزرسانی هشدار');
        }
        
        // بروزرسانی UI
        loadAlerts();
    } catch (error) {
        console.error('Error marking alert as read:', error);
    }
}
```

### 5. صفحه تنظیمات (Settings)

**فایل اصلی**: index.html (بخش settingsContent)

**قابلیت‌های کلیدی**:
- مدیریت کلیدواژه‌ها (افزودن، ویرایش، حذف)
- تنظیمات API (بودجه روزانه، مدل کلود)
- نمایش آمار مصرف API

**API‌های مرتبط**:
```
GET /api/v1/tweets/keywords
POST /api/v1/tweets/keywords
DELETE /api/v1/tweets/keywords/{keyword_id}
GET /api/v1/settings/
PUT /api/v1/settings/
GET /api/v1/settings/budget
PUT /api/v1/settings/budget
GET /api/v1/settings/api-usage
```

**نمونه کد ارتباط با API**:
```javascript
async function loadKeywords() {
    try {
        const response = await fetch(`${API_BASE_URL}/tweets/keywords`, {
            headers: { 'Authorization': `Bearer ${authToken}` }
        });
        
        if (!response.ok) {
            throw new Error('خطا در بارگیری کلیدواژه‌ها');
        }
        
        const keywords = await response.json();
        
        // نمایش کلیدواژه‌ها در UI
        displayKeywords(keywords);
    } catch (error) {
        console.error('Error loading keywords:', error);
    }
}

async function addKeyword(event) {
    event.preventDefault();
    
    const text = document.getElementById('keywordText').value;
    const priority = parseInt(document.getElementById('keywordPriority').value);
    const description = document.getElementById('keywordDescription').value;
    
    try {
        const response = await fetch(`${API_BASE_URL}/tweets/keywords`, {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${authToken}`,
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                text: text,
                is_active: true,
                priority: priority,
                description: description
            })
        });
        
        if (!response.ok) {
            throw new Error('خطا در افزودن کلیدواژه');
        }
        
        // پاک کردن فرم و بروزرسانی لیست
        document.getElementById('keywordText').value = '';
        document.getElementById('keywordPriority').value = '1';
        document.getElementById('keywordDescription').value = '';
        
        loadKeywords();
    } catch (error) {
        console.error('Error adding keyword:', error);
    }
}
```

### 6. صفحه مدیریت سرویس‌ها (Services)

**فایل اصلی**: index.html (بخش servicesContent)

**قابلیت‌های کلیدی**:
- نمایش وضعیت سرویس‌های مختلف (جمع‌آوری کننده، پردازشگر، تحلیلگر)
- شروع و توقف سرویس‌ها
- نمایش لاگ‌های سیستم
- نمایش اطلاعات سیستم

**API‌های مرتبط**:
```
GET /api/v1/services/
POST /api/v1/services/{service_name}/start
POST /api/v1/services/{service_name}/stop
GET /api/v1/services/logs/{service_name}
```

**نمونه کد ارتباط با API**:
```javascript
async function loadServices() {
    try {
        const response = await fetch(`${API_BASE_URL}/services/`, {
            headers: { 'Authorization': `Bearer ${authToken}` }
        });
        
        if (!response.ok) {
            throw new Error('خطا در بارگیری وضعیت سرویس‌ها');
        }
        
        const data = await response.json();
        
        // بروزرسانی وضعیت سرویس‌ها در UI
        updateServiceStatus(data.services);
        
        // بروزرسانی اطلاعات سیستم
        updateSystemInfo(data.system_info);
    } catch (error) {
        console.error('Error loading services:', error);
    }
}

async function startService(serviceName) {
    try {
        const response = await fetch(`${API_BASE_URL}/services/${serviceName}/start`, {
            method: 'POST',
            headers: { 'Authorization': `Bearer ${authToken}` }
        });
        
        if (!response.ok) {
            throw new Error(`خطا در شروع سرویس ${serviceName}`);
        }
        
        // بروزرسانی وضعیت سرویس‌ها
        setTimeout(loadServices, 2000);
    } catch (error) {
        console.error(`Error starting service ${serviceName}:`, error);
    }
}
```

## نمودارها و تجسم داده‌ها

برای نمایش نمودارها، از کتابخانه Chart.js استفاده می‌شود. نمونه کد برای نمایش نمودار توزیع احساسات:

```javascript
function createSentimentChart(data) {
    const ctx = document.getElementById('sentimentChart').getContext('2d');
    
    const chartData = {
        labels: ['مثبت', 'منفی', 'خنثی', 'ترکیبی'],
        datasets: [{
            data: [
                data.positive || 0,
                data.negative || 0,
                data.neutral || 0,
                data.mixed || 0
            ],
            backgroundColor: [
                '#1cc88a',  // سبز
                '#e74a3b',  // قرمز
                '#858796',  // خاکستری
                '#f6c23e'   // زرد
            ],
            borderWidth: 1
        }]
    };
    
    const options = {
        responsive: true,
        maintainAspectRatio: false,
        legend: {
            position: 'right',
            rtl: true,
            labels: {
                fontFamily: 'Vazir'
            }
        }
    };
    
    new Chart(ctx, {
        type: 'doughnut',
        data: chartData,
        options: options
    });
}
```

## نکات مهم فنی

### 1. توکن احراز هویت
- توکن JWT در localStorage ذخیره می‌شود.
- در هر درخواست، توکن در هدر Authorization قرار می‌گیرد.
- زمانی که توکن منقضی می‌شود، کاربر به صفحه ورود هدایت می‌شود.

```javascript
// بررسی وضعیت ورود
function checkAuthStatus() {
    const token = localStorage.getItem('authToken');
    if (!token) {
        showPage('login');
        return;
    }
    
    // بررسی اعتبار توکن با درخواست به اندپوینت me
    fetch(`${API_BASE_URL}/auth/me`, {
        headers: {
            'Authorization': `Bearer ${token}`
        }
    })
    .then(response => {
        if (!response.ok) {
            throw new Error('توکن نامعتبر است');
        }
        return response.json();
    })
    .then(user => {
        // ذخیره اطلاعات کاربر و نمایش داشبورد
        currentUser = user;
        document.getElementById('userDisplayName').textContent = user.email;
        showPage('dashboard');
    })
    .catch(error => {
        // حذف توکن و هدایت به صفحه ورود
        localStorage.removeItem('authToken');
        showPage('login');
    });
}
```

### 2. مدیریت چند زبانه
- همه رابط کاربری به فارسی است.
- تاریخ‌ها با `toLocaleString('fa-IR')` نمایش داده می‌شوند.
- اعداد با `toLocaleString('fa-IR')` نمایش داده می‌شوند.

### 3. مدیریت خطاها
- خطاهای شبکه باید به کاربر نمایش داده شوند.
- هنگام بارگیری داده‌ها، باید نمایشگر لودینگ نمایش داده شود.

```javascript
// مدیریت خطاها
function handleApiError(error, elementId) {
    const errorElement = document.getElementById(elementId);
    errorElement.textContent = error.message || 'خطا در ارتباط با سرور';
    errorElement.style.display = 'block';
    
    // پنهان کردن خطا بعد از 5 ثانیه
    setTimeout(() => {
        errorElement.style.display = 'none';
    }, 5000);
}

// نمایش لودینگ
function showLoading(containerId) {
    const container = document.getElementById(containerId);
    container.innerHTML = `
        <div class="text-center p-4">
            <div class="spinner-border text-primary" role="status">
                <span class="visually-hidden">در حال بارگذاری...</span>
            </div>
        </div>
    `;
}
```

### 4. پاسخگویی (Responsive Design)
- از کلاس‌های Bootstrap برای رسپانسیو بودن رابط کاربری استفاده شود.
- از media query‌ها برای تنظیم طرح‌بندی در اندازه‌های مختلف استفاده شود.

```css
/* مثال media query برای دستگاه‌های موبایل */
@media (max-width: 768px) {
    .stat-card {
        margin-bottom: 15px;
    }
    
    .stat-card .stat-value {
        font-size: 24px;
    }
}
```

## قواعد کدنویسی

1. **نام‌گذاری**:
   - نام توابع با camelCase (مانند `loadTweets`)
   - نام متغیرها با camelCase (مانند `authToken`)
   - نام ثابت‌ها با UPPER_SNAKE_CASE (مانند `API_BASE_URL`)

2. **دسته‌بندی**:
   - توابع مرتبط با هر صفحه در بخش‌های مجزا قرار گیرند
   - توابع عمومی در بالای فایل قرار گیرند

3. **کامنت‌گذاری**:
   - برای هر تابع، کامنت توضیحی نوشته شود
   - برای بخش‌های پیچیده، کامنت درون تابع اضافه شود

4. **مدیریت رویدادها**:
   - از انتخابگرهای مناسب برای افزودن رویدادها استفاده شود
   - از تکنیک event delegation برای رویدادهای پویا استفاده شود

## نحوه استفاده از فرانت‌اند با بک‌اند

برای استفاده از فرانت‌اند با بک‌اند:

1. **پورت**:
   - بک‌اند معمولاً روی پورت 8000 اجرا می‌شود
   - آدرس پایه API به صورت `http://localhost:8000/api/v1` است

2. **CORS**:
   - بک‌اند CORS را پشتیبانی می‌کند
   - در فایل `.env` می‌توان دامنه‌های مجاز را تنظیم کرد

3. **راه‌اندازی ساده**:
   - فایل‌های فرانت‌اند را می‌توان مستقیماً از مرورگر باز کرد
   - برای استفاده در محیط توسعه، می‌توان از یک سرور ساده HTTP استفاده کرد:
     ```bash
     # با استفاده از Python
     cd frontend
     python -m http.server 3000
     ```

## مراحل بعدی توسعه

1. **بهبود رابط کاربری**:
   - ارتقا به فریم‌ورک React برای مدیریت بهتر state
   - استفاده از کامپوننت‌های مدرن UI
   - بهبود موبایل فرندلی بودن

2. **افزودن قابلیت‌های پیشرفته**:
   - نمودارهای تعاملی پیشرفته
   - داشبورد قابل شخصی‌سازی
   - سیستم اعلان‌های بلادرنگ

3. **بهبود تجربه کاربری**:
   - انیمیشن‌های بهتر
   - راهنماهای داخل برنامه
   - تم روشن/تاریک

## راهنمای عیب‌یابی

1. **مشکلات CORS**:
   - اطمینان حاصل کنید که دامنه فرانت‌اند در تنظیمات CORS بک‌اند مجاز است
   - در محیط توسعه، می‌توانید از یک پروکسی CORS استفاده کنید

2. **مشکلات احراز هویت**:
   - بررسی کنید که توکن به درستی در localStorage ذخیره شده باشد
   - اطمینان حاصل کنید که توکن در هدر Authorization قرار دارد

3. **خطاهای API**:
   - همیشه کنسول مرورگر را برای خطاهای شبکه بررسی کنید
   - از network tab مرورگر برای بررسی درخواست‌ها و پاسخ‌ها استفاده کنید

---

این راهنما برای کمک به توسعه‌دهندگان در ایجاد و بهبود فرانت‌اند پروژه رصد طراحی شده است. تمام کدهای ارائه شده باید با معماری و ساختار موجود هماهنگ باشند و از قراردادهای نام‌گذاری و کدنویسی پروژه پیروی کنند.