"""
Survey design optimizer

Iteratively improve survey to reduce drop-off while maintaining power
"""

from typing import Dict, List, Optional, Callable
import numpy as np


class DesignOptimizer:
    """
    Optimize survey design to minimize invitations while maintaining power.

    Workflow:
    1. Run power analysis → determine required completes
    2. Run fatigue audit → estimate drop-off
    3. Calculate invitations needed
    4. If too high, suggest design improvements
    5. Re-run audit with improvements → re-calculate invitations
    6. Iterate until acceptable
    """

    def __init__(
        self,
        power_calculator,
        power_params: Dict,
        fatigue_calculator: Optional[Callable] = None,
    ):
        """
        Initialize optimizer.

        Args:
            power_calculator: Power calculator instance
            power_params: Parameters for power calculation
            fatigue_calculator: Function that takes survey and returns fatigue score
        """
        self.power_calculator = power_calculator
        self.power_params = power_params
        self.fatigue_calculator = fatigue_calculator

    def optimize(
        self,
        initial_fatigue_score: float,
        max_invitations: Optional[int] = None,
        target_dropoff: Optional[float] = None,
        response_rate: float = 1.0,
    ) -> Dict:
        """
        Optimize survey design to meet constraints.

        Args:
            initial_fatigue_score: Starting fatigue score
            max_invitations: Maximum invitations available (optional constraint)
            target_dropoff: Target drop-off rate (optional constraint)
            response_rate: Expected response rate

        Returns:
            Optimization results with recommendations
        """
        from .dropoff import (
            estimate_dropoff_from_score,
            calculate_invitations,
            integrated_sample_plan,
        )

        # Calculate required completes from power analysis
        power_result = self.power_calculator.calculate(**self.power_params)

        if 'total_n' in power_result:
            required_n = power_result['total_n']
        elif 'n' in power_result:
            required_n = power_result['n']
        else:
            required_n = power_result.get('n_per_group', 100)

        # Initial state
        initial_dropoff = estimate_dropoff_from_score(initial_fatigue_score)
        initial_invitations = calculate_invitations(
            required_n, initial_dropoff, response_rate
        )['invitations_needed']

        # Check if optimization needed
        needs_optimization = False
        constraints_violated = []

        if max_invitations and initial_invitations > max_invitations:
            needs_optimization = True
            constraints_violated.append(
                f"Invitations needed ({initial_invitations}) exceeds maximum ({max_invitations})"
            )

        if target_dropoff and initial_dropoff > target_dropoff:
            needs_optimization = True
            constraints_violated.append(
                f"Drop-off rate ({initial_dropoff:.1%}) exceeds target ({target_dropoff:.1%})"
            )

        # Generate optimization scenarios
        scenarios = self._generate_scenarios(
            initial_fatigue_score,
            required_n,
            response_rate,
            max_invitations,
            target_dropoff,
        )

        return {
            'initial_state': {
                'fatigue_score': initial_fatigue_score,
                'dropoff_rate': initial_dropoff,
                'required_completes': required_n,
                'invitations_needed': initial_invitations,
            },
            'needs_optimization': needs_optimization,
            'constraints_violated': constraints_violated,
            'optimization_scenarios': scenarios,
            'best_scenario': scenarios[0] if scenarios else None,
        }

    def _generate_scenarios(
        self,
        initial_score: float,
        required_n: int,
        response_rate: float,
        max_invitations: Optional[int],
        target_dropoff: Optional[float],
    ) -> List[Dict]:
        """Generate optimization scenarios with different fatigue reductions."""
        from .dropoff import estimate_dropoff_from_score, calculate_invitations

        scenarios = []

        # Try different levels of fatigue reduction
        reductions = [10, 20, 30, 40, 50]  # Points to reduce

        for reduction in reductions:
            new_score = max(0, initial_score - reduction)
            new_dropoff = estimate_dropoff_from_score(new_score)
            new_invitations = calculate_invitations(
                required_n, new_dropoff, response_rate
            )['invitations_needed']

            # Check if this scenario meets constraints
            meets_constraints = True
            if max_invitations and new_invitations > max_invitations:
                meets_constraints = False
            if target_dropoff and new_dropoff > target_dropoff:
                meets_constraints = False

            scenarios.append({
                'fatigue_reduction': reduction,
                'new_fatigue_score': new_score,
                'new_dropoff_rate': new_dropoff,
                'new_invitations_needed': new_invitations,
                'invitations_saved': calculate_invitations(
                    required_n, estimate_dropoff_from_score(initial_score), response_rate
                )['invitations_needed'] - new_invitations,
                'meets_constraints': meets_constraints,
                'effort_level': self._estimate_effort(reduction),
            })

        # Sort by invitations saved (most savings first)
        scenarios.sort(key=lambda x: x['invitations_saved'], reverse=True)

        return scenarios

    def _estimate_effort(self, fatigue_reduction: int) -> str:
        """Estimate implementation effort for fatigue reduction."""
        if fatigue_reduction <= 15:
            return "Low (minor tweaks)"
        elif fatigue_reduction <= 30:
            return "Medium (moderate changes)"
        else:
            return "High (major redesign)"


