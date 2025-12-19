/**
 * Team Member Dashboard JavaScript
 * Handles team member-specific functionality
 */

class TeamMemberDashboard {
    constructor() {
        this.assignedOrders = [];
        this.plans = [];
        this.currentOrder = null;
        this.init();
    }
    
    init() {
        this.loadAssignedOrders();
        this.loadPlans();
        this.setupEventListeners();
        this.setupRealtimeUpdates();
        this.initializeOTPHandler();
    }
    
    // Load assigned orders
    async loadAssignedOrders() {
        try {
            const response = await fetch('/api/team/orders');
            if (response.ok) {
                this.assignedOrders = await response.json();
                this.updateOrdersDisplay();
            }
        } catch (error) {
            console.error('Error loading assigned orders:', error);
        }
    }
    
    // Update orders display
    updateOrdersDisplay() {
        const container = document.getElementById('assigned-orders');
        if (!container) return;
        
        if (this.assignedOrders.length === 0) {
            container.innerHTML = `
                <div class="text-center py-5">
                    <i class="fas fa-clipboard-list fa-3x text-muted mb-3"></i>
                    <h4>No orders assigned</h4>
                    <p class="text-muted">You don't have any orders assigned at the moment.</p>
                </div>
            `;
            return;
        }
        
        let ordersHTML = '';
        this.assignedOrders.forEach(order => {
            const statusClass = this.getStatusClass(order.status);
            const itemCount = order.items ? order.items.length : 0;
            
            ordersHTML += `
                <div class="card mb-3 order-card" id="order-${order.id}">
                    <div class="card-body">
                        <div class="d-flex justify-content-between align-items-start mb-2">
                            <div>
                                <h5 class="card-title mb-1">Order #${order.id}</h5>
                                <p class="card-text mb-1">
                                    <small class="text-muted">
                                        <i class="fas fa-user me-1"></i> ${order.customer_name}
                                    </small>
                                </p>
                                <p class="card-text mb-2">
                                    <small class="text-muted">
                                        <i class="fas fa-map-marker-alt me-1"></i> ${order.address.substring(0, 50)}${order.address.length > 50 ? '...' : ''}
                                    </small>
                                </p>
                            </div>
                            <div class="text-end">
                                <span class="badge ${statusClass} mb-2">${order.status.replace('_', ' ').toUpperCase()}</span>
                                <div class="h5">₹${order.total_amount.toFixed(2)}</div>
                            </div>
                        </div>
                        
                        <div class="row">
                            <div class="col-md-6">
                                <p class="mb-1">
                                    <strong>Items:</strong> ${itemCount} item${itemCount !== 1 ? 's' : ''}
                                </p>
                                <p class="mb-1">
                                    <strong>Ordered:</strong> ${new Date(order.created_at).toLocaleTimeString('en-IN', { hour: '2-digit', minute: '2-digit' })}
                                </p>
                            </div>
                            <div class="col-md-6">
                                <div class="btn-group w-100">
                                    <button class="btn btn-sm btn-outline-info" 
                                            onclick="teamMemberDashboard.viewOrderDetails(${order.id})">
                                        <i class="fas fa-eye me-1"></i> Details
                                    </button>
                                    
                                    ${this.getActionButton(order)}
                                </div>
                            </div>
                        </div>
                        
                        ${order.special_instructions ? `
                        <div class="mt-2">
                            <strong><i class="fas fa-sticky-note me-1"></i> Instructions:</strong>
                            <p class="mb-0 small">${order.special_instructions}</p>
                        </div>
                        ` : ''}
                    </div>
                </div>
            `;
        });
        
        container.innerHTML = ordersHTML;
    }
    
