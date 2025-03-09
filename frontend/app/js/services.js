// services.js - مدیریت سرویس‌ها
// این ماژول مسئول مدیریت سرویس‌های پشت صحنه سیستم است:
// 1. جمع‌آوری‌کننده (collector): جمع‌آوری توییت‌ها از توییتر
// 2. پردازشگر (processor): پردازش و فیلتر توییت‌ها
// 3. تحلیلگر (analyzer): تحلیل محتوا و احساسات توییت‌ها

// متغیرهای ماژول
let serviceStatus = {
    collector: { status: 'unknown', details: null },
    processor: { status: 'unknown', details: null },
    analyzer: { status: 'unknown', details: null }
};

let loadingServices = false;
let refreshInterval = null;
const AUTO_REFRESH_INTERVAL = 60000; // بروزرسانی خودکار هر 60 ثانیه

/**
 * بارگذاری وضعیت سرویس‌ها
 * @returns {Promise<Object>} وضعیت سرویس‌ها
 */
async function loadServices() {
    if (loadingServices) return; // جلوگیری از فراخوانی‌های همزمان
    
    loadingServices = true;
    
    try {
        // نمایش وضعیت در حال بارگذاری در المان‌های اصلی
        updateLoadingState(true);
        
        // دریافت وضعیت سرویس‌ها از API
        const servicesData = await api.get('/services/');
        
        // ذخیره وضعیت سرویس‌ها در متغیر ماژول
        serviceStatus = {
            collector: servicesData.services.collector || { status: 'unknown', details: null },
            processor: servicesData.services.processor || { status: 'unknown', details: null },
            analyzer: servicesData.services.analyzer || { status: 'unknown', details: null }
        };
        
        // بروزرسانی نمایش وضعیت سرویس‌ها
        updateServicesStatus(servicesData.services);
        
        // بروزرسانی اطلاعات سیستم
        updateSystemInfo(servicesData.system_info);
        
        return servicesData;
    } catch (error) {
        console.error('Error loading services:', error);
        showErrorMessage('خطا در بارگذاری وضعیت سرویس‌ها');
        
        // بروزرسانی نمایش وضعیت خطا
        updateErrorState();
    } finally {
        loadingServices = false;
        updateLoadingState(false);
    }
}

/**
 * نمایش وضعیت در حال بارگذاری
 * @param {boolean} isLoading آیا در حال بارگذاری است
 */
function updateLoadingState(isLoading) {
    const statusElements = [
        document.getElementById('collectorStatus'),
        document.getElementById('processorStatus'),
        document.getElementById('analyzerStatus'),
        document.getElementById('allServicesStatus')
    ];
    
    statusElements.forEach(element => {
        if (element && isLoading) {
            element.innerHTML = `<div class="spinner-border spinner-border-sm text-primary" role="status">
                <span class="visually-hidden">در حال بارگذاری...</span>
            </div>`;
        }
    });
    
    const systemInfoElement = document.getElementById('systemInfo');
    if (systemInfoElement && isLoading) {
        systemInfoElement.innerHTML = `<div class="text-center">
            <div class="spinner-border text-primary" role="status">
                <span class="visually-hidden">در حال بارگذاری...</span>
            </div>
        </div>`;
    }
}

/**
 * نمایش وضعیت خطا
 */
function updateErrorState() {
    const statusElements = [
        { id: 'collectorStatus', label: 'جمع‌آوری‌کننده' },
        { id: 'processorStatus', label: 'پردازشگر' },
        { id: 'analyzerStatus', label: 'تحلیلگر' }
    ];
    
    statusElements.forEach(item => {
        const element = document.getElementById(item.id);
        if (element) {
            element.innerHTML = `<span class="badge bg-danger">خطای ارتباط</span>`;
        }
    });
    
    const allServicesElement = document.getElementById('allServicesStatus');
    if (allServicesElement) {
        allServicesElement.textContent = "خطا";
        allServicesElement.className = "badge bg-danger";
    }
    
    const systemInfoElement = document.getElementById('systemInfo');
    if (systemInfoElement) {
        systemInfoElement.innerHTML = `<div class="alert alert-danger">
            <i class="bi bi-exclamation-triangle-fill"></i> خطا در دریافت اطلاعات سیستم
        </div>`;
    }
}

