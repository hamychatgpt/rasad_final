// keywords.js - مدیریت کلیدواژه‌ها

// بارگذاری کلیدواژه‌ها
async function loadKeywords(activeOnly = false) {
    try {
        const params = activeOnly ? '?active_only=true' : '';
        const response = await api.get(`/tweets/keywords${params}`);
        
        // اگر پاسخ آرایه نیست (مثلاً JSONResponse از بک‌اند)، آن را بررسی می‌کنیم
        if (response && !Array.isArray(response)) {
            // اگر پاسخ شامل آرایه‌ای در یک فیلد است
            if (response.data && Array.isArray(response.data)) {
                return response.data;
            }
        }
        
        return response || [];
    } catch (error) {
        console.error('Error loading keywords:', error);
        showErrorMessage('خطا در بارگذاری کلیدواژه‌ها');
        return [];
    }
}

// نمایش کلیدواژه‌های فعال در داشبورد
async function updateActiveKeywords() {
    const activeKeywordsElement = document.getElementById('activeKeywords');
    if (!activeKeywordsElement) return;
    
    try {
        const keywords = await loadKeywords(true);
        
        if (keywords.length === 0) {
            activeKeywordsElement.innerHTML = `
                <div class="alert alert-info">
                    <p class="mb-0">هنوز کلیدواژه‌ای تعریف نشده است. می‌توانید از بخش تنظیمات، کلیدواژه‌های مورد نظر خود را اضافه کنید.</p>
                </div>
                <a href="#" class="btn btn-primary btn-sm" id="goToSettings">
                    <i class="bi bi-gear"></i> رفتن به تنظیمات کلیدواژه‌ها
                </a>
            `;
            
            // افزودن عملکرد به دکمه
            document.getElementById('goToSettings')?.addEventListener('click', () => {
                showPage('settings');
            });
            
            return;
        }
        
        activeKeywordsElement.innerHTML = '';
        const badgeContainer = document.createElement('div');
        badgeContainer.className = 'd-flex flex-wrap gap-2';
        
        keywords.forEach(keyword => {
            const badge = document.createElement('span');
            // رنگ badge بر اساس اولویت
            const priorityClass = keyword.priority > 5 ? 'bg-danger' : keyword.priority > 3 ? 'bg-primary' : 'bg-info';
            badge.className = `badge ${priorityClass}`;
            badge.textContent = keyword.text;
            badgeContainer.appendChild(badge);
        });
        
        activeKeywordsElement.appendChild(badgeContainer);
        
    } catch (error) {
        activeKeywordsElement.innerHTML = '<p class="text-center text-danger">خطا در بارگذاری کلیدواژه‌ها</p>';
    }
}

// بارگذاری و نمایش کلیدواژه‌ها در صفحه تنظیمات
async function loadAndDisplayKeywords() {
    const keywordsListElement = document.getElementById('keywordsList');
    if (!keywordsListElement) return;
    
    try {
        const keywords = await loadKeywords();
        
        if (keywords.length === 0) {
            keywordsListElement.innerHTML = '<tr><td colspan="5" class="text-center">کلیدواژه‌ای یافت نشد</td></tr>';
            return;
        }
        
        keywordsListElement.innerHTML = '';
        
        keywords.forEach(keyword => {
            const row = document.createElement('tr');
            
            // وضعیت فعال یا غیرفعال
            const statusBadge = keyword.is_active
                ? '<span class="badge bg-success">فعال</span>'
                : '<span class="badge bg-secondary">غیرفعال</span>';
            
            row.innerHTML = `
                <td>${keyword.text}</td>
                <td>${statusBadge}</td>
                <td>${keyword.priority}</td>
                <td>${keyword.description || '-'}</td>
                <td>
                    <button class="btn btn-sm btn-outline-danger keyword-delete" data-id="${keyword.id}">
                        <i class="bi bi-trash"></i>
                    </button>
                    ${keyword.is_active ? 
                        `<button class="btn btn-sm btn-outline-warning ms-1 keyword-toggle" data-id="${keyword.id}" data-action="deactivate">
                            <i class="bi bi-eye-slash"></i>
                        </button>` : 
                        `<button class="btn btn-sm btn-outline-success ms-1 keyword-toggle" data-id="${keyword.id}" data-action="activate">
                            <i class="bi bi-eye"></i>
                        </button>`
                    }
                </td>
            `;
            
            keywordsListElement.appendChild(row);
        });
        
        // اضافه کردن گوش‌دهنده‌ها برای دکمه‌های حذف
        document.querySelectorAll('.keyword-delete').forEach(button => {
            button.addEventListener('click', function() {
                const keywordId = this.getAttribute('data-id');
                deleteKeyword(keywordId);
            });
        });
        
        // اضافه کردن گوش‌دهنده‌ها برای دکمه‌های تغییر وضعیت
        document.querySelectorAll('.keyword-toggle').forEach(button => {
            button.addEventListener('click', function() {
                const keywordId = this.getAttribute('data-id');
                const action = this.getAttribute('data-action');
                toggleKeywordStatus(keywordId, action === 'activate');
            });
        });
        
        // بارگذاری آمار کلیدواژه‌ها
        await loadKeywordStats();
        
    } catch (error) {
        keywordsListElement.innerHTML = '<tr><td colspan="5" class="text-center text-danger">خطا در بارگذاری کلیدواژه‌ها</td></tr>';
    }
}

