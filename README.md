# Survey Fatigue Audit

Analyze Qualtrics surveys for cognitive fatigue issues and get actionable recommendations.

## Quick Start

### Installation

```bash
# Clone repository
git clone <repo-url>
cd survey-fatigue-audit

# Install dependencies
pip install -r requirements.txt
```

### Command-Line Usage

```bash
# Analyze a single survey
python analyze_survey.py survey.qsf

# Compare multiple surveys
python analyze_survey.py *.qsf --compare

# Executive summary
python analyze_survey.py *.qsf --executive

# View scoring explanation
python analyze_survey.py --explain
```

### Notebook Usage (Optional)

```bash
jupyter notebook notebooks/01-load-and-analyze-survey.ipynb
```

## What You Get

### Fatigue Score (0-100)

**IMPORTANT: Lower score = Better design = Less fatigue**

```
 0 ─────── 25 ─────── 50 ─────── 75 ─────── 100
 │          │          │          │          │
LOW      MODERATE    HIGH      EXTREME   CATASTROPHIC
✅         ⚠️         🔴         ❌         💀
```

- **0-25:** ✅ LOW RISK - Launch immediately
- **26-50:** ⚠️ MODERATE RISK - Review and optimize
- **51-75:** 🔴 HIGH RISK - Redesign required
- **76-100:** ❌ EXTREME RISK - Complete overhaul

### Category Breakdown

See exactly where fatigue comes from:
- **Loop Penalty** - Repeated question blocks
- **Cluster Penalty** - High-load questions grouped together
- **Position Penalty** - High-load questions late in survey
- **Grid Complexity** - Large matrix questions
- **Attention Checks** - Validation in fatigue zones
- **Skip Logic Bonus** - Effective question reduction

### Specific Issues

Each problem flagged with:
- Severity (Critical / High / Medium / Low)
- Question position
- Impact on score
- Fix recommendation

### Time & Drop-Off Estimates

- Estimated completion time (min-max range)
- Expected drop-off rate
- Effective sample size after fatigue

## What It Detects

### 🔴 Critical Issues

1. **Loops with 5+ iterations** (especially with open-ended questions)
2. **Open-ended questions inside loops**
3. **Matrix grids exceeding 50 cells**
4. **4+ high-load questions in sequence**

### ⚠️ High Priority Issues

5. **Loops with 3-4 iterations**
6. **Large grids (35-50 cells)**
7. **High-load questions in late survey positions (Q31+)**
8. **3+ high-load questions clustered**
9. **Attention checks after loop 2 or Q20+**

### 🟡 Medium Priority Issues

10. **Grids with 20-35 cells**
11. **High-load questions in mid-survey fatigue zone (Q21-30)**
12. **Missing skip logic opportunities**
13. **Back-to-back multi-select questions**

## Evidence Base

Based on research from:
- **Walr Study (n=1,000):** "Don't know" responses rose 50% by loop 3
- **Krosnick (1991):** Satisficing theory - respondents start agreeing by default when fatigued
- **SurveyMonkey (100k surveys):** Sharpest drop-off in first 15 questions
- **Jeong et al. (2023):** Extra hour increases skip rate by 10-64%

See `block1_design_your_survey.md` and `six_strategies_reduce_cognitive_fatigue.md` for full research references.

## Project Structure

```
survey-fatigue-audit/
├── notebooks/
│   └── 01-load-and-analyze-survey.ipynb    # Main analysis notebook
├── src/
│   ├── parsers/
│   │   └── qualtrics.py                    # QSF file parser
│   └── analyzers/
│       └── fatigue_scorer.py               # Scoring engine
├── data/
│   ├── sample-surveys/                     # Your QSF files go here
│   └── outputs/                            # Generated reports
├── requirements.txt
├── CLAUDE.md                               # Project instructions
└── README.md
```

## Scoring Algorithm

```
Total Score = Base Load + Position Multiplier + Cluster Penalties + Loop Penalties - Skip Logic Bonus

Where:
- Base Load = Sum of cognitive load from all question types
- Position Multiplier = Questions later in survey weighted higher
  - Q1-10: 1.0x
  - Q11-20: 1.2x
  - Q21-30: 1.5x
  - Q31+: 2.0x
- Cluster Penalties = High-load questions grouped (3+ in sequence)
- Loop Penalties = Iterations × Questions × Avg Load (heaviest penalty)
- Skip Logic Bonus = Effective question count reduction
```

## Fatigue Hierarchy

Question types ranked by cognitive load:

| Question Type | Cognitive Load | Score |
|---------------|----------------|-------|
| Single choice | Low | 5 |
| Slider | Low-Medium | 10 |
| Multiple choice | Medium | 15 |
| Text entry (short) | High | 25 |
| Matrix/Grid | High | 30+ (×cells) |
| Rank order | Very High | 35 |
| Text entry (long) | Extreme | 50 |

**Special case:** Questions in loops multiply their cognitive load by iteration count.

## Next Steps

1. **Trial with your QSF files** - Drop them in `data/sample-surveys/` and run the notebook
2. **Refine the parser** - QSF structure varies; we may need to adjust for your specific surveys
3. **Validate scoring** - Compare scores against known good/bad surveys
4. **Build HTML report generator** - Pretty output for stakeholders
5. **Package as Claude Code skill** - `/audit-survey survey.qsf`

## Contributing

Found a bug? Have a QSF file that doesn't parse correctly? Open an issue with:
- The QSF file (or sanitized version)
- Expected vs actual behavior
- Error messages

## License

Internal tool for survey research. Reference materials cite original sources.
