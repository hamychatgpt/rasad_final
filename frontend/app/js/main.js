// main.js - نقطه ورود اصلی برنامه
// این ماژول مسئول مدیریت ارتباط بین تمام ماژول‌های دیگر است
// و ورود کاربر به برنامه را مدیریت می‌کند

// متغیرهای ماژول
let appState = {
    currentPage: 'dashboard', // صفحه فعلی
    isAuthenticated: false,   // وضعیت احراز هویت
    isLoading: false,         // آیا در حال بارگذاری است
    userData: null,           // اطلاعات کاربر
    isDevelopment: true       // آیا در حالت توسعه هستیم؟
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
        // اگر در حالت توسعه هستیم، پنل دیباگ را نمایش می‌دهیم
        if (appState.isDevelopment && typeof setupDebug === 'function') {
            setupDebug();
        }
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
                if (typeof logout === 'function') {
                    logout();
                } else {
                    // اگر تابع logout تعریف نشده، عملکرد پیش‌فرض را اجرا می‌کنیم
                    localStorage.removeItem('authToken');
                    appState.isAuthenticated = false;
                    showPage('login');
                    toastManager.showInfo('خروج از سیستم انجام شد');
                }
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

    // اضافه کردن دکمه دیباگ در حالت توسعه
    if (appState.isDevelopment) {
        addDevModeFeatures();
    }
}

/**
 * اضافه کردن ویژگی‌های حالت توسعه
 */
function addDevModeFeatures() {
    // افزودن دکمه توکن موقت
    const navbarNav = document.querySelector('#navbarNav .navbar-nav.ms-auto');
    if (navbarNav) {
        const devItem = document.createElement('li');
        devItem.className = 'nav-item';
        devItem.innerHTML = `
            <a class="nav-link" href="#" id="devModeLink">
                <span class="badge bg-warning">حالت توسعه</span>
            </a>
        `;
        navbarNav.appendChild(devItem);
        
        // افزودن گوش‌دهنده به دکمه
        document.getElementById('devModeLink').addEventListener('click', () => {
            // نمایش منوی کشویی ابزارهای توسعه
            showDevTools();
        });
    }
}

/**
 * نمایش ابزارهای توسعه
 */
function showDevTools() {
    // بررسی وجود منوی ابزارهای توسعه
    let devToolsMenu = document.getElementById('devToolsMenu');
    
    if (devToolsMenu) {
        // اگر قبلاً ایجاد شده، آن را نمایش/مخفی می‌کنیم
        devToolsMenu.style.display = devToolsMenu.style.display === 'none' ? 'block' : 'none';
        return;
    }
    
    // ایجاد منوی ابزارهای توسعه
    devToolsMenu = document.createElement('div');
    devToolsMenu.id = 'devToolsMenu';
    devToolsMenu.className = 'card position-absolute';
    devToolsMenu.style.top = '50px';
    devToolsMenu.style.right = '10px';
    devToolsMenu.style.zIndex = '1000';
    devToolsMenu.style.minWidth = '250px';
    
    devToolsMenu.innerHTML = `
        <div class="card-header bg-warning">
            <h5 class="mb-0">ابزارهای توسعه</h5>
        </div>
        <div class="card-body">
            <div class="d-grid gap-2">
                <button class="btn btn-outline-primary btn-sm" id="devGenerateToken">
                    <i class="bi bi-key"></i> تولید توکن موقت
                </button>
                <button class="btn btn-outline-info btn-sm" id="devDebugPanel">
                    <i class="bi bi-bug"></i> پنل دیباگ
                </button>
                <button class="btn btn-outline-danger btn-sm" id="devClearStorage">
                    <i class="bi bi-trash"></i> پاک کردن ذخیره‌سازی
                </button>
            </div>
        </div>
    `;
    
    // افزودن به بدنه
    document.body.appendChild(devToolsMenu);
    
    // افزودن گوش‌دهنده‌ها
    document.getElementById('devGenerateToken').addEventListener('click', () => {
        const token = "dev-token-" + Date.now();
        if (typeof api !== 'undefined' && api.setToken) {
            api.setToken(token);
            toastManager.showSuccess(`توکن موقت ایجاد شد: ${token}`);
        } else {
            localStorage.setItem('authToken', token);
            toastManager.showSuccess(`توکن موقت ایجاد شد: ${token} (API در دسترس نیست)`);
        }
    });
    
    document.getElementById('devDebugPanel').addEventListener('click', () => {
        showPage('settings');
        // اطمینان از وجود پنل دیباگ
        if (typeof setupDebug === 'function') {
            setupDebug();
        } else {
            toastManager.showInfo('ماژول دیباگ در دسترس نیست');
        }
        // اسکرول به پنل دیباگ
        const debugPanel = document.getElementById('debugPanel');
        if (debugPanel) {
            debugPanel.scrollIntoView({ behavior: 'smooth' });
        }
    });
    
    document.getElementById('devClearStorage').addEventListener('click', () => {
        if (confirm('آیا از پاک کردن تمام ذخیره‌سازی محلی اطمینان دارید؟')) {
            localStorage.clear();
            toastManager.showSuccess('ذخیره‌سازی محلی پاک شد');
        }
    });
    
    // بستن منو با کلیک خارج از آن
    document.addEventListener('click', function(event) {
        if (devToolsMenu && !devToolsMenu.contains(event.target) && 
            event.target.id !== 'devModeLink' && !event.target.closest('#devModeLink')) {
            devToolsMenu.style.display = 'none';
        }
    });
}

