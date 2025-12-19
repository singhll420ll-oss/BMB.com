/**
 * Admin Panel JavaScript
 * Handles admin-specific functionality and dashboard updates
 */

class AdminPanel {
    constructor() {
        this.stats = {};
        this.realtimeUpdates = {};
        this.init();
    }
    
    init() {
        this.loadDashboardStats();
        this.setupEventListeners();
        this.setupRealtimeUpdates();
        this.initializeDataTables();
        this.setupChartJs();
    }
    
    // Load dashboard statistics
    async loadDashboardStats() {
        try {
            const response = await fetch('/api/orders/stats');
            if (response.ok) {
                this.stats = await response.json();
                this.updateStatsDisplay();
            }
        } catch (error) {
            console.error('Error loading dashboard stats:', error);
        }
        
        // Load recent orders
        this.loadRecentOrders();
        
        // Load recent customers
        this.loadRecentCustomers();
        
        // Load team member stats
        this.loadTeamMemberStats();
    }
    
    // Update stats display
    updateStatsDisplay() {
        // Update order stats cards
        const statCards = {
            'total-orders': this.stats.total_orders || 0,
            'today-orders': this.stats.todays_orders || 0,
            'total-revenue': this.stats.total_revenue || 0,
            'pending-orders': this.stats.orders_by_status?.pending || 0
        };
        
        Object.entries(statCards).forEach(([id, value]) => {
            const element = document.getElementById(id);
            if (element) {
                if (id === 'total-revenue') {
                    element.textContent = `₹${parseFloat(value).toFixed(2)}`;
                } else {
                    element.textContent = value;
                }
            }
        });
        
        // Update order status chart if available
        this.updateOrderStatusChart();
    }
    
    // Load recent orders
    async loadRecentOrders() {
        try {
            const response = await fetch('/api/orders/recent?limit=10');
            if (response.ok) {
                const orders = await response.json();
                this.updateRecentOrdersTable(orders);
            }
        } catch (error) {
            console.error('Error loading recent orders:', error);
        }
    }
    
    // Update recent orders table
    updateRecentOrdersTable(orders) {
        const tableBody = document.getElementById('recent-orders-body');
        if (!tableBody) return;
        
        let rowsHTML = '';
        orders.forEach(order => {
            const statusClass = this.getStatusClass(order.status);
            rowsHTML += `
                <tr>
                    <td>#${order.id}</td>
                    <td>${order.customer_name}</td>
                    <td>${order.service_name}</td>
                    <td>₹${order.total_amount.toFixed(2)}</td>
                    <td>
                        <span class="badge ${statusClass}">${order.status}</span>
                    </td>
                    <td>
                        <button class="btn btn-sm btn-info" 
                                onclick="adminPanel.viewOrderDetails(${order.id})">
                            <i class="fas fa-eye"></i>
                        </button>
                        ${order.status === 'pending' ? `
                        <button class="btn btn-sm btn-warning"
                                onclick="adminPanel.assignOrder(${order.id})">
                            <i class="fas fa-user-plus"></i>
                        </button>
                        ` : ''}
                    </td>
                </tr>
            `;
        });
        
        tableBody.innerHTML = rowsHTML || '<tr><td colspan="6" class="text-center">No orders found</td></tr>';
    }
    
    // Load recent customers
    async loadRecentCustomers() {
        try {
            const response = await fetch('/api/users/customers?limit=10');
            if (response.ok) {
                const customers = await response.json();
                this.updateRecentCustomersTable(customers);
            }
        } catch (error) {
            console.error('Error loading recent customers:', error);
        }
    }
    
