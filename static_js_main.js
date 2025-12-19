/**
 * Bite Me Buddy - Main JavaScript File
 * Common functions and utilities used across the application
 */

// Global application state
const AppState = {
    user: null,
    cart: {},
    notifications: [],
    isOnline: true,
    apiBaseUrl: window.location.origin,
    
    // Initialize application
    init: function() {
        this.loadUser();
        this.loadCart();
        this.setupEventListeners();
        this.setupHTMX();
        this.checkOnlineStatus();
        this.setupServiceWorker();
    },
    
    // Load user data from cookies/localStorage
    loadUser: function() {
        try {
            const userData = localStorage.getItem('bite_me_buddy_user');
            if (userData) {
                this.user = JSON.parse(userData);
                this.updateUIForUser();
            }
        } catch (error) {
            console.error('Error loading user data:', error);
        }
    },
    
    // Update UI based on user state
    updateUIForUser: function() {
        // Update user info in header
        const userElements = document.querySelectorAll('.user-info');
        userElements.forEach(element => {
            if (this.user) {
                element.innerHTML = `
                    <div class="user-avatar">${this.user.name.charAt(0)}</div>
                    <div class="user-details">
                        <div class="user-name">${this.user.name}</div>
                        <div class="user-role badge bg-primary">${this.user.role}</div>
                    </div>
                `;
            } else {
                element.innerHTML = '<a href="/auth/login" class="btn btn-outline-primary">Login</a>';
            }
        });
        
        // Update navigation based on role
        this.updateNavigation();
    },
    
    // Update navigation based on user role
    updateNavigation: function() {
        const navLinks = document.querySelectorAll('.nav-link');
        navLinks.forEach(link => {
            const role = link.dataset.role;
            if (role && this.user && this.user.role !== role) {
                link.style.display = 'none';
            } else if (role && (!this.user || this.user.role !== role)) {
                // Already hidden by default in HTML
            } else {
                link.style.display = 'block';
            }
        });
    },
    
    // Load cart from localStorage
    loadCart: function() {
        try {
            const cartData = localStorage.getItem('bite_me_buddy_cart');
            if (cartData) {
                this.cart = JSON.parse(cartData);
                this.updateCartBadge();
            }
        } catch (error) {
            console.error('Error loading cart:', error);
            this.cart = {};
        }
    },
    
    // Save cart to localStorage
    saveCart: function() {
        try {
            localStorage.setItem('bite_me_buddy_cart', JSON.stringify(this.cart));
            this.updateCartBadge();
        } catch (error) {
            console.error('Error saving cart:', error);
        }
    },
    
    // Update cart badge count
    updateCartBadge: function() {
        const cartCount = Object.keys(this.cart).length;
        const badges = document.querySelectorAll('.cart-badge');
        badges.forEach(badge => {
            badge.textContent = cartCount;
            badge.style.display = cartCount > 0 ? 'inline-block' : 'none';
        });
        
        // Update cart total
        const cartTotal = this.calculateCartTotal();
        const totalElements = document.querySelectorAll('.cart-total');
        totalElements.forEach(element => {
            element.textContent = `₹${cartTotal.toFixed(2)}`;
        });
    },
    
    // Calculate cart total
    calculateCartTotal: function() {
        return Object.values(this.cart).reduce((total, item) => {
            return total + (item.price * item.quantity);
        }, 0);
    },
    
    // Add item to cart
    addToCart: function(itemId, itemData) {
        if (this.cart[itemId]) {
            this.cart[itemId].quantity += itemData.quantity || 1;
        } else {
            this.cart[itemId] = {
                ...itemData,
                quantity: itemData.quantity || 1
            };
        }
        this.saveCart();
        this.showNotification('Item added to cart', 'success');
    },
    
    // Remove item from cart
    removeFromCart: function(itemId) {
        if (this.cart[itemId]) {
            delete this.cart[itemId];
            this.saveCart();
            this.showNotification('Item removed from cart', 'info');
        }
    },
    
    // Update cart item quantity
    updateCartItem: function(itemId, quantity) {
        if (this.cart[itemId]) {
            if (quantity <= 0) {
                this.removeFromCart(itemId);
            } else {
                this.cart[itemId].quantity = quantity;
                this.saveCart();
            }
        }
    },
    
    // Clear cart
    clearCart: function() {
        this.cart = {};
        this.saveCart();
        this.showNotification('Cart cleared', 'info');
    },
    
    // Show notification
    showNotification: function(message, type = 'info', duration = 5000) {
        const notification = {
            id: Date.now(),
            message,
            type,
            duration
        };
        
        this.notifications.push(notification);
        this.displayNotification(notification);
    },
    
    // Display notification in UI
    displayNotification: function(notification) {
        const container = document.getElementById('notification-container') || this.createNotificationContainer();
        
        const notificationElement = document.createElement('div');
        notificationElement.className = `notification alert alert-${notification.type}`;
        notificationElement.id = `notification-${notification.id}`;
        notificationElement.innerHTML = `
            <span>${notification.message}</span>
            <button type="button" class="btn-close" onclick="AppState.removeNotification(${notification.id})"></button>
        `;
        
        container.appendChild(notificationElement);
        
        // Auto-remove after duration
        setTimeout(() => {
            this.removeNotification(notification.id);
        }, notification.duration);
    },
    
    // Create notification container if it doesn't exist
    createNotificationContainer: function() {
        const container = document.createElement('div');
        container.id = 'notification-container';
        container.className = 'notification-container';
        container.style.cssText = `
            position: fixed;
            top: 20px;
            right: 20px;
            z-index: 9999;
            max-width: 300px;
        `;
        document.body.appendChild(container);
        return container;
    },
    
    // Remove notification
    removeNotification: function(notificationId) {
        const element = document.getElementById(`notification-${notificationId}`);
        if (element) {
            element.style.opacity = '0';
            element.style.transform = 'translateX(100%)';
            setTimeout(() => element.remove(), 300);
        }
        
        this.notifications = this.notifications.filter(n => n.id !== notificationId);
    },
    
    // Check online status
    checkOnlineStatus: function() {
        this.isOnline = navigator.onLine;
        
        if (!this.isOnline) {
            this.showNotification('You are offline. Some features may not work.', 'warning');
        }
        
        // Listen for online/offline events
        window.addEventListener('online', () => {
            this.isOnline = true;
            this.showNotification('You are back online', 'success');
        });
        
        window.addEventListener('offline', () => {
            this.isOnline = false;
            this.showNotification('You are offline. Some features may not work.', 'warning');
        });
    },
    
    // Setup service worker for PWA
    setupServiceWorker: function() {
        if ('serviceWorker' in navigator) {
            window.addEventListener('load', () => {
                navigator.serviceWorker.register('/static/js/service-worker.js')
                    .then(registration => {
                        console.log('ServiceWorker registered:', registration);
                    })
                    .catch(error => {
                        console.log('ServiceWorker registration failed:', error);
                    });
            });
        }
    },
    
    // Setup event listeners
    setupEventListeners: function() {
        // Logout button
        document.addEventListener('click', (e) => {
            if (e.target.closest('.logout-btn')) {
                e.preventDefault();
                this.logout();
            }
        });
        
        // Add to cart buttons
        document.addEventListener('click', (e) => {
            const addToCartBtn = e.target.closest('.add-to-cart');
            if (addToCartBtn) {
                e.preventDefault();
                const itemId = addToCartBtn.dataset.itemId;
                const itemData = {
                    name: addToCartBtn.dataset.itemName,
                    price: parseFloat(addToCartBtn.dataset.itemPrice),
                    image: addToCartBtn.dataset.itemImage
                };
                this.addToCart(itemId, itemData);
            }
        });
        
        // Keyboard shortcuts
        document.addEventListener('keydown', (e) => {
            // Ctrl/Cmd + S to save
            if ((e.ctrlKey || e.metaKey) && e.key === 's') {
                e.preventDefault();
                this.saveCurrentForm();
            }
            
            // Escape to close modals
            if (e.key === 'Escape') {
                this.closeAllModals();
            }
        });
    },
    
    // Setup HTMX event handlers
    setupHTMX: function() {
        // Before request
        document.body.addEventListener('htmx:beforeRequest', (e) => {
            const target = e.target;
            target.classList.add('loading');
            
            // Show loading indicator
            if (target.dataset.loadingIndicator) {
                const indicator = document.querySelector(target.dataset.loadingIndicator);
                if (indicator) indicator.style.display = 'block';
            }
        });
        
        // After request
        document.body.addEventListener('htmx:afterRequest', (e) => {
            const target = e.target;
            target.classList.remove('loading');
            
            // Hide loading indicator
            if (target.dataset.loadingIndicator) {
                const indicator = document.querySelector(target.dataset.loadingIndicator);
                if (indicator) indicator.style.display = 'none';
            }
            
            // Handle redirects
            if (e.detail.xhr.status === 303) {
                const redirectUrl = e.detail.xhr.getResponseHeader('Location');
                if (redirectUrl) {
                    window.location.href = redirectUrl;
                }
            }
        });
        
        // On error
        document.body.addEventListener('htmx:responseError', (e) => {
            this.showNotification('An error occurred. Please try again.', 'error');
            console.error('HTMX Error:', e.detail);
        });
    },
    
    // Save current form (generic)
    saveCurrentForm: function() {
        const activeForm = document.querySelector('form:focus-within');
        if (activeForm && activeForm.checkValidity()) {
            if (activeForm.hasAttribute('hx-post')) {
                htmx.trigger(activeForm, 'submit');
            } else {
                activeForm.submit();
            }
        }
    },
    
    // Close all modals
    closeAllModals: function() {
        const modals = document.querySelectorAll('.modal');
        modals.forEach(modal => {
            const modalInstance = bootstrap.Modal.getInstance(modal);
            if (modalInstance) modalInstance.hide();
        });
    },
    
    // Logout user
    logout: function() {
        fetch('/auth/logout', {
            method: 'GET',
            credentials: 'include'
        })
        .then(response => {
            if (response.ok) {
                localStorage.removeItem('bite_me_buddy_user');
                localStorage.removeItem('bite_me_buddy_cart');
                this.user = null;
                this.cart = {};
                this.updateUIForUser();
                this.showNotification('Logged out successfully', 'success');
                setTimeout(() => {
                    window.location.href = '/';
                }, 1000);
            }
        })
        .catch(error => {
            console.error('Logout error:', error);
            this.showNotification('Error logging out', 'error');
        });
    },
    
    // Format currency
    formatCurrency: function(amount) {
        return new Intl.NumberFormat('en-IN', {
            style: 'currency',
            currency: 'INR',
            minimumFractionDigits: 2
        }).format(amount);
    },
    
    // Format date
    formatDate: function(dateString, format = 'medium') {
        const date = new Date(dateString);
        const options = {
            dateStyle: format,
            timeStyle: format === 'date' ? undefined : 'short'
        };
        return new Intl.DateTimeFormat('en-IN', options).format(date);
    },
    
    // Validate email
    validateEmail: function(email) {
        const re = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
        return re.test(email);
    },
    
    // Validate phone number (Indian)
    validatePhone: function(phone) {
        const re = /^[6-9]\d{9}$/;
        return re.test(phone.replace(/\D/g, ''));
    },
    
    // Debounce function
    debounce: function(func, wait) {
        let timeout;
        return function executedFunction(...args) {
            const later = () => {
                clearTimeout(timeout);
                func(...args);
            };
            clearTimeout(timeout);
            timeout = setTimeout(later, wait);
        };
    },
    
    // Throttle function
    throttle: function(func, limit) {
        let inThrottle;
        return function() {
            const args = arguments;
            const context = this;
            if (!inThrottle) {
                func.apply(context, args);
                inThrottle = true;
                setTimeout(() => inThrottle = false, limit);
            }
        };
    },
    
    // Get query parameters
    getQueryParams: function() {
        const params = {};
        const queryString = window.location.search.substring(1);
        const pairs = queryString.split('&');
        
        pairs.forEach(pair => {
            const [key, value] = pair.split('=');
            if (key) {
                params[decodeURIComponent(key)] = decodeURIComponent(value || '');
            }
        });
        
        return params;
    },
    
    // Update query parameters
    updateQueryParams: function(params) {
        const url = new URL(window.location);
        Object.entries(params).forEach(([key, value]) => {
            if (value === null || value === undefined) {
                url.searchParams.delete(key);
            } else {
                url.searchParams.set(key, value);
            }
        });
        window.history.pushState({}, '', url);
    }
};

