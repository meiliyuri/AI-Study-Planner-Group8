// Study Plan Drag & Drop and Validation JavaScript

class StudyPlanManager {
    constructor() {
        this.planData = window.studyPlanData || {};
        this.programCode = window.programCode || window.courseCode; // Support both new and old
        this.isValidating = false;
        this.hasUserMadeChanges = false;
        
        this.initializeEventListeners();
        // Don't auto-validate on page load - only validate when user makes changes
    }
    
    initializeEventListeners() {
        // Export button
        const exportBtn = document.getElementById('exportBtn');
        if (exportBtn) {
            exportBtn.addEventListener('click', () => this.exportPDF());
        }
        
        // Set up drag and drop for existing units
        this.setupDragAndDrop();
    }
    
    setupDragAndDrop() {
        // Make all unit cards draggable
        document.querySelectorAll('.unit-card').forEach(card => {
            card.draggable = true;
            card.addEventListener('dragstart', this.handleDragStart.bind(this));
            card.addEventListener('dragend', this.handleDragEnd.bind(this));
        });
        
        // Make all semester containers droppable
        document.querySelectorAll('.units-container').forEach(container => {
            container.addEventListener('dragover', this.handleDragOver.bind(this));
            container.addEventListener('drop', this.handleDrop.bind(this));
            container.addEventListener('dragenter', this.handleDragEnter.bind(this));
            container.addEventListener('dragleave', this.handleDragLeave.bind(this));
        });
    }
    
    handleDragStart(e) {
        const unitCard = e.target;
        unitCard.classList.add('dragging');
        
        e.dataTransfer.setData('text/plain', JSON.stringify({
            unitCode: unitCard.dataset.unit,
            sourceSemester: unitCard.closest('.semester-container').dataset.semester
        }));
    }
    
    handleDragEnd(e) {
        e.target.classList.remove('dragging');
    }
    
    handleDragOver(e) {
        e.preventDefault();
    }
    
    handleDragEnter(e) {
        e.preventDefault();
        if (e.target.classList.contains('units-container')) {
            e.target.classList.add('drag-over');
        }
    }
    
    handleDragLeave(e) {
        if (e.target.classList.contains('units-container')) {
            e.target.classList.remove('drag-over');
        }
    }
    
    handleDrop(e) {
        e.preventDefault();
        const container = e.target.closest('.units-container');
        if (!container) return;
        
        container.classList.remove('drag-over');
        
        try {
            const dragData = JSON.parse(e.dataTransfer.getData('text/plain'));
            const targetSemester = container.closest('.semester-container').dataset.semester;
            
            if (dragData.sourceSemester === targetSemester) {
                return; // No change needed
            }
            
            this.moveUnit(dragData.unitCode, dragData.sourceSemester, targetSemester);
            
        } catch (error) {
            console.error('Error handling drop:', error);
        }
    }
    
    moveUnit(unitCode, fromSemester, toSemester) {
        // Update the visual representation
        const unitCard = document.querySelector(`[data-unit="${unitCode}"]`);
        const targetContainer = document.querySelector(`[data-semester="${toSemester}"] .units-container`);
        
        if (unitCard && targetContainer) {
            targetContainer.appendChild(unitCard);
            
            // Update internal data structure
            this.updatePlanData(unitCode, fromSemester, toSemester);
            
            // Mark that user has made changes and validate
            this.hasUserMadeChanges = true;
            this.validateCurrentPlan();
        }
    }
    
    updatePlanData(unitCode, fromSemester, toSemester) {
        // Remove from source semester
        if (this.planData[fromSemester]) {
            const index = this.planData[fromSemester].indexOf(unitCode);
            if (index > -1) {
                this.planData[fromSemester].splice(index, 1);
            }
        }
        
        // Add to target semester
        if (!this.planData[toSemester]) {
            this.planData[toSemester] = [];
        }
        this.planData[toSemester].push(unitCode);
    }
    
