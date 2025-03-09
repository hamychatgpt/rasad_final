// tweets.js - مدیریت توییت‌ها

// متغیرهای داخلی ماژول
let currentPage = 1;
let pageSize = 10;
let totalTweets = 0;
let currentTweetId = null; // برای استفاده در مدال جزئیات توییت

// بارگذاری توییت‌ها با قابلیت فیلتر
async function loadTweets(event) {
    if (event) event.preventDefault();
    
    // نمایش وضعیت در حال بارگذاری
    document.getElementById('tweetsList').innerHTML = `
        <div class="text-center py-4">
            <div class="spinner-border text-primary" role="status">
                <span class="visually-hidden">در حال بارگذاری...</span>
            </div>
        </div>
    `;
    
    try {
        // پارامترهای فیلتر
        const query = document.getElementById('searchQuery')?.value || '';
        const sentiment = document.getElementById('sentimentFilter')?.value || '';
        const keywordFilter = document.getElementById('keywordFilter')?.value || '';
        const minImportance = document.getElementById('importanceFilter')?.value || '0';
        
        // ساخت URL با پارامترهای فیلتر
        let url = `/api/v1/tweets?limit=${pageSize}&skip=${(currentPage - 1) * pageSize}`;
        if (query) url += `&query=${encodeURIComponent(query)}`;
        if (sentiment) url += `&sentiment=${sentiment}`;
        if (keywordFilter) url += `&keywords=${encodeURIComponent(keywordFilter)}`;
        if (minImportance) url += `&min_importance=${minImportance}`;
        
        // دریافت توییت‌ها از سرور
        const tweets = await api.get(url);
        
        // دریافت تعداد کل توییت‌ها
        const countResponse = await api.get(`/api/v1/tweets/count?query=${encodeURIComponent(query)}&sentiment=${sentiment}`);
        totalTweets = countResponse.total;
        
        // بروزرسانی نمایش تعداد توییت‌ها
        document.getElementById('tweetCount').textContent = totalTweets.toLocaleString();
        
        // نمایش توییت‌ها
        displayTweets(tweets);
        
        // بروزرسانی صفحه‌بندی
        updatePagination();
        
    } catch (error) {
        console.error('Error loading tweets:', error);
        document.getElementById('tweetsList').innerHTML = `
            <div class="alert alert-danger">
                خطا در بارگذاری توییت‌ها: ${error.message || 'خطای ناشناخته'}
            </div>
        `;
    }
}

// نمایش توییت‌ها در صفحه
function displayTweets(tweets) {
    const tweetsContainer = document.getElementById('tweetsList');
    
    if (!tweets || tweets.length === 0) {
        tweetsContainer.innerHTML = '<div class="text-center py-4">توییتی یافت نشد</div>';
        return;
    }
    
    tweetsContainer.innerHTML = '';
    
    // ایجاد کارت برای هر توییت
    tweets.forEach(tweet => {
        const tweetCard = document.createElement('div');
        tweetCard.className = 'tweet-card';
        
        // تعیین کلاس برچسب احساسات
        let sentimentBadge = '<span class="badge bg-secondary">نامشخص</span>';
        if (tweet.sentiment_label === 'positive') {
            sentimentBadge = '<span class="badge sentiment-badge sentiment-positive">مثبت</span>';
        } else if (tweet.sentiment_label === 'negative') {
            sentimentBadge = '<span class="badge sentiment-badge sentiment-negative">منفی</span>';
        } else if (tweet.sentiment_label === 'neutral') {
            sentimentBadge = '<span class="badge sentiment-badge sentiment-neutral">خنثی</span>';
        } else if (tweet.sentiment_label === 'mixed') {
            sentimentBadge = '<span class="badge sentiment-badge sentiment-mixed">ترکیبی</span>';
        }
        
        // ایجاد محتوای کارت
        tweetCard.innerHTML = `
            <div class="d-flex justify-content-between">
                <div class="tweet-user">
                    ${tweet.user ? '@' + tweet.user.username : 'کاربر ناشناس'}
                    ${tweet.user && tweet.user.verified ? '<i class="bi bi-patch-check-fill text-primary"></i>' : ''}
                </div>
                <div class="tweet-date">
                    ${tweet.created_at ? new Date(tweet.created_at).toLocaleString('fa-IR') : '-'}
                </div>
            </div>
            <div class="tweet-content">
                ${tweet.content}
            </div>
            <div class="d-flex justify-content-between">
                <div>
                    ${sentimentBadge}
                    ${tweet.sentiment_score ? 
                      `<span class="badge bg-light text-dark">${Math.round(tweet.sentiment_score * 100)}%</span>` : ''}
                    ${tweet.importance_score ? 
                      `<span class="badge bg-info">اهمیت: ${tweet.importance_score.toFixed(1)}</span>` : ''}
                </div>
                <div>
                    <button class="btn btn-sm btn-outline-primary view-tweet" data-id="${tweet.id}">
                        <i class="bi bi-eye"></i>
                    </button>
                    <button class="btn btn-sm btn-outline-success analyze-tweet" data-id="${tweet.id}" 
                        ${tweet.is_analyzed ? 'disabled' : ''}>
                        <i class="bi bi-graph-up"></i>
                    </button>
                </div>
            </div>
        `;
        
        tweetsContainer.appendChild(tweetCard);
    });
    
    // اضافه کردن event listener به دکمه‌ها
    document.querySelectorAll('.view-tweet').forEach(button => {
        button.addEventListener('click', function() {
            const tweetId = this.getAttribute('data-id');
            showTweetDetails(tweetId);
        });
    });
    
    document.querySelectorAll('.analyze-tweet').forEach(button => {
        button.addEventListener('click', function() {
            const tweetId = this.getAttribute('data-id');
            analyzeTweet(tweetId);
        });
    });
}