/**
 * بروزرسانی نمایش وضعیت سرویس‌ها
 * @param {Object} services وضعیت سرویس‌ها
 */
function updateServicesStatus(services) {
    // بروزرسانی المان‌های صفحه سرویس‌ها
    updateServiceStatusElement('collectorStatus', services.collector);
    updateServiceStatusElement('processorStatus', services.processor);
    updateServiceStatusElement('analyzerStatus', services.analyzer);
    
    // بروزرسانی وضعیت کلی سرویس‌ها
    updateAllServicesStatus(services);
    
    // بروزرسانی در داشبورد
    updateDashboardServices(services);
}

/**
 * بروزرسانی المان وضعیت یک سرویس خاص
 * @param {string} elementId شناسه المان HTML
 * @param {Object} serviceStatus وضعیت سرویس
 */
function updateServiceStatusElement(elementId, serviceStatus) {
    const element = document.getElementById(elementId);
    if (!element) return;
    
    if (serviceStatus?.status === "running") {
        let uptime = '';
        if (serviceStatus.uptime) {
            uptime = serviceStatus.uptime_human || formatUptime(serviceStatus.uptime);
        }
        
        element.innerHTML = `
            <span class="status-badge status-running">در حال اجرا</span>
            ${uptime ? `<small class="d-block mt-1">مدت اجرا: ${uptime}</small>` : ''}
            ${serviceStatus.pid ? `<small class="d-block text-muted">PID: ${serviceStatus.pid}</small>` : ''}
        `;
    } else {
        element.innerHTML = `<span class="status-badge status-stopped">متوقف</span>`;
    }
}

/**
 * بروزرسانی وضعیت کلی سرویس‌ها
 * @param {Object} services وضعیت همه سرویس‌ها
 */
function updateAllServicesStatus(services) {
    const element = document.getElementById('allServicesStatus');
    if (!element) return;
    
    const allRunning = Object.values(services).every(s => s.status === "running");
    const allStopped = Object.values(services).every(s => s.status === "stopped");
    
    if (allRunning) {
        element.textContent = "در حال اجرا";
        element.className = "status-badge status-running";
    } else if (allStopped) {
        element.textContent = "متوقف";
        element.className = "status-badge status-stopped";
    } else {
        element.textContent = "اجرای بخشی";
        element.className = "status-badge status-warning";
    }
}

/**
 * بروزرسانی بخش سرویس‌ها در داشبورد
 * @param {Object} services وضعیت سرویس‌ها
 */
