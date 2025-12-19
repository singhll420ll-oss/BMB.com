/**
 * Shopping Cart Management
 * Handles cart operations, quantity updates, and order placement
 */

class ShoppingCart {
    constructor() {
        this.cart = {};
        this.cartKey = 'bite_me_buddy_cart';
        this.init();
    }
    
    init() {
        this.loadCart();
        this.setupEventListeners();
        this.updateCartDisplay();
    }
    
    // Load cart from localStorage
    loadCart() {
        try {
            const cartData = localStorage.getItem(this.cartKey);
            if (cartData) {
                this.cart = JSON.parse(cartData);
            }
        } catch (error) {
            console.error('Error loading cart:', error);
            this.cart = {};
        }
    }
    
    // Save cart to localStorage
    saveCart() {
        try {
            localStorage.setItem(this.cartKey, JSON.stringify(this.cart));
            this.updateCartDisplay();
            this.dispatchCartUpdate();
        } catch (error) {
            console.error('Error saving cart:', error);
        }
    }
    
    // Add item to cart
    addItem(itemId, itemData) {
        if (this.cart[itemId]) {
            this.cart[itemId].quantity += itemData.quantity || 1;
        } else {
            this.cart[itemId] = {
                ...itemData,
                quantity: itemData.quantity || 1
            };
        }
        
        this.saveCart();
        this.showNotification(`${itemData.name} added to cart`, 'success');
    }
    
    // Remove item from cart
    removeItem(itemId) {
        if (this.cart[itemId]) {
            const itemName = this.cart[itemId].name;
            delete this.cart[itemId];
            this.saveCart();
            this.showNotification(`${itemName} removed from cart`, 'info');
            return true;
        }
        return false;
    }
    
    // Update item quantity
    updateQuantity(itemId, quantity) {
        if (this.cart[itemId]) {
            if (quantity <= 0) {
                this.removeItem(itemId);
            } else {
                this.cart[itemId].quantity = quantity;
                this.saveCart();
            }
            return true;
        }
        return false;
    }
    
    // Clear cart
    clearCart() {
        this.cart = {};
        this.saveCart();
        this.showNotification('Cart cleared', 'info');
    }
    
    // Get cart item count
    getItemCount() {
        return Object.keys(this.cart).length;
    }
    
    // Get cart total
    getTotal() {
        return Object.values(this.cart).reduce((total, item) => {
            return total + (item.price * item.quantity);
        }, 0);
    }
    
    // Get cart items
    getItems() {
        return Object.entries(this.cart).map(([id, item]) => ({
            id,
            ...item
        }));
    }
    
    // Update cart display in UI
    updateCartDisplay() {
        // Update cart badge
        const cartCount = this.getItemCount();
        const badges = document.querySelectorAll('.cart-badge');
        badges.forEach(badge => {
            badge.textContent = cartCount;
            badge.style.display = cartCount > 0 ? 'inline-block' : 'none';
        });
        
        // Update cart total
        const cartTotal = this.getTotal();
        const totalElements = document.querySelectorAll('.cart-total');
        totalElements.forEach(element => {
            element.textContent = `₹${cartTotal.toFixed(2)}`;
        });
        
        // Update cart items list if on cart page
        this.updateCartItemsList();
    }
    
