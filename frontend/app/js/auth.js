// auth.js - مدیریت احراز هویت

// ورود به سیستم
async function login(username, password) {
    try {
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
        api.setToken(data.access_token);
        
        return true;
    } catch (error) {
        console.error('Login error:', error);
        throw error;
    }
}

// بررسی وضعیت احراز هویت
async function checkAuthStatus() {
    if (!api.token) {
        return false;
    }

    try {
        const userData = await api.get('/api/v1/auth/me');
        
        // نمایش اطلاعات کاربر در منو
        const userDisplayName = document.getElementById('userDisplayName');
        if (userDisplayName) {
            userDisplayName.textContent = userData.email || userData.full_name || 'کاربر';
        }
        
        return true;
    } catch (error) {
        console.error('Auth check error:', error);
        api.clearToken();
        return false;
    }
}

// خروج از سیستم
function logout() {
    api.clearToken();
    
    // بازگشت به صفحه ورود
    showPage('login');
    
    // بازنشانی نام کاربر در منو
    const userDisplayName = document.getElementById('userDisplayName');
    if (userDisplayName) {
        userDisplayName.textContent = 'ورود';
    }
    
    // نمایش پیام خروج
    showSuccessMessage('با موفقیت از سیستم خارج شدید');
}

// اتصال فرم ورود
function setupAuthListeners() {
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
                    showPage('dashboard');
                    showSuccessMessage('به سیستم رصد خوش آمدید');
                }
            } catch (error) {
                if (loginError) {
                    loginError.textContent = error.message;
                    loginError.style.display = 'block';
                } else {
                    showErrorMessage(error.message);
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
}

// صادرات توابع عمومی
window.login = login;
window.checkAuthStatus = checkAuthStatus;
window.logout = logout;
window.setupAuthListeners = setupAuthListeners;