"""
Drop-off estimation and invitation calculation

Links power analysis to survey fatigue audit or direct drop-off rate specification
"""

from typing import Dict, Optional
import numpy as np


def estimate_dropoff_from_score(fatigue_score: float) -> float:
    """
    Estimate drop-off rate from fatigue score.

    Based on empirical relationship:
    - Low fatigue (0-25): 5-15% drop-off
    - Moderate fatigue (26-50): 15-25% drop-off
    - High fatigue (51-75): 25-40% drop-off
    - Extreme fatigue (76-100): 40-60% drop-off

    Args:
        fatigue_score: Fatigue score from survey audit (0-100)

    Returns:
        Estimated drop-off rate (0.0-1.0)
    """
    if not 0 <= fatigue_score <= 100:
        raise ValueError("fatigue_score must be between 0 and 100")

    # Piecewise linear function
    if fatigue_score <= 25:
        # Low: 5% to 15%
        dropoff = 0.05 + (fatigue_score / 25) * 0.10
    elif fatigue_score <= 50:
        # Moderate: 15% to 25%
        dropoff = 0.15 + ((fatigue_score - 25) / 25) * 0.10
    elif fatigue_score <= 75:
        # High: 25% to 40%
        dropoff = 0.25 + ((fatigue_score - 50) / 25) * 0.15
    else:
        # Extreme: 40% to 60%
        dropoff = 0.40 + ((fatigue_score - 75) / 25) * 0.20

    return min(dropoff, 0.60)  # Cap at 60%


def calculate_invitations(
    required_completes: int,
    dropoff_rate: float,
    ctr: float = 1.0,
    response_rate: float = 1.0,
    buffer: float = 0.0,
) -> Dict[str, float]:
    """
    Calculate number of invitations needed given full survey funnel.

    Survey Funnel:
        Invitations → Clicks (CTR) → Starts (response_rate) → Completions (1 - dropoff_rate)

    Formula:
        invitations = required_completes / (CTR * response_rate * (1 - dropoff_rate) * (1 + buffer))

    Args:
        required_completes: Number of complete responses needed (from power analysis)
        dropoff_rate: Expected drop-off rate (0.0-1.0) - % who start but don't finish
        ctr: Click-through rate (0.0-1.0, default 1.0) - % who click invitation link
        response_rate: Expected response rate (0.0-1.0, default 1.0) - % who start after clicking
        buffer: Safety buffer (default 0.0 = no buffer, 0.1 = 10% buffer)

    Returns:
        Dictionary with:
        - required_completes: Input value
        - dropoff_rate: Input drop-off rate
        - ctr: Click-through rate
        - response_rate: Response rate
        - buffer: Safety buffer
        - effective_rate: Combined completion rate (CTR × response × completion)
        - invitations_needed: Number of invitations to send
        - expected_clicks: Expected clicks from invitations
        - expected_starts: Expected survey starts
        - expected_completes: Expected number of completes
        - buffer_completes: Extra completes from buffer

    Examples:
        # Need 200 completes, 30% drop-off, 40% CTR
        calculate_invitations(200, dropoff_rate=0.30, ctr=0.40)
        # Returns: invitations_needed = 715
        # (40% click → 286 starts → 70% complete → 200 completes)

        # Need 200 completes, 30% drop-off, 40% CTR, 10% buffer
        calculate_invitations(200, dropoff_rate=0.30, ctr=0.40, buffer=0.10)
        # Returns: invitations_needed = 787
    """
    if not 0 <= dropoff_rate <= 1:
        raise ValueError("dropoff_rate must be between 0 and 1")
    if not 0 < ctr <= 1:
        raise ValueError("ctr must be between 0 and 1")
    if not 0 < response_rate <= 1:
        raise ValueError("response_rate must be between 0 and 1")
    if buffer < 0:
        raise ValueError("buffer must be >= 0")

    # Effective completion rate through full funnel
    completion_rate = (1 - dropoff_rate)
    effective_rate = ctr * response_rate * completion_rate

    if effective_rate <= 0:
        raise ValueError("Effective rate too low (funnel rates make completion impossible)")

    # Calculate base invitations needed
    base_invitations = required_completes / effective_rate

    # Add buffer
    invitations_needed = int(np.ceil(base_invitations * (1 + buffer)))

    # Expected outcomes at each funnel stage
    expected_clicks = int(invitations_needed * ctr)
    expected_starts = int(expected_clicks * response_rate)
    expected_completes = int(expected_starts * completion_rate)

    # Extra completes from buffer
    buffer_completes = expected_completes - required_completes

    return {
        'required_completes': required_completes,
        'dropoff_rate': dropoff_rate,
        'ctr': ctr,
        'response_rate': response_rate,
        'buffer': buffer,
        'effective_rate': effective_rate,
        'completion_rate': completion_rate,
        'invitations_needed': invitations_needed,
        'expected_clicks': expected_clicks,
        'expected_starts': expected_starts,
        'expected_completes': expected_completes,
        'buffer_completes': buffer_completes,
    }


