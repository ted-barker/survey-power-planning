# Survey & Statistical Power Planning

**Interactive dashboard for calculating statistical power requirements and survey sample size planning.**

Single-page application showing mathematical relationships between survey efficiency and statistical power.

---

## Features

- 📊 **Statistical Power Calculators** - 8 test types (t-test, ANOVA, regression, correlation, chi-square, proportions, segment analysis)
- 🔢 **Survey Sample Planning** - CTR and drop-off rate calculations
- 🧮 **Visual Mathematics** - Equation showing how components multiply together
- ⚡ **Real-Time Calculation** - Three-column layout with instant updates
- 🎛️ **Quick Presets** - Small/Medium/Large effect size buttons
- 🎨 **Professional UI** - Clean design with Plotly visualizations

---

## Quick Start

### 1. Install

```bash
# Clone repository
git clone https://github.com/ted-barker/survey-power-planning.git
cd survey-power-planning

# Install dependencies
pip install -r requirements.txt
```

### 2. Launch Dashboard

```bash
streamlit run app.py
```

The dashboard will open in your browser at `http://localhost:8501`

---

## How It Works

The dashboard calculates how many survey invitations you need to send based on:

### Three Components

**1. Survey Sample (Column 1)**
- CTR (Click-Through Rate): % who click your invitation link
- Drop-off Rate: % who start but don't finish
- Calculates overall conversion rate

**2. Statistical Power (Column 2)**
- Select test type (t-test, ANOVA, regression, etc.)
- Choose effect size (Small/Medium/Large)
- Set desired power (typically 80%)
- Calculates required sample size

**3. Final Estimate (Column 3)**
- Shows total invitations needed
- Displays expected sample size
- Shows conversion rate

### The Math

```
CTR Multiplier × Drop-off Multiplier × Statistical Requirement = Total Invitations
```

**Example:**
- CTR: 5% (×20 multiplier)
- Drop-off: 30% (×1.43 multiplier)
- Statistical requirement: 128 participants
- **Result: 128 × 20 × 1.43 = 3,657 invitations**

---

## Statistical Tests Supported

### Comparing Means
- **Independent t-test** - Compare 2 groups
- **Paired t-test** - Before/after within same people
- **ANOVA** - Compare 3+ groups

### Regression & Correlation
- **Multiple Regression** - Predict from multiple variables
- **Correlation** - Relationship between 2 variables

### Proportions
- **Chi-Square** - Association between categories
- **Proportions** - Compare percentages

### Advanced
- **Segment Analysis** - Compare pre-defined segments (e.g., personas) with known prevalence

---

## Usage Examples

### Example 1: A/B Test Planning

**Scenario:** Test two design variants

```
Survey Sample:
- CTR: 5% (email with incentive)
- Drop-off: 25% (standard survey)
- Conversion: 3.75%

Statistical Power:
- Test: Independent t-test
- Effect: Medium (0.5)
- Power: 80%
- Required: 128 participants

Final Estimate:
- Send 3,413 invitations
- Expect 128 completions
```

### Example 2: Segment Comparison

**Scenario:** Compare 3 user personas (40%/40%/20% split)

```
Survey Sample:
- CTR: 8% (in-app survey)
- Drop-off: 20% (short survey)
- Conversion: 6.4%

Statistical Power:
- Test: Segment Analysis
- 3 segments: 40%, 40%, 20%
- Effect: Medium (0.25)
- Power: 80%
- Required: 159 participants

Final Estimate:
- Send 2,484 invitations
- Expect 159 completions (64/64/32 per segment)
```

### Example 3: Regression Study

**Scenario:** Predict satisfaction from 5 factors

```
Survey Sample:
- CTR: 3% (cold email list)
- Drop-off: 35% (complex survey)
- Conversion: 1.95%

Statistical Power:
- Test: Multiple Regression
- Predictors: 5
- Effect: Medium (0.15)
- Power: 80%
- Required: 92 participants

Final Estimate:
- Send 4,718 invitations
- Expect 92 completions
```

---

## Understanding the Results

### CTR (Click-Through Rate)

**Typical ranges:**
- No incentive: ~1%
- Standard email: 2-5%
- With incentive: 5-10%
- In-app/intercept: 100% (no email link)

**Impact:** Low CTR has the biggest multiplier effect. Improving CTR from 2% to 5% cuts invitations needed by 60%.

### Drop-off Rate

**Typical ranges:**
- Simple survey (<10 min): 15-20%
- Standard survey (10-15 min): 20-30%
- Complex survey (>15 min): 30-40%

**Impact:** High drop-off compounds with low CTR. Both together create the overall conversion penalty.

### Effect Size

**What it means:**
- **Small (0.2)**: Subtle difference, hard to detect, needs large sample
- **Medium (0.5)**: Moderate difference, typical in research
- **Large (0.8)**: Obvious difference, easier to detect, needs smaller sample

**Be realistic:** Using "large" when your real effect is "small" leaves you underpowered.

---

## Visual Equation Explained

The dashboard shows:

```
×20 (CTR) × ×1.43 (Drop-off) × 128 (Statistical) = 3,657 (Total)
```

**Reading this:**
1. **×20 from CTR**: Only 5% click, so you need 20× more invitations than starters
2. **×1.43 from Drop-off**: Only 70% complete, so you need 1.43× more starters than completions
3. **128 from Statistical Power**: Your test needs 128 completed responses
4. **= 3,657 Total**: Multiply all three together

**The key insight:** Survey inefficiency (CTR and drop-off) amplifies your statistical requirement.

---

## Project Structure

```
survey-power-planning/
├── app.py                              # Main Streamlit dashboard
├── src/power/
│   ├── calculators/
│   │   ├── means.py                   # t-tests, ANOVA
│   │   ├── regression.py              # Regression, correlation
│   │   ├── proportions.py             # Chi-square, proportions
│   │   └── segments.py                # Segment analysis
│   ├── visualizations/
│   │   ├── power_curves.py            # Power vs sample plots
│   │   └── sensitivity.py             # Sensitivity analysis
│   ├── integrations/
│   │   ├── dropoff.py                 # Survey funnel calculations
│   │   └── optimizer.py               # Optimization suggestions
│   └── agent.py                        # Conversational interface
├── notebooks/
│   ├── 00-power-planning.ipynb        # Tutorial notebook
│   └── 04-optimize-design.ipynb       # Integrated workflow
├── tests/power/                        # Unit tests
├── docs/                               # Additional documentation
└── requirements.txt
```

---

## Requirements

- Python 3.8+
- streamlit
- numpy
- pandas
- scipy
- statsmodels
- pingouin
- plotly

All dependencies listed in `requirements.txt`

---

## Optional: Use Jupyter Notebooks

Alternative to the dashboard - use notebooks for analysis:

```bash
jupyter notebook
```

Open `notebooks/00-power-planning.ipynb` for interactive examples.

---

## Contributing

Contributions welcome! Areas for improvement:

- Additional statistical tests (SEM, multilevel models, etc.)
- More visualization options
- Export functionality (PDF reports)
- Integration with survey platforms

---

## License

MIT License

---

## Citation

If you use this tool in research:

```bibtex
@software{survey_power_planning,
  title = {Survey & Statistical Power Planning Tool},
  author = {Barker, Ted},
  year = {2026},
  url = {https://github.com/ted-barker/survey-power-planning}
}
```

---

## Contact

Questions or feedback? Open an issue on GitHub.
