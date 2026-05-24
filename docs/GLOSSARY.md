# Power Analysis & Survey Planning Glossary

Definitions of all technical terms used in the tool (alphabetical order).

---

## A

### Significance Level (α - Alpha)
**Definition:** Probability of false positive (Type I error) - finding an effect when none exists.

**Standard:** 0.05 (5%)
- Meaning: 5% chance of incorrectly claiming an effect exists
- Alternative values: 0.01 (stricter), 0.10 (more lenient)

**Trade-off:** Lower α (stricter) requires larger samples.

---

## B

### Buffer
**Definition:** Safety margin added to invitation count (optional).

**Formula:** Invitations × (1 + buffer)

**Example:** 
- Need 1,000 invitations
- 10% buffer
- Send: 1,000 × 1.10 = 1,100

**Use when:** Uncertain about CTR/drop-off estimates, need extra cushion for deadlines.

---

## C

### Click-Through Rate (CTR)
**Definition:** Percentage of people who click your survey invitation link.

**Formula:** CTR = Clicks ÷ Invitations

**Realistic Ranges:**
- No incentive: ~1% or below
- Standard email campaign: 2-5%
- With prize draw/incentive: 5-10%
- Best case (with prize draw): ~10%
- Intercept survey (in-app pop-up): 100% (no CTR - skip this metric)

**Important:** 10% CTR is exceptional and requires incentives. Most email surveys get 2-5%.

**When to skip CTR (use 100%):**
- Intercept surveys (pop-ups in app/website)
- Survey embedded directly in product
- Survey displayed on device screen
- Any scenario where clicking an email/link is not required

**Unsure about your CTR?**
- Ask ResearchOps team
- Check past campaign analytics in your email platform
- Review previous survey performance data

**Why it matters:** CTR is often the BIGGEST bottleneck in survey recruitment. Improving CTR from 2% → 8% has 50x more impact than reducing drop-off.

**How to improve:**
- Better subject lines
- Personalization
- Send time optimization
- Clear value proposition
- Incentives

### Cluster Analysis
**Definition:** Statistical method used to group similar observations (exploratory segmentation).

See "Cluster Analysis" test type for sample size requirements.

### Cohen's d
**Definition:** Effect size measure for t-tests (difference between two means).

**Guidelines:**
- Small: 0.2 (subtle difference, e.g., 2 vs 2.2 on 10-point scale)
- Medium: 0.5 (moderate difference, e.g., 2 vs 3)
- Large: 0.8 (obvious difference, e.g., 2 vs 4)

**Rule of thumb:** If you expect subtle differences, use small effect sizes (requires larger samples). If you expect obvious differences, use large effect sizes (requires smaller samples).

### Cohen's f
**Definition:** Effect size measure for ANOVA (variance between groups).

**Guidelines:**
- Small: 0.10
- Medium: 0.25
- Large: 0.40

### Cohen's f²
**Definition:** Effect size measure for regression (variance explained by predictors).

**Guidelines:**
- Small: 0.02 (R² = 0.02, explains 2% of variance)
- Medium: 0.15 (R² = 0.13, explains 13% of variance)
- Large: 0.35 (R² = 0.26, explains 26% of variance)

### Completes
**Definition:** Number of people who finish your survey (complete responses).

This is your **usable sample size** for statistical analysis. Not everyone who starts will finish (see Drop-off Rate).

### Completion Rate
**Definition:** Percentage of people who FINISH your survey after starting.

**Formula:** Completion Rate = 100% - Drop-off Rate

**Example:** If 30% drop off, then 70% complete.

### Confirmatory Factor Analysis (CFA)
**Definition:** Statistical method used to test a pre-specified factor structure (hypothesis testing).

See "CFA" test type for sample size requirements.

---

## D

### Drop-off Rate
**Definition:** Percentage of people who START your survey but DON'T finish it.