    // Get action button based on order status
    getActionButton(order) {
        switch (order.status) {
            case 'pending':
                return `
                    <button class="btn btn-sm btn-success"
                            onclick="teamMemberDashboard.updateOrderStatus(${order.id}, 'confirmed')">
                        <i class="fas fa-check me-1"></i> Confirm
                    </button>
                `;
            case 'confirmed':
                return `
                    <button class="btn btn-sm btn-primary"
                            onclick="teamMemberDashboard.updateOrderStatus(${order.id}, 'preparing')">
                        <i class="fas fa-utensils me-1"></i> Start Prep
                    </button>
                `;
            case 'preparing':
                return `
                    <button class="btn btn-sm btn-warning"
                            onclick="teamMemberDashboard.updateOrderStatus(${order.id}, 'out_for_delivery')">
                        <i class="fas fa-motorcycle me-1"></i> Out for Delivery
                    </button>
                `;
            case 'out_for_delivery':
                return `
                    <button class="btn btn-sm btn-success"
                            onclick="teamMemberDashboard.startDelivery(${order.id})">
                        <i class="fas fa-check-circle me-1"></i> Deliver
                    </button>
                `;
            default:
                return '';
        }
    }
    
    // Get status class
    getStatusClass(status) {
        const classes = {
            pending: 'bg-warning',
            confirmed: 'bg-info',
            preparing: 'bg-primary',
            out_for_delivery: 'bg-success',
            delivered: 'bg-success',
            cancelled: 'bg-danger'
        };
        return classes[status] || 'bg-secondary';
    }
    
    // Load plans
    async loadPlans() {
        try {
            const response = await fetch('/api/team/plans');
            if (response.ok) {
                this.plans = await response.json();
                this.updatePlansDisplay();
            }
        } catch (error) {
            console.error('Error loading plans:', error);
        }
    }
    
    // Update plans display
    updatePlansDisplay() {
        const container = document.getElementById('team-plans');
        if (!container) return;
        
        const unreadPlans = this.plans.filter(plan => !plan.is_read);
        const readPlans = this.plans.filter(plan => plan.is_read);
        
        if (this.plans.length === 0) {
            container.innerHTML = `
                <div class="text-center py-5">
                    <i class="fas fa-calendar-alt fa-3x text-muted mb-3"></i>
                    <h4>No plans assigned</h4>
                    <p class="text-muted">You don't have any plans from admin yet.</p>
                </div>
            `;
            return;
        }
        
        let plansHTML = '';
        
        // Show unread plans first
        if (unreadPlans.length > 0) {
            plansHTML += `
                <div class="mb-4">
                    <h5 class="text-primary">
                        <i class="fas fa-bell me-2"></i> New Plans (${unreadPlans.length})
                    </h5>
            `;
            
            unreadPlans.forEach(plan => {
                plansHTML += this.createPlanCard(plan, true);
            });
            
            plansHTML += `</div>`;
        }
        
        // Show read plans
        if (readPlans.length > 0) {
            plansHTML += `
                <div>
                    <h5 class="text-muted">
                        <i class="fas fa-history me-2"></i> Previous Plans
                    </h5>
            `;
            
            readPlans.forEach(plan => {
                plansHTML += this.createPlanCard(plan, false);
            });
            
            plansHTML += `</div>`;
        }
        
        container.innerHTML = plansHTML;
        
        // Update notification badge
        this.updatePlanNotificationBadge(unreadPlans.length);
    }
    
    // Create plan card
    createPlanCard(plan, isUnread) {
        const date = new Date(plan.created_at).toLocaleDateString('en-IN', {
            weekday: 'short',
            year: 'numeric',
            month: 'short',
            day: 'numeric',
            hour: '2-digit',
            minute: '2-digit'
        });
        
        return `
            <div class="card mb-3 plan-card ${isUnread ? 'border-primary' : ''}" id="plan-${plan.id}">
                <div class="card-body">
                    <div class="d-flex justify-content-between align-items-start mb-2">
                        <div>
                            <h6 class="card-title mb-1">
                                ${isUnread ? '<span class="badge bg-primary me-2">NEW</span>' : ''}
                                Plan from ${plan.admin_name}
                            </h6>
                            <p class="card-text">
                                <small class="text-muted">
                                    <i class="fas fa-clock me-1"></i> ${date}
                                </small>
                            </p>
                        </div>
                        <div>
                            ${isUnread ? `
                            <button class="btn btn-sm btn-outline-success"
                                    onclick="teamMemberDashboard.markPlanAsRead(${plan.id})">
                                <i class="fas fa-check me-1"></i> Mark Read
                            </button>
                            ` : ''}
                        </div>
                    </div>
                    
                    <div class="mb-3">
                        <p class="mb-0">${plan.description}</p>
                    </div>
                    
                    ${plan.image_url ? `
                    <div class="mb-3">
                        <img src="${plan.image_url}" 
                             alt="Plan Image" 
                             class="img-fluid rounded"
                             style="max-height: 200px;">
                    </div>
                    ` : ''}
                    
                    <div class="text-end">
                        <button class="btn btn-sm btn-outline-info"
                                onclick="teamMemberDashboard.viewPlanDetails(${plan.id})">
                            <i class="fas fa-expand me-1"></i> View Details
                        </button>
                    </div>
                </div>
            </div>
        `;
    }
    
