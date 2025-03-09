// alerts.js - مدیریت هشدارها

// متغیرهای داخلی ماژول
let currentAlertId = null; // برای استفاده در مدال جزئیات هشدار

// بارگذاری لیست هشدارها
async function loadAlerts(event) {
    if (event) event.preventDefault();
    
    try {
        // نمایش وضعیت در حال بارگذاری
        document.getElementById('alertsList').innerHTML = `
            <div class="text-center py-4">
                <div class="spinner-border text-primary" role="status">
                    <span class="visually-hidden">در حال بارگذاری...</span>
                </div>
            </div>
        `;
        
        // پارامترهای فیلتر
        const alertType = document.getElementById('alertType')?.value || '';
        const severity = document.getElementById('alertSeverity')?.value || '';
        const isRead = document.getElementById('isReadFilter')?.value || '';
        
        // ساخت URL با پارامترهای فیلتر
        let url = '/api/v1/waves/alerts?limit=20';
        if (alertType) url += `&alert_type=${alertType}`;
        if (severity) url += `&severity=${severity}`;
        if (isRead !== '') url += `&is_read=${isRead}`;
        
        // دریافت هشدارها از سرور
        const alerts = await api.get(url);
        
        // نمایش هشدارها
        displayAlerts(alerts);
        
        // بروزرسانی شمارنده هشدارها در داشبورد
        updateAlertsCounter(alerts.filter(alert => !alert.is_read).length);
        
    } catch (error) {
        console.error('Error loading alerts:', error);
        document.getElementById('alertsList').innerHTML = `
            <div class="alert alert-danger">
                خطا در بارگذاری هشدارها: ${error.message || 'خطای ناشناخته'}
            </div>
        `;
    }
}

// نمایش هشدارها در صفحه
function displayAlerts(alerts) {
    const alertsContainer = document.getElementById('alertsList');
    
    if (!alerts || alerts.length === 0) {
        alertsContainer.innerHTML = '<div class="text-center py-4 mt-3">هشداری یافت نشد</div>';
        return;
    }
    
    // ایجاد ردیف جدید برای نمایش کارت‌ها
    alertsContainer.innerHTML = '<div class="row" id="alertsRow"></div>';
    const alertsRow = document.getElementById('alertsRow');
    
    // ایجاد کارت برای هر هشدار
    alerts.forEach(alert => {
        const alertCard = document.createElement('div');
        alertCard.className = 'col-md-6 mb-3';
        
        // تعیین کلاس کارت براساس شدت
        let cardClass = 'alert-warning';
        if (alert.severity === 'high') {
            cardClass = 'alert-danger';
        } else if (alert.severity === 'low') {
            cardClass = 'alert-info';
        }
        
        // تعیین آیکون براساس نوع هشدار
        let alertIcon = '<i class="bi bi-exclamation-triangle"></i>';
        if (alert.alert_type === 'volume_wave') {
            alertIcon = '<i class="bi bi-graph-up"></i>';
        } else if (alert.alert_type === 'sentiment_shift') {
            alertIcon = '<i class="bi bi-emoji-expressionless"></i>';
        }
        
        // نمایش وضعیت خوانده شدن
        let readBadge = alert.is_read
            ? '<span class="badge bg-secondary ms-2">خوانده شده</span>'
            : '<span class="badge bg-success ms-2">جدید</span>';
        
        alertCard.innerHTML = `
            <div class="card alert-card ${cardClass}">
                <div class="card-header d-flex justify-content-between align-items-center">
                    <span>${alertIcon} ${alert.title} ${readBadge}</span>
                    <div>
                        <button class="btn btn-sm view-alert" data-id="${alert.id}">
                            <i class="bi bi-eye"></i>
                        </button>
                        ${!alert.is_read ? `
                            <button class="btn btn-sm mark-read-alert" data-id="${alert.id}">
                                <i class="bi bi-check2"></i>
                            </button>
                        ` : ''}
                    </div>
                </div>
                <div class="card-body">
                    <p class="card-text">${alert.message.substring(0, 150)}${alert.message.length > 150 ? '...' : ''}</p>
                    <p class="card-text"><small class="text-muted">
                        ${new Date(alert.created_at).toLocaleString('fa-IR')}
                    </small></p>
                </div>
            </div>
        `;
        
        alertsRow.appendChild(alertCard);
    });
    
    // اضافه کردن event listener به دکمه‌ها
    document.querySelectorAll('.view-alert').forEach(button => {
        button.addEventListener('click', function() {
            const alertId = this.getAttribute('data-id');
            showAlertDetails(alertId);
        });
    });
    
    document.querySelectorAll('.mark-read-alert').forEach(button => {
        button.addEventListener('click', function() {
            const alertId = this.getAttribute('data-id');
            markAlertAsRead(alertId);
        });
    });
}

