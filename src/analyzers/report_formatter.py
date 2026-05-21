#!/usr/bin/env python3
"""
Report formatting utilities for survey fatigue analysis.

Generates human-readable reports with scoring explanations.
"""

from typing import List, Optional
from .fatigue_scorer import FatigueReport, SCORING_EXPLANATION


def format_full_report(report: FatigueReport) -> str:
    """
    Generate a complete formatted report with scoring explanation.

    Args:
        report: FatigueReport object from FatigueScorer

    Returns:
        Formatted report string with scoring explanation at top
    """

    # Start with scoring explanation
    output = [SCORING_EXPLANATION]
    output.append("")

    # Survey header
    output.append("=" * 78)
    output.append(f"SURVEY FATIGUE ANALYSIS REPORT")
    output.append("=" * 78)
    output.append("")

    # Survey name and overview
    output.append(f"Survey: {report.survey_name}")

    # Question counts
    if report.uses_bibd:
        output.append(f"Total questions in QSF: {report.total_questions}")
        output.append(f"Questions per respondent: ~{report.effective_questions} (BIBD design)")
    else:
        total_q = report.total_questions if report.total_questions > 0 else "Unknown"
        output.append(f"Total questions: {total_q}")

    output.append("")

    # Score display with visual indicator
    risk_icon = {
        "LOW": "✅",
        "MODERATE": "⚠️",
        "HIGH": "🔴",
        "CRITICAL": "❌"
    }.get(report.risk_level, "")

    output.append("━" * 78)
    output.append(f"SCORE: {report.total_score:.1f}/100 points")
    output.append(f"RISK LEVEL: {risk_icon} {report.risk_level}")
    output.append("━" * 78)

    # Interpretation
    if report.total_score <= 25:
        interpretation = "Excellent design, minimal fatigue → Launch immediately"
    elif report.total_score <= 50:
        interpretation = "Acceptable with caveats → Review and optimize"
    elif report.total_score <= 75:
        interpretation = "Problematic, major revisions needed → Redesign required"
    else:
        interpretation = "Unacceptable, severe fatigue → Complete overhaul"

    output.append(f"INTERPRETATION: {interpretation}")
    output.append("")

    # Time and drop-off estimates
    output.append(f"Estimated time: {report.estimated_time_min}-{report.estimated_time_max} minutes")
    output.append(f"Expected drop-off: {report.expected_dropoff_pct:.1f}%")
    output.append(f"Effective sample: {report.effective_sample_size_pct:.1f}%")
    output.append("")

    # Score breakdown
    output.append("SCORE BREAKDOWN:")
    output.append("─" * 78)

    for category in report.category_scores:
        output.append(f"+ {category.name}: {category.points:.1f} points")
        output.append(f"  └─ {category.description}")
        if category.issues:
            output.append(f"     ({len(category.issues)} issues detected)")
        output.append("")

    output.append(f"━" * 78)
    output.append(f"TOTAL: {report.total_score:.1f}/100 points ({report.risk_level} RISK)")
    output.append("")

    # Issues summary
    if report.issues:
        output.append("ISSUES DETECTED:")
        output.append("─" * 78)

        # Group by severity
        critical = [i for i in report.issues if i.severity == "CRITICAL"]
        high = [i for i in report.issues if i.severity == "HIGH"]
        medium = [i for i in report.issues if i.severity == "MEDIUM"]
        low = [i for i in report.issues if i.severity == "LOW"]

        for severity, issues in [("CRITICAL", critical), ("HIGH", high),
                                  ("MEDIUM", medium), ("LOW", low)]:
            if issues:
                icon = {"CRITICAL": "❌", "HIGH": "🔴", "MEDIUM": "🟡", "LOW": "🟢"}[severity]
                output.append(f"{icon} {severity} ({len(issues)} issues):")
                for issue in issues[:5]:  # Show first 5
                    output.append(f"   • Q{issue.position} ({issue.question_id}): {issue.description}")
                if len(issues) > 5:
                    output.append(f"   ... and {len(issues) - 5} more")
                output.append("")
    else:
        output.append("✅ NO ISSUES DETECTED")
        output.append("")

    # BIBD note if applicable
    if report.uses_bibd:
        output.append("NOTE: BIBD (Balanced Incomplete Block Design) detected")
        output.append(f"Respondents see {report.effective_questions} of {report.total_questions} questions")
        output.append("Score based on actual respondent experience, not total question pool")
        output.append("")

    return "\n".join(output)


