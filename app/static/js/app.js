// AI Study Planner Frontend JavaScript

$(document).ready(function() {
    initializeApp();
});

let currentPlan = {};
let availableUnits = [];
let allUnitsData = [];
let sortableInstances = [];

function initializeApp() {
    loadMajors();
    setupEventHandlers();
    setupDragAndDrop();
}

function setupEventHandlers() {
    $('#major-select').on('change', function() {
        const majorId = $(this).val();
        $('#generate-plan').prop('disabled', !majorId);
    });

    $('#generate-plan').on('click', function() {
        generateStudyPlan();
    });

    $('#export-pdf').on('click', function() {
        exportToPDF();
    });

    $('#ai-validate-plan').on('click', function() {
        aiValidatePlan();
    });

    $('#unit-search').on('input', function() {
        filterUnits($(this).val());
    });
}

// DRAG & DROP

function setupDragAndDrop() {
    const semesters = [
        'Year 1, Semester 1', 'Year 1, Semester 2',
        'Year 2, Semester 1', 'Year 2, Semester 2',
        'Year 3, Semester 1', 'Year 3, Semester 2'
    ];

    semesters.forEach(semester => {
        const element = document.getElementById(semester);
        if (element) {
            const sortable = Sortable.create(element, {
                group: 'units',
                animation: 150,
                onAdd: handleUnitMove,
                onUpdate: handleUnitMove,
                onRemove: function(evt) {
                    const removedUnitCode = $(evt.item).data('unit-code');
                    updateDropZone(evt.from);
                    checkDependentUnitsAfterRemoval(removedUnitCode);
                }
            });
            sortableInstances.push(sortable);
        }
    });

    const availableUnitsElement = document.getElementById('available-units');
    if (availableUnitsElement) {
        Sortable.create(availableUnitsElement, {
            group: { name: 'units', pull: 'clone', put: true },
            sort: false,
            animation: 150,
            onAdd: function(evt) {
                const removedUnitCode = $(evt.item).data('unit-code');
                evt.item.remove();
                updateAvailableUnitsFilter();
                checkDependentUnitsAfterRemoval(removedUnitCode);
                validatePlan();
            }
        });
    }

    const trashZone = document.getElementById('trash-zone');
    if (trashZone) {
        Sortable.create(trashZone, {
            group: { name: 'units', pull: false, put: true },
            animation: 150,
            onAdd: function(evt) {
                const removedUnitCode = $(evt.item).data('unit-code');
                evt.item.remove();
                updateAvailableUnitsFilter();
                checkDependentUnitsAfterRemoval(removedUnitCode);
                validatePlan();
                updateValidationStatus('Unit removed from plan', 'success');
            }
        });
    }
}

// MAJOR & PLAN

function loadMajors() {
    $.get('/api/majors')
        .done(function(data) {
            const select = $('#major-select');
            select.empty().append('<option value="">Select a Major...</option>');
            data.majors.forEach(major => {
                select.append(`<option value="${major.id}">${major.code} - ${major.name}</option>`);
            });
        })
        .fail(function() {
            showError('Failed to load majors');
        });
}

function generateStudyPlan() {
    const majorId = $('#major-select').val();
    if (!majorId) return;

    showLoading('Generating study plan...');

    $.ajax({
        url: '/api/generate_plan',
        method: 'POST',
        contentType: 'application/json',
        data: JSON.stringify({ major_id: parseInt(majorId) }),
        success: function(data) {
            hideLoading();
            currentPlan = data.plan;

            allUnitsData = [];
            if (data.enriched_plan) {
                Object.keys(data.enriched_plan).forEach(semester => {
                    data.enriched_plan[semester].forEach(unitData => {
                        allUnitsData.push(unitData);
                    });
                });
            }

            const planToDisplay = data.enriched_plan || data.plan;
            displayStudyPlan(planToDisplay, !!data.enriched_plan);

            if (data.major_electives || data.general_electives) {
                displayCategorizedUnits(data.major_electives || [], data.general_electives || []);
            } else {
                loadAvailableUnits();
            }

            updateValidationStatus('Plan generated successfully', 'success');
        },
        error: function(xhr) {
            hideLoading();
            showError('Failed to generate plan: ' + (xhr.responseJSON?.error || 'Unknown error'));
        }
    });
}

