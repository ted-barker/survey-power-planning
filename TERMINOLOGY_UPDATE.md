# Terminology Update: "Completes" → "Sample"

## Date: 2026-05-23

---

## Rationale

"Completes" is jargon specific to survey research that confuses general audiences.

**Problem:** Users don't understand "completes" vs "invitations" vs "sample size"

**Solution:** Use "sample" or "sample size" consistently throughout the interface

---

## Changes Made

### Global Replacements:

1. **"completes needed"** → **"sample size needed"**
2. **"required completes"** → **"required sample size"**
3. **"Expected completes"** → **"Expected sample"**
4. **"completes you'll get"** → **"sample you'll get"**
5. **"How many completes"** → **"How many participants"**
6. **"survey completes"** → **"sample size"**
7. **"X completes"** → **"X sample"** (in results)

### Variable Names:
- `required_completes` → `required_sample`
- `default_completes` → `default_sample`
- `completes` (variable) → `sample`

### Files Updated:
- ✅ `app.py` (49 instances)
- ✅ `src/power/agent.py` (18 instances)
- ⏸️ `docs/GLOSSARY.md` (kept as terminology definition)

---

## Before/After Examples

### Statistical Power Tab

**Before:**
> Calculate how many survey completes you need for your statistical analysis

**After:**
> Calculate the sample size needed to obtain adequate power for your statistical tests.

### Results Display

**Before:**
> Required Completes: 200 completes

**After:**
> Required Sample Size: 200 sample

### Survey Sample Size

**Before:**
> Required completes (from power analysis)

**After:**
> Required sample size (from power analysis)

### Agent Workflow

**Before:**
> Calculate: completes needed → invitations to send

**After:**
> Calculate: sample size needed → invitations to send

**Before:**
> Calculate: completes I'll get → what tests are feasible

**After:**
> Calculate: sample I'll get → what tests are feasible

---

## Exceptions (Kept "Completes")

### Glossary Definition
Kept "Completes" as a defined term in the glossary since it's teaching survey terminology:

```markdown
### Completes
**Definition:** Number of people who finish your survey (complete responses).

This is your **usable sample size** for statistical analysis.
```

This is appropriate because the glossary explains technical terms.

---

## User-Facing Language Now Uses:

1. **"Sample"** or **"Sample size"** - For the number of participants needed
2. **"Participants"** - For people in the study
3. **"Invitations"** - For emails/messages sent
4. **"Expected sample"** - For funnel calculations

---

## Consistency Check

All user-facing text now consistently uses:
- ✅ "Sample size" (not "completes")
- ✅ "Participants" (not "completes")
- ✅ "Sample" in metrics and results
- ✅ "Sample you'll get" in workflows

---

**Status:** ✅ Complete
**Impact:** Clearer, more accessible language for all users