    // Update cart items list (for cart page)
    updateCartItemsList() {
        const cartItemsContainer = document.getElementById('cart-items');
        if (!cartItemsContainer) return;
        
        const items = this.getItems();
        
        if (items.length === 0) {
            cartItemsContainer.innerHTML = `
                <div class="text-center py-5">
                    <i class="fas fa-shopping-cart fa-3x text-muted mb-3"></i>
                    <h4>Your cart is empty</h4>
                    <p class="text-muted">Add some delicious items to get started!</p>
                    <a href="/customer/services" class="btn btn-primary mt-3">
                        <i class="fas fa-utensils me-2"></i>Browse Menu
                    </a>
                </div>
            `;
            return;
        }
        
        let itemsHTML = '';
        items.forEach(item => {
            const subtotal = item.price * item.quantity;
            itemsHTML += `
                <div class="cart-item" id="cart-item-${item.id}">
                    <img src="${item.image || '/static/images/default-food.jpg'}" 
                         alt="${item.name}" class="cart-item-image">
                    <div class="cart-item-details flex-grow-1">
                        <h6 class="mb-1">${item.name}</h6>
                        <p class="text-muted mb-1 small">₹${item.price.toFixed(2)} each</p>
                        <div class="cart-item-actions">
                            <div class="quantity-control">
                                <button class="quantity-btn minus" 
                                        data-item-id="${item.id}"
                                        onclick="shoppingCart.decreaseQuantity('${item.id}')">
                                    <i class="fas fa-minus"></i>
                                </button>
                                <input type="number" 
                                       class="quantity-input" 
                                       value="${item.quantity}"
                                       min="1" 
                                       max="99"
                                       data-item-id="${item.id}"
                                       onchange="shoppingCart.updateQuantityInput('${item.id}', this.value)">
                                <button class="quantity-btn plus"
                                        data-item-id="${item.id}"
                                        onclick="shoppingCart.increaseQuantity('${item.id}')">
                                    <i class="fas fa-plus"></i>
                                </button>
                            </div>
                            <div class="ms-3">
                                <strong>₹${subtotal.toFixed(2)}</strong>
                            </div>
                        </div>
                    </div>
                    <button class="btn btn-sm btn-outline-danger ms-3"
                            onclick="shoppingCart.removeItem('${item.id}')">
                        <i class="fas fa-trash"></i>
                    </button>
                </div>
            `;
        });
        
        cartItemsContainer.innerHTML = itemsHTML;
        
        // Update cart summary
        this.updateCartSummary();
    }
    
    // Update cart summary (totals)
    updateCartSummary() {
        const items = this.getItems();
        const subtotal = this.getTotal();
        const tax = subtotal * 0.05; // 5% tax
        const deliveryCharge = subtotal > 0 ? 40 : 0; // ₹40 delivery charge
        const total = subtotal + tax + deliveryCharge;
        
        const summaryHTML = `
            <div class="summary-row">
                <span>Subtotal (${items.length} items)</span>
                <span>₹${subtotal.toFixed(2)}</span>
            </div>
            <div class="summary-row">
                <span>Tax (5%)</span>
                <span>₹${tax.toFixed(2)}</span>
            </div>
            <div class="summary-row">
                <span>Delivery Charge</span>
                <span>${deliveryCharge > 0 ? `₹${deliveryCharge.toFixed(2)}` : 'FREE'}</span>
            </div>
            <div class="summary-row total">
                <span>Total</span>
                <span>₹${total.toFixed(2)}</span>
            </div>
        `;
        
        const summaryContainer = document.getElementById('cart-summary');
        if (summaryContainer) {
            summaryContainer.innerHTML = summaryHTML;
        }
    }
    
    // Increase item quantity
    increaseQuantity(itemId) {
        if (this.cart[itemId]) {
            this.updateQuantity(itemId, this.cart[itemId].quantity + 1);
        }
    }
    
    // Decrease item quantity
    decreaseQuantity(itemId) {
        if (this.cart[itemId]) {
            this.updateQuantity(itemId, this.cart[itemId].quantity - 1);
        }
    }
    
    // Update quantity from input
    updateQuantityInput(itemId, value) {
        const quantity = parseInt(value);
        if (!isNaN(quantity) && quantity >= 1) {
            this.updateQuantity(itemId, quantity);
        }
    }
    