// بروزرسانی شمارنده هشدارها در داشبورد
function updateAlertsCounter(count) {
    const activeAlertsValue = document.getElementById('activeAlertsValue');
    if (activeAlertsValue) {
        activeAlertsValue.textContent = count.toString();
    }
}

// نمایش جزئیات هشدار در مدال
async function showAlertDetails(alertId) {
    try {
        currentAlertId = alertId;
        
        // دریافت اطلاعات هشدار
        const alert = await api.get(`/api/v1/waves/alerts/${alertId}`);
        
        // تنظیم عنوان مدال
        document.getElementById('alertModalTitle').textContent = alert.title;
        
        // پر کردن محتوای مدال
        const modalContent = document.getElementById('alertDetailContent');
        
        // تعیین کلاس نوار براساس شدت
        let severityClass = 'bg-warning';
        if (alert.severity === 'high') {
            severityClass = 'bg-danger';
        } else if (alert.severity === 'low') {
            severityClass = 'bg-info';
        }
        
        // تعیین متن شدت
        let severityText = 'متوسط';
        if (alert.severity === 'high') {
            severityText = 'زیاد';
        } else if (alert.severity === 'low') {
            severityText = 'کم';
        }
        
        // تعیین نوع هشدار
        let alertTypeText = 'ناشناخته';
        if (alert.alert_type === 'volume_wave') {
            alertTypeText = 'موج حجمی';
        } else if (alert.alert_type === 'sentiment_shift') {
            alertTypeText = 'تغییر احساسات';
        }
        
        // استخراج داده‌های اضافی
        let additionalContent = '';
        if (alert.data) {
            const data = typeof alert.data === 'string' ? JSON.parse(alert.data) : alert.data;
            
            // نمایش تعداد توییت‌ها
            if (data.tweet_count) {
                additionalContent += `
                    <div class="mb-3">
                        <b>تعداد توییت‌ها:</b> ${data.tweet_count.toLocaleString()}
                    </div>
                `;
            }
            
            // نمایش بازه زمانی
            if (data.start_time && data.end_time) {
                const startTime = new Date(data.start_time).toLocaleString('fa-IR');
                const endTime = new Date(data.end_time).toLocaleString('fa-IR');
                additionalContent += `
                    <div class="mb-3">
                        <b>بازه زمانی:</b> از ${startTime} تا ${endTime}
                    </div>
                `;
            }
            
            // نمایش توزیع احساسات اگر وجود داشته باشد
            if (data.sentiment_distribution) {
                additionalContent += `
                    <div class="mb-3">
                        <b>توزیع احساسات:</b>
                        <div class="progress mt-2" style="height: 20px;">
                `;
                
                const sentiments = data.sentiment_distribution;
                if (sentiments.positive) {
                    const positivePercent = Math.round(sentiments.positive * 100);
                    additionalContent += `
                        <div class="progress-bar bg-success" role="progressbar" style="width: ${positivePercent}%" 
                         aria-valuenow="${positivePercent}" aria-valuemin="0" aria-valuemax="100" 
                         title="مثبت: ${positivePercent}%">
                         ${positivePercent}%
                        </div>
                    `;
                }
                
                if (sentiments.negative) {
                    const negativePercent = Math.round(sentiments.negative * 100);
                    additionalContent += `
                        <div class="progress-bar bg-danger" role="progressbar" style="width: ${negativePercent}%" 
                         aria-valuenow="${negativePercent}" aria-valuemin="0" aria-valuemax="100"
                         title="منفی: ${negativePercent}%">
                         ${negativePercent}%
                        </div>
                    `;
                }
                
                if (sentiments.neutral) {
                    const neutralPercent = Math.round(sentiments.neutral * 100);
                    additionalContent += `
                        <div class="progress-bar bg-secondary" role="progressbar" style="width: ${neutralPercent}%" 
                         aria-valuenow="${neutralPercent}" aria-valuemin="0" aria-valuemax="100"
                         title="خنثی: ${neutralPercent}%">
                         ${neutralPercent}%
                        </div>
                    `;
                }
                
                if (sentiments.mixed) {
                    const mixedPercent = Math.round(sentiments.mixed * 100);
                    additionalContent += `
                        <div class="progress-bar bg-warning" role="progressbar" style="width: ${mixedPercent}%" 
                         aria-valuenow="${mixedPercent}" aria-valuemin="0" aria-valuemax="100"
                         title="ترکیبی: ${mixedPercent}%">
                         ${mixedPercent}%
                        </div>
                    `;
                }
                
                additionalContent += `
                        </div>
                    </div>
                `;
            }
            
            // نمایش توییت‌های مهم
            if (data.top_tweets && data.top_tweets.length > 0) {
                additionalContent += `
                    <div class="mb-3">
                        <b>توییت‌های مهم مرتبط:</b>
                        <div class="list-group mt-2">
                `;
                
                data.top_tweets.slice(0, 3).forEach(tweet => {
                    additionalContent += `
                        <div class="list-group-item list-group-item-action flex-column align-items-start p-3">
                            <div class="d-flex justify-content-between">
                                <small class="text-muted">@${tweet.user_id}</small>
                                <small class="text-muted">اهمیت: ${tweet.importance_score?.toFixed(1) || 'نامشخص'}</small>
                            </div>
                            <p class="mb-1 mt-2">${tweet.content}</p>
                        </div>
                    `;
                });
                
                additionalContent += `
                        </div>
                    </div>
                `;
            }
        }
        
        // آماده‌سازی محتوای مدال
        modalContent.innerHTML = `
            <div class="alert ${severityClass}">
                <div class="d-flex justify-content-between">
                    <div>
                        <b>شدت:</b> ${severityText}
                    </div>
                    <div>
                        <b>نوع:</b> ${alertTypeText}
                    </div>
                </div>
            </div>
            
            <div class="mb-3">
                ${alert.message.replace(/\n/g, '<br>')}
            </div>
            
            ${additionalContent}
            
            <div class="mb-3">
                <b>زمان ایجاد:</b> ${new Date(alert.created_at).toLocaleString('fa-IR')}
            </div>
            
            <div class="d-flex justify-content-between">
                <div>
                    <b>وضعیت:</b> ${alert.is_read ? 
                      '<span class="badge bg-secondary">خوانده شده</span>' : 
                      '<span class="badge bg-success">جدید</span>'}
                </div>
                ${alert.related_tweet_id ? `
                    <button class="btn btn-sm btn-outline-primary" onclick="showRelatedTweet(${alert.related_tweet_id})">
                        نمایش توییت مرتبط
                    </button>
                ` : ''}
            </div>
        `;
        
        // تنظیم وضعیت دکمه علامت‌گذاری به عنوان خوانده شده
        const markAsReadBtn = document.getElementById('markAsReadBtn');
        if (markAsReadBtn) {
            if (alert.is_read) {
                markAsReadBtn.style.display = 'none';
            } else {
                markAsReadBtn.style.display = 'block';
                markAsReadBtn.onclick = function() {
                    markAlertAsRead(currentAlertId);
                };
            }
        }
        
        // نمایش مدال
        const alertDetailModal = new bootstrap.Modal(document.getElementById('alertDetailModal'));
        alertDetailModal.show();
        
    } catch (error) {
        console.error('Error fetching alert details:', error);
        showErrorMessage('خطا در دریافت جزئیات هشدار');
    }
}