// بروزرسانی صفحه‌بندی
function updatePagination() {
    const paginationContainer = document.getElementById('tweetPagination');
    if (!paginationContainer) return;
    
    const totalPages = Math.ceil(totalTweets / pageSize);
    
    // ایجاد المان‌های صفحه‌بندی
    let paginationHTML = '';
    
    // دکمه قبلی
    paginationHTML += `
        <li class="page-item ${currentPage === 1 ? 'disabled' : ''}">
            <a class="page-link" href="#" data-page="${currentPage - 1}" aria-disabled="${currentPage === 1}">قبلی</a>
        </li>
    `;
    
    // صفحات
    const startPage = Math.max(1, currentPage - 2);
    const endPage = Math.min(totalPages, startPage + 4);
    
    for (let i = startPage; i <= endPage; i++) {
        paginationHTML += `
            <li class="page-item ${i === currentPage ? 'active' : ''}">
                <a class="page-link" href="#" data-page="${i}">${i}</a>
            </li>
        `;
    }
    
    // دکمه بعدی
    paginationHTML += `
        <li class="page-item ${currentPage === totalPages ? 'disabled' : ''}">
            <a class="page-link" href="#" data-page="${currentPage + 1}" aria-disabled="${currentPage === totalPages}">بعدی</a>
        </li>
    `;
    
    paginationContainer.innerHTML = paginationHTML;
    
    // اضافه کردن event listener به لینک‌های صفحه‌بندی
    document.querySelectorAll('#tweetPagination .page-link').forEach(link => {
        link.addEventListener('click', function(e) {
            e.preventDefault();
            const page = parseInt(this.getAttribute('data-page'));
            if (page && page !== currentPage && page > 0 && page <= totalPages) {
                currentPage = page;
                loadTweets();
            }
        });
    });
}

// بارگذاری کلیدواژه‌ها در فیلتر
async function loadKeywordsFilter() {
    try {
        const keywordFilter = document.getElementById('keywordFilter');
        if (!keywordFilter) return;
        
        const keywords = await loadKeywords(true); // از keywords.js
        
        // تنظیم گزینه‌های فیلتر
        let optionsHTML = '<option value="">همه</option>';
        
        keywords.forEach(keyword => {
            optionsHTML += `<option value="${keyword.text}">${keyword.text}</option>`;
        });
        
        keywordFilter.innerHTML = optionsHTML;
        
    } catch (error) {
        console.error('Error loading keywords for filter:', error);
    }
}

