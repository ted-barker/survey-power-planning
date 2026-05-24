"""
Power curve visualizations

Shows relationship between sample size, power, and effect size
"""

from typing import Dict, List, Optional, Union
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots


def plot_power_curve(
    calculator,
    effect_sizes: Optional[List[float]] = None,
    alpha: float = 0.05,
    n_range: Optional[tuple] = None,
    title: Optional[str] = None,
    **calc_kwargs
) -> go.Figure:
    """
    Create interactive power curve showing power vs. sample size.

    Args:
        calculator: Initialized power calculator instance
        effect_sizes: List of effect sizes to plot (default: small, medium, large)
        alpha: Significance level
        n_range: Tuple of (min_n, max_n) for x-axis
        title: Plot title
        **calc_kwargs: Additional arguments for calculator (e.g., n_predictors, n_groups)

    Returns:
        Plotly figure object
    """
    # Get effect size guidelines if not provided
    if effect_sizes is None:
        guidelines = calculator.get_effect_size_guidelines()
        if isinstance(guidelines, dict):
            # Extract first set of guidelines (e.g., 'cohens_d' or 'small')
            if 'small' in guidelines:
                effect_sizes = [guidelines['small'], guidelines['medium'], guidelines['large']]
                effect_labels = ['Small', 'Medium', 'Large']
            else:
                # Nested structure (e.g., {'f_squared': {...}})
                first_key = list(guidelines.keys())[0]
                effect_sizes = [
                    guidelines[first_key]['small'],
                    guidelines[first_key]['medium'],
                    guidelines[first_key]['large']
                ]
                effect_labels = ['Small', 'Medium', 'Large']
    else:
        effect_labels = [f'ES={es:.2f}' for es in effect_sizes]

    # Determine sample size range
    if n_range is None:
        # Calculate reasonable range based on largest effect size
        calc_result = calculator.calculate(
            effect_size=min(effect_sizes),
            alpha=alpha,
            power=0.80,
            solve_for='n',
            **calc_kwargs
        )
        # Get total n (different keys for different calculators)
        if 'total_n' in calc_result:
            max_n = int(calc_result['total_n'] * 2)
        elif 'n' in calc_result:
            max_n = int(calc_result['n'] * 2)
        elif 'n_per_group' in calc_result:
            max_n = int(calc_result['n_per_group'] * 2)
        else:
            max_n = 200

        n_range = (10, max_n)

    # Generate sample size values
    n_values = np.linspace(n_range[0], n_range[1], 100, dtype=int)

    # Create figure
    fig = go.Figure()

    # Plot power curve for each effect size
    for es, label in zip(effect_sizes, effect_labels):
        power_values = []

        for n in n_values:
            try:
                # Handle different calculator types
                if hasattr(calculator, 'test_type'):
                    if calculator.test_type in ['anova', 'repeated_anova']:
                        result = calculator.calculate(
                            effect_size=es,
                            n=n,
                            alpha=alpha,
                            solve_for='power',
                            **calc_kwargs
                        )
                    elif calculator.test_type in ['independent', 'paired']:
                        result = calculator.calculate(
                            effect_size=es,
                            n=n,
                            alpha=alpha,
                            solve_for='power',
                            **calc_kwargs
                        )
                    elif calculator.test_type in ['simple', 'multiple', 'moderation', 'partial']:
                        result = calculator.calculate(
                            effect_size=es,
                            n=n,
                            alpha=alpha,
                            solve_for='power',
                            **calc_kwargs
                        )
                    elif calculator.test_type in ['two_proportions', 'one_proportion', 'chi_square']:
                        result = calculator.calculate(
                            effect_size=es,
                            n=n,
                            alpha=alpha,
                            solve_for='power',
                            **calc_kwargs
                        )
                    else:
                        # Segment calculator
                        result = calculator.calculate(
                            effect_size=es,
                            total_n=n,
                            alpha=alpha,
                            solve_for='power',
                            **calc_kwargs
                        )
                else:
                    # Default
                    result = calculator.calculate(
                        effect_size=es,
                        n=n,
                        alpha=alpha,
                        solve_for='power',
                        **calc_kwargs
                    )

                power_values.append(result['power'])
            except (ValueError, KeyError):
                power_values.append(np.nan)

        fig.add_trace(go.Scatter(
            x=n_values,
            y=power_values,
            mode='lines',
            name=label,
            line=dict(width=2),
            hovertemplate='<b>%{fullData.name}</b><br>' +
                         'n=%{x}<br>' +
                         'Power=%{y:.1%}<br>' +
                         '<extra></extra>'
        ))

    # Add reference line at 80% power
    fig.add_hline(
        y=0.80,
        line_dash="dash",
        line_color="gray",
        annotation_text="80% Power",
        annotation_position="right"
    )

    # Update layout
    if title is None:
        title = f"Power Analysis (α={alpha})"

    fig.update_layout(
        title=title,
        xaxis_title="Sample Size",
        yaxis_title="Statistical Power",
        hovermode='x unified',
        legend=dict(
            yanchor="bottom",
            y=0.01,
            xanchor="right",
            x=0.99
        ),
        height=500
    )

    fig.update_yaxes(range=[0, 1], tickformat='.0%')
    fig.update_xaxes(range=[n_range[0], n_range[1]])

    return fig


