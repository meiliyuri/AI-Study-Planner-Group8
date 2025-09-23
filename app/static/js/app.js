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
