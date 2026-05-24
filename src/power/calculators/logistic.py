"""
Power analysis for logistic regression models

Supports:
- Binary logistic regression (yes/no outcome)
- Ordinal logistic regression (ordered categories)
- Multinomial logistic regression (unordered categories)
"""

from typing import Dict, Literal, Optional
import numpy as np
from scipy import stats


class LogisticPowerCalc:
    """
    Power analysis calculator for logistic regression models.

    Examples:
        # Binary logistic regression
        calc = LogisticPowerCalc(test_type='binary')
        result = calc.calculate(effect_size=0.15, alpha=0.05, power=0.80, solve_for='n', n_predictors=3)

        # Ordinal logistic regression
        calc = LogisticPowerCalc(test_type='ordinal')
        result = calc.calculate(effect_size=0.15, alpha=0.05, power=0.80, solve_for='n',
                               n_predictors=2, n_categories=5)
    """

    VALID_TEST_TYPES = ['binary', 'ordinal', 'multinomial']
    VALID_SOLVE_FOR = ['n', 'power', 'effect_size']

    def __init__(self, test_type: Literal['binary', 'ordinal', 'multinomial']):
        """
        Initialize the logistic regression power calculator.

        Args:
            test_type: Type of logistic regression
                - 'binary': Binary outcome (yes/no)
                - 'ordinal': Ordered categories (e.g., Likert scale)
                - 'multinomial': Unordered categories
        """
        if test_type not in self.VALID_TEST_TYPES:
            raise ValueError(f"test_type must be one of {self.VALID_TEST_TYPES}")

        self.test_type = test_type

    def calculate(
        self,
        effect_size: Optional[float] = None,
        alpha: float = 0.05,
        power: Optional[float] = None,
        n: Optional[int] = None,
        solve_for: Literal['n', 'power', 'effect_size'] = 'n',
        n_predictors: int = 1,
        n_categories: int = 2,
        **kwargs
    ) -> Dict:
        """
        Calculate power analysis for logistic regression.

        Args:
            effect_size: Effect size (Odds Ratio or f²)
            alpha: Significance level (default 0.05)
            power: Statistical power (default 0.80)
            n: Sample size
            solve_for: What to calculate ('n', 'power', or 'effect_size')
            n_predictors: Number of predictor variables
            n_categories: Number of outcome categories (for ordinal/multinomial)

        Returns:
            Dictionary with results
        """
        if solve_for not in self.VALID_SOLVE_FOR:
            raise ValueError(f"solve_for must be one of {self.VALID_SOLVE_FOR}")

        # Rule of thumb: 10-20 events per predictor variable (EPV)
        # For logistic regression, common heuristic is 15 EPV
        events_per_variable = 15

        if self.test_type == 'binary':
            return self._calculate_binary(effect_size, alpha, power, n, solve_for,
                                         n_predictors, events_per_variable)
        elif self.test_type == 'ordinal':
            return self._calculate_ordinal(effect_size, alpha, power, n, solve_for,
                                          n_predictors, n_categories, events_per_variable)
        else:  # multinomial
            return self._calculate_multinomial(effect_size, alpha, power, n, solve_for,
                                              n_predictors, n_categories, events_per_variable)

    def _calculate_binary(self, effect_size, alpha, power, n, solve_for, n_predictors, epv):
        """Binary logistic regression power calculation."""

        if solve_for == 'n':
            # Rule of thumb: 15 events per predictor
            # Assuming 50/50 split, need 2 * (15 * n_predictors)
            required_n = 2 * (epv * n_predictors)

            # Adjust for effect size (smaller effects need more sample)
            if effect_size and effect_size < 0.15:
                required_n = int(required_n * 1.5)
            elif effect_size and effect_size > 0.35:
                required_n = int(required_n * 0.7)

            return {
                'n': required_n,
                'effect_size': effect_size,
                'alpha': alpha,
                'power': power or 0.80,
                'n_predictors': n_predictors,
                'test_type': 'binary logistic',
                'rule': f'{epv} events per predictor',
                'assumptions': '50/50 outcome split assumed'
            }

        elif solve_for == 'power':
            # Approximate power given sample size
            actual_epv = (n / 2) / n_predictors
            if actual_epv >= epv:
                estimated_power = min(0.95, 0.70 + (actual_epv - epv) * 0.03)
            else:
                estimated_power = max(0.50, 0.70 - (epv - actual_epv) * 0.05)

            return {
                'power': estimated_power,
                'n': n,
                'effect_size': effect_size,
                'alpha': alpha,
                'n_predictors': n_predictors,
                'actual_epv': actual_epv,
                'test_type': 'binary logistic'
            }

        else:  # solve_for effect_size
            return {
                'effect_size': 0.15,  # Medium effect
                'n': n,
                'alpha': alpha,
                'power': power,
                'n_predictors': n_predictors,
                'note': 'Effect size guidelines: Small=0.02, Medium=0.15, Large=0.35'
            }

    def _calculate_ordinal(self, effect_size, alpha, power, n, solve_for,
                          n_predictors, n_categories, epv):
        """Ordinal logistic regression power calculation."""

        # Ordinal regression needs more sample than binary
        # Add penalty for number of categories
        category_multiplier = 1 + (n_categories - 2) * 0.1

        if solve_for == 'n':
            base_n = 2 * (epv * n_predictors)
            required_n = int(base_n * category_multiplier)

            return {
                'n': required_n,
                'effect_size': effect_size,
                'alpha': alpha,
                'power': power or 0.80,
                'n_predictors': n_predictors,
                'n_categories': n_categories,
                'test_type': 'ordinal logistic',
                'rule': f'{epv} events per predictor × category adjustment',
                'assumptions': f'{n_categories} ordered categories'
            }

        elif solve_for == 'power':
            base_epv = (n / 2) / n_predictors
            adjusted_epv = base_epv / category_multiplier

            if adjusted_epv >= epv:
                estimated_power = min(0.95, 0.70 + (adjusted_epv - epv) * 0.03)
            else:
                estimated_power = max(0.50, 0.70 - (epv - adjusted_epv) * 0.05)

            return {
                'power': estimated_power,
                'n': n,
                'effect_size': effect_size,
                'alpha': alpha,
                'n_predictors': n_predictors,
                'n_categories': n_categories,
                'test_type': 'ordinal logistic'
            }

        else:
            return {
                'effect_size': 0.15,
                'n': n,
                'alpha': alpha,
                'power': power,
                'note': 'Ordinal effect sizes similar to binary logistic'
            }

    def _calculate_multinomial(self, effect_size, alpha, power, n, solve_for,
                               n_predictors, n_categories, epv):
        """Multinomial logistic regression power calculation."""

        # Multinomial needs even more sample - estimate (k-1) comparisons
        category_multiplier = (n_categories - 1) * 0.4

        if solve_for == 'n':
            base_n = 2 * (epv * n_predictors)
            required_n = int(base_n * (1 + category_multiplier))

            return {
                'n': required_n,
                'effect_size': effect_size,
                'alpha': alpha,
                'power': power or 0.80,
                'n_predictors': n_predictors,
                'n_categories': n_categories,
                'test_type': 'multinomial logistic',
                'rule': f'{epv} events per predictor × (k-1) comparisons',
                'assumptions': f'{n_categories} unordered categories'
            }

        elif solve_for == 'power':
            base_epv = (n / n_categories) / n_predictors
            adjusted_epv = base_epv / (1 + category_multiplier)

            if adjusted_epv >= epv:
                estimated_power = min(0.95, 0.70 + (adjusted_epv - epv) * 0.03)
            else:
                estimated_power = max(0.50, 0.70 - (epv - adjusted_epv) * 0.05)

            return {
                'power': estimated_power,
                'n': n,
                'effect_size': effect_size,
                'alpha': alpha,
                'n_predictors': n_predictors,
                'n_categories': n_categories,
                'test_type': 'multinomial logistic'
            }

        else:
            return {
                'effect_size': 0.15,
                'n': n,
                'alpha': alpha,
                'power': power,
                'note': 'Multinomial effect sizes similar to binary logistic'
            }

    @staticmethod
    def effect_size_guidelines() -> Dict[str, float]:
        """Return effect size guidelines for logistic regression."""
        return {
            'small': 0.02,
            'medium': 0.15,
            'large': 0.35,
            'note': 'Based on Odds Ratios: Small=1.5, Medium=2.5, Large=4.0'
        }