// علامت‌گذاری هشدار به عنوان خوانده شده
async function markAlertAsRead(alertId) {
    try {
        // ارسال درخواست علامت‌گذاری
        await api.put(`/api/v1/waves/alerts/${alertId}/read`, {});
        
        // بستن مدال اگر باز است
        const alertDetailModal = bootstrap.Modal.getInstance(document.getElementById('alertDetailModal'));
        if (alertDetailModal) {
            alertDetailModal.hide();
        }
        
        // بارگذاری مجدد لیست هشدارها
        await loadAlerts();
        
        // بارگذاری مجدد داشبورد اگر در صفحه داشبورد هستیم
        if (window.currentPage === 'dashboard') {
            await loadDashboard();
        }
        
        showSuccessMessage('هشدار به عنوان خوانده شده علامت‌گذاری شد');
        
    } catch (error) {
        console.error('Error marking alert as read:', error);
        showErrorMessage('خطا در علامت‌گذاری هشدار: ' + (error.message || 'خطای ناشناخته'));
    }
}

// نمایش توییت مرتبط با هشدار
async function showRelatedTweet(tweetId) {
    try {
        // بستن مدال هشدار
        const alertDetailModal = bootstrap.Modal.getInstance(document.getElementById('alertDetailModal'));
        if (alertDetailModal) {
            alertDetailModal.hide();
        }
        
        // نمایش جزئیات توییت
        if (typeof window.showTweetDetails === 'function') {
            setTimeout(() => {
                window.showTweetDetails(tweetId);
            }, 500);
        } else {
            console.error('Function showTweetDetails not found');
            showErrorMessage('خطا در نمایش توییت مرتبط');
        }
        
    } catch (error) {
        console.error('Error showing related tweet:', error);
        showErrorMessage('خطا در نمایش توییت مرتبط');
    }
}

