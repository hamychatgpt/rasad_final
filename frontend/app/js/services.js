// services.js - مدیریت سرویس‌ها

// بارگذاری وضعیت سرویس‌ها
async function loadServices() {
    try {
        const servicesData = await api.get('/services/');
        updateServicesStatus(servicesData.services);
        return servicesData;
    } catch (error) {
        console.error('Error loading services:', error);
        showErrorMessage('خطا در بارگذاری وضعیت سرویس‌ها');
    }
}

// بروزرسانی نمایش وضعیت سرویس‌ها
function updateServicesStatus(services) {
    // صفحه سرویس‌ها
    updateServiceStatusElement('collectorStatus', services.collector);
    updateServiceStatusElement('processorStatus', services.processor);
    updateServiceStatusElement('analyzerStatus', services.analyzer);
    
    // وضعیت کلی
    updateAllServicesStatus(services);
    
    // بروزرسانی در داشبورد
    updateDashboardServices(services);
}

// بروزرسانی المان وضعیت سرویس
function updateServiceStatusElement(elementId, serviceStatus) {
    const element = document.getElementById(elementId);
    if (!element) return;
    
    if (serviceStatus?.status === "running") {
        element.innerHTML = `<span class="status-badge status-running">در حال اجرا</span>`;
        if (serviceStatus.uptime) {
            element.innerHTML += `<small class="d-block mt-1">مدت اجرا: ${serviceStatus.uptime_human || formatUptime(serviceStatus.uptime)}</small>`;
        }
    } else {
        element.innerHTML = `<span class="status-badge status-stopped">متوقف</span>`;
    }
}

// بروزرسانی وضعیت کلی سرویس‌ها
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

// شروع یک سرویس
async function startService(serviceName) {
    try {
        // نمایش وضعیت در حال بارگذاری
        const statusElement = document.getElementById(`${serviceName}Status`);
        if (statusElement) {
            statusElement.innerHTML = `<div class="spinner-border spinner-border-sm text-primary" role="status">
                <span class="visually-hidden">در حال شروع...</span>
            </div>`;
        }

        await api.post(`/services/${serviceName}/start`, {});
        await loadServices();
        
    } catch (error) {
        console.error(`Error starting service ${serviceName}:`, error);
        showErrorMessage(`خطا در شروع سرویس ${serviceName}`);
        await loadServices();
    }
}

// توقف یک سرویس
async function stopService(serviceName) {
    try {
        // نمایش وضعیت در حال بارگذاری
        const statusElement = document.getElementById(`${serviceName}Status`);
        if (statusElement) {
            statusElement.innerHTML = `<div class="spinner-border spinner-border-sm text-primary" role="status">
                <span class="visually-hidden">در حال توقف...</span>
            </div>`;
        }

        await api.post(`/services/${serviceName}/stop`, {});
        await loadServices();
        
    } catch (error) {
        console.error(`Error stopping service ${serviceName}:`, error);
        showErrorMessage(`خطا در توقف سرویس ${serviceName}`);
        await loadServices();
    }
}

// بروزرسانی بخش سرویس‌ها در داشبورد
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

// تابع کمکی برای فرمت زمان اجرا
function formatUptime(seconds) {
    if (!seconds) return '';
    
    const hours = Math.floor(seconds / 3600);
    const minutes = Math.floor((seconds % 3600) / 60);
    const secs = Math.floor(seconds % 60);
    
    return `${hours}:${minutes.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
}

// اتصال گوش‌دهنده‌های رویداد برای دکمه‌های سرویس
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
}