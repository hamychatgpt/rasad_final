// dashboard.js - مدیریت داشبورد

// بارگذاری داشبورد
async function loadDashboard() {
    try {
        // بارگذاری آمار توییت‌ها
        const tweetsData = await api.get('/tweets/count');
        updateTweetStats(tweetsData);
        
        // بارگذاری هشدارهای اخیر
        const alerts = await api.get('/waves/alerts?limit=5&is_read=false');
        updateLatestAlerts(alerts);
        
        // بارگذاری موضوعات برتر
        const topics = await api.get('/analysis/topics?limit=5');
        updateTopTopics(topics);
        
        // بارگذاری کلیدواژه‌های فعال
        await updateActiveKeywords();
        
        // بارگذاری وضعیت سرویس‌ها
        await loadServices();
        
    } catch (error) {
        console.error('Error loading dashboard:', error);
        showErrorMessage('خطا در بارگذاری داشبورد');
    }
}

// بروزرسانی آمار توییت‌ها
function updateTweetStats(data) {
    // بروزرسانی تعداد کل توییت‌ها
    document.querySelector('#totalTweetsValue').textContent = data.total.toLocaleString();
    
    // محاسبه درصد احساسات
    const sentiments = data.sentiment_counts;
    const total = data.total || 1; // جلوگیری از تقسیم بر صفر
    
    const positivePercent = Math.round((sentiments.positive / total) * 100);
    const negativePercent = Math.round((sentiments.negative / total) * 100);
    
    // بروزرسانی درصدها
    document.querySelector('#positiveSentimentValue').textContent = positivePercent + '%';
    document.querySelector('#negativeSentimentValue').textContent = negativePercent + '%';
}

// بروزرسانی آخرین هشدارها
function updateLatestAlerts(alerts) {
    const alertsContainer = document.getElementById('latestAlerts');
    if (!alertsContainer) return;
    
    if (alerts.length === 0) {
        alertsContainer.innerHTML = '<p class="text-center text-muted">هشداری یافت نشد</p>';
        return;
    }
    
    alertsContainer.innerHTML = '';
    
    alerts.forEach(alert => {
        const alertElement = document.createElement('div');
        
        // تعیین کلاس آلرت بر اساس شدت
        let alertClass = 'alert-warning';
        if (alert.severity === 'high') alertClass = 'alert-danger';
        else if (alert.severity === 'low') alertClass = 'alert-info';
        
        alertElement.className = `alert ${alertClass}`;
        alertElement.innerHTML = `
            <h5>${alert.title}</h5>
            <p class="mb-0">${alert.message.substring(0, 100)}${alert.message.length > 100 ? '...' : ''}</p>
            <small class="text-muted">
                ${new Date(alert.created_at).toLocaleString('fa-IR')}
            </small>
        `;
        
        alertsContainer.appendChild(alertElement);
    });
    
    // بروزرسانی تعداد هشدارهای فعال
    document.querySelector('#activeAlertsValue').textContent = alerts.length.toString();
}

// بروزرسانی موضوعات برتر
function updateTopTopics(topics) {
    const topicsContainer = document.getElementById('topTopics');
    if (!topicsContainer) return;
    
    if (topics.length === 0) {
        topicsContainer.innerHTML = '<p class="text-center text-muted">موضوعی یافت نشد</p>';
        return;
    }
    
    topicsContainer.innerHTML = '';
    
    topics.forEach(topic => {
        const topicElement = document.createElement('div');
        topicElement.className = 'd-flex justify-content-between align-items-center mb-3';
        topicElement.innerHTML = `
            <span>${topic.name}</span>
            <span class="badge bg-primary rounded-pill">${topic.tweet_count}</span>
        `;
        topicsContainer.appendChild(topicElement);
    });
}

// اتصال گوش‌دهنده‌های رویداد برای داشبورد
function setupDashboardListeners() {
    const refreshDashboardButton = document.getElementById('refreshDashboard');
    if (refreshDashboardButton) {
        refreshDashboardButton.addEventListener('click', loadDashboard);
    }
    
    const viewAllAlertsButton = document.getElementById('viewAllAlerts');
    if (viewAllAlertsButton) {
        viewAllAlertsButton.addEventListener('click', () => {
            showPage('alerts');
        });
    }
    
    const viewTopTopicsButton = document.getElementById('viewTopTopics');
    if (viewTopTopicsButton) {
        viewTopTopicsButton.addEventListener('click', () => {
            showPage('analysis');
        });
    }
}