    // Update recent customers table
    updateRecentCustomersTable(customers) {
        const tableBody = document.getElementById('recent-customers-body');
        if (!tableBody) return;
        
        let rowsHTML = '';
        customers.forEach(customer => {
            rowsHTML += `
                <tr>
                    <td>${customer.id}</td>
                    <td>${customer.name}</td>
                    <td>${customer.email}</td>
                    <td>${customer.phone}</td>
                    <td>${new Date(customer.created_at).toLocaleDateString()}</td>
                    <td>
                        <button class="btn btn-sm btn-info"
                                onclick="adminPanel.viewCustomerDetails(${customer.id})">
                            <i class="fas fa-eye"></i>
                        </button>
                    </td>
                </tr>
            `;
        });
        
        tableBody.innerHTML = rowsHTML || '<tr><td colspan="6" class="text-center">No customers found</td></tr>';
    }
    
    // Load team member stats
    async loadTeamMemberStats() {
        try {
            const response = await fetch('/api/users/team-members/stats');
            if (response.ok) {
                const stats = await response.json();
                this.updateTeamMemberStats(stats);
            }
        } catch (error) {
            console.error('Error loading team member stats:', error);
        }
    }
    
    // Update team member stats
    updateTeamMemberStats(stats) {
        const container = document.getElementById('team-member-stats');
        if (!container) return;
        
        let statsHTML = '';
        stats.forEach(member => {
            statsHTML += `
                <div class="col-md-4 mb-3">
                    <div class="card">
                        <div class="card-body">
                            <h6 class="card-title">${member.name}</h6>
                            <div class="row">
                                <div class="col-6">
                                    <small class="text-muted">Assigned</small>
                                    <div class="h5">${member.assigned_orders}</div>
                                </div>
                                <div class="col-6">
                                    <small class="text-muted">Delivered</small>
                                    <div class="h5">${member.delivered_orders}</div>
                                </div>
                            </div>
                            <div class="mt-2">
                                <span class="badge bg-${member.is_online ? 'success' : 'secondary'}">
                                    ${member.is_online ? 'Online' : 'Offline'}
                                </span>
                            </div>
                        </div>
                    </div>
                </div>
            `;
        });
        
        container.innerHTML = statsHTML || '<div class="col-12 text-center">No team members found</div>';
    }
    
    // Setup event listeners
    setupEventListeners() {
        // Refresh dashboard button
        document.addEventListener('click', (e) => {
            if (e.target.closest('#refresh-dashboard')) {
                e.preventDefault();
                this.loadDashboardStats();
                this.showNotification('Dashboard refreshed', 'success');
            }
        });
        
        // Export data buttons
        document.addEventListener('click', (e) => {
            if (e.target.closest('.export-data')) {
                e.preventDefault();
                const dataType = e.target.dataset.type;
                this.exportData(dataType);
            }
        });
        
        // Bulk actions
        document.addEventListener('change', (e) => {
            if (e.target.id === 'bulk-action') {
                this.handleBulkAction(e.target.value);
            }
        });
        
        // Search functionality
        const searchInputs = document.querySelectorAll('.admin-search');
        searchInputs.forEach(input => {
            input.addEventListener('input', this.debounce(() => {
                this.handleSearch(input);
            }, 300));
        });
        
        // Filter controls
        const filters = document.querySelectorAll('.admin-filter');
        filters.forEach(filter => {
            filter.addEventListener('change', () => {
                this.applyFilters();
            });
        });
        
        // Date range picker
        const dateRange = document.getElementById('date-range');
        if (dateRange) {
            flatpickr(dateRange, {
                mode: "range",
                dateFormat: "Y-m-d",
                onChange: (selectedDates) => {
                    if (selectedDates.length === 2) {
                        this.applyDateFilter(selectedDates);
                    }
                }
            });
        }
    }
    
    // Setup realtime updates
    setupRealtimeUpdates() {
        // Update stats every 30 seconds
        this.realtimeUpdates.statsInterval = setInterval(() => {
            this.loadDashboardStats();
        }, 30000);
        
        // Listen for new orders via WebSocket or polling
        this.setupOrderNotifications();
    }
    
