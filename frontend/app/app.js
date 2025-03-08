// تنظیمات اصلی
const API_BASE_URL = 'http://localhost:8000/api/v1';
let authToken = localStorage.getItem('authToken');
let currentPage = 'dashboard';

// اتصال به المان‌های DOM
document.addEventListener('DOMContentLoaded', () => {
    // لینک‌های ناوبری
    document.getElementById('dashboardLink').addEventListener('click', () => showPage('dashboard'));
    document.getElementById('tweetsLink').addEventListener('click', () => showPage('tweets'));
    document.getElementById('alertsLink').addEventListener('click', () => showPage('alerts'));
    document.getElementById('settingsLink').addEventListener('click', () => showPage('settings'));
    document.getElementById('loginLink').addEventListener('click', () => showPage('login'));

    // فرم‌ها
    document.getElementById('authForm').addEventListener('submit', handleLogin);
    document.getElementById('tweetFilterForm').addEventListener('submit', loadTweets);
    document.getElementById('alertFilterForm').addEventListener('submit', loadAlerts);
    document.getElementById('addKeywordForm').addEventListener('submit', addKeyword);
    document.getElementById('apiSettingsForm').addEventListener('submit', saveApiSettings);

    // دکمه‌های بروزرسانی
    document.getElementById('refreshTweets').addEventListener('click', loadTweets);
    document.getElementById('refreshAlerts').addEventListener('click', loadAlerts);

    // بررسی وضعیت ورود
    checkAuthStatus();
});

// بررسی وضعیت ورود
function checkAuthStatus() {
    if (!authToken) {
        showPage('login');
        return;
    }

    // بررسی اعتبار توکن
    fetch(`${API_BASE_URL}/auth/me`, {
        method: 'GET',
        headers: {
            'Authorization': `Bearer ${authToken}`
        }
    })
    .then(response => {
        if (!response.ok) {
            throw new Error('توکن نامعتبر است');
        }
        return response.json();
    })
    .then(data => {
        console.log('User info:', data);
        document.getElementById('loginLink').textContent = data.email;
        loadDashboard();
    })
    .catch(error => {
        console.error('Auth error:', error);
        localStorage.removeItem('authToken');
        authToken = null;
        showPage('login');
    });
}

// مدیریت ورود
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

        checkAuthStatus();
        showPage('dashboard');
    } catch (error) {
        console.error('Login error:', error);
        alert(error.message);
    }
}

// نمایش صفحه مورد نظر
function showPage(page) {
    currentPage = page;

    // پنهان کردن همه صفحات
    document.getElementById('dashboardContent').style.display = 'none';
    document.getElementById('tweetsContent').style.display = 'none';
    document.getElementById('alertsContent').style.display = 'none';
    document.getElementById('settingsContent').style.display = 'none';
    document.getElementById('loginForm').style.display = 'none';

    // غیرفعال کردن همه لینک‌ها
    document.querySelectorAll('.nav-link').forEach(link => {
        link.classList.remove('active');
    });

    // نمایش صفحه مورد نظر
    if (page === 'login') {
        document.getElementById('loginForm').style.display = 'block';
    } else if (page === 'dashboard') {
        document.getElementById('dashboardContent').style.display = 'block';
        document.getElementById('dashboardLink').classList.add('active');
        loadDashboard();
    } else if (page === 'tweets') {
        document.getElementById('tweetsContent').style.display = 'block';
        document.getElementById('tweetsLink').classList.add('active');
        loadTweets();
    } else if (page === 'alerts') {
        document.getElementById('alertsContent').style.display = 'block';
        document.getElementById('alertsLink').classList.add('active');
        loadAlerts();
    } else if (page === 'settings') {
        document.getElementById('settingsContent').style.display = 'block';
        document.getElementById('settingsLink').classList.add('active');
        loadSettings();
    }
}

