// debug.js - ابزارهای دیباگ سیستم

// متغیر برای تنظیم حالت توسعه
const DEV_MODE = true; // تغییر به false در محیط تولید

// بارگذاری وضعیت دیباگ سیستم
async function loadDebugStatus() {
    try {
        const debugStatusElement = document.getElementById('debugStatus');
        if (!debugStatusElement) return;
        
        // نمایش وضعیت بارگذاری
        debugStatusElement.innerHTML = `
            <div class="text-center">
                <div class="spinner-border text-primary" role="status">
                    <span class="visually-hidden">در حال بارگذاری...</span>
                </div>
            </div>
        `;
        
        // دریافت اطلاعات از API
        const debugInfo = await api.get('/tweets/debug/keywords');
        
        // نمایش نتایج
        displayDebugInfo(debugInfo);
        
    } catch (error) {
        console.error('Error loading debug status:', error);
        const debugStatusElement = document.getElementById('debugStatus');
        if (debugStatusElement) {
            debugStatusElement.innerHTML = `
                <div class="alert alert-danger">
                    <i class="bi bi-exclamation-triangle-fill"></i> خطا در بارگذاری اطلاعات دیباگ: ${error.message}
                </div>
            `;
        }
    }
}

// نمایش اطلاعات دیباگ
function displayDebugInfo(debugInfo) {
    const debugStatusElement = document.getElementById('debugStatus');
    if (!debugStatusElement) return;
    
    let html = '';
    
    // اطلاعات عمومی
    html += `
        <div class="card mb-3">
            <div class="card-header">
                <h5 class="mb-0">
                    <i class="bi bi-info-circle"></i> اطلاعات عمومی
                </h5>
            </div>
            <div class="card-body">
                <div class="mb-2">
                    <strong>وضعیت:</strong> 
                    <span class="badge ${debugInfo.status === 'ok' ? 'bg-success' : 'bg-danger'}">${debugInfo.status === 'ok' ? 'سالم' : 'خطا'}</span>
                </div>
                <div class="mb-2">
                    <strong>زمان:</strong> ${new Date(debugInfo.timestamp).toLocaleString('fa-IR')}
                </div>
            </div>
        </div>
    `;
    
    // اطلاعات جداول دیتابیس
    if (debugInfo.tables) {
        html += `
            <div class="card mb-3">
                <div class="card-header">
                    <h5 class="mb-0">
                        <i class="bi bi-table"></i> وضعیت جداول دیتابیس
                    </h5>
                </div>
                <div class="card-body">
                    <div class="mb-2">
                        <strong>وجود جدول کلیدواژه‌ها:</strong> 
                        <span class="badge ${debugInfo.tables.keywords_exists ? 'bg-success' : 'bg-danger'}">
                            ${debugInfo.tables.keywords_exists ? 'بله' : 'خیر'}
                        </span>
                    </div>
                    <div class="mb-2">
                        <strong>تعداد کلیدواژه‌ها:</strong> ${debugInfo.tables.keywords_count || 0}
                    </div>
                    <div class="mb-2">
                        <strong>لیست جداول موجود:</strong> 
                        <ul class="list-group">
                            ${debugInfo.tables.all_tables.map(table => `
                                <li class="list-group-item">${table}</li>
                            `).join('')}
                        </ul>
                    </div>
                </div>
            </div>
        `;
    }
    
    // کلیدواژه‌های موجود
    if (debugInfo.keywords && debugInfo.keywords.length > 0) {
        html += `
            <div class="card mb-3">
                <div class="card-header">
                    <h5 class="mb-0">
                        <i class="bi bi-key"></i> کلیدواژه‌های موجود
                    </h5>
                </div>
                <div class="card-body">
                    <div class="table-responsive">
                        <table class="table table-sm table-hover">
                            <thead>
                                <tr>
                                    <th>ID</th>
                                    <th>متن</th>
                                    <th>وضعیت</th>
                                    <th>اولویت</th>
                                    <th>توضیحات</th>
                                </tr>
                            </thead>
                            <tbody>
                                ${debugInfo.keywords.map(keyword => `
                                    <tr>
                                        <td>${keyword.id}</td>
                                        <td>${keyword.text}</td>
                                        <td>
                                            <span class="badge ${keyword.is_active ? 'bg-success' : 'bg-secondary'}">
                                                ${keyword.is_active ? 'فعال' : 'غیرفعال'}
                                            </span>
                                        </td>
                                        <td>${keyword.priority}</td>
                                        <td>${keyword.description || '-'}</td>
                                    </tr>
                                `).join('')}
                            </tbody>
                        </table>
                    </div>
                </div>
            </div>
        `;
    }
    
    // خطاها
    if (debugInfo.errors && debugInfo.errors.length > 0) {
        html += `
            <div class="card mb-3 border-danger">
                <div class="card-header bg-danger text-white">
                    <h5 class="mb-0">
                        <i class="bi bi-exclamation-triangle-fill"></i> خطاها
                    </h5>
                </div>
                <div class="card-body">
                    <ul class="list-group">
                        ${debugInfo.errors.map(error => `
                            <li class="list-group-item list-group-item-danger">${error}</li>
                        `).join('')}
                    </ul>
                </div>
            </div>
        `;
    }
    
    // بررسی عملکرد API‌ها
    html += `
        <div class="card mb-3">
            <div class="card-header">
                <h5 class="mb-0">
                    <i class="bi bi-eyedropper"></i> تست عملکرد API‌ها
                </h5>
            </div>
            <div class="card-body">
                <div class="d-flex flex-wrap gap-2 mb-3">
                    <button class="btn btn-primary btn-sm test-api" data-endpoint="/tweets/count" data-method="get">
                        <i class="bi bi-chat-dots"></i> تست API توییت‌ها
                    </button>
                    <button class="btn btn-info btn-sm test-api" data-endpoint="/waves/alerts?limit=1" data-method="get">
                        <i class="bi bi-bell"></i> تست API هشدارها
                    </button>
                    <button class="btn btn-success btn-sm test-api" data-endpoint="/settings/" data-method="get">
                        <i class="bi bi-gear"></i> تست API تنظیمات
                    </button>
                </div>
                <div id="apiTestResult"></div>
            </div>
        </div>
    `;
    
    // اضافه کردن بخش اطلاعات مرورگر و سیستم‌عامل
    html += `
        <div class="card mb-3">
            <div class="card-header">
                <h5 class="mb-0">
                    <i class="bi bi-laptop"></i> اطلاعات مرورگر و سیستم‌عامل
                </h5>
            </div>
            <div class="card-body">
                <div class="mb-2">
                    <strong>مرورگر:</strong> ${navigator.userAgent}
                </div>
                <div class="mb-2">
                    <strong>زبان:</strong> ${navigator.language}
                </div>
                <div class="mb-2">
                    <strong>پلتفرم:</strong> ${navigator.platform}
                </div>
                <div class="mb-2">
                    <strong>تعداد هسته‌های پردازنده:</strong> ${navigator.hardwareConcurrency || 'نامشخص'}
                </div>
                <div class="mb-2">
                    <strong>حافظه:</strong> ${navigator.deviceMemory ? navigator.deviceMemory + ' GB' : 'نامشخص'}
                </div>
                <div class="mb-2">
                    <strong>اتصال اینترنت:</strong> 
                    <span class="badge ${navigator.onLine ? 'bg-success' : 'bg-danger'}">
                        ${navigator.onLine ? 'متصل' : 'قطع'}
                    </span>
                </div>
            </div>
        </div>
    `;
    
    debugStatusElement.innerHTML = html;
    
    // اضافه کردن گوش‌دهنده‌ها برای دکمه‌های تست API
    document.querySelectorAll('.test-api').forEach(button => {
        button.addEventListener('click', async () => {
            const endpoint = button.getAttribute('data-endpoint');
            const method = button.getAttribute('data-method') || 'get';
            await testAPI(endpoint, method);
        });
    });
}

