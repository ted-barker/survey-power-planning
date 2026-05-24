"""
Sensitivity analysis visualizations

Shows detectable effect sizes given constraints
"""

from typing import Dict, List, Optional
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots


def plot_sensitivity_analysis(
    calculator,
    n_values: List[int],
    power: float = 0.80,
    alpha: float = 0.05,
    title: Optional[str] = None,
    **calc_kwargs
) -> go.Figure:
    """
    Create sensitivity analysis showing detectable effect sizes.

    Args:
        calculator: Initialized power calculator instance
        n_values: List of sample sizes to test
        power: Desired statistical power
        alpha: Significance level
        title: Plot title
        **calc_kwargs: Additional arguments for calculator

    Returns:
        Plotly figure object
    """
    effect_sizes = []

    for n in n_values:
        try:
            result = calculator.calculate(
                n=n,
                alpha=alpha,
                power=power,
                solve_for='effect_size',
                **calc_kwargs
            )

            # Extract effect size
            if 'effect_size' in result:
                effect_sizes.append(result['effect_size'])
            elif 'effect_size_f2' in result:
                effect_sizes.append(result['effect_size_f2'])
            elif 'effect_size_h' in result:
                effect_sizes.append(result['effect_size_h'])
            elif 'effect_size_w' in result:
                effect_sizes.append(result['effect_size_w'])
            else:
                effect_sizes.append(np.nan)
        except (ValueError, KeyError):
            effect_sizes.append(np.nan)

    # Create figure
    fig = go.Figure()

    fig.add_trace(go.Scatter(
        x=n_values,
        y=effect_sizes,
        mode='lines+markers',
        name='Detectable Effect Size',
        line=dict(width=2, color='steelblue'),
        marker=dict(size=6),
        hovertemplate='<b>Sample Size</b>: %{x}<br>' +
                     '<b>Detectable ES</b>: %{y:.3f}<br>' +
                     '<extra></extra>'
    ))

    # Add effect size guideline bands if available
    guidelines = calculator.get_effect_size_guidelines()
    if isinstance(guidelines, dict):
        if 'small' in guidelines:
            small = guidelines['small']
            medium = guidelines['medium']
            large = guidelines['large']
        else:
            first_key = list(guidelines.keys())[0]
            small = guidelines[first_key]['small']
            medium = guidelines[first_key]['medium']
            large = guidelines[first_key]['large']

        # Add horizontal lines for reference
        fig.add_hline(y=small, line_dash="dot", line_color="gray",
                     annotation_text="Small", annotation_position="right")
        fig.add_hline(y=medium, line_dash="dot", line_color="gray",
                     annotation_text="Medium", annotation_position="right")
        fig.add_hline(y=large, line_dash="dot", line_color="gray",
                     annotation_text="Large", annotation_position="right")

    if title is None:
        title = f"Sensitivity Analysis (Power={power:.0%}, α={alpha})"

    fig.update_layout(
        title=title,
        xaxis_title="Sample Size",
        yaxis_title="Detectable Effect Size",
        hovermode='closest',
        height=500
    )

    return fig


def plot_effect_size_detection(
    calculator,
    n: int,
    alpha: float = 0.05,
    power_range: tuple = (0.5, 0.99),
    title: Optional[str] = None,
    **calc_kwargs
) -> go.Figure:
    """
    Plot detectable effect size vs. power for fixed sample size.

    Args:
        calculator: Initialized power calculator instance
        n: Fixed sample size
        alpha: Significance level
        power_range: Tuple of (min_power, max_power)
        title: Plot title
        **calc_kwargs: Additional arguments for calculator

    Returns:
        Plotly figure object
    """
    power_values = np.linspace(power_range[0], power_range[1], 50)
    effect_sizes = []

    for power in power_values:
        try:
            result = calculator.calculate(
                n=n,
                alpha=alpha,
                power=power,
                solve_for='effect_size',
                **calc_kwargs
            )

            # Extract effect size
            if 'effect_size' in result:
                effect_sizes.append(result['effect_size'])
            elif 'effect_size_f2' in result:
                effect_sizes.append(result['effect_size_f2'])
            elif 'effect_size_h' in result:
                effect_sizes.append(result['effect_size_h'])
            elif 'effect_size_w' in result:
                effect_sizes.append(result['effect_size_w'])
            else:
                effect_sizes.append(np.nan)
        except (ValueError, KeyError):
            effect_sizes.append(np.nan)

    # Create figure
    fig = go.Figure()

    fig.add_trace(go.Scatter(
        x=power_values,
        y=effect_sizes,
        mode='lines+markers',
        name=f'n={n}',
        line=dict(width=2),
        marker=dict(size=4),
        hovertemplate='<b>Power</b>: %{x:.1%}<br>' +
                     '<b>Required ES</b>: %{y:.3f}<br>' +
                     '<extra></extra>'
    ))

    # Add vertical line at 80% power
    fig.add_vline(
        x=0.80,
        line_dash="dash",
        line_color="gray",
        annotation_text="80% Power"
    )

    if title is None:
        title = f"Effect Size Requirements (n={n}, α={alpha})"

    fig.update_layout(
        title=title,
        xaxis_title="Statistical Power",
        yaxis_title="Required Effect Size",
        hovermode='closest',
        height=500
    )

    fig.update_xaxes(tickformat='.0%')

    return fig