def calculate_effective_n(
    total_invitations: int,
    dropoff_rate: float,
    ctr: float = 1.0,
    response_rate: float = 1.0,
) -> Dict[str, int]:
    """
    Calculate expected number of completes given invitation count.

    Inverse of calculate_invitations - useful for "what if" scenarios.

    Args:
        total_invitations: Number of invitations you plan to send
        dropoff_rate: Expected drop-off rate
        ctr: Click-through rate
        response_rate: Expected response rate

    Returns:
        Dictionary with expected outcomes at each funnel stage
    """
    if not 0 <= dropoff_rate <= 1:
        raise ValueError("dropoff_rate must be between 0 and 1")
    if not 0 < ctr <= 1:
        raise ValueError("ctr must be between 0 and 1")
    if not 0 < response_rate <= 1:
        raise ValueError("response_rate must be between 0 and 1")

    # Funnel stages
    expected_clicks = int(total_invitations * ctr)
    expected_starts = int(expected_clicks * response_rate)
    expected_completes = int(expected_starts * (1 - dropoff_rate))
    expected_dropoffs = int(expected_starts * dropoff_rate)

    # Non-participants
    expected_non_clickers = total_invitations - expected_clicks
    expected_non_starters = expected_clicks - expected_starts

    effective_rate = ctr * response_rate * (1 - dropoff_rate)

    return {
        'total_invitations': total_invitations,
        'expected_clicks': expected_clicks,
        'expected_starts': expected_starts,
        'expected_completes': expected_completes,
        'expected_dropoffs': expected_dropoffs,
        'expected_non_clickers': expected_non_clickers,
        'expected_non_starters': expected_non_starters,
        'effective_rate': effective_rate,
    }


def integrated_sample_plan(
    power_result: Dict,
    fatigue_score: Optional[float] = None,
    dropoff_rate: Optional[float] = None,
    ctr: float = 1.0,
    response_rate: float = 1.0,
    buffer: float = 0.0,
) -> Dict:
    """
    Create integrated sample plan combining power analysis and survey funnel.

    Args:
        power_result: Result from power calculator
        fatigue_score: Fatigue score from survey audit (0-100) - DEPRECATED, use dropoff_rate
        dropoff_rate: Expected drop-off rate (0.0-1.0) - direct specification
        ctr: Click-through rate (0.0-1.0, default 1.0 = everyone clicks)
        response_rate: Expected response rate (0.0-1.0, default 1.0)
        buffer: Safety buffer (optional)

    Returns:
        Comprehensive sample plan with full funnel breakdown
    """
    # Extract required completes from power result
    if 'total_n' in power_result:
        required_n = power_result['total_n']
    elif 'n' in power_result:
        required_n = power_result['n']
    elif 'n_per_group' in power_result:
        # For t-tests, might need both groups
        required_n = power_result.get('total_n', power_result['n_per_group'] * 2)
    else:
        raise ValueError("Could not determine required sample size from power_result")

    # Get drop-off rate (prefer direct dropoff_rate, fall back to fatigue_score)
    if dropoff_rate is not None:
        final_dropoff_rate = dropoff_rate
        final_fatigue_score = None  # Not using fatigue score
        risk_level = get_risk_level_from_dropoff(dropoff_rate)
    elif fatigue_score is not None:
        # Legacy path: convert fatigue score to drop-off
        final_dropoff_rate = estimate_dropoff_from_score(fatigue_score)
        final_fatigue_score = fatigue_score
        risk_level = get_risk_level(fatigue_score)
    else:
        raise ValueError("Must provide either dropoff_rate or fatigue_score")

    # Calculate invitations needed (full funnel)
    invitation_plan = calculate_invitations(
        required_completes=required_n,
        dropoff_rate=final_dropoff_rate,
        ctr=ctr,
        response_rate=response_rate,
        buffer=buffer,
    )

    # Combine all information
    return {
        'power_analysis': {
            'required_completes': required_n,
            'power': power_result.get('power'),
            'effect_size': power_result.get('effect_size', power_result.get('effect_size_f2')),
            'alpha': power_result.get('alpha'),
        },
        'fatigue_audit': {
            'fatigue_score': final_fatigue_score,
            'estimated_dropoff_rate': final_dropoff_rate,
            'risk_level': risk_level,
        },
        'sample_plan': invitation_plan,
        'recommendations': generate_recommendations_from_dropoff(
            final_dropoff_rate, required_n, invitation_plan['invitations_needed']
        ),
    }


