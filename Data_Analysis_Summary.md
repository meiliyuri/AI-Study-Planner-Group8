# UWA Study Planner - Data Analysis Summary

## Current Data Sources Analysis

### Files Currently Used:
1. **Units Availabilities.csv** (4,073 rows) - Unit scheduling and operational details
2. **Units.csv** (10,429 rows) - Unit metadata, prerequisites, course mappings
3. **Sequence export (XXX-XXXXX).xlsx** - Specific course degree structures

### Additional CSV Files Available (Not Currently Used):
- **sequences table.csv** (5 rows) - Course definitions
- **sequencegroups table.csv** (18 rows) - Hierarchical structure
- **sequenceelements table.csv** (50 rows) - Unit mappings with internal IDs

## Key Findings

### What Each Data Source Provides:

**Units Availabilities.csv:**
- Unit scheduling: Year, teaching period, location, mode
- Operational details: Credit points, faculty, teaching responsibilities
- Links to units via `UnitCode`

**Units.csv:**
- Unit metadata: Code, title, prerequisites, corequisites, incompatibles
- Course curriculum mappings: Shows which degrees/majors each unit belongs to
- Rich course context and prerequisites

**Sequence Export Excel Files:**
- Complete course maps with unit codes, titles, prerequisites
- Rich metadata: Detailed descriptions, outcomes, curriculum mapping
- Course-specific structure and progression

## LLM Processing Test Results

Tested whether LLM could reconstruct Excel data from CSVs:

| Task | Status | Details |
|------|--------|---------|
| **Map numeric IDs to unit codes** | ❌ FAILED | Critical linking data missing between cIDs and unit codes |
| **Rebuild hierarchical structure** | ⚠️ PARTIAL | Can build structure but can't populate without ID mappings |
| **Reformat availability data** | ✅ SUCCESS | Can perfectly match Excel format |
| **Add course context** | ✅ SUCCESS | Can extract rich course context from Units.csv |

**Conclusion:** The critical blocker is mapping numeric IDs (cIDs) to unit codes. Without this, CSV reconstruction is not feasible.

## Web Scraping Alternative

### Data Availability:
- UWA Handbook online: https://handbooks.uwa.edu.au/
- Complete course structures available for all majors
- Standardized format across all major pages

### Assessment:
- **Technically feasible** but **medium-high complexity**
- **Pros:** Up-to-date data, complete coverage, automated updates
- **Cons:** Website dependency, maintenance overhead, legal considerations

### Recommendation:
- **Current project:** Stick with Excel exports (faster, lower risk, proven)
- **Future enhancement:** Consider web scraping for automation

## Sample Data Extracted:

### MJD-ECNPF (Economics) Structure:
- **Level 1 (24 points):** ECON1101, ECON1102, FINA1221, STAT1520
- **Level 2 (30 points):** Core units + electives
- **Level 3 (36 points):** Applied units + research methods

### MJD-FINEC (Financial Economics) Structure:
- **Level 1 (24 points):** Same as Economics
- **Level 2 (30 points):** Includes FINA2222 Corporate Financial Policy
- **Level 3 (36 points):** Focus on finance units like FINA3324, FINA3307

## Current Implementation Status:
✅ Working system using Excel exports
✅ Successfully imports Units.csv and Units Availabilities.csv
✅ Processes sequence Excel files for course structures
✅ Client exports sequence files for each degree they want to support

## Next Steps Discussion Points:
1. Client workflow: Export sequence files for popular degrees vs. all degrees
2. Automation possibilities: Web scraping for future enhancement
3. Data update frequency: How often do course structures change?
4. Scope expansion: How many majors does the client want to support initially?