function updateDashboardServices(services) {
    const servicesStatus = document.getElementById('servicesStatus');
    if (!servicesStatus) return;
    
    servicesStatus.innerHTML = '';
    
    // ایجاد کارت وضعیت برای هر سرویس
    const serviceNames = {
        'collector': 'جمع‌آوری‌کننده',
        'processor': 'پردازشگر',
        'analyzer': 'تحلیلگر'
    };
    
    // ایجاد کارت برای هر سرویس
    for (const [name, status] of Object.entries(services)) {
        const displayName = serviceNames[name] || name;
        const statusClass = status.status === 'running' ? 'bg-success' : 'bg-danger';
        const statusText = status.status === 'running' ? 'در حال اجرا' : 'متوقف';
        
        const serviceCard = document.createElement('div');
        serviceCard.className = 'd-flex justify-content-between align-items-center mb-2 p-2 border rounded';
        serviceCard.innerHTML = `
            <div>
                <strong>${displayName}</strong>
                <span class="badge ${statusClass} ms-2">${statusText}</span>
            </div>
            <div>
                ${status.status === 'running' ? 
                  `<button class="btn btn-sm btn-danger service-action" data-action="stop" data-service="${name}">
                     <i class="bi bi-stop-fill"></i> توقف
                   </button>` : 
                  `<button class="btn btn-sm btn-success service-action" data-action="start" data-service="${name}">
                     <i class="bi bi-play-fill"></i> شروع
                   </button>`
                }
            </div>
        `;
        
        servicesStatus.appendChild(serviceCard);
    }
    
    // اضافه کردن دکمه مدیریت همه سرویس‌ها
    const allButton = document.createElement('div');
    allButton.className = 'd-flex justify-content-center mt-3';
    allButton.innerHTML = `
        <div class="btn-group">
            <button class="btn btn-success service-action" data-action="start" data-service="all">
                <i class="bi bi-play-fill"></i> شروع همه
            </button>
            <button class="btn btn-danger service-action" data-action="stop" data-service="all">
                <i class="bi bi-stop-fill"></i> توقف همه
            </button>
        </div>
    `;
    
    servicesStatus.appendChild(allButton);
    
    // اضافه کردن event listener به دکمه‌ها
    document.querySelectorAll('.service-action').forEach(button => {
        button.addEventListener('click', function() {
            const service = this.getAttribute('data-service');
            const action = this.getAttribute('data-action');
            
            if (action === 'start') {
                startService(service);
            } else if (action === 'stop') {
                stopService(service);
            }
        });
    });
}

/**
 * بروزرسانی اطلاعات سیستم
 * @param {Object} systemInfo اطلاعات سیستم
 */
function updateSystemInfo(systemInfo) {
    const systemInfoElement = document.getElementById('systemInfo');
    if (!systemInfoElement || !systemInfo) return;
    
    const memoryUsagePercent = Math.round(100 - (systemInfo.memory_available / systemInfo.memory_total * 100));
    
    systemInfoElement.innerHTML = `
        <div class="row">
            <div class="col-md-6">
                <ul class="list-group mb-3">
                    <li class="list-group-item d-flex justify-content-between align-items-center">
                        <span><i class="bi bi-cpu"></i> سیستم‌عامل:</span>
                        <span class="text-muted">${systemInfo.platform} ${systemInfo.platform_version}</span>
                    </li>
                    <li class="list-group-item d-flex justify-content-between align-items-center">
                        <span><i class="bi bi-hdd"></i> نام میزبان:</span>
                        <span class="text-muted">${systemInfo.hostname}</span>
                    </li>
                    <li class="list-group-item d-flex justify-content-between align-items-center">
                        <span><i class="bi bi-cpu-fill"></i> تعداد هسته‌های CPU:</span>
                        <span class="text-muted">${systemInfo.cpu_count}</span>
                    </li>
                </ul>
            </div>
            <div class="col-md-6">
                <ul class="list-group mb-3">
                    <li class="list-group-item d-flex justify-content-between align-items-center">
                        <span><i class="bi bi-memory"></i> حافظه کل:</span>
                        <span class="text-muted">${systemInfo.memory_total.toFixed(2)} GB</span>
                    </li>
                    <li class="list-group-item d-flex justify-content-between align-items-center">
                        <span><i class="bi bi-memory"></i> حافظه در دسترس:</span>
                        <span class="text-muted">${systemInfo.memory_available.toFixed(2)} GB</span>
                    </li>
                    <li class="list-group-item">
                        <span><i class="bi bi-bar-chart-fill"></i> استفاده از حافظه:</span>
                        <div class="progress mt-2" style="height: 20px;">
                            <div class="progress-bar ${memoryUsagePercent > 80 ? 'bg-danger' : memoryUsagePercent > 60 ? 'bg-warning' : 'bg-success'}" 
                                role="progressbar" style="width: ${memoryUsagePercent}%;" 
                                aria-valuenow="${memoryUsagePercent}" aria-valuemin="0" aria-valuemax="100">
                                ${memoryUsagePercent}%
                            </div>
                        </div>
                    </li>
                </ul>
            </div>
        </div>
        <div class="row">
            <div class="col-12">
                <div class="text-muted text-center">
                    <small>اطلاعات سیستم در تاریخ ${new Date().toLocaleString('fa-IR')} بروزرسانی شده است</small>
                </div>
            </div>
        </div>
    `;
}

