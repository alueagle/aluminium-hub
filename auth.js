// Aluminium Hub - Authentication System
// نظام المصادقة والتسجيل

// User database
const USERS = {
    'admin': {
        password: 'admin123',
        role: 'admin',
        name: 'مدير النظام',
        permissions: ['admin', 'manage_stock', 'manage_users', 'view_reports', 'print_labels'],
        redirect: 'admin_dashboard.html'
    },
    'worker1': {
        password: 'worker123',
        role: 'worker',
        name: 'صنايعي 1',
        permissions: ['scan', 'cut', 'view_stock', 'waste_management'],
        redirect: 'mobile_technician_app.html'
    },
    'worker2': {
        password: 'worker123',
        role: 'worker',
        name: 'صنايعي 2',
        permissions: ['scan', 'cut', 'view_stock', 'waste_management'],
        redirect: 'mobile_technician_app.html'
    },
    'supervisor': {
        password: 'super123',
        role: 'supervisor',
        name: 'مشرف الورشة',
        permissions: ['supervisor', 'scan', 'cut', 'view_reports', 'manage_stock'],
        redirect: 'admin_dashboard.html'
    }
};

// Session management
class AuthManager {
    constructor() {
        this.currentUser = null;
        this.sessionTimeout = 8 * 60 * 60 * 1000; // 8 hours
        this.init();
    }

    init() {
        // Check existing session
        this.checkExistingSession();
        
        // Setup auto-logout
        this.setupAutoLogout();
        
        // Setup session monitoring
        this.setupSessionMonitoring();
    }

    // Check if user is already logged in
    checkExistingSession() {
        const savedUser = localStorage.getItem('currentUser');
        const rememberMe = localStorage.getItem('rememberMe');
        const loginTime = localStorage.getItem('loginTime');
        
        if (savedUser && rememberMe === 'true') {
            // Check if session is still valid
            if (loginTime && (Date.now() - parseInt(loginTime)) < this.sessionTimeout) {
                this.currentUser = JSON.parse(savedUser);
                return true;
            } else {
                // Session expired
                this.logout();
            }
        }
        return false;
    }

    // Login user
    login(username, password, rememberMe = false) {
        const user = USERS[username];
        
        if (!user || user.password !== password) {
            throw new Error('اسم المستخدم أو كلمة المرور غير صحيحة');
        }

        // Create user session
        const session = {
            username: username,
            role: user.role,
            name: user.name,
            permissions: user.permissions,
            loginTime: new Date().toISOString(),
            rememberMe: rememberMe
        };

        // Save session
        this.currentUser = session;
        localStorage.setItem('currentUser', JSON.stringify(session));
        localStorage.setItem('rememberMe', rememberMe.toString());
        localStorage.setItem('loginTime', Date.now().toString());

        return session;
    }

    // Logout user
    logout() {
        this.currentUser = null;
        localStorage.removeItem('currentUser');
        localStorage.removeItem('rememberMe');
        localStorage.removeItem('loginTime');
        
        // Redirect to login
        if (window.location.pathname !== '/login.html') {
            window.location.href = 'login.html';
        }
    }

    // Check if user has specific permission
    hasPermission(permission) {
        if (!this.currentUser) return false;
        return this.currentUser.permissions.includes(permission);
    }

    // Check if user has admin role
    isAdmin() {
        return this.currentUser && this.currentUser.role === 'admin';
    }

    // Check if user is worker
    isWorker() {
        return this.currentUser && this.currentUser.role === 'worker';
    }

    // Get current user info
    getCurrentUser() {
        return this.currentUser;
    }

    // Setup auto-logout
    setupAutoLogout() {
        setInterval(() => {
            const loginTime = localStorage.getItem('loginTime');
            if (loginTime && (Date.now() - parseInt(loginTime)) > this.sessionTimeout) {
                this.logout();
            }
        }, 60000); // Check every minute
    }

    // Setup session monitoring
    setupSessionMonitoring() {
        // Listen for storage changes (for multi-tab support)
        window.addEventListener('storage', (e) => {
            if (e.key === 'currentUser') {
                if (!e.newValue) {
                    // User logged out in another tab
                    this.logout();
                }
            }
        });

        // Listen for visibility changes
        document.addEventListener('visibilitychange', () => {
            if (!document.hidden && this.currentUser) {
                // Check if session is still valid when tab becomes visible
                this.checkExistingSession();
            }
        });
    }

    // Extend session
    extendSession() {
        if (this.currentUser) {
            localStorage.setItem('loginTime', Date.now().toString());
        }
    }

    // Get session time remaining
    getSessionTimeRemaining() {
        const loginTime = localStorage.getItem('loginTime');
        if (!loginTime) return 0;
        
        const elapsed = Date.now() - parseInt(loginTime);
        return Math.max(0, this.sessionTimeout - elapsed);
    }