    async validateCurrentPlan() {
        if (this.isValidating) return;
        
        this.isValidating = true;
        this.showValidationLoading();
        
        try {
            const response = await fetch('/api/validate_plan', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    program_code: this.programCode,
                    plan: this.planData
                })
            });
            
            const result = await response.json();
            this.displayValidationResult(result);
            
        } catch (error) {
            console.error('Validation error:', error);
            this.displayValidationError('Unable to validate plan. Please try again.');
        } finally {
            this.isValidating = false;
        }
    }
    
    showValidationLoading() {
        const validationStatus = document.getElementById('validationStatus');
        validationStatus.innerHTML = `
            <div class="text-center">
                <div class="spinner-border spinner-small text-primary" role="status">
                    <span class="visually-hidden">Validating...</span>
                </div>
                <p class="mt-2 mb-0">Validating plan...</p>
            </div>
        `;
    }
    
    displayValidationResult(result) {
        const validationStatus = document.getElementById('validationStatus');
        
        if (result.isValid) {
            validationStatus.innerHTML = `
                <div class="validation-success p-3 rounded">
                    <i class="fas fa-check-circle text-success"></i>
                    <strong class="text-success ms-2">Plan is valid!</strong>
                </div>
            `;
        } else {
            let errorHtml = `
                <div class="validation-error p-3 rounded">
                    <i class="fas fa-exclamation-triangle text-danger"></i>
                    <strong class="text-danger ms-2">Validation Issues:</strong>
                    <ul class="mt-2 mb-0">
            `;
            
            if (result.errors) {
                result.errors.forEach(error => {
                    errorHtml += `<li>${error}</li>`;
                });
            }
            
            errorHtml += '</ul></div>';
            
            if (result.warnings && result.warnings.length > 0) {
                errorHtml += `
                    <div class="validation-warning p-3 rounded mt-2">
                        <strong class="text-warning">Warnings:</strong>
                        <ul class="mt-1 mb-0">
                `;
                result.warnings.forEach(warning => {
                    errorHtml += `<li>${warning}</li>`;
                });
                errorHtml += '</ul></div>';
            }
            
            validationStatus.innerHTML = errorHtml;
        }
    }
    
    displayValidationError(message) {
        const validationStatus = document.getElementById('validationStatus');
        validationStatus.innerHTML = `
            <div class="validation-error p-3 rounded">
                <i class="fas fa-times-circle text-danger"></i>
                <strong class="text-danger ms-2">Validation Error</strong>
                <p class="mb-0 mt-1">${message}</p>
            </div>
        `;
    }
    
    async exportPDF() {
        const exportBtn = document.getElementById('exportBtn');
        const originalText = exportBtn.innerHTML;
        
        try {
            exportBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Generating...';
            exportBtn.disabled = true;
            
            const response = await fetch('/api/export_pdf', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    program_code: this.programCode,
                    plan: this.planData
                })
            });
            
            if (response.ok) {
                const blob = await response.blob();
                const url = window.URL.createObjectURL(blob);
                const a = document.createElement('a');
                a.href = url;
                a.download = `study_plan_${this.programCode}.pdf`;
                document.body.appendChild(a);
                a.click();
                window.URL.revokeObjectURL(url);
                document.body.removeChild(a);
                
                // Show success feedback
                this.showNotification('PDF exported successfully!', 'success');
            } else {
                throw new Error('Failed to generate PDF');
            }
            
        } catch (error) {
            console.error('Export error:', error);
            this.showNotification('Failed to export PDF. Please try again.', 'error');
        } finally {
            exportBtn.innerHTML = originalText;
            exportBtn.disabled = false;
        }
    }
    
    showNotification(message, type = 'info') {
        // Create and show a temporary notification
        const notification = document.createElement('div');
        notification.className = `alert alert-${type === 'error' ? 'danger' : type === 'success' ? 'success' : 'info'} alert-dismissible fade show position-fixed`;
        notification.style.cssText = 'top: 20px; right: 20px; z-index: 1050; max-width: 300px;';
        notification.innerHTML = `
            ${message}
            <button type="button" class="btn-close" onclick="this.parentElement.remove()"></button>
        `;
        
        document.body.appendChild(notification);
        
        // Auto-remove after 5 seconds
        setTimeout(() => {
            if (notification.parentElement) {
                notification.remove();
            }
        }, 5000);
    }
}

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    window.studyPlanManager = new StudyPlanManager();
});

// Legacy functions for backward compatibility (if needed)
function allowDrop(ev) {
    ev.preventDefault();
}

function drag(ev) {
    // This is handled by the StudyPlanManager class now
}

function drop(ev) {
    // This is handled by the StudyPlanManager class now
}