    // Setup order notifications
    setupOrderNotifications() {
        // Check for new orders every minute
        this.realtimeUpdates.orderCheck = setInterval(async () => {
            try {
                const response = await fetch('/api/orders/recent?limit=1&status=pending');
                if (response.ok) {
                    const orders = await response.json();
                    if (orders.length > 0) {
                        const latestOrder = orders[0];
                        const lastNotified = localStorage.getItem('last_notified_order');
                        
                        if (!lastNotified || parseInt(latestOrder.id) > parseInt(lastNotified)) {
                            this.showNewOrderNotification(latestOrder);
                            localStorage.setItem('last_notified_order', latestOrder.id);
                        }
                    }
                }
            } catch (error) {
                console.error('Error checking new orders:', error);
            }
        }, 60000);
    }
    
    // Show new order notification
    showNewOrderNotification(order) {
        if (!("Notification" in window)) return;
        
        if (Notification.permission === "granted") {
            this.createOrderNotification(order);
        } else if (Notification.permission !== "denied") {
            Notification.requestPermission().then(permission => {
                if (permission === "granted") {
                    this.createOrderNotification(order);
                }
            });
        }
    }
    
    // Create order notification
    createOrderNotification(order) {
        const notification = new Notification("New Order Received!", {
            body: `Order #${order.id} from ${order.customer_name} - ₹${order.total_amount}`,
            icon: '/static/images/logo.png',
            tag: 'new-order'
        });
        
        notification.onclick = () => {
            window.focus();
            this.viewOrderDetails(order.id);
        };
    }
    
    // Initialize DataTables
    initializeDataTables() {
        const dataTables = document.querySelectorAll('.data-table');
        dataTables.forEach(table => {
            if ($.fn.DataTable) {
                $(table).DataTable({
                    pageLength: 25,
                    responsive: true,
                    order: [[0, 'desc']],
                    language: {
                        search: "Search:",
                        lengthMenu: "Show _MENU_ entries",
                        info: "Showing _START_ to _END_ of _TOTAL_ entries",
                        paginate: {
                            first: "First",
                            last: "Last",
                            next: "Next",
                            previous: "Previous"
                        }
                    }
                });
            }
        });
    }
    
    // Setup Chart.js for statistics
    setupChartJs() {
        const orderChart = document.getElementById('order-chart');
        if (orderChart && typeof Chart !== 'undefined') {
            this.orderChart = new Chart(orderChart, {
                type: 'line',
                data: {
                    labels: [],
                    datasets: [{
                        label: 'Orders',
                        data: [],
                        borderColor: '#ff6b35',
                        backgroundColor: 'rgba(255, 107, 53, 0.1)',
                        tension: 0.4
                    }]
                },
                options: {
                    responsive: true,
                    plugins: {
                        legend: {
                            position: 'top',
                        },
                        title: {
                            display: true,
                            text: 'Orders Trend'
                        }
                    }
                }
            });
            
            this.loadOrderChartData();
        }
    }
    
    // Load order chart data
    async loadOrderChartData() {
        try {
            const response = await fetch('/api/orders/chart-data?days=7');
            if (response.ok) {
                const data = await response.json();
                this.updateOrderChart(data);
            }
        } catch (error) {
            console.error('Error loading chart data:', error);
        }
    }
    
    // Update order chart
    updateOrderChart(data) {
        if (!this.orderChart) return;
        
        this.orderChart.data.labels = data.labels;
        this.orderChart.data.datasets[0].data = data.values;
        this.orderChart.update();
    }
    
    // Update order status chart
    updateOrderStatusChart() {
        const chartElement = document.getElementById('order-status-chart');
        if (!chartElement || !this.stats.orders_by_status) return;
        
        if (typeof Chart !== 'undefined') {
            // Destroy existing chart if any
            if (this.statusChart) {
                this.statusChart.destroy();
            }
            
            const statusData = this.stats.orders_by_status;
            const labels = Object.keys(statusData).map(status => 
                status.charAt(0).toUpperCase() + status.slice(1)
            );
            const values = Object.values(statusData);
            const colors = labels.map(label => this.getStatusColor(label.toLowerCase()));
            
            this.statusChart = new Chart(chartElement, {
                type: 'doughnut',
                data: {
                    labels: labels,
                    datasets: [{
                        data: values,
                        backgroundColor: colors,
                        borderWidth: 1
                    }]
                },
                options: {
                    responsive: true,
                    plugins: {
                        legend: {
                            position: 'right',
                        },
                        title: {
                            display: true,
                            text: 'Order Status Distribution'
                        }
                    }
                }
            });
        }
    }
    
