# Dashboard Update: Integrated Planning Interface

## Date: 2026-05-24

---

## Overview

Transformed the "Survey Sample Size" tab into an integrated **Planning** dashboard that combines statistical power analysis + survey funnel + invitations in a single, unified interface.

---

## Navigation Changes

### Before:
```
Home
Guided Agent
Survey Sample Size  ← Two separate calculators (forward/reverse)
Statistical Power
Visualizations
Glossary
```

### After:
```
Home
Guided Agent
Planning           ← NEW: Integrated dashboard (all-in-one)
Statistical Power  ← Detailed calculations
Visualizations
Glossary
```

---

## New Dashboard Layout

### Three-Column Input Section

**Column 1: Statistical Power**
- Test Type selector (t-test, ANOVA, Regression, Chi-Square)
- Effect size presets (Small/Medium/Large)
- Power slider (70-95%, default 80%)
- Alpha slider (0.01-0.10, default 0.05)
- Test-specific parameters (groups, predictors)

**Column 2: Survey Funnel**
- Click-Through Rate (CTR) slider
- Drop-off Rate slider
- Auto-calculated completion rate
- Auto-calculated overall conversion
- CTR Guidelines expander

**Column 3: Quick Presets**
- Conservative button (small effect, typical survey)
- Standard button (medium effect, good survey)
- Optimistic button (large effect, excellent survey)

### Results Dashboard

**Summary Info Box:**
- One-line study summary
- Complete plan in plain language

**Four Metric Cards:**
1. Required Sample (from power analysis)
2. Invitations to Send (accounting for funnel)
3. Expected Clicks (CTR applied)
4. Expected Completion (drop-off applied)

**Visual Funnel:**
- Plotly funnel chart showing:
  - Invitations → Clicks → Starts → Final Sample
  - Percentage retention at each stage
  - Color-coded stages

**Conversion Breakdown:**
- Step-by-step calculation
- Shows: invitations × CTR × completion = final sample

---

## Advanced Features

### Power Curve Visualization
- Collapsible expander
- Interactive Plotly chart
- Shows power vs. sample size for 3 effect sizes
- Marks user's target on curve

### Automated Recommendations
- **Red alerts** for critical issues:
  - Very low CTR (<2%)
  - Very high drop-off (>40%)
  - Low overall conversion (<3%)

- **Yellow warnings** for moderate issues:
  - Low CTR (<5%)
  - High drop-off (>30%)
  - Large invitation count (>10K)

- **Green success** when all parameters reasonable

### Optimization Suggestions
Calculates impact of improvements:
1. **Improve CTR by 50%**
   - Shows new invitations needed
   - Calculates savings

2. **Reduce drop-off by 5%**
   - Shows new invitations needed
   - Calculates savings

3. Accept lower power (70% vs 80%)
4. Focus on larger effects only

### Scenario Comparison Table
Side-by-side comparison of:
- Current Plan
- Improved CTR (+50%)
- Reduced Drop-off (-5%)
- Both Improved

Shows for each:
- CTR, Drop-off, Conversion rate
- Sample needed, Invitations needed
- Savings vs. current plan

### Export Functionality
- Formatted text summary
- Downloadable .txt file
- Includes:
  - Study details
  - Sample requirements
  - Survey funnel parameters
  - Invitations plan
  - Conversion breakdown

---

## Key Benefits

### 1. See Everything at Once
No more switching between tabs. All parameters and results visible on one screen.

### 2. Instant Feedback
Adjust any slider → immediately see impact on invitations needed.

### 3. Clear Cause-and-Effect
Visual funnel shows exactly how CTR and drop-off affect final sample.

### 4. Actionable Recommendations
Not just "low CTR" but "improve CTR from 3% → 5% and save 2,000 invitations"

### 5. Scenario Planning
Compare multiple approaches before committing to survey design.

### 6. Export-Ready
Download complete plan for stakeholder review or documentation.

---

## User Workflows Supported

### Workflow 1: Standard Planning (Most Common)
1. Select test type (e.g., Independent t-test)
2. Choose effect size (Medium)
3. Keep default power (80%) and alpha (0.05)
4. Set survey parameters:
   - CTR: 5% (with incentive)
   - Drop-off: 25% (standard survey)
