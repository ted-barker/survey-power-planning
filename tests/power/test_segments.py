"""
Tests for segment-based power calculator (LCA analysis)
"""

import pytest
import numpy as np
from src.power.calculators.segments import SegmentPowerCalc


class TestSegmentPowerCalcInit:
    """Tests for segment calculator initialization"""

    def test_init_valid(self):
        """Test initialization with valid parameters"""
        calc = SegmentPowerCalc(
            n_segments=3,
            prevalence=[0.40, 0.40, 0.20],
            test_type='anova'
        )

        assert calc.n_segments == 3
        assert calc.prevalence == [0.40, 0.40, 0.20]
        assert calc.test_type == 'anova'

    def test_init_prevalence_sum_not_one(self):
        """Test error when prevalence doesn't sum to 1.0"""
        with pytest.raises(ValueError, match="must sum to 1.0"):
            SegmentPowerCalc(
                n_segments=3,
                prevalence=[0.40, 0.40, 0.10],  # Sums to 0.90
                test_type='anova'
            )

    def test_init_prevalence_length_mismatch(self):
        """Test error when prevalence length doesn't match n_segments"""
        with pytest.raises(ValueError, match="must have 3 elements"):
            SegmentPowerCalc(
                n_segments=3,
                prevalence=[0.50, 0.50],  # Only 2 elements
                test_type='anova'
            )

    def test_init_negative_prevalence(self):
        """Test error with negative prevalence"""
        with pytest.raises(ValueError, match="must be > 0"):
            SegmentPowerCalc(
                n_segments=3,
                prevalence=[0.50, 0.60, -0.10],  # Negative value
                test_type='anova'
            )

    def test_init_too_few_segments(self):
        """Test error with less than 2 segments"""
        with pytest.raises(ValueError, match="must be at least 2"):
            SegmentPowerCalc(
                n_segments=1,
                prevalence=[1.0],
                test_type='anova'
            )


class TestSegmentPowerCalcANOVA:
    """Tests for segment ANOVA analysis"""

    def test_solve_n_balanced_segments(self):
        """Test solving for n with balanced segments"""
        calc = SegmentPowerCalc(
            n_segments=3,
            prevalence=[0.33, 0.33, 0.34],
            test_type='anova'
        )

        result = calc.calculate(
            effect_size=0.25,  # Cohen's f
            alpha=0.05,
            power=0.80,
            solve_for='n'
        )

        assert result['solve_for'] == 'n'
        assert result['total_n'] > 0
        assert len(result['n_per_segment']) == 3
        assert sum(result['n_per_segment']) >= result['total_n']

    def test_solve_n_unbalanced_segments(self):
        """Test solving for n with unbalanced segments"""
        calc = SegmentPowerCalc(
            n_segments=3,
            prevalence=[0.40, 0.40, 0.20],  # One smaller segment
            test_type='anova'
        )

        result = calc.calculate(
            effect_size=0.25,
            alpha=0.05,
            power=0.80,
            solve_for='n'
        )

        assert result['n_per_segment'][0] == result['n_per_segment'][1]  # First two equal
        assert result['n_per_segment'][2] < result['n_per_segment'][0]  # Third smaller

    def test_solve_power_given_n(self):
        """Test solving for power given sample size"""
        calc = SegmentPowerCalc(
            n_segments=3,
            prevalence=[0.40, 0.40, 0.20],
            test_type='anova'
        )

        result = calc.calculate(
            total_n=500,
            effect_size=0.25,
            alpha=0.05,
            solve_for='power'
        )

        assert result['solve_for'] == 'power'
        assert result['total_n'] == 500
        assert 0 < result['power'] < 1
        assert len(result['n_per_segment']) == 3

    def test_solve_effect_size_given_n_power(self):
        """Test solving for effect size given n and power"""
        calc = SegmentPowerCalc(
            n_segments=3,
            prevalence=[0.40, 0.40, 0.20],
            test_type='anova'
        )

        result = calc.calculate(
            total_n=500,
            alpha=0.05,
            power=0.80,
            solve_for='effect_size'
        )

        assert result['solve_for'] == 'effect_size'
        assert result['effect_size'] > 0


