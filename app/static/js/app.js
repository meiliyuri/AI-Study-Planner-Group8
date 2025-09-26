// AI Study Planner Frontend JavaScript

$(document).ready(function() {
    // Initialize the application
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
    // AI Send Button
    $('#ai-send-btn').on('click', async function() {
        const userInput = $('#ai-user-input').val().trim();
        if (!userInput) return;

        const log = $('#debug-log');
        const userMsg = $('<div class="text-end mb-2"><strong>You:</strong> ' + userInput + '</div>');
        log.append(userMsg);

        try {
            const response = await fetch('/api/ai-regenerate', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ comment: userInput })
            });
            const data = await response.json();

            const aiMsg = $('<div class="text-start mb-2"><strong>AI:</strong> ' + data.response + '</div>');
            log.append(aiMsg);

            log.scrollTop(log.prop("scrollHeight")); 
            $('#ai-user-input').val(''); 
        } catch (err) {
            console.error(err);
        }
    });
}

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
                onAdd: function(evt) {
                    handleUnitMove(evt);
                },
                onUpdate: function(evt) {
                    handleUnitMove(evt);
                },
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
            group: {
                name: 'units',
                pull: 'clone',
                put: true
            },
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
            group: {
                name: 'units',
                pull: false,
                put: true
            },
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

function displayStudyPlan(plan, isEnriched = false) {
    $('#study-plan-container .text-center').hide();
    $('#plan-grid').show();
    $('#export-pdf').prop('disabled', false);
    $('#ai-validate-plan').prop('disabled', false);

    $('.semester-units').each(function() {
        $(this).empty().append('<div class="drop-zone">Drop units here (4 max)</div>');
    });

    Object.keys(plan).forEach(semester => {
        const semesterElement = $(`#${CSS.escape(semester)}`);
        if (semesterElement.length) {
            let semesterUnits = plan[semester];

            if (isEnriched) {
                semesterUnits = [...semesterUnits].sort((a, b) => {
                    if (a.level !== b.level) {
                        return a.level - b.level;
                    }
                    return a.code.localeCompare(b.code);
                });
            }

            semesterUnits.forEach(unitData => {
                if (isEnriched) {
                    addUnitToSemester(semesterElement, unitData.code, unitData);
                } else {
                    addUnitToSemester(semesterElement, unitData);
                }
            });
        }
    });

    updateAllDropZones();
    updateAvailableUnitsFilter();
    validateAndHighlightAllUnits();
}

function addUnitToSemester(semesterElement, unitCode, unitData = null) {
    const unitCard = createUnitCard(unitCode, unitData);
    semesterElement.append(unitCard);
}

function createUnitCard(unitCode, unitData = null) {
    if (!unitData) {
        unitData = allUnitsData.find(unit => unit.code === unitCode) || {
            code: unitCode,
            title: 'Unknown Unit',
            level: 1
        };
    }

    return `
        <div class="unit-card" data-unit-code="${unitData.code}">
            <div class="unit-code">${unitData.code}</div>
            <div class="unit-title">${unitData.title}</div>
            <span class="unit-level level-${unitData.level}">L${unitData.level}</span>
        </div>
    `;
}

function handleUnitMove(evt) {
    const semester = evt.to.dataset.semester;
    const unitCount = $(evt.to).find('.unit-card').length;
    const unitCode = $(evt.item).data('unit-code');

    updateDropZone(evt.to);
    updateAvailableUnitsFilter();

    if (unitCount > 4) {
        updateValidationStatus(`${semester} has ${unitCount} units (max 4 allowed)`, 'error');
    } else {
        const constraintValidation = validateUnitConstraints(unitCode, semester);
        if (!constraintValidation.isValid) {
            updateValidationStatus(constraintValidation.message, constraintValidation.type);
        } else {
            validatePlan();
        }
    }

    validateAndHighlightAllUnits();
}

function updateDropZone(semesterElement) {
    const unitCount = $(semesterElement).find('.unit-card').length;
    const dropZone = $(semesterElement).find('.drop-zone');

    if (unitCount > 0) {
        dropZone.hide();
        $(semesterElement).addClass('has-units');
    } else {
        dropZone.show();
        $(semesterElement).removeClass('has-units');
    }

    if (unitCount === 4) {
        $(semesterElement).closest('.semester-container').addClass('semester-full');
    } else {
        $(semesterElement).closest('.semester-container').removeClass('semester-full');
    }
}

