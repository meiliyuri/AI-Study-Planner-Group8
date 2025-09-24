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

function handleUnitMove(evt) {
    updateDropZone(evt.to);
    const movedUnitCode = $(evt.item).data('unit-code');
    validatePlan();
    checkDependentUnitsAfterMove(movedUnitCode);
}

function updateDropZone(container) {
    if (container.querySelectorAll('.unit-card').length === 0) {
        container.classList.add('empty');
    } else {
        container.classList.remove('empty');
    }
}

function loadMajors() {
    $.get('/api/majors', function(data) {
        const select = $('#major-select');
        select.empty().append('<option value="">Select Major</option>');
        data.majors.forEach(major => {
            select.append(`<option value="${major.id}">${major.name}</option>`);
        });
    }).fail(function(xhr, status, error) {
        showError('Failed to load majors: ' + error);
    });
}

function generateStudyPlan() {
    const majorId = $('#major-select').val();
    if (!majorId) {
        showError('Please select a major');
        return;
    }

    $.ajax({
        url: '/api/generate_plan',
        method: 'POST',
        contentType: 'application/json',
        data: JSON.stringify({ major: majorId }),
        success: function(data) {
            currentPlan = data.plan;
            availableUnits = data.available_units;
            allUnitsData = data.all_units;
            renderStudyPlan(data);
            renderAvailableUnits(data.available_units);
            updateValidationStatus('Plan generated successfully', 'success');
        },
        error: function(xhr, status, error) {
            showError('Failed to generate plan: ' + error);
        }
    });
}

function renderStudyPlan(data) {
    Object.entries(data.plan).forEach(([semester, units]) => {
        const container = $(`#${semester}`);
        container.empty();
        units.forEach(unit => {
            container.append(createUnitCard(unit));
        });
        updateDropZone(container[0]);
    });
}

function renderAvailableUnits(units) {
    const container = $('#available-units');
    container.empty();
    units.forEach(unit => {
        container.append(createUnitCard(unit));
    });
}

function createUnitCard(unit) {
    return `
        <div class="unit-card" data-unit-code="${unit.code}">
            <div class="unit-header">${unit.code}</div>
            <div class="unit-title">${unit.title}</div>
        </div>
    `;
}

function filterUnits(query) {
    query = query.toLowerCase();
    $('#available-units .unit-card').each(function() {
        const text = $(this).text().toLowerCase();
        $(this).toggle(text.includes(query));
    });
}

function updateAvailableUnitsFilter() {
    const query = $('#unit-search').val();
    filterUnits(query);
}

function validatePlan() {
    const planData = extractPlanData();

    $.ajax({
        url: '/api/validate_plan',
        method: 'POST',
        contentType: 'application/json',
        data: JSON.stringify({ plan: planData }),
        success: function(data) {
            validateAndHighlightAllUnits(planData, data);
            if (data.isValid) {
                updateValidationStatus('Plan is valid', 'success');
            } else {
                updateValidationStatus(data.errors.join(', '), 'error');
            }
        },
        error: function(xhr, status, error) {
            showError('Validation failed: ' + error);
        }
    });
}

function validateAndHighlightAllUnits(planData, backendValidation) {
    let allValid = true;

    Object.entries(planData).forEach(([semester, units]) => {
        const container = $(`#${semester}`);
        units.forEach(unitCode => {
            const unitCard = container.find(`.unit-card[data-unit-code="${unitCode}"]`);
            unitCard.removeClass('invalid warning');

            const validation = validateUnitConstraints(unitCode, semester);
            if (!validation.isValid) {
                allValid = false;
                unitCard.addClass(validation.type || 'invalid');
            }
        });
    });

    if (backendValidation && backendValidation.errors.length > 0) {
        backendValidation.errors.forEach(error => {
            if (error.unit) {
                $(`.unit-card[data-unit-code="${error.unit}"]`).addClass('invalid');
            }
        });
    }

    return allValid;
}