// تست API
async function testAPI(endpoint, method = 'get') {
    const resultElement = document.getElementById('apiTestResult');
    if (!resultElement) return;
    
    try {
        // نمایش وضعیت بارگذاری
        resultElement.innerHTML = `
            <div class="alert alert-info">
                <div class="d-flex align-items-center">
                    <div class="spinner-border spinner-border-sm me-2" role="status">
                        <span class="visually-hidden">در حال تست...</span>
                    </div>
                    <div>
                        در حال تست API: ${endpoint}
                    </div>
                </div>
            </div>
        `;
        
        // شروع زمان‌سنجی
        const startTime = performance.now();
        
        // انجام درخواست
        let response;
        if (method === 'get') {
            response = await api.get(endpoint);
        } else if (method === 'post') {
            response = await api.post(endpoint, {});
        }
        
        // محاسبه زمان اجرا
        const duration = (performance.now() - startTime).toFixed(2);
        
        // نمایش نتیجه
        resultElement.innerHTML = `
            <div class="alert alert-success">
                <h5>
                    <i class="bi bi-check-circle-fill"></i> API با موفقیت تست شد
                </h5>
                <div class="mb-2">
                    <strong>مسیر:</strong> ${endpoint}
                </div>
                <div class="mb-2">
                    <strong>روش:</strong> ${method.toUpperCase()}
                </div>
                <div class="mb-2">
                    <strong>زمان اجرا:</strong> ${duration} میلی‌ثانیه
                </div>
                <div class="mb-2">
                    <strong>پاسخ:</strong>
                    <pre class="bg-light p-2 mt-2 rounded" style="max-height: 200px; overflow: auto; direction: ltr;">${JSON.stringify(response, null, 2)}</pre>
                </div>
            </div>
        `;
    } catch (error) {
        // نمایش خطا
        resultElement.innerHTML = `
            <div class="alert alert-danger">
                <h5>
                    <i class="bi bi-exclamation-triangle-fill"></i> خطا در تست API
                </h5>
                <div class="mb-2">
                    <strong>مسیر:</strong> ${endpoint}
                </div>
                <div class="mb-2">
                    <strong>روش:</strong> ${method.toUpperCase()}
                </div>
                <div class="mb-2">
                    <strong>پیام خطا:</strong> ${error.message}
                </div>
                <div class="mb-2">
                    <strong>جزئیات:</strong>
                    <pre class="bg-light p-2 mt-2 rounded" style="max-height: 200px; overflow: auto; direction: ltr;">${JSON.stringify(error, null, 2)}</pre>
                </div>
            </div>
        `;
    }
}