function updateAllDropZones() {
    $('.semester-units').each(function() {
        updateDropZone(this);
    });
}

function validatePlan() {
    const localValidation = validatePlanLocally();

    if (!localValidation.isValid) {
        updateValidationStatus(localValidation.reason, localValidation.type);
        return;
    }

    const plan = getCurrentPlan();

    $.ajax({
        url: '/api/validate_plan',
        method: 'POST',
        contentType: 'application/json',
        data: JSON.stringify({ plan: plan }),
        success: function(data) {
            const statusType = data.type || (data.isValid ? 'success' : 'error');
            updateValidationStatus(data.reason, statusType);
        },
        error: function(xhr) {
            updateValidationStatus('Validation failed', 'error');
        }
    });
}

function validatePlanLocally() {
    const issues = [];
    const warnings = [];

    $('.semester-units').each(function() {
        const semesterName = $(this).attr('id');
        const unitCount = $(this).find('.unit-card').length;

        if (unitCount > 4) {
            issues.push(`${semesterName} has ${unitCount} units (max 4 allowed)`);
        } else if (unitCount > 0 && unitCount < 4) {
            warnings.push(`${semesterName} has only ${unitCount} units`);
        }
    });

    const totalUnits = $('.semester-units .unit-card').length;
    if (totalUnits > 24) {
        issues.push(`Total ${totalUnits} units exceeds maximum of 24`);
    } else if (totalUnits < 24) {
        warnings.push(`Plan has ${totalUnits} units (target: 24)`);
    }

    if (issues.length > 0) {
        return { isValid: false, reason: issues[0], type: 'error' };
    } else if (warnings.length > 0) {
        return { isValid: true, reason: warnings[0] + ' - plan incomplete', type: 'warning' };
    } else {
        return { isValid: true, reason: 'Plan structure looks good', type: 'success' };
    }
}

function validateUnitConstraints(unitCode, targetSemester) {
    const unitData = allUnitsData.find(unit => unit.code === unitCode);
    if (!unitData) {
        return { isValid: false, message: `Unit data not found for ${unitCode}`, type: 'error' };
    }

    const semesterCheck = checkSemesterAvailability(unitData, targetSemester);
    if (!semesterCheck.isValid) {
        return semesterCheck;
    }

    const prereqCheck = checkPrerequisites(unitData, targetSemester);
    if (!prereqCheck.isValid) {
        return prereqCheck;
    }

    return { isValid: true, message: 'Constraints satisfied', type: 'success' };
}

function checkSemesterAvailability(unitData, targetSemester) {
    if (!unitData.availabilities) {
        return { isValid: true, message: 'No semester restrictions', type: 'success' };
    }

    const availabilities = unitData.availabilities.toLowerCase();
    const semesterNum = targetSemester.includes('Semester 1') ? 1 : 2;

    if (availabilities.includes('semester 1') && !availabilities.includes('semester 2')) {
        if (semesterNum !== 1) {
            return { isValid: false, message: `${unitData.code} is only available in Semester 1`, type: 'error' };
        }
    } else if (availabilities.includes('semester 2') && !availabilities.includes('semester 1')) {
        if (semesterNum !== 2) {
            return { isValid: false, message: `${unitData.code} is only available in Semester 2`, type: 'error' };
        }
    }

    return { isValid: true, message: 'Semester availability satisfied', type: 'success' };
}

function checkPrerequisites(unitData, targetSemester) {
    if (!unitData.prerequisites || unitData.prerequisites.toLowerCase().includes('nil')) {
        return { isValid: true, message: 'No prerequisites', type: 'success' };
    }

    if (unitData.level === 1) {
        return { isValid: true, message: 'Level 1 unit - ATAR requirements assumed', type: 'success' };
    }

    const unitsTakenBefore = getUnitsTakenBefore(targetSemester);
    const prereqResult = parseAndCheckPrerequisites(unitData.prerequisites, unitsTakenBefore);

    if (!prereqResult.isValid) {
        return { isValid: false, message: `${unitData.code}: ${prereqResult.message}`, type: 'warning' };
    }

    return { isValid: true, message: 'Prerequisites satisfied', type: 'success' };
}