/**
 * شروع یک سرویس
 * @param {string} serviceName نام سرویس
 * @returns {Promise<void>}
 */
async function startService(serviceName) {
    try {
        // نمایش وضعیت در حال بارگذاری
        const statusElement = document.getElementById(`${serviceName}Status`);
        if (statusElement) {
            statusElement.innerHTML = `<div class="spinner-border spinner-border-sm text-primary" role="status">
                <span class="visually-hidden">در حال شروع...</span>
            </div>`;
        }

        // غیرفعال کردن دکمه‌ها برای جلوگیری از کلیک‌های متعدد
        updateServiceButtons(serviceName, true);
        
        // ارسال درخواست شروع سرویس
        await api.post(`/services/${serviceName}/start`, {});
        
        // بروزرسانی وضعیت سرویس‌ها
        await loadServices();
        
        // نمایش پیام موفقیت
        showSuccessMessage(`سرویس ${getServiceDisplayName(serviceName)} با موفقیت شروع شد`);
        
    } catch (error) {
        console.error(`Error starting service ${serviceName}:`, error);
        showErrorMessage(`خطا در شروع سرویس ${getServiceDisplayName(serviceName)}: ${error.message}`);
        
        // بروزرسانی مجدد وضعیت سرویس‌ها
        await loadServices();
    } finally {
        // فعال کردن دکمه‌ها
        updateServiceButtons(serviceName, false);
    }
}

/**
 * فعال/غیرفعال کردن دکمه‌های سرویس
 * @param {string} serviceName نام سرویس
 * @param {boolean} disabled آیا دکمه‌ها غیرفعال شوند
 */
function updateServiceButtons(serviceName, disabled) {
    if (serviceName === 'all') {
        // دکمه‌های همه سرویس‌ها
        document.querySelectorAll('[id^="start"], [id^="stop"]').forEach(button => {
            button.disabled = disabled;
        });
    } else {
        // دکمه‌های یک سرویس خاص
        const startButton = document.getElementById(`start${capitalizeFirstLetter(serviceName)}`);
        const stopButton = document.getElementById(`stop${capitalizeFirstLetter(serviceName)}`);
        
        if (startButton) startButton.disabled = disabled;
        if (stopButton) stopButton.disabled = disabled;
    }
    
    // دکمه‌های داشبورد
    document.querySelectorAll('.service-action').forEach(button => {
        const btnService = button.getAttribute('data-service');
        if (btnService === serviceName || serviceName === 'all') {
            button.disabled = disabled;
        }
    });
}

/**
 * دریافت نام قابل نمایش سرویس
 * @param {string} serviceName نام سرویس
 * @returns {string} نام قابل نمایش
 */
function getServiceDisplayName(serviceName) {
    const serviceNames = {
        'collector': 'جمع‌آوری‌کننده',
        'processor': 'پردازشگر',
        'analyzer': 'تحلیلگر',
        'all': 'همه سرویس‌ها'
    };
    
    return serviceNames[serviceName] || serviceName;
}

/**
 * حروف اول یک رشته را بزرگ می‌کند
 * @param {string} str رشته ورودی
 * @returns {string} رشته با حرف اول بزرگ
 */
function capitalizeFirstLetter(str) {
    return str.charAt(0).toUpperCase() + str.slice(1);
}

/**
 * بارگذاری لاگ‌های سرویس
 * @param {string} serviceName نام سرویس
 * @param {number} lines تعداد خطوط
 * @returns {Promise<void>}
 */