// بارگذاری هشدارهای داشبورد
async function loadLatestAlerts() {
    try {
        // دریافت هشدارهای خوانده نشده
        const alerts = await api.get('/api/v1/waves/alerts?limit=5&is_read=false');
        
        // بروزرسانی بخش هشدارها در داشبورد
        updateLatestAlerts(alerts);
        
    } catch (error) {
        console.error('Error loading latest alerts:', error);
        
        const alertsContainer = document.getElementById('latestAlerts');
        if (alertsContainer) {
            alertsContainer.innerHTML = '<p class="text-center text-danger">خطا در بارگذاری هشدارها</p>';
        }
    }
}

// بروزرسانی بخش هشدارها در داشبورد
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
        
        // اضافه کردن event listener برای نمایش جزئیات
        alertElement.style.cursor = 'pointer';
        alertElement.addEventListener('click', () => {
            showAlertDetails(alert.id);
        });
        
        alertsContainer.appendChild(alertElement);
    });
    
    // بروزرسانی تعداد هشدارهای فعال
    const activeAlertsValue = document.getElementById('activeAlertsValue');
    if (activeAlertsValue) {
        activeAlertsValue.textContent = alerts.length.toString();
    }
}

// تنظیم گوش‌دهنده‌های رویداد
function setupAlertsListeners() {
    // فرم فیلتر هشدارها
    const alertFilterForm = document.getElementById('alertFilterForm');
    if (alertFilterForm) {
        alertFilterForm.addEventListener('submit', (event) => {
            event.preventDefault();
            loadAlerts();
        });
    }
    
    // دکمه بروزرسانی
    const refreshAlerts = document.getElementById('refreshAlerts');
    if (refreshAlerts) {
        refreshAlerts.addEventListener('click', () => {
            loadAlerts();
        });
    }
    
    // دکمه مشاهده همه هشدارها در داشبورد
    const viewAllAlerts = document.getElementById('viewAllAlerts');
    if (viewAllAlerts) {
        viewAllAlerts.addEventListener('click', () => {
            showPage('alerts');
        });
    }
}

// صادرات توابع و متغیرهای مورد نیاز
window.loadAlerts = loadAlerts;
window.markAlertAsRead = markAlertAsRead;
window.showAlertDetails = showAlertDetails;
window.loadLatestAlerts = loadLatestAlerts;
window.updateLatestAlerts = updateLatestAlerts;
window.setupAlertsListeners = setupAlertsListeners;