**Formula:** Drop-off Rate = Incomplete ÷ Starts

**Typical Ranges:**
- Simple survey (<10 min, single-choice questions): 5-15%
- Standard survey (10-15 min, mixed questions): 15-25%
- Complex survey (loops, grids, 15-20 min): 25-40%
- Very complex (multiple loops, >20 min): 40-60%

**Completion Rate = 100% - Drop-off Rate**

**Example:** 30% drop-off = 70% completion (70% finish)

**Causes of high drop-off:**
- Survey too long
- Repetitive questions (loops)
- Complex grid questions
- Unclear instructions
- Technical issues
- No progress indicator

**How to reduce:**
- Remove unnecessary questions
- Reduce loop iterations (max 2-3)
- Simplify grid questions (<5 rows)
- Add skip logic
- Show progress bar
- Test on mobile

---

## E

### Effect Size
**Definition:** Magnitude of the difference or relationship you're trying to detect.

**Cohen's d** (for t-tests):
- Small: 0.2 (subtle difference, e.g., 2 vs 2.2 on 10-point scale)
- Medium: 0.5 (moderate difference, e.g., 2 vs 3)
- Large: 0.8 (obvious difference, e.g., 2 vs 4)

**Cohen's f** (for ANOVA):
- Small: 0.10
- Medium: 0.25
- Large: 0.40

**Cohen's f²** (for regression):
- Small: 0.02 (R² = 0.02, explains 2% of variance)
- Medium: 0.15 (R² = 0.13, explains 13% of variance)
- Large: 0.35 (R² = 0.26, explains 26% of variance)

**Rule of thumb:** If you expect subtle differences, use small effect sizes (requires larger samples). If you expect obvious differences, use large effect sizes (requires smaller samples).

### Exploratory Factor Analysis (EFA)
**Definition:** Statistical method used to identify underlying dimensions in your data (data reduction).

See "PCA/EFA" test type for sample size requirements.

---

## F

### Fatigue Score (DEPRECATED)
**Old approach:** Abstract 0-100 score from survey audit.

**New approach:** Use drop-off rate directly (more intuitive).

**Conversion:**
- Fatigue 0-25 → 5-15% drop-off
- Fatigue 26-50 → 15-25% drop-off
- Fatigue 51-75 → 25-40% drop-off
- Fatigue 76-100 → 40-60% drop-off

---

## I

### Invitations
**Definition:** Total number of survey invitations you need to send.

**Calculated from:** Invitations = Completes ÷ (CTR × Completion Rate)

**Example:**
- Need 200 completes
- CTR = 5% (engaged email)
- Completion rate = 70% (30% drop-off)
- Invitations = 200 ÷ (0.05 × 0.70) = 5,715

---

## L

### Latent Class Analysis (LCA)
**Definition:** Statistical method used to identify unobserved subgroups (classes) in your data.

See "LCA" test type for sample size requirements.

---

## M

### Minimum Segment Size
**Rule:** Each segment needs minimum 30 participants for reliable statistical inference.

**What the tool does:** Automatically scales up total sample if smallest segment falls below 30.

**Example:**
```
Power analysis says: 158 total needed
With 60%, 30%, 10% prevalence:
- Segment 1: 95 ✅
- Segment 2: 47 ✅
- Segment 3: 16 ❌ (below minimum)

Tool adjusts to: 296 total
- Segment 1: 178 ✅
- Segment 2: 89 ✅
- Segment 3: 30 ✅ (meets minimum)
```

---

## O

### Overall Conversion Rate
**Definition:** Percentage of invitations that result in completed surveys.

**Formula:** Conversion = CTR × Completion Rate

**Example:**
- CTR = 5%
- Completion = 70%
- Conversion = 0.05 × 0.70 = 3.5%
- Meaning: For every 100 invitations, 3.5 people complete

---

## P

### Power Analysis
**Statistical power analysis** determines the sample size needed to detect an effect of a given size with a specified level of confidence.

