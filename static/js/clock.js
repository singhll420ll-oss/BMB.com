/**
 * Secret Clock Implementation
 * Hidden admin access via 15-second long press + 5 taps
 * No visual hints, timers, or indicators
 */

class SecretClock {
    constructor() {
        this.clockElement = null;
        this.editModeElement = null;
        this.timeInput = null;
        this.periodSelect = null;
        this.saveButton = null;
        this.cancelButton = null;
        
        // Secret combination tracking
        this.longPressStart = 0;
        this.longPressActive = false;
        this.longPressTimer = null;
        this.tapCount = 0;
        this.lastTapTime = 0;
        this.combinationCompleted = false;
        
        // Long press duration (15 seconds)
        this.LONG_PRESS_DURATION = 15000;
        
        // Tap interval (500ms max between taps)
        this.TAP_INTERVAL = 500;
        
        // Required taps (5 taps)
        this.REQUIRED_TAPS = 5;
        
        // Secret time (3:43)
        this.SECRET_HOUR = 3;
        this.SECRET_MINUTE = 43;
        
        this.init();
    }
    
    init() {
        // Find clock elements
        this.clockElement = document.getElementById('secret-clock');
        this.editModeElement = document.getElementById('clock-edit-mode');
        
        if (!this.clockElement || !this.editModeElement) {
            console.warn('Clock elements not found');
            return;
        }
        
        // Find edit mode elements
        this.timeInput = document.getElementById('time-input');
        this.periodSelect = document.getElementById('period-select');
        this.saveButton = document.getElementById('clock-save-btn');
        this.cancelButton = document.getElementById('clock-cancel-btn');
        
        // Initialize real-time clock
        this.updateRealTime();
        setInterval(() => this.updateRealTime(), 1000);
        
        // Setup event listeners
        this.setupEventListeners();
        
        // Hide any potential visual hints
        this.hideAllHints();
    }
    
    // Update real-time clock display
    updateRealTime() {
        if (this.combinationCompleted) return;
        
        const now = new Date();
        const options = {
            timeZone: 'Asia/Kolkata',
            hour12: true,
            hour: 'numeric',
            minute: '2-digit',
            second: '2-digit'
        };
        
        const formatter = new Intl.DateTimeFormat('en-IN', options);
        const parts = formatter.formatToParts(now);
        
        let hour = '';
        let minute = '';
        let second = '';
        let period = '';
        
        parts.forEach(part => {
            switch (part.type) {
                case 'hour': hour = part.value; break;
                case 'minute': minute = part.value; break;
                case 'second': second = part.value; break;
                case 'dayPeriod': period = part.value; break;
            }
        });
        
        this.clockElement.innerHTML = `
            <div class="clock-time">
                ${hour}:${minute}:${second} ${period}
            </div>
        `;
    }
    