function validateUnitConstraints(unitCode, targetSemester) {
    const unitData = allUnitsData.find(unit => unit.code === unitCode);
    if (!unitData) return { isValid: true };

    const semesterIndex = getSemesterIndex(targetSemester);
    const unitsBefore = getUnitsBeforeSemester(semesterIndex);

    if (unitData.level === 1) {
        return { isValid: true };
    }

    const prereqResult = parseAndCheckPrerequisites(unitData.prerequisites, unitsBefore);
    if (!prereqResult.isValid) {
        return {
            isValid: false,
            message: `${unitData.code}: ${prereqResult.message}`,
            type: 'warning'
        };
    }

    if (!checkAvailability(unitData, targetSemester)) {
        return {
            isValid: false,
            message: `${unitData.code} not available in ${targetSemester}`,
            type: 'invalid'
        };
    }

    if (checkSemesterCapacity(targetSemester)) {
        return {
            isValid: false,
            message: `${targetSemester} exceeds unit limit`,
            type: 'invalid'
        };
    }

    return { isValid: true };
}

function parseAndCheckPrerequisites(prerequisiteText, unitsTakenBefore) {
    if (!prerequisiteText || prerequisiteText.toLowerCase().includes('nil')) {
        return { isValid: true, message: 'No prerequisites' };
    }

    const prereq = prerequisiteText.toLowerCase();

    if (prereq.includes('points') || prereq.includes('credit')) {
        const totalPoints = unitsTakenBefore.length * 6;
        const pointMatches = prereq.match(/(\d+)\s*points?/);
        if (pointMatches) {
            const requiredPoints = parseInt(pointMatches[1]);
            if (totalPoints < requiredPoints) {
                return {
                    isValid: false,
                    message: `Insufficient points: ${totalPoints}/${requiredPoints}`
                };
            }
        }
    }

    const tokens = prerequisiteText
        .replace(/\(/g, ' ( ')
        .replace(/\)/g, ' ) ')
        .split(/\s+/)
        .map(t => t.trim())
        .filter(t => t.length > 0);

    function evalTokens(tokens) {
        const stack = [];

        while (tokens.length > 0) {
            const token = tokens.shift();

            if (token === '(') {
                stack.push(evalTokens(tokens));
            } else if (token === ')') {
                break;
            } else if (token.toLowerCase() === 'and') {
                stack.push('AND');
            } else if (token.toLowerCase() === 'or') {
                stack.push('OR');
            } else if (/^[A-Z]{4}[0-9]{4}$/.test(token)) {
                stack.push(unitsTakenBefore.includes(token));
            }
        }

        let result = null;
        let lastOp = null;
        stack.forEach(item => {
            if (item === 'AND' || item === 'OR') {
                lastOp = item;
            } else {
                if (result === null) {
                    result = item;
                } else if (lastOp === 'AND') {
                    result = result && item;
                } else if (lastOp === 'OR') {
                    result = result || item;
                }
            }
        });

        return result === null ? true : result;
    }

    const isValid = evalTokens(tokens);

    if (isValid) {
        return { isValid: true, message: 'Prerequisites satisfied' };
    } else {
        const requiredUnits = prerequisiteText.match(/[A-Z]{4}[0-9]{4}/g) || [];
        return {
            isValid: false,
            message: `Prerequisite not satisfied: ${requiredUnits.join(' AND/OR ')}`
        };
    }
}

function checkAvailability(unitData, semester) {
    return unitData.availabilities && unitData.availabilities.includes(semester);
}

function checkSemesterCapacity(semester) {
    return $(`#${semester} .unit-card`).length > 4;
}

function extractPlanData() {
    const planData = {};
    $('.semester-units').each(function() {
        const semesterId = $(this).attr('id');
        const units = [];
        $(this).find('.unit-card').each(function() {
            units.push($(this).data('unit-code'));
        });
        planData[semesterId] = units;
    });
    return planData;
}

function getSemesterIndex(semester) {
    const order = [
        'Year 1, Semester 1', 'Year 1, Semester 2',
        'Year 2, Semester 1', 'Year 2, Semester 2',
        'Year 3, Semester 1', 'Year 3, Semester 2'
    ];
    return order.indexOf(semester);
}

function getUnitsBeforeSemester(index) {
    const units = [];
    $('.semester-units').each(function() {
        const semId = $(this).attr('id');
        const semIndex = getSemesterIndex(semId);
        if (semIndex < index) {
            $(this).find('.unit-card').each(function() {
                units.push($(this).data('unit-code'));
            });
        }
    });
    return units;
}