    // Format session time
    formatSessionTime(remainingMs) {
        const hours = Math.floor(remainingMs / (1000 * 60 * 60));
        const minutes = Math.floor((remainingMs % (1000 * 60 * 60)) / (1000 * 60));
        
        if (hours > 0) {
            return `${hours} ساعة و ${minutes} دقيقة`;
        } else {
            return `${minutes} دقيقة`;
        }
    }
}

// Create global auth instance
const auth = new AuthManager();

// Authentication middleware for pages
function requireAuth() {
    if (!auth.getCurrentUser()) {
        window.location.href = 'login.html';
        return false;
    }
    return true;
}

// Role-based access control
function requireRole(role) {
    if (!auth.getCurrentUser()) {
        window.location.href = 'login.html';
        return false;
    }
    
    if (auth.getCurrentUser().role !== role && !auth.isAdmin()) {
        alert('ليس لديك صلاحية للوصول إلى هذه الصفحة');
        return false;
    }
    
    return true;
}

// Permission-based access control
function requirePermission(permission) {
    if (!auth.getCurrentUser()) {
        window.location.href = 'login.html';
        return false;
    }
    
    if (!auth.hasPermission(permission)) {
        alert('ليس لديك صلاحية للقيام بهذه العملية');
        return false;
    }
    
    return true;
}

// Initialize user interface
function initializeUserInterface() {
    const currentUser = auth.getCurrentUser();
    if (!currentUser) return;

    // Update user info display
    const userNameElements = document.querySelectorAll('.current-user-name');
    const userRoleElements = document.querySelectorAll('.current-user-role');
    
    userNameElements.forEach(el => {
        el.textContent = currentUser.name;
    });
    
    userRoleElements.forEach(el => {
        const roleNames = {
            'admin': 'مدير النظام',
            'worker': 'صنايعي',
            'supervisor': 'مشرف الورشة'
        };
        el.textContent = roleNames[currentUser.role] || currentUser.role;
    });

    // Setup logout buttons
    const logoutButtons = document.querySelectorAll('.logout-btn');
    logoutButtons.forEach(btn => {
        btn.addEventListener('click', (e) => {
            e.preventDefault();
            if (confirm('هل أنت متأكد من تسجيل الخروج؟')) {
                auth.logout();
            }
        });
    });

    // Setup role-based UI elements
    setupRoleBasedUI();
}

// Setup role-based UI elements
function setupRoleBasedUI() {
    const currentUser = auth.getCurrentUser();
    if (!currentUser) return;

    // Hide/show elements based on permissions
    const adminOnlyElements = document.querySelectorAll('.admin-only');
    const workerOnlyElements = document.querySelectorAll('.worker-only');
    const supervisorOnlyElements = document.querySelectorAll('.supervisor-only');

    adminOnlyElements.forEach(el => {
        el.style.display = auth.isAdmin() ? '' : 'none';
    });

    workerOnlyElements.forEach(el => {
        el.style.display = auth.isWorker() ? '' : 'none';
    });

    supervisorOnlyElements.forEach(el => {
        el.style.display = currentUser.role === 'supervisor' || auth.isAdmin() ? '' : 'none';
    });
}

// Session timeout warning
function setupSessionTimeoutWarning() {
    setInterval(() => {
        const remaining = auth.getSessionTimeRemaining();
        const warningTime = 5 * 60 * 1000; // 5 minutes before timeout

        if (remaining > 0 && remaining < warningTime) {
            showSessionWarning(remaining);
        }
    }, 30000); // Check every 30 seconds
}

// Show session timeout warning
function showSessionWarning(remainingMs) {
    const warningDiv = document.createElement('div');
    warningDiv.className = 'fixed top-4 right-4 bg-yellow-500 text-white px-6 py-3 rounded-lg shadow-lg z-50 fade-in';
    warningDiv.innerHTML = `
        <div class="flex items-center">
            <svg class="w-5 h-5 ml-2" fill="currentColor" viewBox="0 0 20 20">
                <path fill-rule="evenodd" d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z" clip-rule="evenodd"></path>
            </svg>
            <div>
                <p class="font-medium">تنبيه انتهاء الجلسة</p>
                <p class="text-sm">متبقي ${auth.formatSessionTime(remainingMs)} على انتهاء الجلسة</p>
                <button onclick="auth.extendSession(); this.parentElement.parentElement.parentElement.remove();" class="mt-2 bg-white text-yellow-600 px-3 py-1 rounded text-sm">
                    تمديد الجلسة
                </button>
            </div>
        </div>
    `;
    document.body.appendChild(warningDiv);

    // Auto-remove after 10 seconds
    setTimeout(() => {
        if (warningDiv.parentElement) {
            warningDiv.remove();
        }
    }, 10000);
}

// Export for global use
window.auth = auth;
window.requireAuth = requireAuth;
window.requireRole = requireRole;
window.requirePermission = requirePermission;
window.initializeUserInterface = initializeUserInterface;

// Initialize on page load
document.addEventListener('DOMContentLoaded', function() {
    initializeUserInterface();
    setupSessionTimeoutWarning();
});
