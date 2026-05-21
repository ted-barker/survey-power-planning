# Survey Fatigue Audit - Project Instructions

## Purpose

Analyze existing survey designs for cognitive fatigue issues. This project provides Jupyter notebooks that audit survey structures (from Qualtrics, SurveyMonkey, etc.) and identify fatigue-inducing patterns.

## Core Principles

**Cognitive Load is the Enemy**

Survey length matters less than cognitive effort. This tool identifies high-load patterns:
- Looped question blocks
- Grid/matrix questions
- Open-ended questions (especially in loops)
- Forced ranking tasks
- Attention checks in high-fatigue zones

**Evidence-Based Detection**

Based on research showing:
- "Don't know" responses rise 50% by loop iteration 3 (Walr study, n=1,000)
- Variance collapse happens mid-survey during fatigue
- Drop-off is concentrated early (not linear)
- Each loop iteration = withdrawal from attention budget

## Scoring System

**IMPORTANT: Lower score = Better design = Less fatigue**

The tool generates a **Fatigue Risk Score** from 0-100 points:

```
 0 ─────── 25 ─────── 50 ─────── 75 ─────── 100
 │          │          │          │          │
LOW      MODERATE    HIGH      EXTREME   CATASTROPHIC
✅         ⚠️         🔴         ❌         💀
```

**Risk Levels:**
- ✅ **LOW (0-25 points):** Excellent design, minimal fatigue → Launch immediately
- ⚠️ **MODERATE (26-50 points):** Acceptable with caveats → Review and optimize
- 🔴 **HIGH (51-75 points):** Problematic, major revisions needed → Redesign required
- ❌ **EXTREME (76-100 points):** Unacceptable, severe fatigue → Complete overhaul

**What the score measures:**
- Base cognitive load (question types × quantity)
- Position penalty (high-load questions late in survey)
- Loop penalty (repeated blocks multiply fatigue)
- Cluster penalty (high-load questions grouped together)
- Grid complexity (matrix dimensions)
- Attention check issues

**What reduces the score:**
- BIBD (Balanced Incomplete Block Design) - respondents see subset of questions
- Skip logic / DisplayLogic - conditional questions reduce effective length
- Simple question formats (single-choice, binary comparisons)
- Proper question sequencing (easy questions early, hard questions mid-survey)

## Project Structure

```
survey-fatigue-audit/
├── notebooks/
│   ├── 01-load-survey.ipynb          # Import QSF/platform exports
│   ├── 02-fatigue-analysis.ipynb     # Detect high-load patterns
│   ├── 03-generate-report.ipynb      # Output recommendations
│   └── examples/                     # Example audit workflows
├── src/
│   ├── parsers/                      # Platform-specific parsers
│   │   ├── qualtrics.py
│   │   ├── surveymonkey.py
│   │   └── typeform.py
│   ├── analyzers/
│   │   ├── fatigue_hierarchy.py      # Score questions by cognitive load
│   │   ├── loop_detector.py          # Identify repeated blocks
│   │   └── sequence_optimizer.py     # Suggest reordering
│   └── reporters/
│       ├── report_generator.py       # Create audit reports
│       └── visualizations.py         # Charts for fatigue patterns
├── data/
│   ├── sample-surveys/               # Example survey files
│   └── outputs/                      # Generated reports
├── tests/
└── requirements.txt
```

## Fatigue Hierarchy (Reference)

From lowest to highest cognitive load:

| Level | Question Type | Cognitive Load | Notes |
|-------|---------------|----------------|-------|
| 1 | Single-choice (radio) | Low | Easiest to answer |
| 2 | Multiple-choice (checkbox) | Low-Medium | Slightly harder than radio |
| 3 | Dropdown/Select | Medium | Requires scrolling/search |
| 4 | Slider/Scale | Medium | Visual but requires precision |
| 5 | Text entry (short) | Medium-High | Requires typing |
| 6 | Grid/Matrix (single) | High | Multiple questions at once |
| 7 | Grid/Matrix (multiple) | Very High | Compound cognitive load |
| 8 | Ranking | Very High | Requires comparison + ordering |
| 9 | Open-ended (long text) | Extreme | Highest effort |
| 10 | **Looped blocks** | **Multiplied** | Each iteration = attention withdrawal |

**Special Cases:**
- Attention checks in loops = high risk of false failures
- Open-ended questions in loops = fatigue accelerator
- Grids after loop 2 = variance collapse zone

## Key Workflows

### Workflow 1: Audit Existing Survey

1. **Load survey file** (QSF, JSON, or platform export)
   ```python
   from src.parsers.qualtrics import load_qsf
   survey = load_qsf('data/sample-surveys/user-research.qsf')
   ```

2. **Run fatigue analysis**
   ```python
   from src.analyzers.fatigue_hierarchy import analyze_survey
   report = analyze_survey(survey)
   ```

