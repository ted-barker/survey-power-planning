"""
Power Analysis and Sample Size Calculation Module

Provides statistical power calculations for:
- Means tests (t-tests, ANOVA)
- Regression analysis (simple, multiple, moderation)
- Proportions and chi-square tests
- Segment analysis (LCA-based)
- Integration with survey fatigue audit for drop-off estimation
"""

from .calculators.means import MeansPowerCalc
from .calculators.regression import RegressionPowerCalc
from .calculators.proportions import ProportionsPowerCalc
from .calculators.segments import SegmentPowerCalc

__all__ = [
    'MeansPowerCalc',
    'RegressionPowerCalc',
    'ProportionsPowerCalc',
    'SegmentPowerCalc',
]
