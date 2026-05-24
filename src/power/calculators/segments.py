"""
Power analysis for segment-based analysis (LCA/latent class analysis)

Supports:
- Pre-specified segment proportions
- Power to detect differences between segments
- Segment-specific sample size allocation
- Validation of prevalence constraints
"""

from typing import Dict, List, Literal, Optional, Union
import numpy as np
from scipy import stats
from statsmodels.stats.power import FTestAnovaPower


class SegmentPowerCalc:
    """
    Power analysis calculator for segment-based analysis.

    Used when you have pre-specified latent classes or segments
    (e.g., from LCA, mclust, or theoretical groupings).

    Examples:
        # 3 segments with 40%/40%/20% prevalence
        calc = SegmentPowerCalc(
            n_segments=3,
            prevalence=[0.40, 0.40, 0.20],
            test_type='anova'
        )

        # Calculate power given total n
        result = calc.calculate(
            total_n=500,
            effect_size=0.5,
            alpha=0.05,
            solve_for='power'
        )

        # Calculate required n
        result = calc.calculate(
            effect_size=0.5,
            alpha=0.05,
            power=0.80,
            solve_for='n'
        )
    """

    VALID_TEST_TYPES = ['anova', 'pairwise', 'regression']
    VALID_SOLVE_FOR = ['n', 'power', 'effect_size']

    def __init__(
        self,
        n_segments: int,
        prevalence: List[float],
        test_type: Literal['anova', 'pairwise', 'regression'] = 'anova',
    ):
        """
        Initialize the segment power calculator.

        Args:
            n_segments: Number of segments/latent classes
            prevalence: List of segment prevalences (must sum to 1.0)
            test_type: Type of analysis
                - 'anova': Compare means across all segments
                - 'pairwise': Pairwise comparisons between segments
                - 'regression': Segment as predictor in regression

        Raises:
            ValueError: If prevalence doesn't sum to 1.0 or lengths don't match
        """
        if n_segments < 2:
            raise ValueError("n_segments must be at least 2")

        if len(prevalence) != n_segments:
            raise ValueError(f"prevalence must have {n_segments} elements")

        # Validate prevalence sums to 1.0 (with tolerance for floating point)
        prevalence_sum = sum(prevalence)
        if not np.isclose(prevalence_sum, 1.0, atol=0.001):
            raise ValueError(
                f"prevalence must sum to 1.0 (got {prevalence_sum:.4f}). "
                f"Provided: {prevalence}"
            )

        # Validate all prevalences are positive
        if any(p <= 0 for p in prevalence):
            raise ValueError("All prevalences must be > 0")

        if test_type not in self.VALID_TEST_TYPES:
            raise ValueError(f"test_type must be one of {self.VALID_TEST_TYPES}")

        self.n_segments = n_segments
        self.prevalence = prevalence
        self.test_type = test_type

        # Initialize power analysis object
        if test_type in ['anova', 'pairwise']:
            self.power_obj = FTestAnovaPower()
        elif test_type == 'regression':
            from statsmodels.stats.power import FTestPower
            self.power_obj = FTestPower()

    def calculate(
        self,
        total_n: Optional[int] = None,
        effect_size: Optional[float] = None,
        alpha: float = 0.05,
        power: Optional[float] = None,
        solve_for: Literal['n', 'power', 'effect_size'] = 'n',
        min_segment_n: Optional[int] = None,
    ) -> Dict[str, Union[int, float, str, List]]:
        """
        Calculate sample size, power, or effect size for segment analysis.

        Args:
            total_n: Total sample size across all segments
            effect_size: Effect size (Cohen's d or f)
            alpha: Significance level (default: 0.05)
            power: Statistical power (default: 0.80)
            solve_for: What to solve for ('n', 'power', or 'effect_size')
            min_segment_n: Minimum n required per segment (optional constraint)

        Returns:
            Dictionary with calculation results, including:
            - total_n: Total sample size
            - n_per_segment: List of sample sizes per segment
            - power: Statistical power
            - warnings: List of warnings about underpowered segments

        Raises:
            ValueError: If required parameters are missing or invalid
        """
        if solve_for not in self.VALID_SOLVE_FOR:
            raise ValueError(f"solve_for must be one of {self.VALID_SOLVE_FOR}")

        # Validate required parameters
        if solve_for == 'n':
            if effect_size is None or power is None:
                raise ValueError("effect_size and power required when solving for n")
        elif solve_for == 'power':
            if effect_size is None or total_n is None:
                raise ValueError("effect_size and total_n required when solving for power")
        elif solve_for == 'effect_size':
            if power is None or total_n is None:
                raise ValueError("power and total_n required when solving for effect_size")

        # Perform calculation
        result = self._solve(
            total_n=total_n,
            effect_size=effect_size,
            alpha=alpha,
            power=power,
            solve_for=solve_for,
            min_segment_n=min_segment_n,
        )

        return result

    def _solve(
        self,
        total_n: Optional[int],
        effect_size: Optional[float],
        alpha: float,
        power: Optional[float],
        solve_for: str,
        min_segment_n: Optional[int],
    ) -> Dict[str, Union[int, float, str, List]]:
        """Internal method to perform the actual calculation."""

        if solve_for == 'n':
            return self._solve_n(
                effect_size=effect_size,
                alpha=alpha,
                power=power,
                min_segment_n=min_segment_n,
            )
        elif solve_for == 'power':
            return self._solve_power(
                total_n=total_n,
                effect_size=effect_size,
                alpha=alpha,
            )
        elif solve_for == 'effect_size':
            return self._solve_effect_size(
                total_n=total_n,
                alpha=alpha,
                power=power,
            )

    def _solve_n(
        self,
        effect_size: float,
        alpha: float,
        power: float,
        min_segment_n: Optional[int],
    ) -> Dict[str, Union[int, float, str, List]]:
        """Solve for required sample size."""

        if self.test_type == 'anova':
            # Calculate total n needed for ANOVA
            total_n = self.power_obj.solve_power(
                effect_size=effect_size,
                alpha=alpha,
                power=power,
                k_groups=self.n_segments,
            )
            total_n = int(np.ceil(total_n))

            # CRITICAL: Ensure smallest segment has minimum 30 participants
            # This is a statistical best practice for reliable inference
            if min_segment_n is None:
                min_segment_n = 30  # Default minimum

            # Calculate what total_n gives us per segment
            n_per_segment = [int(np.ceil(total_n * p)) for p in self.prevalence]
            min_n_achieved = min(n_per_segment)

            # If smallest segment is below threshold, scale up
            if min_n_achieved < min_segment_n:
                scale_factor = min_segment_n / min_n_achieved
                total_n = int(np.ceil(total_n * scale_factor))
                n_per_segment = [int(np.ceil(total_n * p)) for p in self.prevalence]

        elif self.test_type == 'pairwise':
            # For pairwise comparisons, need to account for multiple comparisons
            # Use Bonferroni correction
            n_comparisons = (self.n_segments * (self.n_segments - 1)) / 2
            adjusted_alpha = alpha / n_comparisons

            # Use t-test power for pairwise
            from statsmodels.stats.power import TTestIndPower
            ttest_power = TTestIndPower()

            # Calculate n per group for smallest segment pair
            # Conservative: assume equal allocation
            n_per_group = ttest_power.solve_power(
                effect_size=effect_size,
                alpha=adjusted_alpha,
                power=power,
                ratio=1.0,
                alternative='two-sided',
            )
            n_per_group = int(np.ceil(n_per_group))

            # Total n assuming equal allocation
            total_n = n_per_group * self.n_segments

        elif self.test_type == 'regression':
            # Segment as categorical predictor (k-1 dummy variables)
            from statsmodels.stats.power import FTestPower
            regression_power = FTestPower()

            # df_num = n_segments - 1 (dummy variables)
            # Solve iteratively for n
            n_estimate = 50
            for _ in range(50):
                df_denom = n_estimate - self.n_segments
                if df_denom <= 0:
                    n_estimate += 10
                    continue

                calculated_power = regression_power.solve_power(
                    effect_size=effect_size,
                    df_num=self.n_segments - 1,
                    df_denom=df_denom,
                    alpha=alpha,
                )

                if abs(calculated_power - power) < 0.001:
                    break

                if calculated_power < power:
                    n_estimate += max(1, int((power - calculated_power) * 50))
                else:
                    n_estimate -= max(1, int((calculated_power - power) * 50))

            total_n = int(np.ceil(n_estimate))

        # Check for warnings
        warnings = []
        min_n_achieved = min(n_per_segment)

        if min_n_achieved < 30:
            warnings.append(
                f"⚠️ Smallest segment has only {min_n_achieved} participants. "
                f"Minimum 30 recommended for reliable inference. Total adjusted to {total_n}."
            )

        # Recalculate actual power with final n
        actual_power = self._calculate_power(total_n, effect_size, alpha)

        return {
            'test_type': self.test_type,
            'solve_for': 'n',
            'total_n': total_n,
            'n_per_segment': n_per_segment,
            'prevalence': self.prevalence,
            'n_segments': self.n_segments,
            'effect_size': effect_size,
            'alpha': alpha,
            'requested_power': power,
            'actual_power': actual_power,
            'warnings': warnings,
        }

    def _solve_power(
        self,
        total_n: int,
        effect_size: float,
        alpha: float,
    ) -> Dict[str, Union[int, float, str, List]]:
        """Solve for statistical power given sample size."""

        # Allocate sample sizes to segments
        n_per_segment = [int(total_n * p) for p in self.prevalence]

        # Calculate power
        calculated_power = self._calculate_power(total_n, effect_size, alpha)

        # Check for underpowered segments
        warnings = []
        for i, n in enumerate(n_per_segment):
            if n < 30:  # Rule of thumb: n < 30 is concerning
                warnings.append(
                    f"Segment {i+1} (prevalence={self.prevalence[i]:.1%}) "
                    f"has only n={n}, which may be underpowered"
                )

        return {
            'test_type': self.test_type,
            'solve_for': 'power',
            'power': calculated_power,
            'total_n': total_n,
            'n_per_segment': n_per_segment,
            'prevalence': self.prevalence,
            'n_segments': self.n_segments,
            'effect_size': effect_size,
            'alpha': alpha,
            'warnings': warnings,
        }

    def _solve_effect_size(
        self,
        total_n: int,
        alpha: float,
        power: float,
    ) -> Dict[str, Union[int, float, str, List]]:
        """Solve for detectable effect size given sample size and power."""

        if self.test_type == 'anova':
            calculated_es = self.power_obj.solve_power(
                nobs=total_n,
                alpha=alpha,
                power=power,
                k_groups=self.n_segments,
            )

        elif self.test_type == 'pairwise':
            n_comparisons = (self.n_segments * (self.n_segments - 1)) / 2
            adjusted_alpha = alpha / n_comparisons

            from statsmodels.stats.power import TTestIndPower
            ttest_power = TTestIndPower()

            # Use smallest segment size (most conservative)
            n_per_segment = [int(total_n * p) for p in self.prevalence]
            min_n = min(n_per_segment)

            calculated_es = ttest_power.solve_power(
                nobs1=min_n,
                alpha=adjusted_alpha,
                power=power,
                ratio=1.0,
                alternative='two-sided',
            )

        elif self.test_type == 'regression':
            from statsmodels.stats.power import FTestPower
            regression_power = FTestPower()

            df_denom = total_n - self.n_segments

            calculated_es = regression_power.solve_power(
                df_num=self.n_segments - 1,
                df_denom=df_denom,
                alpha=alpha,
                power=power,
            )

        n_per_segment = [int(total_n * p) for p in self.prevalence]

        return {
            'test_type': self.test_type,
            'solve_for': 'effect_size',
            'effect_size': float(calculated_es),
            'total_n': total_n,
            'n_per_segment': n_per_segment,
            'prevalence': self.prevalence,
            'n_segments': self.n_segments,
            'power': power,
            'alpha': alpha,
            'warnings': [],
        }

    def _calculate_power(self, total_n: int, effect_size: float, alpha: float) -> float:
        """Helper to calculate power given n and effect size."""

        if self.test_type == 'anova':
            power = self.power_obj.solve_power(
                effect_size=effect_size,
                nobs=total_n,
                alpha=alpha,
                k_groups=self.n_segments,
            )

        elif self.test_type == 'pairwise':
            n_comparisons = (self.n_segments * (self.n_segments - 1)) / 2
            adjusted_alpha = alpha / n_comparisons

            from statsmodels.stats.power import TTestIndPower
            ttest_power = TTestIndPower()

            n_per_segment = [int(total_n * p) for p in self.prevalence]
            min_n = min(n_per_segment)

            power = ttest_power.solve_power(
                effect_size=effect_size,
                nobs1=min_n,
                alpha=adjusted_alpha,
                ratio=1.0,
                alternative='two-sided',
            )

        elif self.test_type == 'regression':
            from statsmodels.stats.power import FTestPower
            regression_power = FTestPower()

            df_denom = total_n - self.n_segments

            power = regression_power.solve_power(
                effect_size=effect_size,
                df_num=self.n_segments - 1,
                df_denom=df_denom,
                alpha=alpha,
            )

        return float(power)

    def get_balanced_allocation(self, total_n: int) -> Dict[str, Union[int, List]]:
        """
        Calculate sample allocation based on segment prevalence.

        Args:
            total_n: Total sample size

        Returns:
            Dictionary with allocation details
        """
        n_per_segment = [int(np.ceil(total_n * p)) for p in self.prevalence]
        actual_total = sum(n_per_segment)

        return {
            'total_n_requested': total_n,
            'total_n_allocated': actual_total,
            'n_per_segment': n_per_segment,
            'prevalence': self.prevalence,
            'difference': actual_total - total_n,
        }

    def validate_prevalence(self) -> Dict[str, Union[bool, str, List]]:
        """
        Validate that prevalence specification is reasonable.

        Returns:
            Dictionary with validation results and warnings
        """
        warnings = []
        is_valid = True

        # Check if any segment is very small (<5%)
        for i, p in enumerate(self.prevalence):
            if p < 0.05:
                warnings.append(
                    f"Segment {i+1} has very low prevalence ({p:.1%}). "
                    f"This may require a very large total sample size."
                )

        # Check if any segment is very large (>80%)
        for i, p in enumerate(self.prevalence):
            if p > 0.80:
                warnings.append(
                    f"Segment {i+1} has very high prevalence ({p:.1%}). "
                    f"Consider whether segment analysis is appropriate."
                )

        # Check if prevalence is very unbalanced
        max_p = max(self.prevalence)
        min_p = min(self.prevalence)
        ratio = max_p / min_p if min_p > 0 else np.inf

        if ratio > 5:
            warnings.append(
                f"Prevalence is highly unbalanced (ratio {ratio:.1f}:1). "
                f"Smallest segment may require very large total sample size."
            )

        return {
            'is_valid': is_valid,
            'prevalence_sum': sum(self.prevalence),
            'warnings': warnings,
        }
