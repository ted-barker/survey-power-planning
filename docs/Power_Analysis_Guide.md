# Power Analysis & Sample Planning Guide

**Version:** 3.0  
**Last Updated:** 2026-05-23  
**Tool:** Power Analysis & Sample Planning

---

## Table of Contents

1. [Overview](#overview)
2. [Quick Start](#quick-start)
3. [Workflows](#workflows)
4. [Statistical Tests Supported](#statistical-tests-supported)
5. [Segment Analysis](#segment-analysis)
6. [Integrated Planning](#integrated-planning)
7. [Interpreting Results](#interpreting-results)
8. [Best Practices](#best-practices)
9. [Troubleshooting](#troubleshooting)
10. [API Reference](#api-reference)

---

## Overview

### What Does This Tool Do?

**Power Analysis & Sample Planning** helps researchers determine:

1. **Statistical Power** 📊  
   How many **completes** do I need for my statistical test?

2. **Survey Logistics** 📧  
   How many **invitations** should I send accounting for drop-off?

3. **Integrated Workflow** ⚡  
   Both: Statistical power → Survey design → Invitations needed

### Key Features

- ✅ Conversational agent guides you through analysis
- ✅ Supports all common statistical tests (t-test, ANOVA, regression, segments)
- ✅ Integrates survey fatigue to estimate drop-off
- ✅ Interactive visualizations (power curves, sensitivity analysis)
- ✅ Minimum segment size validation (ensures reliable inference)

---

## Quick Start

### Launch the App

```bash
cd survey-fatigue-audit
streamlit run app.py
```

Opens at: `http://localhost:8501`

### Choose Your Path

**Option 1: Guided Agent (Recommended)**
- Conversational Q&A
- Recommends appropriate test
- Walks through all parameters

**Option 2: Power Calculators**
- Direct access if you know your test
- Manual parameter entry
- Quick results

**Option 3: Optimizer**
- For calculating invitations when you already know completes needed
- Accounts for survey fatigue and drop-off

---

## Workflows

### Workflow 1: Statistical Power Only

**Use When:** You just need sample size for your analysis

**Steps:**
1. Choose "Calculate sample size" (option 1)
2. Describe your research question
3. Specify effect size
4. Get required completes

**Example:**
```
You: Compare satisfaction between two designs
Agent: Independent t-test → Need 128 participants (64 per group)
```

---

### Workflow 2: Integrated Planning

**Use When:** You need both statistical power AND invitation count

**Steps:**
1. Choose "Integrated planning" (option 2)
2. Describe your research question
3. Specify effect size
4. Enter survey fatigue score
5. Get completes + invitations needed

**Example:**
```
You: Test differences across 3 user segments (60%, 30%, 10%)
Agent: Need 296 completes
       With fatigue score 68 → Send 461 invitations
```

---

## Statistical Tests Supported

### 1. Independent T-Test

**Use For:** Comparing means between two independent groups

**Parameters:**
- Effect size: Cohen's d (small=0.2, medium=0.5, large=0.8)
- Alpha: Usually 0.05
- Power: Usually 0.80 (80%)

**Example:** Do users prefer Design A or Design B?

---

### 2. One-Way ANOVA

**Use For:** Comparing means across 3+ groups

**Parameters:**
- Effect size: Cohen's f (small=0.1, medium=0.25, large=0.4)
- Number of groups
- Alpha: 0.05
- Power: 0.80

**Example:** Do satisfaction scores differ across 4 product tiers?

---

### 3. Multiple Regression

**Use For:** Predicting outcome from multiple variables

**Parameters:**
- Effect size: f² (small=0.02, medium=0.15, large=0.35)
- Number of predictors
- Alpha: 0.05
- Power: 0.80

**Example:** What predicts customer satisfaction? (predictors: price, quality, support)

---

### 4. Segment Analysis (LCA)

**Use For:** Comparing outcomes across pre-specified segments

**Parameters:**
- Number of segments
- Prevalence (percentage in each segment)
- Effect size: Cohen's f
- Alpha: 0.05
- Power: 0.80

**Example:** Do NPS scores differ across 3 user personas (40%, 40%, 20%)?

**⚠️ Important:** Tool automatically ensures minimum 30 participants per segment for reliable inference.

---

## Segment Analysis

### Overview

Segment analysis is designed for **pre-specified groups** (e.g., from latent class analysis, cluster analysis, or theoretical segmentation).

### Key Considerations

#### 1. Minimum Sample Size

**Rule:** Each segment needs **minimum 30 participants** for reliable statistical inference.

**What the tool does:**
- Calculates total sample based on statistical power
- Checks if smallest segment has ≥30
- If not, scales up total sample to meet threshold

**Example:**

```
Initial calculation: 158 total
Allocation by prevalence (60%, 30%, 10%):
- Segment 1: 95 ✅
- Segment 2: 48 ✅
- Segment 3: 16 ❌ (below minimum)

Adjusted calculation: 296 total
- Segment 1: 178 ✅
- Segment 2: 89 ✅
- Segment 3: 30 ✅ (meets minimum)
```

#### 2. Unbalanced Segments

**Challenge:** Small segments (e.g., 10% prevalence) require large total samples.

**Solutions:**
- **Disproportionate sampling:** Oversample small segments
- **Combine segments:** Merge small groups if theoretically justified
- **Increase budget:** Accept larger total sample needed

#### 3. Prevalence Validation

**Tool validates:**
- ✅ Prevalence values sum to 100%
- ✅ All segments have positive prevalence
- ✅ Values are in valid range (0-100%)

**Error handling:**
```
Input: "60, 30, 1" (sums to 91%)
Output: ❌ Prevalence should sum to 100%. You entered 91%
        Did you mean: '60, 30, 10'?
```

---

## Integrated Planning

### Overview

Combines **statistical power** with **survey logistics** to calculate final invitation count.

### The Process

```
1. Power Analysis → Required Completes
   Example: Need 200 completes for 80% power

2. Fatigue Audit → Estimated Drop-off
   Fatigue score 68/100 → 35.8% drop-off

3. Calculate Invitations
   200 / (1 - 0.358) = 312 invitations
```

### Fatigue Score Reference

| Score | Risk Level | Expected Drop-off | Characteristics |
|-------|------------|-------------------|-----------------|
| 0-25 | Low | 5-15% | Simple survey, <10 min, single-choice questions |
| 26-50 | Moderate | 15-25% | Typical survey, 10-15 min, mix of question types |
| 51-75 | High | 25-40% | Complex survey, loops, grids, 15-20 min |
| 76-100 | Extreme | 40-60% | Very complex, multiple loops, >20 min |

### Optimization

**If invitations needed is too high:**

1. **Reduce survey complexity**
   - Remove loops or reduce iterations
   - Simplify grids
   - Add skip logic

2. **Re-run fatigue audit**
   - New fatigue score → Lower drop-off

3. **Recalculate invitations**
   - Fewer invitations needed ✅

**Example:**
```
Before optimization:
- Fatigue: 68/100
- Drop-off: 35.8%
- Invitations: 312

After reducing to moderate fatigue:
- Fatigue: 50/100
- Drop-off: 25%
- Invitations: 267 (saves 45 invitations!)
```

---

## Interpreting Results

### Power Analysis Output

```
✅ Power Analysis Complete!

Required Sample Size: 296

Study Parameters:
- Power: 80%
- Significance level (α): 0.05
- Effect size: 0.10

Sample per segment:
- Segment 1 (60%): 178 participants
- Segment 2 (30%): 89 participants
- Segment 3 (10%): 30 participants

⚠️ Smallest segment has 30 participants. 
   Minimum 30 recommended for reliable inference.
```

### Key Metrics

**Power (80%):** 80% chance of detecting the effect if it exists

**Alpha (0.05):** 5% chance of false positive (Type I error)

**Effect Size:** Magnitude of difference you expect to find
- Larger effect = Smaller sample needed
- Smaller effect = Larger sample needed

---

## Best Practices

### 1. Effect Size Selection

**Conservative approach (Recommended):**
- Use "small" effect sizes
- Requires larger sample but less risk of being underpowered
- Better for exploratory research

**Informed approach:**
- Based on pilot data or literature
- More efficient sample sizing
- Requires domain knowledge

**Power user tip:** If uncertain, run sensitivity analysis to see detectable effects at different sample sizes.

---

### 2. Segment Analysis

**Do:**
- ✅ Ensure theoretical justification for segments
- ✅ Verify minimum 30 per segment
- ✅ Consider oversampling small segments if critical
- ✅ Document prevalence assumptions

**Don't:**
- ❌ Create segments post-hoc to "find significance"
- ❌ Ignore small segment warnings
- ❌ Assume equal allocation is always best
- ❌ Forget to validate prevalence sums to 100%

---

### 3. Integrated Workflow

**Do:**
- ✅ Run power analysis first (know required completes)
- ✅ Design survey with fatigue in mind
- ✅ Run fatigue audit before fielding
- ✅ Iterate: Optimize survey → Re-calculate invitations

**Don't:**
- ❌ Skip fatigue audit (leads to underpowered studies)
- ❌ Ignore high fatigue warnings
- ❌ Assume response rate = completion rate
- ❌ Forget to account for screening criteria

---

## Troubleshooting

### Issue: "Sample size seems too large"

**Possible causes:**
1. Small effect size (solution: justify larger effect or accept larger n)
2. Many segments with low prevalence (solution: oversample or combine)
3. High desired power (solution: reduce to 70-80% if acceptable)

**Check:** Run sensitivity analysis to see effect sizes detectable with your budget.

---

### Issue: "Segment too small (< 30)"

**What it means:** Smallest segment has fewer than 30 participants, risking unreliable estimates.

**Solutions:**
1. **Accept larger total sample** (tool auto-adjusts)
2. **Oversample small segment** (disproportionate allocation)
3. **Combine small segments** (if theoretically valid)
4. **Simplify analysis** (remove small segment)

---

### Issue: "Prevalence doesn't sum to 100%"

**What it means:** Segment percentages entered incorrectly.

**Example error:**
```
Input: "60, 30, 1"
Sum: 91% ❌

Correct: "60, 30, 10"
Sum: 100% ✅
```

**Tool provides suggestion:** Shows what you entered and correct format.

---

### Issue: "Too many invitations needed"

**What it means:** High survey fatigue → High drop-off → Many invitations.

**Solutions:**
1. **Optimize survey design:**
   - Reduce loops (max 2 iterations)
   - Simplify grids (<5 rows)
   - Add skip logic

2. **Re-run fatigue audit** → Get new score

3. **Recalculate invitations** → See improvement

**Target:** Fatigue score <50 for moderate drop-off (<25%).

---

## API Reference

### Agent Commands

| Command | Function | Example |
|---------|----------|---------|
| `1` or `2` | Choose workflow | Type at start |
| `small`, `medium`, `large` | Effect size | "medium" |
| `60, 30, 10` | Segment prevalence | Flexible format |
| `calculate` | Calculate sample size | Instead of entering existing n |
| `restart` | Start over | Any time |
| `back` | Return to previous step | Any time |

---

### Python API

#### Example: Segment Power Analysis

```python
from src.power.calculators.segments import SegmentPowerCalc

# Initialize
calc = SegmentPowerCalc(
    n_segments=3,
    prevalence=[0.60, 0.30, 0.10],
    test_type='anova'
)

# Calculate required sample
result = calc.calculate(
    effect_size=0.25,  # Cohen's f
    alpha=0.05,
    power=0.80,
    solve_for='n',
    min_segment_n=30  # Optional: enforce minimum
)

print(f"Total needed: {result['total_n']}")
print(f"Per segment: {result['n_per_segment']}")
```

#### Example: Integrated Planning

```python
from src.power.integrations.dropoff import integrated_sample_plan

# Combine power + fatigue
sample_plan = integrated_sample_plan(
    power_result=result,  # From power analysis
    fatigue_score=68,     # From survey audit
    response_rate=1.0
)

print(f"Invitations: {sample_plan['sample_plan']['invitations_needed']}")
print(f"Completes: {sample_plan['power_analysis']['required_completes']}")
print(f"Drop-off: {sample_plan['fatigue_audit']['estimated_dropoff_rate']:.1%}")
```

---

## Support

**Questions?**
- Check FAQ in app
- Review example notebooks in `notebooks/`
- Consult CLAUDE.md for detailed workflows

**Found a bug?**
- GitHub issues: [repository link]

---

## Version History

**v3.0 (2026-05-23)**
- ✅ Added conversational agent
- ✅ Minimum segment size validation (n≥30)
- ✅ Back command for navigation
- ✅ Summary before calculation
- ✅ Comprehensive error validation
- ✅ Integrated workflow (power + fatigue)

**v2.0 (Previous)**
- Basic power calculators
- Jupyter notebooks

---

*Generated with Power Analysis & Sample Planning v3.0*
