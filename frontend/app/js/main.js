// main.js - نقطه ورود اصلی برنامه
// این ماژول مسئول مدیریت ارتباط بین تمام ماژول‌های دیگر است
// و ورود کاربر به برنامه را مدیریت می‌کند

// متغیرهای ماژول
let appState = {
    currentPage: 'dashboard', // صفحه فعلی
    isAuthenticated: false,   // وضعیت احراز هویت
    isLoading: false,         // آیا در حال بارگذاری است
    userData: null            // اطلاعات کاربر
};

// مدیریت توست‌ها (نمایش پیغام‌ها)
const toastManager = {
    container: null,
    
    // ایجاد کانتینر توست اگر وجود ندارد
    createContainer: function() {
        if (!this.container) {
            const container = document.createElement('div');
            container.id = 'toastContainer';
            container.className = 'toast-container position-fixed top-0 end-0 p-3';
            document.body.appendChild(container);
            this.container = container;
        }
        return this.container;
    },
    
    // نمایش پیغام خطا
    showError: function(message) {
        const container = this.createContainer();
        const toastId = 'toast-' + Date.now();
        
        const toastHTML = `
            <div id="${toastId}" class="toast align-items-center text-white bg-danger border-0" role="alert" aria-live="assertive" aria-atomic="true">
                <div class="d-flex">
                    <div class="toast-body">
                        <i class="bi bi-exclamation-triangle-fill me-2"></i>
                        ${message}
                    </div>
                    <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast" aria-label="Close"></button>
                </div>
            </div>
        `;
        
        container.insertAdjacentHTML('beforeend', toastHTML);
        
        const toastElement = document.getElementById(toastId);
        const toast = new bootstrap.Toast(toastElement);
        toast.show();
        
        toastElement.addEventListener('hidden.bs.toast', function () {
            this.remove();
        });
    },
    
    // نمایش پیغام موفقیت
    showSuccess: function(message) {
        const container = this.createContainer();
        const toastId = 'toast-' + Date.now();
        
        const toastHTML = `
            <div id="${toastId}" class="toast align-items-center text-white bg-success border-0" role="alert" aria-live="assertive" aria-atomic="true">
                <div class="d-flex">
                    <div class="toast-body">
                        <i class="bi bi-check-circle-fill me-2"></i>
                        ${message}
                    </div>
                    <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast" aria-label="Close"></button>
                </div>
            </div>
        `;
        
        container.insertAdjacentHTML('beforeend', toastHTML);
        
        const toastElement = document.getElementById(toastId);
        const toast = new bootstrap.Toast(toastElement);
        toast.show();
        
        toastElement.addEventListener('hidden.bs.toast', function () {
            this.remove();
        });
    },
    
    // نمایش پیغام اطلاع‌رسانی
    showInfo: function(message) {
        const container = this.createContainer();
        const toastId = 'toast-' + Date.now();
        
        const toastHTML = `
            <div id="${toastId}" class="toast align-items-center text-white bg-info border-0" role="alert" aria-live="assertive" aria-atomic="true">
                <div class="d-flex">
                    <div class="toast-body">
                        <i class="bi bi-info-circle-fill me-2"></i>
                        ${message}
                    </div>
                    <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast" aria-label="Close"></button>
                </div>
            </div>
        `;
        
        container.insertAdjacentHTML('beforeend', toastHTML);
        
        const toastElement = document.getElementById(toastId);
        const toast = new bootstrap.Toast(toastElement);
        toast.show();
        
        toastElement.addEventListener('hidden.bs.toast', function () {
            this.remove();
        });
    }
};

/**
 * نمایش صفحه مورد نظر
 * @param {string} page - نام صفحه
 */
function showPage(page) {
    // ذخیره صفحه فعلی
    appState.currentPage = page;

    // پنهان کردن همه صفحات
    document.getElementById('dashboardContent').style.display = 'none';
    document.getElementById('tweetsContent').style.display = 'none';
    document.getElementById('alertsContent').style.display = 'none';
    document.getElementById('settingsContent').style.display = 'none';
    document.getElementById('servicesContent').style.display = 'none';
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
        if (typeof loadDashboard === 'function') loadDashboard();
    } else if (page === 'tweets') {
        document.getElementById('tweetsContent').style.display = 'block';
        document.getElementById('tweetsLink').classList.add('active');
        if (typeof loadTweets === 'function') loadTweets();
    } else if (page === 'alerts') {
        document.getElementById('alertsContent').style.display = 'block';
        document.getElementById('alertsLink').classList.add('active');
        if (typeof loadAlerts === 'function') loadAlerts();
    } else if (page === 'settings') {
        document.getElementById('settingsContent').style.display = 'block';
        document.getElementById('settingsLink').classList.add('active');
        if (typeof loadAndDisplayKeywords === 'function') loadAndDisplayKeywords();
    } else if (page === 'services') {
        document.getElementById('servicesContent').style.display = 'block';
        document.getElementById('servicesLink').classList.add('active');
        if (typeof loadServices === 'function') loadServices();
    }
    
    // ذخیره صفحه فعلی در localStorage برای دفعات بعدی
    try {
        localStorage.setItem('lastPage', page);
    } catch (e) {
        console.error('Error saving last page to localStorage:', e);
    }
}

/**
 * مدیریت وضعیت بارگذاری بر سراسر برنامه
 * @param {boolean} isLoading - آیا در حال بارگذاری است
 */