    // Setup event listeners for secret combination
    setupEventListeners() {
        // Mouse/touch events for long press + taps
        this.clockElement.addEventListener('mousedown', (e) => this.handlePressStart(e));
        this.clockElement.addEventListener('touchstart', (e) => this.handlePressStart(e));
        
        this.clockElement.addEventListener('mouseup', (e) => this.handlePressEnd(e));
        this.clockElement.addEventListener('touchend', (e) => this.handlePressEnd(e));
        this.clockElement.addEventListener('mouseleave', (e) => this.handlePressEnd(e));
        
        this.clockElement.addEventListener('click', (e) => this.handleTap(e));
        
        // Edit mode event listeners
        if (this.saveButton) {
            this.saveButton.addEventListener('click', () => this.handleSave());
        }
        
        if (this.cancelButton) {
            this.cancelButton.addEventListener('click', () => this.cancelEditMode());
        }
        
        // Time input validation
        if (this.timeInput) {
            this.timeInput.addEventListener('input', () => this.validateTimeInput());
            this.timeInput.addEventListener('keypress', (e) => {
                if (e.key === 'Enter') {
                    this.handleSave();
                }
            });
        }
        
        // Period select change
        if (this.periodSelect) {
            this.periodSelect.addEventListener('change', () => this.validateTimeInput());
        }
        
        // Close edit mode on escape
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape' && this.editModeElement.classList.contains('active')) {
                this.cancelEditMode();
            }
        });
    }
    
    // Handle press start (long press detection)
    handlePressStart(event) {
        event.preventDefault();
        
        // Only start if not already in edit mode
        if (this.editModeElement.classList.contains('active')) return;
        
        this.longPressStart = Date.now();
        this.longPressActive = true;
        
        // Start long press timer
        this.longPressTimer = setTimeout(() => {
            if (this.longPressActive) {
                this.handleLongPressComplete();
            }
        }, this.LONG_PRESS_DURATION);
    }
    
    // Handle press end
    handlePressEnd(event) {
        event.preventDefault();
        
        this.longPressActive = false;
        
        if (this.longPressTimer) {
            clearTimeout(this.longPressTimer);
            this.longPressTimer = null;
        }
        
        // Reset tap count if too much time passed
        const now = Date.now();
        if (now - this.lastTapTime > this.TAP_INTERVAL * 2) {
            this.resetCombination();
        }
    }
    
    // Handle tap
    handleTap(event) {
        event.preventDefault();
        
        // Don't count taps during long press or in edit mode
        if (this.longPressActive || this.editModeElement.classList.contains('active')) {
            return;
        }
        
        const now = Date.now();
        
        // Check if within tap interval
        if (now - this.lastTapTime <= this.TAP_INTERVAL) {
            this.tapCount++;
            this.lastTapTime = now;
            
            // Check if required taps completed
            if (this.tapCount >= this.REQUIRED_TAPS) {
                this.handleTapsComplete();
            }
        } else {
            // Reset if too slow
            this.resetCombination();
            this.tapCount = 1;
            this.lastTapTime = now;
        }
        
        // No visual feedback - completely silent
    }
    
    // Handle long press complete
    handleLongPressComplete() {
        // Long press completed, wait for taps
        // No visual feedback
    }
    
    // Handle taps complete
    handleTapsComplete() {
        // Combination completed: long press + 5 taps
        this.combinationCompleted = true;
        
        // Enter edit mode
        this.enterEditMode();
        
        // Reset for next time
        setTimeout(() => {
            this.resetCombination();
        }, 1000);
    }
    
    // Enter edit mode
    enterEditMode() {
        // Show edit mode
        this.editModeElement.classList.add('active');
        
        // Set focus to time input
        if (this.timeInput) {
            this.timeInput.focus();
        }
        
        // Reset clock display to editable format
        this.clockElement.innerHTML = `
            <div class="clock-time">
                <input type="text" id="hour-input" maxlength="2" placeholder="HH" style="width: 40px; text-align: center;">
                :
                <input type="text" id="minute-input" maxlength="2" placeholder="MM" style="width: 40px; text-align: center;">
                <select id="period-input">
                    <option value="AM">AM</option>
                    <option value="PM">PM</option>
                </select>
            </div>
        `;
        
        // Set up edit mode inputs
        const hourInput = document.getElementById('hour-input');
        const minuteInput = document.getElementById('minute-input');
        const periodInput = document.getElementById('period-input');
        
        if (hourInput && minuteInput && periodInput) {
            hourInput.addEventListener('input', (e) => {
                this.validateHourInput(e.target);
            });
            
            minuteInput.addEventListener('input', (e) => {
                this.validateMinuteInput(e.target);
            });
            
            hourInput.addEventListener('keydown', (e) => {
                if (e.key === 'Enter' || e.key === ':') {
                    e.preventDefault();
                    minuteInput.focus();
                }
            });
            
            minuteInput.addEventListener('keydown', (e) => {
                if (e.key === 'Enter') {
                    e.preventDefault();
                    this.handleSave();
                }
            });
        }
    }
    
    // Cancel edit mode
    cancelEditMode() {
        this.editModeElement.classList.remove('active');
        this.combinationCompleted = false;
        this.resetCombination();
        
        // Restore real-time clock
        this.updateRealTime();
    }
    
    // Handle save
    handleSave() {
        if (!this.validateSecretTime()) {
            this.showMessage('Please set the time to 3:43', 'error');
            return;
        }
        
        // Secret time is correct - redirect to admin login
        this.showMessage('Access granted! Redirecting...', 'success');
        
        setTimeout(() => {
            window.location.href = '/auth/admin-login';
        }, 1000);
    }
    
    // Validate secret time (3:43)
    validateSecretTime() {
        const hourInput = document.getElementById('hour-input');
        const minuteInput = document.getElementById('minute-input');
        const periodInput = document.getElementById('period-input');
        
        if (!hourInput || !minuteInput || !periodInput) {
            return false;
        }
        
        const hour = parseInt(hourInput.value);
        const minute = parseInt(minuteInput.value);
        const period = periodInput.value;
        
        // Check if time is exactly 3:43 (AM or PM)
        return hour === this.SECRET_HOUR && minute === this.SECRET_MINUTE;
    }
    
    // Validate hour input
    validateHourInput(input) {
        let value = input.value.replace(/\D/g, '');
        
        if (value.length > 2) {
            value = value.substring(0, 2);
        }
        
        if (value.length === 2) {
            const hour = parseInt(value);
            if (hour < 1 || hour > 12) {
                value = '12';
            }
        }
        
        input.value = value;
    }
    
    // Validate minute input
    validateMinuteInput(input) {
        let value = input.value.replace(/\D/g, '');
        
        if (value.length > 2) {
            value = value.substring(0, 2);
        }
        
        if (value.length === 2) {
            const minute = parseInt(value);
            if (minute < 0 || minute > 59) {
                value = '00';
            }
        }
        
        input.value = value;
    }
    
    // Validate time input (for regular input field)
    validateTimeInput() {
        if (!this.timeInput || !this.saveButton) return;
        
        const timeValue = this.timeInput.value.trim();
        const periodValue = this.periodSelect ? this.periodSelect.value : 'AM';
        
        // Parse time (format: HH:MM)
        const [hourStr, minuteStr] = timeValue.split(':');
        const hour = parseInt(hourStr);
        const minute = parseInt(minuteStr);
        
        // Check if time is valid and equals 3:43
        const isValid = !isNaN(hour) && !isNaN(minute) &&
                       hour >= 1 && hour <= 12 &&
                       minute >= 0 && minute <= 59 &&
                       hour === this.SECRET_HOUR && minute === this.SECRET_MINUTE;
        
        this.saveButton.disabled = !isValid;
    }
    
    // Reset combination tracking
    resetCombination() {
        this.longPressStart = 0;
        this.longPressActive = false;
        this.tapCount = 0;
        this.lastTapTime = 0;
        
        if (this.longPressTimer) {
            clearTimeout(this.longPressTimer);
            this.longPressTimer = null;
        }
    }
    
    // Show message (for errors/success)
    showMessage(message, type) {
        // Create message element
        const messageElement = document.createElement('div');
        messageElement.className = `clock-message ${type}`;
        messageElement.textContent = message;
        
        // Add to document
        document.body.appendChild(messageElement);
        
        // Show with animation
        setTimeout(() => {
            messageElement.classList.add('show');
        }, 10);
        
        // Remove after delay
        setTimeout(() => {
            messageElement.classList.remove('show');
            setTimeout(() => {
                if (messageElement.parentNode) {
                    messageElement.parentNode.removeChild(messageElement);
                }
            }, 300);
        }, 3000);
    }
    
    // Hide all visual hints
    hideAllHints() {
        // Remove any hint elements
        const hints = document.querySelectorAll('[class*="hint"], [class*="Hint"], [data-hint]');
        hints.forEach(hint => hint.remove());
        
        // Remove any tooltips
        const tooltips = document.querySelectorAll('[title*="press"], [title*="tap"], [title*="long"]');
        tooltips.forEach(tooltip => tooltip.removeAttribute('title'));
        
        // Remove any instructional text
        const instructions = document.querySelectorAll('p, span, div');
        instructions.forEach(element => {
            const text = element.textContent.toLowerCase();
            if (text.includes('long press') || text.includes('15 second') || 
                text.includes('5 tap') || text.includes('secret') ||
                text.includes('hidden') || text.includes('admin')) {
                element.remove();
            }
        });
    }
}

