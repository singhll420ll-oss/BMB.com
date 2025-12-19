/**
 * HTMX Event Handlers and Custom Extensions
 * Provides smooth dynamic updates without page reloads
 */

class HTMXHandlers {
    constructor() {
        this.init();
    }
    
    init() {
        this.setupGlobalHandlers();
        this.setupCustomExtensions();
        this.setupErrorHandling();
        this.setupLoadingIndicators();
        this.setupAnimations();
    }
    
    // Setup global HTMX event handlers
    setupGlobalHandlers() {
        // Before request - add CSRF token
        document.body.addEventListener('htmx:beforeRequest', (event) => {
            this.handleBeforeRequest(event);
        });
        
        // After request - handle responses
        document.body.addEventListener('htmx:afterRequest', (event) => {
            this.handleAfterRequest(event);
        });
        
        // On error
        document.body.addEventListener('htmx:responseError', (event) => {
            this.handleResponseError(event);
        });
        
        // Before swap - add animations
        document.body.addEventListener('htmx:beforeSwap', (event) => {
            this.handleBeforeSwap(event);
        });
        
        // After swap - initialize new content
        document.body.addEventListener('htmx:afterSwap', (event) => {
            this.handleAfterSwap(event);
        });
        
        // Validation
        document.body.addEventListener('htmx:validation:validate', (event) => {
            this.handleValidation(event);
        });
        
        // Confirm - for delete actions
        document.body.addEventListener('htmx:confirm', (event) => {
            this.handleConfirm(event);
        });
    }
    
    // Handle before request
    handleBeforeRequest(event) {
        const target = event.detail.elt;
        
        // Add loading class
        target.classList.add('htmx-request');
        
        // Add CSRF token if not present
        const csrfToken = this.getCSRFToken();
        if (csrfToken && event.detail.requestConfig.method !== 'GET') {
            const headers = event.detail.requestConfig.headers || {};
            headers['X-CSRF-Token'] = csrfToken;
            event.detail.requestConfig.headers = headers;
        }
        
        // Show loading indicator
        this.showLoadingIndicator(target);
        
        // Disable submit buttons to prevent double submission
        const submitButtons = target.querySelectorAll('button[type="submit"], input[type="submit"]');
        submitButtons.forEach(button => {
            button.disabled = true;
            button.classList.add('disabled');
        });
    }
    
    // Handle after request
    handleAfterRequest(event) {
        const target = event.detail.elt;
        
        // Remove loading class
        target.classList.remove('htmx-request');
        
        // Hide loading indicator
        this.hideLoadingIndicator(target);
        
        // Re-enable submit buttons
        const submitButtons = target.querySelectorAll('button[type="submit"], input[type="submit"]');
        submitButtons.forEach(button => {
            button.disabled = false;
            button.classList.remove('disabled');
        });
        
        // Handle redirects
        if (event.detail.xhr.status === 303) {
            const redirectUrl = event.detail.xhr.getResponseHeader('Location');
            if (redirectUrl) {
                setTimeout(() => {
                    window.location.href = redirectUrl;
                }, 100);
            }
        }
        
        // Handle success notifications
        if (event.detail.xhr.status >= 200 && event.detail.xhr.status < 300) {
            const successMessage = target.getAttribute('data-success-message');
            if (successMessage) {
                this.showToast(successMessage, 'success');
            }
        }
    }
    
    // Handle response error
    handleResponseError(event) {
        const target = event.detail.elt;
        const xhr = event.detail.xhr;
        
        // Remove loading class
        target.classList.remove('htmx-request');
        
        // Hide loading indicator
        this.hideLoadingIndicator(target);
        
        // Show error message
        let errorMessage = 'An error occurred';
        
        try {
            const response = JSON.parse(xhr.responseText);
            if (response.detail) {
                errorMessage = response.detail;
            } else if (response.message) {
                errorMessage = response.message;
            }
        } catch (e) {
            // If not JSON, try to get error from response text
            if (xhr.responseText) {
                errorMessage = xhr.responseText.substring(0, 100);
            }
        }
        
        this.showToast(errorMessage, 'error');
        
        // Re-enable submit buttons
        const submitButtons = target.querySelectorAll('button[type="submit"], input[type="submit"]');
        submitButtons.forEach(button => {
            button.disabled = false;
            button.classList.remove('disabled');
        });
    }
    