    // Setup event listeners
    setupEventListeners() {
        // Add to cart buttons
        document.addEventListener('click', (e) => {
            const addToCartBtn = e.target.closest('.add-to-cart');
            if (addToCartBtn) {
                e.preventDefault();
                
                const itemId = addToCartBtn.dataset.itemId;
                const itemData = {
                    name: addToCartBtn.dataset.itemName,
                    price: parseFloat(addToCartBtn.dataset.itemPrice),
                    image: addToCartBtn.dataset.itemImage,
                    serviceId: addToCartBtn.dataset.serviceId
                };
                
                // Use HTMX if available
                if (addToCartBtn.hasAttribute('hx-post')) {
                    htmx.trigger(addToCartBtn, 'click');
                } else {
                    this.addItem(itemId, itemData);
                }
            }
        });
        
        // Clear cart button
        document.addEventListener('click', (e) => {
            if (e.target.closest('#clear-cart-btn')) {
                if (confirm('Are you sure you want to clear your cart?')) {
                    this.clearCart();
                }
            }
        });
        
        // Place order button
        document.addEventListener('click', (e) => {
            if (e.target.closest('#place-order-btn')) {
                this.placeOrder();
            }
        });
        
        // Listen for cart updates from other components
        document.addEventListener('cart:updated', () => {
            this.loadCart();
            this.updateCartDisplay();
        });
    }
    
    // Place order
    placeOrder() {
        if (this.getItemCount() === 0) {
            this.showNotification('Your cart is empty', 'error');
            return;
        }
        
        // Check if user is logged in
        if (!window.AppState || !window.AppState.user) {
            this.showNotification('Please login to place order', 'error');
            window.location.href = '/auth/login?role=customer';
            return;
        }
        
        // Show address form if not already filled
        const addressForm = document.getElementById('address-form');
        if (addressForm && addressForm.style.display === 'none') {
            addressForm.style.display = 'block';
            addressForm.scrollIntoView({ behavior: 'smooth' });
            return;
        }
        
        // Collect order data
        const addressInput = document.getElementById('order-address');
        const instructionsInput = document.getElementById('special-instructions');
        
        if (addressInput && !addressInput.value.trim()) {
            this.showNotification('Please enter delivery address', 'error');
            addressInput.focus();
            return;
        }
        
        const orderData = {
            items: this.getItems().map(item => ({
                menu_item_id: parseInt(item.id),
                quantity: item.quantity
            })),
            address: addressInput ? addressInput.value.trim() : '',
            special_instructions: instructionsInput ? instructionsInput.value.trim() : ''
        };
        
        // Show loading
        this.showLoading(true);
        
        // Submit order via HTMX or fetch
        const orderForm = document.getElementById('order-form');
        if (orderForm && orderForm.hasAttribute('hx-post')) {
            // Prepare form data
            const formData = new FormData();
            formData.append('address', orderData.address);
            if (orderData.special_instructions) {
                formData.append('special_instructions', orderData.special_instructions);
            }
            
            // Trigger HTMX submit
            htmx.trigger(orderForm, 'submit');
        } else {
            // Use fetch API
            this.submitOrder(orderData);
        }
    }
    
