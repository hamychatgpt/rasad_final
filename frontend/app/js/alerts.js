// alerts.js - مدیریت هشدارها

// بارگذاری هشدارها
async function loadAlerts(params = new URLSearchParams()) {
    try {
        const queryString = params.toString();
        const endpoint = `/waves/alerts?${queryString}`;
        const alerts = await api.get(endpoint);
        
        displayAlerts(alerts);
        return alerts;
    } catch (error) {
        console.error('Error loading alerts:', error);
        showErrorMessage('خطا در بارگذاری هشدارها');
        return [];
    }
}

// نمایش هشدارها در صفحه
function displayAlerts(alerts) {
    const alertsContainer = document.getElementById('alertsList');
    if (!alertsContainer) return;
    
    if (alerts.length === 0) {
        alertsContainer.innerHTML = '<div class="alert alert-info">هشداری یافت نشد</div>';
        return;
    }
    
    alertsContainer.innerHTML = '';
    
    alerts.forEach(alert => {
        const alertElement = document.createElement('div');
        
        // تعیین کلاس آلرت بر اساس شدت
        let alertClass = 'alert-warning';
        if (alert.severity === 'high') alertClass = 'alert-danger';
        else if (alert.severity === 'low') alertClass = 'alert-info';
        
        // تعیین آیکون بر اساس نوع هشدار
        let alertIcon = 'bi-exclamation-triangle';
        if (alert.alert_type === 'wave') alertIcon = 'bi-graph-up';
        else if (alert.alert_type === 'security') alertIcon = 'bi-shield-exclamation';
        
        alertElement.className = `alert ${alertClass} ${alert.is_read ? 'alert-read' : ''}`;
        alertElement.innerHTML = `
            <div class="d-flex">
                <div class="alert-icon me-3">
                    <i class="bi ${alertIcon} fs-4"></i>
                </div>
                <div class="flex-grow-1">
                    <div class="d-flex justify-content-between">
                        <h5>${alert.title}</h5>
                        <small class="text-muted">${formatDate(alert.created_at)}</small>
                    </div>
                    <p>${alert.message}</p>
                    <div class="d-flex justify-content-end">
                        <button class="btn btn-sm btn-outline-primary me-2" onclick="showAlertDetails(${alert.id})">
                            جزئیات
                        </button>
                        ${!alert.is_read ? `
                            <button class="btn btn-sm btn-outline-secondary" onclick="markAlertAsRead(${alert.id})">
                                علامت‌گذاری به عنوان خوانده شده
                            </button>
                        ` : ''}
                    </div>
                </div>
            </div>
        `;
        
        alertsContainer.appendChild(alertElement);
    });
}

// نمایش جزئیات هشدار
async function showAlertDetails(alertId) {
    try {
        const alert = await api.get(`/waves/alerts/${alertId}`);
        
        const modal = document.getElementById('alertDetailModal');
        const