    // Get status class for badge
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
    
    // Get status color for chart
    getStatusColor(status) {
        const colors = {
            pending: '#ffc107',
            confirmed: '#17a2b8',
            preparing: '#007bff',
            out_for_delivery: '#28a745',
            delivered: '#20c997',
            cancelled: '#dc3545'
        };
        return colors[status] || '#6c757d';
    }
    
    // View order details
    viewOrderDetails(orderId) {
        // Use HTMX to load order details
        const modal = document.getElementById('order-details-modal');
        if (modal && htmx) {
            htmx.ajax('GET', `/admin/orders/${orderId}/details`, '#order-details-content');
            new bootstrap.Modal(modal).show();
        } else {
            // Fallback to page navigation
            window.location.href = `/admin/orders/${orderId}`;
        }
    }
    
    // View customer details
    viewCustomerDetails(customerId) {
        const modal = document.getElementById('customer-details-modal');
        if (modal && htmx) {
            htmx.ajax('GET', `/admin/customers/${customerId}`, '#customer-details-content');
            new bootstrap.Modal(modal).show();
        }
    }
    
    // Assign order
    assignOrder(orderId) {
        const modal = document.getElementById('assign-order-modal');
        if (modal) {
            document.getElementById('assign-order-id').value = orderId;
            
            // Load team members for dropdown
            this.loadTeamMembersForAssignment(orderId);
            
            new bootstrap.Modal(modal).show();
        }
    }
    
    // Load team members for assignment
    async loadTeamMembersForAssignment(orderId) {
        try {
            const response = await fetch('/api/users/team-members?active=true');
            if (response.ok) {
                const teamMembers = await response.json();
                const select = document.getElementById('assign-team-member');
                
                if (select) {
                    select.innerHTML = '<option value="">Select Team Member</option>';
                    teamMembers.forEach(member => {
                        select.innerHTML += `<option value="${member.id}">${member.name}</option>`;
                    });
                    
                    // Set up assignment form
                    const form = document.getElementById('assign-order-form');
                    if (form) {
                        form.onsubmit = (e) => {
                            e.preventDefault();
                            this.submitAssignment(orderId, select.value);
                        };
                    }
                }
            }
        } catch (error) {
            console.error('Error loading team members:', error);
        }
    }
    
