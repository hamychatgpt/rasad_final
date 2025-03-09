// api.js - مدیریت ارتباط با API

// کلاس مدیریت API
class Api {
    constructor() {
        this.token = localStorage.getItem('authToken');
    }

    setToken(token) {
        this.token = token;
        localStorage.setItem('authToken', token);
    }

    clearToken() {
        this.token = null;
        localStorage.removeItem('authToken');
    }

    async request(endpoint, options = {}) {
        // اطمینان از اینکه آدرس درست است (با یا بدون / شروع شود)
        // مسیرها باید با /api/v1 شروع شوند، مگر اینکه کامل باشند
        let url;
        if (endpoint.startsWith('http')) {
            url = endpoint;
        } else if (endpoint.startsWith('/api/v1')) {
            url = endpoint;
        } else {
            // اضافه کردن پیشوند /api/v1 به مسیر
            url = `/api/v1${endpoint.startsWith('/') ? endpoint : `/${endpoint}`}`;
        }
        
        // اضافه کردن هدر احراز هویت
        const headers = {
            ...(options.headers || {}),
        };
        
        if (this.token) {
            headers['Authorization'] = `Bearer ${this.token}`;
        }
        
        // ترکیب تنظیمات
        const fetchOptions = {
            ...options,
            headers
        };
        
        try {
            const response = await fetch(url, fetchOptions);
            
            if (!response.ok) {
                // پردازش خطاهای HTTP
                if (response.status === 401) {
                    this.clearToken();
                    throw new Error('نشست شما منقضی شده است. لطفاً دوباره وارد شوید.');
                }
                
                const errorData = await response.json().catch(() => {
                    return { detail: response.statusText };
                });
                
                throw new Error(errorData.detail || 'خطای ناشناخته');
            }
            
            // اگر پاسخ خالی است، آبجکت خالی برگردانیم
            if (response.status === 204) {
                return {};
            }
            
            return await response.json();
        } catch (error) {
            console.error(`API Error (${url}):`, error);
            throw error;
        }
    }

    // روش‌های درخواست HTTP
    async get(endpoint) {
        return this.request(endpoint);
    }

    async post(endpoint, data) {
        return this.request(endpoint, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(data)
        });
    }

    async put(endpoint, data) {
        return this.request(endpoint, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(data)
        });
    }

    async delete(endpoint) {
        return this.request(endpoint, { method: 'DELETE' });
    }
}

// ایجاد یک نمونه جهانی
const api = new Api();

// صادرات نمونه API به صورت عمومی
window.api = api;