3. **Generate recommendations**
   ```python
   from src.reporters.report_generator import generate_report
   generate_report(report, output='data/outputs/audit-report.html')
   ```

### Workflow 2: Compare Survey Versions

Audit multiple versions and compare fatigue scores to see if changes improved or worsened cognitive load.

### Workflow 3: Pre-Launch Check

Run audit before survey launch to catch high-fatigue patterns early.

## Analysis Outputs

Each audit produces:

### 1. **Overall Fatigue Score** (0-100)

Composite score calculated from multiple factors:

```
Total Score = Base Load + Position Multiplier + Cluster Penalties + Loop Penalties - Skip Logic Bonus

Where:
- Base Load = Sum of individual question cognitive load scores
- Position Multiplier = Questions later in survey weighted higher (Q1-10: 1.0x, Q11-20: 1.2x, Q21-30: 1.5x, Q31+: 2.0x)
- Cluster Penalties = High-load questions grouped together (3+ in sequence)
- Loop Penalties = Iterations × questions × avg_load (heaviest penalty)
- Skip Logic Bonus = Effective question count reduction
```

**Interpretation:**
- **0-30:** Low risk (well-optimized survey)
- **31-50:** Moderate risk (acceptable, monitor in pilot)
- **51-70:** High risk (major revisions needed before launch)
- **71-100:** Critical risk (will produce unreliable data)

### 2. **Category Breakdown** (Point Contribution)

Detailed breakdown showing how each category contributes to the total score:

```
Total Fatigue Score: 68/100 (HIGH RISK)

Contributing Factors:
├─ Loop Penalty: 25 points
│  └─ 3 loops with 8-12 questions each, includes open-ended
├─ Cluster Penalty: 15 points
│  └─ 2 matrix grids back-to-back (Q18-19), 4 open-ended in sequence (Q28-31)
├─ Position Weight: 12 points
│  └─ High-load questions concentrated in Q20-35 range
├─ Grid Complexity: 10 points
│  └─ 10×7 grid at Q18 (70 cells), 8×5 grid at Q19 (40 cells)
├─ Attention Check: 6 points
│  └─ Validation question at Q27 (after loop 2 = false failure zone)
└─ Skip Logic Bonus: -8 points
   └─ Reduces effective question count by ~15%
```

### 3. **Specific Issues Flagged**

Each problem identified with:
- **Question ID/Position**
- **Issue Type** (loop, grid, cluster, attention check, etc.)
- **Severity** (Critical / High / Medium / Low)
- **Impact** (points contributed to score)
- **Fix Recommendation** (specific action to take)

**Example:**
```
🔴 CRITICAL: Loop Detected (Q15-Q22)
   - Loop iterations: 5
   - Questions per iteration: 8
   - Contains: 2 open-ended, 1 grid (6×5)
   - Impact: +18 points to fatigue score
   - Fix: Reduce to 2 iterations maximum, or remove open-ended from loop
   
⚠️ HIGH: Matrix Grid Dimensions (Q18)
   - Size: 10 rows × 7 columns (70 cells)
   - Position: Q18 (early-mid survey)
   - Impact: +6 points
   - Fix: Reduce to 5-7 rows maximum, or split into 2 separate grids
   
⚠️ HIGH: Question Cluster (Q28-Q31)
   - Type: 4 open-ended questions in sequence
   - Position: Late survey (fatigue zone)
   - Impact: +8 points
   - Fix: Spread throughout survey, or reduce to 1-2 maximum
```

### 4. **Time & Drop-Off Estimates**

- **Estimated completion time:** 18 minutes (range: 15-22 min)
- **Expected drop-off:** 32% (based on fatigue score + length)
- **Effective sample size:** If n=500 invited, expect ~340 completes

**Time breakdown by question type:**
- Single choice (n=15): ~60 seconds total
- Multiple choice (n=8): ~90 seconds total
- Grids (n=3): ~120 seconds total
- Open-ended (n=6): ~360 seconds total
- Loops (n=1, 5 iterations): ~600 seconds total

### 5. **Actionable Recommendations**

Prioritized list of changes ranked by impact:

**🔥 Critical (Do First):**
1. **Cut loop iterations from 5 to 2** → Saves 360 seconds, reduces score by 12 points
2. **Remove open-ended questions from loop** → Reduces score by 6 points
3. **Reduce Q18 grid from 10 rows to 6** → Reduces score by 4 points

**⚠️ High Priority:**
4. **Move attention check from Q27 to Q12** → Out of false failure zone, reduces score by 6 points
5. **Break up Q28-31 open-ended cluster** → Spread to Q10, Q15, Q25, Q35
6. **Add skip logic to Q23-25** → Could reduce effective questions by 20%

