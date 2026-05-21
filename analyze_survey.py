#!/usr/bin/env python3
"""
Survey Fatigue Analysis Tool

Usage:
    python analyze_survey.py <survey.qsf>
    python analyze_survey.py <survey1.qsf> <survey2.qsf> <survey3.qsf>
    python analyze_survey.py *.qsf

Examples:
    python analyze_survey.py Bold_Claims_2AFC_BIBD.qsf
    python analyze_survey.py *.qsf --compare
"""

import sys
import argparse
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from parsers.qualtrics import load_qsf
from analyzers.fatigue_scorer import FatigueScorer
from analyzers.report_formatter import (
    format_full_report,
    format_comparison_report,
    format_executive_summary,
    print_scoring_explanation
)


def main():
    parser = argparse.ArgumentParser(
        description="Analyze Qualtrics surveys for cognitive fatigue issues",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python analyze_survey.py survey.qsf
  python analyze_survey.py survey1.qsf survey2.qsf --compare
  python analyze_survey.py *.qsf --executive
  python analyze_survey.py --explain
        """
    )

    parser.add_argument(
        'qsf_files',
        nargs='*',
        help='One or more .qsf files to analyze'
    )

    parser.add_argument(
        '--compare',
        action='store_true',
        help='Generate comparison table for multiple surveys'
    )

    parser.add_argument(
        '--executive',
        action='store_true',
        help='Generate executive summary only'
    )

    parser.add_argument(
        '--explain',
        action='store_true',
        help='Print scoring system explanation and exit'
    )

    args = parser.parse_args()

    # Just print scoring explanation
    if args.explain:
        print_scoring_explanation()
        return 0

    # Require at least one file
    if not args.qsf_files:
        parser.print_help()
        return 1

    # Check files exist
    qsf_paths = []
    for qsf_file in args.qsf_files:
        path = Path(qsf_file)
        if not path.exists():
            print(f"Error: File not found: {qsf_file}", file=sys.stderr)
            return 1
        if not path.suffix.lower() == '.qsf':
            print(f"Warning: {qsf_file} is not a .qsf file, skipping", file=sys.stderr)
            continue
        qsf_paths.append(path)

    if not qsf_paths:
        print("Error: No valid .qsf files provided", file=sys.stderr)
        return 1

    # Parse and analyze surveys
    reports = []
    for qsf_path in qsf_paths:
        try:
            print(f"Analyzing {qsf_path.name}...", file=sys.stderr)
            survey = load_qsf(str(qsf_path))

            # Use filename as survey name if "Untitled Survey"
            if survey.name == "Untitled Survey":
                survey.name = qsf_path.stem.replace('_', ' ').title()

            scorer = FatigueScorer()
            report = scorer.analyze(survey)
            reports.append(report)

        except Exception as e:
            print(f"Error analyzing {qsf_path}: {e}", file=sys.stderr)
            continue

    if not reports:
        print("Error: No surveys successfully analyzed", file=sys.stderr)
        return 1

    # Generate output based on mode
    if args.executive:
        # Executive summary
        print(format_executive_summary(reports))
    elif args.compare or len(reports) > 1:
        # Comparison table
        print(format_comparison_report(reports))
    else:
        # Full report for single survey
        print(format_full_report(reports[0]))

    return 0


if __name__ == "__main__":
    sys.exit(main())
