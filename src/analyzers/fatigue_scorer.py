#!/usr/bin/env python3
"""
Cognitive Fatigue Scoring Engine.

Calculates fatigue scores based on:
- Question types (fatigue hierarchy)
- Position weighting (later questions = higher fatigue)
- Clustering (high-load questions grouped together)
- Loops (repeated blocks multiply fatigue)
- Skip logic (reduces effective question count)
- Grid complexity (rows × columns)
- Attention check placement
"""

from dataclasses import dataclass, field
from typing import List, Dict, Tuple, Optional
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent))
from parsers.qualtrics import Survey, Question, Loop


# ============================================================================
# Scoring System Explanation
# ============================================================================

SCORING_EXPLANATION = """
╔══════════════════════════════════════════════════════════════════════════╗
║                     SURVEY FATIGUE SCORING SYSTEM                        ║
╚══════════════════════════════════════════════════════════════════════════╝

WHAT THE SCORE MEANS:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Score = FATIGUE RISK POINTS (higher = worse, lower = better)

 0 ─────── 25 ─────── 50 ─────── 75 ─────── 100
 │          │          │          │          │
LOW      MODERATE    HIGH      EXTREME   CATASTROPHIC
✅         ⚠️         🔴         ❌         💀

Good    Acceptable  Problem   Bad      Disaster


RISK LEVELS:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
✅ LOW (0-25 points)
   Excellent design, minimal fatigue
   → Launch immediately

⚠️ MODERATE (26-50 points)
   Acceptable with caveats
   → Review and optimize

🔴 HIGH (51-75 points)
   Problematic, major revisions needed
   → Redesign required

❌ EXTREME (76-100 points)
   Unacceptable, severe fatigue
   → Complete overhaul

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Remember: LOWER SCORE = BETTER DESIGN = LESS FATIGUE
"""

# ============================================================================
# Fatigue Hierarchy: Cognitive Load Scores by Question Type
# ============================================================================

FATIGUE_HIERARCHY = {
    "SingleAnswer": 5,          # Low cognitive load
    "MultipleAnswer": 15,       # Medium load (scanning + multiple selections)
    "Slider": 10,               # Medium-low (visual but requires precision)
    "TextEntry": 25,            # High load (short text)
    "Matrix": 30,               # High load (base - multiplied by size)
    "RankOrder": 35,            # Very high (comparison + ordering)
    "TextEntryLong": 50,        # Extreme (long open-ended)
    "DescriptiveText": 0,       # No load (just reading)
    "Timing": 0,                # No load
}

# Position multipliers (questions later in survey = higher fatigue)
POSITION_MULTIPLIERS = [
    (0, 10, 1.0),    # Q1-10: baseline
    (11, 20, 1.2),   # Q11-20: 20% increase
    (21, 30, 1.5),   # Q21-30: 50% increase
    (31, 999, 2.0),  # Q31+: 2x multiplier
]


# ============================================================================
# Issue Severity Levels
# ============================================================================

@dataclass
class Issue:
    """Represents a detected fatigue issue."""
    severity: str  # CRITICAL, HIGH, MEDIUM, LOW
    category: str  # Loop, Grid, Cluster, AttentionCheck, etc.
    question_id: str
    position: int
    description: str
    impact: float  # Points contributed to total score
    recommendation: str

    def __repr__(self) -> str:
        icon = {"CRITICAL": "🔴", "HIGH": "⚠️", "MEDIUM": "🟡", "LOW": "🟢"}[self.severity]
        return f"{icon} {self.severity}: {self.category} (Q{self.position})"


@dataclass
class CategoryScore:
    """Score contribution from a specific category."""
    name: str
    points: float
    description: str
    issues: List[Issue] = field(default_factory=list)