    // Submit order via fetch API
    async submitOrder(orderData) {
        try {
            const response = await fetch('/api/orders/create', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(orderData),
                credentials: 'include'
            });
            
            if (response.ok) {
                const result = await response.json();
                
                // Clear cart
                this.clearCart();
                
                // Show success message
                this.showNotification(`Order #${result.order_id} placed successfully!`, 'success');
                
                // Redirect to orders page
                setTimeout(() => {
                    window.location.href = '/customer/orders';
                }, 2000);
                
            } else {
                const error = await response.json();
                this.showNotification(error.detail || 'Failed to place order', 'error');
            }
        } catch (error) {
            console.error('Order submission error:', error);
            this.showNotification('Network error. Please try again.', 'error');
        } finally {
            this.showLoading(false);
        }
    }
    
    // Show loading state
    showLoading(show) {
        const placeOrderBtn = document.getElementById('place-order-btn');
        if (placeOrderBtn) {
            if (show) {
                placeOrderBtn.innerHTML = '<i class="fas fa-spinner fa-spin me-2"></i> Processing...';
                placeOrderBtn.disabled = true;
            } else {
                placeOrderBtn.innerHTML = '<i class="fas fa-check me-2"></i> Place Order';
                placeOrderBtn.disabled = false;
            }
        }
    }
    
    // Show notification
    showNotification(message, type = 'info') {
        // Use AppState notification system if available
        if (window.AppState && window.AppState.showNotification) {
            window.AppState.showNotification(message, type);
            return;
        }
        
        // Fallback notification
        const notification = document.createElement('div');
        notification.className = `alert alert-${type} alert-dismissible fade show`;
        notification.innerHTML = `
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        `;
        
        const container = document.querySelector('.notification-container') || document.body;
        container.appendChild(notification);
        
        // Auto-remove after 5 seconds
        setTimeout(() => {
            if (notification.parentNode) {
                notification.parentNode.removeChild(notification);
            }
        }, 5000);
    }
    
    // Dispatch cart update event
    dispatchCartUpdate() {
        const event = new CustomEvent('cart:updated', {
            detail: { cart: this.cart }
        });
        document.dispatchEvent(event);
    }
    
    // Export cart data (for checkout)
    exportCart() {
        return {
            items: this.getItems(),
            total: this.getTotal(),
            itemCount: this.getItemCount()
        };
    }
    
    // Import cart data
    importCart(cartData) {
        if (cartData && cartData.items) {
            this.cart = {};
            cartData.items.forEach(item => {
                this.cart[item.id] = item;
            });
            this.saveCart();
        }
    }
}

// Initialize shopping cart
let shoppingCart;

document.addEventListener('DOMContentLoaded', () => {
    shoppingCart = new ShoppingCart();
    window.shoppingCart = shoppingCart;
});

// Cart utility functions
const CartUtils = {
    // Format price
    formatPrice: function(price) {
        return new Intl.NumberFormat('en-IN', {
            style: 'currency',
            currency: 'INR',
            minimumFractionDigits: 2
        }).format(price);
    },
    
    // Calculate tax
    calculateTax: function(subtotal, taxRate = 0.05) {
        return subtotal * taxRate;
    },
    
    // Calculate delivery charge
    calculateDelivery: function(subtotal, minFreeDelivery = 500, charge = 40) {
        return subtotal >= minFreeDelivery ? 0 : charge;
    },
    
    // Calculate total
    calculateTotal: function(subtotal, tax, delivery) {
        return subtotal + tax + delivery;
    },
    
    // Validate cart for checkout
    validateCartForCheckout: function(cart) {
        if (!cart || Object.keys(cart).length === 0) {
            return { valid: false, message: 'Cart is empty' };
        }
        
        // Check if all items are available
        const unavailableItems = Object.values(cart).filter(item => !item.isAvailable);
        if (unavailableItems.length > 0) {
            return { 
                valid: false, 
                message: 'Some items are no longer available' 
            };
        }
        
        return { valid: true };
    },
    
    // Generate order summary text
    generateOrderSummary: function(cart) {
        const items = Object.values(cart);
        const itemCount = items.reduce((sum, item) => sum + item.quantity, 0);
        const subtotal = items.reduce((sum, item) => sum + (item.price * item.quantity), 0);
        const tax = this.calculateTax(subtotal);
        const delivery = this.calculateDelivery(subtotal);
        const total = this.calculateTotal(subtotal, tax, delivery);
        
        return {
            itemCount,
            subtotal: this.formatPrice(subtotal),
            tax: this.formatPrice(tax),
            delivery: delivery > 0 ? this.formatPrice(delivery) : 'FREE',
            total: this.formatPrice(total),
            items: items.map(item => ({
                name: item.name,
                quantity: item.quantity,
                price: this.formatPrice(item.price),
                subtotal: this.formatPrice(item.price * item.quantity)
            }))
        };
    }
};

// Export for testing/debugging
if (typeof module !== 'undefined' && module.exports) {
    module.exports = { ShoppingCart, CartUtils };
}