def optimize_survey_design(
    power_result: Dict,
    fatigue_score: float,
    response_rate: float = 1.0,
    max_invitations: Optional[int] = None,
    target_dropoff: Optional[float] = None,
) -> Dict:
    """
    Simplified optimizer function.

    Args:
        power_result: Result from power calculator
        fatigue_score: Current fatigue score
        response_rate: Expected response rate
        max_invitations: Maximum invitations constraint
        target_dropoff: Target drop-off rate constraint

    Returns:
        Optimization recommendations
    """
    from .dropoff import (
        estimate_dropoff_from_score,
        calculate_invitations,
        get_risk_level,
    )

    # Extract required n
    if 'total_n' in power_result:
        required_n = power_result['total_n']
    elif 'n' in power_result:
        required_n = power_result['n']
    else:
        required_n = power_result.get('n_per_group', 100)

    # Current state
    current_dropoff = estimate_dropoff_from_score(fatigue_score)
    current_invitations = calculate_invitations(
        required_n, current_dropoff, response_rate
    )['invitations_needed']

    # Determine if optimization is needed
    needs_optimization = False
    issues = []

    if max_invitations and current_invitations > max_invitations:
        needs_optimization = True
        issues.append(
            f"Current design requires {current_invitations} invitations, "
            f"exceeds budget of {max_invitations}"
        )

    if target_dropoff and current_dropoff > target_dropoff:
        needs_optimization = True
        issues.append(
            f"Current drop-off rate ({current_dropoff:.1%}) exceeds "
            f"target ({target_dropoff:.1%})"
        )

    if fatigue_score > 50:
        needs_optimization = True
        issues.append(
            f"High fatigue score ({fatigue_score:.0f}/100) will lead to "
            f"poor data quality and high drop-off"
        )

    # Generate improvement scenarios
    scenarios = []

    # Scenario 1: Reduce to MODERATE risk (score = 50)
    if fatigue_score > 50:
        target_score = 50
        target_dropoff_rate = estimate_dropoff_from_score(target_score)
        target_invitations = calculate_invitations(
            required_n, target_dropoff_rate, response_rate
        )['invitations_needed']

        scenarios.append({
            'name': 'Reduce to Moderate Risk',
            'target_fatigue_score': target_score,
            'fatigue_reduction': fatigue_score - target_score,
            'new_dropoff_rate': target_dropoff_rate,
            'new_invitations': target_invitations,
            'invitations_saved': current_invitations - target_invitations,
            'effort': 'Medium to High',
            'actions': [
                'Reduce loop iterations to 2 maximum',
                'Remove open-ended questions from loops',
                'Simplify or remove large matrix grids',
                'Add skip logic to reduce effective question count',
            ],
        })

    # Scenario 2: Reduce to LOW risk (score = 25)
    if fatigue_score > 25:
        target_score = 25
        target_dropoff_rate = estimate_dropoff_from_score(target_score)
        target_invitations = calculate_invitations(
            required_n, target_dropoff_rate, response_rate
        )['invitations_needed']

        scenarios.append({
            'name': 'Reduce to Low Risk',
            'target_fatigue_score': target_score,
            'fatigue_reduction': fatigue_score - target_score,
            'new_dropoff_rate': target_dropoff_rate,
            'new_invitations': target_invitations,
            'invitations_saved': current_invitations - target_invitations,
            'effort': 'High',
            'actions': [
                'Remove all loops or limit to 1 iteration',
                'Convert grids to single-choice questions',
                'Remove all open-ended questions except 1-2 critical ones',
                'Aggressive skip logic throughout',
                'Randomize question order to reduce fatigue concentration',
            ],
        })

    # Scenario 3: Incremental improvement (10% dropoff reduction)
    if current_dropoff > 0.10:
        # Find score that gives 10% lower dropoff
        target_dropoff_rate = current_dropoff * 0.9
        # Reverse engineer fatigue score (approximate)
        if target_dropoff_rate <= 0.15:
            target_score = (target_dropoff_rate - 0.05) / 0.10 * 25
        elif target_dropoff_rate <= 0.25:
            target_score = 25 + (target_dropoff_rate - 0.15) / 0.10 * 25
        elif target_dropoff_rate <= 0.40:
            target_score = 50 + (target_dropoff_rate - 0.25) / 0.15 * 25
        else:
            target_score = 75 + (target_dropoff_rate - 0.40) / 0.20 * 25

        target_invitations = calculate_invitations(
            required_n, target_dropoff_rate, response_rate
        )['invitations_needed']

        scenarios.append({
            'name': 'Incremental Improvement',
            'target_fatigue_score': target_score,
            'fatigue_reduction': fatigue_score - target_score,
            'new_dropoff_rate': target_dropoff_rate,
            'new_invitations': target_invitations,
            'invitations_saved': current_invitations - target_invitations,
            'effort': 'Low to Medium',
            'actions': [
                'Reduce one loop by 1 iteration',
                'Split one large grid into two smaller grids',
                'Move attention check to earlier position',
                'Add progress bar to manage perceived effort',
            ],
        })

    return {
        'current_state': {
            'fatigue_score': fatigue_score,
            'risk_level': get_risk_level(fatigue_score),
            'dropoff_rate': current_dropoff,
            'required_completes': required_n,
            'invitations_needed': current_invitations,
        },
        'needs_optimization': needs_optimization,
        'issues': issues,
        'optimization_scenarios': scenarios,
        'recommendation': scenarios[0] if scenarios else None,
    }