def plot_sample_size_curve(
    calculator,
    power_levels: Optional[List[float]] = None,
    alpha: float = 0.05,
    effect_size_range: Optional[tuple] = None,
    title: Optional[str] = None,
    **calc_kwargs
) -> go.Figure:
    """
    Create interactive curve showing required sample size vs. effect size.

    Args:
        calculator: Initialized power calculator instance
        power_levels: List of power levels to plot (default: [0.70, 0.80, 0.90])
        alpha: Significance level
        effect_size_range: Tuple of (min_es, max_es)
        title: Plot title
        **calc_kwargs: Additional arguments for calculator

    Returns:
        Plotly figure object
    """
    if power_levels is None:
        power_levels = [0.70, 0.80, 0.90]

    # Get effect size range
    if effect_size_range is None:
        guidelines = calculator.get_effect_size_guidelines()
        if isinstance(guidelines, dict):
            if 'small' in guidelines:
                effect_size_range = (guidelines['small'] * 0.5, guidelines['large'] * 1.5)
            else:
                first_key = list(guidelines.keys())[0]
                effect_size_range = (
                    guidelines[first_key]['small'] * 0.5,
                    guidelines[first_key]['large'] * 1.5
                )
        else:
            effect_size_range = (0.1, 1.0)

    # Generate effect size values
    es_values = np.linspace(effect_size_range[0], effect_size_range[1], 100)

    # Create figure
    fig = go.Figure()

    # Plot sample size curve for each power level
    for power in power_levels:
        n_values = []

        for es in es_values:
            try:
                result = calculator.calculate(
                    effect_size=es,
                    alpha=alpha,
                    power=power,
                    solve_for='n',
                    **calc_kwargs
                )

                # Extract n (different keys for different calculators)
                if 'total_n' in result:
                    n_values.append(result['total_n'])
                elif 'n' in result:
                    n_values.append(result['n'])
                elif 'n_per_group' in result:
                    n_values.append(result['n_per_group'])
                else:
                    n_values.append(np.nan)
            except (ValueError, KeyError):
                n_values.append(np.nan)

        fig.add_trace(go.Scatter(
            x=es_values,
            y=n_values,
            mode='lines',
            name=f'Power={power:.0%}',
            line=dict(width=2),
            hovertemplate='<b>%{fullData.name}</b><br>' +
                         'Effect Size=%{x:.2f}<br>' +
                         'Required n=%{y:.0f}<br>' +
                         '<extra></extra>'
        ))

    # Update layout
    if title is None:
        title = f"Required Sample Size by Effect Size (α={alpha})"

    fig.update_layout(
        title=title,
        xaxis_title="Effect Size",
        yaxis_title="Required Sample Size",
        hovermode='x unified',
        legend=dict(
            yanchor="top",
            y=0.99,
            xanchor="right",
            x=0.99
        ),
        height=500
    )

    return fig


def plot_power_comparison(
    results: List[Dict],
    labels: List[str],
    title: str = "Power Analysis Comparison"
) -> go.Figure:
    """
    Compare power across multiple scenarios.

    Args:
        results: List of power calculation results
        labels: Labels for each scenario
        title: Plot title

    Returns:
        Plotly figure object
    """
    fig = go.Figure()

    # Extract power values
    powers = [r.get('power', 0) for r in results]

    # Extract sample sizes
    n_values = []
    for r in results:
        if 'total_n' in r:
            n_values.append(r['total_n'])
        elif 'n' in r:
            n_values.append(r['n'])
        elif 'n_per_group' in r:
            n_values.append(r['n_per_group'])
        else:
            n_values.append(0)

    # Create bar chart
    fig.add_trace(go.Bar(
        x=labels,
        y=powers,
        text=[f"{p:.1%}" for p in powers],
        textposition='auto',
        marker=dict(
            color=powers,
            colorscale='RdYlGn',
            cmin=0,
            cmax=1,
            showscale=True,
            colorbar=dict(title="Power", tickformat='.0%')
        ),
        hovertemplate='<b>%{x}</b><br>' +
                     'Power=%{y:.1%}<br>' +
                     'Sample Size=%{customdata}<br>' +
                     '<extra></extra>',
        customdata=n_values
    ))

    # Add reference line at 80%
    fig.add_hline(
        y=0.80,
        line_dash="dash",
        line_color="red",
        annotation_text="80% Power Threshold"
    )

    fig.update_layout(
        title=title,
        yaxis_title="Statistical Power",
        yaxis=dict(range=[0, 1], tickformat='.0%'),
        height=500
    )

    return fig
