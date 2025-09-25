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
                put: true  // Allow units to be dragged back here
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
            logDebug('Plan generated', data);
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
    const semester = evt.to.dataset.semester; // Get the semester the item is being moved to
    const unitCount = $(evt.to).find('.unit-card').length; // Count the number of units in the target semester
    const unitCode = $(evt.item).data('unit-code'); // Get the unit code of the item being moved

    // Record which semester the current item belongs to
    $(evt.item).attr('data-semester', semester);

    // Update the UI
    updateDropZone(evt.to); // Update the drop zone UI
    updateAvailableUnitsFilter(); // Update the filter for available units

    // Clear previous flags (to avoid residual mis-coloring)
    $(evt.item).removeClass('constraint-error constraint-warning constraint-valid')
               .removeAttr('data-constraint-message');

    // Check semester capacity
    if (unitCount > 4) {
        updateValidationStatus(`${semester} has ${unitCount} units (max 4 allowed)`, 'error'); // Update validation status
        $(evt.item).addClass('constraint-error') // Add error class for visual feedback
                   .attr('data-constraint-message', 'Too many units in this semester'); // Set error message
        return; // Exit function if the limit is exceeded
    }

    // Validate semester availability & prerequisites
    const constraintValidation = validateUnitConstraints(unitCode, semester);

    if (!constraintValidation.isValid) {
        // Set card color based on validation result
        if (constraintValidation.type === 'error') {
            $(evt.item).addClass('constraint-error'); // Add error class if validation fails
        } else if (constraintValidation.type === 'warning') {
            $(evt.item).addClass('constraint-warning'); // Add warning class if there are warnings
        }
        $(evt.item).attr('data-constraint-message', constraintValidation.message); // Set the constraint message

        // Update the status on the right side
        updateValidationStatus(constraintValidation.message, constraintValidation.type);

    } else {
        // If valid, add a green mark to indicate compliance
        $(evt.item).addClass('constraint-valid');
        // Continue with overall validatePlan()
        validatePlan();
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
            logDebug('Validation result', data);
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
        console.log(`❌ VALIDATION BUG: Unit data not found for ${unitCode} in allUnitsData`);
        console.log('🔍 Available units in allUnitsData:', allUnitsData.map(u => u.code).slice(0, 10));
        return { isValid: false, message: `Unit data not found for ${unitCode}`, type: 'error' };
    }

    console.log(`Validating ${unitCode} for ${targetSemester}:`, unitData);

    // Check semester availability
    const semesterCheck = checkSemesterAvailability(unitData, targetSemester);
    if (!semesterCheck.isValid) {
        console.log(`Semester availability failed for ${unitCode}:`, semesterCheck);
        return semesterCheck;
    }

    // Check prerequisites
    const prereqCheck = checkPrerequisites(unitData, targetSemester);
    if (!prereqCheck.isValid) {
        console.log(`Prerequisites failed for ${unitCode}:`, prereqCheck);
        return prereqCheck;
    }

    console.log(`All constraints satisfied for ${unitCode}`);
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
    console.log(`Checking prerequisites for ${unitData.code}: "${unitData.prerequisites}"`);

    if (!unitData.prerequisites || unitData.prerequisites.toLowerCase().includes('nil')) {
        console.log(`No prerequisites for ${unitData.code}`);
        return { isValid: true, message: 'No prerequisites', type: 'success' };
    }

    // LEVEL 1 UNITS: Assume students come in with appropriate ATAR qualifications
    // Skip prerequisite validation for first year units entirely
    if (unitData.level === 1) {
        console.log(`Skipping prerequisite validation for Level 1 unit ${unitData.code} (assuming ATAR requirements met)`);
        return { isValid: true, message: 'Level 1 unit - ATAR requirements assumed', type: 'success' };
    }

    // Get all units taken before this semester
    const unitsTakenBefore = getUnitsTakenBefore(targetSemester);
    console.log(`Units taken before ${targetSemester}:`, unitsTakenBefore);

    // Parse and check prerequisites
    const prereqResult = parseAndCheckPrerequisites(unitData.prerequisites, unitsTakenBefore);
    console.log(`Prerequisite result for ${unitData.code}:`, prereqResult);

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
    console.log(`🔧 PREREQ DEBUG: Checking "${prerequisiteText}" with taken units:`, unitsTakenBefore);

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

    console.log(`   📋 Required units found: [${requiredUnits.join(', ')}]`);
    console.log(`   📚 Units taken before: [${unitsTakenBefore.join(', ')}]`);

    // Simple approach: if ANY required unit is taken, prerequisites are satisfied
    // This handles most OR logic cases correctly
    const hasAnyRequiredUnit = requiredUnits.some(unit => unitsTakenBefore.includes(unit));

    console.log(`   ✅ Has any required unit: ${hasAnyRequiredUnit}`);

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
    console.log(`Checking dependent units after removing ${removedUnitCode}`);

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
                console.log(`${unitCode} depends on removed unit ${removedUnitCode}, re-validating`);

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

    // Check if plan has any units
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

    const modalHtml = `
        <div class="modal fade" id="qualityCheckModal" tabindex="-1">
            <div class="modal-dialog modal-lg">
                <div class="modal-content">
                    <div class="modal-header">
                        <h5 class="modal-title">
                            <i class="${qualityIcon} ${qualityClass}"></i>
                            AI Study Plan Quality Check
                        </h5>
                        <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
                    </div>
                    <div class="modal-body">
                        <!-- Overall Quality Score -->
                        <div class="row mb-4">
                            <div class="col-md-6">
                                <div class="card ${qualityClass === 'text-success' ? 'border-success' : qualityClass === 'text-danger' ? 'border-danger' : 'border-warning'}">
                                    <div class="card-body text-center">
                                        <h3 class="${qualityClass}">${qualityScore}%</h3>
                                        <p class="mb-0">Quality Score</p>
                                        <small class="${qualityClass}">${overallQuality.toUpperCase()}</small>
                                    </div>
                                </div>
                            </div>
                            <div class="col-md-6">
                                <div class="alert alert-info border-0 h-100 d-flex align-items-center">
                                    <div>
                                        <i class="fas fa-info-circle me-2"></i>
                                        <strong>Recommendation:</strong><br>
                                        ${qualityAdvice}
                                    </div>
                                </div>
                            </div>
                        </div>

                        <!-- AI Disclaimer -->
                        <div class="alert alert-warning border-warning bg-warning bg-opacity-10 mb-4">
                            <div class="d-flex align-items-center">
                                <i class="fas fa-robot text-warning me-2"></i>
                                <div>
                                    <strong>AI Analysis:</strong> This assessment uses Claude AI and may contain errors.
                                    Always verify against official UWA requirements and consult academic advisors for final decisions.
                                </div>
                            </div>
                        </div>

                        <!-- Analysis Results -->
                        ${warnings.length > 0 ? `
                        <div class="mb-3">
                            <h6><i class="fas fa-exclamation-triangle text-warning me-2"></i>Warnings</h6>
                            <ul class="list-group list-group-flush">
                                ${warnings.map(warning => `<li class="list-group-item border-0 bg-light">${warning}</li>`).join('')}
                            </ul>
                        </div>
                        ` : ''}

                        ${recommendations.length > 0 ? `
                        <div class="mb-3">
                            <h6><i class="fas fa-lightbulb text-info me-2"></i>Recommendations</h6>
                            <ul class="list-group list-group-flush">
                                ${recommendations.map(rec => `<li class="list-group-item border-0 bg-light">${rec}</li>`).join('')}
                            </ul>
                        </div>
                        ` : ''}

                        ${strengths.length > 0 ? `
                        <div class="mb-3">
                            <h6><i class="fas fa-check-circle text-success me-2"></i>Strengths</h6>
                            <ul class="list-group list-group-flush">
                                ${strengths.map(strength => `<li class="list-group-item border-0 bg-light">${strength}</li>`).join('')}
                            </ul>
                        </div>
                        ` : ''}

                        <!-- Detailed Analysis -->
                        <div class="accordion" id="detailedAnalysis">
                            <div class="accordion-item">
                                <h2 class="accordion-header">
                                    <button class="accordion-button collapsed" type="button" data-bs-toggle="collapse" data-bs-target="#academicProgression">
                                        Academic Progression Analysis
                                    </button>
                                </h2>
                                <div id="academicProgression" class="accordion-collapse collapse" data-bs-parent="#detailedAnalysis">
                                    <div class="accordion-body">
                                        ${result.academicProgression || 'Analysis not available'}
                                    </div>
                                </div>
                            </div>
                            <div class="accordion-item">
                                <h2 class="accordion-header">
                                    <button class="accordion-button collapsed" type="button" data-bs-toggle="collapse" data-bs-target="#majorCoherence">
                                        Major Coherence & Career Pathway
                                    </button>
                                </h2>
                                <div id="majorCoherence" class="accordion-collapse collapse" data-bs-parent="#detailedAnalysis">
                                    <div class="accordion-body">
                                        <strong>Major Coherence:</strong> ${result.majorCoherence || 'Analysis not available'}<br><br>
                                        <strong>Career Pathway:</strong> ${result.careerPathway || 'Analysis not available'}
                                    </div>
                                </div>
                            </div>
                            <div class="accordion-item">
                                <h2 class="accordion-header">
                                    <button class="accordion-button collapsed" type="button" data-bs-toggle="collapse" data-bs-target="#constraintCompliance">
                                        Constraint & Policy Compliance
                                    </button>
                                </h2>
                                <div id="constraintCompliance" class="accordion-collapse collapse" data-bs-parent="#detailedAnalysis">
                                    <div class="accordion-body">
                                        <strong>Level Distribution:</strong> ${result.levelDistribution || 'Analysis not available'}<br><br>
                                        <strong>UWA Policy Compliance:</strong> ${result.constraintCompliance || 'Analysis not available'}
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>
                    <div class="modal-footer">
                        <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Close</button>
                        <button type="button" class="btn btn-primary" onclick="$('#qualityCheckModal').modal('hide'); $('#export-pdf').click();">
                            <i class="fas fa-file-pdf me-2"></i>Continue to PDF Export
                        </button>
                    </div>
                </div>
            </div>
        </div>
    `;

    // Remove existing modal if any
    $('#qualityCheckModal').remove();

    // Add modal to page
    $('body').append(modalHtml);

    // Show modal
    $('#qualityCheckModal').modal('show');
}

function showError(message) {
    alert(message); // Replace with better notification system
}

function logDebug(action, data) {
    const timestamp = new Date().toLocaleTimeString();
    const logEntry = `
        <div class="debug-entry">
            <div class="debug-timestamp">[${timestamp}]</div>
            <strong>${action}:</strong> ${JSON.stringify(data, null, 2)}
        </div>
    `;

    $('#debug-log').prepend(logEntry);

    // Keep only last 10 entries
    $('#debug-log .debug-entry').slice(10).remove();
}