    // Submit assignment
    async submitAssignment(orderId, teamMemberId) {
        if (!teamMemberId) {
            this.showNotification('Please select a team member', 'error');
            return;
        }
        
        try {
            const response = await fetch(`/api/orders/${orderId}/assign`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ team_member_id: parseInt(teamMemberId) }),
                credentials: 'include'
            });
            
            if (response.ok) {
                this.showNotification('Order assigned successfully', 'success');
                bootstrap.Modal.getInstance(document.getElementById('assign-order-modal')).hide();
                this.loadDashboardStats();
            } else {
                const error = await response.json();
                this.showNotification(error.detail || 'Assignment failed', 'error');
            }
        } catch (error) {
            console.error('Error assigning order:', error);
            this.showNotification('Network error', 'error');
        }
    }
    
    // Export data
    async exportData(dataType) {
        this.showNotification(`Exporting ${dataType} data...`, 'info');
        
        try {
            const response = await fetch(`/api/export/${dataType}`);
            if (response.ok) {
                const blob = await response.blob();
                const url = window.URL.createObjectURL(blob);
                const a = document.createElement('a');
                a.href = url;
                a.download = `${dataType}-${new Date().toISOString().split('T')[0]}.csv`;
                document.body.appendChild(a);
                a.click();
                document.body.removeChild(a);
                window.URL.revokeObjectURL(url);
                
                this.showNotification(`${dataType} exported successfully`, 'success');
            } else {
                this.showNotification('Export failed', 'error');
            }
        } catch (error) {
            console.error('Error exporting data:', error);
            this.showNotification('Export failed', 'error');
        }
    }
    
    // Handle bulk action
    handleBulkAction(action) {
        const selectedItems = this.getSelectedItems();
        if (selectedItems.length === 0) {
            this.showNotification('Please select items first', 'warning');
            return;
        }
        
        switch (action) {
            case 'delete':
                if (confirm(`Delete ${selectedItems.length} selected item(s)?`)) {
                    this.performBulkDelete(selectedItems);
                }
                break;
            case 'export':
                this.exportSelectedItems(selectedItems);
                break;
            case 'status_change':
                this.showBulkStatusChangeModal(selectedItems);
                break;
        }
        
        // Reset select
        document.getElementById('bulk-action').value = '';
    }
    
    // Get selected items from checkboxes
    getSelectedItems() {
        const checkboxes = document.querySelectorAll('.item-checkbox:checked');
        return Array.from(checkboxes).map(cb => cb.value);
    }
    
    // Perform bulk delete
    async performBulkDelete(items) {
        try {
            const response = await fetch('/api/bulk/delete', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ items }),
                credentials: 'include'
            });
            
            if (response.ok) {
                this.showNotification(`${items.length} items deleted`, 'success');
                this.loadDashboardStats();
            } else {
                this.showNotification('Delete failed', 'error');
            }
        } catch (error) {
            console.error('Error in bulk delete:', error);
            this.showNotification('Delete failed', 'error');
        }
    }
    
    // Export selected items
    exportSelectedItems(items) {
        // Create CSV data
        const headers = ['ID', 'Name', 'Type', 'Created At'];
        const csvData = [headers.join(',')];
        
        items.forEach(id => {
            // In a real implementation, you would fetch item details
            const row = [id, 'Item ' + id, 'Unknown', new Date().toISOString()];
            csvData.push(row.join(','));
        });
        
        const csvContent = csvData.join('\n');
        const blob = new Blob([csvContent], { type: 'text/csv' });
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `selected-items-${new Date().getTime()}.csv`;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        window.URL.revokeObjectURL(url);
        
        this.showNotification('Items exported', 'success');
    }
    
    // Show bulk status change modal
    showBulkStatusChangeModal(items) {
        const modal = document.getElementById('bulk-status-modal');
        if (modal) {
            document.getElementById('bulk-status-items').value = items.join(',');
            new bootstrap.Modal(modal).show();
        }
    }
    
    // Handle search
    handleSearch(input) {
        const searchTerm = input.value.toLowerCase();
        const tableId = input.dataset.table;
        const table = document.getElementById(tableId);
        
        if (!table) return;
        
        const rows = table.querySelectorAll('tbody tr');
        rows.forEach(row => {
            const text = row.textContent.toLowerCase();
            row.style.display = text.includes(searchTerm) ? '' : 'none';
        });
    }
    
    // Apply filters
    applyFilters() {
        const filters = {};
        document.querySelectorAll('.admin-filter').forEach(filter => {
            if (filter.value) {
                filters[filter.name] = filter.value;
            }
        });
        
        // Reload data with filters
        this.loadFilteredData(filters);
    }
    
    // Apply date filter
    applyDateFilter(dates) {
        const [startDate, endDate] = dates;
        this.loadFilteredData({
            start_date: startDate.toISOString().split('T')[0],
            end_date: endDate.toISOString().split('T')[0]
        });
    }
    
    // Load filtered data
    async loadFilteredData(filters) {
        const queryString = new URLSearchParams(filters).toString();
        
        try {
            const response = await fetch(`/api/admin/filtered-data?${queryString}`);
            if (response.ok) {
                const data = await response.json();
                this.updateFilteredTable(data);
            }
        } catch (error) {
            console.error('Error loading filtered data:', error);
        }
    }
    
    // Update filtered table
    updateFilteredTable(data) {
        // Implementation depends on specific table structure
        console.log('Filtered data:', data);
        // Update the relevant table with filtered data
    }
    
    // Show notification
    showNotification(message, type = 'info') {
        // Use toast notifications if available
        if (typeof bootstrap !== 'undefined' && bootstrap.Toast) {
            const toastEl = document.getElementById('admin-toast');
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
            alert(`${type.toUpperCase()}: ${message}`);
        }
    }
    
    // Debounce function for search
    debounce(func, wait) {
        let timeout;
        return function executedFunction(...args) {
            const later = () => {
                clearTimeout(timeout);
                func(...args);
            };
            clearTimeout(timeout);
            timeout = setTimeout(later, wait);
        };
    }
    
    // Cleanup on page unload
    cleanup() {
        if (this.realtimeUpdates.statsInterval) {
            clearInterval(this.realtimeUpdates.statsInterval);
        }
        if (this.realtimeUpdates.orderCheck) {
            clearInterval(this.realtimeUpdates.orderCheck);
        }
    }
}