// Initialize app when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    AppState.init();
});

// Make AppState globally available
window.AppState = AppState;

// HTMX configuration
document.addEventListener('DOMContentLoaded', function() {
    // Configure HTMX
    htmx.config.includeIndicatorStyles = false;
    htmx.config.indicatorClass = 'htmx-indicator';
    htmx.config.requestClass = 'htmx-request';
    htmx.config.addedClass = 'htmx-added';
    htmx.config.settlingClass = 'htmx-settling';
    htmx.config.swappingClass = 'htmx-swapping';
    
    // Add loading indicator styles
    const style = document.createElement('style');
    style.textContent = `
        .htmx-indicator {
            opacity: 0;
            transition: opacity 200ms ease-in;
        }
        .htmx-request .htmx-indicator {
            opacity: 1;
        }
        .htmx-request.htmx-indicator {
            opacity: 1;
        }
        .loading {
            position: relative;
            opacity: 0.7;
            pointer-events: none;
        }
        .loading::after {
            content: '';
            position: absolute;
            top: 50%;
            left: 50%;
            width: 20px;
            height: 20px;
            margin: -10px 0 0 -10px;
            border: 2px solid #ff6b35;
            border-top-color: transparent;
            border-radius: 50%;
            animation: spin 1s linear infinite;
        }
    `;
    document.head.appendChild(style);
});

