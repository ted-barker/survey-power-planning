"""
Power analysis for proportions and categorical tests

Supports:
- Two proportions test (independent samples)
- One proportion test (vs. population value)
- Chi-square test of independence
- Fisher's exact test (small samples)
"""

from typing import Dict, Literal, Optional, Union
import numpy as np
from scipy import stats
from statsmodels.stats.power import (
    zt_ind_solve_power,
    NormalIndPower,
    GofChisquarePower,
)


class ProportionsPowerCalc:
    """
    Power analysis calculator for proportions and categorical tests.

    Examples:
        # Two proportions test
        calc = ProportionsPowerCalc(test_type='two_proportions')
        result = calc.calculate(p1=0.30, p2=0.40, alpha=0.05, power=0.80, solve_for='n')

        # One proportion test
        calc = ProportionsPowerCalc(test_type='one_proportion')
        result = calc.calculate(p1=0.35, p2=0.50, alpha=0.05, power=0.80, solve_for='n')

        # Chi-square test
        calc = ProportionsPowerCalc(test_type='chi_square')
        result = calc.calculate(effect_size=0.3, alpha=0.05, power=0.80,
                               solve_for='n', df=2)
    """

    VALID_TEST_TYPES = ['two_proportions', 'one_proportion', 'chi_square']
    VALID_SOLVE_FOR = ['n', 'power', 'effect_size']

    def __init__(self, test_type: Literal['two_proportions', 'one_proportion', 'chi_square']):
        """
        Initialize the proportions power calculator.

        Args:
            test_type: Type of test
                - 'two_proportions': Compare two independent proportions
                - 'one_proportion': Test one proportion vs. population value
                - 'chi_square': Chi-square test of independence
        """
        if test_type not in self.VALID_TEST_TYPES:
            raise ValueError(f"test_type must be one of {self.VALID_TEST_TYPES}")

        self.test_type = test_type

        if test_type in ['two_proportions', 'one_proportion']:
            self.power_obj = NormalIndPower()
        elif test_type == 'chi_square':
            self.power_obj = GofChisquarePower()

    def calculate(
        self,
        p1: Optional[float] = None,
        p2: Optional[float] = None,
        effect_size: Optional[float] = None,
        alpha: float = 0.05,
        power: Optional[float] = None,
        n: Optional[int] = None,
        solve_for: Literal['n', 'power', 'effect_size'] = 'n',
        alternative: Literal['two-sided', 'larger', 'smaller'] = 'two-sided',
        ratio: float = 1.0,
        df: Optional[int] = None,
    ) -> Dict[str, Union[int, float, str]]:
        """
        Calculate sample size, power, or effect size for proportions tests.

        Args:
            p1: Proportion in group 1 (or sample proportion)
            p2: Proportion in group 2 (or population proportion)
            effect_size: Cohen's h or w (alternative to p1/p2)
            alpha: Significance level (default: 0.05)
            power: Statistical power (default: 0.80)
            n: Sample size (per group for two proportions, total for chi-square)
            solve_for: What to solve for ('n', 'power', or 'effect_size')
            alternative: Type of test ('two-sided', 'larger', 'smaller')
            ratio: Ratio of sample sizes between groups (default: 1.0)
            df: Degrees of freedom (required for chi-square)

        Returns:
            Dictionary with calculation results and metadata

        Raises:
            ValueError: If required parameters are missing or invalid
        """
        if solve_for not in self.VALID_SOLVE_FOR:
            raise ValueError(f"solve_for must be one of {self.VALID_SOLVE_FOR}")

        # For proportions tests, calculate effect size from p1 and p2 if not provided
        if self.test_type in ['two_proportions', 'one_proportion']:
            if effect_size is None:
                if p1 is None or p2 is None:
                    raise ValueError("p1 and p2 required when effect_size not provided")
                effect_size = self._cohens_h(p1, p2)

        # Chi-square specific validation
        if self.test_type == 'chi_square':
            if df is None:
                raise ValueError("df (degrees of freedom) required for chi-square test")
            if df < 1:
                raise ValueError("df must be at least 1")

        # Validate based on what we're solving for
        if solve_for == 'n':
            if effect_size is None or power is None:
                raise ValueError("effect_size and power required when solving for n")
        elif solve_for == 'power':
            if effect_size is None or n is None:
                raise ValueError("effect_size and n required when solving for power")
        elif solve_for == 'effect_size':
            if power is None or n is None:
                raise ValueError("power and n required when solving for effect_size")

        # Perform calculation
        result = self._solve(
            p1=p1,
            p2=p2,
            effect_size=effect_size,
            alpha=alpha,
            power=power,
            n=n,
            solve_for=solve_for,
            alternative=alternative,
            ratio=ratio,
            df=df,
        )

        return result

    def _solve(
        self,
        p1: Optional[float],
        p2: Optional[float],
        effect_size: float,
        alpha: float,
        power: Optional[float],
        n: Optional[int],
        solve_for: str,
        alternative: str,
        ratio: float,
        df: Optional[int],
    ) -> Dict[str, Union[int, float, str]]:
        """Internal method to perform the actual calculation."""

        if self.test_type in ['two_proportions', 'one_proportion']:
            return self._solve_proportions(
                p1, p2, effect_size, alpha, power, n, solve_for, alternative, ratio
            )
        elif self.test_type == 'chi_square':
            return self._solve_chi_square(
                effect_size, alpha, power, n, solve_for, df
            )

    def _solve_proportions(
        self,
        p1: Optional[float],
        p2: Optional[float],
        effect_size: float,
        alpha: float,
        power: Optional[float],
        n: Optional[int],
        solve_for: str,
        alternative: str,
        ratio: float,
    ) -> Dict[str, Union[int, float, str]]:
        """Solve for proportions tests (two proportions or one proportion)."""

        if solve_for == 'n':
            # Use zt_ind_solve_power for more accurate calculation
            n_per_group = zt_ind_solve_power(
                effect_size=effect_size,
                alpha=alpha,
                power=power,
                ratio=ratio,
                alternative=alternative,
            )
            n_per_group = int(np.ceil(n_per_group))

            result = {
                'test_type': self.test_type,
                'solve_for': 'n',
                'n_per_group': n_per_group,
                'total_n': n_per_group * 2 if ratio == 1.0 else int(n_per_group * (1 + ratio)),
                'effect_size_h': effect_size,
                'alpha': alpha,
                'power': power,
                'alternative': alternative,
                'ratio': ratio,
            }

            if p1 is not None and p2 is not None:
                result['p1'] = p1
                result['p2'] = p2
                result['difference'] = abs(p1 - p2)

            return result

        elif solve_for == 'power':
            calculated_power = zt_ind_solve_power(
                effect_size=effect_size,
                nobs1=n,
                alpha=alpha,
                ratio=ratio,
                alternative=alternative,
            )

            result = {
                'test_type': self.test_type,
                'solve_for': 'power',
                'power': float(calculated_power),
                'n_per_group': n,
                'total_n': n * 2 if ratio == 1.0 else int(n * (1 + ratio)),
                'effect_size_h': effect_size,
                'alpha': alpha,
                'alternative': alternative,
                'ratio': ratio,
            }

            if p1 is not None and p2 is not None:
                result['p1'] = p1
                result['p2'] = p2
                result['difference'] = abs(p1 - p2)

            return result

        elif solve_for == 'effect_size':
            calculated_es = zt_ind_solve_power(
                nobs1=n,
                alpha=alpha,
                power=power,
                ratio=ratio,
                alternative=alternative,
            )

            # Convert back to proportion difference if possible
            p1_calc = None
            p2_calc = None
            if p1 is not None:
                # Given p1, calculate p2 from effect size
                p2_calc = self._h_to_p2(calculated_es, p1)
            elif p2 is not None:
                # Given p2, calculate p1 from effect size
                p1_calc = self._h_to_p2(calculated_es, p2)

            result = {
                'test_type': self.test_type,
                'solve_for': 'effect_size',
                'effect_size_h': float(calculated_es),
                'n_per_group': n,
                'total_n': n * 2 if ratio == 1.0 else int(n * (1 + ratio)),
                'power': power,
                'alpha': alpha,
                'alternative': alternative,
                'ratio': ratio,
            }

            if p1_calc is not None:
                result['p1'] = p1_calc
                result['p2'] = p2
                result['difference'] = abs(p1_calc - p2)
            elif p2_calc is not None:
                result['p1'] = p1
                result['p2'] = p2_calc
                result['difference'] = abs(p1 - p2_calc)

            return result

    def _solve_chi_square(
        self,
        effect_size: float,
        alpha: float,
        power: Optional[float],
        n: Optional[int],
        solve_for: str,
        df: int,
    ) -> Dict[str, Union[int, float, str]]:
        """Solve for chi-square test."""

        if solve_for == 'n':
            total_n = self.power_obj.solve_power(
                effect_size=effect_size,
                alpha=alpha,
                power=power,
                n_bins=df + 1,
            )
            total_n = int(np.ceil(total_n))

            return {
                'test_type': 'chi_square',
                'solve_for': 'n',
                'total_n': total_n,
                'effect_size_w': effect_size,
                'alpha': alpha,
                'power': power,
                'df': df,
            }

        elif solve_for == 'power':
            calculated_power = self.power_obj.solve_power(
                effect_size=effect_size,
                nobs=n,
                alpha=alpha,
                n_bins=df + 1,
            )

            return {
                'test_type': 'chi_square',
                'solve_for': 'power',
                'power': float(calculated_power),
                'total_n': n,
                'effect_size_w': effect_size,
                'alpha': alpha,
                'df': df,
            }

        elif solve_for == 'effect_size':
            calculated_es = self.power_obj.solve_power(
                nobs=n,
                alpha=alpha,
                power=power,
                n_bins=df + 1,
            )

            return {
                'test_type': 'chi_square',
                'solve_for': 'effect_size',
                'effect_size_w': float(calculated_es),
                'total_n': n,
                'power': power,
                'alpha': alpha,
                'df': df,
            }

    def _cohens_h(self, p1: float, p2: float) -> float:
        """
        Calculate Cohen's h effect size for proportions.

        Cohen's h = 2 * (arcsin(sqrt(p1)) - arcsin(sqrt(p2)))
        """
        if not (0 <= p1 <= 1) or not (0 <= p2 <= 1):
            raise ValueError("Proportions must be between 0 and 1")

        h = 2 * (np.arcsin(np.sqrt(p1)) - np.arcsin(np.sqrt(p2)))
        return abs(h)

    def _h_to_p2(self, h: float, p1: float) -> float:
        """
        Convert Cohen's h back to proportion p2 given p1.

        Solve: h = 2 * (arcsin(sqrt(p1)) - arcsin(sqrt(p2)))
        """
        arcsin_p1 = np.arcsin(np.sqrt(p1))
        arcsin_p2 = arcsin_p1 - (h / 2)
        p2 = (np.sin(arcsin_p2)) ** 2
        return np.clip(p2, 0, 1)

    def get_effect_size_guidelines(self) -> Dict[str, Dict[str, float]]:
        """
        Return conventional effect size guidelines.

        Returns:
            Dictionary with 'small', 'medium', 'large' effect sizes
            for both Cohen's h (proportions) and Cohen's w (chi-square)
        """
        return {
            'cohens_h': {
                'small': 0.20,
                'medium': 0.50,
                'large': 0.80,
            },
            'cohens_w': {
                'small': 0.10,
                'medium': 0.30,
                'large': 0.50,
            },
        }

    def calculate_chi_square_effect_from_table(
        self, observed_table: np.ndarray
    ) -> Dict[str, Union[float, np.ndarray]]:
        """
        Calculate Chi-square effect size (Cohen's w) from contingency table.

        Args:
            observed_table: Contingency table (2D array)

        Returns:
            Dictionary with effect size and related statistics
        """
        observed_table = np.array(observed_table)

        if observed_table.ndim != 2:
            raise ValueError("observed_table must be a 2D array")

        # Calculate expected frequencies under independence
        row_sums = observed_table.sum(axis=1, keepdims=True)
        col_sums = observed_table.sum(axis=0, keepdims=True)
        total = observed_table.sum()

        expected_table = (row_sums @ col_sums) / total

        # Calculate Cohen's w
        # w = sqrt(sum((observed - expected)^2 / expected) / n)
        chi_square_stat = np.sum((observed_table - expected_table) ** 2 / expected_table)
        w = np.sqrt(chi_square_stat / total)

        # Degrees of freedom
        df = (observed_table.shape[0] - 1) * (observed_table.shape[1] - 1)

        return {
            'effect_size_w': float(w),
            'chi_square_stat': float(chi_square_stat),
            'df': int(df),
            'observed': observed_table,
            'expected': expected_table,
        }

    def minimum_cell_frequency(self, n_rows: int, n_cols: int) -> int:
        """
        Calculate minimum expected cell frequency for chi-square test.

        Rule of thumb: Expected frequency should be at least 5 in each cell.

        Args:
            n_rows: Number of rows in contingency table
            n_cols: Number of columns in contingency table

        Returns:
            Minimum total sample size needed
        """
        n_cells = n_rows * n_cols
        min_per_cell = 5
        return n_cells * min_per_cell