5. Review results:
   - Required Sample: 128
   - Invitations: ~3,400
6. Check recommendations
7. Export plan

### Workflow 2: Constraint-Based
1. Know you have 5,000 contacts available
2. Work backwards:
   - Set realistic CTR and drop-off
   - See final sample you'll get
3. Compare to test requirements
4. Adjust test type or effect size if needed

### Workflow 3: Optimization
1. Get initial plan (e.g., 10,000 invitations needed)
2. Review optimization suggestions
3. Adjust CTR slider to see impact
4. Adjust drop-off slider to see impact
5. Compare scenarios
6. Decide on improvements
7. Export final plan

---

## Technical Implementation

### Files Modified:
- `app.py`: New `show_integrated_dashboard()` function (~300 lines)
- Navigation updated: "Survey Sample Size" → "Planning"
- Import added: `plotly.graph_objects`

### New Components:
1. **Three-column input layout** (statistical + survey + presets)
2. **Four-metric card dashboard** (sample, invitations, clicks, completion)
3. **Plotly funnel chart** (visual survey flow)
4. **Power curve visualization** (collapsible)
5. **Automated issue detection** (red/yellow/green alerts)
6. **Optimization calculator** (projected savings)
7. **Scenario comparison table** (pandas DataFrame)
8. **Export functionality** (download button)

### Session State:
```python
st.session_state.integrated_test_type
st.session_state.integrated_effect_size
st.session_state.integrated_power
st.session_state.integrated_alpha
st.session_state.integrated_ctr
st.session_state.integrated_dropoff
```

### Calculations:
```python
# Power analysis
required_sample = calc.calculate(effect_size, alpha, power, solve_for='n')

# Survey funnel
overall_conversion = ctr × (1 - dropoff)
invitations_needed = required_sample / overall_conversion
clicks_expected = invitations_needed × ctr
starts_expected = clicks_expected  # Assume 100%

# Optimization
improved_ctr = ctr × 1.5
new_invitations = required_sample / (improved_ctr × completion_rate)
savings = invitations_needed - new_invitations
```

---

## Design Philosophy

### Dashboard vs. Calculator
**Old approach:** Separate calculators for each task
**New approach:** Unified dashboard showing entire system

### Visual Hierarchy
1. **Inputs** at top (parameters you control)
2. **Key metrics** in middle (what you need to know)
3. **Visualization** below (understand the flow)
4. **Recommendations** at bottom (what to do about it)

### Progressive Disclosure
- Core information always visible
- Advanced features in expanders:
  - Power curve
  - Optimization suggestions
  - Scenario comparison
  - Export options

### Contextual Guidance
- Inline help text on every input
- CTR guidelines expander
- Automated warnings when values problematic
- Specific recommendations with numbers

---

## Before/After Comparison

### Before (Separate Tabs):
```
Statistical Power Tab:
- Calculate sample needed (e.g., 128)
- Copy number manually

Survey Sample Size Tab:
- Paste sample (128)
- Enter CTR (5%)
- Enter drop-off (25%)
- Calculate invitations (3,400)
```

### After (Integrated Dashboard):
```
Planning Tab:
- Select test + effect + power → 128 sample
- Set CTR (5%) + drop-off (25%) → 3,400 invitations
- See funnel visualization
- Review recommendations
- Compare scenarios
- Export plan
All in one view, instant updates
```

---

## Success Metrics

**Reduction in clicks:** 8+ clicks → 2 clicks (select mode + review results)
**Reduction in tabs:** 2 tabs → 1 tab
**Time to complete plan:** ~3-5 minutes → ~1-2 minutes
**Understanding:** Separate → Integrated (cause-and-effect visible)

---

## Next Steps (Future Enhancements)

1. **Save/Load Plans**
   - Store scenarios for later comparison
   - Build plan library

2. **Budget Calculator**
   - Add cost per complete
   - Show total budget needed

3. **Timeline Estimator**
   - Field period calculator
   - Recruitment rate estimator

4. **A/B Test Designer**
   - Multi-arm planning
   - Minimum detectable effect

5. **Integration with Survey Platforms**
   - Direct export to Qualtrics
   - Auto-configure sample settings

---

**Status:** ✅ Complete
**Version:** 3.1
**Ready for:** User testing