function updateValidationStatus(message, status) {
    const statusEl = $('#validation-status');
    statusEl.removeClass().addClass(`alert alert-${status}`).text(message).show();
}

function showError(message) {
    updateValidationStatus(message, 'danger');
}

function checkDependentUnitsAfterRemoval(removedUnitCode) {
    $('.unit-card').each(function() {
        const unitCode = $(this).data('unit-code');
        const unitData = allUnitsData.find(u => u.code === unitCode);
        if (unitData && unitData.prerequisites.includes(removedUnitCode)) {
            $(this).addClass('warning');
        }
    });
}

function checkDependentUnitsAfterMove(movedUnitCode) {
    $('.unit-card').each(function() {
        const unitCode = $(this).data('unit-code');
        const unitData = allUnitsData.find(u => u.code === unitCode);
        if (unitData && unitData.prerequisites.includes(movedUnitCode)) {
            $(this).addClass('warning');
        }
    });
}

function exportToPDF() {
    const planData = extractPlanData();

    $.ajax({
        url: '/api/export_pdf',
        method: 'POST',
        contentType: 'application/json',
        data: JSON.stringify({ plan: planData }),
        xhrFields: { responseType: 'blob' },
        success: function(blob) {
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = 'study_plan.pdf';
            document.body.appendChild(a);
            a.click();
            window.URL.revokeObjectURL(url);
        },
        error: function(xhr, status, error) {
            showError('PDF export failed: ' + error);
        }
    });
}

function aiValidatePlan() {
    const planData = extractPlanData();

    $.ajax({
        url: '/api/ai_validate_plan',
        method: 'POST',
        contentType: 'application/json',
        data: JSON.stringify({ plan: planData }),
        success: function(data) {
            showQualityCheckModal(data);
        },
        error: function(xhr, status, error) {
            showError('AI validation failed: ' + error);
        }
    });
}

function showQualityCheckModal(data) {
    let qualityClass = 'text-secondary';
    let qualityAdvice = '';

    if (data.overall_quality === 'excellent') {
        qualityClass = 'text-success';
        qualityAdvice = 'Plan quality is excellent - ready for PDF export!';
    } else if (data.overall_quality === 'good') {
        qualityClass = 'text-primary';
        qualityAdvice = 'Plan quality is good - consider minor improvements.';
    } else if (data.overall_quality === 'poor') {
        qualityClass = 'text-danger';
        qualityAdvice = 'Plan quality is poor - please revise.';
    } else {
        qualityAdvice = 'Plan quality could not be determined.';
    }

    $('#quality-check-modal .modal-body').html(`
        <p class="${qualityClass}">${qualityAdvice}</p>
        <h6>Detailed Analysis:</h6>
        <ul>
            ${data.analysis.map(item => `<li>${item}</li>`).join('')}
        </ul>
    `);

    $('#quality-check-modal').modal('show');
}
// AI Study Planner Frontend JavaScript

$(document).ready(function() {
    // Initialize the application
    initializeApp();
});

let currentPlan = {};
let availableUnits = [];
let allUnitsData = []; // Store all unit data including those in the plan
let sortableInstances = [];

function initializeApp() {
    loadMajors();
    setupEventHandlers();
    setupDragAndDrop();
}

function setupEventHandlers() {
    // Major selection
    $('#major-select').on('change', function() {
        const majorId = $(this).val();
        $('#generate-plan').prop('disabled', !majorId);
    });

    // Generate plan button
    $('#generate-plan').on('click', function() {
        generateStudyPlan();
    });

    // Export PDF button
    $('#export-pdf').on('click', function() {
        exportToPDF();
    });

    // AI Validate Plan button
    $('#ai-validate-plan').on('click', function() {
        aiValidatePlan();
    });

    // Unit search
    $('#unit-search').on('input', function() {
        filterUnits($(this).val());
    });
}

