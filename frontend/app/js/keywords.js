// keywords.js - مدیریت کلیدواژه‌ها

// بارگذاری کلیدواژه‌ها
async function loadKeywords(activeOnly = false) {
    try {
        const params = activeOnly ? '?active_only=true' : '';
        const keywords = await api.get(`/tweets/keywords${params}`);
        return keywords;
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
            badge.className = 'badge bg-primary';
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
}