// بارگیری داشبورد
async function loadDashboard() {
    if (!authToken) return;

    try {
        // بارگیری آمار توییت‌ها
        const tweetsResponse = await fetch(`${API_BASE_URL}/tweets/count`, {
            headers: { 'Authorization': `Bearer ${authToken}` }
        });

        if (tweetsResponse.ok) {
            const tweetsData = await tweetsResponse.json();

            // بروزرسانی آمار
            document.querySelector('#dashboardStats .card:nth-child(1) .card-text').textContent =
                tweetsData.total.toLocaleString();

            const sentiments = tweetsData.sentiment_counts;
            const total = tweetsData.total || 1; // جلوگیری از تقسیم بر صفر

            const positivePercent = Math.round((sentiments.positive / total) * 100);
            const negativePercent = Math.round((sentiments.negative / total) * 100);

            document.querySelector('#dashboardStats .card:nth-child(2) .card-text').textContent =
                positivePercent + '%';
            document.querySelector('#dashboardStats .card:nth-child(3) .card-text').textContent =
                negativePercent + '%';
        }

        // بارگیری آمار هشدارها
        const alertsResponse = await fetch(`${API_BASE_URL}/waves/alerts?limit=5&is_read=false`, {
            headers: { 'Authorization': `Bearer ${authToken}` }
        });

        if (alertsResponse.ok) {
            const alertsData = await alertsResponse.json();

            document.querySelector('#dashboardStats .card:nth-child(4) .card-text').textContent =
                alertsData.length.toString();

            // بروزرسانی لیست هشدارها
            const alertsContainer = document.getElementById('latestAlerts');

            if (alertsData.length === 0) {
                alertsContainer.innerHTML = '<p class="text-center text-muted">هشداری یافت نشد</p>';
            } else {
                alertsContainer.innerHTML = '';

                alertsData.forEach(alert => {
                    const alertElement = document.createElement('div');
                    alertElement.className = 'alert alert-warning';
                    alertElement.innerHTML = `
                        <h5>${alert.title}</h5>
                        <p class="mb-0">${alert.message}</p>
                        <small class="text-muted">
                            ${new Date(alert.created_at).toLocaleString('fa-IR')}
                        </small>
                    `;
                    alertsContainer.appendChild(alertElement);
                });
            }
        }

        // بارگیری موضوعات برتر
        const topicsResponse = await fetch(`${API_BASE_URL}/analysis/topics?limit=5`, {
            headers: { 'Authorization': `Bearer ${authToken}` }
        });

        if (topicsResponse.ok) {
            const topicsData = await topicsResponse.json();

            const topicsContainer = document.getElementById('topTopics');

            if (topicsData.length === 0) {
                topicsContainer.innerHTML = '<p class="text-center text-muted">موضوعی یافت نشد</p>';
            } else {
                topicsContainer.innerHTML = '';

                topicsData.forEach(topic => {
                    const topicElement = document.createElement('div');
                    topicElement.className = 'd-flex justify-content-between align-items-center mb-3';
                    topicElement.innerHTML = `
                        <span>${topic.name}</span>
                        <span class="badge bg-primary rounded-pill">${topic.tweet_count}</span>
                    `;
                    topicsContainer.appendChild(topicElement);
                });
            }
        }

    } catch (error) {
        console.error('Error loading dashboard:', error);
    }
}

// بارگیری توییت‌ها
async function loadTweets(event) {
    if (event) event.preventDefault();
    if (!authToken) return;

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
        const tweetsContainer = document.getElementById('tweetsList');

        if (tweets.length === 0) {
            tweetsContainer.innerHTML = '<tr><td colspan="6" class="text-center">توییتی یافت نشد</td></tr>';
        } else {
            tweetsContainer.innerHTML = '';

            tweets.forEach(tweet => {
                const row = document.createElement('tr');

                // تعیین رنگ براساس احساسات
                let sentimentBadge = '<span class="badge bg-secondary">نامشخص</span>';
                if (tweet.sentiment_label === 'positive') {
                    sentimentBadge = '<span class="badge bg-success">مثبت</span>';
                } else if (tweet.sentiment_label === 'negative') {
                    sentimentBadge = '<span class="badge bg-danger">منفی</span>';
                } else if (tweet.sentiment_label === 'neutral') {
                    sentimentBadge = '<span class="badge bg-light text-dark">خنثی</span>';
                } else if (tweet.sentiment_label === 'mixed') {
                    sentimentBadge = '<span class="badge bg-warning text-dark">ترکیبی</span>';
                }

                row.innerHTML = `
                    <td>${tweet.content}</td>
                    <td>${tweet.user ? tweet.user.username : 'ناشناس'}</td>
                    <td>${sentimentBadge} ${tweet.sentiment_score ? (tweet.sentiment_score * 100).toFixed(0) + '%' : ''}</td>
                    <td>${tweet.importance_score ? tweet.importance_score.toFixed(2) : '-'}</td>
                    <td>${tweet.created_at ? new Date(tweet.created_at).toLocaleString('fa-IR') : '-'}</td>
                    <td>
                        <button class="btn btn-sm btn-outline-primary" onclick="analyzeTweet(${tweet.id})">
                            <i class="bi bi-pie-chart"></i>
                        </button>
                    </td>
                `;

                tweetsContainer.appendChild(row);
            });
        }
    } catch (error) {
        console.error('Error loading tweets:', error);
        alert(error.message);
    }
}