// ارسال درخواست HTTP به یک مسیر
async function makeHttpRequest(url, method = 'GET', data = null) {
    try {
        const options = {
            method: method,
            headers: {
                'Accept': 'application/json'
            }
        };
        
        if (data && method !== 'GET') {
            options.headers['Content-Type'] = 'application/json';
            options.body = JSON.stringify(data);
        }
        
        const response = await fetch(url, options);
        return await response.json();
    } catch (error) {
        console.error(`Error making ${method} request to ${url}:`, error);
        throw error;
    }
}

// افزودن پنل دیباگ به بخش تنظیمات
function addDebugPanelToSettings() {
    // پنل دیباگ فقط در حالت توسعه فعال باشد
    if (!DEV_MODE) return;
    
    const settingsContent = document.getElementById('settingsContent');
    if (!settingsContent) return;
    
    // بررسی وجود پنل دیباگ
    if (document.getElementById('debugPanel')) return;
    
    // ایجاد پنل دیباگ
    const debugPanel = document.createElement('div');
    debugPanel.id = 'debugPanel';
    debugPanel.innerHTML = `
        <div class="card mb-4">
            <div class="card-header">
                <div class="d-flex justify-content-between align-items-center">
                    <h5 class="mb-0">
                        <i class="bi bi-bug"></i> ابزارهای دیباگ
                        <span class="badge bg-warning ms-2">حالت توسعه</span>
                    </h5>
                    <button class="btn btn-sm btn-outline-primary" id="refreshDebugStatus">
                        <i class="bi bi-arrow-clockwise"></i> بروزرسانی
                    </button>
                </div>
            </div>
            <div class="card-body">
                <div class="alert alert-warning">
                    <i class="bi bi-exclamation-triangle-fill"></i> توجه: این بخش فقط در حالت توسعه نمایش داده می‌شود و برای عیب‌یابی سیستم استفاده می‌شود.
                </div>
                
                <div id="debugStatus">
                    <!-- اطلاعات دیباگ اینجا نمایش داده می‌شود -->
                </div>
            </div>
        </div>
    `;
    
    // افزودن به انتهای بخش تنظیمات
    settingsContent.appendChild(debugPanel);
    
    // افزودن گوش‌دهنده به دکمه بروزرسانی
    document.getElementById('refreshDebugStatus').addEventListener('click', loadDebugStatus);
    
    // بارگذاری اولیه وضعیت دیباگ
    loadDebugStatus();
}

