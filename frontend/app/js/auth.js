// auth.js - مدیریت احراز هویت

// متغیر برای تنظیم حالت توسعه (بدون نیاز به احراز هویت)
const DEV_MODE = true; // تغییر به false در محیط تولید

// تعریف API به صورت محلی اگر موجود نباشد
if (typeof window.api === 'undefined') {
    console.warn('API module not available, creating minimal API');
    window.api = {
        token: localStorage.getItem('authToken'),
        
        setToken: function(token) {
            this.token = token;
            localStorage.setItem('authToken', token);
            console.log('Token set:', token);
        },
        
        clearToken: function() {
            this.token = null;
            localStorage.removeItem('authToken');
            console.log('Token cleared');
        },
        
        get: async function(endpoint) {
            console.warn('Using mock API.get for:', endpoint);
            if (endpoint === '/auth/me') {
                return { email: 'dev@example.com', full_name: 'کاربر توسعه' };
            }
            return {};
        }
    };
}

// ورود به سیستم
async function login(username, password) {
    try {
        // در حالت توسعه، ورود با هر مشخصاتی مجاز است
        if (DEV_MODE) {
            window.api.setToken("dev-mode-token");
            console.log('Development mode: login successful with mock token');
            return true;
        }
        
        const formData = new URLSearchParams();
        formData.append('username', username);
        formData.append('password', password);
        
        const response = await fetch(`/api/v1/auth/login`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/x-www-form-urlencoded'
            },
            body: formData
        });

        if (!response.ok) {
            throw new Error('نام کاربری یا رمز عبور نادرست است');
        }

        const data = await response.json();
        window.api.setToken(data.access_token);
        
        return true;
    } catch (error) {
        console.error('Login error:', error);
        
        // در حالت توسعه، خطا را نادیده می‌گیریم و ورود موفق فرض می‌کنیم
        if (DEV_MODE) {
            console.warn('Development mode: ignoring login error');
            window.api.setToken("dev-mode-token-fallback");
            return true;
        }
        
        throw error;
    }
}

// بررسی وضعیت احراز هویت
async function checkAuthStatus() {
    console.log('Checking auth status...');
    
    // در حالت توسعه، همیشه احراز هویت شده فرض می‌شود
    if (DEV_MODE) {
        if (!window.api.token) {
            window.api.setToken("dev-mode-token");
        }
        
        // تنظیم نام کاربر در منو
        const userDisplayName = document.getElementById('userDisplayName');
        if (userDisplayName) {
            userDisplayName.textContent = 'کاربر توسعه';
        }
        
        console.log('Development mode: auth status is true');
        return true;
    }
    
    if (!window.api.token) {
        console.log('No token found');
        return false;
    }

    try {
        const userData = await window.api.get('/auth/me');
        
        // نمایش اطلاعات کاربر در منو
        const userDisplayName = document.getElementById('userDisplayName');
        if (userDisplayName) {
            userDisplayName.textContent = userData.email || userData.full_name || 'کاربر';
        }
        
        console.log('Auth successful');
        return true;
    } catch (error) {
        console.error('Auth check error:', error);
        window.api.clearToken();
        
        // در حالت توسعه، خطا را نادیده می‌گیریم و احراز هویت موفق فرض می‌کنیم
        if (DEV_MODE) {
            console.warn('Development mode: ignoring auth check error');
            window.api.setToken("dev-mode-token-fallback");
            return true;
        }
        
        return false;
    }
}

// خروج از سیستم
function logout() {
    console.log('Logging out...');
    window.api.clearToken();
    
    // بازگشت به صفحه ورود
    if (typeof window.showPage === 'function') {
        window.showPage('login');
    }
    
    // بازنشانی نام کاربر در منو
    const userDisplayName = document.getElementById('userDisplayName');
    if (userDisplayName) {
        userDisplayName.textContent = 'ورود';
    }
    
    // نمایش پیام خروج
    if (typeof window.showSuccessMessage === 'function') {
        window.showSuccessMessage('با موفقیت از سیستم خارج شدید');
    } else {
        alert('با موفقیت از سیستم خارج شدید');
    }
}

// اتصال فرم ورود
function setupAuthListeners() {
    console.log('Setting up auth listeners...');
    const authForm = document.getElementById('authForm');
    if (authForm) {
        authForm.addEventListener('submit', async (event) => {
            event.preventDefault();
            
            const username = document.getElementById('username').value;
            const password = document.getElementById('password').value;
            const loginError = document.getElementById('loginError');
            
            if (loginError) {
                loginError.style.display = 'none';
            }
            
            try {
                // نمایش وضعیت بارگذاری
                const submitBtn = authForm.querySelector('button[type="submit"]');
                const originalBtnText = submitBtn.innerHTML;
                submitBtn.disabled = true;
                submitBtn.innerHTML = '<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> در حال ورود...';
                
                await login(username, password);
                const authenticated = await checkAuthStatus();
                
                if (authenticated) {
                    if (typeof window.showPage === 'function') {
                        window.showPage('dashboard');
                    }
                    if (typeof window.showSuccessMessage === 'function') {
                        window.showSuccessMessage('به سیستم رصد خوش آمدید');
                    } else {
                        alert('به سیستم رصد خوش آمدید');
                    }
                }
            } catch (error) {
                if (loginError) {
                    loginError.textContent = error.message;
                    loginError.style.display = 'block';
                } else if (typeof window.showErrorMessage === 'function') {
                    window.showErrorMessage(error.message);
                } else {
                    alert('خطا: ' + error.message);
                }
            } finally {
                // بازگرداندن وضعیت دکمه
                const submitBtn = authForm.querySelector('button[type="submit"]');
                if (submitBtn) {
                    submitBtn.disabled = false;
                    submitBtn.innerHTML = '<i class="bi bi-box-arrow-in-right"></i> ورود';
                }
            }
        });
    }
    
    // اضافه کردن اخطار حالت توسعه در صفحه ورود
    if (DEV_MODE) {
        const loginForm = document.getElementById('loginForm');
        if (loginForm) {
            const devModeAlert = document.createElement('div');
            devModeAlert.className = 'alert alert-warning mb-3';
            devModeAlert.innerHTML = `
                <i class="bi bi-exclamation-triangle-fill"></i>
                <strong>حالت توسعه فعال است.</strong> احراز هویت غیرفعال شده و می‌توانید بدون ورود از سیستم استفاده کنید.
                <button class="btn btn-sm btn-warning ms-2" id="skipLoginBtn">ورود بدون احراز هویت</button>
            `;
            
            const authForm = loginForm.querySelector('#authForm');
            if (authForm) {
                authForm.parentNode.insertBefore(devModeAlert, authForm);
                
                // دکمه ورود بدون احراز هویت
                document.getElementById('skipLoginBtn').addEventListener('click', async () => {
                    await login('dev', 'dev');
                    await checkAuthStatus();
                    
                    if (typeof window.showPage === 'function') {
                        window.showPage('dashboard');
                    }
                });
            }
        }
    }
    
    console.log('Auth listeners setup complete');
}

// اطمینان از دسترسی‌پذیری توابع
window.login = login;
window.checkAuthStatus = checkAuthStatus;
window.logout = logout;
window.setupAuthListeners = setupAuthListeners;

// اجرای خودکار setUp برای اطمینان از آماده بودن
document.addEventListener('DOMContentLoaded', () => {
    console.log('Auth module loaded');
});