    // Handle before swap - add animations
    handleBeforeSwap(event) {
        const target = event.detail.target;
        
        // Add fade-out animation
        if (target && target.style) {
            target.style.opacity = '0.5';
            target.style.transition = 'opacity 0.3s ease';
        }
        
        // Handle different response types
        const contentType = event.detail.xhr.getResponseHeader('Content-Type');
        if (contentType && contentType.includes('application/json')) {
            try {
                const response = JSON.parse(event.detail.xhr.responseText);
                
                // Handle JSON responses that should redirect
                if (response.redirect) {
                    window.location.href = response.redirect;
                    event.preventDefault();
                    return;
                }
                
                // Handle JSON responses that should show modal
                if (response.modal) {
                    this.showModal(response.modal, response.title);
                    event.preventDefault();
                    return;
                }
                
                // Handle JSON responses with notifications
                if (response.notification) {
                    this.showToast(response.notification.message, response.notification.type);
                }
                
            } catch (e) {
                console.error('Error parsing JSON response:', e);
            }
        }
    }
    
    // Handle after swap - initialize new content
    handleAfterSwap(event) {
        const target = event.detail.target;
        
        // Fade in new content
        if (target && target.style) {
            target.style.opacity = '0';
            setTimeout(() => {
                target.style.opacity = '1';
                target.style.transition = 'opacity 0.3s ease';
            }, 10);
        }
        
        // Initialize Bootstrap components in new content
        this.initializeBootstrapComponents(target);
        
        // Initialize tooltips and popovers
        this.initializeTooltips(target);
        
        // Initialize form validation
        this.initializeFormValidation(target);
        
        // Initialize sorting and filtering
        this.initializeSorting(target);
        
        // Update counters and badges
        this.updateCounters();
        
        // Scroll to target if needed
        this.scrollToTarget(target);
        
        // Focus first input in forms
        this.focusFirstInput(target);
    }
    
    // Handle validation
    handleValidation(event) {
        const target = event.detail.elt;
        const value = event.detail.value;
        const validator = event.detail.validator;
        
        // Custom validation examples
        if (validator === 'email') {
            if (!this.validateEmail(value)) {
                event.detail.setCustomValidity('Please enter a valid email address');
                return;
            }
        }
        
        if (validator === 'phone') {
            if (!this.validatePhone(value)) {
                event.detail.setCustomValidity('Please enter a valid Indian phone number');
                return;
            }
        }
        
        if (validator === 'password') {
            if (value.length < 8) {
                event.detail.setCustomValidity('Password must be at least 8 characters');
                return;
            }
        }
        
        event.detail.setCustomValidity('');
    }
    
    // Handle confirm (for delete actions)
    handleConfirm(event) {
        const message = event.detail.question || 'Are you sure?';
        const confirmed = confirm(message);
        
        if (!confirmed) {
            event.preventDefault();
        }
    }
    
    // Setup custom HTMX extensions
    setupCustomExtensions() {
        // Add loading states extension
        this.addLoadingStatesExtension();
        
        // Add modal extension
        this.addModalExtension();
        
        // Add toast extension
        this.addToastExtension();
        
        // Add form reset extension
        this.addFormResetExtension();
        
        // Add poll extension for real-time updates
        this.addPollExtension();
    }
    
    // Add loading states extension
    addLoadingStatesExtension() {
        htmx.defineExtension('loading-states', {
            onEvent: function(name, evt) {
                if (name === 'htmx:beforeRequest') {
                    const target = evt.detail.elt;
                    const indicator = target.getAttribute('data-loading-indicator');
                    
                    if (indicator) {
                        const indicatorEl = document.querySelector(indicator);
                        if (indicatorEl) {
                            indicatorEl.style.display = 'block';
                        }
                    }
                }
                
                if (name === 'htmx:afterRequest') {
                    const target = evt.detail.elt;
                    const indicator = target.getAttribute('data-loading-indicator');
                    
                    if (indicator) {
                        const indicatorEl = document.querySelector(indicator);
                        if (indicatorEl) {
                            indicatorEl.style.display = 'none';
                        }
                    }
                }
            }
        });
    }
    