// DISPLAY & VALIDATION

// AVAILABLE UNITS

// STATUS & EXPORT

function updateValidationStatus(message, type) {
    const statusDiv = $('#validation-status');
    statusDiv.removeClass('validation-success validation-error validation-warning');
    switch(type) {
        case 'success': statusDiv.addClass('validation-success'); break;
        case 'error': statusDiv.addClass('validation-error'); break;
        case 'warning': statusDiv.addClass('validation-warning'); break;
    }
    statusDiv.html(`<strong>${type.charAt(0).toUpperCase() + type.slice(1)}:</strong> ${message}`);
}

function exportToPDF() {
    const plan = getCurrentPlan();
    const hasUnits = Object.values(plan).some(semester => semester.length > 0);
    if (!hasUnits) {
        showError('No units in plan to export');
        return;
    }
    showLoading('Generating PDF...');
    fetch('/api/export_pdf', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ plan: plan })
    })
    .then(response => {
        if (!response.ok) {
            return response.json().then(err => Promise.reject(err));
        }
        return response.blob();
    })
    .then(blob => {
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.style.display = 'none';
        a.href = url;
        a.download = `study_plan_${new Date().toISOString().slice(0,19).replace(/:/g,'-')}.pdf`;
        document.body.appendChild(a);
        a.click();
        window.URL.revokeObjectURL(url);
        document.body.removeChild(a);
        hideLoading();
        updateValidationStatus('PDF exported successfully', 'success');
    })
    .catch(error => {
        hideLoading();
        showError('Failed to export PDF: ' + (error.error || 'Unknown error'));
    });
}

// AI VALIDATION + INDICATOR

function aiValidatePlan() {
    const plan = getCurrentPlan();
    const majorId = $('#major-select').val();

    const hasUnits = Object.values(plan).some(semester => semester.length > 0);
    if (!hasUnits) {
        showError('No units in plan to validate');
        return;
    }
    if (!majorId) {
        showError('Please select a major first');
        return;
    }

    showLoading('Running AI quality analysis...');

    fetch('/api/ai_validate_plan', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ plan: plan, major_code: majorId })
    })
    .then(response => {
        if (!response.ok) {
            return response.json().then(err => Promise.reject(err));
        }
        return response.json();
    })
    .then(result => {
        hideLoading();
        updateAIStatusIndicator(result);
        showQualityCheckModal(result);
    })
    .catch(error => {
        hideLoading();
        showError('Failed to validate plan: ' + (error.error || 'Unknown error'));
        $('#ai-status-indicator').show().removeClass('bg-success bg-warning').addClass('bg-danger').text('Fail');
    });
}

function updateAIStatusIndicator(result) {
    const indicator = $('#ai-status-indicator');
    const overallQuality = result.overallQuality || 'unknown';

    indicator.show().removeClass('bg-success bg-warning bg-danger').text('');

    switch (overallQuality) {
        case 'excellent':
        case 'good':
            indicator.addClass('bg-success').text('Pass');
            break;
        case 'fair':
            indicator.addClass('bg-warning').text('Warning');
            break;
        case 'poor':
            indicator.addClass('bg-danger').text('Fail');
            break;
        default:
            indicator.text('N/A');
            break;
    }
}

// QUALITY CHECK MODAL

// HELPERS

function showLoading(message) {
    $('#loading-message').text(message);
    $('#loading-modal').modal('show');
}

function hideLoading() {
    $('#loading-modal').modal('hide');
}

function showError(message) {
    alert(message);
}
