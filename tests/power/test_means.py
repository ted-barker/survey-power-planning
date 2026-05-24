"""
Tests for means power calculator (t-tests, ANOVA)
"""

import pytest
import numpy as np
from src.power.calculators.means import MeansPowerCalc


class TestMeansPowerCalcIndependent:
    """Tests for independent t-test power calculations"""

    def test_init(self):
        """Test calculator initialization"""
        calc = MeansPowerCalc(test_type='independent')
        assert calc.test_type == 'independent'

    def test_init_invalid_type(self):
        """Test initialization with invalid test type"""
        with pytest.raises(ValueError):
            MeansPowerCalc(test_type='invalid')

    def test_solve_n_medium_effect(self):
        """Test solving for n with medium effect size"""
        calc = MeansPowerCalc(test_type='independent')
        result = calc.calculate(
            effect_size=0.5,  # Medium effect
            alpha=0.05,
            power=0.80,
            solve_for='n'
        )

        assert result['solve_for'] == 'n'
        assert result['n_per_group'] == 64  # Known value for d=0.5, power=0.80
        assert result['total_n'] == 128
        assert result['effect_size'] == 0.5
        assert result['power'] == 0.80

    def test_solve_power_given_n(self):
        """Test solving for power given sample size"""
        calc = MeansPowerCalc(test_type='independent')
        result = calc.calculate(
            effect_size=0.5,
            alpha=0.05,
            n=64,
            solve_for='power'
        )

        assert result['solve_for'] == 'power'
        assert result['n_per_group'] == 64
        assert 0.79 < result['power'] < 0.81  # Should be ~0.80

    def test_solve_effect_size_given_n_power(self):
        """Test solving for effect size given n and power"""
        calc = MeansPowerCalc(test_type='independent')
        result = calc.calculate(
            n=64,
            alpha=0.05,
            power=0.80,
            solve_for='effect_size'
        )

        assert result['solve_for'] == 'effect_size'
        assert 0.49 < result['effect_size'] < 0.51  # Should be ~0.5

    def test_unequal_groups_ratio(self):
        """Test with unequal group sizes"""
        calc = MeansPowerCalc(test_type='independent')
        result = calc.calculate(
            effect_size=0.5,
            alpha=0.05,
            power=0.80,
            solve_for='n',
            ratio=2.0  # Group 2 is twice the size of Group 1
        )

        assert result['ratio'] == 2.0
        assert result['total_n'] > 128  # Needs more than equal groups

    def test_missing_params_error(self):
        """Test error when required parameters missing"""
        calc = MeansPowerCalc(test_type='independent')

        with pytest.raises(ValueError):
            calc.calculate(solve_for='n', alpha=0.05)  # Missing effect_size and power


class TestMeansPowerCalcPaired:
    """Tests for paired t-test power calculations"""

    def test_solve_n_paired(self):
        """Test solving for n in paired t-test"""
        calc = MeansPowerCalc(test_type='paired')
        result = calc.calculate(
            effect_size=0.5,
            alpha=0.05,
            power=0.80,
            solve_for='n'
        )

        assert result['test_type'] == 'paired_ttest'
        assert result['n_pairs'] == 34  # Paired design needs fewer pairs


class TestMeansPowerCalcANOVA:
    """Tests for ANOVA power calculations"""

    def test_solve_n_anova_3_groups(self):
        """Test solving for n in one-way ANOVA with 3 groups"""
        calc = MeansPowerCalc(test_type='anova')
        result = calc.calculate(
            effect_size=0.25,  # Cohen's f
            alpha=0.05,
            power=0.80,
            solve_for='n',
            n_groups=3
        )

        assert result['test_type'] == 'anova'
        assert result['n_groups'] == 3
        assert result['total_n'] > 0
        assert result['df_num'] == 2  # n_groups - 1

    def test_missing_n_groups_error(self):
        """Test error when n_groups not provided for ANOVA"""
        calc = MeansPowerCalc(test_type='anova')

        with pytest.raises(ValueError):
            calc.calculate(
                effect_size=0.25,
                alpha=0.05,
                power=0.80,
                solve_for='n'
            )


class TestEffectSizeConversion:
    """Tests for effect size conversion utilities"""

    def test_get_guidelines(self):
        """Test effect size guidelines"""
        calc = MeansPowerCalc(test_type='independent')
        guidelines = calc.get_effect_size_guidelines()

        assert 'small' in guidelines
        assert 'medium' in guidelines
        assert 'large' in guidelines
        assert guidelines['small'] == 0.2
        assert guidelines['medium'] == 0.5
        assert guidelines['large'] == 0.8

    def test_convert_d_to_r(self):
        """Test converting Cohen's d to correlation r"""
        calc = MeansPowerCalc(test_type='independent')

        # d = 0.5 should give r ≈ 0.24
        r = calc.convert_effect_size(from_metric='d', to_metric='r', value=0.5)
        assert 0.23 < r < 0.25

    def test_convert_r_to_d(self):
        """Test converting correlation r to Cohen's d"""
        calc = MeansPowerCalc(test_type='independent')

        # r = 0.24 should give d ≈ 0.5
        d = calc.convert_effect_size(from_metric='r', to_metric='d', value=0.24)
        assert 0.48 < d < 0.52

    def test_convert_d_to_f(self):
        """Test converting Cohen's d to Cohen's f"""
        calc = MeansPowerCalc(test_type='independent')

        # d = 0.5 → f = 0.25
        f = calc.convert_effect_size(from_metric='d', to_metric='f', value=0.5)
        assert 0.24 < f < 0.26


class TestAlternativeHypotheses:
    """Tests for one-sided tests"""

    def test_one_sided_larger(self):
        """Test one-sided test (alternative='larger')"""
        calc = MeansPowerCalc(test_type='independent')
        result = calc.calculate(
            effect_size=0.5,
            alpha=0.05,
            power=0.80,
            solve_for='n',
            alternative='larger'
        )

        assert result['alternative'] == 'larger'
        # One-sided test needs fewer samples
        assert result['n_per_group'] < 64

    def test_one_sided_smaller(self):
        """Test one-sided test (alternative='smaller')"""
        calc = MeansPowerCalc(test_type='independent')
        result = calc.calculate(
            effect_size=0.5,
            alpha=0.05,
            power=0.80,
            solve_for='n',
            alternative='smaller'
        )

        assert result['alternative'] == 'smaller'
        assert result['n_per_group'] < 64
