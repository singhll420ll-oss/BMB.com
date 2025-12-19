/**
 * OTP (One-Time Password) Management System
 * Handles OTP generation, validation, and SMS integration
 */

class OTPManager {
    constructor() {
        this.otpStore = new Map(); // In-memory store (use Redis in production)
        this.otpExpiry = 5 * 60 * 1000; // 5 minutes in milliseconds
        this.maxAttempts = 3;
        this.init();
    }
    
    init() {
        // Load any persisted OTP data
        this.loadFromStorage();
        
        // Cleanup expired OTPs every minute
        setInterval(() => this.cleanupExpiredOTPs(), 60000);
        
        // Setup event listeners
        this.setupEventListeners();
    }
    
    // Generate OTP for an order
    generateOTP(orderId, phoneNumber) {
        // Generate 4-digit OTP
        const otp = Math.floor(1000 + Math.random() * 9000).toString();
        
        // Store OTP with metadata
        this.otpStore.set(orderId, {
            otp,
            phone: phoneNumber,
            attempts: 0,
            generatedAt: Date.now(),
            expiresAt: Date.now() + this.otpExpiry,
            verified: false
        });
        
        // Save to localStorage for persistence
        this.saveToStorage();
        
        // Send OTP via SMS
        this.sendOTPSMS(phoneNumber, otp, orderId);
        
        return otp;
    }
    
    // Verify OTP
    verifyOTP(orderId, inputOTP) {
        const otpData = this.otpStore.get(orderId);
        
        if (!otpData) {
            return {
                success: false,
                message: 'OTP not found or expired',
                remainingAttempts: 0
            };
        }
        
        // Check if OTP is expired
        if (Date.now() > otpData.expiresAt) {
            this.otpStore.delete(orderId);
            this.saveToStorage();
            return {
                success: false,
                message: 'OTP has expired',
                remainingAttempts: 0
            };
        }
        
        // Check if maximum attempts reached
        if (otpData.attempts >= this.maxAttempts) {
            return {
                success: false,
                message: 'Maximum OTP attempts exceeded',
                remainingAttempts: 0
            };
        }
        
        // Increment attempts
        otpData.attempts++;
        
        // Verify OTP
        if (otpData.otp === inputOTP) {
            otpData.verified = true;
            otpData.verifiedAt = Date.now();
            this.otpStore.set(orderId, otpData);
            this.saveToStorage();
            
            return {
                success: true,
                message: 'OTP verified successfully',
                remainingAttempts: this.maxAttempts - otpData.attempts
            };
        } else {
            this.otpStore.set(orderId, otpData);
            this.saveToStorage();
            
            const remainingAttempts = this.maxAttempts - otpData.attempts;
            return {
                success: false,
                message: `Invalid OTP. ${remainingAttempts} attempt${remainingAttempts !== 1 ? 's' : ''} remaining`,
                remainingAttempts
            };
        }
    }
    
    // Check OTP status
    checkOTPStatus(orderId) {
        const otpData = this.otpStore.get(orderId);
        
        if (!otpData) {
            return {
                exists: false,
                verified: false,
                expired: true,
                attempts: 0,
                remainingAttempts: 0,
                timeRemaining: 0
            };
        }
        
        const timeRemaining = Math.max(0, otpData.expiresAt - Date.now());
        const remainingAttempts = Math.max(0, this.maxAttempts - otpData.attempts);
        
        return {
            exists: true,
            verified: otpData.verified || false,
            expired: timeRemaining === 0,
            attempts: otpData.attempts,
            remainingAttempts,
            timeRemaining: Math.ceil(timeRemaining / 1000) // in seconds
        };
    }
    
    // Resend OTP
    resendOTP(orderId) {
        const otpData = this.otpStore.get(orderId);
        
        if (!otpData) {
            return {
                success: false,
                message: 'Cannot resend OTP. Please generate a new one.'
            };
        }
        
        // Generate new OTP
        const newOTP = this.generateOTP(orderId, otpData.phone);
        
        return {
            success: true,
            message: 'New OTP sent successfully',
            otp: newOTP
        };
    }
    