// نمایش جزئیات توییت در مدال
async function showTweetDetails(tweetId) {
    try {
        currentTweetId = tweetId;
        
        // دریافت اطلاعات توییت
        const tweet = await api.get(`/api/v1/tweets/${tweetId}`);
        
        // پر کردن محتوای مدال
        const modalContent = document.getElementById('tweetDetailContent');
        
        // اطلاعات کاربر
        let userInfo = 'کاربر ناشناس';
        if (tweet.user) {
            userInfo = `
                <div class="d-flex align-items-center mb-3">
                    ${tweet.user.profile_image_url ? 
                      `<img src="${tweet.user.profile_image_url}" alt="Profile" class="rounded-circle me-2" width="48" height="48">` : 
                      `<div class="rounded-circle bg-light me-2" style="width: 48px; height: 48px; display: flex; align-items: center; justify-content: center;">
                        <i class="bi bi-person-fill text-secondary" style="font-size: 1.5rem;"></i>
                      </div>`
                    }
                    <div>
                        <div class="fw-bold">
                            ${tweet.user.display_name || tweet.user.username} 
                            ${tweet.user.verified ? '<i class="bi bi-patch-check-fill text-primary"></i>' : ''}
                        </div>
                        <div class="text-muted">@${tweet.user.username}</div>
                    </div>
                </div>
                <div class="mb-3">
                    <small class="text-muted">
                        <i class="bi bi-people-fill"></i> ${tweet.user.followers_count?.toLocaleString() || 0} فالوور
                    </small>
                    ${tweet.user.location ? `<small class="text-muted ms-2"><i class="bi bi-geo-alt-fill"></i> ${tweet.user.location}</small>` : ''}
                </div>
            `;
        }
        
        // تعیین کلاس برچسب احساسات
        let sentimentBadge = '<span class="badge bg-secondary">نامشخص</span>';
        if (tweet.sentiment_label === 'positive') {
            sentimentBadge = '<span class="badge sentiment-badge sentiment-positive">مثبت</span>';
        } else if (tweet.sentiment_label === 'negative') {
            sentimentBadge = '<span class="badge sentiment-badge sentiment-negative">منفی</span>';
        } else if (tweet.sentiment_label === 'neutral') {
            sentimentBadge = '<span class="badge sentiment-badge sentiment-neutral">خنثی</span>';
        } else if (tweet.sentiment_label === 'mixed') {
            sentimentBadge = '<span class="badge sentiment-badge sentiment-mixed">ترکیبی</span>';
        }
        
        // هشتگ‌ها و منشن‌ها
        let entities = '';
        if (tweet.entities) {
            const entitiesData = typeof tweet.entities === 'string' ? JSON.parse(tweet.entities) : tweet.entities;
            
            if (entitiesData.hashtags && entitiesData.hashtags.length > 0) {
                entities += '<div class="mb-2"><b>هشتگ‌ها:</b> ';
                entitiesData.hashtags.forEach(tag => {
                    entities += `<span class="badge bg-primary me-1">#${tag}</span>`;
                });
                entities += '</div>';
            }
            
            if (entitiesData.mentions && entitiesData.mentions.length > 0) {
                entities += '<div class="mb-2"><b>منشن‌ها:</b> ';
                entitiesData.mentions.forEach(mention => {
                    entities += `<span class="badge bg-secondary me-1">@${mention}</span>`;
                });
                entities += '</div>';
            }
        }
        
        // آماده‌سازی محتوای مدال
        modalContent.innerHTML = `
            ${userInfo}
            <div class="card mb-3">
                <div class="card-body">
                    <p class="card-text">${tweet.content}</p>
                    <div class="text-muted">
                        <small>${tweet.created_at ? new Date(tweet.created_at).toLocaleString('fa-IR') : '-'}</small>
                    </div>
                </div>
                <div class="card-footer bg-light">
                    <div class="d-flex justify-content-between">
                        <div>
                            <i class="bi bi-chat"></i> ${tweet.reply_count || 0}
                            <i class="bi bi-repeat ms-3"></i> ${tweet.retweet_count || 0}
                            <i class="bi bi-heart ms-3"></i> ${tweet.like_count || 0}
                        </div>
                        <div>
                            ${sentimentBadge}
                            ${tweet.sentiment_score ? 
                              `<span class="badge bg-light text-dark">${Math.round(tweet.sentiment_score * 100)}%</span>` : ''}
                        </div>
                    </div>
                </div>
            </div>
            ${entities}
            <div class="row">
                <div class="col-md-6">
                    <div class="mb-3">
                        <b>زبان:</b> ${tweet.language || 'نامشخص'}
                    </div>
                </div>
                <div class="col-md-6">
                    <div class="mb-3">
                        <b>امتیاز اهمیت:</b> ${tweet.importance_score?.toFixed(2) || 'نامشخص'}
                    </div>
                </div>
            </div>
            <div class="mb-3">
                <b>وضعیت:</b>
                ${tweet.is_processed ? '<span class="badge bg-success">پردازش شده</span>' : '<span class="badge bg-warning">پردازش نشده</span>'}
                ${tweet.is_analyzed ? '<span class="badge bg-success ms-1">تحلیل شده</span>' : '<span class="badge bg-warning ms-1">تحلیل نشده</span>'}
            </div>
        `;
        
        // آماده‌سازی دکمه تحلیل
        const analyzeTweetBtn = document.getElementById('analyzeTweetBtn');
        if (analyzeTweetBtn) {
            if (tweet.is_analyzed) {
                analyzeTweetBtn.disabled = true;
                analyzeTweetBtn.textContent = 'قبلاً تحلیل شده';
            } else {
                analyzeTweetBtn.disabled = false;
                analyzeTweetBtn.textContent = 'تحلیل توییت';
                
                // اضافه کردن event listener
                analyzeTweetBtn.onclick = function() {
                    analyzeTweet(currentTweetId);
                };
            }
        }
        
        // نمایش مدال
        const tweetDetailModal = new bootstrap.Modal(document.getElementById('tweetDetailModal'));
        tweetDetailModal.show();
        
    } catch (error) {
        console.error('Error fetching tweet details:', error);
        showErrorMessage('خطا در دریافت جزئیات توییت');
    }
}