async function loadServiceLogs(serviceName, lines = 100) {
    try {
        // نمایش وضعیت در حال بارگذاری
        const logsElement = document.getElementById('serviceLogs');
        if (logsElement) {
            logsElement.textContent = 'در حال بارگذاری لاگ‌ها...';
        }
        
        // دریافت لاگ‌ها از API
        const response = await api.get(`/services/logs/${serviceName}?lines=${lines}`);
        
        // نمایش لاگ‌ها
        if (logsElement) {
            if (!response.logs || Object.keys(response.logs).length === 0) {
                logsElement.textContent = 'لاگی برای نمایش وجود ندارد';
                return;
            }
            
            // تعیین لاگ مناسب برای نمایش
            let logContent = '';
            
            if (serviceName === 'all' && response.logs.all) {
                logContent = response.logs.all;
            } else if (response.logs.service) {
                logContent = response.logs.service;
            } else if (response.logs.output) {
                logContent = response.logs.output;
            } else if (response.logs.error) {
                logContent = response.logs.error;
            } else {
                // نمایش اولین لاگ موجود
                const firstLog = Object.values(response.logs)[0];
                logContent = firstLog || 'لاگی برای نمایش وجود ندارد';
            }
            
            logsElement.textContent = logContent;
        }
    } catch (error) {
        console.error(`Error loading service logs for ${serviceName}:`, error);
        
        const logsElement = document.getElementById('serviceLogs');
        if (logsElement) {
            logsElement.textContent = `خطا در بارگذاری لاگ‌ها: ${error.message}`;
        }
    }
}

/**
 * فعال/غیرفعال کردن بروزرسانی خودکار
 * @param {boolean} enable آیا بروزرسانی خودکار فعال شود
 */
function enableAutoRefresh(enable) {
    // لغو تایمر قبلی
    if (refreshInterval) {
        clearInterval(refreshInterval);
        refreshInterval = null;
    }
    
    // تنظیم تایمر جدید
    if (enable) {
        refreshInterval = setInterval(loadServices, AUTO_REFRESH_INTERVAL);
        
        // نمایش وضعیت فعال بودن بروزرسانی خودکار
        const autoRefreshBtn = document.getElementById('toggleAutoRefresh');
        if (autoRefreshBtn) {
            autoRefreshBtn.innerHTML = '<i class="bi bi-toggle-on"></i> غیرفعال کردن بروزرسانی خودکار';
            autoRefreshBtn.classList.remove('btn-outline-primary');
            autoRefreshBtn.classList.add('btn-primary');
        }
    } else {
        // نمایش وضعیت غیرفعال بودن بروزرسانی خودکار
        const autoRefreshBtn = document.getElementById('toggleAutoRefresh');
        if (autoRefreshBtn) {
            autoRefreshBtn.innerHTML = '<i class="bi bi-toggle-off"></i> فعال کردن بروزرسانی خودکار';
            autoRefreshBtn.classList.remove('btn-primary');
            autoRefreshBtn.classList.add('btn-outline-primary');
        }
    }
}

/**
 * تابع کمکی برای فرمت زمان اجرا
 * @param {number} seconds زمان به ثانیه
 * @returns {string} زمان فرمت شده
 */
