// main.js - نقطه ورود اصلی برنامه

// تنظیم وضعیت اولیه
let currentPage = 'dashboard';

// نمایش صفحه مورد نظر
function showPage(page) {
    currentPage = page;

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
        loadDashboard();
    } else if (page === 'tweets') {
        document.getElementById('tweetsContent').style.display = 'block';
        document.getElementById('tweetsLink').classList.add('active');
        // loadTweets();
    } else if (page === 'alerts') {
        document.getElementById('alertsContent').style.display = 'block';
        document.getElementById('alertsLink').classList.add('active');
        // loadAlerts();
    } else if (page === 'settings') {
        document.getElementById('settingsContent').style.display = 'block';
        document.getElementById('settingsLink').classList.add('active');
        loadAndDisplayKeywords();
        // loadSettings();
    } else if (page === 'services') {
        document.getElementById('servicesContent').style.display = 'block';
        document.getElementById('servicesLink').classList.add('active');
        loadServices();
    }
}

// نمایش پیام خطا
function showErrorMessage(message) {
    // ایجاد المان توست
    const toastContainer = document.getElementById('toastContainer');
    if (!toastContainer) {
        // ایجاد کانتینر توست اگر وجود ندارد
        const container = document.createElement('div');
        container.id = 'toastContainer';
        container.className = 'toast-container position-fixed top-0 end-0 p-3';
        document.body.appendChild(container);
    }
    
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
    
    document.getElementById('toastContainer').insertAdjacentHTML('beforeend', toastHTML);
    
    // نمایش توست
    const toastElement = document.getElementById(toastId);
    const toast = new bootstrap.Toast(toastElement);
    toast.show();
    
    // حذف توست بعد از بسته شدن
    toastElement.addEventListener('hidden.bs.toast', function () {
        this.remove();
    });
}

// نمایش پیام موفقیت
function showSuccessMessage(message) {
    // مشابه showErrorMessage اما با کلاس bg-success
    const toastContainer = document.getElementById('toastContainer');
    if (!toastContainer) {
        const container = document.createElement('div');
        container.id = 'toastContainer';
        container.className = 'toast-container position-fixed top-0 end-0 p-3';
        document.body.appendChild(container);
    }
    
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
    
    document.getElementById('toastContainer').insertAdjacentHTML('beforeend', toastHTML);
    
    const toastElement = document.getElementById(toastId);
    const toast = new bootstrap.Toast(toastElement);
    toast.show();
    
    toastElement.addEventListener('hidden.bs.toast', function () {
        this.remove();
    });
}

// راه‌اندازی برنامه
document.addEventListener('DOMContentLoaded', () => {
    // اتصال به المان‌های DOM برای ناوبری
    document.getElementById('dashboardLink').addEventListener('click', () => showPage('dashboard'));
    document.getElementById('tweetsLink').addEventListener('click', () => showPage('tweets'));
    document.getElementById('alertsLink').addEventListener('click', () => showPage('alerts'));
    document.getElementById('settingsLink').addEventListener('click', () => showPage('settings'));
    document.getElementById('servicesLink').addEventListener('click', () => showPage('services'));
    
    // گوش‌دهنده‌های رویداد برای تمام ماژول‌ها
    setupAuthListeners();
    setupDashboardListeners();
    setupServiceListeners();
    setupKeywordListeners();
    
    // ایجاد کانتینر توست
    if (!document.getElementById('toastContainer')) {
        const container = document.createElement('div');
        container.id = 'toastContainer';
        container.className = 'toast-container position-fixed top-0 end-0 p-3';
        document.body.appendChild(container);
    }
    
    // بررسی وضعیت احراز هویت
    checkAuthStatus().then(authenticated => {
        if (authenticated) {
            showPage('dashboard');
        }
    });
});