    // Add modal extension
    addModalExtension() {
        htmx.defineExtension('modal', {
            onEvent: function(name, evt) {
                if (name === 'htmx:afterRequest') {
                    const response = evt.detail.xhr.responseText;
                    
                    // Check if response contains modal HTML
                    if (response.includes('modal-content') || response.includes('data-bs-toggle="modal"')) {
                        // Create modal container if it doesn't exist
                        let modalContainer = document.getElementById('htmx-modal-container');
                        if (!modalContainer) {
                            modalContainer = document.createElement('div');
                            modalContainer.id = 'htmx-modal-container';
                            modalContainer.className = 'modal-container';
                            document.body.appendChild(modalContainer);
                        }
                        
                        // Insert modal HTML
                        modalContainer.innerHTML = response;
                        
                        // Initialize and show modal
                        const modalElement = modalContainer.querySelector('.modal');
                        if (modalElement) {
                            const modal = new bootstrap.Modal(modalElement);
                            modal.show();
                            
                            // Remove modal from DOM when hidden
                            modalElement.addEventListener('hidden.bs.modal', () => {
                                modalElement.remove();
                            });
                        }
                    }
                }
            }
        });
    }
    
    // Add toast extension
    addToastExtension() {
        htmx.defineExtension('toast', {
            onEvent: function(name, evt) {
                if (name === 'htmx:afterRequest') {
                    const target = evt.detail.elt;
                    const toastMessage = target.getAttribute('data-toast-message');
                    const toastType = target.getAttribute('data-toast-type') || 'info';
                    
                    if (toastMessage) {
                        // Create toast element
                        const toastId = 'toast-' + Date.now();
                        const toastHtml = `
                            <div id="${toastId}" class="toast align-items-center border-0" role="alert">
                                <div class="d-flex">
                                    <div class="toast-body">
                                        ${toastMessage}
                                    </div>
                                    <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast"></button>
                                </div>
                            </div>
                        `;
                        
                        // Add to toast container
                        let toastContainer = document.getElementById('toast-container');
                        if (!toastContainer) {
                            toastContainer = document.createElement('div');
                            toastContainer.id = 'toast-container';
                            toastContainer.className = 'toast-container position-fixed top-0 end-0 p-3';
                            document.body.appendChild(toastContainer);
                        }
                        
                        toastContainer.insertAdjacentHTML('beforeend', toastHtml);
                        
                        // Initialize and show toast
                        const toastEl = document.getElementById(toastId);
                        const toast = new bootstrap.Toast(toastEl);
                        toast.show();
                        
                        // Remove toast after it's hidden
                        toastEl.addEventListener('hidden.bs.toast', () => {
                            toastEl.remove();
                        });
                    }
                }
            }
        });
    }
    
    // Add form reset extension
    addFormResetExtension() {
        htmx.defineExtension('form-reset', {
            onEvent: function(name, evt) {
                if (name === 'htmx:afterRequest') {
                    const target = evt.detail.elt;
                    
                    // Check if form should be reset
                    if (target.tagName === 'FORM' && target.hasAttribute('data-reset-after')) {
                        if (evt.detail.xhr.status >= 200 && evt.detail.xhr.status < 300) {
                            setTimeout(() => {
                                target.reset();
                                target.classList.remove('was-validated');
                                
                                // Clear validation states
                                const inputs = target.querySelectorAll('.is-valid, .is-invalid');
                                inputs.forEach(input => {
                                    input.classList.remove('is-valid', 'is-invalid');
                                });
                            }, 300);
                        }
                    }
                }
            }
        });
    }
    