function getUnitsTakenBefore(targetSemester) {
    const semesterOrder = [
        'Year 1, Semester 1', 'Year 1, Semester 2',
        'Year 2, Semester 1', 'Year 2, Semester 2',
        'Year 3, Semester 1', 'Year 3, Semester 2'
    ];
    const targetIndex = semesterOrder.indexOf(targetSemester);
    if (targetIndex === -1) return [];

    const unitsTaken = [];
    for (let i = 0; i < targetIndex; i++) {
        const semester = semesterOrder[i];
        $(`#${CSS.escape(semester)} .unit-card`).each(function() {
            const unitCode = $(this).data('unit-code');
            if (unitCode) {
                unitsTaken.push(unitCode);
            }
        });
    }
    return unitsTaken;
}

function parseAndCheckPrerequisites(prerequisiteText, unitsTakenBefore) {
    const prereq = prerequisiteText.toLowerCase();

    if (prereq.includes('points') || prereq.includes('credit')) {
        const totalPoints = unitsTakenBefore.length * 6;
        const pointMatches = prereq.match(/(\d+)\s*points?/);
        if (pointMatches) {
            const requiredPoints = parseInt(pointMatches[1]);
            if (totalPoints < requiredPoints) {
                return { isValid: false, message: `Insufficient points: ${totalPoints}/${requiredPoints}` };
            }
        }
    }

    const unitCodePattern = /[A-Z]{4}[0-9]{4}/g;
    const requiredUnits = prerequisiteText.match(unitCodePattern) || [];

    if (requiredUnits.length === 0) {
        return { isValid: true, message: 'Prerequisites satisfied' };
    }

    const hasAnyRequiredUnit = requiredUnits.some(unit => unitsTakenBefore.includes(unit));

    if (hasAnyRequiredUnit) {
        return { isValid: true, message: 'Prerequisites satisfied' };
    }

    return {
        isValid: false,
        message: `Need one of: ${requiredUnits.join(' OR ')}`
    };
}

function validateAndHighlightAllUnits() {
    $('.unit-card').removeClass('constraint-error constraint-warning constraint-valid').removeAttr('data-constraint-message');
    $('.semester-units').each(function() {
        const semester = $(this).data('semester');
        $(this).find('.unit-card').each(function() {
            const unitCode = $(this).data('unit-code');
            const constraintValidation = validateUnitConstraints(unitCode, semester);

            if (!constraintValidation.isValid) {
                if (constraintValidation.type === 'error') {
                    $(this).addClass('constraint-error');
                } else if (constraintValidation.type === 'warning') {
                    $(this).addClass('constraint-warning');
                }
                $(this).attr('data-constraint-message', constraintValidation.message);
            }
        });
    });
}

function checkDependentUnitsAfterRemoval(removedUnitCode) {
    $('.semester-units').each(function() {
        const semester = $(this).data('semester');
        $(this).find('.unit-card').each(function() {
            const unitCode = $(this).data('unit-code');
            const unitData = allUnitsData.find(unit => unit.code === unitCode);
            if (!unitData || !unitData.prerequisites) return;

            if (unitData.prerequisites.includes(removedUnitCode)) {
                const constraintValidation = validateUnitConstraints(unitCode, semester);
                $(this).removeClass('constraint-error constraint-warning constraint-valid').removeAttr('data-constraint-message');
                if (!constraintValidation.isValid) {
                    if (constraintValidation.type === 'error') {
                        $(this).addClass('constraint-error');
                    } else if (constraintValidation.type === 'warning') {
                        $(this).addClass('constraint-warning');
                    }
                    $(this).attr('data-constraint-message', constraintValidation.message);
                    updateValidationStatus(constraintValidation.message, constraintValidation.type);
                }
            }
        });
    });
}

function getCurrentPlan() {
    const plan = {};
    $('.semester-units').each(function() {
        const semester = $(this).data('semester');
        const units = [];
        $(this).find('.unit-card').each(function() {
            units.push($(this).data('unit-code'));
        });
        plan[semester] = units;
    });
    return plan;
}

