"""
Power analysis for non-parametric tests

Supports:
- Mann-Whitney U test (2 independent groups)
- Wilcoxon signed-rank test (paired data)
- Kruskal-Wallis H test (3+ independent groups)
- Friedman test (repeated measures)
"""

from typing import Dict, Literal, Optional
import numpy as np
from scipy import stats


class NonParametricPowerCalc:
    """
    Power analysis calculator for non-parametric tests.

    Note: Non-parametric tests typically require 5-15% more sample than
    parametric equivalents to achieve the same power.

    Examples:
        # Mann-Whitney U (equivalent to independent t-test)
        calc = NonParametricPowerCalc(test_type='mann_whitney')
        result = calc.calculate(effect_size=0.5, alpha=0.05, power=0.80, solve_for='n')

        # Kruskal-Wallis (equivalent to ANOVA)
        calc = NonParametricPowerCalc(test_type='kruskal_wallis')
        result = calc.calculate(effect_size=0.25, alpha=0.05, power=0.80,
                               solve_for='n', n_groups=4)
    """

    VALID_TEST_TYPES = ['mann_whitney', 'wilcoxon', 'kruskal_wallis', 'friedman']
    VALID_SOLVE_FOR = ['n', 'power', 'effect_size']

    # Asymptotic Relative Efficiency (ARE) - how much more sample needed vs parametric
    ARE = {
        'mann_whitney': 0.955,  # 95.5% efficient vs t-test
        'wilcoxon': 0.955,      # 95.5% efficient vs paired t-test
        'kruskal_wallis': 0.955,  # 95.5% efficient vs ANOVA
        'friedman': 0.955       # 95.5% efficient vs repeated ANOVA
    }

    def __init__(self, test_type: Literal['mann_whitney', 'wilcoxon', 'kruskal_wallis', 'friedman']):
        """
        Initialize the non-parametric power calculator.

        Args:
            test_type: Type of non-parametric test
                - 'mann_whitney': Compare 2 independent groups (ranks)
                - 'wilcoxon': Compare paired/matched observations (ranks)
                - 'kruskal_wallis': Compare 3+ independent groups (ranks)
                - 'friedman': Compare 3+ repeated measures (ranks)
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
        n_groups: int = 2,
        **kwargs
    ) -> Dict:
        """
        Calculate power analysis for non-parametric tests.

        Args:
            effect_size: Effect size (same scale as parametric equivalent)
                - Mann-Whitney/Wilcoxon: Cohen's d
                - Kruskal-Wallis/Friedman: Cohen's f
            alpha: Significance level (default 0.05)
            power: Statistical power (default 0.80)
            n: Sample size (per group for independent, total for paired)
            solve_for: What to calculate ('n', 'power', or 'effect_size')
            n_groups: Number of groups (for Kruskal-Wallis/Friedman)

        Returns:
            Dictionary with results
        """
        if solve_for not in self.VALID_SOLVE_FOR:
            raise ValueError(f"solve_for must be one of {self.VALID_SOLVE_FOR}")

        if self.test_type == 'mann_whitney':
            return self._calculate_mann_whitney(effect_size, alpha, power, n, solve_for)
        elif self.test_type == 'wilcoxon':
            return self._calculate_wilcoxon(effect_size, alpha, power, n, solve_for)
        elif self.test_type == 'kruskal_wallis':
            return self._calculate_kruskal_wallis(effect_size, alpha, power, n, solve_for, n_groups)
        else:  # friedman
            return self._calculate_friedman(effect_size, alpha, power, n, solve_for, n_groups)

    def _calculate_mann_whitney(self, effect_size, alpha, power, n, solve_for):
        """Mann-Whitney U test (non-parametric independent t-test)."""

        if solve_for == 'n':
            # Start with parametric sample size, then adjust for efficiency
            # Using formula for independent t-test
            z_alpha = stats.norm.ppf(1 - alpha / 2)
            z_beta = stats.norm.ppf(power or 0.80)

            # Parametric n per group
            n_parametric = int(np.ceil(2 * ((z_alpha + z_beta) / effect_size) ** 2))

            # Adjust for ARE (need slightly more sample)
            n_per_group = int(np.ceil(n_parametric / self.ARE['mann_whitney']))

            return {
                'n_per_group': n_per_group,
                'total_n': n_per_group * 2,
                'effect_size': effect_size,
                'alpha': alpha,
                'power': power or 0.80,
                'test_type': 'Mann-Whitney U',
                'parametric_equivalent': 'Independent t-test',
                'efficiency': f'{self.ARE["mann_whitney"]:.1%} (vs t-test)',
                'note': 'Use when assumptions for t-test are violated (non-normal, ordinal data)'
            }

        elif solve_for == 'power':
            # Estimate power given sample size
            # Approximate using parametric formula adjusted for ARE
            adjusted_n = int(n * self.ARE['mann_whitney'])
            z_alpha = stats.norm.ppf(1 - alpha / 2)
            z = effect_size * np.sqrt(adjusted_n / 2) - z_alpha
            estimated_power = stats.norm.cdf(z)

            return {
                'power': max(0.05, min(0.99, estimated_power)),
                'n_per_group': n,
                'total_n': n * 2,
                'effect_size': effect_size,
                'alpha': alpha,
                'test_type': 'Mann-Whitney U'
            }

        else:  # solve_for effect_size
            # Reverse calculation
            z_alpha = stats.norm.ppf(1 - alpha / 2)
            z_beta = stats.norm.ppf(power or 0.80)
            adjusted_n = int(n * self.ARE['mann_whitney'])
            effect_size = (z_alpha + z_beta) / np.sqrt(adjusted_n / 2)

            return {
                'effect_size': effect_size,
                'n_per_group': n,
                'total_n': n * 2,
                'alpha': alpha,
                'power': power or 0.80,
                'test_type': 'Mann-Whitney U'
            }

    def _calculate_wilcoxon(self, effect_size, alpha, power, n, solve_for):
        """Wilcoxon signed-rank test (non-parametric paired t-test)."""

        if solve_for == 'n':
            # Paired test formula
            z_alpha = stats.norm.ppf(1 - alpha / 2)
            z_beta = stats.norm.ppf(power or 0.80)

            # Parametric paired n
            n_parametric = int(np.ceil(((z_alpha + z_beta) / effect_size) ** 2))

            # Adjust for ARE
            required_n = int(np.ceil(n_parametric / self.ARE['wilcoxon']))

            return {
                'n': required_n,
                'effect_size': effect_size,
                'alpha': alpha,
                'power': power or 0.80,
                'test_type': 'Wilcoxon signed-rank',
                'parametric_equivalent': 'Paired t-test',
                'efficiency': f'{self.ARE["wilcoxon"]:.1%} (vs paired t-test)',
                'note': 'Paired observations (same subjects, before/after)'
            }

        elif solve_for == 'power':
            adjusted_n = int(n * self.ARE['wilcoxon'])
            z_alpha = stats.norm.ppf(1 - alpha / 2)
            z = effect_size * np.sqrt(adjusted_n) - z_alpha
            estimated_power = stats.norm.cdf(z)

            return {
                'power': max(0.05, min(0.99, estimated_power)),
                'n': n,
                'effect_size': effect_size,
                'alpha': alpha,
                'test_type': 'Wilcoxon signed-rank'
            }

        else:
            z_alpha = stats.norm.ppf(1 - alpha / 2)
            z_beta = stats.norm.ppf(power or 0.80)
            adjusted_n = int(n * self.ARE['wilcoxon'])
            effect_size = (z_alpha + z_beta) / np.sqrt(adjusted_n)

            return {
                'effect_size': effect_size,
                'n': n,
                'alpha': alpha,
                'power': power or 0.80,
                'test_type': 'Wilcoxon signed-rank'
            }

    def _calculate_kruskal_wallis(self, effect_size, alpha, power, n, solve_for, n_groups):
        """Kruskal-Wallis H test (non-parametric ANOVA)."""

        if solve_for == 'n':
            # ANOVA formula
            df1 = n_groups - 1
            df2_target = 100  # Approximate

            # Using F-distribution approximation
            f_crit = stats.f.ppf(1 - alpha, df1, df2_target)
            ncp = effect_size ** 2 * (n_groups * 50)  # Approximate NCP

            # Target power
            target_power = power or 0.80

            # Iterate to find required n per group
            for n_per_group in range(20, 1000):
                df2 = n_groups * n_per_group - n_groups
                ncp_actual = effect_size ** 2 * n_groups * n_per_group
                power_actual = 1 - stats.ncf.cdf(f_crit, df1, df2, ncp_actual)
                if power_actual >= target_power:
                    break

            # Adjust for ARE
            n_per_group = int(np.ceil(n_per_group / self.ARE['kruskal_wallis']))

            return {
                'n_per_group': n_per_group,
                'total_n': n_per_group * n_groups,
                'effect_size': effect_size,
                'alpha': alpha,
                'power': power or 0.80,
                'n_groups': n_groups,
                'test_type': 'Kruskal-Wallis H',
                'parametric_equivalent': 'One-way ANOVA',
                'efficiency': f'{self.ARE["kruskal_wallis"]:.1%} (vs ANOVA)',
                'note': 'Use when ANOVA assumptions violated (non-normal, ordinal data)'
            }

        elif solve_for == 'power':
            df1 = n_groups - 1
            df2 = n_groups * n - n_groups
            adjusted_n = int(n * self.ARE['kruskal_wallis'])
            ncp = effect_size ** 2 * n_groups * adjusted_n
            f_crit = stats.f.ppf(1 - alpha, df1, df2)
            estimated_power = 1 - stats.ncf.cdf(f_crit, df1, df2, ncp)

            return {
                'power': max(0.05, min(0.99, estimated_power)),
                'n_per_group': n,
                'total_n': n * n_groups,
                'effect_size': effect_size,
                'alpha': alpha,
                'n_groups': n_groups,
                'test_type': 'Kruskal-Wallis H'
            }

        else:
            return {
                'effect_size': 0.25,  # Medium effect
                'n_per_group': n,
                'total_n': n * n_groups,
                'alpha': alpha,
                'power': power or 0.80,
                'note': 'Cohen\'s f: Small=0.10, Medium=0.25, Large=0.40'
            }

    def _calculate_friedman(self, effect_size, alpha, power, n, solve_for, n_groups):
        """Friedman test (non-parametric repeated measures ANOVA)."""

        if solve_for == 'n':
            # Repeated measures formula (conservative estimate)
            df1 = n_groups - 1
            target_power = power or 0.80

            # Iterate to find required n
            for required_n in range(10, 500):
                df2 = (required_n - 1) * df1
                ncp = effect_size ** 2 * required_n * n_groups
                f_crit = stats.f.ppf(1 - alpha, df1, df2)
                power_actual = 1 - stats.ncf.cdf(f_crit, df1, df2, ncp)
                if power_actual >= target_power:
                    break

            # Adjust for ARE
            required_n = int(np.ceil(required_n / self.ARE['friedman']))

            return {
                'n': required_n,
                'effect_size': effect_size,
                'alpha': alpha,
                'power': power or 0.80,
                'n_groups': n_groups,
                'test_type': 'Friedman test',
                'parametric_equivalent': 'Repeated measures ANOVA',
                'efficiency': f'{self.ARE["friedman"]:.1%} (vs RM-ANOVA)',
                'note': 'Repeated measurements on same subjects'
            }

        elif solve_for == 'power':
            df1 = n_groups - 1
            df2 = (n - 1) * df1
            adjusted_n = int(n * self.ARE['friedman'])
            ncp = effect_size ** 2 * adjusted_n * n_groups
            f_crit = stats.f.ppf(1 - alpha, df1, df2)
            estimated_power = 1 - stats.ncf.cdf(f_crit, df1, df2, ncp)

            return {
                'power': max(0.05, min(0.99, estimated_power)),
                'n': n,
                'effect_size': effect_size,
                'alpha': alpha,
                'n_groups': n_groups,
                'test_type': 'Friedman test'
            }

        else:
            return {
                'effect_size': 0.25,
                'n': n,
                'alpha': alpha,
                'power': power or 0.80,
                'note': 'Cohen\'s f: Small=0.10, Medium=0.25, Large=0.40'
            }

    @staticmethod
    def effect_size_guidelines() -> Dict[str, float]:
        """Return effect size guidelines (same as parametric equivalents)."""
        return {
            'small': 0.2,
            'medium': 0.5,
            'large': 0.8,
            'note': 'Cohen\'s d for Mann-Whitney/Wilcoxon, Cohen\'s f for Kruskal-Wallis/Friedman'
        }