class TestSegmentPowerCalcPairwise:
    """Tests for pairwise segment comparisons"""

    def test_pairwise_bonferroni_adjustment(self):
        """Test that pairwise comparisons account for multiple testing"""
        calc = SegmentPowerCalc(
            n_segments=3,
            prevalence=[0.33, 0.33, 0.34],
            test_type='pairwise'
        )

        result = calc.calculate(
            effect_size=0.5,
            alpha=0.05,
            power=0.80,
            solve_for='n'
        )

        # Pairwise with Bonferroni should need more samples than ANOVA
        calc_anova = SegmentPowerCalc(
            n_segments=3,
            prevalence=[0.33, 0.33, 0.34],
            test_type='anova'
        )

        result_anova = calc_anova.calculate(
            effect_size=0.25,  # Convert d to f: f ≈ d/2
            alpha=0.05,
            power=0.80,
            solve_for='n'
        )

        assert result['total_n'] > result_anova['total_n']


class TestSegmentPowerCalcRegression:
    """Tests for regression with segment predictor"""

    def test_regression_segments_as_predictor(self):
        """Test using segments as categorical predictor"""
        calc = SegmentPowerCalc(
            n_segments=3,
            prevalence=[0.40, 0.40, 0.20],
            test_type='regression'
        )

        result = calc.calculate(
            effect_size=0.15,  # f²
            alpha=0.05,
            power=0.80,
            solve_for='n'
        )

        assert result['test_type'] == 'regression'
        assert result['total_n'] > 0


class TestMinimumSegmentSize:
    """Tests for minimum segment size constraints"""

    def test_min_segment_n_constraint(self):
        """Test minimum segment size constraint"""
        calc = SegmentPowerCalc(
            n_segments=3,
            prevalence=[0.40, 0.40, 0.20],
            test_type='anova'
        )

        result = calc.calculate(
            effect_size=0.25,
            alpha=0.05,
            power=0.80,
            solve_for='n',
            min_segment_n=50  # Require at least 50 per segment
        )

        # All segments should have at least 50
        assert all(n >= 50 for n in result['n_per_segment'])

    def test_small_segment_warning(self):
        """Test warning for small segment sizes"""
        calc = SegmentPowerCalc(
            n_segments=3,
            prevalence=[0.40, 0.40, 0.20],
            test_type='anova'
        )

        result = calc.calculate(
            total_n=100,  # Small total n
            effect_size=0.25,
            alpha=0.05,
            solve_for='power'
        )

        # Should have warning about small segments
        assert len(result['warnings']) > 0


class TestAllocationUtilities:
    """Tests for sample allocation utilities"""

    def test_balanced_allocation(self):
        """Test balanced allocation based on prevalence"""
        calc = SegmentPowerCalc(
            n_segments=3,
            prevalence=[0.40, 0.40, 0.20],
            test_type='anova'
        )

        allocation = calc.get_balanced_allocation(total_n=500)

        assert allocation['total_n_requested'] == 500
        assert len(allocation['n_per_segment']) == 3
        # Check proportions are roughly correct
        assert 180 <= allocation['n_per_segment'][0] <= 220  # ~40% of 500 = 200
        assert 180 <= allocation['n_per_segment'][1] <= 220
        assert 80 <= allocation['n_per_segment'][2] <= 120   # ~20% of 500 = 100

    def test_validate_prevalence_warnings(self):
        """Test prevalence validation with warnings"""
        calc = SegmentPowerCalc(
            n_segments=3,
            prevalence=[0.85, 0.10, 0.05],  # Very unbalanced
            test_type='anova'
        )

        validation = calc.validate_prevalence()

        assert validation['prevalence_sum'] == 1.0
        assert len(validation['warnings']) > 0  # Should warn about imbalance


class TestEdgeCases:
    """Tests for edge cases"""

    def test_two_segments_equal(self):
        """Test with 2 segments (simplest case)"""
        calc = SegmentPowerCalc(
            n_segments=2,
            prevalence=[0.50, 0.50],
            test_type='anova'
        )

        result = calc.calculate(
            effect_size=0.25,
            alpha=0.05,
            power=0.80,
            solve_for='n'
        )

        assert result['n_segments'] == 2
        assert len(result['n_per_segment']) == 2

    def test_many_segments(self):
        """Test with many segments"""
        calc = SegmentPowerCalc(
            n_segments=5,
            prevalence=[0.20, 0.20, 0.20, 0.20, 0.20],
            test_type='anova'
        )

        result = calc.calculate(
            effect_size=0.25,
            alpha=0.05,
            power=0.80,
            solve_for='n'
        )

        assert result['n_segments'] == 5
        assert len(result['n_per_segment']) == 5

    def test_floating_point_prevalence_sum(self):
        """Test that floating point rounding is handled"""
        # This should be valid despite floating point precision
        calc = SegmentPowerCalc(
            n_segments=3,
            prevalence=[0.333, 0.333, 0.334],  # Sum is 1.0 within tolerance
            test_type='anova'
        )

        assert calc.n_segments == 3