function loadAvailableUnits() {
    $.get('/api/units')
        .done(function(data) {
            availableUnits = data.units;
            data.units.forEach(unit => {
                const existingIndex = allUnitsData.findIndex(existing => existing.code === unit.code);
                if (existingIndex >= 0) {
                    allUnitsData[existingIndex] = unit;
                } else {
                    allUnitsData.push(unit);
                }
            });
            displayAvailableUnits(data.units);
        })
        .fail(function() {
            showError('Failed to load available units');
        });
}

function displayAvailableUnits(units) {
    const container = $('#available-units');
    container.empty();
    units.forEach(unit => {
        const unitCard = createUnitCard(unit.code, unit);
        container.append(unitCard);
    });
}

function displayCategorizedUnits(majorElectives, generalElectives) {
    const container = $('#available-units');
    container.empty();
    if (majorElectives.length > 0) {
        container.append('<div class="unit-section-header"><h6>Major Electives:</h6></div>');
        majorElectives.forEach(unit => {
            const unitCard = createUnitCard(unit.code, unit);
            container.append(unitCard);
        });
    }
    if (generalElectives.length > 0) {
        container.append('<div class="unit-section-header mt-3"><h6>General Electives:</h6></div>');
        generalElectives.forEach(unit => {
            const unitCard = createUnitCard(unit.code, unit);
            container.append(unitCard);
        });
    }
    availableUnits = [...majorElectives, ...generalElectives];
    [...majorElectives, ...generalElectives].forEach(unit => {
        const existingIndex = allUnitsData.findIndex(existing => existing.code === unit.code);
        if (existingIndex >= 0) {
            allUnitsData[existingIndex] = unit;
        } else {
            allUnitsData.push(unit);
        }
    });
}

function updateAvailableUnitsFilter() {
    const unitsInPlan = new Set();
    $('.semester-units .unit-card').each(function() {
        unitsInPlan.add($(this).data('unit-code'));
    });
    $('#available-units .unit-card').each(function() {
        if (unitsInPlan.has($(this).data('unit-code'))) {
            $(this).hide();
        } else {
            $(this).show();
        }
    });
    updateSectionHeaders();
}

function updateSectionHeaders() {
    $('.unit-section-header').each(function() {
        const $header = $(this);
        let hasVisibleUnits = false;
        $header.nextUntil('.unit-section-header, :last').each(function() {
            if ($(this).hasClass('unit-card') && $(this).is(':visible')) {
                hasVisibleUnits = true;
                return false;
            }
        });
        $header.toggle(hasVisibleUnits);
    });
}

function filterUnits(searchTerm) {
    const term = searchTerm.toLowerCase();
    const unitsInPlan = new Set();
    $('.semester-units .unit-card').each(function() {
        unitsInPlan.add($(this).data('unit-code'));
    });
    $('#available-units .unit-card').each(function() {
        const unitCode = $(this).find('.unit-code').text().toLowerCase();
        const unitTitle = $(this).find('.unit-title').text().toLowerCase();
        const actualUnitCode = $(this).data('unit-code');
        const matchesSearch = unitCode.includes(term) || unitTitle.includes(term);
        const notInPlan = !unitsInPlan.has(actualUnitCode);
        $(this).toggle(matchesSearch && notInPlan);
    });
    updateSectionHeaders();
}

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
    if (!Object.values(plan).some(semester => semester.length > 0)) {
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

function aiValidatePlan() {
    const plan = getCurrentPlan();
    const majorId = $('#major-select').val();
    const indicator = $('#ai-status-indicator');
    
    // Reset the indicator and status before the request
    indicator.hide().removeClass('bg-success bg-warning bg-danger').text('');

    if (!Object.values(plan).some(semester => semester.length > 0)) {
        showError('No units in plan to validate');
        indicator.show().addClass('bg-danger').text('Fail');
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
        indicator.show().addClass('bg-danger').text('Fail');
    });
}

function updateAIStatusIndicator(result) {
    const indicator = $('#ai-status-indicator');
    const overallQuality = result.overallQuality || 'unknown';

    indicator.show();
    
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
            indicator.removeClass('bg-success bg-warning bg-danger').text('N/A');
            break;
    }
}