    // Send OTP via SMS
    async sendOTPSMS(phoneNumber, otp, orderId) {
        // In production, integrate with Twilio or other SMS service
        try {
            const message = `Your Bite Me Buddy order #${orderId} is out for delivery. OTP: ${otp}. Valid for 5 minutes.`;
            
            // Uncomment when SMS service is configured
            /*
            const response = await fetch('/api/sms/send', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    to: phoneNumber,
                    message: message
                })
            });
            
            if (!response.ok) {
                throw new Error('SMS sending failed');
            }
            */
            
            // For demo purposes, log to console
            console.log(`SMS to ${phoneNumber}: ${message}`);
            
            // Show success message
            this.showNotification(`OTP sent to ${phoneNumber}`, 'success');
            
            return { success: true, message: 'SMS sent successfully' };
            
        } catch (error) {
            console.error('Error sending SMS:', error);
            this.showNotification('Failed to send SMS', 'error');
            return { success: false, message: 'Failed to send SMS' };
        }
    }
    
    // Cleanup expired OTPs
    cleanupExpiredOTPs() {
        const now = Date.now();
        let cleanedCount = 0;
        
        for (const [orderId, otpData] of this.otpStore.entries()) {
            if (now > otpData.expiresAt + 300000) { // 5 minutes after expiry
                this.otpStore.delete(orderId);
                cleanedCount++;
            }
        }
        
        if (cleanedCount > 0) {
            this.saveToStorage();
            console.log(`Cleaned up ${cleanedCount} expired OTPs`);
        }
    }
    
    // Save to localStorage
    saveToStorage() {
        try {
            const data = Object.fromEntries(this.otpStore);
            localStorage.setItem('bite_me_buddy_otps', JSON.stringify(data));
        } catch (error) {
            console.error('Error saving OTPs to storage:', error);
        }
    }
    
    // Load from localStorage
    loadFromStorage() {
        try {
            const data = localStorage.getItem('bite_me_buddy_otps');
            if (data) {
                const parsed = JSON.parse(data);
                for (const [key, value] of Object.entries(parsed)) {
                    this.otpStore.set(key, value);
                }
            }
        } catch (error) {
            console.error('Error loading OTPs from storage:', error);
            this.otpStore.clear();
        }
    }
    
    // Setup event listeners
    setupEventListeners() {
        // OTP input auto-focus
        document.addEventListener('input', (e) => {
            if (e.target.classList.contains('otp-digit')) {
                this.handleOTPInput(e.target);
            }
        });
        
        // OTP form submission
        document.addEventListener('submit', (e) => {
            const otpForm = e.target.closest('.otp-form');
            if (otpForm) {
                e.preventDefault();
                this.handleOTPFormSubmit(otpForm);
            }
        });
        
        // Resend OTP button
        document.addEventListener('click', (e) => {
            if (e.target.closest('.resend-otp')) {
                e.preventDefault();
                this.handleResendOTP(e.target.closest('.resend-otp'));
            }
        });
        
        // OTP timer updates
        this.startOTPTimers();
    }
    
    // Handle OTP input (auto-advance)
    handleOTPInput(input) {
        const value = input.value;
        const maxLength = parseInt(input.getAttribute('maxlength')) || 1;
        
        // Only allow digits
        if (!/^\d*$/.test(value)) {
            input.value = '';
            return;
        }
        
        // Limit to max length
        if (value.length > maxLength) {
            input.value = value.substring(0, maxLength);
        }
        
        // Auto-advance to next input
        if (value.length === maxLength) {
            const nextInput = input.nextElementSibling;
            if (nextInput && nextInput.classList.contains('otp-digit')) {
                nextInput.focus();
            }
        }
        
        // Auto-submit if all digits entered
        this.autoSubmitOTP(input.closest('.otp-input-group'));
    }
    
    // Auto-submit OTP when all digits entered
    autoSubmitOTP(container) {
        if (!container) return;
        
        const inputs = container.querySelectorAll('.otp-digit');
        const otp = Array.from(inputs).map(input => input.value).join('');
        
        if (otp.length === inputs.length) {
            const form = container.closest('.otp-form');
            if (form) {
                setTimeout(() => {
                    form.requestSubmit();
                }, 100);
            }
        }
    }
    