function setupDragAndDrop() {
    // Initialize sortable for each semester
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
                    // Check if any remaining units depend on the removed unit
                    checkDependentUnitsAfterRemoval(removedUnitCode);
                }
            });
            sortableInstances.push(sortable);
        }
    });

    // Initialize sortable for available units
    const availableUnitsElement = document.getElementById('available-units');
    if (availableUnitsElement) {
        Sortable.create(availableUnitsElement, {
            group: {
                name: 'units',
                pull: 'clone',
                put: true // Allow units to be dragged back here
            },
            sort: false,
            animation: 150,
            onAdd: function(evt) {
                // When unit is dragged back to available units, remove it from plan
                const removedUnitCode = $(evt.item).data('unit-code');
                evt.item.remove();
                updateAvailableUnitsFilter();
                checkDependentUnitsAfterRemoval(removedUnitCode);
                validatePlan();
            }
        });
    }

    // Initialize trash zone
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
                // Remove the unit completely when dropped in trash
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

            // Clear and populate allUnitsData with enriched plan data
            allUnitsData = [];
            if (data.enriched_plan) {
                Object.keys(data.enriched_plan).forEach(semester => {
                    data.enriched_plan[semester].forEach(unitData => {
                        allUnitsData.push(unitData);
                    });
                });
            }

            // Use enriched plan if available, otherwise fall back to regular plan
            const planToDisplay = data.enriched_plan || data.plan;
            displayStudyPlan(planToDisplay, !!data.enriched_plan);

            // Display categorized available units
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

    // Clear existing units
    $('.semester-units').each(function() {
        $(this).empty().append('<div class="drop-zone">Drop units here (4 max)</div>');
    });

    // Populate semesters with units
    Object.keys(plan).forEach(semester => {
        const semesterElement = $(`#${CSS.escape(semester)}`);
        if (semesterElement.length) {
            let semesterUnits = plan[semester];

            // Sort units by level then alphabetically if enriched
            if (isEnriched) {
                semesterUnits = [...semesterUnits].sort((a, b) => {
                    // First sort by level
                    if (a.level !== b.level) {
                        return a.level - b.level;
                    }
                    // Then sort alphabetically by code
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
    // Update available units filter to hide units already in plan
    updateAvailableUnitsFilter();
    // Apply visual validation to all units in the plan
    validateAndHighlightAllUnits();
}

function addUnitToSemester(semesterElement, unitCode, unitData = null) {
    const unitCard = createUnitCard(unitCode, unitData);
    semesterElement.append(unitCard);
}

function createUnitCard(unitCode, unitData = null) {
    // If unitData is not provided, try to find it in allUnitsData
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

    // Always update the UI, but validate afterwards
    updateDropZone(evt.to);
    updateAvailableUnitsFilter();

    // Check for validation issues and update status
    if (unitCount > 4) {
        updateValidationStatus(`${semester} has ${unitCount} units (max 4 allowed)`, 'error');
    } else {
        // Check prerequisite and semester availability constraints
        const constraintValidation = validateUnitConstraints(unitCode, semester);
        if (!constraintValidation.isValid) {
            updateValidationStatus(constraintValidation.message, constraintValidation.type);
        } else {
            // Check other validation rules
            validatePlan();
        }
    }

    // Apply visual validation to all units in the plan
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

    // Update semester capacity indicator
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
    // First do local validation for immediate feedback
    const localValidation = validatePlanLocally();

    if (!localValidation.isValid) {
        updateValidationStatus(localValidation.reason, localValidation.type);
        return;
    }

    // If local validation passes, check with backend
    const plan = getCurrentPlan();

    $.ajax({
        url: '/api/validate_plan',
        method: 'POST',
        contentType: 'application/json',
        data: JSON.stringify({ plan: plan }),
        success: function(data) {
            // Use the type from backend if provided, otherwise default logic
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

    // Check semester capacity (max 4 units per semester)
    $('.semester-units').each(function() {
        const semesterName = $(this).attr('id');
        const unitCount = $(this).find('.unit-card').length;

        if (unitCount > 4) {
            issues.push(`${semesterName} has ${unitCount} units (max 4 allowed)`);
        } else if (unitCount > 0 && unitCount < 4) {
            warnings.push(`${semesterName} has only ${unitCount} units`);
        }
    });

    // Count total units
    const totalUnits = $('.semester-units .unit-card').length;
    if (totalUnits > 24) {
        issues.push(`Total ${totalUnits} units exceeds maximum of 24`);
    } else if (totalUnits < 24) {
        warnings.push(`Plan has ${totalUnits} units (target: 24)`);
    }

    // Return results
    if (issues.length > 0) {
        return {
            isValid: false,
            reason: issues[0], // Show first critical issue
            type: 'error'
        };
    } else if (warnings.length > 0) {
        return {
            isValid: true, // Valid but with warnings
            reason: warnings[0] + ' - plan incomplete',
            type: 'warning'
        };
    } else {
        return {
            isValid: true,
            reason: 'Plan structure looks good',
            type: 'success'
        };
    }
}

function validateUnitConstraints(unitCode, targetSemester) {
    // Find unit data in all units (both in plan and available)
    const unitData = allUnitsData.find(unit => unit.code === unitCode);
    if (!unitData) {
        return { isValid: false, message: `Unit data not found for ${unitCode}`, type: 'error' };
    }

    // Check semester availability
    const semesterCheck = checkSemesterAvailability(unitData, targetSemester);
    if (!semesterCheck.isValid) {
        return semesterCheck;
    }

    // Check prerequisites
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

    // Parse availability string to check if unit is offered in target semester
    if (availabilities.includes('semester 1') && !availabilities.includes('semester 2')) {
        // Only offered in Semester 1
        if (semesterNum !== 1) {
            return {
                isValid: false,
                message: `${unitData.code} is only available in Semester 1`,
                type: 'error'
            };
        }
    } else if (availabilities.includes('semester 2') && !availabilities.includes('semester 1')) {
        // Only offered in Semester 2
        if (semesterNum !== 2) {
            return {
                isValid: false,
                message: `${unitData.code} is only available in Semester 2`,
                type: 'error'
            };
        }
    }

    return { isValid: true, message: 'Semester availability satisfied', type: 'success' };
}

function checkPrerequisites(unitData, targetSemester) {
    if (!unitData.prerequisites || unitData.prerequisites.toLowerCase().includes('nil')) {
        return { isValid: true, message: 'No prerequisites', type: 'success' };
    }

    // LEVEL 1 UNITS: Assume students come in with appropriate ATAR qualifications
    // Skip prerequisite validation for first year units entirely
    if (unitData.level === 1) {
        return { isValid: true, message: 'Level 1 unit - ATAR requirements assumed', type: 'success' };
    }

    // Get all units taken before this semester
    const unitsTakenBefore = getUnitsTakenBefore(targetSemester);

    // Parse and check prerequisites
    const prereqResult = parseAndCheckPrerequisites(unitData.prerequisites, unitsTakenBefore);

    if (!prereqResult.isValid) {
        return {
            isValid: false,
            message: `${unitData.code}: ${prereqResult.message}`,
            type: 'warning' // Prerequisites are warnings, not hard errors
        };
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

    // Get units from all previous semesters
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
    if (!prerequisiteText || prerequisiteText.toLowerCase().includes('nil')) {
        return { isValid: true, message: 'No prerequisites' };
    }

    const prereq = prerequisiteText.toLowerCase();

    // Check for point requirements first
    if (prereq.includes('points') || prereq.includes('credit')) {
        const totalPoints = unitsTakenBefore.length * 6; // Assume 6 points per unit

        const pointMatches = prereq.match(/(\d+)\s*points?/);
        if (pointMatches) {
            const requiredPoints = parseInt(pointMatches[1]);
            if (totalPoints < requiredPoints) {
                return {
                    isValid: false,
                    message: `Insufficient points: ${totalPoints}/${requiredPoints}`
                };
            }
        }
    }

    // Extract all unit codes from the prerequisite text
    const unitCodePattern = /[A-Z]{4}[0-9]{4}/g;
    const requiredUnits = prerequisiteText.match(unitCodePattern) || [];

    if (requiredUnits.length === 0) {
        // No specific unit codes found, assume satisfied if we got here
        return { isValid: true, message: 'Prerequisites satisfied' };
    }

    // Simple approach: if ANY required unit is taken, prerequisites are satisfied
    // This handles most OR logic cases correctly
    const hasAnyRequiredUnit = requiredUnits.some(unit => unitsTakenBefore.includes(unit));

    if (hasAnyRequiredUnit) {
        return { isValid: true, message: 'Prerequisites satisfied' };
    }

    // None of the required units are taken
    return {
        isValid: false,
        message: `Need one of: ${requiredUnits.join(' OR ')}`
    };
}

function validateAndHighlightAllUnits() {
    // Clear all existing constraint classes
    $('.unit-card').removeClass('constraint-error constraint-warning constraint-valid')
        .removeAttr('data-constraint-message');

    // Validate each unit in each semester
    $('.semester-units').each(function() {
        const semester = $(this).data('semester');

        $(this).find('.unit-card').each(function() {
            const unitCode = $(this).data('unit-code');
            const constraintValidation = validateUnitConstraints(unitCode, semester);

            // Apply visual styling based on validation result
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
    // Go through all units currently on the board
    $('.semester-units').each(function() {
        const semester = $(this).data('semester');

        $(this).find('.unit-card').each(function() {
            const unitCode = $(this).data('unit-code');
            const unitData = allUnitsData.find(unit => unit.code === unitCode);

            if (!unitData || !unitData.prerequisites) {
                return; // Skip if no unit data or no prerequisites
            }

            // Check if this unit's prerequisites mention the removed unit
            if (unitData.prerequisites.includes(removedUnitCode)) {
                // Re-validate this unit's constraints
                const constraintValidation = validateUnitConstraints(unitCode, semester);

                // Clear previous styling
                $(this).removeClass('constraint-error constraint-warning constraint-valid')
                    .removeAttr('data-constraint-message');

                // Apply new styling based on validation result
                if (!constraintValidation.isValid) {
                    if (constraintValidation.type === 'error') {
                        $(this).addClass('constraint-error');
                    } else if (constraintValidation.type === 'warning') {
                        $(this).addClass('constraint-warning');
                    }
                    $(this).attr('data-constraint-message', constraintValidation.message);

                    // Update validation status to show the issue
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

            // Add available units to allUnitsData for validation
            data.units.forEach(unit => {
                const existingIndex = allUnitsData.findIndex(existing => existing.code === unit.code);
                if (existingIndex >= 0) {
                    // Update existing record with complete data from API
                    allUnitsData[existingIndex] = unit;
                } else {
                    // Add new unit
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

    // Add Major Electives section
    if (majorElectives.length > 0) {
        container.append('<div class="unit-section-header"><h6>Major Electives:</h6></div>');
        majorElectives.forEach(unit => {
            const unitCard = createUnitCard(unit.code, unit);
            container.append(unitCard);
        });
    }

    // Add General Electives section
    if (generalElectives.length > 0) {
        container.append('<div class="unit-section-header mt-3"><h6>General Electives:</h6></div>');
        generalElectives.forEach(unit => {
            const unitCard = createUnitCard(unit.code, unit);
            container.append(unitCard);
        });
    }

    // Store for filtering
    availableUnits = [...majorElectives, ...generalElectives];

    // Add available units to allUnitsData as well
    [...majorElectives, ...generalElectives].forEach(unit => {
        const existingIndex = allUnitsData.findIndex(existing => existing.code === unit.code);
        if (existingIndex >= 0) {
            // Update existing record with complete data
            allUnitsData[existingIndex] = unit;
        } else {
            // Add new unit
            allUnitsData.push(unit);
        }
    });
}

function updateAvailableUnitsFilter() {
    // Get all units currently in the plan
    const unitsInPlan = new Set();
    $('.semester-units .unit-card').each(function() {
        const unitCode = $(this).data('unit-code');
        unitsInPlan.add(unitCode);
    });

    // Hide/show units in available units list
    $('#available-units .unit-card').each(function() {
        const unitCode = $(this).data('unit-code');
        if (unitsInPlan.has(unitCode)) {
            $(this).hide();
        } else {
            $(this).show();
        }
    });

    // Hide section headers if all units in that section are hidden
    updateSectionHeaders();
}

function updateSectionHeaders() {
    $('.unit-section-header').each(function() {
        const $header = $(this);
        let hasVisibleUnits = false;

        // Check if any unit cards after this header are visible
        $header.nextUntil('.unit-section-header, :last').each(function() {
            if ($(this).hasClass('unit-card') && $(this).is(':visible')) {
                hasVisibleUnits = true;
                return false; // break
            }
        });

        if (hasVisibleUnits) {
            $header.show();
        } else {
            $header.hide();
        }
    });
}

function filterUnits(searchTerm) {
    const term = searchTerm.toLowerCase();

    // Get units currently in plan to maintain that filter
    const unitsInPlan = new Set();
    $('.semester-units .unit-card').each(function() {
        const unitCode = $(this).data('unit-code');
        unitsInPlan.add(unitCode);
    });

    $('#available-units .unit-card').each(function() {
        const unitCode = $(this).find('.unit-code').text().toLowerCase();
        const unitTitle = $(this).find('.unit-title').text().toLowerCase();
        const actualUnitCode = $(this).data('unit-code');

        // Show if matches search AND not in plan
        const matchesSearch = unitCode.includes(term) || unitTitle.includes(term);
        const notInPlan = !unitsInPlan.has(actualUnitCode);

        if (matchesSearch && notInPlan) {
            $(this).show().removeClass('hidden');
        } else {
            $(this).hide().addClass('hidden');
        }
    });

    // Update section headers based on visibility
    updateSectionHeaders();
}

function updateValidationStatus(message, type) {
    const statusDiv = $('#validation-status');
    statusDiv.removeClass('validation-success validation-error validation-warning');

    switch(type) {
        case 'success':
            statusDiv.addClass('validation-success');
            break;
        case 'error':
            statusDiv.addClass('validation-error');
            break;
        case 'warning':
            statusDiv.addClass('validation-warning');
            break;
    }

    statusDiv.html(`<strong>${type.charAt(0).toUpperCase() + type.slice(1)}:</strong> ${message}`);
}

function exportToPDF() {
    const plan = getCurrentPlan();

    // Check if plan has any units
    const hasUnits = Object.values(plan).some(semester => semester.length > 0);
    if (!hasUnits) {
        showError('No units in plan to export');
        return;
    }

    showLoading('Generating PDF...');

    fetch('/api/export_pdf', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ plan: plan })
    })
    .then(response => {
        if (!response.ok) {
            return response.json().then(err => Promise.reject(err));
        }
        return response.blob();
    })
    .then(blob => {
        // Create download link
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
    
    // 重置指示灯状态
    indicator.hide().removeClass('bg-success bg-warning bg-danger').text('');

    const hasUnits = Object.values(plan).some(semester => semester.length > 0);
    if (!hasUnits) {
        showError('No units in plan to validate');
        indicator.show().addClass('bg-danger').text('Fail');
        return;
    }

    if (!majorId) {
        showError('Please select a major first');
        indicator.show().addClass('bg-danger').text('Fail');
        return;
    }

    showLoading('Running AI quality analysis...');

    fetch('/api/ai_validate_plan', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            plan: plan,
            major_code: majorId
        })
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

function showLoading(message) {
    $('#loading-message').text(message);
    $('#loading-modal').modal('show');
}

function hideLoading() {
    $('#loading-modal').modal('hide');
}

function showQualityCheckModal(result) {
    const qualityScore = result.qualityScore || 0;
    const overallQuality = result.overallQuality || 'unknown';
    const recommendations = result.recommendations || [];
    const warnings = result.warnings || [];
    const strengths = result.strengths || [];
    const metadata = result.metadata || {};

    // Determine quality color and icon
    let qualityClass = 'text-secondary';
    let qualityIcon = 'fas fa-question-circle';
    let qualityAdvice = '';

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
    } else {
        qualityAdvice = 'Quality analysis unavailable - manual validation recommended';
    }

    // Modal HTML remains the same as your original code
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
        // Create modal if it doesn't exist
        $('body').append('<div class="modal fade" id="qualityCheckModal" tabindex="-1"></div>');
    }
    $('#qualityCheckModal').html(modalHtml).modal('show');
}

function showError(message) {
    console.error('Error:', message);
    const statusDiv = $('#validation-status');
    statusDiv.html(`<div class="alert alert-danger">${message}</div>`);
}

/**
 * * * New functions for AI status indicator
 * * */

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