// اضافه کردن آیکون دیباگ به نوار ناوبری
function addDebugMenuToNavbar() {
    // منو دیباگ فقط در حالت توسعه فعال باشد
    if (!DEV_MODE) return;
    
    const navbarNav = document.querySelector('#navbarNav .navbar-nav');
    if (!navbarNav) return;
    
    // بررسی وجود منو دیباگ
    if (document.getElementById('debugLink')) return;
    
    // ایجاد آیتم منو دیباگ
    const debugMenuItem = document.createElement('li');
    debugMenuItem.className = 'nav-item';
    debugMenuItem.innerHTML = `
        <a class="nav-link" href="#" id="debugLink">
            <i class="bi bi-bug"></i> دیباگ
            <span class="badge bg-warning">توسعه</span>
        </a>
    `;
    
    // افزودن به منو
    navbarNav.appendChild(debugMenuItem);
    
    // افزودن گوش‌دهنده به منو دیباگ
    document.getElementById('debugLink').addEventListener('click', () => {
        showPage('settings');
        // اطمینان از وجود پنل دیباگ
        addDebugPanelToSettings();
        // اسکرول به پنل دیباگ
        document.getElementById('debugPanel').scrollIntoView({ behavior: 'smooth' });
    });
}

// راه‌اندازی بخش دیباگ
function setupDebug() {
    if (DEV_MODE) {
        // افزودن پنل دیباگ به بخش تنظیمات در صورت فعال بودن صفحه تنظیمات
        if (document.getElementById('settingsContent') && 
            document.getElementById('settingsContent').style.display !== 'none') {
            addDebugPanelToSettings();
        }
        
        // افزودن آیکون دیباگ به نوار ناوبری
        addDebugMenuToNavbar();
        
        // افزودن هشدار حالت توسعه به بالای صفحه
        addDevModeWarning();
    }
}

// افزودن هشدار حالت توسعه
function addDevModeWarning() {
    if (!DEV_MODE) return;
    
    // بررسی وجود هشدار
    if (document.getElementById('devModeWarning')) return;
    
    // ایجاد نوار هشدار
    const warning = document.createElement('div');
    warning.id = 'devModeWarning';
    warning.className = 'alert alert-warning text-center py-1 mb-0';
    warning.style.position = 'sticky';
    warning.style.top = '0';
    warning.style.zIndex = '1000';
    warning.innerHTML = `
        <i class="bi bi-exclamation-triangle-fill"></i>
        <strong>حالت توسعه فعال است.</strong> احراز هویت غیرفعال شده و API‌ها در حالت دیباگ هستند.
        <button class="btn btn-sm btn-outline-dark ms-2" id="hideDevWarning">پنهان کردن</button>
    `;
    
    // افزودن به ابتدای بدنه
    document.body.insertBefore(warning, document.body.firstChild);
    
    // افزودن گوش‌دهنده به دکمه پنهان کردن
    document.getElementById('hideDevWarning').addEventListener('click', () => {
        warning.style.display = 'none';
    });
}

// تنظیم گوش‌دهنده‌های رویداد
document.addEventListener('DOMContentLoaded', setupDebug);

// صادرات توابع عمومی
window.loadDebugStatus = loadDebugStatus;
window.testAPI = testAPI;
window.setupDebug = setupDebug;