    // Handle OTP form submission
    async handleOTPFormSubmit(form) {
        const orderId = form.dataset.orderId;
        const inputs = form.querySelectorAll('.otp-digit');
        const otp = Array.from(inputs).map(input => input.value).join('');
        
        if (otp.length !== inputs.length) {
            this.showNotification('Please enter complete OTP', 'error');
            this.shakeOTPInputs(inputs);
            return;
        }
        
        // Show loading
        this.showOTPLoading(form, true);
        
        // Verify OTP
        const result = this.verifyOTP(orderId, otp);
        
        // Simulate API delay
        setTimeout(() => {
            this.showOTPLoading(form, false);
            
            if (result.success) {
                this.showNotification(result.message, 'success');
                
                // Mark order as delivered
                this.markOrderAsDelivered(orderId);
                
                // Clear inputs
                inputs.forEach(input => input.value = '');
                
                // Close modal if exists
                const modal = form.closest('.modal');
                if (modal) {
                    const modalInstance = bootstrap.Modal.getInstance(modal);
                    if (modalInstance) {
                        modalInstance.hide();
                    }
                }
                
                // Redirect or reload
                setTimeout(() => {
                    if (window.teamMemberDashboard) {
                        window.teamMemberDashboard.loadAssignedOrders();
                    }
                    if (window.location.pathname.includes('/team/')) {
                        window.location.reload();
                    }
                }, 1500);
                
            } else {
                this.showNotification(result.message, 'error');
                this.shakeOTPInputs(inputs);
                
                // Clear inputs if no attempts remaining
                if (result.remainingAttempts === 0) {
                    inputs.forEach(input => input.value = '');
                    const firstInput = inputs[0];
                    if (firstInput) firstInput.focus();
                }
            }
        }, 1000);
    }
    
    // Handle resend OTP
    async handleResendOTP(button) {
        const orderId = button.dataset.orderId;
        
        // Disable button and show loading
        button.disabled = true;
        const originalText = button.innerHTML;
        button.innerHTML = '<i class="fas fa-spinner fa-spin me-1"></i> Sending...';
        
        // Resend OTP
        const result = this.resendOTP(orderId);
        
        setTimeout(() => {
            if (result.success) {
                this.showNotification(result.message, 'success');
                
                // Start/reset timer
                this.startOTPTimer(button, orderId);
                
            } else {
                this.showNotification(result.message, 'error');
            }
            
            // Re-enable button
            setTimeout(() => {
                button.innerHTML = originalText;
                button.disabled = false;
            }, 30000); // Re-enable after 30 seconds
        }, 1500);
    }
    
    // Start OTP timers
    startOTPTimers() {
        const resendButtons = document.querySelectorAll('.resend-otp');
        resendButtons.forEach(button => {
            const orderId = button.dataset.orderId;
            if (orderId) {
                this.startOTPTimer(button, orderId);
            }
        });
    }
    
    // Start OTP timer for resend button
    startOTPTimer(button, orderId) {
        const status = this.checkOTPStatus(orderId);
        
        if (status.exists && !status.expired) {
            let timeLeft = status.timeRemaining;
            
            const timerInterval = setInterval(() => {
                if (timeLeft <= 0) {
                    clearInterval(timerInterval);
                    button.disabled = false;
                    button.innerHTML = 'Resend OTP';
                    return;
                }
                
                button.disabled = true;
                const minutes = Math.floor(timeLeft / 60);
                const seconds = timeLeft % 60;
                button.innerHTML = `Resend in ${minutes}:${seconds.toString().padStart(2, '0')}`;
                
                timeLeft--;
            }, 1000);
        }
    }
    
    // Show OTP loading state
    showOTPLoading(form, show) {
        const submitButton = form.querySelector('.otp-submit-btn');
        if (submitButton) {
            if (show) {
                submitButton.disabled = true;
                submitButton.innerHTML = '<i class="fas fa-spinner fa-spin me-1"></i> Verifying...';
            } else {
                submitButton.disabled = false;
                submitButton.innerHTML = '<i class="fas fa-check me-1"></i> Verify OTP';
            }
        }
    }
    