function setLoadingState(isLoading) {
    appState.isLoading = isLoading;
    
    // نمایش/پنهان کردن نشانگر بارگذاری سراسری
    const globalLoader = document.getElementById('globalLoader');
    if (globalLoader) {
        globalLoader.style.display = isLoading ? 'block' : 'none';
    } else if (isLoading) {
        // ایجاد لودر در صورت عدم وجود
        const loader = document.createElement('div');
        loader.id = 'globalLoader';
        loader.className = 'position-fixed top-0 start-0 w-100 h-100 d-flex justify-content-center align-items-center';
        loader.style.backgroundColor = 'rgba(0,0,0,0.3)';
        loader.style.zIndex = '9999';
        loader.innerHTML = `
            <div class="spinner-border text-light" role="status">
                <span class="visually-hidden">در حال بارگذاری...</span>
            </div>
        `;
        document.body.appendChild(loader);
    }
    
    // غیرفعال/فعال کردن المان‌های تعاملی
    if (isLoading) {
        document.querySelectorAll('button, a, input, select, textarea').forEach(el => {
            if (!el.hasAttribute('data-original-disabled')) {
                el.setAttribute('data-original-disabled', el.disabled ? 'true' : 'false');
                el.disabled = true;
            }
        });
    } else {
        document.querySelectorAll('[data-original-disabled]').forEach(el => {
            const wasDisabled = el.getAttribute('data-original-disabled') === 'true';
            el.disabled = wasDisabled;
            el.removeAttribute('data-original-disabled');
        });
    }
}

/**
 * تنظیم گوش‌دهنده‌های رویداد اصلی
 */
function setupMainListeners() {
    // گوش‌دهنده‌های رویداد برای منوی ناوبری
    document.getElementById('dashboardLink').addEventListener('click', () => showPage('dashboard'));
    document.getElementById('tweetsLink').addEventListener('click', () => showPage('tweets'));
    document.getElementById('alertsLink').addEventListener('click', () => showPage('alerts'));
    document.getElementById('settingsLink').addEventListener('click', () => showPage('settings'));
    document.getElementById('servicesLink').addEventListener('click', () => showPage('services'));
    
    // گوش‌دهنده برای لینک کاربر (ورود/خروج)
    document.getElementById('userInfoLink').addEventListener('click', function(e) {
        e.preventDefault();
        
        // اگر کاربر وارد شده است، خروج انجام شود
        if (appState.isAuthenticated) {
            if (confirm('آیا می‌خواهید از سیستم خارج شوید؟')) {
                logout();
            }
        } else {
            // اگر کاربر وارد نشده است، صفحه ورود نمایش داده شود
            showPage('login');
        }
    });
    
    // گوش‌دهنده برای زمانی که کلید F5 فشرده می‌شود یا صفحه refresh می‌شود
    window.addEventListener('beforeunload', function() {
        // ذخیره وضعیت فعلی صفحه
        try {
            localStorage.setItem('lastPage', appState.currentPage);
        } catch (e) {
            console.error('Error saving state before unload:', e);
        }
    });
}

/**
 * بررسی وضعیت احراز هویت و بارگذاری صفحه مناسب
 */
async function initializeApp() {
    try {
        // نمایش وضعیت بارگذاری
        setLoadingState(true);
        
        // ایجاد کانتینر توست
        toastManager.createContainer();
        
        // گوش‌دهنده‌های رویداد اصلی
        setupMainListeners();
        
        // بررسی وضعیت احراز هویت
        const authenticated = await checkAuthStatus();
        appState.isAuthenticated = authenticated;
        
        // راه‌اندازی سایر ماژول‌ها
        if (typeof setupAuthListeners === 'function') setupAuthListeners();
        if (typeof setupDashboardListeners === 'function') setupDashboardListeners();
        if (typeof setupServiceListeners === 'function') setupServiceListeners();
        if (typeof setupKeywordListeners === 'function') setupKeywordListeners();
        if (typeof setupTweetsListeners === 'function') setupTweetsListeners();
        if (typeof setupAlertsListeners === 'function') setupAlertsListeners();
        
        // نمایش صفحه مناسب
        if (authenticated) {
            // بررسی آخرین صفحه‌ای که کاربر بازدید کرده
            try {
                const lastPage = localStorage.getItem('lastPage');
                if (lastPage && lastPage !== 'login') {
                    showPage(lastPage);
                } else {
                    showPage('dashboard');
                }
            } catch (e) {
                console.error('Error reading last page from localStorage:', e);
                showPage('dashboard');
            }
        } else {
            showPage('login');
        }
    } catch (error) {
        console.error('Error initializing app:', error);
        toastManager.showError('خطا در راه‌اندازی برنامه: ' + error.message);
        showPage('login');
    } finally {
        // پایان وضعیت بارگذاری
        setLoadingState(false);
    }
}

// راه‌اندازی برنامه بعد از بارگذاری کامل DOM
document.addEventListener('DOMContentLoaded', initializeApp);

// صادرات توابع و متغیرها به window برای دسترسی سایر ماژول‌ها
window.showPage = showPage;
window.showErrorMessage = toastManager.showError.bind(toastManager);
window.showSuccessMessage = toastManager.showSuccess.bind(toastManager);
window.showInfoMessage = toastManager.showInfo.bind(toastManager);
window.setLoadingState = setLoadingState;
window.getAppState = () => ({ ...appState }); // ارائه یک کپی از وضعیت برنامه