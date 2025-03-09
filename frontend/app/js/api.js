// api.js - مدیریت ارتباط با API

// متغیر برای تنظیم حالت توسعه
const DEV_MODE = true; // تغییر به false در محیط تولید

// کلاس مدیریت API
class Api {
    constructor() {
        this.token = localStorage.getItem('authToken');
        console.log('API initialized, token:', this.token ? 'exists' : 'not found');
        
        // اگر حالت توسعه فعال است و توکن موجود نیست، توکن پیش‌فرض ایجاد می‌کنیم
        if (DEV_MODE && !this.token) {
            this.token = "dev-mode-token";
            localStorage.setItem('authToken', this.token);
            console.log('Development mode: setting default token');
        }
    }

    setToken(token) {
        this.token = token;
        localStorage.setItem('authToken', token);
        console.log('Token set:', token);
    }

    clearToken() {
        this.token = null;
        localStorage.removeItem('authToken');
        console.log('Token cleared');
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
        
        console.log(`API request: ${options.method || 'GET'} ${url}`);
        
        // اضافه کردن هدر احراز هویت
        const headers = {
            ...(options.headers || {}),
        };
        
        if (this.token) {
            headers['Authorization'] = `Bearer ${this.token}`;
        }
        
        // در حالت توسعه، هدرهای CORS را اضافه می‌کنیم
        if (DEV_MODE) {
            headers['X-Requested-With'] = 'XMLHttpRequest';
        }
        
        // ترکیب تنظیمات
        const fetchOptions = {
            ...options,
            headers
        };
        
        try {
            // در حالت توسعه، اگر درخواست احراز هویت است، مستقیماً پاسخ می‌دهیم
            if (DEV_MODE && (url.includes('/auth/me') || url.includes('/auth/login'))) {
                console.log('Development mode: mocking auth response');
                return {
                    access_token: this.token || 'dev-mode-token',
                    token_type: 'bearer',
                    user: {
                        email: 'dev@example.com',
                        full_name: 'کاربر توسعه'
                    }
                };
            }
            
            const response = await fetch(url, fetchOptions);
            
            if (!response.ok) {
                // پردازش خطاهای HTTP
                if (response.status === 401) {
                    // در حالت توسعه، خطای 401 را نادیده می‌گیریم و با توکن جدید تلاش می‌کنیم
                    if (DEV_MODE) {
                        console.warn('Auth error in development mode - trying with new token');
                        this.setToken("dev-mode-token-" + Date.now());
                        return this.request(endpoint, options);
                    }
                    
                    this.clearToken();
                    throw new Error('نشست شما منقضی شده است. لطفاً دوباره وارد شوید.');
                }
                
                let errorData;
                try {
                    errorData = await response.json();
                } catch (e) {
                    errorData = { detail: response.statusText };
                }
                
                const errorMessage = errorData.detail || 'خطای ناشناخته';
                console.error(`API error (${response.status}): ${errorMessage}`);
                
                // در حالت توسعه، برخی خطاها را نادیده می‌گیریم
                if (DEV_MODE && [404, 500].includes(response.status)) {
                    console.warn(`Development mode: ignoring ${response.status} error`);
                    
                    // برگرداندن داده‌های ساختگی برای برخی مسیرها
                    if (url.includes('/keywords')) {
                        return [
                            { id: 1, text: 'کلیدواژه نمونه ۱', is_active: true, priority: 1, created_at: new Date().toISOString() },
                            { id: 2, text: 'کلیدواژه نمونه ۲', is_active: true, priority: 2, created_at: new Date().toISOString() }
                        ];
                    }
                    
                    // برای سایر درخواست‌ها، یک آبجکت خالی برمی‌گردانیم
                    return {};
                }
                
                throw new Error(errorMessage);
            }
            
            // اگر پاسخ خالی است، آبجکت خالی برگردانیم
            if (response.status === 204) {
                return {};
            }
            
            const data = await response.json();
            console.log('API response:', data);
            return data;
        } catch (error) {
            console.error(`API Error (${url}):`, error);
            
            // در حالت توسعه، برخی خطاها را نادیده می‌گیریم و داده‌های ساختگی برمی‌گردانیم
            if (DEV_MODE) {
                console.warn('Development mode: returning mock data for failed request');
                
                if (url.includes('/tweets/keywords')) {
                    return [
                        { id: 1, text: 'کلیدواژه نمونه ۱', is_active: true, priority: 1, created_at: new Date().toISOString() },
                        { id: 2, text: 'کلیدواژه نمونه ۲', is_active: true, priority: 2, created_at: new Date().toISOString() }
                    ];
                }
                
                if (url.includes('/tweets/count')) {
                    return {
                        total: 123,
                        sentiment_counts: {
                            positive: 50,
                            negative: 30,
                            neutral: 40,
                            mixed: 3
                        }
                    };
                }
                
                if (url.includes('/auth/me') || url.includes('/auth/login')) {
                    return { 
                        email: 'dev@example.com', 
                        full_name: 'کاربر توسعه' 
                    };
                }
                
                // برای سایر درخواست‌ها، یک آبجکت خالی برمی‌گردانیم
                return {};
            }
            
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

console.log('API module loaded');