### Prevalence
**Definition:** Percentage of the population in each segment.

**Must sum to 100%**

**Example:** 3 segments with 40%, 40%, 20% prevalence
- Segment 1: 40% of people
- Segment 2: 40% of people
- Segment 3: 20% of people
- Total: 100%

**Why it matters:** Smaller segments need proportionally more total sample to ensure minimum 30 participants per segment.

### Principal Component Analysis (PCA)
**Definition:** Statistical method used to identify underlying dimensions in your data (data reduction).

See "PCA/EFA" test type for sample size requirements.

---

## R

### Response Rate
**Definition:** Percentage of people who START your survey after clicking the link.

**Formula:** Response Rate = Starts ÷ Clicks

**Typical Value:** ~100% (most people who click will start)

**Note:** This is different from CTR. Response rate happens AFTER the click.

---

## S

### Sample Size
**Definition:** Number of participants needed in your study.

- **Total n:** Overall sample across all groups
- **n per group:** Sample in each condition (for t-tests, ANOVA)

**Example:** Independent t-test with n=64 per group means 128 total participants.

### Segment
**Definition:** Pre-defined group within your population (e.g., user persona, customer type, cluster).

**Important:** Segments must be defined BEFORE analysis, not discovered during analysis.

**Sources:**
- Latent Class Analysis (LCA)
- Cluster analysis (k-means, hierarchical)
- Theoretical segmentation (personas)
- Behavioral segments

### Statistical Power
**Definition:** Probability of detecting a real effect when it exists (1 - β, where β = Type II error).

**Standard:** 0.80 (80%)
- Meaning: 80% chance of finding the effect if it's really there
- Higher power (0.90, 0.95) = more confidence but requires larger samples

**Trade-off:** More power requires more participants.

---

## T

### Tests

#### Chi-Square Test
**Use for:** Testing association between categorical variables.

**Example:** Is there a relationship between customer type (3 categories) and satisfaction level (5 categories)?

**Parameters:**
- Effect size: Cramer's V / w
- Contingency table dimensions
- Minimum expected cell count

#### Confirmatory Factor Analysis (CFA)
**Use for:** Testing a pre-specified factor structure (hypothesis testing).

**Example:** Confirm that satisfaction, quality, and value are distinct factors.

**Requirements:**
- Minimum 200 participants
- 10-20 observations per estimated parameter

#### Correlation / Simple Regression
**Use for:** Measuring relationship between two continuous variables.

**Example:** Correlation between customer satisfaction and loyalty score.

**Parameters:**
- Effect size: r, R², or f²
- Mathematically equivalent for power analysis

#### Independent t-test
**Use for:** Comparing means between two independent groups.

**Example:** Do users prefer Design A or Design B?

**Parameters:**
- Effect size: Cohen's d
- Two groups
- Independent observations (different people in each group)

#### Latent Class Analysis (LCA)
**Use for:** Identifying unobserved subgroups (classes) in your data.

**Example:** Discover user types based on behavioral patterns.

**Requirements:**
- Minimum 500 participants
- 50+ participants in smallest class

#### Multiple Regression
**Use for:** Predicting an outcome from multiple predictors.

**Example:** What predicts customer satisfaction? (predictors: price, quality, support)

**Parameters:**
- Effect size: f² or R²
- Number of predictors
- Rule: 10-20 observations per predictor

#### One-Way ANOVA
**Use for:** Comparing means across 3+ groups.

**Example:** Do satisfaction scores differ across 4 pricing tiers?

**Parameters:**
- Effect size: Cohen's f
- 3 or more groups
- Independent observations

#### Paired t-test
**Use for:** Comparing means for the same people at two time points.

**Example:** Does training improve test scores? (same people, before vs. after)

**Parameters:**
- Effect size: Cohen's d
- Two measurements per person
- Dependent observations (same people measured twice)

