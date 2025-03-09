// tweets.js - مدیریت توییت‌ها

// بارگذاری توییت‌ها
async function loadTweets(params = new URLSearchParams()) {
    try {
        const queryString = params.toString();
        const endpoint = `/tweets/?${queryString}`;
        const tweets = await api.get(endpoint);
        
        displayTweets(tweets);
        return tweets;
    } catch (error) {
        console.error('Error loading tweets:', error);
        showErrorMessage('خطا در بارگذاری توییت‌ها');
        return [];
    }
}

// نمایش توییت‌ها در صفحه
function displayTweets(tweets) {
    const tweetsContainer = document.getElementById('tweetsList');
    if (!tweetsContainer) return;
    
    if (tweets.length === 0) {
        tweetsContainer.innerHTML = '<div class="alert alert-info">توییتی یافت نشد</div>';
        return;
    }
    
    tweetsContainer.innerHTML = '';
    
    tweets.forEach(tweet => {
        const tweetElement = document.createElement('div');
        tweetElement.className = 'tweet-card';
        
        // تعیین کلاس احساسات
        let sentimentClass = '';
        if (tweet.sentiment_label === 'positive') sentimentClass = 'sentiment-positive';
        else if (tweet.sentiment_label === 'negative') sentimentClass = 'sentiment-negative';
        else if (tweet.sentiment_label === 'neutral') sentimentClass = 'sentiment-neutral';
        else if (tweet.sentiment_label === 'mixed') sentimentClass = 'sentiment-mixed';
        
        tweetElement.innerHTML = `
            <div class="d-flex justify-content-between">
                <div>
                    <span class="tweet-user">${tweet.user ? tweet.user.username : 'ناشناس'}</span>
                    <span class="tweet-date">${formatDate(tweet.created_at)}</span>
                </div>
                <div>
                    <span class="sentiment-badge ${sentimentClass}">${getSentimentLabel(tweet.sentiment_label)}</span>
                </div>
            </div>
            <div class="tweet-content">${tweet.content}</div>
            <div class="d-flex justify-content-end">
                <button class="btn btn-sm btn-outline-primary me-2" onclick="showTweetDetails(${tweet.id})">
                    جزئیات
                </button>
                <button class="btn btn-sm btn-outline-secondary" onclick="analyzeTweet(${tweet.id})">
                    تحلیل
                </button>
            </div>
        `;
        
        tweetsContainer.appendChild(tweetElement);
    });
}

// تحلیل توییت
async function analyzeTweet(tweetId) {
    try {
        const response = await api.post(`/analysis/tweet/${tweetId}`);
        showSuccessMessage('تحلیل توییت با موفقیت انجام شد');
        
        // بارگذاری مجدد توییت‌ها برای نمایش نتایج جدید
        await loadTweets();
        
        return response;
    } catch (error) {
        console.error('Error analyzing tweet:', error);
        showErrorMessage('خطا در تحلیل توییت');
    }
}

// نمایش جزئیات توییت
function showTweetDetails(tweetId) {
    // کد نمایش جزئیات توییت در مودال
}

// تبدیل تاریخ به فرمت مناسب
function formatDate(dateString) {
    if (!dateString) return 'تاریخ نامشخص';
    
    const date = new Date(dateString);
    return new Intl.DateTimeFormat('fa-IR', {
        year: 'numeric',
        month: 'short',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
    }).format(date);
}

// تبدیل برچسب احساسات به متن فارسی
function getSentimentLabel(sentiment) {
    switch (sentiment) {
        case 'positive': return 'مثبت';
        case 'negative': return 'منفی';
        case 'neutral': return 'خنثی';
        case 'mixed': return 'ترکیبی';
        default: return 'نامشخص';
    }
}

// راه‌اندازی گوش‌دهنده‌های رویداد
function setupTweetListeners() {
    const searchForm = document.getElementById('tweetSearchForm');
    if (searchForm) {
        searchForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            
            const query = document.getElementById('searchQuery').value;
            const sentiment = document.getElementById('sentimentFilter').value;
            const keyword = document.getElementById('keywordFilter').value;
            const minImportance = document.getElementById('minImportance').value;
            
            const params = new URLSearchParams();
            if (query) params.append('query', query);
            if (sentiment && sentiment !== 'all') params.append('sentiment', sentiment);
            if (keyword && keyword !== 'all') params.append('keywords', keyword);
            if (minImportance) params.append('min_importance', minImportance);
            
            await loadTweets(params);
        });
    }
    
    // دکمه بازنشانی فیلترها
    const resetFiltersBtn = document.getElementById('resetFilters');
    if (resetFiltersBtn) {
        resetFiltersBtn.addEventListener('click', () => {
            document.getElementById('searchQuery').value = '';
            document.getElementById('sentimentFilter').value = 'all';
            document.getElementById('keywordFilter').value = 'all';
            document.getElementById('minImportance').value = '';
            
            loadTweets();
        });
    }
}

// صادر کردن توابع مورد نیاز
window.loadTweets = loadTweets;
window.analyzeTweet = analyzeTweet;
window.showTweetDetails = showTweetDetails;
window.setupTweetListeners = setupTweetListeners;