// Bootstrap tooltip initialization
document.addEventListener('DOMContentLoaded', function() {
    var tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    var tooltipList = tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });
});

// Bootstrap popover initialization
document.addEventListener('DOMContentLoaded', function() {
    var popoverTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="popover"]'));
    var popoverList = popoverTriggerList.map(function (popoverTriggerEl) {
        return new bootstrap.Popover(popoverTriggerEl);
    });
});

// Form validation enhancement
document.addEventListener('DOMContentLoaded', function() {
    // Add custom validation to forms
    const forms = document.querySelectorAll('form[novalidate]');
    forms.forEach(form => {
        form.addEventListener('submit', function(event) {
            if (!form.checkValidity()) {
                event.preventDefault();
                event.stopPropagation();
            }
            
            form.classList.add('was-validated');
        }, false);
    });
    
    // Real-time validation
    const inputs = document.querySelectorAll('input[pattern], input[type="email"], input[type="tel"]');
    inputs.forEach(input => {
        input.addEventListener('input', function() {
            if (input.validity.valid) {
                input.classList.remove('is-invalid');
                input.classList.add('is-valid');
            } else {
                input.classList.remove('is-valid');
                input.classList.add('is-invalid');
            }
        });
    });
});

// Mobile menu toggle
document.addEventListener('DOMContentLoaded', function() {
    const menuToggle = document.querySelector('.menu-toggle');
    const navLinks = document.querySelector('.nav-links');
    
    if (menuToggle && navLinks) {
        menuToggle.addEventListener('click', function() {
            navLinks.classList.toggle('show');
        });
        
        // Close menu when clicking outside
        document.addEventListener('click', function(event) {
            if (!menuToggle.contains(event.target) && !navLinks.contains(event.target)) {
                navLinks.classList.remove('show');
            }
        });
    }
});