    // Add poll extension
    addPollExtension() {
        htmx.defineExtension('poll', {
            onEvent: function(name, evt) {
                if (name === 'htmx:afterRequest') {
                    const target = evt.detail.elt;
                    
                    // Check if element should poll
                    if (target.hasAttribute('data-poll')) {
                        const interval = parseInt(target.getAttribute('data-poll-interval')) || 5000;
                        const event = target.getAttribute('data-poll-event') || 'load';
                        
                        // Set up polling
                        const pollFunction = () => {
                            if (document.body.contains(target)) {
                                htmx.trigger(target, event);
                            }
                        };
                        
                        // Clear existing interval if any
                        if (target._pollInterval) {
                            clearInterval(target._pollInterval);
                        }
                        
                        // Start new interval
                        target._pollInterval = setInterval(pollFunction, interval);
                        
                        // Clean up when element is removed
                        const observer = new MutationObserver((mutations) => {
                            mutations.forEach((mutation) => {
                                if (mutation.removedNodes) {
                                    for (const node of mutation.removedNodes) {
                                        if (node === target || node.contains(target)) {
                                            clearInterval(target._pollInterval);
                                            observer.disconnect();
                                        }
                                    }
                                }
                            });
                        });
                        
                        observer.observe(document.body, { childList: true, subtree: true });
                    }
                }
            }
        });
    }
    
    // Setup error handling
    setupErrorHandling() {
        // Global error handler for HTMX
        window.addEventListener('htmx:error', (event) => {
            console.error('HTMX Error:', event.detail);
            this.showToast('Network error. Please check your connection.', 'error');
        });
        
        // Timeout handling
        window.addEventListener('htmx:timeout', (event) => {
            this.showToast('Request timed out. Please try again.', 'error');
        });
    }
    
