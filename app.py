"""
Streamlit app for Survey Fatigue Audit + Power Analysis

Features:
- Conversational agent for guided power analysis
- Interactive power calculators
- Fatigue audit integration
- Optimization recommendations
"""

import streamlit as st
import numpy as np
import pandas as pd
import plotly.graph_objects as go
import sys
sys.path.append('.')

from src.power.agent import PowerAnalysisAgent
from src.power.calculators.means import MeansPowerCalc
from src.power.calculators.regression import RegressionPowerCalc
from src.power.calculators.proportions import ProportionsPowerCalc
from src.power.calculators.segments import SegmentPowerCalc
from src.power.calculators.nonparametric import NonParametricPowerCalc
from src.power.calculators.logistic import LogisticPowerCalc
from src.power.visualizations.power_curves import plot_power_curve, plot_sample_size_curve
from src.power.visualizations.sensitivity import plot_sensitivity_analysis, create_segment_allocation_plot
from src.power.integrations.dropoff import (
    calculate_invitations,
    estimate_dropoff_from_score,
    integrated_sample_plan
)
from src.power.integrations.optimizer import optimize_survey_design


# Page config
st.set_page_config(
    page_title="Survey & Statistical Power Planning",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="collapsed"  # Hide sidebar
)

# Custom CSS for better tooltip visibility
st.markdown("""
<style>
    /* Make tooltips more visible with distinct background */
    div[data-baseweb="tooltip"] {
        background-color: #2d3748 !important;
        border: 2px solid #4CAF50 !important;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.5) !important;
        border-radius: 8px !important;
    }

    div[data-baseweb="tooltip"] div {
        background-color: #2d3748 !important;
        color: #ffffff !important;
        font-size: 14px !important;
        line-height: 1.6 !important;
        padding: 16px !important;
        max-width: 400px !important;
    }

    /* Style the help icon to be more visible */
    button[kind="icon"] svg {
        fill: #4CAF50 !important;
    }

    button[kind="icon"]:hover svg {
        fill: #66BB6A !important;
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state
if 'agent' not in st.session_state:
    st.session_state.agent = PowerAnalysisAgent()
if 'conversation_started' not in st.session_state:
    st.session_state.conversation_started = False
if 'messages' not in st.session_state:
    st.session_state.messages = []


def main():
    # Single dashboard - no sidebar navigation
    show_integrated_dashboard()


def show_agent_interface():
    """Conversational agent interface"""
    st.header("Guided Power Analysis")

    st.info("""
    **What this does:**
    - Asks about your research question
    - Recommends the right statistical test
    - Calculates **sample size needed** (statistical power)
    - *Optional:* Estimates **invitations needed** (if you have survey fatigue score)

    **Best for:** First-time users or integrated workflow
    """)

    # Start button
    if not st.session_state.conversation_started:
        if st.button("Start Conversation", type="primary"):
            st.session_state.conversation_started = True
            welcome_msg = st.session_state.agent.start_conversation()
            st.session_state.messages.append(("assistant", welcome_msg))
            st.rerun()
    else:
        # Display conversation history
        for role, message in st.session_state.messages:
            with st.chat_message(role):
                st.markdown(message)

        # User input
        if prompt := st.chat_input("E.g., 'Compare user satisfaction between two designs'"):
            # Add user message
            st.session_state.messages.append(("user", prompt))

            with st.chat_message("user"):
                st.markdown(prompt)

            # Get agent response
            response = st.session_state.agent.process_response(prompt)
            st.session_state.messages.append(("assistant", response))

            with st.chat_message("assistant"):
                st.markdown(response)

        # Reset button with confirmation
        col1, col2 = st.columns([3, 1])
        with col2:
            if 'confirm_reset' not in st.session_state:
                st.session_state.confirm_reset = False

            if not st.session_state.confirm_reset:
                if st.button("Start Over", help="Clear conversation and start fresh"):
                    st.session_state.confirm_reset = True
                    st.rerun()
            else:
                st.warning("Warning: This will delete your conversation history.")
                col_yes, col_no = st.columns(2)
                with col_yes:
                    if st.button("✓ Yes", type="primary"):
                        st.session_state.agent = PowerAnalysisAgent()
                        st.session_state.conversation_started = False
                        st.session_state.messages = []
                        st.session_state.confirm_reset = False
                        st.rerun()
                with col_no:
                    if st.button("✗ Cancel"):
                        st.session_state.confirm_reset = False
                        st.rerun()


def show_calculator_interface():
    """Manual power calculator interface"""
    st.header("Statistical Power")

    st.markdown("""
    Calculate the sample size needed to obtain adequate power for your statistical tests.
    """)

    # Initialize calculation history
    if 'calculation_history' not in st.session_state:
        st.session_state.calculation_history = []

    # Show last calculation if exists
    if 'last_calculation' in st.session_state:
        with st.expander("Last Calculation (click to view details)", expanded=False):
            calc = st.session_state['last_calculation']

            # Condensed summary format
            if calc['solve_for'] == 'n':
                if 'total_n' in calc['result']:
                    result_text = f"{calc['result']['total_n']:,} sample"
                elif 'n' in calc['result']:
                    result_text = f"{calc['result']['n']:,} sample"
                st.write(f"**{calc['test']}** → {result_text}")
            else:
                power_text = f"{calc['result']['power']:.0%}"
                st.write(f"**{calc['test']}** → {power_text} power")

            # View details toggle
            if st.button("View Full Details", key="expand_last_calc"):
                st.write(f"**Test:** {calc['test']}")
                if 'effect_size' in calc['result']:
                    st.write(f"**Effect Size:** {calc['result']['effect_size']:.2f}")
                if 'alpha' in calc['result']:
                    st.write(f"**Significance Level:** {calc['result']['alpha']}")
                if 'power' in calc['result']:
                    st.write(f"**Power:** {calc['result']['power']:.1%}")
                if 'n_groups' in calc:
                    st.write(f"**Groups:** {calc['n_groups']}")
                if 'n_predictors' in calc:
                    st.write(f"**Predictors:** {calc['n_predictors']}")
                if 'sample_n' in calc:
                    st.write(f"**Sample Tested:** {calc['sample_n']:,}")

    # Show calculation history
    if len(st.session_state.calculation_history) > 0:
        with st.expander(f"History ({len(st.session_state.calculation_history)} recent)", expanded=False):
            for idx, calc in enumerate(reversed(st.session_state.calculation_history[-5:])):
                # Condensed single-line format
                if 'total_n' in calc['result']:
                    st.caption(f"{idx + 1}. {calc['test']}: {calc['result']['total_n']:,} sample")
                elif 'n' in calc['result']:
                    st.caption(f"{idx + 1}. {calc['test']}: {calc['result']['n']:,} sample")
                elif 'power' in calc['result']:
                    st.caption(f"{idx + 1}. {calc['test']}: {calc['result']['power']:.0%} power")

    # Workflow selection at the top
    col_workflow, col_reset = st.columns([4, 1])
    with col_workflow:
        workflow = st.radio(
            "What do you want to calculate?",
            ["Sample Size (How many participants do I need?)",
             "Power Check (Is my current sample adequate?)",
             "Compare Scenarios (Quick comparison of multiple effect sizes)"],
            help="Choose workflow: Single calculation, power check, or compare multiple scenarios side-by-side"
        )
    with col_reset:
        st.write("")  # Spacing
        st.write("")  # Spacing
        if st.button("Reset", help="Clear all inputs and start fresh"):
            # Clear last calculation
            if 'last_calculation' in st.session_state:
                del st.session_state['last_calculation']
            st.rerun()

    if workflow.startswith("📝"):
        solve_for = 'n'
    elif workflow.startswith("🔍"):
        solve_for = 'power'
    else:
        solve_for = 'compare'

    st.markdown("---")

    # Test type selection with examples
    col_test, col_examples = st.columns([3, 1])
    with col_test:
        test_type = st.selectbox(
            "Select your statistical test:",
            [
                "Independent t-test (compare 2 groups)",
                "ANOVA (compare 3+ groups)",
                "Correlation / Simple Regression (relationship between 2 variables)",
                "Multiple Regression (predict from multiple variables)",
                "Logistic Regression (predict yes/no outcome)",
                "Ordinal Regression (predict ordered categories)",
                "Multinomial Regression (predict unordered categories)",
                "Non-Parametric: Mann-Whitney U (2 groups, ranks)",
                "Non-Parametric: Wilcoxon (paired, ranks)",
                "Non-Parametric: Kruskal-Wallis (3+ groups, ranks)",
                "Non-Parametric: Friedman (repeated measures, ranks)",
                "Chi-Square (association between categories)",
                "Proportions (compare percentages)",
                "Segment Analysis (compare pre-defined segments)"
            ],
            help="Not sure which test? Use the Guided Agent instead"
        )
    with col_examples:
        st.write("")
        st.write("")
        with st.popover("View See Examples"):
            st.markdown("""
            **Independent t-test**
            - A/B testing (Design A vs B)
            - Treatment vs Control
            - Before vs After (same people)

            **ANOVA**
            - Compare 3+ pricing tiers
            - Multiple design variants
            - Cross-regional comparison

            **Correlation/Regression**
            - Satisfaction → Loyalty
            - Usage → Retention
            - Price → Purchase intent

            **Multiple Regression**
            - Predict NPS from age, tenure, satisfaction
            - Churn prediction (multiple factors)

            **Segment Analysis**
            - Compare user personas (40%/40%/20%)
            - LCA-derived segments
            - Behavioral clusters

            **Chi-Square**
            - Customer type × Satisfaction level
            - Region × Product preference

            Not sure? Use **Guided Agent**
            """)

    st.markdown("---")

    # Extract base test name (before parenthesis)
    base_test = test_type.split(" (")[0]

    # Show test description as reminder
    test_descriptions = {
        "Independent t-test": "Compare means between 2 independent groups",
        "ANOVA": "Compare means across 3 or more groups",
        "Correlation / Simple Regression": "Measure relationship between 2 continuous variables",
        "Multiple Regression": "Predict outcome from multiple variables",
        "Logistic Regression": "Predict yes/no outcome",
        "Ordinal Regression": "Predict ordered categories (e.g., Likert scales)",
        "Multinomial Regression": "Predict unordered categories",
        "Non-Parametric: Mann-Whitney U": "Compare 2 groups using ranks (alternative to t-test)",
        "Non-Parametric: Wilcoxon": "Compare paired observations using ranks",
        "Non-Parametric: Kruskal-Wallis": "Compare 3+ groups using ranks (alternative to ANOVA)",
        "Non-Parametric: Friedman": "Compare repeated measures using ranks",
        "Chi-Square": "Test association between categorical variables",
        "Proportions": "Compare percentages between groups",
        "Segment Analysis": "Compare outcomes across pre-defined segments"
    }

    if base_test in test_descriptions:
        st.info(f"**Selected Test:** {base_test} — {test_descriptions[base_test]}")

    # For power check, show sample size input first
    if solve_for == 'power':
        st.subheader("Your Current Sample")
        if base_test in ["Independent t-test", "ANOVA", "Segment Analysis"]:
            sample_n = st.number_input(
                "Sample size per group *",
                min_value=20, value=50, step=1,
                help="Number of participants in each group/condition. * Required field. Minimum 20, but 50+ recommended for adequate power."
            )
            if sample_n < 30:
                st.warning(f"""
                **Problem:** Small sample size (n={sample_n} per group).

                **Why this matters:** With {sample_n} per group, you can only detect very large effects (d≥0.8). Smaller effects will be missed.

                **Minimum recommended:** 30 per group (can detect d≈0.7)
                **For medium effects (d=0.5):** Need 64 per group
                """)
        else:
            sample_n = st.number_input(
                "Total sample size *",
                min_value=30, value=100, step=10,
                help="Total number of participants in your study. * Required field. Minimum 30, but 100+ recommended for most analyses."
            )
            if sample_n < 50:
                st.warning(f"""
                **Problem:** Small sample size (n={sample_n} total).

                **Why this matters:** With {sample_n} participants, power will be low for detecting typical effects in this analysis.

                **Minimum recommended:** 50 participants
                **For adequate power:** Typically need 100+ for most analyses
                """)
        st.markdown("---")

    col_header, col_presets = st.columns([2, 2])
    with col_header:
        st.subheader("Study Parameters")
        st.caption("Fields marked with * are required")
    with col_presets:
        st.write("**Quick Presets:**")
        col_p1, col_p2, col_p3, col_p4 = st.columns(4)

        # Initialize effect size in session state
        if 'effect_size_ttest' not in st.session_state:
            st.session_state.effect_size_ttest = 0.5

        with col_p1:
            if st.button("Small", help="Small effect, 80% power, α=0.05", key="preset_small"):
                st.session_state.effect_size_ttest = 0.2
        with col_p2:
            if st.button("Medium", help="Medium effect, 80% power, α=0.05", key="preset_medium"):
                st.session_state.effect_size_ttest = 0.5
        with col_p3:
            if st.button("Large", help="Large effect, 80% power, α=0.05", key="preset_large"):
                st.session_state.effect_size_ttest = 0.8
        with col_p4:
            if st.button("↩️", help="Reset to defaults", key="reset_params"):
                st.session_state.effect_size_ttest = 0.5

    col1, col2 = st.columns(2)

    if base_test == "Independent t-test":
        with col1:
            st.caption("Effect Size: Small=0.2 | Medium=0.5 | Large=0.8")
            with st.popover("ℹ️ Learn More About Effect Sizes"):
                st.markdown("""
                **Cohen's d Guidelines:**
                - **Small (0.2):** Subtle difference (e.g., 2.0 vs 2.2 on 10-point scale)
                - **Medium (0.5):** Moderate difference (e.g., 2.0 vs 3.0) - Most common in social science
                - **Large (0.8):** Obvious difference (e.g., 2.0 vs 4.0)

                **When to use each:**
                - Small: Subtle interventions, incremental improvements
                - Medium: Typical experiments, standard interventions
                - Large: Extreme groups, strong interventions

                **Unsure?** Use Medium (0.5) - most research falls here.
                """)

            effect_size = st.slider(
                "Effect Size (Cohen's d)",
                0.1, 2.0, st.session_state.effect_size_ttest, 0.1,
                help="Magnitude of the difference between groups (Cohen's d). Small=0.2, Medium=0.5, Large=0.8. Larger effects are easier to detect and require smaller samples.",
                key="effect_slider_ttest"
            )

            # Update session state when slider changes
            st.session_state.effect_size_ttest = effect_size

            if effect_size > 1.0:
                st.warning(f"""
                **Note:** Very large effect size (d={effect_size:.1f}).

                **When to use large effects:**
                - Comparing extreme groups (e.g., experts vs. novices)
                - Strong interventions (e.g., training program with dramatic results)
                - Physical/biological outcomes with clear mechanisms

                **Most social science research:** Use d≤0.8. If unsure, use medium (0.5).
                """)

            alpha = st.selectbox(
                "Significance Level (chance of false positive)",
                [0.01, 0.05, 0.10],
                index=1,
                help="Probability of false positive (Type I error). Also called alpha (α). Standard is 0.05 (5% chance of finding effect when none exists)."
            )
        with col2:
            if solve_for == 'n':
                power = st.slider(
                    "Statistical Power (% chance of detecting real effect)",
                    0.5, 0.99, 0.80, 0.01,
                    help="Probability of detecting a real effect if it exists (1 - Type II error). Standard is 0.80 (80% chance of finding effect when it exists).",
                    format="%.0%%"
                )
            elif solve_for == 'power':
                st.write("**Effect Size Guidelines:**")
                st.caption("Small: d = 0.2")
                st.caption("Medium: d = 0.5")
                st.caption("Large: d = 0.8")
            else:  # compare mode
                alpha = 0.05
                power = 0.80
                st.info("**Comparison Mode:** Comparing Small (0.2), Medium (0.5), and Large (0.8) effect sizes with standard settings (α=0.05, power=80%)")

        if solve_for == 'compare':
            # Quick comparison mode
            st.markdown("---")
            st.subheader("Results")

            calc = MeansPowerCalc(test_type='independent')
            comparison_data = []

            for effect_label, effect_val in [("Small", 0.2), ("Medium", 0.5), ("Large", 0.8)]:
                result = calc.calculate(effect_size=effect_val, alpha=0.05, power=0.80, solve_for='n')
                comparison_data.append({
                    "Effect Size": f"{effect_label} (d={effect_val})",
                    "Per Group": f"{result['n_per_group']:,}",
                    "Total": f"{result['total_n']:,}"
                })

            # Display as table
            import pandas as pd
            df = pd.DataFrame(comparison_data)
            st.table(df)

            # Export buttons
            col_export1, col_export2 = st.columns(2)

            with col_export1:
                csv = df.to_csv(index=False)
                st.download_button(
                    label="Download CSV",
                    data=csv,
                    file_name="power_analysis_comparison.csv",
                    mime="text/csv",
                    help="Download as CSV for Excel/Google Sheets"
                )

            with col_export2:
                # Generate Markdown
                markdown_content = f"""# Power Analysis Comparison - Independent t-test

**Date:** {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M')}

## Scenario Comparison

| Effect Size | Per Group | Total |
|-------------|-----------|-------|
"""
                for row in comparison_data:
                    markdown_content += f"| {row['Effect Size']} | {row['Per Group']} | {row['Total']} |\n"

                markdown_content += f"""
## Parameters

- **Test:** Independent t-test (compare 2 groups)
- **Significance Level (α):** 0.05 (5%)
- **Statistical Power:** 0.80 (80%)

## Interpretation

- **Small effect (d=0.2):** Subtle differences, requires large sample
- **Medium effect (d=0.5):** Typical for social sciences
- **Large effect (d=0.8):** Obvious differences, smaller sample needed

---
*Generated by Power Analysis Tool*
"""

                st.download_button(
                    label="Download Markdown",
                    data=markdown_content,
                    file_name="power_analysis_comparison.md",
                    mime="text/markdown",
                    help="Download as Markdown for Confluence/Notion/GitHub"
                )

            st.info("Tip: **Tip:** Use this quick comparison to get a sense of sample size ranges, then use Single Calculation mode for precise values.")

        elif st.button("Calculate", type="primary", key="ttest_calc"):
            st.markdown("---")
            st.subheader("Results")

            with st.spinner("Calculating Sample Size..."):
                calc = MeansPowerCalc(test_type='independent')

                if solve_for == 'n':
                    result = calc.calculate(
                        effect_size=effect_size,
                        alpha=alpha,
                        power=power,
                        solve_for='n'
                    )

                    # Store in session state with full parameters
                    result['effect_size'] = effect_size
                    result['alpha'] = alpha
                    result['power'] = power
                    calc_data = {
                        'test': 'Independent t-test',
                        'result': result,
                        'solve_for': 'n'
                    }
                    st.session_state['last_calculation'] = calc_data

                    # Add to history (keep last 10)
                    st.session_state.calculation_history.append(calc_data.copy())
                    if len(st.session_state.calculation_history) > 10:
                        st.session_state.calculation_history.pop(0)

                    st.success(f"**Required Sample Size:** {result['n_per_group']:,} per group ({result['total_n']:,} total)")

                    # Export results
                    col_copy, col_md = st.columns(2)

                    with col_copy:
                        results_text = f"""Independent t-test Sample Size Calculation
Effect Size (Cohen's d): {effect_size}
Significance Level: {alpha}
Statistical Power: {power:.0%}
Required Sample Size: {result['n_per_group']:,} per group ({result['total_n']:,} total)
"""
                        if st.button("View Copy Results", key="copy_ttest"):
                            st.code(results_text, language=None)
                            st.caption("Copy with Ctrl+C / Cmd+C")

                    with col_md:
                        # Generate Markdown
                        markdown_result = f"""# Power Analysis Results

**Test:** Independent t-test (compare 2 groups)
**Date:** {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M')}

## Results

**Required Sample Size:** {result['n_per_group']:,} per group ({result['total_n']:,} total)

## Parameters

| Parameter | Value |
|-----------|-------|
| Effect Size (Cohen's d) | {effect_size} |
| Significance Level (α) | {alpha} ({alpha*100:.0f}%) |
| Statistical Power | {power:.0%} |

## Next Steps

Success: This is the number of survey **sample** you need.

Warning: This does NOT include:
- Click-through rate (CTR)
- Survey drop-off rate

Go to **Survey Sample Size** to calculate invitations needed.

---
*Generated by Power Analysis Tool*
"""
                        st.download_button(
                            label="📥 Markdown",
                            data=markdown_result,
                            file_name=f"power_analysis_{pd.Timestamp.now().strftime('%Y%m%d_%H%M')}.md",
                            mime="text/markdown",
                            help="Download for Confluence/Notion",
                            key="md_ttest"
                        )

                    st.info(f"""
                    **This is the number of survey sample you need.**

                    Next step: Go to **Survey Sample Size** tab to calculate how many invitations to send,
                    accounting for click-through rate (CTR) and survey drop-off.
                    """)

                    # Show visualization
                    fig = plot_power_curve(calc, effect_sizes=[effect_size], alpha=alpha)
                    st.plotly_chart(fig, use_container_width=True)

                    # Quick actions
                    st.markdown("---")
                    st.info(f"""
                    **Next Step:** Calculate invitations to send

                    Your result ({result['total_n']:,} sample) has been saved. Go to **Survey Sample Size** in the sidebar to calculate how many invitations you need to send, accounting for CTR and drop-off.

                    The required sample size will be auto-populated for you.
                    """)

                    col_action1, col_action2 = st.columns(2)
                    with col_action1:
                        if st.button("Calculate Again with Different Parameters", key="recalc_ttest"):
                            st.info("👆 Scroll up to adjust parameters and click Calculate again")
                else:
                    result = calc.calculate(
                        effect_size=effect_size,
                        alpha=alpha,
                        n=sample_n,
                        solve_for='power'
                    )

                    # Store in session state with full parameters
                    result['effect_size'] = effect_size
                    result['alpha'] = alpha
                    st.session_state['last_calculation'] = {
                        'test': 'Independent t-test',
                        'result': result,
                        'solve_for': 'power',
                        'sample_n': sample_n
                    }

                    if result['power'] >= 0.80:
                        st.success(f"**Power:** {result['power']:.1%} Success: Adequate for detecting d={effect_size}")
                        power_status = "Adequate"
                    elif result['power'] >= 0.70:
                        st.warning(f"**Power:** {result['power']:.1%} Warning: Moderate - may miss some effects")
                        st.info("Consider increasing sample size or accepting lower effect size detectability.")
                        power_status = "Moderate"
                    else:
                        st.error(f"**Power:** {result['power']:.1%} Error: Underpowered - likely to miss real effects")

                        # Calculate exact n needed for 80% power
                        calc_fix = MeansPowerCalc(test_type='independent')
                        result_fix = calc_fix.calculate(
                            effect_size=effect_size,
                            alpha=alpha,
                            power=0.80,
                            solve_for='n'
                        )
                        st.info(f"""
                        **How to fix:** Increase to **{result_fix['n_per_group']:,} per group** ({result_fix['total_n']:,} total) to achieve 80% power.

                        Current: {sample_n} per group → {result['power']:.0%} power
                        Needed: {result_fix['n_per_group']:,} per group → 80% power
                        """)
                        power_status = "Underpowered"

                    # Copy results button
                    results_text = f"""Independent t-test Power Check
Sample Size: {sample_n} per group
Effect Size (Cohen's d): {effect_size}
Significance Level: {alpha}
Power: {result['power']:.1%} ({power_status})
"""
                    if st.button("View Copy Results", key="copy_ttest_power"):
                        st.code(results_text, language=None)
                        st.caption("Results formatted above - copy with Ctrl+C / Cmd+C")

    elif base_test == "ANOVA":
        with col1:
            n_groups = st.number_input(
                "Number of groups",
                min_value=3, value=3, step=1,
                help="Number of independent groups to compare (minimum 3 for ANOVA)"
            )
            st.caption("Effect Size (ANOVA): Small=0.10 | Medium=0.25 | Large=0.40")
            with st.popover("ℹ️ Learn More About Effect Sizes"):
                st.markdown("""
                **Cohen's f Guidelines (ANOVA):**
                - **Small (0.10):** Subtle differences across groups
                - **Medium (0.25):** Moderate differences - Most common
                - **Large (0.40):** Obvious differences across groups

                **Typical scenarios:**
                - Small: Minor variations (e.g., 4 similar pricing tiers)
                - Medium: Standard group differences (e.g., low/med/high satisfaction)
                - Large: Extreme differences (e.g., beginner/intermediate/expert)

                **Unsure?** Use Medium (0.25)
                """)
            effect_size = st.slider(
                "Effect Size (Cohen's f)",
                0.1, 1.0, 0.25, 0.05,
                help="For ANOVA (Cohen's f). Small=0.10, Medium=0.25, Large=0.40."
            )
            if effect_size > 0.5:
                st.warning(f"""
                **Note:** Very large effect size (f={effect_size:.2f}).

                **When to use large ANOVA effects:**
                - Extreme group differences (e.g., different treatment protocols)
                - Strong experimental manipulations
                - Comparing very distinct populations

                **Most research:** Use f≤0.40. If unsure, use medium (0.25).
                """)

            alpha = st.selectbox(
                "Significance Level (α)",
                [0.01, 0.05, 0.10],
                index=1,
                key="anova_alpha",
                help="Probability of false positive. Standard is 0.05."
            )
        with col2:
            if solve_for == 'n':
                power = st.slider(
                    "Statistical Power (% chance of detecting real effect)",
                    0.5, 0.99, 0.80, 0.01,
                    key="anova_power",
                    help="Probability of detecting real effect. Standard is 0.80 (80%)."
                )
            else:
                st.write("**Effect Size Guidelines:**")
                st.caption("Small: f = 0.10")
                st.caption("Medium: f = 0.25")
                st.caption("Large: f = 0.40")

        if st.button("Calculate", type="primary", key="anova_calc"):
            st.markdown("---")
            st.subheader("Results")

            with st.spinner("Calculating Sample Size..."):
                calc = MeansPowerCalc(test_type='anova')

                if solve_for == 'n':
                    result = calc.calculate(
                        effect_size=effect_size,
                        alpha=alpha,
                        power=power,
                        solve_for='n',
                        n_groups=n_groups
                    )

                    st.session_state['last_calculation'] = {
                        'test': 'ANOVA',
                        'result': result,
                        'solve_for': 'n',
                        'n_groups': n_groups
                    }

                    st.success(f"**Required Sample Size:** {result['n_per_group']:,} per group ({result['total_n']:,} total)")

                    st.info(f"""
                    **This is the number of survey sample you need.**

                    Next step: Go to **Survey Sample Size** tab to calculate how many invitations to send.
                    """)

                    fig = plot_power_curve(calc, effect_sizes=[effect_size], alpha=alpha, n_groups=n_groups)
                    st.plotly_chart(fig, use_container_width=True)
                else:
                    result = calc.calculate(
                        effect_size=effect_size,
                        alpha=alpha,
                        n=sample_n,
                        solve_for='power',
                        n_groups=n_groups
                    )

                    st.session_state['last_calculation'] = {
                        'test': 'ANOVA',
                        'result': result,
                        'solve_for': 'power',
                        'sample_n': sample_n,
                        'n_groups': n_groups
                    }

                    if result['power'] >= 0.80:
                        st.success(f"**Power:** {result['power']:.1%} Success: Adequate for detecting f={effect_size}")
                    elif result['power'] >= 0.70:
                        st.warning(f"**Power:** {result['power']:.1%} Warning: Moderate - may miss some effects")
                        st.info("Consider increasing sample size or accepting lower effect size detectability.")
                    else:
                        st.error(f"**Power:** {result['power']:.1%} Error: Underpowered - likely to miss real effects")

                        # Calculate exact n needed for 80% power
                        calc_fix = MeansPowerCalc(test_type='anova')
                        result_fix = calc_fix.calculate(
                            effect_size=effect_size,
                            alpha=alpha,
                            power=0.80,
                            solve_for='n',
                            n_groups=n_groups
                        )
                        st.info(f"""
                        **How to fix:** Increase to **{result_fix['n_per_group']:,} per group** ({result_fix['total_n']:,} total) to achieve 80% power.

                        Current: {sample_n} per group → {result['power']:.0%} power
                        Needed: {result_fix['n_per_group']:,} per group → 80% power
                        """)

    elif base_test == "Correlation / Simple Regression":
        st.info("""
        **Correlation / Simple Regression** - Relationship between two continuous variables

        These are mathematically equivalent for power analysis:
        • **Correlation (r):** Measures strength of linear relationship (-1 to +1)
        • **Simple Regression (b):** Predicts Y from X (one predictor)

        Example: Correlation between customer satisfaction and loyalty score
        """)

        with col1:
            st.write("**Choose your effect size format:**")

            effect_format = st.radio(
                "Effect size as:",
                ["Correlation (r)", "R² (variance explained)", "Cohen's f²"],
                help="All are equivalent - choose the format you're most familiar with"
            )

            if effect_format == "Correlation (r)":
                r = st.slider(
                    "Expected correlation (r)",
                    0.01, 0.90, 0.30, 0.01,
                    help="Small=0.10, Medium=0.30, Large=0.50. Absolute value (direction doesn't matter for power)."
                )
                r_squared = r ** 2
                f_squared = r_squared / (1 - r_squared)
            elif effect_format == "R² (variance explained)":
                r_squared = st.slider(
                    "Expected R²",
                    0.01, 0.50, 0.10, 0.01,
                    help="Small=0.01 (1%), Medium=0.09 (9%), Large=0.25 (25%)"
                )
                r = r_squared ** 0.5
                f_squared = r_squared / (1 - r_squared)
            else:  # Cohen's f²
                f_squared = st.slider(
                    "Expected f²",
                    0.01, 0.50, 0.10, 0.01,
                    help="Small=0.02, Medium=0.15, Large=0.35"
                )
                r_squared = f_squared / (1 + f_squared)
                r = r_squared ** 0.5

            alpha = st.selectbox(
                "Significance Level (α)",
                [0.01, 0.05, 0.10],
                index=1,
                key="corr_alpha",
                help="Probability of false positive. Standard is 0.05."
            )

        with col2:
            if solve_for == 'n':
                power = st.slider(
                    "Statistical Power (% chance of detecting real effect)",
                    0.5, 0.99, 0.80, 0.01,
                    key="corr_power",
                    help="Probability of detecting real correlation. Standard is 0.80 (80%)."
                )

            st.write("**Effect size conversions:**")
            st.caption(f"r = {r:.3f}")
            st.caption(f"R² = {r_squared:.3f} ({r_squared*100:.1f}% variance)")
            st.caption(f"f² = {f_squared:.3f}")

        if st.button("Calculate", type="primary", key="corr_calc"):
            st.markdown("---")
            st.subheader("Results")

            with st.spinner("Calculating Sample Size..."):
                calc = RegressionPowerCalc(test_type='simple')

                if solve_for == 'n':
                    result = calc.calculate(
                        effect_size=f_squared,
                        alpha=alpha,
                        power=power,
                        solve_for='n',
                        n_predictors=1
                    )

                    st.session_state['last_calculation'] = {
                        'test': 'Correlation / Simple Regression',
                        'result': result,
                        'solve_for': 'n',
                        'r': r,
                        'r_squared': r_squared
                    }

                    st.success(f"**Required Sample Size:** {result['n']:,} participants")

                    st.info(f"""
                    **Study parameters:**
                    • Correlation: r = {r:.3f}
                    • Variance explained: R² = {r_squared:.3f} ({r_squared*100:.1f}%)
                    • Effect size: f² = {f_squared:.3f}
                    • Power: {power:.0%}
                    • Alpha: {alpha}

                    **Interpretation:**
                    {r:.3f} correlation means the two variables share {r_squared*100:.1f}% of their variance.

                    **Next step:** Go to **Survey Sample Size** to calculate invitations needed.
                    """)

                    fig = plot_power_curve(calc, effect_sizes=[f_squared], alpha=alpha, n_predictors=1)
                    st.plotly_chart(fig, use_container_width=True)
                else:
                    result = calc.calculate(
                        effect_size=f_squared,
                        alpha=alpha,
                        n=sample_n,
                        solve_for='power',
                        n_predictors=1
                    )

                    st.session_state['last_calculation'] = {
                        'test': 'Correlation / Simple Regression',
                        'result': result,
                        'solve_for': 'power',
                        'sample_n': sample_n,
                        'r': r
                    }

                    if result['power'] >= 0.80:
                        st.success(f"**Power:** {result['power']:.1%} Success: Adequate for detecting r={r:.3f}")
                    elif result['power'] >= 0.70:
                        st.warning(f"**Power:** {result['power']:.1%} Warning: Moderate - may miss some effects")
                        st.info("Consider increasing sample size or accepting lower effect size detectability.")
                    else:
                        st.error(f"**Power:** {result['power']:.1%} Error: Underpowered - likely to miss real effects")

                        # Calculate exact n needed for 80% power
                        calc_fix = RegressionPowerCalc(test_type='simple')
                        result_fix = calc_fix.calculate(
                            effect_size=f_squared,
                            alpha=alpha,
                            power=0.80,
                            solve_for='n',
                            n_predictors=1
                        )
                        st.info(f"""
                        **How to fix:** Increase to **{result_fix['n']:,} participants** to achieve 80% power.

                        Current: {sample_n} participants → {result['power']:.0%} power
                        Needed: {result_fix['n']:,} participants → 80% power
                        """)

                    st.info(f"""
                    **Minimum detectable correlation:**
                    With n={sample_n}, you can reliably detect correlations of r ≥ {(result.get('effect_size', f_squared) / (1 + result.get('effect_size', f_squared)))**0.5:.3f}
                    """)

        st.markdown("---")
        st.markdown("""
        **Common correlation interpretations (Cohen's guidelines):**
        - **Small:** r = 0.10 (1% shared variance)
        - **Medium:** r = 0.30 (9% shared variance)
        - **Large:** r = 0.50 (25% shared variance)

        **Note:** In many fields, even small correlations can be meaningful if:
        - Large sample size allows precise estimation
        - Cumulative effects matter (e.g., public health)
        - Outcome is important (e.g., safety, revenue)

        **Simple regression equivalent:**
        Testing correlation r = testing whether regression slope β ≠ 0
        """)

    elif base_test == "Multiple Regression":
        with col1:
            n_predictors = st.number_input(
                "Number of predictors",
                min_value=1, value=3, step=1,
                help="Number of independent variables (e.g., age, gender, income = 3 predictors)"
            )
            if n_predictors > 10:
                min_recommended = n_predictors * 15
                st.warning(f"""
                **Problem:** Many predictors ({n_predictors}) increases overfitting risk.

                **Rule of thumb:** 10-20 observations per predictor
                - Minimum: {n_predictors * 10:,} participants
                - Recommended: {min_recommended:,} participants

                **How to fix (choose one):**
                1. Reduce to 5-10 key predictors (combine or remove less important ones)
                2. Increase sample size to {min_recommended:,}+
                3. Use regularization (LASSO/Ridge regression) if keeping many predictors
                """)

            st.caption("Effect Size (f²): Small=0.02 | Medium=0.15 | Large=0.35")
            with st.popover("ℹ️ Learn More About Effect Sizes"):
                st.markdown("""
                **Cohen's f² Guidelines (Regression):**
                - **Small (0.02):** R²=2% variance explained
                - **Medium (0.15):** R²=13% variance explained
                - **Large (0.35):** R²=26% variance explained

                **Context:**
                - Small effects are common in complex real-world phenomena
                - Medium is typical for social science research
                - Large effects are rare (strong predictive models)

                **Conversion:** f² = R² / (1 - R²)

                **Unsure?** Use Medium (0.15)
                """)
            effect_size = st.slider(
                "Effect Size (f²)",
                0.01, 0.50, 0.15, 0.01,
                help="Cohen's f². Small=0.02, Medium=0.15, Large=0.35. Measures variance explained by predictors."
            )
            alpha = st.selectbox(
                "Significance Level (α)",
                [0.01, 0.05, 0.10],
                index=1,
                key="reg_alpha",
                help="Probability of false positive. Standard is 0.05."
            )
        with col2:
            if solve_for == 'n':
                power = st.slider(
                    "Statistical Power (% chance of detecting real effect)",
                    0.5, 0.99, 0.80, 0.01,
                    key="reg_power",
                    help="Probability of detecting real effect. Standard is 0.80 (80%)."
                )
            else:
                st.write("**Effect Size Guidelines:**")
                st.caption("Small: f² = 0.02 (R² = 2%)")
                st.caption("Medium: f² = 0.15 (R² = 13%)")
                st.caption("Large: f² = 0.35 (R² = 26%)")

        if st.button("Calculate", type="primary", key="reg_calc"):
            st.markdown("---")
            st.subheader("Results")

            with st.spinner("Calculating Sample Size..."):
                calc = RegressionPowerCalc(test_type='multiple')

                if solve_for == 'n':
                    result = calc.calculate(
                        effect_size=effect_size,
                        alpha=alpha,
                        power=power,
                        solve_for='n',
                        n_predictors=n_predictors
                    )

                    st.session_state['last_calculation'] = {
                        'test': 'Multiple Regression',
                        'result': result,
                        'solve_for': 'n',
                        'n_predictors': n_predictors
                    }

                    st.success(f"**Required Sample Size:** {result['n']:,} participants")
                    st.info(f"""
                    **R² = {result.get('r_squared', effect_size / (1 + effect_size)):.2%}** (variance explained by {n_predictors} predictors)

                    **Next step:** Go to **Survey Sample Size** to calculate invitations needed.
                    """)

                    fig = plot_power_curve(calc, effect_sizes=[effect_size], alpha=alpha, n_predictors=n_predictors)
                    st.plotly_chart(fig, use_container_width=True)
                else:
                    result = calc.calculate(
                        effect_size=effect_size,
                        alpha=alpha,
                        n=sample_n,
                        solve_for='power',
                        n_predictors=n_predictors
                    )

                    st.session_state['last_calculation'] = {
                        'test': 'Multiple Regression',
                        'result': result,
                        'solve_for': 'power',
                        'sample_n': sample_n,
                        'n_predictors': n_predictors
                    }

                    r_squared = result.get('r_squared', effect_size / (1 + effect_size))
                    if result['power'] >= 0.80:
                        st.success(f"**Power:** {result['power']:.1%} Success: Adequate for detecting R²={r_squared:.1%}")
                    elif result['power'] >= 0.70:
                        st.warning(f"**Power:** {result['power']:.1%} Warning: Moderate - may miss some effects")
                        st.info("Consider increasing sample size or reducing number of predictors.")
                    else:
                        st.error(f"**Power:** {result['power']:.1%} Error: Underpowered - likely to miss real effects")

                        # Calculate exact n needed for 80% power
                        calc_fix = RegressionPowerCalc(test_type='multiple')
                        result_fix = calc_fix.calculate(
                            effect_size=effect_size,
                            alpha=alpha,
                            power=0.80,
                            solve_for='n',
                            n_predictors=n_predictors
                        )
                        st.info(f"""
                        **How to fix (choose one):**
                        1. **Increase sample:** {result_fix['n']:,} participants → 80% power
                        2. **Reduce predictors:** Try removing least important predictors (target 3-5 key predictors)

                        Current: {sample_n} participants, {n_predictors} predictors → {result['power']:.0%} power
                        Option 1: {result_fix['n']:,} participants, {n_predictors} predictors → 80% power
                        """)

    elif base_test == "Logistic Regression":
        st.info("""
        **Logistic Regression** - Predicting binary outcomes (Yes/No, Success/Failure)

        Example: Predict whether customer will churn (Yes/No) based on usage, satisfaction, price
        """)

        with col1:
            n_predictors = st.number_input(
                "Number of predictors",
                min_value=1, value=5, step=1,
                help="Number of independent variables (e.g., age, income, usage, satisfaction = 4 predictors)"
            )

            st.caption("Effect Size: Small=0.02 | Medium=0.15 | Large=0.35")
            effect_size = st.slider(
                "Effect size (f²)",
                0.01, 0.50, 0.15, 0.01,
                help="Cohen's f² for logistic regression. Small=0.02, Medium=0.15, Large=0.35"
            )

            alpha = st.selectbox(
                "Significance Level (α)",
                [0.01, 0.05, 0.10],
                index=1,
                key="logit_alpha",
                help="Probability of false positive. Standard is 0.05."
            )

        with col2:
            if solve_for == 'n':
                power = st.slider(
                    "Statistical Power (% chance of detecting real effect)",
                    0.5, 0.99, 0.80, 0.01,
                    key="logit_power",
                    help="Probability of detecting real effect. Standard is 0.80 (80%)."
                )
            else:
                sample_n = st.number_input(
                    "Sample size",
                    min_value=50, value=200, step=10,
                    key="logit_sample",
                    help="Current sample size to evaluate power"
                )

        if st.button("Calculate", type="primary", key="logit_calc"):
            st.markdown("---")
            st.subheader("Results")

            with st.spinner("Calculating Sample Size..."):
                calc = LogisticPowerCalc(test_type='binary')

                if solve_for == 'n':
                    result = calc.calculate(
                        effect_size=effect_size,
                        alpha=alpha,
                        power=power,
                        solve_for='n',
                        n_predictors=n_predictors
                    )

                    st.session_state['last_calculation'] = {
                        'test': 'Binary Logistic Regression',
                        'result': result,
                        'solve_for': 'n',
                        'n_predictors': n_predictors
                    }

                    st.success(f"**Required Sample Size:** {result['n']:,} participants")
                    st.info(f"""
                    **Rule of thumb:** {result['rule']}

                    **Assumptions:** {result['assumptions']}
                    """)

                else:  # solve_for == 'power'
                    result = calc.calculate(
                        effect_size=effect_size,
                        alpha=alpha,
                        n=sample_n,
                        solve_for='power',
                        n_predictors=n_predictors
                    )

                    st.session_state['last_calculation'] = {
                        'test': 'Binary Logistic Regression',
                        'result': result,
                        'solve_for': 'power',
                        'sample_n': sample_n
                    }

                    if result['power'] >= 0.80:
                        st.success(f"**Power:** {result['power']:.1%} ✓ Adequate")
                    elif result['power'] >= 0.70:
                        st.warning(f"**Power:** {result['power']:.1%} ⚠ Moderate")
                    else:
                        st.error(f"**Power:** {result['power']:.1%} ✗ Underpowered")

    elif base_test == "Ordinal Regression":
        st.info("""
        **Ordinal Regression** - Predicting ordered categorical outcomes

        Use when outcome has natural order (e.g., Likert scales, severity ratings)

        Example: Predict customer satisfaction level (Very Low, Low, Medium, High, Very High)
        based on service quality, price, and support
        """)

        with col1:
            n_predictors = st.number_input(
                "Number of predictors",
                min_value=1, value=5, step=1,
                help="Number of independent variables predicting the outcome"
            )

            n_categories = st.number_input(
                "Number of outcome categories",
                min_value=3, value=5, step=1,
                help="Number of ordered levels (e.g., 5-point Likert: Strongly Disagree to Strongly Agree)"
            )

            st.write("**Category distribution (%):**")
            st.caption("Estimate how responses will be distributed across categories")

            # Auto-balance button
            if 'ord_categories_dist' not in st.session_state:
                st.session_state.ord_categories_dist = None

            if st.button("Auto-balance to 100%", key="ord_autobalance", help="Proportionally adjust to sum to 100%"):
                # Proportionally adjust existing values instead of resetting
                if st.session_state.ord_categories_dist:
                    current_values = st.session_state.ord_categories_dist
                    total = sum(current_values)
                    if total > 0:
                        # Scale proportionally
                        st.session_state.ord_categories_dist = [round(v * 100 / total) for v in current_values]
                st.rerun()

            # Get distribution across categories
            categories_dist = []
            total_pct = 0
            for i in range(n_categories):
                default_pct = 100 // n_categories
                # Use session state if available
                if st.session_state.ord_categories_dist and i < len(st.session_state.ord_categories_dist):
                    default_pct = st.session_state.ord_categories_dist[i]

                pct = st.number_input(
                    f"Category {i+1} %",
                    min_value=1, max_value=100,
                    value=default_pct,
                    key=f"ord_cat_{i}",
                    help=f"Percentage in category {i+1}"
                )
                categories_dist.append(pct)
                total_pct += pct

            # Store current values
            st.session_state.ord_categories_dist = categories_dist

            # Real-time validation
            pct_valid = abs(total_pct - 100) <= 1
            if not pct_valid:
                st.error(f"**Problem:** Category percentages must add up to 100% (currently {total_pct}%)")
                st.info(f"**How to fix:** Click 'Auto-balance' above to proportionally adjust your values to 100%, or manually adjust the numbers above.")
            elif abs(total_pct - 100) < 1 and abs(total_pct - 100) > 0:
                st.success(f"✓ Categories sum to {total_pct}% (close enough)")

        with col2:
            st.caption("Effect Size: Small=0.02 | Medium=0.15 | Large=0.35")
            effect_size = st.slider(
                "Effect size (f²)",
                0.01, 0.50, 0.15, 0.01,
                help="Cohen's f² for ordinal regression. Small=0.02, Medium=0.15, Large=0.35",
                key="ord_effect"
            )

            alpha = st.selectbox(
                "Significance Level (α)",
                [0.01, 0.05, 0.10],
                index=1,
                key="ord_alpha",
                help="Probability of false positive. Standard is 0.05."
            )

            if solve_for == 'n':
                power = st.slider(
                    "Statistical Power (% chance of detecting real effect)",
                    0.5, 0.99, 0.80, 0.01,
                    key="ord_power",
                    help="Probability of detecting real effect. Standard is 0.80 (80%)."
                )
            else:
                sample_n = st.number_input(
                    "Sample size",
                    min_value=50, value=200, step=10,
                    key="ord_sample",
                    help="Current sample size to evaluate power"
                )

        # Disable calculate if percentages invalid
        if st.button("Calculate", type="primary", key="ord_calc", disabled=not pct_valid):
            st.markdown("---")
            st.subheader("Results")

            with st.spinner("Calculating Sample Size..."):
                calc = LogisticPowerCalc(test_type='ordinal')

                if solve_for == 'n':
                    result = calc.calculate(
                        effect_size=effect_size,
                        alpha=alpha,
                        power=power,
                        solve_for='n',
                        n_predictors=n_predictors,
                        n_categories=n_categories
                    )

                    st.session_state['last_calculation'] = {
                        'test': 'Ordinal Logistic Regression',
                        'result': result,
                        'solve_for': 'n',
                        'n_predictors': n_predictors
                    }

                    st.success(f"**Required Sample Size:** {result['n']:,} participants")
                    st.info(f"""
                    **Rule of thumb:** {result['rule']}

                    **Assumptions:** {result['assumptions']}
                    """)

                else:  # solve_for == 'power'
                    result = calc.calculate(
                        effect_size=effect_size,
                        alpha=alpha,
                        n=sample_n,
                        solve_for='power',
                        n_predictors=n_predictors,
                        n_categories=n_categories
                    )

                    st.session_state['last_calculation'] = {
                        'test': 'Ordinal Logistic Regression',
                        'result': result,
                        'solve_for': 'power',
                        'sample_n': sample_n
                    }

                    if result['power'] >= 0.80:
                        st.success(f"**Power:** {result['power']:.1%} ✓ Adequate")
                    elif result['power'] >= 0.70:
                        st.warning(f"**Power:** {result['power']:.1%} ⚠ Moderate")
                    else:
                        st.error(f"**Power:** {result['power']:.1%} ✗ Underpowered")

    elif base_test == "Multinomial Regression":
        st.info("""
        **Multinomial Regression** - Predicting unordered categorical outcomes

        Use when outcome has NO natural order (e.g., choice of product, preferred channel)

        Example: Predict which product customer will choose (Product A, B, or C)
        based on demographics, usage patterns, and preferences
        """)

        with col1:
            n_predictors = st.number_input(
                "Number of predictors",
                min_value=1, value=5, step=1,
                help="Number of independent variables predicting the outcome"
            )

            n_outcomes = st.number_input(
                "Number of outcome categories",
                min_value=3, value=4, step=1,
                help="Number of unordered choices (e.g., 3 products, 4 channels). One will be reference category."
            )

            st.write("**Outcome distribution (%):**")
            st.caption("Estimate how responses will be distributed across outcomes")

            # Auto-balance button
            if 'multi_outcomes_dist' not in st.session_state:
                st.session_state.multi_outcomes_dist = None

            if st.button("Auto-balance to 100%", key="multi_autobalance", help="Proportionally adjust to sum to 100%"):
                # Proportionally adjust existing values
                if st.session_state.multi_outcomes_dist:
                    current_values = st.session_state.multi_outcomes_dist
                    total = sum(current_values)
                    if total > 0:
                        st.session_state.multi_outcomes_dist = [round(v * 100 / total) for v in current_values]
                st.rerun()

            # Get distribution across outcomes
            outcomes_dist = []
            total_pct = 0
            for i in range(n_outcomes):
                default_pct = 100 // n_outcomes
                # Use session state if available
                if st.session_state.multi_outcomes_dist and i < len(st.session_state.multi_outcomes_dist):
                    default_pct = st.session_state.multi_outcomes_dist[i]

                pct = st.number_input(
                    f"Outcome {i+1} %",
                    min_value=1, max_value=100,
                    value=default_pct,
                    key=f"multi_out_{i}",
                    help=f"Percentage choosing outcome {i+1}"
                )
                outcomes_dist.append(pct)
                total_pct += pct

            # Store current values
            st.session_state.multi_outcomes_dist = outcomes_dist

            # Real-time validation
            outcomes_valid = abs(total_pct - 100) <= 1
            if not outcomes_valid:
                st.error(f"**Problem:** Outcome percentages must add up to 100% (currently {total_pct}%)")
                st.info(f"**How to fix:** Click 'Auto-balance' above to proportionally adjust your values to 100%, or manually adjust the numbers above.")
            elif abs(total_pct - 100) < 1 and abs(total_pct - 100) > 0:
                st.success(f"✓ Outcomes sum to {total_pct}% (close enough)")

        with col2:
            st.caption("Effect Size: Small=0.02 | Medium=0.15 | Large=0.35")
            effect_size = st.slider(
                "Effect size (f²)",
                0.01, 0.50, 0.15, 0.01,
                help="Cohen's f² for multinomial regression. Small=0.02, Medium=0.15, Large=0.35",
                key="multi_effect"
            )

            alpha = st.selectbox(
                "Significance Level (α)",
                [0.01, 0.05, 0.10],
                index=1,
                key="multi_alpha",
                help="Probability of false positive. Standard is 0.05."
            )

            if solve_for == 'n':
                power = st.slider(
                    "Statistical Power (% chance of detecting real effect)",
                    0.5, 0.99, 0.80, 0.01,
                    key="multi_power",
                    help="Probability of detecting real effect. Standard is 0.80 (80%)."
                )
            else:
                sample_n = st.number_input(
                    "Sample size",
                    min_value=100, value=300, step=20,
                    key="multi_sample",
                    help="Current sample size to evaluate power"
                )

        # Disable calculate if percentages invalid
        if st.button("Calculate", type="primary", key="multi_calc", disabled=not outcomes_valid):
            st.markdown("---")
            st.subheader("Results")

            with st.spinner("Calculating Sample Size..."):
                calc = LogisticPowerCalc(test_type='multinomial')

                if solve_for == 'n':
                    result = calc.calculate(
                        effect_size=effect_size,
                        alpha=alpha,
                        power=power,
                        solve_for='n',
                        n_predictors=n_predictors,
                        n_categories=n_outcomes
                    )

                    st.session_state['last_calculation'] = {
                        'test': 'Multinomial Logistic Regression',
                        'result': result,
                        'solve_for': 'n',
                        'n_predictors': n_predictors
                    }

                    st.success(f"**Required Sample Size:** {result['n']:,} participants")
                    st.info(f"""
                    **Rule of thumb:** {result['rule']}

                    **Assumptions:** {result['assumptions']}

                    **Note:** Multinomial regression requires more sample than binary or ordinal
                    due to estimating (k-1) comparisons simultaneously.
                    """)

                else:  # solve_for == 'power'
                    result = calc.calculate(
                        effect_size=effect_size,
                        alpha=alpha,
                        n=sample_n,
                        solve_for='power',
                        n_predictors=n_predictors,
                        n_categories=n_outcomes
                    )

                    st.session_state['last_calculation'] = {
                        'test': 'Multinomial Logistic Regression',
                        'result': result,
                        'solve_for': 'power',
                        'sample_n': sample_n
                    }

                    if result['power'] >= 0.80:
                        st.success(f"**Power:** {result['power']:.1%} ✓ Adequate")
                    elif result['power'] >= 0.70:
                        st.warning(f"**Power:** {result['power']:.1%} ⚠ Moderate")
                    else:
                        st.error(f"**Power:** {result['power']:.1%} ✗ Underpowered")

    elif base_test == "Chi-Square":
        st.info("""
        **Chi-Square Test** - Testing association between categorical variables

        Example: Is there a relationship between customer type (3 categories) and satisfaction level (5 categories)?
        """)

        with col1:
            n_rows = st.number_input(
                "Number of rows (first variable)",
                min_value=2, value=3, step=1,
                help="Categories in first variable (e.g., 3 customer types: New, Regular, VIP)"
            )

            n_cols = st.number_input(
                "Number of columns (second variable)",
                min_value=2, value=4, step=1,
                help="Categories in second variable (e.g., 4 satisfaction levels: Low, Medium, High, Very High)"
            )

            effect_size = st.selectbox(
                "Effect size (Cramer's V / w)",
                ["Small (0.1)", "Medium (0.3)", "Large (0.5)"],
                index=1,
                help="Small=0.1 (subtle association), Medium=0.3 (moderate), Large=0.5 (strong association)"
            )

        with col2:
            alpha = st.selectbox(
                "Significance Level (α)",
                [0.01, 0.05, 0.10],
                index=1,
                key="chi_alpha",
                help="Probability of false positive. Standard is 0.05."
            )

            power = st.slider(
                "Statistical Power (% chance of detecting real effect)",
                0.5, 0.99, 0.80, 0.01,
                key="chi_power",
                help="Probability of detecting real association. Standard is 0.80 (80%)."
            )

            min_expected = st.slider(
                "Minimum expected cell count",
                1, 10, 5, 1,
                help="Minimum expected count per cell. Standard: 5. Conservative: 10. With <5, chi-square may be unreliable."
            )

        # Parse effect size
        if "Small" in effect_size:
            w = 0.1
        elif "Medium" in effect_size:
            w = 0.3
        else:
            w = 0.5

        # Calculate using chi-square power calc
        calc = ProportionsPowerCalc(test_type='chi_square')
        df = (n_rows - 1) * (n_cols - 1)

        result = calc.calculate(
            effect_size=w,
            alpha=alpha,
            power=power,
            solve_for='n',
            df=df
        )

        total_cells = n_rows * n_cols
        min_n_from_cells = total_cells * min_expected

        recommended_n = max(result.get('n', 0), min_n_from_cells)

        st.success(f"**Required Sample Size:** {recommended_n:,} participants")

        st.info(f"""
        **Breakdown:**
        • Contingency table: {n_rows} × {n_cols} = {total_cells} cells
        • Degrees of freedom: ({n_rows}-1) × ({n_cols}-1) = {df}
        • Effect size (w): {w}
        • Min expected per cell: {min_expected}

        **Average per cell:** {int(recommended_n / total_cells)} participants
        """)

        st.warning("""
        **Important:**
        • All cells should have expected count ≥5 for valid chi-square
        • For 2×2 tables, consider Fisher's exact test if counts are small
        • Larger tables (many cells) require much larger samples
        """)

    elif base_test in ["Non-Parametric: Mann-Whitney U", "Non-Parametric: Wilcoxon",
                        "Non-Parametric: Kruskal-Wallis", "Non-Parametric: Friedman"]:

        # Determine test type
        if "Mann-Whitney" in base_test:
            test_type = 'mann_whitney'
            test_name = "Mann-Whitney U Test"
            desc = "Non-parametric alternative to independent t-test (compare 2 groups using ranks)"
            parametric_equiv = "Independent t-test"
        elif "Wilcoxon" in base_test:
            test_type = 'wilcoxon'
            test_name = "Wilcoxon Signed-Rank Test"
            desc = "Non-parametric alternative to paired t-test (compare matched pairs using ranks)"
            parametric_equiv = "Paired t-test"
        elif "Kruskal-Wallis" in base_test:
            test_type = 'kruskal_wallis'
            test_name = "Kruskal-Wallis H Test"
            desc = "Non-parametric alternative to ANOVA (compare 3+ groups using ranks)"
            parametric_equiv = "One-way ANOVA"
        else:  # Friedman
            test_type = 'friedman'
            test_name = "Friedman Test"
            desc = "Non-parametric alternative to repeated measures ANOVA (compare repeated measures using ranks)"
            parametric_equiv = "Repeated measures ANOVA"

        st.info(f"""
        **{test_name}** - {desc}

        **Parametric equivalent:** {parametric_equiv}

        **When to use:**
        • Ordinal data (e.g., Likert scales without assuming intervals)
        • Severely skewed distributions
        • Outliers that can't be removed
        • Violated parametric assumptions
        """)

        with col1:
            if test_type in ['kruskal_wallis', 'friedman']:
                n_groups = st.number_input(
                    "Number of groups",
                    min_value=3, value=3, step=1,
                    help="Number of groups to compare"
                )
            else:
                n_groups = 2

            # Effect size - use Cohen's d scale for consistency
            if test_type in ['mann_whitney', 'wilcoxon']:
                st.caption("Effect Size (Cohen's d): Small=0.2 | Medium=0.5 | Large=0.8")
                effect_size = st.slider(
                    "Effect Size (Cohen's d)",
                    0.1, 1.5, 0.5, 0.05,
                    help="Same scale as parametric tests. Small=0.2, Medium=0.5, Large=0.8"
                )
            else:  # kruskal_wallis, friedman
                st.caption("Effect Size (Cohen's f): Small=0.1 | Medium=0.25 | Large=0.4")
                effect_size = st.slider(
                    "Effect Size (Cohen's f)",
                    0.1, 1.0, 0.25, 0.05,
                    help="Same scale as ANOVA. Small=0.1, Medium=0.25, Large=0.4"
                )

            alpha = st.selectbox(
                "Significance Level (α)",
                [0.01, 0.05, 0.10],
                index=1,
                key=f"{test_type}_alpha",
                help="Probability of false positive. Standard is 0.05."
            )

        with col2:
            if solve_for == 'n':
                power = st.slider(
                    "Statistical Power (% chance of detecting real effect)",
                    0.5, 0.99, 0.80, 0.01,
                    key=f"{test_type}_power",
                    help="Probability of detecting real effect. Standard is 0.80 (80%)."
                )
            else:
                sample_n = st.number_input(
                    "Sample size per group",
                    min_value=10, value=50, step=5,
                    key=f"{test_type}_sample",
                    help="Current sample size to evaluate power"
                )

        if st.button("Calculate", type="primary", key=f"{test_type}_calc"):
            st.markdown("---")
            st.subheader("Results")

            with st.spinner("Calculating Sample Size..."):
                calc = NonParametricPowerCalc(test_type=test_type)

                if solve_for == 'n':
                    result = calc.calculate(
                        effect_size=effect_size,
                        alpha=alpha,
                        power=power,
                        solve_for='n',
                        n_groups=n_groups if test_type in ['kruskal_wallis', 'friedman'] else None
                    )

                    st.session_state['last_calculation'] = {
                        'test': test_name,
                        'result': result,
                        'solve_for': 'n'
                    }

                    if 'n_per_group' in result:
                        st.success(f"**Required Sample Size:** {result['n_per_group']:,} per group ({result['total_n']:,} total)")
                    else:
                        st.success(f"**Required Sample Size:** {result['n']:,} participants")

                    st.info(f"""
                    **Efficiency vs {result['parametric_equivalent']}:**
                    {result['efficiency']}

                    **When to use non-parametric:**
                    {result['note']}
                    """)

                else:  # solve_for == 'power'
                    result = calc.calculate(
                        effect_size=effect_size,
                        alpha=alpha,
                        n=sample_n,
                        solve_for='power',
                        n_groups=n_groups if test_type in ['kruskal_wallis', 'friedman'] else None
                    )

                    st.session_state['last_calculation'] = {
                        'test': test_name,
                        'result': result,
                        'solve_for': 'power',
                        'sample_n': sample_n
                    }

                    if result['power'] >= 0.80:
                        st.success(f"**Power:** {result['power']:.1%} ✓ Adequate")
                    elif result['power'] >= 0.70:
                        st.warning(f"**Power:** {result['power']:.1%} ⚠ Moderate")
                    else:
                        st.error(f"**Power:** {result['power']:.1%} ✗ Underpowered")

    elif base_test == "Proportions":
        with col1:
            st.info("Comparing proportions between two groups (e.g., conversion rates)")
            p1 = st.slider(
                "Group 1 proportion",
                0.01, 0.99, 0.50, 0.01,
                help="Expected proportion in first group (e.g., 0.50 = 50%)"
            )
            p2 = st.slider(
                "Group 2 proportion",
                0.01, 0.99, 0.60, 0.01,
                help="Expected proportion in second group (e.g., 0.60 = 60%)"
            )
            alpha = st.selectbox(
                "Significance Level (α)",
                [0.01, 0.05, 0.10],
                index=1,
                key="prop_alpha",
                help="Probability of false positive. Standard is 0.05."
            )
        with col2:
            power = st.slider(
                "Statistical Power (% chance of detecting real effect)",
                0.5, 0.99, 0.80, 0.01,
                key="prop_power",
                help="Probability of detecting real difference. Standard is 0.80 (80%)."
            )
            ratio = st.slider(
                "Group size ratio",
                0.5, 2.0, 1.0, 0.1,
                help="Ratio of group sizes. 1.0 = equal groups, 2.0 = Group 1 twice as large"
            )

        if st.button("Calculate", type="primary", key="prop_calc"):
            calc = ProportionsPowerCalc(test_type='two_proportions')

            result = calc.calculate(
                p1=p1,
                p2=p2,
                alpha=alpha,
                power=power,
                solve_for='n',
                ratio=ratio
            )
            st.success(f"**Required Sample Size:** {result['n1']:,} in Group 1, {result['n2']:,} in Group 2 ({result['total_n']:,} total)")
            st.info(f"**Effect size (h):** {result.get('effect_size', abs(p2-p1)):.3f}")

    elif base_test == "PCA/EFA":
        st.info("""
        **Principal Component Analysis (PCA) / Exploratory Factor Analysis (EFA)**

        Used to identify underlying dimensions in your data (data reduction).
        """)

        with col1:
            n_items = st.number_input(
                "Number of items/variables",
                min_value=3, value=20, step=1,
                help="Total number of survey items or variables you're analyzing (e.g., 20 Likert items)"
            )

            rule = st.selectbox(
                "Sample size rule",
                ["Conservative (20:1)", "Standard (10:1)", "Minimum (5:1)"],
                index=1,
                help="""Rules of thumb for items-to-participants ratio:

• Conservative (20:1): 20 participants per item - Very reliable
• Standard (10:1): 10 participants per item - Commonly used
• Minimum (5:1): 5 participants per item - Absolute minimum"""
            )

        with col2:
            if rule == "Conservative (20:1)":
                ratio = 20
            elif rule == "Standard (10:1)":
                ratio = 10
            else:
                ratio = 5

            recommended_n = n_items * ratio
            absolute_min = max(100, n_items * 2)

            st.metric("Recommended Sample Size", f"{recommended_n:,}")
            st.caption(f"Based on {ratio}:1 ratio")

            st.warning(f"**Absolute minimum:** {absolute_min} participants")

            st.info("""
            **Additional guidelines:**
            • Minimum 100 participants regardless of items
            • Aim for 200-300 for stable factor structures
            • More participants needed if you expect weak correlations
            """)

    elif base_test == "CFA":
        st.info("""
        **Confirmatory Factor Analysis (CFA)**

        Used to test a pre-specified factor structure (hypothesis testing).
        """)

        with col1:
            n_factors = st.number_input(
                "Number of factors/latent variables",
                min_value=1, value=3, step=1,
                help="Number of latent constructs you're testing (e.g., 3 factors: Satisfaction, Quality, Value)"
            )

            items_per_factor = st.number_input(
                "Average items per factor",
                min_value=2, value=4, step=1,
                help="Average number of observed items measuring each factor (minimum 3 recommended)"
            )

            complexity = st.selectbox(
                "Model complexity",
                ["Simple (independent factors)", "Moderate (some correlations)", "Complex (cross-loadings, higher-order)"],
                index=1,
                help="Simple: Factors uncorrelated. Complex: Many parameters, cross-loadings, hierarchical structure"
            )

        with col2:
            total_items = n_factors * items_per_factor

            # Base calculation: 10-20 observations per estimated parameter
            if complexity == "Simple (independent factors)":
                params = total_items + n_factors  # loadings + variances
                multiplier = 10
            elif complexity == "Moderate (some correlations)":
                params = total_items + n_factors + (n_factors * (n_factors - 1) / 2)
                multiplier = 15
            else:
                params = total_items * 1.5 + n_factors * 2
                multiplier = 20

            recommended_n = int(params * multiplier)
            recommended_n = max(200, recommended_n)  # Minimum 200 for CFA

            st.metric("Recommended Sample Size", f"{recommended_n:,}")
            st.caption(f"Based on {int(params)} estimated parameters")

            st.warning("**Absolute minimum:** 200 participants for any CFA")

            st.info("""
            **Fit index sample size requirements:**
            • CFI/TLI: Minimum 200
            • RMSEA: Minimum 100 (but 200+ recommended)
            • Chi-square test: 200-400+ for reliable results

            **Rule of thumb:** 10-20 observations per estimated parameter
            """)

    elif base_test == "LCA":
        st.info("""
        **Latent Class Analysis (LCA)**

        Used to identify unobserved subgroups (classes) in your data.
        """)

        with col1:
            n_classes = st.number_input(
                "Expected number of classes",
                min_value=2, value=3, step=1,
                help="Number of latent classes you expect (e.g., 3 user types)"
            )

            n_indicators = st.number_input(
                "Number of indicators",
                min_value=3, value=8, step=1,
                help="Number of observed variables used to form classes (e.g., 8 behavioral indicators)"
            )

            indicator_type = st.selectbox(
                "Indicator type",
                ["Binary (Yes/No)", "Categorical (3-5 levels)", "Mixed"],
                help="Type of variables: Binary is simplest, categorical requires more data"
            )

            smallest_class = st.slider(
                "Expected smallest class size (%)",
                5, 40, 15, 5,
                help="Percentage of sample in smallest class. Smaller classes need larger total samples."
            )

        with col2:
            # LCA sample size depends on number of cells in contingency table
            if indicator_type == "Binary (Yes/No)":
                cells = 2 ** n_indicators
                base_n = cells * 5  # 5 observations per cell (minimum)
            elif indicator_type == "Categorical (3-5 levels)":
                cells = 4 ** n_indicators
                base_n = cells * 5
            else:
                cells = 3 ** n_indicators
                base_n = cells * 5

            # Adjust for smallest class
            min_per_class = 50  # Minimum 50 in smallest class
            total_from_class = int(min_per_class / (smallest_class / 100))

            recommended_n = max(base_n, total_from_class, 500)

            st.metric("Recommended Sample Size", f"{recommended_n:,}")

            if recommended_n > 5000:
                st.warning(f"Warning: Large sample needed due to complexity ({n_indicators} indicators)")

            st.info(f"""
            **Sample size breakdown:**
            • Minimum per class: 50 participants
            • Smallest class ({smallest_class}%): {int(recommended_n * smallest_class / 100)} participants
            • Largest class (~{100-smallest_class}%): {int(recommended_n * (100-smallest_class) / 100)} participants

            **Rules of thumb:**
            • Minimum 500 participants for stable LCA
            • 50+ participants in smallest class
            • More indicators = more participants needed
            • Binary indicators easier than categorical
            """)

    elif base_test == "Cluster Analysis":
        st.info("""
        **Cluster Analysis**

        Used to group similar observations (exploratory segmentation).
        """)

        with col1:
            n_clusters = st.number_input(
                "Expected number of clusters",
                min_value=2, value=4, step=1,
                help="Number of clusters/segments you're looking for (e.g., 4 customer segments)"
            )

            n_variables = st.number_input(
                "Number of clustering variables",
                min_value=2, value=10, step=1,
                help="Number of variables used for clustering (e.g., 10 behavioral measures)"
            )

            method = st.selectbox(
                "Clustering method",
                ["K-means (most common)", "Hierarchical", "Model-based (Gaussian mixture)"],
                help="K-means is fastest and needs least data. Model-based needs most data."
            )

            validation = st.checkbox(
                "Want to validate clusters?",
                value=True,
                help="Recommended: Split sample to test cluster stability"
            )

        with col2:
            # Rule of thumb: 2^k minimum (exponential with number of clusters)
            base_min = 2 ** n_clusters * 5

            # Add for number of variables (each cluster needs enough to estimate in variable space)
            var_requirement = n_clusters * n_variables * 10

            if method == "K-means (most common)":
                recommended_n = max(base_min, var_requirement, 100)
            elif method == "Hierarchical":
                recommended_n = max(base_min, var_requirement, 100)
            else:  # Model-based
                recommended_n = max(base_min, var_requirement, 200)

            if validation:
                recommended_n = int(recommended_n * 1.5)  # Need extra for validation split

            st.metric("Recommended Sample Size", f"{recommended_n:,}")

            samples_per_cluster = int(recommended_n / n_clusters)
            st.caption(f"~{samples_per_cluster} per cluster")

            if validation:
                st.info(f"""
                **With validation (recommended):**
                • Training sample: {int(recommended_n * 0.6):,} participants
                • Validation sample: {int(recommended_n * 0.4):,} participants
                """)

            st.info("""
            **Rules of thumb:**
            • Minimum: 2^k observations (k = number of clusters)
            • Practical minimum: 100 participants
            • Each cluster should have 30+ members
            • More variables = more participants needed
            • Validation requires 50% more data

            **Stability check:**
            Run clustering multiple times with different starting points.
            If results vary widely, you need more data.
            """)

    elif base_test == "Segment Analysis":
        with col1:
            n_segments = st.number_input(
                "Number of segments",
                min_value=2, value=3, step=1,
                help="Pre-defined groups (e.g., from cluster analysis, LCA, or personas). Tool ensures minimum 30 per segment for reliable inference."
            )
            st.write("**Segment prevalence (must sum to 100%):**")

            # Auto-balance button
            if 'seg_prevalence' not in st.session_state:
                st.session_state.seg_prevalence = None

            if st.button("Auto-balance to 100%", key="seg_autobalance", help="Proportionally adjust to sum to 100%"):
                # Proportionally adjust existing values
                if st.session_state.seg_prevalence:
                    current_values = st.session_state.seg_prevalence
                    total = sum(current_values)
                    if total > 0:
                        st.session_state.seg_prevalence = [round(v * 100 / total) for v in current_values]
                st.rerun()

            prevalence = []
            prevalence_pct = []
            for i in range(n_segments):
                default_value = 100 // n_segments
                # Use session state if available
                if st.session_state.seg_prevalence and i < len(st.session_state.seg_prevalence):
                    default_value = st.session_state.seg_prevalence[i]

                p = st.number_input(
                    f"Segment {i+1} (%)",
                    min_value=1, max_value=100,
                    value=default_value,
                    key=f"prev_{i}",
                    help=f"Percentage of population in segment {i+1}. All segments must sum to 100%."
                )
                prevalence_pct.append(p)
                prevalence.append(p / 100)

            # Store current values
            st.session_state.seg_prevalence = prevalence_pct

            total_prevalence = sum(prevalence)
            prevalence_valid = abs(total_prevalence - 1.0) <= 0.01
            if not prevalence_valid:
                st.error(f"**Problem:** Segment percentages must add up to 100% (currently {total_prevalence*100:.0f}%)")
                st.info(f"**How to fix:** Click 'Auto-balance' above to proportionally adjust your values to 100%, or manually adjust the numbers above.")
            elif abs(total_prevalence - 1.0) < 0.01 and abs(total_prevalence - 1.0) > 0:
                st.success(f"✓ Segments sum to {total_prevalence*100:.0f}% (valid)")

        with col2:
            effect_size = st.slider(
                "Effect Size (0.10=small, 0.25=medium, 0.40=large)",
                0.1, 1.0, 0.25, 0.05,
                help="For ANOVA (Cohen's f). Small=0.10, Medium=0.25, Large=0.40. Measures difference across all segments."
            )
            alpha = st.selectbox(
                "Significance Level (α)",
                [0.01, 0.05, 0.10],
                index=1,
                key="seg_alpha",
                help="Probability of false positive. Standard is 0.05."
            )
            power = st.slider(
                "Statistical Power (% chance of detecting real effect)",
                0.5, 0.99, 0.80, 0.01,
                key="seg_power",
                help="Probability of detecting real differences. Standard is 0.80 (80%)."
            )

        # Disable calculate if prevalence invalid
        if st.button("Calculate", type="primary", disabled=not prevalence_valid):
            if prevalence_valid:
                calc = SegmentPowerCalc(
                    n_segments=n_segments,
                    prevalence=prevalence,
                    test_type='anova'
                )

                result = calc.calculate(
                    effect_size=effect_size,
                    alpha=alpha,
                    power=power,
                    solve_for='n'
                )

                st.success(f"**Total Sample Size Needed:** {result['total_n']:,}")

                st.write("**Sample per segment:**")
                for i, (n, p) in enumerate(zip(result['n_per_segment'], result['prevalence'])):
                    st.write(f"- Segment {i+1} ({p:.0%}): **{n}** participants")

                # Visualization
                fig = create_segment_allocation_plot(result)
                st.plotly_chart(fig, use_container_width=True)

                if result['warnings']:
                    st.warning("**Warnings:**")
                    for warning in result['warnings']:
                        st.write(f"- {warning}")


def show_visualization_interface():
    """Interactive visualizations"""
    st.header("Power Visualizations")

    viz_type = st.selectbox(
        "Visualization type:",
        ["Power Curve", "Sample Size vs Effect Size", "Sensitivity Analysis"]
    )

    calc_type = st.selectbox(
        "Test type:",
        ["Independent t-test (compare 2 groups)", "ANOVA (compare 3+ groups)", "Regression (predict from multiple variables)"]
    )

    # Extract base name
    base_calc = calc_type.split(" (")[0]

    if base_calc == "Independent t-test":
        calc = MeansPowerCalc(test_type='independent')
        extra_params = {}
    elif base_calc == "ANOVA":
        n_groups = st.number_input("Number of groups", min_value=2, value=3, step=1)
        calc = MeansPowerCalc(test_type='anova')
        extra_params = {'n_groups': n_groups}
    else:
        n_predictors = st.number_input("Number of predictors", min_value=1, value=3, step=1)
        calc = RegressionPowerCalc(test_type='multiple')
        extra_params = {'n_predictors': n_predictors}

    if viz_type == "Power Curve":
        st.write("Shows how power increases with sample size for different effect sizes.")

        alpha = st.slider("Significance Level (chance of false positive)", 0.01, 0.10, 0.05, 0.01)

        fig = plot_power_curve(calc, alpha=alpha, **extra_params)
        st.plotly_chart(fig, use_container_width=True)

    elif viz_type == "Sample Size vs Effect Size":
        st.write("Shows required sample size for different effect sizes and power levels.")

        alpha = st.slider("Significance Level (chance of false positive)", 0.01, 0.10, 0.05, 0.01)

        fig = plot_sample_size_curve(calc, alpha=alpha, **extra_params)
        st.plotly_chart(fig, use_container_width=True)

    elif viz_type == "Sensitivity Analysis":
        st.write("Shows what effect sizes you can detect with different sample sizes.")

        alpha = st.slider("Significance Level (chance of false positive)", 0.01, 0.10, 0.05, 0.01)
        power = st.slider("Desired Power (% chance of detecting effect)", 0.5, 0.99, 0.80, 0.01)

        n_min = st.number_input("Minimum sample size", min_value=10, value=50, step=10)
        n_max = st.number_input("Maximum sample size", min_value=n_min+10, value=500, step=10)
        n_values = list(range(n_min, n_max+1, (n_max-n_min)//20))

        fig = plot_sensitivity_analysis(calc, n_values, power=power, alpha=alpha, **extra_params)
        st.plotly_chart(fig, use_container_width=True)




def show_integrated_dashboard():
    """Single unified dashboard - no sidebar navigation"""

    # Header
    st.title("Survey & Statistical Power Planning")

    st.markdown("---")

    # Initialize session state
    if 'integrated_test_type' not in st.session_state:
        st.session_state.integrated_test_type = "Independent t-test"
    if 'integrated_effect_size' not in st.session_state:
        st.session_state.integrated_effect_size = 0.5
    if 'integrated_power' not in st.session_state:
        st.session_state.integrated_power = 0.80
    if 'integrated_alpha' not in st.session_state:
        st.session_state.integrated_alpha = 0.05
    if 'integrated_ctr' not in st.session_state:
        st.session_state.integrated_ctr = 5.0
    if 'integrated_dropoff' not in st.session_state:
        st.session_state.integrated_dropoff = 30

    # Three-column layout: Survey Sample → Statistical Power → Final Estimate
    col1, col2, col3 = st.columns(3)

    # COLUMN 1: Survey Sample
    with col1:
        st.markdown("### Survey Sample")

        use_survey = st.checkbox("Include survey funnel", value=True, help="Calculate invitations needed based on CTR and drop-off")

        if use_survey:
            st.markdown("")
            ctr = st.slider(
                "CTR (%)",
                0.5, 100.0, 5.0, 0.5,
                help="Click-Through Rate: % who click invitation link",
                key="ctr_slider"
            ) / 100

            # CTR presets
            col_ctr1, col_ctr2, col_ctr3 = st.columns(3)
            with col_ctr1:
                if st.button("Low (2%)", key="ctr_low"):
                    st.session_state.ctr_slider = 2.0
                    st.rerun()
            with col_ctr2:
                if st.button("Med (5%)", key="ctr_med"):
                    st.session_state.ctr_slider = 5.0
                    st.rerun()
            with col_ctr3:
                if st.button("High (10%)", key="ctr_high"):
                    st.session_state.ctr_slider = 10.0
                    st.rerun()

            dropoff = st.slider(
                "Drop-off (%)",
                0, 60, 30, 1,
                help="% who start but don't finish survey",
                key="dropoff_slider"
            ) / 100

            # Drop-off presets
            col_d1, col_d2, col_d3 = st.columns(3)
            with col_d1:
                if st.button("Low (15%)", key="drop_low"):
                    st.session_state.dropoff_slider = 15
                    st.rerun()
            with col_d2:
                if st.button("Med (25%)", key="drop_med"):
                    st.session_state.dropoff_slider = 25
                    st.rerun()
            with col_d3:
                if st.button("High (40%)", key="drop_high"):
                    st.session_state.dropoff_slider = 40
                    st.rerun()

            completion_rate = 1 - dropoff
            st.markdown("")
            st.metric("Completion", f"{completion_rate:.0%}", help="Percentage who finish survey")
        else:
            ctr = 1.0
            dropoff = 0.0
            completion_rate = 1.0

    # COLUMN 2: Statistical Power
    with col2:
        st.markdown("### Statistical Power")

        use_stats = st.checkbox("Include statistical power", value=True, help="Calculate required sample size for test")

        if use_stats:
            st.markdown("")
            test_type = st.selectbox(
                "Test",
                [
                    "Independent t-test",
                    "Paired t-test",
                    "ANOVA",
                    "Multiple Regression",
                    "Correlation",
                    "Chi-Square",
                    "Proportions",
                    "Segment Analysis"
                ],
                help="Which statistical test?",
                key="test_select"
            )

            # Effect size based on test
            if "t-test" in test_type:
                effect_label = "Effect (d)"
                effect_options = {"Small (0.2)": 0.2, "Medium (0.5)": 0.5, "Large (0.8)": 0.8}
            elif test_type == "ANOVA" or test_type == "Segment Analysis":
                effect_label = "Effect (f)"
                effect_options = {"Small (0.1)": 0.1, "Medium (0.25)": 0.25, "Large (0.4)": 0.4}
            elif "Regression" in test_type or test_type == "Correlation":
                effect_label = "Effect (f²)"
                effect_options = {"Small (0.02)": 0.02, "Medium (0.15)": 0.15, "Large (0.35)": 0.35}
            else:  # Chi-Square, Proportions
                effect_label = "Effect (w)"
                effect_options = {"Small (0.1)": 0.1, "Medium (0.3)": 0.3, "Large (0.5)": 0.5}

            # Effect size buttons
            col_e1, col_e2, col_e3 = st.columns(3)
            effect_keys = list(effect_options.keys())
            with col_e1:
                if st.button("Small", key="effect_small"):
                    st.session_state.effect_select = 0
                    st.rerun()
            with col_e2:
                if st.button("Medium", key="effect_med"):
                    st.session_state.effect_select = 1
                    st.rerun()
            with col_e3:
                if st.button("Large", key="effect_large"):
                    st.session_state.effect_select = 2
                    st.rerun()

            effect_idx = st.session_state.get('effect_select', 1)
            effect_size_option = st.selectbox(effect_label, effect_keys, index=effect_idx, key="effect_size_select")
            effect_size = effect_options[effect_size_option]

            power = st.slider("Power", 0.70, 0.95, 0.80, 0.05, help="80% standard", key="power_slider")

            # Additional parameters
            n_groups = 2
            n_predictors = 3
            segment_prevalence = None

            if test_type == "ANOVA" or test_type == "Segment Analysis":
                n_groups = st.number_input("Groups", min_value=3, value=3, step=1, key="groups_input")
                if test_type == "Segment Analysis":
                    st.caption("Enter prevalence (must sum to 100%)")
                    prevalence_inputs = []
                    for i in range(n_groups):
                        prev = st.number_input(f"Segment {i+1} %", min_value=1, max_value=100, value=int(100/n_groups), key=f"prev_{i}")
                        prevalence_inputs.append(prev/100)
                    segment_prevalence = prevalence_inputs
            elif test_type == "Multiple Regression":
                n_predictors = st.number_input("Predictors", min_value=1, value=3, step=1, key="pred_input")
        else:
            test_type = None
            required_sample = 100  # Default if no stats

    # COLUMN 3: Final Estimate (calculated after we have all inputs)
    # Placeholder - will fill after calculations

    # Calculate required sample (needed for column 3)
    alpha = 0.05  # Fixed alpha for simplicity
    overall_conversion = ctr * completion_rate

    try:
        if use_stats:
            if test_type == "Independent t-test":
                calc = MeansPowerCalc(test_type='independent')
                result = calc.calculate(effect_size=effect_size, alpha=alpha, power=power, solve_for='n')
                required_sample = result['total_n']
                per_group = result['n_per_group']
                detail = f"{per_group:,} per group"
            elif test_type == "Paired t-test":
                calc = MeansPowerCalc(test_type='paired')
                result = calc.calculate(effect_size=effect_size, alpha=alpha, power=power, solve_for='n')
                required_sample = result['n']
                detail = "paired observations"
            elif test_type == "ANOVA":
                calc = MeansPowerCalc(test_type='anova')
                result = calc.calculate(effect_size=effect_size, alpha=alpha, power=power, solve_for='n', n_groups=n_groups)
                required_sample = result['total_n']
                per_group = result['n_per_group']
                detail = f"{per_group:,} per group"
            elif test_type == "Multiple Regression":
                calc = RegressionPowerCalc(test_type='multiple')
                result = calc.calculate(effect_size=effect_size, alpha=alpha, power=power, solve_for='n', n_predictors=n_predictors)
                required_sample = result['n']
                detail = f"{n_predictors} predictors"
            elif test_type == "Correlation":
                calc = RegressionPowerCalc(test_type='correlation')
                result = calc.calculate(effect_size=effect_size, alpha=alpha, power=power, solve_for='n')
                required_sample = result['n']
                detail = "correlation"
            elif test_type == "Chi-Square":
                calc = ProportionsPowerCalc(test_type='chisquare')
                result = calc.calculate(effect_size=effect_size, alpha=alpha, power=power, solve_for='n', df=4)
                required_sample = result['n']
                detail = "2×3 table"
            elif test_type == "Proportions":
                calc = ProportionsPowerCalc(test_type='two_proportions')
                result = calc.calculate(effect_size=effect_size, alpha=alpha, power=power, solve_for='n')
                required_sample = result['total_n']
                detail = "2 groups"
            elif test_type == "Segment Analysis":
                calc = SegmentPowerCalc(n_segments=n_groups, prevalence=segment_prevalence)
                result = calc.calculate(
                    effect_size=effect_size,
                    alpha=alpha,
                    power=power,
                    solve_for='n'
                )
                required_sample = result['total_n']
                detail = f"{n_groups} segments"
        else:
            required_sample = 100  # Default
            detail = "no test specified"

        # Calculate invitations needed
        invitations_needed = int(required_sample / overall_conversion)
        clicks_expected = int(invitations_needed * ctr)
        starts_expected = clicks_expected

        # COLUMN 3: Final Estimate
        with col3:
            st.markdown("### Final Estimate")
            st.markdown("")
            st.markdown("")

            st.metric(
                "Invitations",
                f"{invitations_needed:,}",
                help="Total invitations to send"
            )

            st.metric(
                "Expected Sample",
                f"{required_sample:,}",
                help="Participants who complete"
            )

            st.metric(
                "Conversion",
                f"{overall_conversion:.1%}",
                help="Invitations → Sample"
            )

            st.markdown("")
            st.caption(f"→ Need: {required_sample:,} sample")

        st.markdown("---")

        # MATHEMATICAL EXPLANATION
        st.subheader("How We Calculate Your Final Estimate")

        # Create three-step explanation
        col_step1, col_step2, col_step3 = st.columns(3)

        with col_step1:
            st.markdown("#### Step 1: Survey Sample")
            st.markdown("**Determines conversion rate**")
            st.markdown("")
            st.markdown(f"CTR: **{ctr:.1%}** → Gets people to start")
            st.markdown(f"× Completion: **{completion_rate:.0%}** → Gets starters to finish")
            st.markdown(f"= Overall Conversion: **{overall_conversion:.1%}**")
            st.markdown("")

            # Example with 100 invitations
            example_starts = 100 * ctr
            example_completes = example_starts * completion_rate
            st.markdown("**Example with 100 invitations:**")
            st.markdown(f"- 100 sent")
            st.markdown(f"- × {ctr:.1%} CTR = **{example_starts:.1f} start**")
            st.markdown(f"- × {completion_rate:.0%} complete = **{example_completes:.1f} finish**")
            st.markdown("")

            st.info(f"For every 100 invitations: **{overall_conversion*100:.1f}** complete")
            st.markdown("")
            st.markdown(f"To get **N** sample:")
            st.markdown(f"Need **N ÷ {overall_conversion:.3f}** invitations")

        with col_step2:
            st.markdown("#### Step 2: Statistical Power")
            st.markdown("**Determines required N**")
            st.markdown("")
            if use_stats:
                st.markdown(f"Test: **{test_type}**")
                st.markdown(f"Effect: **{effect_size_option}**")
                st.markdown(f"Power: **{power:.0%}**")
                st.markdown("")
                st.success(f"**N = {required_sample:,}** sample needed")
                st.markdown("")
                st.caption(detail)
            else:
                st.markdown("No statistical test specified")
                st.markdown("")
                st.info(f"**N = {required_sample:,}** (default)")

        with col_step3:
            st.markdown("#### Step 3: Work Backwards")
            st.markdown("**Get N completions → Send ? invitations**")
            st.markdown("")
            st.markdown(f"**Goal:** {required_sample:,} completed surveys")
            st.markdown(f"*(from Step 2)*")
            st.markdown("")
            st.markdown(f"**Conversion:** {overall_conversion:.1%}")
            st.markdown(f"*(from Step 1)*")
            st.markdown("")
            st.markdown("**Logic:**")
            st.markdown(f"- If {overall_conversion:.1%} of invitations complete,")
            st.markdown(f"- To GET {required_sample:,} completions,")
            st.markdown(f"- SEND: {required_sample:,} ÷ {overall_conversion:.3f}")
            st.markdown("")
            multiplier = 1 / overall_conversion if overall_conversion > 0 else 0
            st.success(f"**= {invitations_needed:,} invitations**")
            st.markdown("")
            st.caption(f"Survey inefficiency (×{multiplier:.1f}) amplifies statistical requirement")

        st.markdown("---")

        # Visual representation
        st.subheader("Visual Breakdown")

        # Create a visual flow diagram
        col_viz1, col_viz2 = st.columns([2, 1])

        with col_viz1:
            # Calculate multipliers
            ctr_multiplier = 1 / ctr if ctr > 0 else 1
            dropoff_multiplier = 1 / completion_rate if completion_rate > 0 else 1

            # Visual Equation
            col_eq1, col_eq2, col_eq3, col_eq4, col_eq5, col_eq6, col_eq7 = st.columns([2, 1, 2, 1, 2, 1, 2])

            with col_eq1:
                st.markdown("### CTR")
                st.markdown(f"# ×{ctr_multiplier:.1f}")
                st.caption(f"{ctr:.1%} efficiency")

            with col_eq2:
                st.markdown("")
                st.markdown("")
                st.markdown("## ×")

            with col_eq3:
                st.markdown("### Drop-off")
                st.markdown(f"# ×{dropoff_multiplier:.2f}")
                st.caption(f"{completion_rate:.0%} complete")

            with col_eq4:
                st.markdown("")
                st.markdown("")
                st.markdown("## ×")

            with col_eq5:
                st.markdown("### Statistical")
                st.markdown(f"# {required_sample:,}")
                st.caption(f"{test_type if use_stats else 'Base'}")

            with col_eq6:
                st.markdown("")
                st.markdown("")
                st.markdown("## =")

            with col_eq7:
                st.markdown("### Total")
                st.markdown(f"# {invitations_needed:,}")
                st.caption("Invitations")

        with col_viz2:
            st.markdown("**Key Numbers**")
            st.markdown("")
            st.metric("Statistical Need", f"{required_sample:,}", help="From power analysis")
            st.metric("Amplification", f"×{multiplier:.1f}", help="Due to survey conversion")
            st.metric("Total Invitations", f"{invitations_needed:,}", help="Final estimate")
            st.markdown("")
            st.caption(f"Survey conversion of {overall_conversion:.1%} means you need {multiplier:.1f}× more invitations than sample")


    except Exception as e:
        st.error(f"Calculation error: {str(e)}")


def show_forward_calculator():
    """Test requirements → Invitations"""
    st.subheader("Calculate Invitations to Send")

    # Visual workflow reminder
    if 'last_calculation' not in st.session_state:
        st.info("""
        **First time?** Go to **Statistical Power** tab first to calculate how many sample you need, then come back here.
        """)

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Power Requirements")

        # Smart default from last calculation
        default_sample = 200
        if 'last_calculation' in st.session_state:
            calc = st.session_state['last_calculation']
            if calc['solve_for'] == 'n':
                if 'total_n' in calc['result']:
                    default_sample = calc['result']['total_n']
                elif 'n' in calc['result']:
                    default_sample = calc['result']['n']
                st.info(f"Auto-populated from your last calculation: **{default_sample:,} sample** from {calc['test']}")

        required_sample = st.number_input(
            "Required sample size (from power analysis)",
            min_value=50, value=default_sample, step=10,
            help="Number of completed surveys needed for your statistical test. This is auto-populated from your last Statistical Power calculation if available."
        )

    with col2:
        st.subheader("Survey Funnel Rates")

        with st.expander("View View CTR Guidelines"):
            st.markdown("""
**Email surveys (typical ranges):**
• No incentive: ~1% or below
• Standard email: 2-5%
• With prize draw/incentive: 5-10%
• Best case (prize draw): ~10%

**Intercept surveys** (in-app pop-ups, embedded): Speak to ResearchOps for guidance.

**Unsure about your CTR?** Ask ResearchOps or check past campaign analytics.

**Note**: CTR is often the BIGGEST factor in invitation requirements. Improving CTR from 2% → 8% can reduce invitations needed by 75%.
            """)

        ctr = st.slider(
            "Click-Through Rate (CTR) %",
            0.5, 100.0, 5.0, 0.5,
            help="% of people who click your survey invitation link. Click 'View CTR Guidelines' above for typical ranges."
        ) / 100

        # Warning for unrealistic CTR
        if ctr > 0.15 and ctr < 1.0:
            st.warning(f"""
            **Problem:** CTR of {ctr:.0%} is very high for email surveys.

            **Why this matters:** If your actual CTR is lower (typical: 2-10%), you'll send too few invitations and won't reach your target sample.

            **How to fix:**
            - Email surveys with incentive: Use 5-10% CTR
            - Email without incentive: Use 1-3% CTR
            - Intercept survey (in-app pop-up): Use 100% CTR

            Best case for email is ~10%. Are you sure this is email and not an intercept survey?
            """)
        elif ctr == 1.0:
            st.info("100% CTR = Intercept survey (in-app pop-up, no email link). This is correct for embedded surveys.")
        elif ctr < 0.01:
            st.warning(f"Warning: CTR of {ctr:.1%} is very low. Consider adding incentives or improving email targeting.")

        dropoff_rate = st.slider(
            "Drop-off Rate (%)",
            0, 60, 30, 1,
            help="""**Drop-off Rate**: % of people who START your survey but DON'T finish it.

**Typical ranges:**
• Simple survey (<10 min, single-choice): 5-15%
• Standard survey (10-15 min, mixed questions): 15-25%
• Complex survey (loops, grids, 15-20 min): 25-40%
• Very complex (multiple loops, >20 min): 40-60%

**Completion Rate** = 100% - Drop-off Rate
Example: 30% drop-off = 70% completion"""
        ) / 100

        # Warning for high drop-off
        if dropoff_rate > 0.40:
            st.error(f"""
            **Problem:** Drop-off rate of {dropoff_rate:.0%} is very high!

            **Why this matters:** You'll need {int(required_sample / (1 - dropoff_rate)):,} invitations. With lower drop-off (25%), you'd only need {int(required_sample / 0.75):,} invitations.

            **How to fix:**
            1. Remove loops or reduce iterations (biggest impact)
            2. Simplify grid questions (<5 rows each)
            3. Add skip logic to reduce effective length
            4. See "Optimization Opportunities" below for specific actions
            """)
        elif dropoff_rate > 0.30:
            st.warning(f"""
            **Problem:** Drop-off rate of {dropoff_rate:.0%} is high.

            **How to improve:**
            - Remove unnecessary questions
            - Reduce loop iterations
            - Add progress bar
            - See "Optimization Opportunities" below for details
            """)

    st.write("---")

    # Calculate invitations with full funnel
    invitations_result = calculate_invitations(
        required_sample,
        dropoff_rate=dropoff_rate,
        ctr=ctr,
        response_rate=1.0
    )

    # Show funnel
    st.subheader("Survey Funnel")

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric(
            "Invitations",
            invitations_result['invitations_needed'],
            help="Total number of survey invitations you need to send (emails, messages, etc.)"
        )
    with col2:
        st.metric(
            "Expected Clicks",
            invitations_result['expected_clicks'],
            delta=f"{ctr:.0%} CTR",
            help="How many people will click your survey link (based on CTR)"
        )
    with col3:
        st.metric(
            "Expected Starts",
            invitations_result['expected_starts'],
            help="How many people will begin taking your survey"
        )
    with col4:
        st.metric(
            "Expected Sample",
            invitations_result['expected_sample'],
            delta=f"{invitations_result['completion_rate']:.0%} complete",
            help="How many people will finish your survey (based on drop-off rate)"
        )

    # Overall conversion
    st.info(f"""**Overall Conversion:** {invitations_result['effective_rate']:.1%} (invitation → complete)

This is your end-to-end conversion rate: for every 100 invitations sent, {invitations_result['effective_rate']*100:.1f} people will complete the survey.""")

    # Export results
    col_copy, col_md = st.columns(2)

    with col_copy:
        funnel_text = f"""Survey Sample Size Results
Required Sample Size: {required_sample}
CTR (Click-Through Rate): {ctr:.1%}
Drop-off Rate: {dropoff_rate:.0%}
Completion Rate: {invitations_result['completion_rate']:.0%}

Survey Funnel:
→ Invitations to Send: {invitations_result['invitations_needed']:,}
→ Expected Clicks: {invitations_result['expected_clicks']:,}
→ Expected Starts: {invitations_result['expected_starts']:,}
→ Expected Sample: {invitations_result['expected_sample']:,}

Overall Conversion: {invitations_result['effective_rate']:.1%}
"""
        if st.button("View Copy Results", key="copy_funnel"):
            st.code(funnel_text, language=None)
            st.caption("Copy with Ctrl+C / Cmd+C")

    with col_md:
        # Generate Markdown
        markdown_funnel = f"""# Survey Sample Size Results

**Date:** {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M')}

## Summary

**📧 Invitations to Send:** {invitations_result['invitations_needed']:,}

## Survey Funnel

| Stage | Count | Rate |
|-------|-------|------|
| 1. Invitations Sent | {invitations_result['invitations_needed']:,} | 100% |
| 2. Expected Clicks | {invitations_result['expected_clicks']:,} | {ctr:.1%} CTR |
| 3. Expected Starts | {invitations_result['expected_starts']:,} | ~100% |
| 4. Expected Sample | {invitations_result['expected_sample']:,} | {invitations_result['completion_rate']:.0%} complete |

**Overall Conversion:** {invitations_result['effective_rate']:.1%} (invitation → complete)

## Parameters

| Parameter | Value |
|-----------|-------|
| Required Sample Size | {required_sample:,} |
| Click-Through Rate (CTR) | {ctr:.1%} |
| Drop-off Rate | {dropoff_rate:.0%} |
| Completion Rate | {invitations_result['completion_rate']:.0%} |

## Interpretation

For every 100 invitations sent, **{invitations_result['effective_rate']*100:.1f} people** will complete the survey.

---
*Generated by Power Analysis Tool*
"""
        st.download_button(
            label="📥 Markdown",
            data=markdown_funnel,
            file_name=f"sample_size_estimation_{pd.Timestamp.now().strftime('%Y%m%d_%H%M')}.md",
            mime="text/markdown",
            help="Download for Confluence/Notion",
            key="md_funnel"
        )

    st.write("---")

    # Optimization scenarios
    if dropoff_rate > 0.15:
        st.subheader("Optimization Opportunities")

        st.info("""
        **Reduce drop-off to lower invitation requirements:**

        - **Simple improvements** (5-10% reduction):
          - Remove unnecessary loops
          - Simplify grid questions
          - Add progress indicators

        - **Medium improvements** (10-15% reduction):
          - Redesign complex sections
          - Add skip logic
          - Reduce survey length

        - **Major improvements** (15-25% reduction):
          - Complete survey overhaul
          - Split into multiple short surveys
          - Implement adaptive design
        """)

        # Show scenarios
        target_dropoffs = [
            ("Reduce to 25%", 0.25),
            ("Reduce to 20%", 0.20),
            ("Reduce to 15%", 0.15)
        ]

        for name, target_dropoff in target_dropoffs:
            if target_dropoff < dropoff_rate:
                new_invitations = int(np.ceil(required_sample / (1 - target_dropoff)))
                saved = invitations_result['invitations_needed'] - new_invitations
                reduction = (dropoff_rate - target_dropoff) / dropoff_rate

                with st.expander(f"{name} - Save {saved} invitations ({reduction:.0%} reduction)"):
                    st.write(f"**New drop-off:** {target_dropoff:.1%}")
                    st.write(f"**New invitations:** {new_invitations}")
                    st.write(f"**Invitations saved:** {saved}")
    else:
        st.success("Success: Low drop-off rate! Your survey design is well-optimized.")


def show_reverse_calculator():
    """Survey details → Test feasibility"""
    st.subheader("Check What Tests Are Feasible")

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Survey Constraints")

        invitations_available = st.number_input(
            "Invitations available",
            min_value=100, value=5000, step=100,
            help="Total number of survey invitations you can send (email list size, participant pool, etc.)"
        )

        ctr = st.slider(
            "Click-Through Rate (CTR) %",
            0.5, 100.0, 5.0, 0.5,
            help="% of people who click your survey invitation link. Click 'View CTR Guidelines' below for typical ranges."
        ) / 100

        with st.expander("View CTR Guidelines"):
            st.markdown("""
**Email surveys (typical ranges):**
• No incentive: ~1% or below
• Standard email: 2-5%
• With prize draw/incentive: 5-10%
• Best case (prize draw): ~10%

**Intercept surveys** (in-app pop-ups, embedded): 100%

**Unsure about your CTR?** Ask ResearchOps or check past campaign analytics.
            """)

        # Warning for unrealistic CTR
        if ctr > 0.15 and ctr < 1.0:
            st.warning(f"""
            **Problem:** CTR of {ctr:.0%} is very high for email surveys.

            **Why this matters:** If your actual CTR is lower (typical: 2-10%), you'll get fewer sample than expected.

            **Typical ranges:** Email with incentive: 5-10% | Email without: 1-3% | Intercept: 100%
            """)
        elif ctr == 1.0:
            st.info("100% CTR = Intercept survey (in-app pop-up, no email link). This is correct for embedded surveys.")

    with col2:
        st.subheader("Survey Design")

        dropoff_rate = st.slider(
            "Drop-off Rate (%)",
            0, 60, 30, 1,
            help="% of people who START your survey but DON'T finish it. Typical: 15-40%"
        ) / 100

        # Warning for high drop-off
        if dropoff_rate > 0.40:
            st.error(f"""
            **Problem:** Drop-off rate of {dropoff_rate:.0%} is very high!

            **Actions:** Remove loops, simplify grids, add skip logic, show progress bar
            """)
        elif dropoff_rate > 0.30:
            st.warning(f"Drop-off rate of {dropoff_rate:.0%} is high. Consider simplifying survey design.")

    st.markdown("---")

    # Calculate sample (sample)
    clicks = int(invitations_available * ctr)
    starts = clicks  # Assume ~100% of clickers start
    sample = int(starts * (1 - dropoff_rate))

    st.subheader("Results: What You'll Get")

    col_inv, col_clicks, col_starts, col_comp = st.columns(4)
    with col_inv:
        st.metric("Invitations", f"{invitations_available:,}")
    with col_clicks:
        st.metric("Expected Clicks", f"{clicks:,}", delta=f"{ctr:.1%} CTR")
    with col_starts:
        st.metric("Expected Starts", f"{starts:,}")
    with col_comp:
        st.metric("Expected Sample", f"{sample:,}", delta=f"{(1-dropoff_rate):.0%} complete")

    overall_conversion = sample / invitations_available
    st.info(f"""**Overall Conversion:** {overall_conversion:.1%} (invitation → complete)

For every 100 invitations sent, **{overall_conversion*100:.1f} people** will complete the survey.""")

    st.markdown("---")

    # Test feasibility check
    st.subheader("Test Feasibility Check")

    st.markdown(f"""
    **You'll get {sample:,} participants.** What can you test with this sample size?

    Select tests below to check power:
    """)

    # Quick feasibility for common tests
    col_t, col_anova, col_reg = st.columns(3)

    with col_t:
        st.markdown("**Independent t-test**")
        st.caption("Compare 2 groups")

        effect_t = st.selectbox("Effect size", ["Small (0.2)", "Medium (0.5)", "Large (0.8)"], index=1, key="t_effect")
        d = 0.2 if "Small" in effect_t else (0.5 if "Medium" in effect_t else 0.8)

        calc_t = MeansPowerCalc(test_type='independent')
        result_t = calc_t.calculate(effect_size=d, alpha=0.05, n=sample//2, solve_for='power')

        if result_t['power'] >= 0.80:
            st.success(f"Success: **{result_t['power']:.0%} power** - Adequate!")
        elif result_t['power'] >= 0.70:
            st.warning(f"**{result_t['power']:.0%} power** - Moderate")
        else:
            st.error(f"**{result_t['power']:.0%} power** - Underpowered")

            # Calculate needed
            result_needed = calc_t.calculate(effect_size=d, alpha=0.05, power=0.80, solve_for='n')
            st.caption(f"Need {result_needed['total_n']:,} sample for 80% power")

    with col_anova:
        st.markdown("**One-Way ANOVA**")
        st.caption("Compare 3+ groups")

        n_groups_anova = st.number_input("Number of groups", min_value=3, value=3, step=1, key="anova_groups")
        effect_anova = st.selectbox("Effect size", ["Small (0.1)", "Medium (0.25)", "Large (0.4)"], index=1, key="anova_effect")
        f = 0.1 if "Small" in effect_anova else (0.25 if "Medium" in effect_anova else 0.4)

        calc_anova = MeansPowerCalc(test_type='anova')
        result_anova = calc_anova.calculate(effect_size=f, alpha=0.05, n=sample//n_groups_anova, solve_for='power', n_groups=n_groups_anova)

        if result_anova['power'] >= 0.80:
            st.success(f"Success: **{result_anova['power']:.0%} power** - Adequate!")
        elif result_anova['power'] >= 0.70:
            st.warning(f"**{result_anova['power']:.0%} power** - Moderate")
        else:
            st.error(f"**{result_anova['power']:.0%} power** - Underpowered")

            # Calculate needed
            result_needed = calc_anova.calculate(effect_size=f, alpha=0.05, power=0.80, solve_for='n', n_groups=n_groups_anova)
            st.caption(f"Need {result_needed['total_n']:,} sample for 80% power")

    with col_reg:
        st.markdown("**Multiple Regression**")
        st.caption("Predict from multiple variables")

        n_predictors = st.number_input("Number of predictors", min_value=1, value=3, step=1, key="reg_predictors")
        effect_reg = st.selectbox("Effect size", ["Small (0.02)", "Medium (0.15)", "Large (0.35)"], index=1, key="reg_effect")
        f2 = 0.02 if "Small" in effect_reg else (0.15 if "Medium" in effect_reg else 0.35)

        calc_reg = RegressionPowerCalc(test_type='multiple')
        result_reg = calc_reg.calculate(effect_size=f2, alpha=0.05, n=sample, solve_for='power', n_predictors=n_predictors)

        if result_reg['power'] >= 0.80:
            st.success(f"Success: **{result_reg['power']:.0%} power** - Adequate!")
        elif result_reg['power'] >= 0.70:
            st.warning(f"**{result_reg['power']:.0%} power** - Moderate")
        else:
            st.error(f"**{result_reg['power']:.0%} power** - Underpowered")

            # Calculate needed
            result_needed = calc_reg.calculate(effect_size=f2, alpha=0.05, power=0.80, solve_for='n', n_predictors=n_predictors)
            st.caption(f"Need {result_needed['n']:,} sample for 80% power")

    st.markdown("---")

    # Optimization suggestions
    st.subheader("Optimization Options")

    if overall_conversion < 0.05:  # Less than 5% conversion
        st.warning(f"""
        **Low overall conversion ({overall_conversion:.1%})**

        **Options to improve:**
        1. **Increase CTR** (biggest impact):
           - Add incentive (prize draw)
           - Improve subject line
           - Better targeting
           - Target: 5-10% CTR

        2. **Reduce drop-off**:
           - Simplify survey design
           - Remove loops
           - Add skip logic
           - Target: 20-25% drop-off

        3. **Increase invitations** (if possible):
           - Expand email list
           - Use multiple channels
        """)

    # Show scenario comparisons
    with st.expander("Compare Improvement Scenarios"):
        st.markdown("**If you made these improvements:**")

        scenarios = [
            ("Improve CTR to 8%", invitations_available, 0.08, dropoff_rate),
            ("Reduce drop-off to 20%", invitations_available, ctr, 0.20),
            ("Both improvements", invitations_available, 0.08, 0.20),
        ]

        comparison_data = []
        for name, inv, ctr_new, drop_new in scenarios:
            clicks_new = int(inv * ctr_new)
            sample_new = int(clicks_new * (1 - drop_new))
            improvement = sample_new - sample

            comparison_data.append({
                "Scenario": name,
                "Completes": f"{sample_new:,}",
                "Improvement": f"+{improvement:,} ({improvement/sample:.0%})"
            })

        df = pd.DataFrame(comparison_data)
        st.table(df)


def show_glossary_page():
    """Display full glossary"""
    st.header("Glossary")

    # Search box
    search_term = st.text_input("Search glossary", placeholder="Type a term (e.g., power, CTR, effect size)")

    # FAQ section
    with st.expander("FAQ: Frequently Asked Questions"):
        st.markdown("""
        **Q: What's the difference between power and sample size?**
        A: Power is the probability of detecting an effect (typically 80%). Sample size is HOW MANY participants you need to achieve that power.

        **Q: What's the difference between sample and invitations?**
        A: Completes = finished surveys (usable data). Invitations = total sent. You need MORE invitations because of CTR and drop-off.

        **Q: How do I know which effect size to use?**
        A: If unsure, use Medium (d=0.5 for t-tests, f=0.25 for ANOVA, f²=0.15 for regression). Small effects need huge samples; large effects are rare.

        **Q: What's a good CTR for email surveys?**
        A: 2-5% standard, 5-10% with incentive, ~10% best case. Above 10% is unrealistic for email (may be intercept survey).

        **Q: What's a typical drop-off rate?**
        A: 15-25% for standard surveys, 25-40% for complex surveys. Above 40% indicates serious design problems.

        **Q: When should I use Statistical Power vs Survey Sample Size?**
        A: Always do both in order: (1) Statistical Power calculates sample size needed, (2) Survey Sample Size calculates invitations to send.

        **Q: What does "underpowered" mean?**
        A: Your sample is too small to reliably detect the effect. You'll likely miss real effects (false negatives). Solution: Increase sample size.

        **Q: Can I use this for qualitative research?**
        A: No, this tool is for quantitative hypothesis testing. Qualitative research uses different sampling approaches (saturation, purposive sampling).

        **Q: What if I can't get the recommended sample size?**
        A: Options: (1) Accept lower power (higher risk of missing effects), (2) Focus on larger effect sizes only, (3) Use existing data/literature, (4) Reconsider research question.

        **Q: Do I always need 80% power?**
        A: 80% is standard but not mandatory. Exploratory research might use 70%. Critical decisions might require 90%. More power = more participants needed.
        """)

    # Read glossary markdown file
    try:
        with open('docs/GLOSSARY.md', 'r') as f:
            glossary_content = f.read()

        # Filter based on search
        if search_term:
            lines = glossary_content.split('\n')
            filtered_lines = []
            include_section = False
            for line in lines:
                if line.startswith('###') and search_term.lower() in line.lower():
                    include_section = True
                    filtered_lines.append(line)
                elif line.startswith('###'):
                    include_section = False
                elif include_section or search_term.lower() in line.lower():
                    filtered_lines.append(line)

            if filtered_lines:
                st.markdown('\n'.join(filtered_lines))
            else:
                st.warning(f"No results found for '{search_term}'. Try a different term or clear the search box.")
        else:
            st.markdown(glossary_content)

    except FileNotFoundError:
        st.error("**Problem:** Glossary file not found at docs/GLOSSARY.md")
        st.info("""
        **How to fix:**
        1. Check that the `docs/GLOSSARY.md` file exists in your project directory
        2. If missing, download from the [project repository](https://github.com/your-repo)
        3. Or view the glossary in the sidebar under "Need Help?" → "Quick Definitions"

        **In the meantime:** Key terms are available in the sidebar help section.
        """)


if __name__ == "__main__":
    main()