// افزودن کلیدواژه جدید
async function addKeyword(keyword) {
    try {
        await api.post('/tweets/keywords', keyword);
        await loadAndDisplayKeywords();
        await updateActiveKeywords();
        showSuccessMessage('کلیدواژه با موفقیت افزوده شد');
    } catch (error) {
        console.error('Error adding keyword:', error);
        showErrorMessage('خطا در افزودن کلیدواژه');
    }
}

// حذف کلیدواژه
async function deleteKeyword(keywordId) {
    if (!confirm('آیا از حذف این کلیدواژه اطمینان دارید؟')) {
        return;
    }
    
    try {
        await api.delete(`/tweets/keywords/${keywordId}`);
        await loadAndDisplayKeywords();
        await updateActiveKeywords();
        showSuccessMessage('کلیدواژه با موفقیت حذف شد');
    } catch (error) {
        console.error('Error deleting keyword:', error);
        showErrorMessage('خطا در حذف کلیدواژه');
    }
}

// تغییر وضعیت کلیدواژه (فعال/غیرفعال)
async function toggleKeywordStatus(keywordId, activate) {
    try {
        // ارسال درخواست به‌روزرسانی
        await api.put(`/tweets/keywords/${keywordId}`, {
            is_active: activate,
            text: "", // این مقادیر در بک‌اند نادیده گرفته می‌شوند اگر تغییر نکنند
            priority: 0,
            description: ""
        });
        
        await loadAndDisplayKeywords();
        await updateActiveKeywords();
        
        const message = activate ? 'کلیدواژه با موفقیت فعال شد' : 'کلیدواژه با موفقیت غیرفعال شد';
        showSuccessMessage(message);
    } catch (error) {
        console.error('Error toggling keyword status:', error);
        showErrorMessage('خطا در تغییر وضعیت کلیدواژه');
    }
}

// استخراج خودکار کلیدواژه‌ها از متن
async function extractKeywords(text, maxKeywords = 10) {
    try {
        if (!text || text.trim() === '') {
            showErrorMessage('لطفاً متنی برای استخراج کلیدواژه وارد کنید');
            return [];
        }
        
        const response = await api.post('/tweets/keywords/extract', {
            text: text,
            max_keywords: maxKeywords
        });
        
        return response || [];
    } catch (error) {
        console.error('Error extracting keywords:', error);
        showErrorMessage('خطا در استخراج کلیدواژه‌ها');
        return [];
    }
}

// نمایش کلیدواژه‌های استخراج شده
async function displayExtractedKeywords(keywords) {
    const container = document.getElementById('extractedKeywords');
    if (!container) return;
    
    container.innerHTML = '';
    
    if (!keywords || keywords.length === 0) {
        container.innerHTML = '<p class="text-muted">هیچ کلیدواژه‌ای یافت نشد</p>';
        return;
    }
    
    const keywordsDiv = document.createElement('div');
    keywordsDiv.className = 'd-flex flex-wrap gap-2';
    
    keywords.forEach(keyword => {
        const checkbox = document.createElement('div');
        checkbox.className = 'form-check';
        checkbox.innerHTML = `
            <input class="form-check-input extracted-keyword-checkbox" type="checkbox" value="${keyword}" id="keyword-${keyword.replace(/\s+/g, '-')}">
            <label class="form-check-label" for="keyword-${keyword.replace(/\s+/g, '-')}">
                ${keyword}
            </label>
        `;
        keywordsDiv.appendChild(checkbox);
    });
    
    container.appendChild(keywordsDiv);
    
    // نمایش دکمه افزودن موارد انتخاب شده
    document.getElementById('addExtractedKeywords').style.display = 'block';
}