def format_comparison_report(reports: List[FatigueReport]) -> str:
    """
    Generate a comparison report for multiple surveys.

    Args:
        reports: List of FatigueReport objects

    Returns:
        Formatted comparison table
    """

    output = [SCORING_EXPLANATION]
    output.append("")
    output.append("=" * 78)
    output.append("SURVEY COMPARISON REPORT")
    output.append("=" * 78)
    output.append("")

    # Header
    output.append(f"{'Survey':<30} {'Score':<12} {'Risk':<12} {'Time':<15} {'Drop-off':<10}")
    output.append("─" * 78)

    # Sort by score (best to worst)
    sorted_reports = sorted(reports, key=lambda r: r.total_score)

    for report in sorted_reports:
        risk_icon = {
            "LOW": "✅",
            "MODERATE": "⚠️",
            "HIGH": "🔴",
            "CRITICAL": "❌"
        }.get(report.risk_level, "")

        name = report.survey_name[:28] if len(report.survey_name) > 28 else report.survey_name
        score = f"{report.total_score:.1f}/100"
        risk = f"{risk_icon} {report.risk_level}"
        time = f"{report.estimated_time_min}-{report.estimated_time_max} min"
        dropoff = f"{report.expected_dropoff_pct:.1f}%"

        output.append(f"{name:<30} {score:<12} {risk:<12} {time:<15} {dropoff:<10}")

    output.append("")
    output.append("KEY:")
    output.append("  ✅ LOW (0-25):       Launch immediately")
    output.append("  ⚠️  MODERATE (26-50): Review and optimize")
    output.append("  🔴 HIGH (51-75):     Redesign required")
    output.append("  ❌ CRITICAL (76-100): Complete overhaul")
    output.append("")

    return "\n".join(output)


def format_executive_summary(reports: List[FatigueReport]) -> str:
    """
    Generate a brief executive summary.

    Args:
        reports: List of FatigueReport objects

    Returns:
        Brief summary string
    """

    output = [SCORING_EXPLANATION]
    output.append("")
    output.append("EXECUTIVE SUMMARY")
    output.append("=" * 78)
    output.append("")

    # Count by risk level
    low = sum(1 for r in reports if r.risk_level == "LOW")
    moderate = sum(1 for r in reports if r.risk_level == "MODERATE")
    high = sum(1 for r in reports if r.risk_level == "HIGH")
    critical = sum(1 for r in reports if r.risk_level == "CRITICAL")

    total = len(reports)

    output.append(f"Surveys analyzed: {total}")
    output.append("")

    if low > 0:
        output.append(f"✅ {low} survey(s) with LOW risk - Ready to launch")
    if moderate > 0:
        output.append(f"⚠️  {moderate} survey(s) with MODERATE risk - Review recommended")
    if high > 0:
        output.append(f"🔴 {high} survey(s) with HIGH risk - Redesign required")
    if critical > 0:
        output.append(f"❌ {critical} survey(s) with CRITICAL risk - Complete overhaul needed")

    output.append("")
    output.append("RECOMMENDATIONS:")
    output.append("─" * 78)

    for report in sorted(reports, key=lambda r: r.total_score):
        if report.risk_level == "LOW":
            action = "✅ Launch immediately"
        elif report.risk_level == "MODERATE":
            action = "⚠️  Review and optimize"
        elif report.risk_level == "HIGH":
            action = "🔴 Major revisions required"
        else:
            action = "❌ Complete overhaul required"

        name = report.survey_name[:40] if len(report.survey_name) > 40 else report.survey_name
        output.append(f"{name}: {report.total_score:.1f}/100 → {action}")

    output.append("")

    return "\n".join(output)


def print_scoring_explanation():
    """Print just the scoring explanation (for reference)."""
    print(SCORING_EXPLANATION)


if __name__ == "__main__":
    # Print scoring explanation when run directly
    print_scoring_explanation()