// Initialize admin panel
let adminPanel;

document.addEventListener('DOMContentLoaded', () => {
    // Check if user is admin
    if (window.AppState && window.AppState.user && window.AppState.user.role === 'admin') {
        adminPanel = new AdminPanel();
        window.adminPanel = adminPanel;
        
        // Setup cleanup on page unload
        window.addEventListener('beforeunload', () => {
            if (adminPanel) {
                adminPanel.cleanup();
            }
        });
    }
});

// Admin utility functions
const AdminUtils = {
    // Format date for display
    formatDate: function(dateString) {
        return new Date(dateString).toLocaleDateString('en-IN', {
            year: 'numeric',
            month: 'short',
            day: 'numeric',
            hour: '2-digit',
            minute: '2-digit'
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
    
    // Calculate percentage
    calculatePercentage: function(part, total) {
        if (total === 0) return 0;
        return ((part / total) * 100).toFixed(1);
    },
    
    // Generate report data
    generateReport: function(data, type = 'daily') {
        const report = {
            labels: [],
            values: []
        };
        
        if (type === 'daily') {
            // Group by day
            const grouped = data.reduce((acc, item) => {
                const date = new Date(item.created_at).toLocaleDateString();
                if (!acc[date]) acc[date] = 0;
                acc[date] += item.amount || 1;
                return acc;
            }, {});
            
            report.labels = Object.keys(grouped);
            report.values = Object.values(grouped);
        }
        
        return report;
    },
    
    // Export to CSV
    exportToCSV: function(data, filename) {
        if (!data || data.length === 0) return;
        
        const headers = Object.keys(data[0]);
        const csvRows = [
            headers.join(','),
            ...data.map(row => 
                headers.map(header => {
                    const value = row[header];
                    if (value === null || value === undefined) return '';
                    if (typeof value === 'string') return `"${value.replace(/"/g, '""')}"`;
                    return value;
                }).join(',')
            )
        ];
        
        const csvContent = csvRows.join('\n');
        const blob = new Blob([csvContent], { type: 'text/csv' });
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = filename || 'export.csv';
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        window.URL.revokeObjectURL(url);
    },
    
    // Print element
    printElement: function(elementId) {
        const element = document.getElementById(elementId);
        if (!element) return;
        
        const printWindow = window.open('', '_blank');
        printWindow.document.write(`
            <html>
                <head>
                    <title>Print</title>
                    <style>
                        body { font-family: Arial, sans-serif; }
                        table { width: 100%; border-collapse: collapse; }
                        th, td { border: 1px solid #ddd; padding: 8px; text-align: left; }
                        th { background-color: #f2f2f2; }
                        @media print {
                            .no-print { display: none; }
                        }
                    </style>
                </head>
                <body>
                    ${element.innerHTML}
                </body>
            </html>
        `);
        printWindow.document.close();
        printWindow.print();
    }
};

// Export for testing/debugging
if (typeof module !== 'undefined' && module.exports) {
    module.exports = { AdminPanel, AdminUtils };
}