// افزودن کلیدواژه‌های استخراج شده انتخاب شده
async function addExtractedKeywords() {
    const selectedKeywords = [];
    document.querySelectorAll('.extracted-keyword-checkbox:checked').forEach(checkbox => {
        selectedKeywords.push(checkbox.value);
    });
    
    if (selectedKeywords.length === 0) {
        showErrorMessage('لطفاً حداقل یک کلیدواژه را انتخاب کنید');
        return;
    }
    
    let addedCount = 0;
    for (const keywordText of selectedKeywords) {
        try {
            await api.post('/tweets/keywords', {
                text: keywordText,
                is_active: true,
                priority: 1,
                description: 'استخراج شده به صورت خودکار'
            });
            addedCount++;
        } catch (error) {
            console.error(`Error adding extracted keyword "${keywordText}":`, error);
        }
    }
    
    if (addedCount > 0) {
        showSuccessMessage(`${addedCount} کلیدواژه با موفقیت افزوده شد`);
        await loadAndDisplayKeywords();
        await updateActiveKeywords();
        
        // پاک کردن انتخاب‌ها
        document.querySelectorAll('.extracted-keyword-checkbox').forEach(checkbox => {
            checkbox.checked = false;
        });
    } else {
        showErrorMessage('خطا در افزودن کلیدواژه‌ها');
    }
}

// بارگذاری آمار کلیدواژه‌ها
async function loadKeywordStats() {
    try {
        const statsContainer = document.getElementById('keywordStatsContainer');
        if (!statsContainer) return;
        
        const days = 7; // تعداد روزهای اخیر
        const stats = await api.get(`/tweets/keywords/stats?days=${days}`);
        
        if (!stats || stats.length === 0) {
            statsContainer.innerHTML = '<p class="text-center text-muted">آماری برای نمایش وجود ندارد</p>';
            return;
        }
        
        // مرتب‌سازی براساس تعداد توییت
        const sortedStats = stats.sort((a, b) => b.tweet_count - a.tweet_count).slice(0, 5); // فقط 5 مورد برتر
        
        // ایجاد نمودار
        const chartContainer = document.createElement('div');
        chartContainer.innerHTML = `
            <h5 class="mb-3">آمار کلیدواژه‌های برتر (${days} روز اخیر)</h5>
            <canvas id="keywordStatsChart" width="400" height="200"></canvas>
        `;
        
        statsContainer.innerHTML = '';
        statsContainer.appendChild(chartContainer);
        
        // ایجاد نمودار با Chart.js
        const ctx = document.getElementById('keywordStatsChart').getContext('2d');
        
        const labels = sortedStats.map(item => item.text);
        const data = sortedStats.map(item => item.tweet_count);
        
        new Chart(ctx, {
            type: 'bar',
            data: {
                labels: labels,
                datasets: [{
                    label: 'تعداد توییت',
                    data: data,
                    backgroundColor: [
                        'rgba(54, 162, 235, 0.6)',
                        'rgba(75, 192, 192, 0.6)',
                        'rgba(153, 102, 255, 0.6)',
                        'rgba(255, 159, 64, 0.6)',
                        'rgba(255, 205, 86, 0.6)'
                    ],
                    borderColor: [
                        'rgba(54, 162, 235, 1)',
                        'rgba(75, 192, 192, 1)',
                        'rgba(153, 102, 255, 1)',
                        'rgba(255, 159, 64, 1)',
                        'rgba(255, 205, 86, 1)'
                    ],
                    borderWidth: 1
                }]
            },
            options: {
                responsive: true,
                scales: {
                    y: {
                        beginAtZero: true
                    }
                }
            }
        });
        
    } catch (error) {
        console.error('Error loading keyword stats:', error);
        const statsContainer = document.getElementById('keywordStatsContainer');
        if (statsContainer) {
            statsContainer.innerHTML = '<p class="text-center text-danger">خطا در بارگذاری آمار کلیدواژه‌ها</p>';
        }
    }
}

