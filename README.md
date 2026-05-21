# Survey Fatigue Audit

**Analyze Qualtrics surveys for cognitive fatigue risk using evidence-based scoring.**

Detects BIBD, skip logic, loops, grids, and position effects. Get actionable recommendations before launch.

---

## Quick Start

### 1. Install

```bash
# Clone repository
git clone https://github.com/ted-barker/survey-fatigue-audit.git
cd survey-fatigue-audit

# Install dependencies
pip install -r requirements.txt
```

### 2. Test with Example

```bash
# Analyze the included example survey
python analyze_survey.py data/sample-surveys/Bold_Claims_2AFC_BIBD.qsf
```

**You'll see:**
- Visual scoring explanation (0-100 scale)
- Score: 2.3/100 (LOW RISK)
- Time estimate: 3-6 minutes
- Detailed breakdown by category
- Specific recommendations

### 3. Analyze Your Survey

```bash
# Export your survey from Qualtrics as .qsf file
# Place it in data/sample-surveys/
# Run analysis

python analyze_survey.py data/sample-surveys/your-survey.qsf
```

---

## Usage Examples

### Analyze Single Survey

```bash
python analyze_survey.py my-survey.qsf
```

**Output includes:**
- Score (0-100 points, lower = better)
- Risk level (LOW/MODERATE/HIGH/EXTREME)
- Time estimate (minutes)
- Expected drop-off rate
- Issue breakdown by severity
- Specific recommendations

### Compare Multiple Surveys

```bash
python analyze_survey.py survey1.qsf survey2.qsf survey3.qsf --compare
```

**Shows:**
- Side-by-side comparison table
- All surveys sorted by score (best to worst)
- Time and drop-off for each

### Executive Summary

```bash
python analyze_survey.py *.qsf --executive
```

**Shows:**
- Count by risk level
- One-line recommendation per survey
- Quick prioritization for stakeholders

### View Scoring System

```bash
python analyze_survey.py --explain
```

**Shows:**
- Visual 0-100 scale explanation
- Risk level definitions
- What each level means

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

## Understanding Your Results

### Example Output

```
╔══════════════════════════════════════════════════════════════════════════╗
║                     SURVEY FATIGUE SCORING SYSTEM                        ║
╚══════════════════════════════════════════════════════════════════════════╝

 0 ─────── 25 ─────── 50 ─────── 75 ─────── 100
 │          │          │          │          │
LOW      MODERATE    HIGH      EXTREME   CATASTROPHIC
✅         ⚠️         🔴         ❌         💀

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
SCORE: 2.3/100 points
RISK LEVEL: ✅ LOW
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
INTERPRETATION: Excellent design, minimal fatigue → Launch immediately

Estimated time: 3-6 minutes
Expected drop-off: 10.0%

SCORE BREAKDOWN:
+ Base Load: 2.3 points
  └─ Cognitive load per respondent (BIBD: 14 effective questions)
+ Position Penalty: 0.0 points
+ Grid Complexity: 0.0 points

✅ NO ISSUES DETECTED
```

### What the Score Means

**Lower score = Better design = Less fatigue**

- **Score 2.3** means 2.3% of maximum possible fatigue
- **97.7% better** than worst possible design
- **Excellent** survey ready to launch

### When to Be Concerned

| Your Score | What It Means | Action |
|------------|---------------|--------|
| **0-25** | ✅ Excellent to good | Launch immediately or with minor tweaks |
| **26-50** | ⚠️ Acceptable but improvable | Review recommendations, optimize before launch |
| **51-75** | 🔴 Problematic | Major revisions required before launch |
| **76-100** | ❌ Severe issues | Complete redesign needed |

---

## What The Tool Detects

### Advanced Survey Techniques

**BIBD Detection** ✅
- Detects Balanced Incomplete Block Design
- Scores based on questions per respondent, not total questions
- Example: 58 questions → 14 per respondent → Score 2.3 (excellent)

**Skip Logic Detection** ✅
- Detects DisplayLogic / conditional questions
- Adjusts score for reduced respondent burden
- Example: 30 questions, 63% conditional → Score 9.6 (excellent)

**What makes these features unique:**
- Other tools (Qualtrics, SurveyMonkey) don't account for BIBD or skip logic
- This tool scores actual respondent experience, not total question pool

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

