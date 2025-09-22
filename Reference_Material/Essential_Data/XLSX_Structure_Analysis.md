# XLSX Sequence Export Structure Analysis

## Overview
Analysis of 5 major sequence export files to understand structure patterns for extracting course requirements.

## File Structure Pattern

### Consistent Format Across All Files:
- **Sheet Name**: "Sequence export"
- **Header Rows**: First 2 rows are headers/metadata
- **Data Columns**:
  1. ID
  2. Code (Unit code)
  3. Title (Unit name)
  4. Availabilities (Semester/location info)
  5. Curriculum (Major assignment and type)
  6. Prerequisites
  7. Corequisites
  8. Incompatibilities
  9. Outcomes

### Key Pattern in Curriculum Column:
Units are classified for each major as:
- **"as core"** = Mandatory units
- **"as option"** = Optional units available to major
- **"as bridging"** = Optional foundation units (usually Level 1)

## Major Structure Analysis

### 1. Financial Economics (MJD-FINEC)
- **Foundation (Level 1)**: 4 core + 1 bridging = 5 units
- **Level 2**: 5 core + 0 optional = 5 units
- **Level 3**: 4 core + 8 optional = 12 units
- **Total in file**: 22 units
- **Requirements**: 13 mandatory + choose 9 from optional + 2 from outside major = 24 units

### 2. Economics (MJD-ECNPF)
- **Foundation (Level 1)**: 4 core + 1 bridging = 5 units
- **Level 2**: 4 core + 5 optional = 9 units
- **Level 3**: 3 core + 10 optional = 13 units
- **Total in file**: 27 units
- **Requirements**: 11 mandatory + choose 13 from 16 optional = 24 units

### 3. Agricultural Science (MJD-AGSCI)
- **Foundation (Level 1)**: 4 core + 3 bridging = 7 units
- **Level 2**: 4 core + 0 optional = 4 units
- **Level 3**: 4 core + 0 optional = 4 units
- **Total in file**: 15 units
- **Requirements**: 12 mandatory + 3 bridging + 9 from outside major = 24 units

### 4. Agribusiness (MJD-AGBUS)
- **Foundation (Level 1)**: 5 core + 2 bridging = 7 units
- **Level 2**: 3 core + 0 optional = 3 units
- **Level 3**: 4 core + 0 optional = 4 units
- **Total in file**: 14 units
- **Requirements**: 12 mandatory + 2 bridging + 10 from outside major = 24 units

### 5. Agricultural Technology (MJD-AGTEC)
- **Foundation (Level 1)**: 3 core + 3 bridging = 6 units
- **Level 2**: 3 core + 0 optional = 3 units
- **Level 3**: 4 core + 0 optional = 4 units
- **Total in file**: 13 units
- **Requirements**: 10 mandatory + 3 bridging + 11 from outside major = 24 units

## Systematic Parsing Strategy

### 1. Extract Unit Level
Parse unit code position 5 to determine level:
- `1` = Foundation (Level 1)
- `2` = Level 2
- `3` = Level 3

### 2. Classify Unit Type
Search curriculum column for major ID pattern and classify:
- **Mandatory**: Contains "as core"
- **Optional**: Contains "as option"
- **Bridging**: Contains "as bridging"

### 3. Calculate Requirements
For each major:
1. Count mandatory units by level
2. Count optional units available by level
3. Calculate: `additional_needed = 24 - mandatory_count`
4. Determine if additional units needed from outside major

### 4. Choice Logic Patterns
- **Economics majors**: Rich optional pools allow choice within major
- **Agricultural majors**: Limited pools require external unit selection
- **No complex group logic** found (like "choose 2 from group A, 3 from group B")

## Programming Implementation

### Data Structure:
```python
major_structure = {
    "mandatory_units": {
        "level_1": [unit_codes],
        "level_2": [unit_codes],
        "level_3": [unit_codes]
    },
    "optional_units": {
        "level_1": [unit_codes],
        "level_2": [unit_codes],
        "level_3": [unit_codes]
    },
    "bridging_units": [unit_codes],
    "total_mandatory": int,
    "additional_needed": int,
    "external_units_required": int
}
```

### Key Parsing Logic:
1. Skip first 2 header rows
2. For each unit row, extract curriculum info for specific major
3. Classify by level and type using unit code and curriculum text
4. Calculate completion requirements

## Conclusion

✅ **Consistent structure** across all files enables systematic parsing
✅ **Clear classification** system (core/option/bridging)
✅ **Level-based organization** follows predictable pattern
⚠️ **External unit requirements** for Agricultural majors need additional data source
✅ **No complex choice group logic** - simple "choose X from Y" patterns only

The XLSX files provide sufficient structure for automated parsing of major requirements, though Agricultural majors will need supplementary data for complete degree planning.