def get_risk_level(fatigue_score: float) -> str:
    """Get risk level label from fatigue score."""
    if fatigue_score <= 25:
        return "LOW"
    elif fatigue_score <= 50:
        return "MODERATE"
    elif fatigue_score <= 75:
        return "HIGH"
    else:
        return "EXTREME"


def get_risk_level_from_dropoff(dropoff_rate: float) -> str:
    """Get risk level label from drop-off rate."""
    if dropoff_rate < 0.15:
        return "LOW"
    elif dropoff_rate < 0.25:
        return "MODERATE"
    elif dropoff_rate < 0.40:
        return "HIGH"
    else:
        return "EXTREME"


def generate_recommendations(
    fatigue_score: float,
    dropoff_rate: float,
    required_n: int,
    invitations_needed: int,
) -> list:
    """Generate recommendations based on sample plan (legacy - uses fatigue score)."""
    recommendations = []

    if fatigue_score > 50:
        recommendations.append(
            f"⚠️ High fatigue score ({fatigue_score:.0f}/100). "
            f"Consider simplifying survey to reduce drop-off from {dropoff_rate:.1%}."
        )

    if dropoff_rate > 0.30:
        recommendations.append(
            f"⚠️ Expected drop-off is {dropoff_rate:.1%}. "
            f"Reducing fatigue could significantly lower invitation requirements."
        )

    invitation_overhead = (invitations_needed - required_n) / required_n
    if invitation_overhead > 0.50:
        recommendations.append(
            f"💡 You need {invitation_overhead:.0%} more invitations than completes. "
            f"Improving survey design could reduce recruitment costs."
        )

    if fatigue_score <= 25:
        recommendations.append(
            f"✅ Low fatigue score ({fatigue_score:.0f}/100). Survey design is well-optimized."
        )

    if dropoff_rate < 0.15:
        recommendations.append(
            f"✅ Low expected drop-off ({dropoff_rate:.1%}). "
            f"Invitation requirements are close to target completes."
        )

    return recommendations


def generate_recommendations_from_dropoff(
    dropoff_rate: float,
    required_n: int,
    invitations_needed: int,
) -> list:
    """Generate recommendations based on sample plan (uses drop-off rate directly)."""
    recommendations = []

    if dropoff_rate > 0.30:
        recommendations.append(
            f"⚠️ High drop-off rate ({dropoff_rate:.1%}). "
            f"Consider simplifying your survey to reduce abandonment."
        )

    invitation_overhead = (invitations_needed - required_n) / required_n
    if invitation_overhead > 0.50:
        recommendations.append(
            f"💡 You need {invitation_overhead:.0%} more invitations than completes. "
            f"Reducing drop-off from {dropoff_rate:.1%} could lower recruitment costs."
        )

    if dropoff_rate < 0.15:
        recommendations.append(
            f"✅ Low drop-off rate ({dropoff_rate:.1%}). "
            f"Your survey design is well-optimized for completion."
        )

    if 0.15 <= dropoff_rate <= 0.25:
        recommendations.append(
            f"✅ Moderate drop-off rate ({dropoff_rate:.1%}). "
            f"This is typical for standard surveys."
        )

    return recommendations