function formatUptime(seconds) {
    if (!seconds) return '';
    
    const days = Math.floor(seconds / 86400);
    const hours = Math.floor((seconds % 86400) / 3600);
    const minutes = Math.floor((seconds % 3600) / 60);
    const secs = Math.floor(seconds % 60);
    
    if (days > 0) {
        return `${days} روز و ${hours}:${minutes.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
    }
    
    return `${hours}:${minutes.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
}

/**
 * تنظیم گوش‌دهنده‌های رویداد برای دکمه‌های سرویس
 */
function setupServiceListeners() {
    // دکمه‌های صفحه سرویس‌ها
    document.getElementById('startCollector')?.addEventListener('click', () => startService('collector'));
    document.getElementById('stopCollector')?.addEventListener('click', () => stopService('collector'));
    document.getElementById('startProcessor')?.addEventListener('click', () => startService('processor'));
    document.getElementById('stopProcessor')?.addEventListener('click', () => stopService('processor'));
    document.getElementById('startAnalyzer')?.addEventListener('click', () => startService('analyzer'));
    document.getElementById('stopAnalyzer')?.addEventListener('click', () => stopService('analyzer'));
    document.getElementById('startAllServices')?.addEventListener('click', () => startService('all'));
    document.getElementById('stopAllServices')?.addEventListener('click', () => stopService('all'));
    document.getElementById('refreshServices')?.addEventListener('click', loadServices);
    
    // انتخاب‌گر سرویس برای لاگ‌ها
    const logServiceSelector = document.getElementById('logServiceSelector');
    if (logServiceSelector) {
        logServiceSelector.addEventListener('change', function() {
            loadServiceLogs(this.value);
        });
    }
    
    // دکمه بروزرسانی لاگ‌ها
    document.getElementById('refreshLogs')?.addEventListener('click', function() {
        const selectedService = document.getElementById('logServiceSelector')?.value || 'all';
        loadServiceLogs(selectedService);
    });
    
    // دکمه مدیریت سرویس‌ها در داشبورد
    document.getElementById('manageServices')?.addEventListener('click', () => {
        showPage('services');
    });
    
    // افزودن دکمه بروزرسانی خودکار
    const refreshServicesButton = document.getElementById('refreshServices');
    if (refreshServicesButton) {
        const autoRefreshButton = document.createElement('button');
        autoRefreshButton.id = 'toggleAutoRefresh';
        autoRefreshButton.className = 'btn btn-outline-primary ms-2';
        autoRefreshButton.innerHTML = '<i class="bi bi-toggle-off"></i> فعال کردن بروزرسانی خودکار';
        
        refreshServicesButton.parentNode.appendChild(autoRefreshButton);
        
        autoRefreshButton.addEventListener('click', function() {
            // تغییر وضعیت بروزرسانی خودکار
            const isAutoRefreshEnabled = !!refreshInterval;
            enableAutoRefresh(!isAutoRefreshEnabled);
        });
    }
    
    // اولین بارگذاری لاگ‌ها
    if (document.getElementById('serviceLogs')) {
        loadServiceLogs('all');
    }
}

// نمایش اولیه سرویس‌ها
document.addEventListener('DOMContentLoaded', () => {
    // اگر صفحه سرویس‌ها نمایش داده شده است
    if (window.currentPage === 'services' && document.getElementById('servicesContent').style.display !== 'none') {
        loadServices();
    }
});

// صادرات توابع و متغیرهای مورد نیاز
window.loadServices = loadServices;
window.startService = startService;
window.stopService = stopService;
window.setupServiceListeners = setupServiceListeners;

/**
 * توقف یک سرویس
 * @param {string} serviceName نام سرویس
 * @returns {Promise<void>}
 */
async function stopService(serviceName) {
    try {
        // نمایش وضعیت در حال بارگذاری
        const statusElement = document.getElementById(`${serviceName}Status`);
        if (statusElement) {
            statusElement.innerHTML = `<div class="spinner-border spinner-border-sm text-primary" role="status">
                <span class="visually-hidden">در حال توقف...</span>
            </div>`;
        }

        // غیرفعال کردن دکمه‌ها برای جلوگیری از کلیک‌های متعدد
        updateServiceButtons(serviceName, true);
        
        // ارسال درخواست توقف سرویس
        await api.post(`/services/${serviceName}/stop`, {});
        
        // بروزرسانی وضعیت سرویس‌ها
        await loadServices();
        
        // نمایش پیام موفقیت
        showSuccessMessage(`سرویس ${getServiceDisplayName(serviceName)} با موفقیت متوقف شد`);
        
    } catch (error) {
        console.error(`Error stopping service ${serviceName}:`, error);
        showErrorMessage(`خطا در توقف سرویس ${getServiceDisplayName(serviceName)}: ${error.message}`);
        
        // بروزرسانی مجدد وضعیت سرویس‌ها
        await loadServices();
    } finally {
        // فعال کردن دکمه‌ها
        updateServiceButtons(serviceName, false);
    }
}