function showQualityCheckModal(result) {
    const qualityScore = result.qualityScore || 'N/A';
    const overallQuality = result.overallQuality || 'unknown';
    const recommendations = result.recommendations || [];
    const warnings = result.warnings || [];
    const strengths = result.strengths || [];
    const metadata = result.metadata || {};

    let qualityClass = 'text-secondary';
    let qualityIcon = 'fas fa-question-circle';
    let qualityAdvice = 'Quality analysis unavailable - manual validation recommended';

    if (overallQuality === 'excellent') {
        qualityClass = 'text-success';
        qualityIcon = 'fas fa-star';
        qualityAdvice = 'Plan quality is excellent - ready for PDF export!';
    } else if (overallQuality === 'good') {
        qualityClass = 'text-info';
        qualityIcon = 'fas fa-thumbs-up';
        qualityAdvice = 'Plan quality is good - suitable for PDF export';
    } else if (overallQuality === 'fair') {
        qualityClass = 'text-warning';
        qualityIcon = 'fas fa-exclamation-triangle';
        qualityAdvice = 'Plan quality is fair - consider reviewing before PDF export';
    } else if (overallQuality === 'poor') {
        qualityClass = 'text-danger';
        qualityIcon = 'fas fa-times-circle';
        qualityAdvice = 'Plan quality is poor - manual validation recommended before PDF export';
    }

    const modalHtml = `
        <div class="modal-dialog modal-dialog-centered modal-lg">
            <div class="modal-content">
                <div class="modal-header">
                    <h5 class="modal-title">AI Plan Quality Analysis</h5>
                    <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
                </div>
                <div class="modal-body">
                    <div class="text-center mb-4">
                        <i class="${qualityIcon} fa-3x ${qualityClass}"></i>
                        <h4 class="mt-2 ${qualityClass}">${overallQuality.toUpperCase()}</h4>
                        <p class="lead">${qualityAdvice}</p>
                        <hr>
                        <h5>Quality Score: <span class="badge bg-secondary">${qualityScore}</span></h5>
                    </div>

                    ${strengths.length > 0 ? `
                    <h6><i class="fas fa-check-circle text-success me-2"></i>Strengths</h6>
                    <ul class="list-group mb-3">
                        ${strengths.map(s => `<li class="list-group-item list-group-item-success">${s}</li>`).join('')}
                    </ul>
                    ` : ''}

                    ${warnings.length > 0 ? `
                    <h6><i class="fas fa-exclamation-triangle text-warning me-2"></i>Warnings</h6>
                    <ul class="list-group mb-3">
                        ${warnings.map(w => `<li class="list-group-item list-group-item-warning">${w}</li>`).join('')}
                    </ul>
                    ` : ''}

                    ${recommendations.length > 0 ? `
                    <h6><i class="fas fa-lightbulb text-info me-2"></i>Recommendations</h6>
                    <ul class="list-group mb-3">
                        ${recommendations.map(r => `<li class="list-group-item list-group-item-info">${r}</li>`).join('')}
                    </ul>
                    ` : ''}

                    ${Object.keys(metadata).length > 0 ? `
                    <div class="card bg-light mt-4">
                        <div class="card-header">
                            <h6 class="mb-0">Analysis Details</h6>
                        </div>
                        <div class="card-body">
                            <pre class="mb-0 small">${JSON.stringify(metadata, null, 2)}</pre>
                        </div>
                    </div>
                    ` : ''}
                </div>
            </div>
        </div>
    `;

    const modalElement = $('#qualityCheckModal');
    if (modalElement.length === 0) {
        $('body').append('<div class="modal fade" id="qualityCheckModal" tabindex="-1"></div>');
    }
    $('#qualityCheckModal').html(modalHtml).modal('show');
}

function showLoading(message) {
    $('#loading-message').text(message);
    $('#loading-modal').modal('show');
}

function hideLoading() {
    $('#loading-modal').modal('hide');
}

function showError(message) {
    console.error('Error:', message);
    const statusDiv = $('#validation-status');
    statusDiv.html(`<div class="alert alert-danger">${message}</div>`);
}