**✅ Medium Priority:**
7. **Front-load important questions** → Move segmentation questions to Q5-10
8. **Randomize multi-select option order** → Reduce primacy bias
9. **Add intro explaining survey purpose** → Increases perceived value, improves completion

**Expected Outcome:**
- Implementing Critical + High changes: **68 → 42** (High Risk → Moderate Risk)
- Implementing all recommendations: **68 → 28** (High Risk → Low Risk)

### 6. **Visual Reports**

- **Cognitive Load Curve:** Line chart showing cumulative fatigue by question position
- **Fatigue Heatmap:** Question grid colored by cognitive load (green → yellow → red)
- **Loop Impact Visualization:** Multiplier effect of repeated blocks
- **Drop-Off Risk Zones:** Highlight questions with highest abandonment risk
- **Category Contribution:** Pie chart showing score breakdown by penalty type

## Detection Rules

### Loop Detection
```python
# Flag any question block that repeats N times
# Especially problematic: N > 3
```

### Grid Detection
```python
# Flag matrix questions
# Especially problematic: multiple grids in sequence
```

### Sequence Issues
```python
# Flag high-load questions late in survey
# Flag attention checks after high-fatigue zones
```

### Skip Logic Opportunities
```python
# Identify branching opportunities to reduce question count
# Suggest conditional display based on prior responses
```

## Success Criteria

A good audit:
- ✅ Identifies all looped blocks
- ✅ Scores questions by cognitive load
- ✅ Detects grids and matrix questions
- ✅ Highlights attention checks in risky positions
- ✅ Generates actionable recommendations
- ✅ Produces visual reports (fatigue curves, heatmaps)
- ✅ Compares pre/post optimization

## Key References

**Research Evidence:**
- Walr study (UK, n=1,000): "Don't know" responses rose 50% by loop 3, engagement dropped ~20% in later iterations
- Variance collapse: respondents give same answer repeatedly during fatigue
- Drop-off pattern: concentrated early, not linear

**Frameworks:**
- BRUSO model (Brief, Relevant, Unambiguous, Specific, Objective) - Open Textbook BC
- Fatigue hierarchy (from Survey Science workshop, Block 1)
- Six strategies to reduce fatigue: cut loops, front-load, skip logic, randomize, break up multi-selects, manage perceived value

## Development Guidelines

**Code Style:**
- Use type hints for all functions
- Docstrings for all public methods
- Pytest for testing parsers and analyzers

**Parser Requirements:**
- Support Qualtrics QSF format (priority 1)
- Support SurveyMonkey exports (priority 2)
- Graceful degradation if format unrecognized

**Analysis Requirements:**
- Assign cognitive load score to each question
- Detect loops (explicit and implicit)
- Identify grids/matrices
- Calculate cumulative fatigue by position

**Reporting Requirements:**
- HTML report with embedded charts
- Markdown summary for quick review
- JSON export for programmatic access

## Common Mistakes to Avoid

1. ❌ **Don't treat all questions equally** - A loop with 5 questions is far worse than 5 sequential questions
2. ❌ **Don't ignore position** - Open-ended questions late in survey = high drop-off risk
3. ❌ **Don't miss implicit loops** - Some platforms hide loop structure in metadata
4. ❌ **Don't forget skip logic** - Analyze actual question count per respondent path, not total questions
5. ❌ **Don't overlook attention checks** - Placement matters; post-loop-2 = false failure zone

## Example Use Cases

**Use Case 1: Post-mortem**
Survey had 40% drop-off. Audit reveals:
- 3 nested loops (effective length 3x longer than apparent)
- Open-ended questions in loop 2 and 3
- Attention check after highest-fatigue grid

**Use Case 2: Pre-launch optimization**
Audit before launch reveals:
- Important segmentation questions buried at position 35
- Recommendation: move to position 5-10
- Result: better data quality on key variables

**Use Case 3: A/B test design**
Compare two versions:
- Version A: fatigue score 72 (high risk)
- Version B: fatigue score 48 (moderate risk)
- Choose Version B or optimize Version A further

## Integration with Other Projects

**Frontend Slide Maker:**
- Audit results can feed into workshop presentations
- Visualizations can be embedded in slides
- Teaching examples come from real audits

**Survey Science Workshop:**
- Real-world examples from audits
- Validate teaching principles with data
- Show before/after fatigue scores

## Next Steps

1. Set up Python environment and install dependencies
2. Create sample survey files for testing
3. Implement Qualtrics QSF parser
4. Build fatigue hierarchy analyzer
5. Generate first audit report
6. Add visualizations (fatigue curves, heatmaps)
7. Test with real survey files

## Notes

- Start with Qualtrics QSF format (most common in research)
- Focus on detection first, optimization second
- Keep reports actionable (specific recommendations, not generic advice)
- Validate against known high-fatigue surveys