    // Shake OTP inputs for error feedback
    shakeOTPInputs(inputs) {
        inputs.forEach(input => {
            input.classList.add('shake');
            setTimeout(() => {
                input.classList.remove('shake');
            }, 500);
        });
    }
    
    // Mark order as delivered
    async markOrderAsDelivered(orderId) {
        try {
            const response = await fetch(`/api/orders/${orderId}/deliver`, {
                method: 'POST',
                credentials: 'include'
            });
            
            if (!response.ok) {
                throw new Error('Failed to mark order as delivered');
            }
            
            console.log(`Order ${orderId} marked as delivered`);
        } catch (error) {
            console.error('Error marking order as delivered:', error);
        }
    }
    
    // Show notification
    showNotification(message, type = 'info') {
        // Use existing notification system if available
        if (window.AppState && window.AppState.showNotification) {
            window.AppState.showNotification(message, type);
            return;
        }
        
        // Fallback notification
        const alert = document.createElement('div');
        alert.className = `alert alert-${type} alert-dismissible fade show`;
        alert.innerHTML = `
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        `;
        
        const container = document.querySelector('.notification-container') || document.body;
        container.appendChild(alert);
        
        setTimeout(() => {
            if (alert.parentNode) {
                alert.parentNode.removeChild(alert);
            }
        }, 5000);
    }
    
    // Generate OTP input HTML
    generateOTPInputHTML(orderId, digitCount = 4) {
        let inputsHTML = '';
        for (let i = 0; i < digitCount; i++) {
            inputsHTML += `
                <input type="text" 
                       class="form-control otp-digit text-center" 
                       maxlength="1"
                       inputmode="numeric"
                       pattern="[0-9]*"
                       style="width: 60px; height: 60px; font-size: 1.5rem;"
                       ${i === 0 ? 'autofocus' : ''}>
            `;
        }
        
        return `
            <div class="otp-form" data-order-id="${orderId}">
                <div class="text-center mb-4">
                    <h5>Enter OTP for Order #${orderId}</h5>
                    <p class="text-muted">Enter the 4-digit OTP sent to customer</p>
                </div>
                
                <div class="d-flex justify-content-center gap-2 mb-4 otp-input-group">
                    ${inputsHTML}
                </div>
                
                <div class="text-center">
                    <button type="submit" class="btn btn-primary btn-lg otp-submit-btn w-100">
                        <i class="fas fa-check me-2"></i> Verify OTP
                    </button>
                    
                    <div class="mt-3">
                        <button type="button" 
                                class="btn btn-outline-secondary btn-sm resend-otp"
                                data-order-id="${orderId}">
                            <i class="fas fa-redo me-1"></i> Resend OTP
                        </button>
                    </div>
                    
                    <div class="mt-2">
                        <small class="text-muted" id="otp-timer-${orderId}">
                            OTP valid for: 5:00
                        </small>
                    </div>
                </div>
            </div>
        `;
    }
    
    // Get OTP statistics
    getStatistics() {
        const total = this.otpStore.size;
        const verified = Array.from(this.otpStore.values()).filter(data => data.verified).length;
        const expired = Array.from(this.otpStore.values()).filter(data => 
            Date.now() > data.expiresAt
        ).length;
        
        return {
            total,
            verified,
            expired,
            active: total - verified - expired,
            successRate: total > 0 ? ((verified / total) * 100).toFixed(1) : 0
        };
    }
}

// Initialize OTP Manager
let otpManager;

document.addEventListener('DOMContentLoaded', () => {
    otpManager = new OTPManager();
    window.otpManager = otpManager;
});