/**
 * بررسی وضعیت احراز هویت داخلی
 * @returns {boolean} آیا کاربر احراز هویت شده است
 */
function internalCheckAuthStatus() {
    // در حالت توسعه، همیشه احراز هویت شده فرض می‌شود
    if (appState.isDevelopment) {
        const token = localStorage.getItem('authToken');
        if (!token) {
            localStorage.setItem('authToken', 'dev-mode-token');
        }
        
        // تنظیم نام کاربر در منو
        const userDisplayName = document.getElementById('userDisplayName');
        if (userDisplayName) {
            userDisplayName.textContent = 'کاربر توسعه';
        }
        
        return true;
    }
    
    // بررسی وجود توکن
    const token = localStorage.getItem('authToken');
    return !!token;
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
        let authenticated = false;
        
        // تلاش برای استفاده از تابع checkAuthStatus از ماژول auth.js
        if (typeof window.checkAuthStatus === 'function') {
            try {
                authenticated = await window.checkAuthStatus();
            } catch (authError) {
                console.error('Error using external checkAuthStatus:', authError);
                // استفاده از بررسی داخلی به عنوان پشتیبان
                authenticated = internalCheckAuthStatus();
            }
        } else {
            // اگر تابع خارجی موجود نیست، از بررسی داخلی استفاده می‌کنیم
            console.warn('External checkAuthStatus function not found, using internal check');
            authenticated = internalCheckAuthStatus();
        }
        
        appState.isAuthenticated = authenticated;
        
        // بارگذاری اسکریپت‌های اضافی
        await loadExtraScripts();
        
        // راه‌اندازی سایر ماژول‌ها با بررسی وجود توابع
        if (typeof setupAuthListeners === 'function') setupAuthListeners();
        if (typeof setupDashboardListeners === 'function') setupDashboardListeners();
        if (typeof setupServiceListeners === 'function') setupServiceListeners();
        if (typeof setupKeywordListeners === 'function') setupKeywordListeners();
        if (typeof setupTweetsListeners === 'function') setupTweetsListeners();
        if (typeof setupAlertsListeners === 'function') setupAlertsListeners();
        if (appState.isDevelopment && typeof setupDebug === 'function') setupDebug();
        
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
            // در حالت توسعه، به جای صفحه ورود، داشبورد را نمایش می‌دهیم
            if (appState.isDevelopment) {
                // ایجاد توکن موقت
                if (typeof api !== 'undefined' && api.setToken) {
                    api.setToken("dev-mode-token");
                } else {
                    localStorage.setItem('authToken', 'dev-mode-token');
                }
                appState.isAuthenticated = true;
                showPage('dashboard');
                toastManager.showInfo('حالت توسعه فعال است. احراز هویت غیرفعال شده است.');
            } else {
                showPage('login');
            }
        }
    } catch (error) {
        console.error('Error initializing app:', error);
        toastManager.showError('خطا در راه‌اندازی برنامه: ' + error.message);
        
        // در صورت خطا، در حالت توسعه به داشبورد و در غیر این صورت به صفحه ورود منتقل می‌شویم
        if (appState.isDevelopment) {
            appState.isAuthenticated = true;
            showPage('dashboard');
        } else {
            showPage('login');
        }
    } finally {
        // پایان وضعیت بارگذاری
        setLoadingState(false);
    }
}

/**
 * بارگذاری اسکریپت‌های اضافی مورد نیاز
 */
async function loadExtraScripts() {
    try {
        // بارگذاری اسکریپت دیباگ در حالت توسعه
        if (appState.isDevelopment && typeof window.loadDebugStatus === 'undefined') {
            try {
                await loadScript('/js/debug.js');
                console.log('Debug module loaded successfully');
            } catch (debugError) {
                console.warn('Error loading debug module:', debugError);
            }
        }
        
        // بررسی وجود API و بارگذاری آن در صورت نیاز
        if (typeof window.api === 'undefined') {
            try {
                await loadScript('/js/api.js');
                console.log('API module loaded successfully');
            } catch (apiError) {
                console.warn('Error loading API module:', apiError);
            }
        }
        
        // بررسی وجود ماژول احراز هویت و بارگذاری آن در صورت نیاز
        if (typeof window.login === 'undefined' || typeof window.checkAuthStatus === 'undefined') {
            try {
                await loadScript('/js/auth.js');
                console.log('Auth module loaded successfully');
            } catch (authError) {
                console.warn('Error loading auth module:', authError);
            }
        }
    } catch (error) {
        console.error('Error loading extra scripts:', error);
    }
}

/**
 * بارگذاری دینامیک اسکریپت
 * @param {string} src - آدرس اسکریپت
 * @returns {Promise} Promise که پس از بارگذاری اسکریپت حل می‌شود
 */
function loadScript(src) {
    return new Promise((resolve, reject) => {
        const script = document.createElement('script');
        script.src = src;
        script.onload = () => resolve();
        script.onerror = () => reject(new Error(`خطا در بارگذاری اسکریپت: ${src}`));
        document.head.appendChild(script);
    });
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