// تحلیل توییت
async function analyzeTweet(tweetId) {
    if (!authToken) return;

    try {
        const response = await fetch(`${API_BASE_URL}/analysis/tweet/${tweetId}`, {
            method: 'POST',
            headers: { 'Authorization': `Bearer ${authToken}` }
        });

        if (!response.ok) {
            throw new Error('خطا در تحلیل توییت');
        }

        const result = await response.json();
        alert(`تحلیل توییت با موفقیت انجام شد. احساس: ${result.sentiment.label}`);

        // بروزرسانی لیست توییت‌ها
        loadTweets();
    } catch (error) {
        console.error('Error analyzing tweet:', error);
        alert(error.message);
    }
}

// بارگیری هشدارها
async function loadAlerts(event) {
    if (event) event.preventDefault();
    if (!authToken) return;

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
        const alertsContainer = document.getElementById('alertsList');

        if (alerts.length === 0) {
            alertsContainer.innerHTML = '<div class="col-12"><p class="text-center text-muted">هشداری یافت نشد</p></div>';
        } else {
            alertsContainer.innerHTML = '';

            alerts.forEach(alert => {
                const card = document.createElement('div');
                card.className = 'col-md-6 mb-3';

                // تعیین رنگ براساس شدت
                let cardClass = 'alert-warning';
                if (alert.severity === 'high') {
                    cardClass = 'alert-danger';
                } else if (alert.severity === 'low') {
                    cardClass = 'alert-info';
                }

                let alertIcon = '';
                if (alert.alert_type === 'volume_wave') {
                    alertIcon = '<i class="bi bi-graph-up-arrow"></i>';
                } else if (alert.alert_type === 'sentiment_shift') {
                    alertIcon = '<i class="bi bi-emoji-angry"></i>';
                }

                let readBadge = alert.is_read
                    ? '<span class="badge bg-secondary ms-2">خوانده شده</span>'
                    : '<span class="badge bg-success ms-2">جدید</span>';

                card.innerHTML = `
                    <div class="card alert-card ${cardClass}">
                        <div class="card-header d-flex justify-content-between align-items-center">
                            <span>${alertIcon} ${alert.title} ${readBadge}</span>
                            <button class="btn btn-sm btn-outline-dark" onclick="markAlertAsRead(${alert.id})">
                                <i class="bi bi-check2"></i>
                            </button>
                        </div>
                        <div class="card-body">
                            <p class="card-text">${alert.message}</p>
                            <p class="card-text"><small class="text-muted">
                                ${new Date(alert.created_at).toLocaleString('fa-IR')}
                            </small></p>
                        </div>
                    </div>
                `;

                alertsContainer.appendChild(card);
            });
        }
    } catch (error) {
        console.error('Error loading alerts:', error);
        alert(error.message);
    }
}

// علامت‌گذاری هشدار به عنوان خوانده شده
async function markAlertAsRead(alertId) {
    if (!authToken) return;

    try {
        const response = await fetch(`${API_BASE_URL}/waves/alerts/${alertId}/read`, {
            method: 'PUT',
            headers: { 'Authorization': `Bearer ${authToken}` }
        });

        if (!response.ok) {
            throw new Error('خطا در به‌روزرسانی هشدار');
        }

        // بروزرسانی لیست هشدارها
        loadAlerts();

        // اگر در صفحه داشبورد هستیم، آن را نیز بروزرسانی کنیم
        if (currentPage === 'dashboard') {
            loadDashboard();
        }
    } catch (error) {
        console.error('Error marking alert as read:', error);
    }
}