// OTP utility functions
const OTPUtils = {
    // Validate OTP format
    validateOTPFormat: function(otp) {
        return /^\d{4,6}$/.test(otp);
    },
    
    // Generate secure OTP
    generateSecureOTP: function(length = 4) {
        const array = new Uint32Array(length);
        window.crypto.getRandomValues(array);
        return Array.from(array, num => num % 10).join('');
    },
    
    // Calculate OTP expiry time
    calculateExpiryTime: function(minutes = 5) {
        const now = new Date();
        now.setMinutes(now.getMinutes() + minutes);
        return now;
    },
    
    // Format time remaining
    formatTimeRemaining: function(seconds) {
        const minutes = Math.floor(seconds / 60);
        const remainingSeconds = seconds % 60;
        return `${minutes}:${remainingSeconds.toString().padStart(2, '0')}`;
    },
    
    // Create OTP hash (for secure storage)
    createOTPHash: function(otp, salt) {
        // In production, use proper hashing like bcrypt
        const data = otp + salt;
        let hash = 0;
        for (let i = 0; i < data.length; i++) {
            const char = data.charCodeAt(i);
            hash = ((hash << 5) - hash) + char;
            hash = hash & hash;
        }
        return hash.toString(16);
    },
    
    // Simulate SMS delay
    simulateSMSDelay: function() {
        return new Promise(resolve => {
            setTimeout(resolve, 1000 + Math.random() * 2000);
        });
    },
    
    // Check if phone number is valid for SMS
    isValidPhoneForSMS: function(phone) {
        // Basic validation for Indian numbers
        const cleaned = phone.replace(/\D/g, '');
        return cleaned.length === 10 && /^[6-9]/.test(cleaned);
    },
    
    // Format phone number for SMS
    formatPhoneForSMS: function(phone) {
        const cleaned = phone.replace(/\D/g, '');
        if (cleaned.length === 10) {
            return `+91${cleaned}`;
        }
        return phone;
    },
    
    // Get OTP delivery methods
    getDeliveryMethods: function() {
        return [
            { id: 'sms', name: 'SMS', icon: 'fas fa-sms', cost: 0.1 },
            { id: 'call', name: 'Voice Call', icon: 'fas fa-phone', cost: 0.5 },
            { id: 'email', name: 'Email', icon: 'fas fa-envelope', cost: 0 }
        ];
    },
    
    // Create OTP audit log entry
    createAuditLog: function(orderId, action, success, details = {}) {
        return {
            timestamp: new Date().toISOString(),
            orderId,
            action,
            success,
            ip: window.clientIP || 'unknown',
            userAgent: navigator.userAgent,
            ...details
        };
    }
};

// CSS for OTP components
const addOTPStyles = () => {
    const style = document.createElement('style');
    style.textContent = `
        .otp-digit {
            transition: all 0.3s ease;
        }
        
        .otp-digit:focus {
            border-color: #ff6b35;
            box-shadow: 0 0 0 0.25rem rgba(255, 107, 53, 0.25);
            transform: scale(1.05);
        }
        
        .otp-digit.shake {
            animation: shake 0.5s ease-in-out;
            border-color: #dc3545 !important;
        }
        
        @keyframes shake {
            0%, 100% { transform: translateX(0); }
            10%, 30%, 50%, 70%, 90% { transform: translateX(-5px); }
            20%, 40%, 60%, 80% { transform: translateX(5px); }
        }
        
        .otp-timer {
            font-family: monospace;
            font-weight: bold;
            color: #ff6b35;
        }
        
        .otp-timer.expiring {
            color: #dc3545;
            animation: pulse 1s infinite;
        }
        
        @keyframes pulse {
            0%, 100% { opacity: 1; }
            50% { opacity: 0.5; }
        }
        
        .otp-success {
            background-color: rgba(40, 167, 69, 0.1);
            border: 2px solid #28a745;
            border-radius: 10px;
            padding: 20px;
        }
        
        .otp-error {
            background-color: rgba(220, 53, 69, 0.1);
            border: 2px solid #dc3545;
            border-radius: 10px;
            padding: 20px;
        }
    `;
    document.head.appendChild(style);
};

// Add styles when DOM loads
document.addEventListener('DOMContentLoaded', addOTPStyles);

// Export for testing/debugging
if (typeof module !== 'undefined' && module.exports) {
    module.exports = { OTPManager, OTPUtils };
}