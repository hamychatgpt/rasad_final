// auth.js - مدیریت احراز هویت

// ورود به سیستم
async function login(username, password) {
    try {
        const formData = new URLSearchParams();
        formData.append('username', username);
        formData.append('password', password);
        
        const response = await fetch(`${API_BASE_URL}/auth/login`, {
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
        showPage('login');
        return false;
    }

    try {
        const userData = await api.get('/auth/me');
        document.getElementById('userDisplayName').textContent = userData.email;
        return true;
    } catch (error) {
        api.clearToken();
        showPage('login');
        return false;
    }
}

// خروج از سیستم
function logout() {
    api.clearToken();
    showPage('login');
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
            
            try {
                loginError.style.display = 'none';
                await login(username, password);
                const authenticated = await checkAuthStatus();
                
                if (authenticated) {
                    showPage('dashboard');
                }
            } catch (error) {
                loginError.textContent = error.message;
                loginError.style.display = 'block';
            }
        });
    }
}