    // Update plan notification badge
    updatePlanNotificationBadge(count) {
        const badges = document.querySelectorAll('.plan-notification-badge');
        badges.forEach(badge => {
            badge.textContent = count;
            badge.style.display = count > 0 ? 'inline-block' : 'none';
        });
    }
    
    // Setup event listeners
    setupEventListeners() {
        // Refresh orders button
        document.addEventListener('click', (e) => {
            if (e.target.closest('#refresh-orders')) {
                e.preventDefault();
                this.loadAssignedOrders();
                this.showNotification('Orders refreshed', 'success');
            }
        });
        
        // Refresh plans button
        document.addEventListener('click', (e) => {
            if (e.target.closest('#refresh-plans')) {
                e.preventDefault();
                this.loadPlans();
                this.showNotification('Plans refreshed', 'success');
            }
        });
        
        // Complete delivery buttons
        document.addEventListener('click', (e) => {
            const completeBtn = e.target.closest('.complete-delivery');
            if (completeBtn) {
                const orderId = completeBtn.dataset.orderId;
                this.startDelivery(orderId);
            }
        });
        
        // Mark all plans as read
        document.addEventListener('click', (e) => {
            if (e.target.closest('#mark-all-read')) {
                this.markAllPlansAsRead();
            }
        });
        
        // Attendance report
        document.addEventListener('click', (e) => {
            if (e.target.closest('#view-attendance')) {
                this.viewAttendanceReport();
            }
        });
        
        // Performance report
        document.addEventListener('click', (e) => {
            if (e.target.closest('#view-performance')) {
                this.viewPerformanceReport();
            }
        });
    }
    
    // Setup realtime updates
    setupRealtimeUpdates() {
        // Check for new orders every 30 seconds
        setInterval(() => {
            this.checkForNewOrders();
        }, 30000);
        
        // Check for new plans every minute
        setInterval(() => {
            this.checkForNewPlans();
        }, 60000);
    }
    
    // Check for new orders
    async checkForNewOrders() {
        try {
            const response = await fetch('/api/team/orders/new-check');
            if (response.ok) {
                const hasNew = await response.json();
                if (hasNew) {
                    this.loadAssignedOrders();
                    this.showNewOrderNotification();
                }
            }
        } catch (error) {
            console.error('Error checking new orders:', error);
        }
    }
    
    // Check for new plans
    async checkForNewPlans() {
        try {
            const response = await fetch('/api/team/plans/new-check');
            if (response.ok) {
                const hasNew = await response.json();
                if (hasNew) {
                    this.loadPlans();
                    this.showNewPlanNotification();
                }
            }
        } catch (error) {
            console.error('Error checking new plans:', error);
        }
    }
    
    // Show new order notification
    showNewOrderNotification() {
        if (!("Notification" in window)) return;
        
        if (Notification.permission === "granted") {
            new Notification("New Order Assigned!", {
                body: "You have been assigned a new order",
                icon: '/static/images/logo.png'
            });
        } else if (Notification.permission !== "denied") {
            Notification.requestPermission().then(permission => {
                if (permission === "granted") {
                    new Notification("New Order Assigned!", {
                        body: "You have been assigned a new order",
                        icon: '/static/images/logo.png'
                    });
                }
            });
        }
    }
    
