// Global JavaScript utilities for AI Study Planner

// Utility functions
const Utils = {
    // Show loading modal
    showLoading(message = 'Processing...') {
        let modal = document.getElementById('loadingModal');
        if (modal) {
            const messageEl = modal.querySelector('.modal-body p');
            if (messageEl) {
                messageEl.textContent = message;
            }
            const bootstrap = window.bootstrap;
            if (bootstrap) {
                new bootstrap.Modal(modal).show();
            }
        }
    },
    
    // Hide loading modal
    hideLoading() {
        const modal = document.getElementById('loadingModal');
        if (modal) {
            const bootstrap = window.bootstrap;
            if (bootstrap) {
                const modalInstance = bootstrap.Modal.getInstance(modal);
                if (modalInstance) {
                    modalInstance.hide();
                }
            }
        }
    },
    
    // Format unit code for display
    formatUnitCode(code) {
        if (!code || typeof code !== 'string') return '';
        return code.toUpperCase().trim();
    },
    
    // Check if a string looks like a unit code
    isValidUnitCode(code) {
        if (!code || typeof code !== 'string') return false;
        const pattern = /^[A-Z]{4}\d{4}$/;
        return pattern.test(code.trim().toUpperCase());
    },
    
    // Debounce function for API calls
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
    },
    
    // Handle API errors gracefully
    handleApiError(error, defaultMessage = 'An error occurred') {
        console.error('API Error:', error);
        
        let message = defaultMessage;
        if (error.response) {
            // Server responded with error status
            message = error.response.data?.error || `Server error: ${error.response.status}`;
        } else if (error.request) {
            // Network error
            message = 'Network error. Please check your connection.';
        } else {
            // Other error
            message = error.message || defaultMessage;
        }
        
        this.showNotification(message, 'error');
        return message;
    },
    
    // Show toast notification
    showNotification(message, type = 'info', duration = 5000) {
        // Remove existing notifications
        document.querySelectorAll('.notification-toast').forEach(n => n.remove());
        
        const notification = document.createElement('div');
        notification.className = `alert alert-${type === 'error' ? 'danger' : type === 'success' ? 'success' : 'info'} notification-toast position-fixed fade show`;
        notification.style.cssText = 'top: 20px; right: 20px; z-index: 1060; max-width: 350px; box-shadow: 0 4px 12px rgba(0,0,0,0.15);';
        
        notification.innerHTML = `
            <div class="d-flex align-items-center">
                <i class="fas fa-${type === 'error' ? 'exclamation-circle' : type === 'success' ? 'check-circle' : 'info-circle'} me-2"></i>
                <span>${message}</span>
                <button type="button" class="btn-close ms-auto" onclick="this.closest('.notification-toast').remove()"></button>
            </div>
        `;
        
        document.body.appendChild(notification);
        
        // Auto-remove
        if (duration > 0) {
            setTimeout(() => {
                if (notification.parentElement) {
                    notification.classList.remove('show');
                    setTimeout(() => notification.remove(), 150);
                }
            }, duration);
        }
    },
    
    // Copy text to clipboard
    async copyToClipboard(text) {
        try {
            await navigator.clipboard.writeText(text);
            this.showNotification('Copied to clipboard!', 'success', 2000);
        } catch (err) {
            console.error('Failed to copy: ', err);
            this.showNotification('Failed to copy to clipboard', 'error');
        }
    },
    
    // Format semester display name
    formatSemesterName(semester) {
        return semester.replace(/([a-z])([A-Z])/g, '$1 $2').replace(/,/g, ',');
    }
};

// API client
const ApiClient = {
    async request(endpoint, options = {}) {
        const defaults = {
            method: 'GET',
            headers: {
                'Content-Type': 'application/json',
            }
        };
        
        const config = { ...defaults, ...options };
        
        try {
            const response = await fetch(endpoint, config);
            
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }
            
            const contentType = response.headers.get('content-type');
            if (contentType && contentType.includes('application/json')) {
                return await response.json();
            }
            
            return response;
            
        } catch (error) {
            Utils.handleApiError(error);
            throw error;
        }
    },
    
    async validatePlan(courseCode, plan) {
        return this.request('/api/validate_plan', {
            method: 'POST',
            body: JSON.stringify({ course_code: courseCode, plan })
        });
    },
    
    async exportPdf(courseCode, plan) {
        return this.request('/api/export_pdf', {
            method: 'POST',
            body: JSON.stringify({ course_code: courseCode, plan })
        });
    }
};

// Initialize global functionality
document.addEventListener('DOMContentLoaded', function() {
    // Initialize tooltips if Bootstrap is available
    if (window.bootstrap && typeof bootstrap.Tooltip !== 'undefined') {
        const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
        tooltipTriggerList.map(function (tooltipTriggerEl) {
            return new bootstrap.Tooltip(tooltipTriggerEl);
        });
    }
    
    // Initialize popovers if Bootstrap is available
    if (window.bootstrap && typeof bootstrap.Popover !== 'undefined') {
        const popoverTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="popover"]'));
        popoverTriggerList.map(function (popoverTriggerEl) {
            return new bootstrap.Popover(popoverTriggerEl);
        });
    }
    
    // Handle form submissions with loading states
    document.querySelectorAll('form[data-loading]').forEach(form => {
        form.addEventListener('submit', function(e) {
            const submitBtn = form.querySelector('[type="submit"]');
            if (submitBtn) {
                submitBtn.disabled = true;
                const originalText = submitBtn.innerHTML;
                submitBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Loading...';
                
                // Re-enable after 5 seconds as fallback
                setTimeout(() => {
                    submitBtn.disabled = false;
                    submitBtn.innerHTML = originalText;
                }, 5000);
            }
        });
    });
    
    // Console welcome message
    if (typeof console !== 'undefined') {
        console.log('%cAI Study Planner', 'color: #007bff; font-size: 20px; font-weight: bold;');
        console.log('%cBuilt for UWA IT Capstone Project 2025', 'color: #6c757d; font-size: 12px;');
    }
});

// Make utilities globally available
window.Utils = Utils;
window.ApiClient = ApiClient;