// تحلیل توییت
async function analyzeTweet(tweetId) {
    try {
        // نمایش وضعیت در حال پردازش
        const analyzeTweetBtn = document.getElementById('analyzeTweetBtn');
        if (analyzeTweetBtn) {
            analyzeTweetBtn.disabled = true;
            analyzeTweetBtn.innerHTML = '<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> در حال تحلیل...';
        }
        
        // ارسال درخواست تحلیل
        const response = await api.post(`/api/v1/analysis/tweet/${tweetId}`, {});
        
        showSuccessMessage('توییت با موفقیت تحلیل شد');
        
        // بستن مدال اگر باز است
        const tweetDetailModal = bootstrap.Modal.getInstance(document.getElementById('tweetDetailModal'));
        if (tweetDetailModal) {
            tweetDetailModal.hide();
        }
        
        // بارگذاری مجدد لیست توییت‌ها
        await loadTweets();
        
    } catch (error) {
        console.error('Error analyzing tweet:', error);
        showErrorMessage('خطا در تحلیل توییت: ' + (error.message || 'خطای ناشناخته'));
        
        // فعال کردن مجدد دکمه
        const analyzeTweetBtn = document.getElementById('analyzeTweetBtn');
        if (analyzeTweetBtn) {
            analyzeTweetBtn.disabled = false;
            analyzeTweetBtn.textContent = 'تحلیل توییت';
        }
    }
}

// تنظیم گوش‌دهنده‌های رویداد
function setupTweetsListeners() {
    // فرم فیلتر توییت‌ها
    const tweetFilterForm = document.getElementById('tweetFilterForm');
    if (tweetFilterForm) {
        tweetFilterForm.addEventListener('submit', (event) => {
            event.preventDefault();
            currentPage = 1; // بازگشت به صفحه اول
            loadTweets();
        });
    }
    
    // دکمه بروزرسانی
    const refreshTweets = document.getElementById('refreshTweets');
    if (refreshTweets) {
        refreshTweets.addEventListener('click', () => {
            loadTweets();
        });
    }
    
    // بارگذاری کلیدواژه‌ها در فیلتر
    loadKeywordsFilter();
}

// صادرات توابع و متغیرهای مورد نیاز
window.loadTweets = loadTweets;
window.analyzeTweet = analyzeTweet;
window.setupTweetsListeners = setupTweetsListeners;