def plot_power_matrix(
    calculator,
    n_range: tuple,
    effect_size_range: tuple,
    alpha: float = 0.05,
    n_points: int = 20,
    es_points: int = 20,
    title: Optional[str] = None,
    **calc_kwargs
) -> go.Figure:
    """
    Create heatmap showing power across sample size × effect size grid.

    Args:
        calculator: Initialized power calculator instance
        n_range: Tuple of (min_n, max_n)
        effect_size_range: Tuple of (min_es, max_es)
        alpha: Significance level
        n_points: Number of sample size points
        es_points: Number of effect size points
        title: Plot title
        **calc_kwargs: Additional arguments for calculator

    Returns:
        Plotly figure object
    """
    n_values = np.linspace(n_range[0], n_range[1], n_points, dtype=int)
    es_values = np.linspace(effect_size_range[0], effect_size_range[1], es_points)

    # Create power matrix
    power_matrix = np.zeros((es_points, n_points))

    for i, es in enumerate(es_values):
        for j, n in enumerate(n_values):
            try:
                # Handle different calculator types
                if hasattr(calculator, 'test_type'):
                    if calculator.test_type in ['anova', 'repeated_anova', 'simple', 'multiple',
                                               'moderation', 'partial', 'chi_square']:
                        result = calculator.calculate(
                            effect_size=es,
                            n=n,
                            alpha=alpha,
                            solve_for='power',
                            **calc_kwargs
                        )
                    else:
                        # Segment or proportions
                        if 'prevalence' in dir(calculator):
                            result = calculator.calculate(
                                effect_size=es,
                                total_n=n,
                                alpha=alpha,
                                solve_for='power',
                                **calc_kwargs
                            )
                        else:
                            result = calculator.calculate(
                                effect_size=es,
                                n=n,
                                alpha=alpha,
                                solve_for='power',
                                **calc_kwargs
                            )
                else:
                    result = calculator.calculate(
                        effect_size=es,
                        n=n,
                        alpha=alpha,
                        solve_for='power',
                        **calc_kwargs
                    )

                power_matrix[i, j] = result['power']
            except (ValueError, KeyError):
                power_matrix[i, j] = np.nan

    # Create heatmap
    fig = go.Figure(data=go.Heatmap(
        z=power_matrix,
        x=n_values,
        y=es_values,
        colorscale='RdYlGn',
        zmin=0,
        zmax=1,
        colorbar=dict(title="Power", tickformat='.0%'),
        hovertemplate='<b>Sample Size</b>: %{x}<br>' +
                     '<b>Effect Size</b>: %{y:.3f}<br>' +
                     '<b>Power</b>: %{z:.1%}<br>' +
                     '<extra></extra>'
    ))

    # Add contour line at 80% power
    fig.add_trace(go.Contour(
        z=power_matrix,
        x=n_values,
        y=es_values,
        contours=dict(
            start=0.80,
            end=0.80,
            size=0.01,
            showlabels=True,
            labelfont=dict(size=12, color='white')
        ),
        showscale=False,
        line=dict(color='white', width=3),
        hoverinfo='skip'
    ))

    if title is None:
        title = f"Power Analysis Matrix (α={alpha})"

    fig.update_layout(
        title=title,
        xaxis_title="Sample Size",
        yaxis_title="Effect Size",
        height=600
    )

    return fig


def create_segment_allocation_plot(
    segment_result: Dict,
    title: str = "Segment Sample Allocation"
) -> go.Figure:
    """
    Visualize sample allocation across segments.

    Args:
        segment_result: Result from SegmentPowerCalc.calculate()
        title: Plot title

    Returns:
        Plotly figure object
    """
    segments = [f"Segment {i+1}" for i in range(segment_result['n_segments'])]
    n_per_segment = segment_result['n_per_segment']
    prevalence = segment_result['prevalence']

    fig = make_subplots(
        rows=1, cols=2,
        subplot_titles=('Sample Allocation', 'Population Prevalence'),
        specs=[[{'type': 'bar'}, {'type': 'pie'}]]
    )

    # Bar chart: sample sizes
    fig.add_trace(
        go.Bar(
            x=segments,
            y=n_per_segment,
            text=n_per_segment,
            textposition='auto',
            marker=dict(color='steelblue'),
            name='Sample Size'
        ),
        row=1, col=1
    )

    # Pie chart: prevalence
    fig.add_trace(
        go.Pie(
            labels=segments,
            values=prevalence,
            textinfo='label+percent',
            name='Prevalence'
        ),
        row=1, col=2
    )

    fig.update_layout(
        title_text=title,
        showlegend=False,
        height=400
    )

    fig.update_yaxes(title_text="Sample Size", row=1, col=1)

    return fig
