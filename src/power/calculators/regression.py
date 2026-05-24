"""
Power analysis for regression-based tests

Supports:
- Simple linear regression (one predictor)
- Multiple regression (multiple predictors)
- Moderation analysis (interaction terms)
- Partial correlation (controlling for covariates)
"""

from typing import Dict, Literal, Optional, Union
import numpy as np
from scipy import stats
from statsmodels.stats.power import FTestPower


class RegressionPowerCalc:
    """
    Power analysis calculator for regression-based tests.

    Examples:
        # Simple linear regression
        calc = RegressionPowerCalc(test_type='simple')
        result = calc.calculate(effect_size=0.15, alpha=0.05, power=0.80, solve_for='n')

        # Multiple regression with 5 predictors
        calc = RegressionPowerCalc(test_type='multiple')
        result = calc.calculate(effect_size=0.15, alpha=0.05, power=0.80,
                               solve_for='n', n_predictors=5)

        # Moderation (interaction term)
        calc = RegressionPowerCalc(test_type='moderation')
        result = calc.calculate(effect_size=0.02, alpha=0.05, power=0.80,
                               solve_for='n', n_predictors=3)
    """

    VALID_TEST_TYPES = ['simple', 'multiple', 'moderation', 'partial']
    VALID_SOLVE_FOR = ['n', 'power', 'effect_size']

    def __init__(self, test_type: Literal['simple', 'multiple', 'moderation', 'partial']):
        """
        Initialize the regression power calculator.

        Args:
            test_type: Type of regression test
                - 'simple': Simple linear regression (1 predictor)
                - 'multiple': Multiple regression (k predictors)
                - 'moderation': Interaction term in regression
                - 'partial': Partial correlation (controlling for covariates)
        """
        if test_type not in self.VALID_TEST_TYPES:
            raise ValueError(f"test_type must be one of {self.VALID_TEST_TYPES}")

        self.test_type = test_type
        self.power_obj = FTestPower()

    def calculate(
        self,
        effect_size: Optional[float] = None,
        alpha: float = 0.05,
        power: Optional[float] = None,
        n: Optional[int] = None,
        solve_for: Literal['n', 'power', 'effect_size'] = 'n',
        n_predictors: Optional[int] = None,
        n_covariates: int = 0,
        r_squared: Optional[float] = None,
    ) -> Dict[str, Union[int, float, str]]:
        """
        Calculate sample size, power, or effect size for regression.

        Args:
            effect_size: Effect size (Cohen's f² or f)
            alpha: Significance level (default: 0.05)
            power: Statistical power (default: 0.80)
            n: Sample size
            solve_for: What to solve for ('n', 'power', or 'effect_size')
            n_predictors: Number of predictors (required for multiple/moderation)
            n_covariates: Number of covariates (for partial correlation)
            r_squared: R² value (alternative to effect_size)

        Returns:
            Dictionary with calculation results and metadata

        Raises:
            ValueError: If required parameters are missing or invalid
        """
        if solve_for not in self.VALID_SOLVE_FOR:
            raise ValueError(f"solve_for must be one of {self.VALID_SOLVE_FOR}")

        # Validate required parameters
        if solve_for == 'n':
            if effect_size is None and r_squared is None:
                raise ValueError("effect_size or r_squared required when solving for n")
            if power is None:
                raise ValueError("power required when solving for n")
        elif solve_for == 'power':
            if effect_size is None and r_squared is None:
                raise ValueError("effect_size or r_squared required when solving for power")
            if n is None:
                raise ValueError("n required when solving for power")
        elif solve_for == 'effect_size':
            if power is None or n is None:
                raise ValueError("power and n required when solving for effect_size")

        # Convert R² to f² if provided
        if r_squared is not None:
            if not 0 <= r_squared < 1:
                raise ValueError("r_squared must be between 0 and 1")
            effect_size = self._r_squared_to_f_squared(r_squared)

        # Determine number of predictors
        if self.test_type == 'simple':
            n_predictors = 1
        elif self.test_type in ['multiple', 'moderation', 'partial']:
            if n_predictors is None:
                raise ValueError(f"n_predictors required for {self.test_type}")
            if n_predictors < 1:
                raise ValueError("n_predictors must be at least 1")

        # Perform calculation
        result = self._solve(
            effect_size=effect_size,
            alpha=alpha,
            power=power,
            n=n,
            solve_for=solve_for,
            n_predictors=n_predictors,
            n_covariates=n_covariates,
        )

        return result

    def _solve(
        self,
        effect_size: Optional[float],
        alpha: float,
        power: Optional[float],
        n: Optional[int],
        solve_for: str,
        n_predictors: int,
        n_covariates: int,
    ) -> Dict[str, Union[int, float, str]]:
        """Internal method to perform the actual calculation."""

        # Degrees of freedom
        # df_num = number of predictors being tested
        # df_denom = n - n_predictors - n_covariates - 1
        df_num = n_predictors

        if solve_for == 'n':
            # Solve for sample size
            # We need to find n such that df_denom = n - n_predictors - n_covariates - 1
            # statsmodels solve_power expects df_denom, so we solve iteratively

            # Use Newton's method to find n
            n_estimate = 50  # Initial guess
            for _ in range(50):  # Max iterations
                df_denom = n_estimate - n_predictors - n_covariates - 1
                if df_denom <= 0:
                    n_estimate += 10
                    continue

                calculated_power = self.power_obj.solve_power(
                    effect_size=effect_size,
                    df_num=df_num,
                    df_denom=df_denom,
                    alpha=alpha,
                )

                if abs(calculated_power - power) < 0.001:
                    break

                # Adjust n_estimate based on power difference
                if calculated_power < power:
                    n_estimate += max(1, int((power - calculated_power) * 50))
                else:
                    n_estimate -= max(1, int((calculated_power - power) * 50))

            n_estimate = int(np.ceil(n_estimate))
            df_denom = n_estimate - n_predictors - n_covariates - 1

            # Convert f² back to R²
            r_squared = self._f_squared_to_r_squared(effect_size)

            return {
                'test_type': self.test_type,
                'solve_for': 'n',
                'n': n_estimate,
                'n_predictors': n_predictors,
                'n_covariates': n_covariates,
                'effect_size_f2': effect_size,
                'r_squared': r_squared,
                'alpha': alpha,
                'power': power,
                'df_num': df_num,
                'df_denom': df_denom,
            }

        elif solve_for == 'power':
            df_denom = n - n_predictors - n_covariates - 1

            if df_denom <= 0:
                raise ValueError(
                    f"Sample size too small. Need n > {n_predictors + n_covariates + 1}"
                )

            calculated_power = self.power_obj.solve_power(
                effect_size=effect_size,
                df_num=df_num,
                df_denom=df_denom,
                alpha=alpha,
            )

            r_squared = self._f_squared_to_r_squared(effect_size)

            return {
                'test_type': self.test_type,
                'solve_for': 'power',
                'power': float(calculated_power),
                'n': n,
                'n_predictors': n_predictors,
                'n_covariates': n_covariates,
                'effect_size_f2': effect_size,
                'r_squared': r_squared,
                'alpha': alpha,
                'df_num': df_num,
                'df_denom': df_denom,
            }

        elif solve_for == 'effect_size':
            df_denom = n - n_predictors - n_covariates - 1

            if df_denom <= 0:
                raise ValueError(
                    f"Sample size too small. Need n > {n_predictors + n_covariates + 1}"
                )

            calculated_es = self.power_obj.solve_power(
                df_num=df_num,
                df_denom=df_denom,
                alpha=alpha,
                power=power,
            )

            r_squared = self._f_squared_to_r_squared(calculated_es)

            return {
                'test_type': self.test_type,
                'solve_for': 'effect_size',
                'effect_size_f2': float(calculated_es),
                'r_squared': r_squared,
                'n': n,
                'n_predictors': n_predictors,
                'n_covariates': n_covariates,
                'power': power,
                'alpha': alpha,
                'df_num': df_num,
                'df_denom': df_denom,
            }

    def _r_squared_to_f_squared(self, r_squared: float) -> float:
        """Convert R² to Cohen's f²."""
        if r_squared >= 1:
            raise ValueError("r_squared must be < 1")
        return r_squared / (1 - r_squared)

    def _f_squared_to_r_squared(self, f_squared: float) -> float:
        """Convert Cohen's f² to R²."""
        return f_squared / (1 + f_squared)

    def get_effect_size_guidelines(self) -> Dict[str, Dict[str, float]]:
        """
        Return conventional effect size guidelines for regression.

        Returns:
            Dictionary with 'small', 'medium', 'large' effect sizes
            for both f² and R²
        """
        return {
            'f_squared': {
                'small': 0.02,
                'medium': 0.15,
                'large': 0.35,
            },
            'r_squared': {
                'small': 0.02,    # f²=0.02 → R²≈0.02
                'medium': 0.13,   # f²=0.15 → R²≈0.13
                'large': 0.26,    # f²=0.35 → R²≈0.26
            },
        }

    def calculate_moderation_power(
        self,
        n: int,
        main_effect_r_squared: float,
        interaction_r_squared: float,
        alpha: float = 0.05,
    ) -> Dict[str, Union[float, str]]:
        """
        Calculate power for moderation (interaction) effect.

        This tests the incremental R² gained by adding the interaction term.

        Args:
            n: Sample size
            main_effect_r_squared: R² from model with only main effects
            interaction_r_squared: R² from full model with interaction
            alpha: Significance level

        Returns:
            Dictionary with power calculation results
        """
        if interaction_r_squared <= main_effect_r_squared:
            raise ValueError("interaction_r_squared must be > main_effect_r_squared")

        # Incremental R² from interaction
        delta_r_squared = interaction_r_squared - main_effect_r_squared

        # Convert to f²
        # f² = (R²full - R²reduced) / (1 - R²full)
        f_squared = delta_r_squared / (1 - interaction_r_squared)

        # df_num = 1 (testing one interaction term)
        # df_denom = n - (number of predictors in full model) - 1
        # Assume full model has: 2 main effects + 1 interaction = 3 predictors
        df_num = 1
        df_denom = n - 3 - 1

        if df_denom <= 0:
            raise ValueError(f"Sample size too small. Need n > 4")

        power = self.power_obj.solve_power(
            effect_size=f_squared,
            df_num=df_num,
            df_denom=df_denom,
            alpha=alpha,
        )

        return {
            'test_type': 'moderation',
            'power': float(power),
            'n': n,
            'main_effect_r_squared': main_effect_r_squared,
            'interaction_r_squared': interaction_r_squared,
            'delta_r_squared': delta_r_squared,
            'effect_size_f2': f_squared,
            'alpha': alpha,
            'df_num': df_num,
            'df_denom': df_denom,
        }

    def calculate_required_n_moderation(
        self,
        main_effect_r_squared: float,
        interaction_r_squared: float,
        alpha: float = 0.05,
        power: float = 0.80,
    ) -> Dict[str, Union[int, float, str]]:
        """
        Calculate required sample size for moderation analysis.

        Args:
            main_effect_r_squared: R² from model with only main effects
            interaction_r_squared: R² from full model with interaction
            alpha: Significance level
            power: Desired statistical power

        Returns:
            Dictionary with required sample size
        """
        if interaction_r_squared <= main_effect_r_squared:
            raise ValueError("interaction_r_squared must be > main_effect_r_squared")

        # Incremental R² from interaction
        delta_r_squared = interaction_r_squared - main_effect_r_squared
        f_squared = delta_r_squared / (1 - interaction_r_squared)

        # Solve for n iteratively
        df_num = 1
        n_estimate = 50

        for _ in range(50):
            df_denom = n_estimate - 3 - 1
            if df_denom <= 0:
                n_estimate += 10
                continue

            calculated_power = self.power_obj.solve_power(
                effect_size=f_squared,
                df_num=df_num,
                df_denom=df_denom,
                alpha=alpha,
            )

            if abs(calculated_power - power) < 0.001:
                break

            if calculated_power < power:
                n_estimate += max(1, int((power - calculated_power) * 50))
            else:
                n_estimate -= max(1, int((calculated_power - power) * 50))

        n_estimate = int(np.ceil(n_estimate))

        return {
            'test_type': 'moderation',
            'solve_for': 'n',
            'n': n_estimate,
            'main_effect_r_squared': main_effect_r_squared,
            'interaction_r_squared': interaction_r_squared,
            'delta_r_squared': delta_r_squared,
            'effect_size_f2': f_squared,
            'alpha': alpha,
            'power': power,
            'df_num': df_num,
            'df_denom': n_estimate - 4,
        }