    // Setup loading indicators
    setupLoadingIndicators() {
        // Add CSS for loading indicators
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
            .loading-spinner {
                display: inline-block;
                width: 1.5rem;
                height: 1.5rem;
                border: 0.25rem solid rgba(255, 107, 53, 0.3);
                border-radius: 50%;
                border-top-color: #ff6b35;
                animation: spin 1s ease-in-out infinite;
            }
            @keyframes spin {
                to { transform: rotate(360deg); }
            }
        `;
        document.head.appendChild(style);
    }
    
    // Setup animations
    setupAnimations() {
        // Add animation CSS
        const style = document.createElement('style');
        style.textContent = `
            .htmx-added {
                opacity: 0;
            }
            .htmx-settling {
                opacity: 0;
                transition: opacity 300ms ease-in;
            }
            .htmx-swapping {
                opacity: 0;
                transition: opacity 300ms ease-out;
            }
            
            /* Fade animations */
            .fade-in {
                animation: fadeIn 0.3s ease;
            }
            .fade-out {
                animation: fadeOut 0.3s ease;
            }
            
            @keyframes fadeIn {
                from { opacity: 0; transform: translateY(-10px); }
                to { opacity: 1; transform: translateY(0); }
            }
            
            @keyframes fadeOut {
                from { opacity: 1; transform: translateY(0); }
                to { opacity: 0; transform: translateY(-10px); }
            }
            
            /* Slide animations */
            .slide-in {
                animation: slideIn 0.3s ease;
            }
            .slide-out {
                animation: slideOut 0.3s ease;
            }
            
            @keyframes slideIn {
                from { transform: translateX(-100%); }
                to { transform: translateX(0); }
            }
            
            @keyframes slideOut {
                from { transform: translateX(0); }
                to { transform: translateX(100%); }
            }
            
            /* Scale animations */
            .scale-in {
                animation: scaleIn 0.3s ease;
            }
            
            @keyframes scaleIn {
                from { transform: scale(0.9); opacity: 0; }
                to { transform: scale(1); opacity: 1; }
            }
        `;
        document.head.appendChild(style);
    }
    
    // Show loading indicator
    showLoadingIndicator(target) {
        const indicator = target.getAttribute('data-loading');
        if (indicator) {
            const indicatorEl = document.querySelector(indicator);
            if (indicatorEl) {
                indicatorEl.style.display = 'block';
                indicatorEl.classList.add('show');
            }
        }
    }
    
    // Hide loading indicator
    hideLoadingIndicator(target) {
        const indicator = target.getAttribute('data-loading');
        if (indicator) {
            const indicatorEl = document.querySelector(indicator);
            if (indicatorEl) {
                indicatorEl.style.display = 'none';
                indicatorEl.classList.remove('show');
            }
        }
    }
    
    // Show toast notification
    showToast(message, type = 'info') {
        // Use Bootstrap toast if available
        if (typeof bootstrap !== 'undefined' && bootstrap.Toast) {
            const toastId = 'toast-' + Date.now();
            const toastHtml = `
                <div id="${toastId}" class="toast align-items-center text-bg-${type} border-0" role="alert">
                    <div class="d-flex">
                        <div class="toast-body">
                            ${message}
                        </div>
                        <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast"></button>
                    </div>
                </div>
            `;
            
            // Add to toast container
            let toastContainer = document.getElementById('toast-container');
            if (!toastContainer) {
                toastContainer = document.createElement('div');
                toastContainer.id = 'toast-container';
                toastContainer.className = 'toast-container position-fixed top-0 end-0 p-3';
                document.body.appendChild(toastContainer);
            }
            
            toastContainer.insertAdjacentHTML('beforeend', toastHtml);
            
            // Initialize and show toast
            const toastEl = document.getElementById(toastId);
            const toast = new bootstrap.Toast(toastEl);
            toast.show();
            
            // Remove toast after it's hidden
            toastEl.addEventListener('hidden.bs.toast', () => {
                toastEl.remove();
            });
        } else {
            // Fallback alert
            alert(`${type.toUpperCase()}: ${message}`);
        }
    }
    
    // Show modal
    showModal(content, title = '') {
        // Create modal if it doesn't exist
        let modal = document.getElementById('htmx-modal');
        if (!modal) {
            modal = document.createElement('div');
            modal.id = 'htmx-modal';
            modal.className = 'modal fade';
            modal.innerHTML = `
                <div class="modal-dialog modal-dialog-centered">
                    <div class="modal-content">
                        ${title ? `<div class="modal-header">
                            <h5 class="modal-title">${title}</h5>
                            <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
                        </div>` : ''}
                        <div class="modal-body" id="htmx-modal-body"></div>
                    </div>
                </div>
            `;
            document.body.appendChild(modal);
        }
        
        // Set content
        const modalBody = document.getElementById('htmx-modal-body');
        if (modalBody) {
            modalBody.innerHTML = content;
        }
        
        // Show modal
        const modalInstance = new bootstrap.Modal(modal);
        modalInstance.show();
        
        // Initialize content in modal
        this.initializeBootstrapComponents(modal);
    }
    
    // Initialize Bootstrap components
    initializeBootstrapComponents(container) {
        // Tooltips
        const tooltips = container.querySelectorAll('[data-bs-toggle="tooltip"]');
        tooltips.forEach(el => {
            new bootstrap.Tooltip(el);
        });
        
        // Popovers
        const popovers = container.querySelectorAll('[data-bs-toggle="popover"]');
        popovers.forEach(el => {
            new bootstrap.Popover(el);
        });
        
        // Dropdowns
        const dropdowns = container.querySelectorAll('.dropdown-toggle');
        dropdowns.forEach(el => {
            new bootstrap.Dropdown(el);
        });
        
        // Collapse
        const collapses = container.querySelectorAll('[data-bs-toggle="collapse"]');
        collapses.forEach(el => {
            new bootstrap.Collapse(el, { toggle: false });
        });
    }
    
    // Initialize tooltips
    initializeTooltips(container) {
        const tooltips = container.querySelectorAll('[title]');
        tooltips.forEach(el => {
            if (!el.hasAttribute('data-bs-toggle')) {
                el.setAttribute('data-bs-toggle', 'tooltip');
                new bootstrap.Tooltip(el);
            }
        });
    }
    
    // Initialize form validation
    initializeFormValidation(container) {
        const forms = container.querySelectorAll('form');
        forms.forEach(form => {
            form.addEventListener('submit', (e) => {
                if (!form.checkValidity()) {
                    e.preventDefault();
                    e.stopPropagation();
                }
                form.classList.add('was-validated');
            }, false);
        });
    }
    
    // Initialize sorting
    initializeSorting(container) {
        const sortableTables = container.querySelectorAll('.sortable');
        sortableTables.forEach(table => {
            const headers = table.querySelectorAll('th[data-sort]');
            headers.forEach(header => {
                header.style.cursor = 'pointer';
                header.addEventListener('click', () => {
                    this.sortTable(table, header);
                });
            });
        });
    }
    
    // Sort table
    sortTable(table, header) {
        const column = header.getAttribute('data-sort');
        const direction = header.getAttribute('data-sort-direction') || 'asc';
        const newDirection = direction === 'asc' ? 'desc' : 'asc';
        
        // Update sort direction
        header.setAttribute('data-sort-direction', newDirection);
        
        // Remove sort indicators from other headers
        const headers = table.querySelectorAll('th[data-sort]');
        headers.forEach(h => {
            if (h !== header) {
                h.removeAttribute('data-sort-direction');
                h.classList.remove('sort-asc', 'sort-desc');
            }
        });
        
        // Add sort indicator to current header
        header.classList.remove('sort-asc', 'sort-desc');
        header.classList.add(`sort-${newDirection}`);
        
        // Get table rows
        const tbody = table.querySelector('tbody');
        const rows = Array.from(tbody.querySelectorAll('tr'));
        
        // Sort rows
        rows.sort((a, b) => {
            const aValue = a.querySelector(`td:nth-child(${Array.from(headers).indexOf(header) + 1})`).textContent;
            const bValue = b.querySelector(`td:nth-child(${Array.from(headers).indexOf(header) + 1})`).textContent;
            
            let comparison = 0;
            if (aValue < bValue) comparison = -1;
            if (aValue > bValue) comparison = 1;
            
            return newDirection === 'asc' ? comparison : -comparison;
        });
        
        // Reorder rows
        rows.forEach(row => tbody.appendChild(row));
    }
    
    // Update counters
    updateCounters() {
        // Update cart counter
        if (window.shoppingCart) {
            const cartCount = window.shoppingCart.getItemCount();
            const counters = document.querySelectorAll('.cart-counter');
            counters.forEach(counter => {
                counter.textContent = cartCount;
                counter.style.display = cartCount > 0 ? 'inline-block' : 'none';
            });
        }
        
        // Update notification counters
        const notificationCount = document.querySelectorAll('.notification-unread').length;
        const notificationCounters = document.querySelectorAll('.notification-counter');
        notificationCounters.forEach(counter => {
            counter.textContent = notificationCount;
            counter.style.display = notificationCount > 0 ? 'inline-block' : 'none';
        });
    }
    
    // Scroll to target
    scrollToTarget(target) {
        if (target.hasAttribute('data-scroll')) {
            const scrollTo = target.getAttribute('data-scroll');
            const scrollElement = scrollTo === 'self' ? target : document.querySelector(scrollTo);
            
            if (scrollElement) {
                setTimeout(() => {
                    scrollElement.scrollIntoView({
                        behavior: 'smooth',
                        block: 'center'
                    });
                }, 100);
            }
        }
    }
    
    // Focus first input
    focusFirstInput(container) {
        if (container.hasAttribute('data-autofocus')) {
            const firstInput = container.querySelector('input, select, textarea');
            if (firstInput) {
                setTimeout(() => {
                    firstInput.focus();
                }, 100);
            }
        }
    }
    
    // Get CSRF token
    getCSRFToken() {
        const metaTag = document.querySelector('meta[name="csrf-token"]');
        if (metaTag) {
            return metaTag.getAttribute('content');
        }
        
        const cookieMatch = document.cookie.match(/csrftoken=([^;]+)/);
        if (cookieMatch) {
            return cookieMatch[1];
        }
        
        return null;
    }
    
    // Validate email
    validateEmail(email) {
        const re = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
        return re.test(email);
    }
    
    // Validate phone
    validatePhone(phone) {
        const re = /^[6-9]\d{9}$/;
        return re.test(phone.replace(/\D/g, ''));
    }
}

// Initialize HTMX Handlers
let htmxHandlers;

document.addEventListener('DOMContentLoaded', () => {
    htmxHandlers = new HTMXHandlers();
    window.htmxHandlers = htmxHandlers;
});

// HTMX Utility Functions
const HTMXUtils = {
    // Trigger HTMX request
    triggerRequest: function(selector, event = 'click') {
        const element = document.querySelector(selector);
        if (element) {
            htmx.trigger(element, event);
        }
    },
    
    // Update element with HTML
    updateElement: function(selector, html) {
        const element = document.querySelector(selector);
        if (element) {
            element.innerHTML = html;
            htmx.process(element);
        }
    },
    
    // Append to element
    appendToElement: function(selector, html) {
        const element = document.querySelector(selector);
        if (element) {
            element.insertAdjacentHTML('beforeend', html);
            htmx.process(element.lastElementChild);
        }
    },
    
    // Prepend to element
    prependToElement: function(selector, html) {
        const element = document.querySelector(selector);
        if (element) {
            element.insertAdjacentHTML('afterbegin', html);
            htmx.process(element.firstElementChild);
        }
    },
    
    // Remove element
    removeElement: function(selector) {
        const element = document.querySelector(selector);
        if (element && element.parentNode) {
            element.parentNode.removeChild(element);
        }
    },
    
    // Add class to element
    addClass: function(selector, className) {
        const element = document.querySelector(selector);
        if (element) {
            element.classList.add(className);
        }
    },
    
    // Remove class from element
    removeClass: function(selector, className) {
        const element = document.querySelector(selector);
        if (element) {
            element.classList.remove(className);
        }
    },
    
    // Toggle class on element
    toggleClass: function(selector, className) {
        const element = document.querySelector(selector);
        if (element) {
            element.classList.toggle(className);
        }
    },
    
    // Set attribute on element
    setAttribute: function(selector, attribute, value) {
        const element = document.querySelector(selector);
        if (element) {
            element.setAttribute(attribute, value);
        }
    },
    
    // Remove attribute from element
    removeAttribute: function(selector, attribute) {
        const element = document.querySelector(selector);
        if (element) {
            element.removeAttribute(attribute);
        }
    },
    
    // Get element value
    getValue: function(selector) {
        const element = document.querySelector(selector);
        if (element) {
            return element.value;
        }
        return null;
    },
    
    // Set element value
    setValue: function(selector, value) {
        const element = document.querySelector(selector);
        if (element) {
            element.value = value;
        }
    },
    
    // Disable element
    disableElement: function(selector) {
        const element = document.querySelector(selector);
        if (element) {
            element.disabled = true;
        }
    },
    
    // Enable element
    enableElement: function(selector) {
        const element = document.querySelector(selector);
        if (element) {
            element.disabled = false;
        }
    },
    
    // Show element
    showElement: function(selector) {
        const element = document.querySelector(selector);
        if (element) {
            element.style.display = '';
        }
    },
    
    // Hide element
    hideElement: function(selector) {
        const element = document.querySelector(selector);
        if (element) {
            element.style.display = 'none';
        }
    },
    
    // Toggle element visibility
    toggleElement: function(selector) {
        const element = document.querySelector(selector);
        if (element) {
            if (element.style.display === 'none') {
                element.style.display = '';
            } else {
                element.style.display = 'none';
            }
        }
    },
    
    // Create and dispatch custom event
    dispatchEvent: function(eventName, detail = {}) {
        const event = new CustomEvent(eventName, { detail });
        document.dispatchEvent(event);
    },
    
    // Listen for custom event
    onEvent: function(eventName, callback) {
        document.addEventListener(eventName, callback);
    },
    
    // Remove event listener
    offEvent: function(eventName, callback) {
        document.removeEventListener(eventName, callback);
    }
};

// Export for testing/debugging
if (typeof module !== 'undefined' && module.exports) {
    module.exports = { HTMXHandlers, HTMXUtils };
}