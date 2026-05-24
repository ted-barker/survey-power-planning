# Changelog - Survey & Statistical Power Planning Tool

## [v3.1.0] - 2026-05-24

### Added - Expanded Statistical Test Coverage

#### New Test Types (6 additional tests)
1. **Non-Parametric: Mann-Whitney U Test**
   - Rank-based alternative to independent t-test
   - 95.5% efficient vs parametric equivalent
   - Use when: ordinal data, skewed distributions, violated assumptions

2. **Non-Parametric: Wilcoxon Signed-Rank Test**
   - Rank-based alternative to paired t-test
   - 95.5% efficient vs parametric equivalent
   - Use for: paired/matched observations with non-normal data

3. **Non-Parametric: Kruskal-Wallis H Test**
   - Rank-based alternative to one-way ANOVA
   - 95.5% efficient vs parametric equivalent
   - Compare 3+ groups when assumptions violated

4. **Non-Parametric: Friedman Test**
   - Rank-based alternative to repeated measures ANOVA
   - 95.5% efficient vs parametric equivalent
   - Repeated measures with non-normal data

5. **Logistic Regression (Binary)**
   - Predict yes/no outcomes
   - Uses Events Per Variable (EPV) rule (15 EPV)
   - Adjusts for effect size (small effects need 50% more sample)

6. **Ordinal Regression**
   - Predict ordered categories (e.g., Likert scales)
   - Category adjustment multiplier based on number of levels
   - Handles ordered outcome data efficiently

7. **Multinomial Regression**
   - Predict unordered categories (3+ choices)
   - (k-1) comparisons multiplier for multiple categories
   - Higher sample requirements than binary/ordinal

#### New Calculator Modules
- **`src/power/calculators/nonparametric.py`** (346 lines)
  - `NonParametricPowerCalc` class with 4 test types
  - Asymptotic Relative Efficiency (ARE) adjustments
  - Supports solve_for='n', 'power', or 'effect_size'
  - Effect size guidelines for rank-based tests

- **`src/power/calculators/logistic.py`** (256 lines)
  - `LogisticPowerCalc` class with 3 test types
  - Events Per Variable (EPV) rule implementation
  - Category multipliers for ordinal/multinomial
  - Power estimation for existing sample sizes

#### Dashboard Integration (app.py updates)
- Updated test selection dropdown (14 total tests now)
- Individual implementations for each non-parametric test
- Proper calculator instantiation and parameter passing
- Effect size guidelines and usage notes for each test
- Power check workflows (solve for n or power)

### Changed

#### Updated Documentation
- **README.md**: Updated test count (8 → 14 tests)
- **README.md**: Added Non-Parametric section with 4 tests
- **README.md**: Added Regression section with logistic variants
- **CHANGELOG.md**: Created comprehensive changelog (this file)

#### Test Descriptions
Updated `test_descriptions` dict in app.py to include:
- Mann-Whitney U → "Compare 2 groups using ranks"
- Wilcoxon → "Compare paired observations using ranks"
- Kruskal-Wallis → "Compare 3+ groups using ranks"
- Friedman → "Compare repeated measures using ranks"

### Technical Details

#### Non-Parametric Implementation
```python
# Asymptotic Relative Efficiency (ARE)
ARE = {
    'mann_whitney': 0.955,  # 95.5% efficient vs t-test
    'wilcoxon': 0.955,      # 95.5% efficient vs paired t-test
    'kruskal_wallis': 0.955,  # 95.5% efficient vs ANOVA
    'friedman': 0.955       # 95.5% efficient vs repeated ANOVA
}

# Sample size calculation:
n_parametric = calculate_parametric_n(effect_size, alpha, power)
n_nonparametric = int(np.ceil(n_parametric / ARE[test_type]))
```

#### Logistic Regression Implementation
```python
# Binary: 15 events per predictor (EPV)
required_n = 2 * (15 * n_predictors)

# Ordinal: Category multiplier
category_multiplier = 1 + (n_categories - 2) * 0.1
required_n = int(base_n * category_multiplier)

# Multinomial: (k-1) comparisons
category_multiplier = (n_categories - 1) * 0.4
required_n = int(base_n * (1 + category_multiplier))
```

### Compatibility
- No breaking changes
- Backwards compatible with existing code
- All previous test types (t-test, ANOVA, regression, etc.) unchanged

### Testing
All calculators tested independently:
- ✅ NonParametricPowerCalc: 4 test types working
- ✅ LogisticPowerCalc: 3 test types working
- ✅ App module imports successfully
- ✅ No syntax errors or import failures

### Summary Statistics

**Total Test Types Supported:** 14
- Parametric: 5 (t-test × 2, ANOVA, regression, correlation)
- Non-Parametric: 4 (Mann-Whitney, Wilcoxon, Kruskal-Wallis, Friedman)
- Logistic: 3 (binary, ordinal, multinomial)
- Proportions: 2 (chi-square, proportions)
- Advanced: 1 (segment analysis)

**Code Added:**
- 346 lines: nonparametric.py
- 256 lines: logistic.py
- ~200 lines: app.py integrations
- **Total:** ~800 new lines of functional code

### Future Work (Not Yet Implemented)
- Cluster Analysis (heuristic-based)
- Latent Class Analysis (LCA)
- PCA/EFA (heuristic-based)
- CFA (heuristic-based)

---

## [v3.0.0] - 2026-05-23

### Added - Initial Power Planning Tool
- Single-page dashboard with three-column layout
- Survey Sample → Statistical Power → Final Estimate
- 8 core statistical tests
- Visual equation showing multiplicative relationship
- Quick preset buttons for effect sizes
- Custom CSS theming (muted teal, Inter font)
- Plotly visualizations

### Changed
- Terminology: "completes" → "sample" throughout application
- Removed all emojis from user interface
- Simplified language and workflow descriptions

---

## Version History Summary

- **v3.1.0** (2026-05-24): Expanded test coverage (+6 tests, 14 total)
- **v3.0.0** (2026-05-23): Initial power planning tool release
- **v2.x**: Survey fatigue audit functionality (separate tool)