@dataclass
class FatigueReport:
    """Complete fatigue analysis report."""
    survey_name: str
    total_score: float = 0.0
    risk_level: str = "MODERATE"  # LOW, MODERATE, HIGH, CRITICAL
    category_scores: List[CategoryScore] = field(default_factory=list)
    issues: List[Issue] = field(default_factory=list)

    # BIBD metadata
    uses_bibd: bool = False
    total_questions: int = 0  # Total in QSF
    effective_questions: Optional[int] = None  # Per respondent

    # Time and drop-off estimates
    estimated_time_min: int = 0
    estimated_time_max: int = 0
    expected_dropoff_pct: float = 0.0
    effective_sample_size_pct: float = 100.0

    def __repr__(self) -> str:
        return (f"FatigueReport(score={self.total_score:.1f}/100, "
                f"risk={self.risk_level}, "
                f"issues={len(self.issues)})")

    def get_risk_level(self) -> str:
        """Determine risk level from score."""
        if self.total_score <= 30:
            return "LOW"
        elif self.total_score <= 50:
            return "MODERATE"
        elif self.total_score <= 70:
            return "HIGH"
        else:
            return "CRITICAL"

    def get_critical_issues(self) -> List[Issue]:
        """Get only critical severity issues."""
        return [i for i in self.issues if i.severity == "CRITICAL"]

    def get_issues_by_category(self, category: str) -> List[Issue]:
        """Get issues for a specific category."""
        return [i for i in self.issues if i.category == category]


# ============================================================================
# Fatigue Scorer
# ============================================================================

