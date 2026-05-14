/**
 * Authentication Helper
 * Manages JWT tokens and auth state
 */

const AUTH_TOKEN_KEY = 'access_token';
const REFRESH_TOKEN_KEY = 'refresh_token';
const USER_KEY = 'user';

class Auth {
    constructor() {
        this.init();
    }

    init() {
        // Update UI based on auth state
        this.updateUI();
        
        // Set up logout handler
        const logoutLink = document.getElementById('logout-link');
        if (logoutLink) {
            logoutLink.addEventListener('click', (e) => {
                e.preventDefault();
                this.logout();
            });
        }
    }

    isAuthenticated() {
        return !!localStorage.getItem(AUTH_TOKEN_KEY);
    }

    getToken() {
        return localStorage.getItem(AUTH_TOKEN_KEY);
    }

    getRefreshToken() {
        return localStorage.getItem(REFRESH_TOKEN_KEY);
    }

    getUser() {
        const userStr = localStorage.getItem(USER_KEY);
        return userStr ? JSON.parse(userStr) : null;
    }

    setTokens(accessToken, refreshToken, user) {
        localStorage.setItem(AUTH_TOKEN_KEY, accessToken);
        localStorage.setItem(REFRESH_TOKEN_KEY, refreshToken);
        localStorage.setItem(USER_KEY, JSON.stringify(user));
        this.updateUI();
    }

    clearTokens() {
        localStorage.removeItem(AUTH_TOKEN_KEY);
        localStorage.removeItem(REFRESH_TOKEN_KEY);
        localStorage.removeItem(USER_KEY);
        this.updateUI();
    }

    logout() {
        this.clearTokens();
        window.location.href = '/';
    }

    updateUI() {
        const isAuth = this.isAuthenticated();
        const user = this.getUser();
        
        // Show/hide navigation items
        const loginLink = document.getElementById('login-link');
        const registerLink = document.getElementById('register-link');
        const userMenu = document.getElementById('user-menu');
        const dashboardLink = document.getElementById('dashboard-link');
        const templatesLink = document.getElementById('templates-link');
        const logsLink = document.getElementById('logs-link');
        const preferencesLink = document.getElementById('preferences-link');
        const testingMenu = document.getElementById('testing-menu');
        
        if (loginLink) loginLink.style.display = isAuth ? 'none' : 'block';
        if (registerLink) registerLink.style.display = isAuth ? 'none' : 'block';
        if (userMenu) userMenu.style.display = isAuth ? 'block' : 'none';
        if (dashboardLink) dashboardLink.style.display = isAuth ? 'block' : 'none';
        if (templatesLink) templatesLink.style.display = isAuth ? 'block' : 'none';
        if (logsLink) logsLink.style.display = isAuth ? 'block' : 'none';
        if (preferencesLink) preferencesLink.style.display = isAuth ? 'block' : 'none';
        if (testingMenu) testingMenu.style.display = isAuth ? 'block' : 'none';
        
        // Update username display
        if (user && isAuth) {
            const usernameDisplay = document.getElementById('username-display');
            if (usernameDisplay) {
                usernameDisplay.textContent = user.username;
            }
        }
    }

    async apiRequest(url, options = {}) {
        const token = this.getToken();
        
        const headers = {
            'Content-Type': 'application/json',
            ...options.headers
        };
        
        if (token) {
            headers['Authorization'] = `Bearer ${token}`;
        }
        
        const response = await fetch(url, {
            ...options,
            headers
        });
        
        // Handle token errors
        if (response.status === 422) {
            // Invalid token - clear and redirect
            console.error('Invalid token detected, clearing auth...');
            this.clearTokens();
            window.location.href = '/login?error=invalid_token';
            throw new Error('Invalid token');
        }
        
        // If unauthorized, try to refresh token
        if (response.status === 401 && token) {
            const refreshed = await this.refreshToken();
            if (refreshed) {
                // Retry request with new token
                headers['Authorization'] = `Bearer ${this.getToken()}`;
                return fetch(url, { ...options, headers });
            } else {
                // Refresh failed, logout
                this.logout();
                throw new Error('Session expired');
            }
        }
        
        return response;
    }

    async refreshToken() {
        const refreshToken = this.getRefreshToken();
        if (!refreshToken) return false;
        
        try {
            const response = await fetch('/api/v1/auth/refresh', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${refreshToken}`
                }
            });
            
            if (response.ok) {
                const data = await response.json();
                localStorage.setItem(AUTH_TOKEN_KEY, data.access_token);
                return true;
            }
        } catch (error) {
            console.error('Token refresh failed:', error);
        }
        
        return false;
    }

    requireAuth() {
        if (!this.isAuthenticated()) {
            window.location.href = '/login';
            return false;
        }
        return true;
    }

    showAlert(message, type = 'info') {
        const alertHtml = `
            <div class="alert alert-${type} alert-dismissible fade show" role="alert">
                ${message}
                <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
            </div>
        `;
        
        // Find or create alert container
        let container = document.getElementById('alert-container');
        if (!container) {
            container = document.createElement('div');
            container.id = 'alert-container';
            container.className = 'container mt-3';
            const main = document.querySelector('main');
            if (main) {
                main.prepend(container);
            } else {
                document.body.prepend(container);
            }
        }
        
        container.innerHTML = alertHtml;
        
        // Auto-dismiss after 5 seconds
        setTimeout(() => {
            const alert = container.querySelector('.alert');
            if (alert) {
                const bsAlert = new bootstrap.Alert(alert);
                bsAlert.close();
            }
        }, 5000);
    }
}

// Create global auth instance
const auth = new Auth();

// Helper function for displaying alerts (legacy support)
function showAlert(message, type = 'info') {
    auth.showAlert(message, type);
}