// Lazy loading images
document.addEventListener('DOMContentLoaded', function() {
    const lazyImages = document.querySelectorAll('img[data-src]');
    
    const imageObserver = new IntersectionObserver((entries, observer) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                const img = entry.target;
                img.src = img.dataset.src;
                img.removeAttribute('data-src');
                observer.unobserve(img);
            }
        });
    });
    
    lazyImages.forEach(img => imageObserver.observe(img));
});

// Back to top button
document.addEventListener('DOMContentLoaded', function() {
    const backToTop = document.createElement('button');
    backToTop.id = 'back-to-top';
    backToTop.className = 'btn btn-primary';
    backToTop.innerHTML = '<i class="fas fa-arrow-up"></i>';
    backToTop.style.cssText = `
        position: fixed;
        bottom: 20px;
        right: 20px;
        width: 50px;
        height: 50px;
        border-radius: 50%;
        display: none;
        z-index: 1000;
    `;
    document.body.appendChild(backToTop);
    
    window.addEventListener('scroll', function() {
        if (window.pageYOffset > 300) {
            backToTop.style.display = 'block';
        } else {
            backToTop.style.display = 'none';
        }
    });
    
    backToTop.addEventListener('click', function() {
        window.scrollTo({
            top: 0,
            behavior: 'smooth'
        });
    });
});

// Session timeout warning
let sessionTimeout;
document.addEventListener('DOMContentLoaded', function() {
    // Set timeout for 25 minutes (session expires in 30 minutes)
    const timeoutMinutes = 25;
    
    function resetTimeout() {
        clearTimeout(sessionTimeout);
        sessionTimeout = setTimeout(showTimeoutWarning, timeoutMinutes * 60 * 1000);
    }
    
    function showTimeoutWarning() {
        if (AppState.user) {
            AppState.showNotification(
                `Your session will expire in 5 minutes. Click to extend.`,
                'warning',
                300000 // 5 minutes
            );
            
            // Add click to extend functionality
            const notification = document.querySelector('.notification');
            if (notification) {
                notification.style.cursor = 'pointer';
                notification.addEventListener('click', extendSession);
            }
        }
    }
    
    function extendSession() {
        fetch('/api/auth/extend-session', {
            method: 'POST',
            credentials: 'include'
        })
        .then(response => {
            if (response.ok) {
                AppState.showNotification('Session extended', 'success');
                resetTimeout();
            }
        })
        .catch(error => {
            console.error('Error extending session:', error);
        });
    }
    
    // Reset timeout on user activity
    ['mousemove', 'keypress', 'click', 'scroll'].forEach(event => {
        document.addEventListener(event, resetTimeout);
    });
    
    // Initialize timeout
    resetTimeout();
});

// Export utilities for use in other modules
window.AppUtils = {
    formatCurrency: AppState.formatCurrency.bind(AppState),
    formatDate: AppState.formatDate.bind(AppState),
    validateEmail: AppState.validateEmail,
    validatePhone: AppState.validatePhone,
    debounce: AppState.debounce,
    throttle: AppState.throttle
};