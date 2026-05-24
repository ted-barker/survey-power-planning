"""
Power analysis for means-based tests (t-tests, ANOVA)

Supports:
- Independent samples t-test
- Paired samples t-test
- One-way ANOVA
- Repeated measures ANOVA
"""

from typing import Dict, Literal, Optional, Union
import numpy as np
from scipy import stats
from statsmodels.stats.power import (
    TTestIndPower,
    TTestPower,
    FTestAnovaPower,
    FTestPower,
)


class MeansPowerCalc:
    """
    Power analysis calculator for means-based statistical tests.

    Examples:
        # Independent t-test
        calc = MeansPowerCalc(test_type='independent')
        result = calc.calculate(effect_size=0.5, alpha=0.05, power=0.80, solve_for='n')

        # One-way ANOVA
        calc = MeansPowerCalc(test_type='anova')
        result = calc.calculate(effect_size=0.25, alpha=0.05, power=0.80,
                               solve_for='n', n_groups=3)
    """

    VALID_TEST_TYPES = ['independent', 'paired', 'anova', 'repeated_anova']
    VALID_SOLVE_FOR = ['n', 'power', 'effect_size']

    def __init__(self, test_type: Literal['independent', 'paired', 'anova', 'repeated_anova']):
        """
        Initialize the means power calculator.

        Args:
            test_type: Type of test
                - 'independent': Independent samples t-test
                - 'paired': Paired samples t-test
                - 'anova': One-way ANOVA
                - 'repeated_anova': Repeated measures ANOVA
        """
        if test_type not in self.VALID_TEST_TYPES:
            raise ValueError(f"test_type must be one of {self.VALID_TEST_TYPES}")

        self.test_type = test_type

        # Initialize appropriate power analysis object
        if test_type == 'independent':
            self.power_obj = TTestIndPower()
        elif test_type == 'paired':
            self.power_obj = TTestPower()
        elif test_type in ['anova', 'repeated_anova']:
            self.power_obj = FTestAnovaPower()
        else:
            raise ValueError(f"Unknown test_type: {test_type}")

    def calculate(
        self,
        effect_size: Optional[float] = None,
        alpha: float = 0.05,
        power: Optional[float] = None,
        n: Optional[int] = None,
        solve_for: Literal['n', 'power', 'effect_size'] = 'n',
        alternative: Literal['two-sided', 'larger', 'smaller'] = 'two-sided',
        n_groups: Optional[int] = None,
        ratio: float = 1.0,
    ) -> Dict[str, Union[int, float, str]]:
        """
        Calculate sample size, power, or effect size.

        Args:
            effect_size: Effect size (Cohen's d for t-tests, Cohen's f for ANOVA)
            alpha: Significance level (default: 0.05)
            power: Statistical power (default: 0.80)
            n: Sample size (per group for independent t-test, total for paired/ANOVA)
            solve_for: What to solve for ('n', 'power', or 'effect_size')
            alternative: Type of test ('two-sided', 'larger', 'smaller')
            n_groups: Number of groups (required for ANOVA)
            ratio: Ratio of sample sizes between groups (default: 1.0 for equal groups)

        Returns:
            Dictionary with calculation results and metadata

        Raises:
            ValueError: If required parameters are missing or invalid
        """
        if solve_for not in self.VALID_SOLVE_FOR:
            raise ValueError(f"solve_for must be one of {self.VALID_SOLVE_FOR}")

        # Validate required parameters based on what we're solving for
        if solve_for == 'n':
            if effect_size is None or power is None:
                raise ValueError("effect_size and power required when solving for n")
        elif solve_for == 'power':
            if effect_size is None or n is None:
                raise ValueError("effect_size and n required when solving for power")
        elif solve_for == 'effect_size':
            if power is None or n is None:
                raise ValueError("power and n required when solving for effect_size")

        # ANOVA-specific validation
        if self.test_type in ['anova', 'repeated_anova']:
            if n_groups is None:
                raise ValueError("n_groups required for ANOVA")
            if n_groups < 2:
                raise ValueError("n_groups must be at least 2")

        # Perform calculation
        result = self._solve(
            effect_size=effect_size,
            alpha=alpha,
            power=power,
            n=n,
            solve_for=solve_for,
            alternative=alternative,
            n_groups=n_groups,
            ratio=ratio,
        )

        return result

    def _solve(
        self,
        effect_size: Optional[float],
        alpha: float,
        power: Optional[float],
        n: Optional[int],
        solve_for: str,
        alternative: str,
        n_groups: Optional[int],
        ratio: float,
    ) -> Dict[str, Union[int, float, str]]:
        """Internal method to perform the actual calculation."""

        if self.test_type == 'independent':
            return self._solve_independent_ttest(
                effect_size, alpha, power, n, solve_for, alternative, ratio
            )
        elif self.test_type == 'paired':
            return self._solve_paired_ttest(
                effect_size, alpha, power, n, solve_for, alternative
            )
        elif self.test_type in ['anova', 'repeated_anova']:
            return self._solve_anova(
                effect_size, alpha, power, n, solve_for, n_groups
            )
        else:
            raise ValueError(f"Unknown test_type: {self.test_type}")

    def _solve_independent_ttest(
        self,
        effect_size: Optional[float],
        alpha: float,
        power: Optional[float],
        n: Optional[int],
        solve_for: str,
        alternative: str,
        ratio: float,
    ) -> Dict[str, Union[int, float, str]]:
        """Solve for independent samples t-test."""

        if solve_for == 'n':
            n_per_group = self.power_obj.solve_power(
                effect_size=effect_size,
                alpha=alpha,
                power=power,
                ratio=ratio,
                alternative=alternative,
            )
            n_per_group = int(np.ceil(n_per_group))

            return {
                'test_type': 'independent_ttest',
                'solve_for': 'n',
                'n_per_group': n_per_group,
                'total_n': n_per_group * 2 if ratio == 1.0 else int(n_per_group * (1 + ratio)),
                'effect_size': effect_size,
                'alpha': alpha,
                'power': power,
                'alternative': alternative,
                'ratio': ratio,
            }

        elif solve_for == 'power':
            calculated_power = self.power_obj.solve_power(
                effect_size=effect_size,
                nobs1=n,
                alpha=alpha,
                ratio=ratio,
                alternative=alternative,
            )

            return {
                'test_type': 'independent_ttest',
                'solve_for': 'power',
                'power': float(calculated_power),
                'n_per_group': n,
                'total_n': n * 2 if ratio == 1.0 else int(n * (1 + ratio)),
                'effect_size': effect_size,
                'alpha': alpha,
                'alternative': alternative,
                'ratio': ratio,
            }

        elif solve_for == 'effect_size':
            calculated_es = self.power_obj.solve_power(
                nobs1=n,
                alpha=alpha,
                power=power,
                ratio=ratio,
                alternative=alternative,
            )

            return {
                'test_type': 'independent_ttest',
                'solve_for': 'effect_size',
                'effect_size': float(calculated_es),
                'n_per_group': n,
                'total_n': n * 2 if ratio == 1.0 else int(n * (1 + ratio)),
                'power': power,
                'alpha': alpha,
                'alternative': alternative,
                'ratio': ratio,
            }

    def _solve_paired_ttest(
        self,
        effect_size: Optional[float],
        alpha: float,
        power: Optional[float],
        n: Optional[int],
        solve_for: str,
        alternative: str,
    ) -> Dict[str, Union[int, float, str]]:
        """Solve for paired samples t-test."""

        if solve_for == 'n':
            n_pairs = self.power_obj.solve_power(
                effect_size=effect_size,
                alpha=alpha,
                power=power,
                alternative=alternative,
            )
            n_pairs = int(np.ceil(n_pairs))

            return {
                'test_type': 'paired_ttest',
                'solve_for': 'n',
                'n_pairs': n_pairs,
                'effect_size': effect_size,
                'alpha': alpha,
                'power': power,
                'alternative': alternative,
            }

        elif solve_for == 'power':
            calculated_power = self.power_obj.solve_power(
                effect_size=effect_size,
                nobs=n,
                alpha=alpha,
                alternative=alternative,
            )

            return {
                'test_type': 'paired_ttest',
                'solve_for': 'power',
                'power': float(calculated_power),
                'n_pairs': n,
                'effect_size': effect_size,
                'alpha': alpha,
                'alternative': alternative,
            }

        elif solve_for == 'effect_size':
            calculated_es = self.power_obj.solve_power(
                nobs=n,
                alpha=alpha,
                power=power,
                alternative=alternative,
            )

            return {
                'test_type': 'paired_ttest',
                'solve_for': 'effect_size',
                'effect_size': float(calculated_es),
                'n_pairs': n,
                'power': power,
                'alpha': alpha,
                'alternative': alternative,
            }

    def _solve_anova(
        self,
        effect_size: Optional[float],
        alpha: float,
        power: Optional[float],
        n: Optional[int],
        solve_for: str,
        n_groups: int,
    ) -> Dict[str, Union[int, float, str]]:
        """Solve for one-way ANOVA or repeated measures ANOVA."""

        # Calculate degrees of freedom
        df_num = n_groups - 1  # Between groups df

        if solve_for == 'n':
            # For ANOVA, solve_power returns total sample size
            total_n = self.power_obj.solve_power(
                effect_size=effect_size,
                alpha=alpha,
                power=power,
                k_groups=n_groups,
            )
            total_n = int(np.ceil(total_n))
            n_per_group = int(np.ceil(total_n / n_groups))

            return {
                'test_type': self.test_type,
                'solve_for': 'n',
                'total_n': total_n,
                'n_per_group': n_per_group,
                'n_groups': n_groups,
                'effect_size': effect_size,
                'alpha': alpha,
                'power': power,
                'df_num': df_num,
                'df_denom': total_n - n_groups,
            }

        elif solve_for == 'power':
            calculated_power = self.power_obj.solve_power(
                effect_size=effect_size,
                nobs=n,
                alpha=alpha,
                k_groups=n_groups,
            )

            return {
                'test_type': self.test_type,
                'solve_for': 'power',
                'power': float(calculated_power),
                'total_n': n,
                'n_per_group': int(n / n_groups),
                'n_groups': n_groups,
                'effect_size': effect_size,
                'alpha': alpha,
                'df_num': df_num,
                'df_denom': n - n_groups,
            }

        elif solve_for == 'effect_size':
            calculated_es = self.power_obj.solve_power(
                nobs=n,
                alpha=alpha,
                power=power,
                k_groups=n_groups,
            )

            return {
                'test_type': self.test_type,
                'solve_for': 'effect_size',
                'effect_size': float(calculated_es),
                'total_n': n,
                'n_per_group': int(n / n_groups),
                'n_groups': n_groups,
                'power': power,
                'alpha': alpha,
                'df_num': df_num,
                'df_denom': n - n_groups,
            }

    def get_effect_size_guidelines(self) -> Dict[str, Dict[str, float]]:
        """
        Return conventional effect size guidelines.

        Returns:
            Dictionary with 'small', 'medium', 'large' effect sizes
        """
        if self.test_type in ['independent', 'paired']:
            # Cohen's d for t-tests
            return {
                'small': 0.2,
                'medium': 0.5,
                'large': 0.8,
            }
        elif self.test_type in ['anova', 'repeated_anova']:
            # Cohen's f for ANOVA
            return {
                'small': 0.10,
                'medium': 0.25,
                'large': 0.40,
            }
        else:
            return {}

    def convert_effect_size(
        self,
        from_metric: Literal['d', 'f', 'eta_squared', 'r'],
        to_metric: Literal['d', 'f', 'eta_squared', 'r'],
        value: float,
    ) -> float:
        """
        Convert between different effect size metrics.

        Args:
            from_metric: Source metric ('d', 'f', 'eta_squared', 'r')
            to_metric: Target metric
            value: Effect size value to convert

        Returns:
            Converted effect size
        """
        # Convert to Cohen's d first (as intermediate)
        if from_metric == 'd':
            d = value
        elif from_metric == 'r':
            d = (2 * value) / np.sqrt(1 - value**2)
        elif from_metric == 'eta_squared':
            d = 2 * np.sqrt(value / (1 - value))
        elif from_metric == 'f':
            d = 2 * value
        else:
            raise ValueError(f"Unknown from_metric: {from_metric}")

        # Convert from Cohen's d to target
        if to_metric == 'd':
            return d
        elif to_metric == 'r':
            return d / np.sqrt(d**2 + 4)
        elif to_metric == 'eta_squared':
            return d**2 / (d**2 + 4)
        elif to_metric == 'f':
            return d / 2
        else:
            raise ValueError(f"Unknown to_metric: {to_metric}")