    // Show new plan notification
    showNewPlanNotification() {
        if (!("Notification" in window)) return;
        
        if (Notification.permission === "granted") {
            new Notification("New Plan Received!", {
                body: "Admin has sent you a new plan",
                icon: '/static/images/logo.png'
            });
        }
    }
    
    // Initialize OTP handler
    initializeOTPHandler() {
        const otpInputs = document.querySelectorAll('.otp-input');
        otpInputs.forEach((input, index) => {
            input.addEventListener('input', (e) => {
                const value = e.target.value;
                if (value.length === 1 && index < otpInputs.length - 1) {
                    otpInputs[index + 1].focus();
                }
            });
            
            input.addEventListener('keydown', (e) => {
                if (e.key === 'Backspace' && !e.target.value && index > 0) {
                    otpInputs[index - 1].focus();
                }
            });
        });
    }
    
    // View order details
    viewOrderDetails(orderId) {
        const modal = document.getElementById('order-details-modal');
        if (modal && htmx) {
            htmx.ajax('GET', `/team/order/${orderId}/details`, '#order-details-content');
            new bootstrap.Modal(modal).show();
        }
    }
    
    // Update order status
    async updateOrderStatus(orderId, status) {
        if (!confirm(`Change order status to "${status.replace('_', ' ')}"?`)) {
            return;
        }
        
        try {
            const response = await fetch(`/api/team/orders/${orderId}/status`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ status }),
                credentials: 'include'
            });
            
            if (response.ok) {
                this.showNotification(`Order status updated to ${status}`, 'success');
                this.loadAssignedOrders();
                
                // If status is "out_for_delivery", show OTP option
                if (status === 'out_for_delivery') {
                    setTimeout(() => {
                        this.showOTPOption(orderId);
                    }, 1000);
                }
            } else {
                const error = await response.json();
                this.showNotification(error.detail || 'Status update failed', 'error');
            }
        } catch (error) {
            console.error('Error updating order status:', error);
            this.showNotification('Network error', 'error');
        }
    }
    
    // Start delivery process
    startDelivery(orderId) {
        this.currentOrder = orderId;
        const modal = document.getElementById('delivery-modal');
        if (modal) {
            new bootstrap.Modal(modal).show();
            
            // Load order details
            this.loadOrderForDelivery(orderId);
        }
    }
    
    // Load order for delivery
    async loadOrderForDelivery(orderId) {
        try {
            const response = await fetch(`/api/team/orders/${orderId}/delivery-details`);
            if (response.ok) {
                const order = await response.json();
                this.updateDeliveryModal(order);
            }
        } catch (error) {
            console.error('Error loading delivery details:', error);
        }
    }
    
    // Update delivery modal
    updateDeliveryModal(order) {
        const container = document.getElementById('delivery-details');
        if (!container) return;
        
        const itemsHTML = order.items.map(item => `
            <tr>
                <td>${item.item_name}</td>
                <td>${item.quantity}</td>
                <td>₹${item.unit_price.toFixed(2)}</td>
                <td>₹${(item.unit_price * item.quantity).toFixed(2)}</td>
            </tr>
        `).join('');
        
        container.innerHTML = `
            <div class="mb-3">
                <h5>Order #${order.id}</h5>
                <p><strong>Customer:</strong> ${order.customer_name}</p>
                <p><strong>Phone:</strong> ${order.customer_phone}</p>
                <p><strong>Address:</strong> ${order.address}</p>
                ${order.special_instructions ? `<p><strong>Instructions:</strong> ${order.special_instructions}</p>` : ''}
            </div>
            
            <div class="table-responsive mb-3">
                <table class="table table-sm">
                    <thead>
                        <tr>
                            <th>Item</th>
                            <th>Qty</th>
                            <th>Price</th>
                            <th>Subtotal</th>
                        </tr>
                    </thead>
                    <tbody>
                        ${itemsHTML}
                    </tbody>
                    <tfoot>
                        <tr>
                            <td colspan="3" class="text-end"><strong>Total:</strong></td>
                            <td><strong>₹${order.total_amount.toFixed(2)}</strong></td>
                        </tr>
                    </tfoot>
                </table>
            </div>
            
            <div class="text-center">
                <button class="btn btn-primary btn-lg" 
                        onclick="teamMemberDashboard.generateOTP(${order.id})">
                    <i class="fas fa-sms me-2"></i> Generate & Send OTP
                </button>
                
                <div id="otp-section" class="mt-3" style="display: none;">
                    <div class="alert alert-info">
                        <i class="fas fa-info-circle me-2"></i>
                        OTP has been sent to customer's phone
                    </div>
                    
                    <div class="mb-3">
                        <label class="form-label">Enter OTP from Customer</label>
                        <div class="d-flex justify-content-center gap-2 mb-3">
                            <input type="text" class="form-control text-center otp-input" 
                                   maxlength="1" style="width: 60px; height: 60px; font-size: 1.5rem;">
                            <input type="text" class="form-control text-center otp-input" 
                                   maxlength="1" style="width: 60px; height: 60px; font-size: 1.5rem;">
                            <input type="text" class="form-control text-center otp-input" 
                                   maxlength="1" style="width: 60px; height: 60px; font-size: 1.5rem;">
                            <input type="text" class="form-control text-center otp-input" 
                                   maxlength="1" style="width: 60px; height: 60px; font-size: 1.5rem;">
                        </div>
                    </div>
                    
                    <button class="btn btn-success btn-lg w-100" 
                            onclick="teamMemberDashboard.verifyOTP(${order.id})">
                        <i class="fas fa-check-circle me-2"></i> Verify OTP & Complete Delivery
                    </button>
                    
                    <button class="btn btn-outline-secondary btn-sm mt-2" 
                            onclick="teamMemberDashboard.skipOTP(${order.id})">
                        <i class="fas fa-forward me-1"></i> Skip OTP Verification
                    </button>
                </div>
            </div>
        `;
        
        // Reinitialize OTP inputs
        this.initializeOTPHandler();
    }
    
    // Generate OTP
    async generateOTP(orderId) {
        try {
            const response = await fetch(`/api/team/orders/${orderId}/generate-otp`, {
                method: 'POST',
                credentials: 'include'
            });
            
            if (response.ok) {
                const result = await response.json();
                this.showNotification('OTP generated and sent to customer', 'success');
                
                // Show OTP section
                const otpSection = document.getElementById('otp-section');
                if (otpSection) {
                    otpSection.style.display = 'block';
                }
                
                // Auto-focus first OTP input
                const firstInput = document.querySelector('.otp-input');
                if (firstInput) {
                    firstInput.focus();
                }
            } else {
                const error = await response.json();
                this.showNotification(error.detail || 'Failed to generate OTP', 'error');
            }
        } catch (error) {
            console.error('Error generating OTP:', error);
            this.showNotification('Network error', 'error');
        }
    }
    
    // Verify OTP
    async verifyOTP(orderId) {
        const otpInputs = document.querySelectorAll('.otp-input');
        const otp = Array.from(otpInputs).map(input => input.value).join('');
        
        if (otp.length !== 4) {
            this.showNotification('Please enter 4-digit OTP', 'error');
            return;
        }
        
        try {
            const response = await fetch(`/api/team/orders/${orderId}/verify-otp`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ otp }),
                credentials: 'include'
            });
            
            if (response.ok) {
                const result = await response.json();
                this.showNotification('Delivery completed successfully!', 'success');
                
                // Close modal
                const modal = bootstrap.Modal.getInstance(document.getElementById('delivery-modal'));
                if (modal) modal.hide();
                
                // Refresh orders
                this.loadAssignedOrders();
                
                // Clear OTP inputs
                otpInputs.forEach(input => input.value = '');
            } else {
                const error = await response.json();
                this.showNotification(error.detail || 'Invalid OTP', 'error');
                
                // Shake animation for error
                otpInputs.forEach(input => {
                    input.classList.add('shake');
                    setTimeout(() => input.classList.remove('shake'), 500);
                });
            }
        } catch (error) {
            console.error('Error verifying OTP:', error);
            this.showNotification('Network error', 'error');
        }
    }
    
    // Skip OTP verification
    async skipOTP(orderId) {
        if (!confirm("Skip OTP verification and mark as delivered?")) {
            return;
        }
        
        try {
            const response = await fetch(`/api/team/orders/${orderId}/skip-otp`, {
                method: 'POST',
                credentials: 'include'
            });
            
            if (response.ok) {
                this.showNotification('Order marked as delivered', 'success');
                
                // Close modal
                const modal = bootstrap.Modal.getInstance(document.getElementById('delivery-modal'));
                if (modal) modal.hide();
                
                // Refresh orders
                this.loadAssignedOrders();
            } else {
                const error = await response.json();
                this.showNotification(error.detail || 'Failed to update order', 'error');
            }
        } catch (error) {
            console.error('Error skipping OTP:', error);
            this.showNotification('Network error', 'error');
        }
    }
    
    // Show OTP option
    showOTPOption(orderId) {
        this.showNotification(
            `Order #${orderId} is ready for delivery. Click to generate OTP.`,
            'info',
            10000
        );
        
        // Make notification clickable
        const notification = document.querySelector('.notification:last-child');
        if (notification) {
            notification.style.cursor = 'pointer';
            notification.onclick = () => {
                this.startDelivery(orderId);
            };
        }
    }
    
    // View plan details
    viewPlanDetails(planId) {
        const modal = document.getElementById('plan-details-modal');
        if (modal && htmx) {
            htmx.ajax('GET', `/team/plan/${planId}`, '#plan-details-content');
            new bootstrap.Modal(modal).show();
        }
    }
    
    // Mark plan as read
    async markPlanAsRead(planId) {
        try {
            const response = await fetch(`/api/team/plans/${planId}/mark-read`, {
                method: 'POST',
                credentials: 'include'
            });
            
            if (response.ok) {
                // Update UI immediately
                const planCard = document.getElementById(`plan-${planId}`);
                if (planCard) {
                    planCard.classList.remove('border-primary');
                    
                    const markReadBtn = planCard.querySelector('button');
                    if (markReadBtn) {
                        markReadBtn.remove();
                    }
                    
                    const badge = planCard.querySelector('.badge');
                    if (badge) {
                        badge.remove();
                    }
                }
                
                this.showNotification('Plan marked as read', 'success');
                this.loadPlans(); // Reload to update counts
            }
        } catch (error) {
            console.error('Error marking plan as read:', error);
            this.showNotification('Failed to mark plan as read', 'error');
        }
    }
    
    // Mark all plans as read
    async markAllPlansAsRead() {
        if (this.plans.length === 0) return;
        
        try {
            const response = await fetch('/api/team/plans/mark-all-read', {
                method: 'POST',
                credentials: 'include'
            });
            
            if (response.ok) {
                this.showNotification('All plans marked as read', 'success');
                this.loadPlans();
            }
        } catch (error) {
            console.error('Error marking all plans as read:', error);
            this.showNotification('Failed to mark plans as read', 'error');
        }
    }
    
    // View attendance report
    viewAttendanceReport() {
        const modal = document.getElementById('attendance-modal');
        if (modal && htmx) {
            htmx.ajax('GET', '/team/attendance', '#attendance-content');
            new bootstrap.Modal(modal).show();
        }
    }
    
    // View performance report
    viewPerformanceReport() {
        const modal = document.getElementById('performance-modal');
        if (modal && htmx) {
            htmx.ajax('GET', '/team/performance', '#performance-content');
            new bootstrap.Modal(modal).show();
        }
    }
    
    // Show notification
    showNotification(message, type = 'info', duration = 5000) {
        // Use toast if available
        if (typeof bootstrap !== 'undefined' && bootstrap.Toast) {
            const toastEl = document.getElementById('team-toast');
            if (toastEl) {
                const toastBody = toastEl.querySelector('.toast-body');
                if (toastBody) {
                    toastBody.textContent = message;
                    toastEl.classList.remove('bg-success', 'bg-danger', 'bg-warning', 'bg-info');
                    toastEl.classList.add(`bg-${type}`);
                    
                    const toast = new bootstrap.Toast(toastEl);
                    toast.show();
                }
            }
        } else {
            // Fallback alert
            const alert = document.createElement('div');
            alert.className = `alert alert-${type} alert-dismissible fade show`;
            alert.innerHTML = `
                ${message}
                <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
            `;
            
            const container = document.querySelector('.notification-container') || document.body;
            container.appendChild(alert);
            
            // Auto-remove
            setTimeout(() => {
                if (alert.parentNode) {
                    alert.parentNode.removeChild(alert);
                }
            }, duration);
        }
    }
}