## Real-World Examples

### Example 1: Exemplary Design (Bold Claims, Score 2.3)

**Survey structure:**
- 58 questions total, 14 per respondent (BIBD)
- Simple 2-choice questions (best-worst scaling)
- 3-6 minute completion time

**Why it scores so low (good):**
- BIBD ensures respondents see subset of questions
- Consistent, simple question format throughout
- No loops, grids, or open-ended questions

**Result:** 2.3% of maximum fatigue - near perfect

### Example 2: Needs Optimization (Wise Business, Score 29.3)

**Survey structure:**
- 22 questions, 4-7 minutes
- One 60-cell matrix grid (4 rows × 15 columns)
- Some text entry questions clustered

**Issues detected:**
- 🔴 HIGH: 60-cell matrix grid (10 points)
- 🟡 MEDIUM: Text entry questions clustered (9 points)

**Recommendation:** Split the matrix grid → score drops to ~15-18

### Example 3: Major Revisions Needed (Singapore, Score 69.0)

**Survey structure:**
- 145 questions, 20-32 minutes
- 21% have skip logic (31 conditional)
- Multiple matrix grids

**Issues detected:**
- Skip logic helps but insufficient coverage
- Length alone is major fatigue factor
- Will lose 25.6% of respondents

**Recommendation:** Increase skip logic to 40-50% coverage OR cut 30-40 questions

---

## Evidence Base

Built on peer-reviewed research:

- **Krosnick (1991):** Satisficing theory - respondents take mental shortcuts when fatigued
- **Galesic & Bosnjak (2009):** Drop-off probability increases exponentially with survey length
- **Walr Study (n=1,000):** "Don't know" responses rose 50% by loop iteration 3
- **Jeong et al. (2023):** Extra survey hour increases skip rate by 10-64%
- **Cochran (1977):** Balanced incomplete block designs maintain statistical power with reduced burden

**See `SCORING_SYSTEM_DEFENSE.md` for complete research citations and validation.**

---

## Frequently Asked Questions

### Can I trust this score?

**Yes, with context.** The score is:
- ✅ Built on 30+ years of peer-reviewed research
- ✅ Validated against real surveys with known outcomes
- ✅ Transparent and auditable (see the math in source code)
- ✅ Calibrated against industry benchmarks (Pew, Qualtrics, AAPOR)

**Use it for:**
- Relative comparisons (Survey A vs B)
- Identifying major structural issues
- Time and drop-off estimates (±20% accuracy)

**Don't rely on it for:**
- Question wording quality (use cognitive testing)
- Exact drop-off predictions
- Replacing pilot testing

**Read `SCORING_SYSTEM_DEFENSE.md` for complete stakeholder defense.**

### What if my survey gets a high score?

**Don't panic.** High scores identify specific fixable issues:

1. **Read the breakdown** - See which categories contribute most points
2. **Check the issues** - Each issue has a specific recommendation
3. **Fix the biggest contributors** - Usually 1-3 major issues drive the score
4. **Re-run analysis** - See the improvement

**Example:** Survey with score 52 had one 80-cell grid. Split the grid → score dropped to 28.

### How accurate are the time estimates?

**Generally within ±2 minutes.** Based on:
- Question count × average time per question type
- Adjusted for BIBD and skip logic
- Validated against real survey completion data

**Factors that affect accuracy:**
- Respondent familiarity with topic
- Incentives (incentivized = faster)
- Device type (mobile = slower)

### Does this work for non-Qualtrics surveys?

**Currently:** Only Qualtrics .qsf files

**Future:** Parsers can be added for:
- SurveyMonkey
- Typeform
- Google Forms
- LimeSurvey

The scoring logic is platform-agnostic.

---

## Contributing

Found a bug or have a QSF file that doesn't parse correctly?

**Open an issue with:**
1. The QSF file (or sanitized version removing sensitive content)
2. Expected vs actual behavior
3. Error messages or incorrect scores

**Pull requests welcome for:**
- Additional platform parsers
- Improved detection algorithms
- Bug fixes

---

## License

MIT License - see LICENSE file for details.

Research citations and methodology based on published peer-reviewed work.