#### PCA / EFA
**Use for:** Discovering underlying dimensions in your data (data reduction).

**Example:** Reduce 20 survey items to 3-5 underlying factors.

**Requirements:**
- Rule of thumb: 10-20 participants per item
- Minimum 100 participants regardless of items

#### Segment Analysis
**Use for:** Comparing outcomes across pre-defined segments.

**Example:** Do NPS scores differ across 3 user personas (40%, 40%, 20% prevalence)?

**Requirements:**
- Segments defined before analysis (e.g., from LCA, cluster analysis, personas)
- Prevalence (% in each segment) must be specified
- Minimum 30 participants per segment for reliable inference

**Parameters:**
- Effect size: Cohen's f
- Number of segments
- Segment prevalence (must sum to 100%)

---

## Survey Funnel Stages

### 1. Invitations Sent
Total emails/messages/notifications sent to potential respondents.

### 2. Clicks
Number of people who click your survey link (CTR applied).

### 3. Starts
Number of people who begin taking the survey (usually ~same as clicks).

### 4. Completes
Number of people who finish the survey (completion rate applied).

### Full Funnel Example:
```
10,000 invitations sent
   ↓ 5% CTR
500 clicks
   ↓ ~100% start
500 starts
   ↓ 70% complete (30% drop-off)
350 completes
```

**Overall: 350 ÷ 10,000 = 3.5% conversion**

---

## Common Misconceptions

### "I need 200 responses, so I'll send 200 invitations"
**Wrong!** You need to account for:
1. CTR (only 5-10% will click)
2. Drop-off (only 70-85% will complete)

**Correct:** Send 2,000-5,000 invitations (depending on CTR).

### "Power analysis tells me how many invitations to send"
**Not quite!** Power analysis tells you how many **completes** you need. Then you calculate invitations based on CTR and drop-off.

### "Improving survey length is most important"
**Not always!** CTR often has 50x more impact than drop-off. Focus on improving CTR first (better subject lines, targeting, incentives).

### "I can use any effect size"
**Be realistic!** Using large effect sizes (easy to detect) when your real effect is small will leave you underpowered. When in doubt, be conservative (use small/medium).

### "80% power is perfect"
**It's standard, not perfect!** 80% power means 20% chance of missing a real effect. For critical decisions, consider 90% power (requires larger sample).

---

## Quick Reference

| Term | Quick Definition | Typical Value |
|------|------------------|---------------|
| Power | Chance of detecting real effect | 80% |
| Alpha | Chance of false positive | 5% |
| Effect Size (d) | Magnitude of difference | 0.2-0.8 |
| CTR | % who click link | 1-10% |
| Drop-off | % who start but don't finish | 15-40% |
| Completion | % who finish after start | 60-85% |
| Completes | Finished surveys (usable data) | From power analysis |
| Invitations | Total sent | Completes ÷ (CTR × Completion) |

---

## Examples

### Example 1: Email Survey (Engaged List)
```
Goal: Test two designs (t-test)
Effect size: Medium (d=0.5)
Power: 80%
→ Need 128 completes (64 per group)

Survey:
Drop-off: 25% (75% complete)
CTR: 8% (engaged email list)

Invitations needed:
128 ÷ (0.08 × 0.75) = 2,134 emails

Funnel:
2,134 emails → 171 clicks → 171 starts → 128 completes
Overall conversion: 6%
```

### Example 2: In-App Survey
```
Goal: Segment comparison (3 groups: 50%, 30%, 20%)
Effect size: Medium (f=0.25)
Power: 80%
→ Need 210 completes

Survey:
Drop-off: 20% (80% complete)
CTR: 100% (in-app, direct access)

Invitations needed:
210 ÷ (1.0 × 0.80) = 263 invitations

Funnel:
263 invitations → 263 starts → 210 completes
Overall conversion: 80%
```

---

**Last Updated:** 2026-05-23