// Initialize team member dashboard
let teamMemberDashboard;

document.addEventListener('DOMContentLoaded', () => {
    // Check if user is team member
    if (window.AppState && window.AppState.user && window.AppState.user.role === 'team_member') {
        teamMemberDashboard = new TeamMemberDashboard();
        window.teamMemberDashboard = teamMemberDashboard;
    }
});

// Team member utility functions
const TeamMemberUtils = {
    // Format time duration
    formatDuration: function(minutes) {
        if (minutes < 60) {
            return `${Math.round(minutes)} minutes`;
        } else {
            const hours = Math.floor(minutes / 60);
            const remainingMinutes = Math.round(minutes % 60);
            return `${hours}h ${remainingMinutes}m`;
        }
    },
    
    // Calculate delivery time estimate
    calculateDeliveryTime: function(distanceKm, trafficFactor = 1) {
        const baseSpeed = 30; // km/h average
        const baseTime = (distanceKm / baseSpeed) * 60; // minutes
        return Math.round(baseTime * trafficFactor);
    },
    
    // Get distance between coordinates (Haversine formula)
    getDistance: function(lat1, lon1, lat2, lon2) {
        const R = 6371; // Earth's radius in km
        const dLat = this.toRad(lat2 - lat1);
        const dLon = this.toRad(lon2 - lon1);
        const a = Math.sin(dLat/2) * Math.sin(dLat/2) +
                  Math.cos(this.toRad(lat1)) * Math.cos(this.toRad(lat2)) *
                  Math.sin(dLon/2) * Math.sin(dLon/2);
        const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1-a));
        return R * c;
    },
    
    toRad: function(degrees) {
        return degrees * (Math.PI / 180);
    },
    
    // Generate delivery route
    generateRoute: function(start, waypoints, end) {
        // Simplified route generation
        // In production, use Google Maps API or similar
        return {
            distance: 'Calculating...',
            duration: 'Calculating...',
            steps: ['Start from restaurant', ...waypoints, 'Deliver to customer']
        };
    },
    
    // Calculate earnings
    calculateEarnings: function(orders, commissionRate = 0.1) {
        const totalAmount = orders.reduce((sum, order) => sum + order.total_amount, 0);
        const earnings = totalAmount * commissionRate;
        return {
            totalAmount: this.formatCurrency(totalAmount),
            earnings: this.formatCurrency(earnings),
            orderCount: orders.length
        };
    },
    
    // Format currency
    formatCurrency: function(amount) {
        return new Intl.NumberFormat('en-IN', {
            style: 'currency',
            currency: 'INR',
            minimumFractionDigits: 2
        }).format(amount);
    },
    
    // Get performance rating
    getPerformanceRating: function(completedOrders, totalOrders, onTimePercentage) {
        const completionRate = (completedOrders / totalOrders) * 100;
        const rating = (completionRate * 0.6) + (onTimePercentage * 0.4);
        
        if (rating >= 90) return { rating: 'Excellent', stars: 5, color: 'success' };
        if (rating >= 75) return { rating: 'Good', stars: 4, color: 'primary' };
        if (rating >= 60) return { rating: 'Average', stars: 3, color: 'warning' };
        return { rating: 'Needs Improvement', stars: 2, color: 'danger' };
    }
};

// Export for testing/debugging
if (typeof module !== 'undefined' && module.exports) {
    module.exports = { TeamMemberDashboard, TeamMemberUtils };
}