// اتصال گوش‌دهنده‌های رویداد برای فرم افزودن کلیدواژه
function setupKeywordListeners() {
    const addKeywordForm = document.getElementById('addKeywordForm');
    if (addKeywordForm) {
        addKeywordForm.addEventListener('submit', async (event) => {
            event.preventDefault();
            
            const keywordText = document.getElementById('keywordText').value;
            const priority = parseInt(document.getElementById('keywordPriority').value);
            const description = document.getElementById('keywordDescription').value;
            
            if (!keywordText) {
                showErrorMessage('لطفاً متن کلیدواژه را وارد کنید');
                return;
            }
            
            const keyword = {
                text: keywordText,
                is_active: true,
                priority: priority,
                description: description
            };
            
            await addKeyword(keyword);
            
            // پاک کردن فرم
            document.getElementById('keywordText').value = '';
            document.getElementById('keywordPriority').value = '1';
            document.getElementById('keywordDescription').value = '';
        });
    }
    
    // دکمه مدیریت کلیدواژه‌ها در داشبورد
    const manageKeywordsButton = document.getElementById('manageKeywords');
    if (manageKeywordsButton) {
        manageKeywordsButton.addEventListener('click', () => {
            showPage('settings');
        });
    }
    
    // دکمه نمایش/مخفی کردن پنل استخراج کلیدواژه
    const keywordExtractorToggle = document.getElementById('keywordExtractorToggle');
    const keywordExtractorPanel = document.getElementById('keywordExtractorPanel');
    
    if (keywordExtractorToggle && keywordExtractorPanel) {
        keywordExtractorToggle.addEventListener('click', () => {
            if (keywordExtractorPanel.style.display === 'none') {
                keywordExtractorPanel.style.display = 'block';
                keywordExtractorToggle.textContent = 'مخفی کردن ابزار استخراج';
            } else {
                keywordExtractorPanel.style.display = 'none';
                keywordExtractorToggle.textContent = 'نمایش ابزار استخراج';
            }
        });
    }
    
    // دکمه استخراج کلیدواژه
    const extractKeywordsButton = document.getElementById('extractKeywords');
    if (extractKeywordsButton) {
        extractKeywordsButton.addEventListener('click', async () => {
            const text = document.getElementById('extractorText').value;
            const maxKeywords = parseInt(document.getElementById('maxKeywords').value);
            
            // ذخیره وضعیت اصلی دکمه
            const originalText = extractKeywordsButton.innerHTML;
            extractKeywordsButton.disabled = true;
            extractKeywordsButton.innerHTML = '<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> در حال استخراج...';
            
            try {
                const keywords = await extractKeywords(text, maxKeywords);
                document.getElementById('extractedKeywordsContainer').style.display = 'block';
                await displayExtractedKeywords(keywords);
            } finally {
                // بازگرداندن وضعیت دکمه
                extractKeywordsButton.disabled = false;
                extractKeywordsButton.innerHTML = originalText;
            }
        });
    }
    
    // دکمه افزودن کلیدواژه‌های استخراج شده
    const addExtractedKeywordsButton = document.getElementById('addExtractedKeywords');
    if (addExtractedKeywordsButton) {
        addExtractedKeywordsButton.addEventListener('click', addExtractedKeywords);
    }
    
    // اضافه کردن کانتینر آمار کلیدواژه‌ها اگر وجود ندارد
    const keywordsSettingsCard = document.querySelector('.card-header:contains("کلیدواژه‌ها")');
    if (keywordsSettingsCard) {
        const settingsCard = keywordsSettingsCard.closest('.card');
        if (settingsCard) {
            // بررسی وجود کانتینر آمار
            let statsContainer = document.getElementById('keywordStatsContainer');
            if (!statsContainer) {
                statsContainer = document.createElement('div');
                statsContainer.id = 'keywordStatsContainer';
                statsContainer.className = 'mt-4';
                
                // افزودن به انتهای کارت تنظیمات
                settingsCard.querySelector('.card-body').appendChild(statsContainer);
            }
        }
    }
}

// صادرات توابع و متغیرهای مورد نیاز
window.loadKeywords = loadKeywords;
window.addKeyword = addKeyword;
window.deleteKeyword = deleteKeyword;
window.setupKeywordListeners = setupKeywordListeners;
window.updateActiveKeywords = updateActiveKeywords;
window.loadAndDisplayKeywords = loadAndDisplayKeywords;
window.extractKeywords = extractKeywords;