// بارگیری تنظیمات
async function loadSettings() {
    if (!authToken) return;

    try {
        // بارگیری کلیدواژه‌ها
        const keywordsResponse = await fetch(`${API_BASE_URL}/tweets/keywords`, {
            headers: { 'Authorization': `Bearer ${authToken}` }
        });

        if (keywordsResponse.ok) {
            const keywords = await keywordsResponse.json();
            const keywordsContainer = document.getElementById('keywordsList');

            if (keywords.length === 0) {
                keywordsContainer.innerHTML = '<tr><td colspan="5" class="text-center">کلیدواژه‌ای یافت نشد</td></tr>';
            } else {
                keywordsContainer.innerHTML = '';

                keywords.forEach(keyword => {
                    const row = document.createElement('tr');

                    const statusBadge = keyword.is_active
                        ? '<span class="badge bg-success">فعال</span>'
                        : '<span class="badge bg-secondary">غیرفعال</span>';

                    row.innerHTML = `
                        <td>${keyword.text}</td>
                        <td>${statusBadge}</td>
                        <td>${keyword.priority}</td>
                        <td>${keyword.description || '-'}</td>
                        <td>
                            <button class="btn btn-sm btn-outline-danger" onclick="deleteKeyword(${keyword.id})">
                                <i class="bi bi-trash"></i>
                            </button>
                        </td>
                    `;

                    keywordsContainer.appendChild(row);
                });
            }
        }

        // بارگیری تنظیمات API
        const settingsResponse = await fetch(`${API_BASE_URL}/settings/`, {
            headers: { 'Authorization': `Bearer ${authToken}` }
        });

        if (settingsResponse.ok) {
            const settings = await settingsResponse.json();

            document.getElementById('dailyBudget').value = settings.daily_budget;
            document.getElementById('claudeModel').value = settings.claude_model;
        }

    } catch (error) {
        console.error('Error loading settings:', error);
    }
}

// افزودن کلیدواژه
async function addKeyword(event) {
    event.preventDefault();
    if (!authToken) return;

    try {
        const keywordText = document.getElementById('keywordText').value;
        const priority = parseInt(document.getElementById('keywordPriority').value);
        const description = document.getElementById('keywordDescription').value;

        const response = await fetch(`${API_BASE_URL}/tweets/keywords`, {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${authToken}`,
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                text: keywordText,
                is_active: true,
                priority: priority,
                description: description
            })
        });

        if (!response.ok) {
            throw new Error('خطا در افزودن کلیدواژه');
        }

        // پاک کردن فرم
        document.getElementById('keywordText').value = '';
        document.getElementById('keywordPriority').value = '1';
        document.getElementById('keywordDescription').value = '';

        // بروزرسانی لیست کلیدواژه‌ها
        loadSettings();

    } catch (error) {
        console.error('Error adding keyword:', error);
        alert(error.message);
    }
}

// حذف کلیدواژه
async function deleteKeyword(keywordId) {
    if (!authToken) return;

    if (!confirm('آیا از حذف این کلیدواژه اطمینان دارید؟')) {
        return;
    }

    try {
        const response = await fetch(`${API_BASE_URL}/tweets/keywords/${keywordId}`, {
            method: 'DELETE',
            headers: { 'Authorization': `Bearer ${authToken}` }
        });

        if (!response.ok) {
            throw new Error('خطا در حذف کلیدواژه');
        }

        // بروزرسانی لیست کلیدواژه‌ها
        loadSettings();

    } catch (error) {
        console.error('Error deleting keyword:', error);
        alert(error.message);
    }
}

// ذخیره تنظیمات API
async function saveApiSettings(event) {
    event.preventDefault();
    if (!authToken) return;

    try {
        const dailyBudget = parseFloat(document.getElementById('dailyBudget').value);
        const claudeModel = document.getElementById('claudeModel').value;

        // بروزرسانی بودجه
        const budgetResponse = await fetch(`${API_BASE_URL}/settings/budget?daily_budget=${dailyBudget}`, {
            method: 'PUT',
            headers: { 'Authorization': `Bearer ${authToken}` }
        });

        if (!budgetResponse.ok) {
            throw new Error('خطا در بروزرسانی بودجه');
        }

        // بروزرسانی سایر تنظیمات
        const settingsResponse = await fetch(`${API_BASE_URL}/settings/`, {
            method: 'PUT',
            headers: {
                'Authorization': `Bearer ${authToken}`,
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                project_name: "Rasad",
                debug: false,
                daily_budget: dailyBudget,
                analyzer_batch_size: 50,
                twitter_api_base_url: "https://api.twitterapi.io",
                claude_model: claudeModel
            })
        });

        if (!settingsResponse.ok) {
            throw new Error('خطا در بروزرسانی تنظیمات');
        }

        alert('تنظیمات با موفقیت ذخیره شد.');

    } catch (error) {
        console.error('Error saving settings:', error);
        alert(error.message);
    }
}