class FatigueScorer:
    """Calculate cognitive fatigue scores for surveys."""

    def __init__(self):
        self.survey: Optional[Survey] = None
        self.report: Optional[FatigueReport] = None

    def analyze(self, survey: Survey) -> FatigueReport:
        """
        Analyze survey and generate fatigue report.

        Args:
            survey: Parsed survey object

        Returns:
            FatigueReport with scores, issues, and recommendations
        """
        self.survey = survey
        self.report = FatigueReport(survey_name=survey.name)

        # Use effective questions if BIBD detected
        if survey.uses_bibd and survey.effective_questions:
            self.report.uses_bibd = True
            self.report.total_questions = len(survey.questions)
            self.report.effective_questions = survey.effective_questions

        # Calculate each component
        base_load = self._calculate_base_load()
        position_penalty = self._calculate_position_penalty()
        loop_penalty = self._calculate_loop_penalty()
        cluster_penalty = self._calculate_cluster_penalty()
        grid_penalty = self._calculate_grid_penalty()
        attention_penalty = self._calculate_attention_check_penalty()
        skip_logic_bonus = self._calculate_skip_logic_bonus()

        # Total score
        total_score = (
            base_load +
            position_penalty +
            loop_penalty +
            cluster_penalty +
            grid_penalty +
            attention_penalty -
            skip_logic_bonus
        )

        # Cap at 100
        self.report.total_score = min(total_score, 100.0)
        self.report.risk_level = self.report.get_risk_level()

        # Calculate time and drop-off estimates
        self._calculate_time_estimates()
        self._calculate_dropoff_estimates()

        # Sort issues by severity
        self.report.issues.sort(key=lambda x: {
            "CRITICAL": 0, "HIGH": 1, "MEDIUM": 2, "LOW": 3
        }[x.severity])

        return self.report

    def _calculate_base_load(self) -> float:
        """Calculate base cognitive load from question types."""
        total_load = 0.0
        issues = []

        # Determine which questions to score
        # If BIBD, we need to estimate load per effective question subset
        questions_to_score = self.survey.questions

        for q in questions_to_score:
            load = FATIGUE_HIERARCHY.get(q.type, 10)
            total_load += load

            # Flag high-load questions
            if load >= 30:
                issues.append(Issue(
                    severity="MEDIUM" if load < 40 else "HIGH",
                    category="HighLoad",
                    question_id=q.id,
                    position=q.position + 1,
                    description=f"{q.type} question with high cognitive load",
                    impact=load,
                    recommendation=f"Consider simplifying or removing this {q.type} question"
                ))

        # If BIBD, adjust load based on effective questions
        if self.survey.uses_bibd and self.survey.effective_questions:
            # Scale load proportionally
            ratio = self.survey.effective_questions / len(self.survey.questions)
            total_load = total_load * ratio

        # If skip logic is present, estimate reduction in effective load
        # Moderate estimate: skip logic reduces load by 40% of intensity
        # (product-based skip logic tends to hide larger question blocks)
        if self.survey.skip_logic_intensity > 0:
            skip_reduction = self.survey.skip_logic_intensity * 0.40
            total_load = total_load * (1 - skip_reduction)

        # Normalize to 0-30 scale for base load (allows skip logic reductions to show)
        # Typical survey: 30Q × 10 avg = 300 → 10 points
        # Long survey: 145Q × 10 avg = 1450 → 48 points (before skip logic)
        normalized_load = min(total_load / 30, 30.0)

        desc = "Sum of cognitive load from all question types"
        if self.survey.uses_bibd:
            desc = f"Cognitive load per respondent (BIBD: {self.survey.effective_questions} effective questions)"
        elif self.survey.skip_logic_intensity > 0:
            estimated_reduction_pct = self.survey.skip_logic_intensity * 40
            desc = f"Cognitive load with skip logic (~{estimated_reduction_pct:.0f}% reduction, {self.survey.questions_with_display_logic} conditional questions)"

        category = CategoryScore(
            name="Base Load",
            points=normalized_load,
            description=desc,
            issues=issues
        )
        self.report.category_scores.append(category)
        self.report.issues.extend(issues)

        return normalized_load

    def _calculate_position_penalty(self) -> float:
        """Calculate penalty for high-load questions late in survey."""
        total_penalty = 0.0
        issues = []

        for q in self.survey.questions:
            base_load = FATIGUE_HIERARCHY.get(q.type, 10)

            # Get position multiplier
            multiplier = 1.0
            for start, end, mult in POSITION_MULTIPLIERS:
                if start <= (q.position + 1) <= end:
                    multiplier = mult
                    break

            # Only penalize if multiplier > 1.0 and load is medium-high
            if multiplier > 1.0 and base_load >= 20:
                penalty = base_load * (multiplier - 1.0)
                total_penalty += penalty

                if penalty >= 10:
                    issues.append(Issue(
                        severity="MEDIUM",
                        category="Position",
                        question_id=q.id,
                        position=q.position + 1,
                        description=f"High-load {q.type} question in fatigue zone (Q{q.position + 1})",
                        impact=penalty,
                        recommendation=f"Move to earlier position (Q1-10) or simplify question type"
                    ))

        # Normalize penalty
        normalized_penalty = min(total_penalty / 15, 15.0)

        category = CategoryScore(
            name="Position Penalty",
            points=normalized_penalty,
            description="High-load questions appearing late in survey",
            issues=issues
        )
        self.report.category_scores.append(category)
        self.report.issues.extend(issues)

        return normalized_penalty

    def _calculate_loop_penalty(self) -> float:
        """Calculate penalty for looped question blocks."""
        if not self.survey.loops:
            category = CategoryScore(
                name="Loop Penalty",
                points=0.0,
                description="No loops detected",
                issues=[]
            )
            self.report.category_scores.append(category)
            return 0.0

        total_penalty = 0.0
        issues = []

        for loop in self.survey.loops:
            # Get questions in loop
            loop_questions = self.survey.get_questions_in_loop(loop.id)

            if not loop_questions:
                continue

            # Calculate average load per iteration
            avg_load = sum(FATIGUE_HIERARCHY.get(q.type, 10) for q in loop_questions) / len(loop_questions)

            # Penalty = iterations × questions × avg_load
            penalty = loop.iterations * len(loop_questions) * avg_load / 10

            total_penalty += penalty

            # Determine severity
            severity = "MEDIUM"
            if loop.iterations >= 5:
                severity = "CRITICAL"
            elif loop.iterations >= 3:
                severity = "HIGH"

            # Check for open-ended in loop (critical issue)
            has_open_ended = any(q.type in ["TextEntry", "TextEntryLong"] for q in loop_questions)
            if has_open_ended:
                severity = "CRITICAL"
                penalty *= 1.5

            issues.append(Issue(
                severity=severity,
                category="Loop",
                question_id=loop.id,
                position=loop_questions[0].position + 1 if loop_questions else 0,
                description=f"Loop with {loop.iterations} iterations, {len(loop_questions)} questions per iteration" +
                           (" (contains open-ended)" if has_open_ended else ""),
                impact=penalty,
                recommendation=(
                    f"Reduce to 2 iterations maximum" if loop.iterations > 2 else
                    "Remove open-ended questions from loop" if has_open_ended else
                    "Consider removing loop entirely"
                )
            ))

        # Normalize penalty (loops are the biggest killer)
        normalized_penalty = min(total_penalty, 30.0)

        category = CategoryScore(
            name="Loop Penalty",
            points=normalized_penalty,
            description=f"{len(self.survey.loops)} loop(s) detected",
            issues=issues
        )
        self.report.category_scores.append(category)
        self.report.issues.extend(issues)

        return normalized_penalty

    def _calculate_cluster_penalty(self) -> float:
        """Calculate penalty for high-load questions clustered together."""
        total_penalty = 0.0
        issues = []

        # Look for 3+ consecutive high-load questions
        cluster_size = 0
        cluster_start = None

        for i, q in enumerate(self.survey.questions):
            load = FATIGUE_HIERARCHY.get(q.type, 10)

            if load >= 25:  # High load threshold
                if cluster_start is None:
                    cluster_start = i
                cluster_size += 1
            else:
                # End of cluster
                if cluster_size >= 3:
                    penalty = cluster_size * 3
                    total_penalty += penalty

                    issues.append(Issue(
                        severity="HIGH" if cluster_size >= 4 else "MEDIUM",
                        category="Cluster",
                        question_id=self.survey.questions[cluster_start].id,
                        position=cluster_start + 1,
                        description=f"{cluster_size} high-load questions in sequence (Q{cluster_start + 1}-Q{i})",
                        impact=penalty,
                        recommendation="Spread high-load questions throughout survey, interspersed with low-load questions"
                    ))

                cluster_size = 0
                cluster_start = None

        # Check final cluster
        if cluster_size >= 3:
            penalty = cluster_size * 3
            total_penalty += penalty

            issues.append(Issue(
                severity="HIGH" if cluster_size >= 4 else "MEDIUM",
                category="Cluster",
                question_id=self.survey.questions[cluster_start].id,
                position=cluster_start + 1,
                description=f"{cluster_size} high-load questions in sequence (Q{cluster_start + 1}-Q{len(self.survey.questions)})",
                impact=penalty,
                recommendation="Spread high-load questions throughout survey"
            ))

        normalized_penalty = min(total_penalty, 20.0)

        category = CategoryScore(
            name="Cluster Penalty",
            points=normalized_penalty,
            description="High-load questions grouped together",
            issues=issues
        )
        self.report.category_scores.append(category)
        self.report.issues.extend(issues)

        return normalized_penalty

    def _calculate_grid_penalty(self) -> float:
        """Calculate penalty based on matrix grid complexity."""
        total_penalty = 0.0
        issues = []

        for q in self.survey.questions:
            if q.type != "Matrix":
                continue

            # Penalty based on total cells
            cells = q.rows * q.columns
            penalty = 0

            if cells > 50:
                penalty = 10
                severity = "HIGH"
            elif cells > 35:
                penalty = 6
                severity = "MEDIUM"
            elif cells > 20:
                penalty = 3
                severity = "LOW"

            if penalty > 0:
                total_penalty += penalty

                issues.append(Issue(
                    severity=severity,
                    category="GridComplexity",
                    question_id=q.id,
                    position=q.position + 1,
                    description=f"Matrix grid with {q.rows} rows × {q.columns} columns ({cells} cells)",
                    impact=penalty,
                    recommendation=(
                        f"Reduce to 5-7 rows maximum" if q.rows > 7 else
                        "Consider splitting into multiple smaller grids"
                    )
                ))

        normalized_penalty = min(total_penalty, 15.0)

        category = CategoryScore(
            name="Grid Complexity",
            points=normalized_penalty,
            description="Matrix questions with high row/column counts",
            issues=issues
        )
        self.report.category_scores.append(category)
        self.report.issues.extend(issues)

        return normalized_penalty

    def _calculate_attention_check_penalty(self) -> float:
        """Calculate penalty for attention checks in high-fatigue zones."""
        # TODO: Implement attention check detection
        # Need to identify validation questions from QSF

        category = CategoryScore(
            name="Attention Check",
            points=0.0,
            description="No attention checks detected (or not in fatigue zones)",
            issues=[]
        )
        self.report.category_scores.append(category)

        return 0.0

    def _calculate_skip_logic_bonus(self) -> float:
        """Calculate bonus for skip logic that reduces question count."""
        if not self.survey.skip_logic:
            category = CategoryScore(
                name="Skip Logic Bonus",
                points=0.0,
                description="No skip logic detected",
                issues=[]
            )
            self.report.category_scores.append(category)
            return 0.0

        # Estimate question count reduction
        # Simple heuristic: each skip logic rule reduces effective count by ~10%
        reduction_pct = min(len(self.survey.skip_logic) * 10, 30)
        bonus = reduction_pct / 3  # Max 10 point bonus

        category = CategoryScore(
            name="Skip Logic Bonus",
            points=bonus,
            description=f"Skip logic reduces effective question count by ~{reduction_pct}%",
            issues=[]
        )
        self.report.category_scores.append(category)

        return bonus

    def _calculate_time_estimates(self) -> None:
        """Estimate completion time in minutes."""
        total_seconds = 0

        # Time per question type (in seconds)
        TIME_ESTIMATES = {
            "SingleAnswer": 5,
            "MultipleAnswer": 10,
            "Slider": 8,
            "TextEntry": 30,
            "TextEntryLong": 180,
            "Matrix": 30,  # Base time, multiplied by cells
            "RankOrder": 45,
            "DescriptiveText": 5,
        }

        for q in self.survey.questions:
            base_time = TIME_ESTIMATES.get(q.type, 10)

            if q.type == "Matrix":
                # More cells = more time
                base_time = base_time * (1 + q.rows * q.columns / 50)

            # Loops multiply time
            if q.in_loop:
                loop = next((l for l in self.survey.loops if l.id == q.loop_id), None)
                if loop:
                    base_time *= loop.iterations

            total_seconds += base_time

        # Convert to minutes (min and max estimates)
        self.report.estimated_time_min = int(total_seconds / 60 * 0.8)  # Fast respondents
        self.report.estimated_time_max = int(total_seconds / 60 * 1.3)  # Slow respondents

    def _calculate_dropoff_estimates(self) -> None:
        """Estimate drop-off rate based on fatigue score."""
        # Higher fatigue score = higher drop-off
        # Base drop-off: 10% (even good surveys lose some people)
        # Add 0.3% per fatigue point above 30

        base_dropoff = 10.0
        if self.report.total_score > 30:
            additional_dropoff = (self.report.total_score - 30) * 0.4
        else:
            additional_dropoff = 0

        self.report.expected_dropoff_pct = min(base_dropoff + additional_dropoff, 70.0)
        self.report.effective_sample_size_pct = 100.0 - self.report.expected_dropoff_pct


def analyze_survey(survey: Survey) -> FatigueReport:
    """
    Convenience function to analyze a survey.

    Args:
        survey: Parsed survey object

    Returns:
        FatigueReport with complete analysis

    Example:
        >>> from parsers.qualtrics import load_qsf
        >>> survey = load_qsf('data/sample-surveys/user-research.qsf')
        >>> report = analyze_survey(survey)
        >>> print(f"Fatigue Score: {report.total_score:.1f}/100 ({report.risk_level} RISK)")
    """
    scorer = FatigueScorer()
    return scorer.analyze(survey)