// Initialize clock when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    // Check if we're on the home page
    if (window.location.pathname === '/' || window.location.pathname === '/index.html') {
        const clock = new SecretClock();
        window.secretClock = clock; // Make available for debugging if needed
        
        // Additional security: prevent right-click inspection
        document.addEventListener('contextmenu', (e) => {
            if (e.target.closest('.clock-container')) {
                e.preventDefault();
            }
        });
        
        // Prevent keyboard shortcuts that might reveal secrets
        document.addEventListener('keydown', (e) => {
            if ((e.ctrlKey || e.metaKey) && 
                (e.key === 'u' || e.key === 'U' || e.key === 'i' || e.key === 'I')) {
                if (document.activeElement.closest('.clock-container')) {
                    e.preventDefault();
                }
            }
        });
        
        // Clear console on clock interaction (optional - for production)
        const originalConsoleLog = console.log;
        console.log = function(...args) {
            if (args.some(arg => 
                typeof arg === 'string' && 
                (arg.includes('clock') || arg.includes('secret') || arg.includes('admin'))
            )) {
                return; // Suppress sensitive logs
            }
            originalConsoleLog.apply(console, args);
        };
    }
});

// Utility functions for clock
const ClockUtils = {
    // Format time as HH:MM
    formatTime: function(hour, minute) {
        return `${hour.toString().padStart(2, '0')}:${minute.toString().padStart(2, '0')}`;
    },
    
    // Parse time string
    parseTime: function(timeString) {
        const match = timeString.match(/^(\d{1,2}):(\d{2})\s*(AM|PM)?$/i);
        if (!match) return null;
        
        let hour = parseInt(match[1]);
        const minute = parseInt(match[2]);
        const period = match[3] ? match[3].toUpperCase() : null;
        
        // Convert to 24-hour format if period specified
        if (period === 'PM' && hour < 12) hour += 12;
        if (period === 'AM' && hour === 12) hour = 0;
        
        return { hour, minute };
    },
    
    // Get current IST time
    getCurrentIST: function() {
        const now = new Date();
        const options = {
            timeZone: 'Asia/Kolkata',
            hour12: false,
            hour: '2-digit',
            minute: '2-digit',
            second: '2-digit'
        };
        
        const formatter = new Intl.DateTimeFormat('en-IN', options);
        const parts = formatter.formatToParts(now);
        
        let hour = '';
        let minute = '';
        let second = '';
        
        parts.forEach(part => {
            switch (part.type) {
                case 'hour': hour = part.value; break;
                case 'minute': minute = part.value; break;
                case 'second': second = part.value; break;
            }
        });
        
        return {
            hour: parseInt(hour),
            minute: parseInt(minute),
            second: parseInt(second),
            formatted: `${hour}:${minute}:${second}`
        };
    },
    
    // Check if time is 3:43
    isSecretTime: function(hour, minute, period) {
        // Convert to 24-hour format for comparison
        let hour24 = hour;
        if (period === 'PM' && hour < 12) hour24 += 12;
        if (period === 'AM' && hour === 12) hour24 = 0;
        
        return hour24 === 3 && minute === 43;
    },
    
    // Generate random clock flash (for anti-pattern detection)
    randomFlash: function(element) {
        if (!element) return;
        
        const originalColor = element.style.color;
        element.style.color = '#ff0000';
        
        setTimeout(() => {
            element.style.color = originalColor || '';
        }, 50);
    }
};

// Export for testing/debugging
if (typeof module !== 'undefined' && module.exports) {
    module.exports = { SecretClock, ClockUtils };
}
