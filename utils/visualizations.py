
# ==============================================================================
# FILE: utils/visualizations.py (UPDATED - Department Chart Fix)
# ==============================================================================
"""
Plotly chart generation utilities.
Creates all dashboard visualizations.
"""

import plotly.graph_objects as go
import polars as pl
from scipy import stats
import numpy as np
from config import COLORS, TOP_DEPARTMENTS_DISPLAY


def create_yoy_trends_chart(yearly_data):
    """
    Create year-over-year trends chart with pass, distinction, and fail rates.
    
    Args:
        yearly_data (pl.DataFrame): Yearly aggregated data
        
    Returns:
        go.Figure: Plotly figure object
    """
    fig = go.Figure()
    
    # Pass rate line
    years = [int(y) if y is not None else None for y in yearly_data['exam_year'].to_list()]
    fig.add_trace(go.Scatter(
        x=years,
        y=yearly_data['pass_rate'].to_list(),
        mode='lines+markers',
        name='Pass Rate',
        line=dict(color=COLORS['pass'], width=3),
        marker=dict(size=10),
        hovertemplate='<b>Year %{x}</b><br>Pass Rate: %{y:.1f}%<extra></extra>'
    ))
    
    # Distinction rate line
    fig.add_trace(go.Scatter(
        x=years,
        y=yearly_data['dist_rate'].to_list(),
        mode='lines+markers',
        name='Distinction Rate',
        line=dict(color=COLORS['distinction'], width=3),
        marker=dict(size=10),
        hovertemplate='<b>Year %{x}</b><br>Distinction: %{y:.1f}%<extra></extra>'
    ))
    
    # Fail rate line
    fig.add_trace(go.Scatter(
        x=years,
        y=yearly_data['fail_rate'].to_list(),
        mode='lines+markers',
        name='Failure Rate',
        line=dict(color=COLORS['fail'], width=3),
        marker=dict(size=10),
        hovertemplate='<b>Year %{x}</b><br>Failure: %{y:.1f}%<extra></extra>'
    ))
    
    # Add trend lines if enough data points
    if len(yearly_data) > 2:
        for metric, color in [('pass_rate', COLORS['pass']), 
                              ('dist_rate', COLORS['distinction']), 
                              ('fail_rate', COLORS['fail'])]:
            trend_df = yearly_data.select([
                pl.col('exam_year').cast(pl.Float64, strict=False).alias('exam_year'),
                pl.col(metric).cast(pl.Float64, strict=False).alias(metric)
            ]).drop_nulls()

            if trend_df.height > 1:
                x_vals = trend_df['exam_year'].to_numpy()
                y_vals = trend_df[metric].to_numpy()
                slope, intercept, *_ = stats.linregress(x_vals, y_vals)
                trend_line = slope * x_vals + intercept

                fig.add_trace(go.Scatter(
                    x=x_vals.tolist(),
                    y=trend_line.tolist(),
                    mode='lines',
                    line=dict(color=color, width=2, dash='dash'),
                    showlegend=False,
                    opacity=0.4,
                    hoverinfo='skip'
                ))
    
    fig.update_layout(
        xaxis_title="Academic Year",
        yaxis_title="Percentage (%)",
        hovermode='x unified',
        height=400,
        template="plotly_white",
        legend=dict(orientation='h', y=-0.2, x=0.5, xanchor='center'),
        yaxis=dict(range=[0, 100]),
        xaxis=dict(type='linear', tickformat='d', dtick=1)
    )
    
    return fig


def create_department_comparison_chart(df, department_filter='All'):
    """
    Create department or subject comparison chart with improved handling.
    
    Args:
        df (pl.DataFrame): Input DataFrame
        department_filter (str): Selected department
        
    Returns:
        go.Figure: Plotly figure object
    """
    import polars as pl
    
    fig = go.Figure()
    
    if department_filter == 'All':
        # Show top departments
        top_depts = (df.group_by('department')
                     .agg(pl.count().alias('count'))
                     .sort('count', descending=True)
                     .head(TOP_DEPARTMENTS_DISPLAY)['department'].to_list())
        
        # Normalize pass_fail for accurate pass count
        pass_fail_norm = df['pass_fail'].cast(pl.Utf8, strict=False).fill_null("").str.to_lowercase()
        
        dept_data = (df.with_columns(pass_fail_norm.alias('_pass_fail_norm'))
            .filter(pl.col('department').is_in(top_depts))
            .group_by(['exam_year', 'department'])
            .agg([
                pl.count().alias('total'),
                (pl.col('_pass_fail_norm') == 'pass').sum().alias('pass_count')
            ])
            .with_columns(
                (pl.col('pass_count') / pl.col('total') * 100).alias('pass_rate')
            )
            .sort(['department', 'exam_year'])
        )
        
        # Calculate min and max pass rates for dynamic y-axis
        all_rates = dept_data['pass_rate'].to_list()
        min_rate = min(all_rates) if all_rates else 0
        max_rate = max(all_rates) if all_rates else 100
        
        # Add 5% padding to min/max
        y_min = max(0, min_rate - 5)
        y_max = min(100, max_rate + 5)
        
        for dept_name in top_depts:
            dept_subset = dept_data.filter(pl.col('department') == dept_name)
            
            # Skip departments with insufficient data
            if len(dept_subset) < 2:
                continue
                
            fig.add_trace(go.Scatter(
                x=dept_subset['exam_year'].to_list(),
                y=dept_subset['pass_rate'].to_list(),
                mode='lines+markers',
                name=dept_name[:30],
                line=dict(width=2),
                marker=dict(size=8),
                connectgaps=False,
                hovertemplate=f'<b>{dept_name}</b><br>Year: %{{x}}<br>Pass Rate: %{{y:.1f}}%<extra></extra>'
            ))
    else:
        # Show subjects within selected department
        dept_df = df.filter(pl.col('department') == department_filter)

        top_subjects = (dept_df.group_by('subject')
                        .agg(pl.count().alias('count'))
                        .sort('count', descending=True)
                        .head(10)['subject'].to_list())
        
        # Normalize pass_fail for accurate pass count
        pass_fail_norm = dept_df['pass_fail'].cast(pl.Utf8, strict=False).fill_null("").str.to_lowercase()
        
        subj_data = (dept_df.with_columns(pass_fail_norm.alias('_pass_fail_norm'))
            .filter(pl.col('subject').is_in(top_subjects))
            .group_by(['exam_year', 'subject'])
            .agg([
                pl.count().alias('total'),
                (pl.col('_pass_fail_norm') == 'pass').sum().alias('pass_count')
            ])
            .with_columns(
                (pl.col('pass_count') / pl.col('total') * 100).alias('pass_rate')
            )
            .sort(['subject', 'exam_year'])
        )
        
        # Calculate min and max pass rates for dynamic y-axis
        all_rates = subj_data['pass_rate'].to_list()
        min_rate = min(all_rates) if all_rates else 0
        max_rate = max(all_rates) if all_rates else 100
        
        # Add 5% padding to min/max
        y_min = max(0, min_rate - 5)
        y_max = min(100, max_rate + 5)
        
        for subj_name in top_subjects:
            subj_subset = subj_data.filter(pl.col('subject') == subj_name)
            
            # Skip subjects with insufficient data
            if len(subj_subset) < 2:
                continue
                
            fig.add_trace(go.Scatter(
                x=subj_subset['exam_year'].to_list(),
                y=subj_subset['pass_rate'].to_list(),
                mode='lines+markers',
                name=str(subj_name)[:30],
                line=dict(width=2),
                marker=dict(size=8),
                connectgaps=False,
                hovertemplate=f'<b>{subj_name}</b><br>Year: %{{x}}<br>Pass Rate: %{{y:.1f}}%<extra></extra>'
            ))
    
    fig.update_layout(
        xaxis_title="Academic Year",
        yaxis_title="Pass Rate (%)",
        hovermode='x unified',
        height=400,
        template="plotly_white",
        legend=dict(orientation='v', y=1, x=1.02),
        yaxis=dict(range=[y_min, y_max]),  # Dynamic range based on data
        xaxis=dict(type='linear', dtick=1)  # Force linear x-axis with year steps
    )
    
    return fig


def create_assessment_trend_chart(summary_df):
    """
    Create CIA vs ESE trend chart by academic year.

    Args:
        summary_df (pl.DataFrame): Output of get_assessment_yearly_summary

    Returns:
        go.Figure: Plotly figure object
    """
    fig = go.Figure()

    if summary_df.height == 0 or "exam_year" not in summary_df.columns:
        fig.update_layout(
            xaxis_title="Academic Year",
            yaxis_title="Average Percentage",
            hovermode="x unified",
            height=400,
            template="plotly_white",
            legend=dict(orientation="h", y=-0.2, x=0.5, xanchor="center"),
            annotations=[
                dict(
                    text="No assessment data available for the selected filters.",
                    xref="paper",
                    yref="paper",
                    x=0.5,
                    y=0.5,
                    showarrow=False,
                    font=dict(color="#6b7280"),
                )
            ],
        )
        return fig

    # CIA and ESE trends for theory
    years = [int(y) if y is not None else None for y in summary_df["exam_year"].to_list()]
    fig.add_trace(
        go.Scatter(
            x=years,
            y=summary_df["cia_theory_avg"].to_list(),
            mode="lines+markers",
            name="CIA Theory",
            line=dict(color="#2563eb", width=3),
            marker=dict(size=8),
            hovertemplate="<b>Year %{x}</b><br>CIA Theory: %{y:.1f}<extra></extra>",
        )
    )
    fig.add_trace(
        go.Scatter(
            x=years,
            y=summary_df["ese_theory_avg"].to_list(),
            mode="lines+markers",
            name="ESE Theory",
            line=dict(color="#0ea5e9", width=3),
            marker=dict(size=8),
            hovertemplate="<b>Year %{x}</b><br>ESE Theory: %{y:.1f}<extra></extra>",
        )
    )

    # CIA and ESE trends for practical
    fig.add_trace(
        go.Scatter(
            x=years,
            y=summary_df["cia_practical_avg"].to_list(),
            mode="lines+markers",
            name="CIA Practical",
            line=dict(color="#f97316", width=3, dash="dash"),
            marker=dict(size=8),
            hovertemplate="<b>Year %{x}</b><br>CIA Practical: %{y:.1f}<extra></extra>",
        )
    )
    fig.add_trace(
        go.Scatter(
            x=years,
            y=summary_df["ese_practical_avg"].to_list(),
            mode="lines+markers",
            name="ESE Practical",
            line=dict(color="#facc15", width=3, dash="dash"),
            marker=dict(size=8),
            hovertemplate="<b>Year %{x}</b><br>ESE Practical: %{y:.1f}<extra></extra>",
        )
    )

    fig.update_layout(
        xaxis_title="Academic Year",
        yaxis_title="Average Percentage",
        hovermode="x unified",
        height=400,
        template="plotly_white",
        legend=dict(orientation="h", y=-0.2, x=0.5, xanchor="center"),
        xaxis=dict(type='linear', dtick=1)
    )

    return fig


def create_assessment_gap_chart(dept_summary):
    """
    Create grouped bar chart showing CIA vs ESE gaps by department.

    Args:
        dept_summary (pl.DataFrame): Output of get_assessment_department_summary

    Returns:
        go.Figure: Plotly figure object
    """
    fig = go.Figure()

    if dept_summary.height == 0 or "department" not in dept_summary.columns:
        fig.update_layout(
            xaxis_title="Department",
            yaxis_title="Average Gap (pts)",
            barmode="group",
            template="plotly_white",
            height=400,
            annotations=[
                dict(
                    text="No department-level assessment data available.",
                    xref="paper",
                    yref="paper",
                    x=0.5,
                    y=0.5,
                    showarrow=False,
                    font=dict(color="#6b7280"),
                )
            ],
        )
        return fig

    departments = dept_summary["department"].to_list()

    fig.add_trace(
        go.Bar(
            x=departments,
            y=dept_summary["theory_gap"].to_list(),
            name="Theory Gap (ESE - CIA)",
            marker_color="#3b82f6",
            hovertemplate="<b>%{x}</b><br>Theory Gap: %{y:.1f}<extra></extra>",
        )
    )

    fig.add_trace(
        go.Bar(
            x=departments,
            y=dept_summary["practical_gap"].to_list(),
            name="Practical Gap (ESE - CIA)",
            marker_color="#f59e0b",
            hovertemplate="<b>%{x}</b><br>Practical Gap: %{y:.1f}<extra></extra>",
        )
    )

    fig.update_layout(
        xaxis_title="Department",
        yaxis_title="Average Gap (pts)",
        barmode="group",
        template="plotly_white",
        height=400,
        legend=dict(orientation="h", y=-0.2, x=0.5, xanchor="center"),
        yaxis=dict(zeroline=True, zerolinewidth=1.5, zerolinecolor="#94a3b8"),
    )

    return fig


def create_distribution_chart(df):
    """
    Create stacked bar chart showing performance distribution by year.
    Uses pass_fail column for Pass/Fail rates and performance column for Distinction.
    
    Args:
        df (pl.DataFrame): Input DataFrame
        
    Returns:
        go.Figure: Plotly figure object
    """
    import polars as pl
    
    # Create a classification column combining pass_fail and distinction
    df_chart = df.with_columns(
        pl.when(
            pl.col('pass_fail').cast(pl.Utf8, strict=False).fill_null("").str.to_lowercase() == 'fail'
        )
        .then(pl.lit('Fail'))
        .when(
            (pl.col('pass_fail').cast(pl.Utf8, strict=False).fill_null("").str.to_lowercase() == 'pass') & 
            (pl.col('performance') == 'Distinction')
        )
        .then(pl.lit('Distinction'))
        .when(
            pl.col('pass_fail').cast(pl.Utf8, strict=False).fill_null("").str.to_lowercase() == 'pass'
        )
        .then(pl.lit('Pass'))
        .otherwise(pl.lit('Other'))
        .alias('_category')
    )
    
    dist_data = (df_chart
        .group_by(['exam_year', '_category'])
        .agg(pl.count().alias('count'))
        .pivot(index='exam_year', columns='_category', values='count')
        .fill_null(0)
        .sort('exam_year')
    )
    
    fig = go.Figure()
    
    # Add bars for each performance category in correct order
    for perf in ['Distinction', 'Pass', 'Fail']:
        if perf in dist_data.columns:
            # Convert years to integers for proper x-axis display
            years = [int(y) if y is not None else None for y in dist_data['exam_year'].to_list()]
            fig.add_trace(go.Bar(
                x=years,
                y=dist_data[perf].to_list(),
                name=perf,
                marker_color=COLORS.get(perf.lower(), COLORS['neutral']),
                hovertemplate=f'<b>{perf}</b><br>Year: %{{x}}<br>Count: %{{y:,}}<extra></extra>'
            ))
    
    fig.update_layout(
        barmode='stack',
        xaxis_title="Academic Year",
        yaxis_title="Number of Exam Attempts",
        height=350,
        template="plotly_white",
        legend=dict(orientation='h', y=-0.2, x=0.5, xanchor='center'),
        xaxis=dict(type='linear', tickformat='d')
    )
    
    return fig


def create_subject_difficulty_chart(difficulty_df: pl.DataFrame) -> go.Figure:
    """
    Create bar chart showing subject difficulty.
    
    Lower average marks imply higher difficulty.
    """
    fig = go.Figure()

    if difficulty_df is None or difficulty_df.height == 0:
        fig.update_layout(
            xaxis_title="Subject",
            yaxis_title="Average Marks",
            template="plotly_white",
            height=400,
            annotations=[
                dict(
                    text="No subject difficulty data available for the selected filters.",
                    xref="paper",
                    yref="paper",
                    x=0.5,
                    y=0.5,
                    showarrow=False,
                    font=dict(color="#6b7280"),
                )
            ],
        )
        return fig

    # Sort by average marks ascending (hardest first)
    data = difficulty_df.sort("avg_total_marks")

    subjects = data["subject"].to_list()
    avg_marks = data["avg_total_marks"].to_list()
    pass_rates = data["pass_rate"].to_list() if "pass_rate" in data.columns else [None] * len(subjects)

    fig.add_trace(
        go.Bar(
            x=subjects,
            y=avg_marks,
            marker_color="#3b82f6",
            hovertemplate="<b>%{x}</b><br>Avg Marks: %{y:.1f}"
            + "<br>Pass Rate: %{customdata:.1f}%<extra></extra>",
            customdata=pass_rates,
        )
    )

    # Calculate dynamic y-axis range based on data
    min_val = min(avg_marks) if avg_marks else 0
    max_val = max(avg_marks) if avg_marks else 100
    
    # Add 10% padding to both sides for visibility
    y_min = max(0, min_val - (max_val - min_val) * 0.1)
    y_max = max_val + (max_val - min_val) * 0.1

    fig.update_layout(
        xaxis_title="Subject (hardest to easiest)",
        yaxis_title="Average Marks",
        template="plotly_white",
        height=400,
        xaxis=dict(tickangle=-45),
        yaxis=dict(range=[y_min, y_max])
    )

    return fig


def create_top_bottom_departments_chart(leaderboard: dict) -> go.Figure:
    """
    Create horizontal bar chart for top and bottom performing departments.
    
    Args:
        leaderboard (dict): Output of get_department_leaderboard
    """
    fig = go.Figure()

    if not leaderboard or "combined" not in leaderboard:
        fig.update_layout(
            xaxis_title="Pass Rate (%)",
            yaxis_title="Department",
            template="plotly_white",
            height=400,
            annotations=[
                dict(
                    text="No department leaderboard data available.",
                    xref="paper",
                    yref="paper",
                    x=0.5,
                    y=0.5,
                    showarrow=False,
                    font=dict(color="#6b7280"),
                )
            ],
        )
        return fig

    combined = leaderboard["combined"]
    if isinstance(combined, pl.DataFrame) and combined.height > 0:
        df_plot = combined.sort("pass_rate")

        departments = df_plot["department"].to_list()
        pass_rates = df_plot["pass_rate"].to_list()
        categories = df_plot["category"].to_list() if "category" in df_plot.columns else ["Dept"] * len(departments)

        colors = ["#22c55e" if cat == "Top" else "#ef4444" for cat in categories]

        fig.add_trace(
            go.Bar(
                x=pass_rates,
                y=departments,
                orientation="h",
                marker_color=colors,
                hovertemplate="<b>%{y}</b><br>Pass Rate: %{x:.1f}%<extra></extra>",
            )
        )

        fig.update_layout(
            xaxis_title="Pass Rate (%)",
            yaxis_title="Department",
            template="plotly_white",
            height=400,
            yaxis=dict(autorange="reversed"),
        )
    else:
        fig.update_layout(
            xaxis_title="Pass Rate (%)",
            yaxis_title="Department",
            template="plotly_white",
            height=400,
            annotations=[
                dict(
                    text="No department leaderboard data available.",
                    xref="paper",
                    yref="paper",
                    x=0.5,
                    y=0.5,
                    showarrow=False,
                    font=dict(color="#6b7280"),
                )
            ],
        )

    return fig
















# """
# Plotly chart generation utilities.
# Creates all dashboard visualizations.
# """

# import polars as pl
# import plotly.graph_objects as go
# from scipy import stats
# import numpy as np
# from config import COLORS, TOP_DEPARTMENTS_DISPLAY


# def create_yoy_trends_chart(yearly_data):
#     """
#     Create year-over-year trends chart with pass, distinction, and fail rates.
    
#     Args:
#         yearly_data (pl.DataFrame): Yearly aggregated data
        
#     Returns:
#         go.Figure: Plotly figure object
#     """
#     fig = go.Figure()
    
#     # Pass rate line
#     fig.add_trace(go.Scatter(
#         x=yearly_data['exam_year'].to_list(),
#         y=yearly_data['pass_rate'].to_list(),
#         mode='lines+markers',
#         name='Pass Rate',
#         line=dict(color=COLORS['pass'], width=3),
#         marker=dict(size=10),
#         hovertemplate='<b>Year %{x}</b><br>Pass Rate: %{y:.1f}%<extra></extra>'
#     ))
    
#     # Distinction rate line
#     fig.add_trace(go.Scatter(
#         x=yearly_data['exam_year'].to_list(),
#         y=yearly_data['dist_rate'].to_list(),
#         mode='lines+markers',
#         name='Distinction Rate',
#         line=dict(color=COLORS['distinction'], width=3),
#         marker=dict(size=10),
#         hovertemplate='<b>Year %{x}</b><br>Distinction: %{y:.1f}%<extra></extra>'
#     ))
    
#     # Fail rate line
#     fig.add_trace(go.Scatter(
#         x=yearly_data['exam_year'].to_list(),
#         y=yearly_data['fail_rate'].to_list(),
#         mode='lines+markers',
#         name='Failure Rate',
#         line=dict(color=COLORS['fail'], width=3),
#         marker=dict(size=10),
#         hovertemplate='<b>Year %{x}</b><br>Failure: %{y:.1f}%<extra></extra>'
#     ))
    
#     # Add trend lines if enough data points
#     if len(yearly_data) > 2:
#         x_vals = yearly_data['exam_year'].to_numpy()
        
#         for metric, color in [('pass_rate', COLORS['pass']), 
#                               ('dist_rate', COLORS['distinction']), 
#                               ('fail_rate', COLORS['fail'])]:
#             y_vals = yearly_data[metric].to_numpy()
#             slope, intercept, *_ = stats.linregress(x_vals, y_vals)
#             trend_line = slope * x_vals + intercept
            
#             fig.add_trace(go.Scatter(
#                 x=x_vals.tolist(),
#                 y=trend_line.tolist(),
#                 mode='lines',
#                 line=dict(color=color, width=2, dash='dash'),
#                 showlegend=False,
#                 opacity=0.4,
#                 hoverinfo='skip'
#             ))
    
#     fig.update_layout(
#         xaxis_title="Academic Year",
#         yaxis_title="Percentage (%)",
#         hovermode='x unified',
#         height=400,
#         template="plotly_white",
#         legend=dict(orientation='h', y=-0.2, x=0.5, xanchor='center'),
#         yaxis=dict(range=[0, 100])
#     )
    
#     return fig


# def create_department_comparison_chart(df, department_filter='All'):
#     """
#     Create department or subject comparison chart.
    
#     Args:
#         df (pl.DataFrame): Input DataFrame
#         department_filter (str): Selected department
        
#     Returns:
#         go.Figure: Plotly figure object
#     """
#     fig = go.Figure()
    
#     if department_filter == 'All':
#         # Show top departments
#         top_depts = (df.group_by('offering_department')
#                      .agg(pl.count().alias('count'))
#                      .sort('count', descending=True)
#                      .head(TOP_DEPARTMENTS_DISPLAY)['offering_department'].to_list())
        
#         dept_data = (df.filter(pl.col('offering_department').is_in(top_depts))
#             .group_by(['exam_year', 'offering_department'])
#             .agg([
#                 pl.count().alias('total'),
#                 ((pl.col('performance') == 'Pass') | 
#                  (pl.col('performance') == 'Distinction')).sum().alias('pass_count')
#             ])
#             .with_columns(
#                 (pl.col('pass_count') / pl.col('total') * 100).alias('pass_rate')
#             )
#         )
        
#         for dept_name in top_depts:
#             dept_subset = dept_data.filter(pl.col('offering_department') == dept_name)
#             fig.add_trace(go.Scatter(
#                 x=dept_subset['exam_year'].to_list(),
#                 y=dept_subset['pass_rate'].to_list(),
#                 mode='lines+markers',
#                 name=dept_name[:30],
#                 line=dict(width=2),
#                 marker=dict(size=6),
#                 hovertemplate=f'<b>{dept_name}</b><br>Year: %{{x}}<br>Pass Rate: %{{y:.1f}}%<extra></extra>'
#             ))
#     else:
#         # Show subjects within selected department
#         top_subjects = (df.group_by('name')
#                         .agg(pl.count().alias('count'))
#                         .sort('count', descending=True)
#                         .head(10)['name'].to_list())
        
#         subj_data = (df.filter(pl.col('name').is_in(top_subjects))
#             .group_by(['exam_year', 'name'])
#             .agg([
#                 pl.count().alias('total'),
#                 ((pl.col('performance') == 'Pass') | 
#                  (pl.col('performance') == 'Distinction')).sum().alias('pass_count')
#             ])
#             .with_columns(
#                 (pl.col('pass_count') / pl.col('total') * 100).alias('pass_rate')
#             )
#         )
        
#         for subj_name in top_subjects:
#             subj_subset = subj_data.filter(pl.col('name') == subj_name)
#             fig.add_trace(go.Scatter(
#                 x=subj_subset['exam_year'].to_list(),
#                 y=subj_subset['pass_rate'].to_list(),
#                 mode='lines+markers',
#                 name=str(subj_name)[:30],
#                 line=dict(width=2),
#                 marker=dict(size=6),
#                 hovertemplate=f'<b>{subj_name}</b><br>Year: %{{x}}<br>Pass Rate: %{{y:.1f}}%<extra></extra>'
#             ))
    
#     fig.update_layout(
#         xaxis_title="Academic Year",
#         yaxis_title="Pass Rate (%)",
#         hovermode='x unified',
#         height=400,
#         template="plotly_white",
#         legend=dict(orientation='v', y=1, x=1.02),
#         yaxis=dict(range=[0, 100])
#     )
    
#     return fig


# def create_distribution_chart(df):
#     """
#     Create stacked bar chart showing performance distribution by year.
    
#     Args:
#         df (pl.DataFrame): Input DataFrame
        
#     Returns:
#         go.Figure: Plotly figure object
#     """
#     dist_data = (df
#         .group_by(['exam_year', 'performance'])
#         .agg(pl.count().alias('count'))
#         .pivot(index='exam_year', columns='performance', values='count')
#         .fill_null(0)
#     )
    
#     fig = go.Figure()
    
#     # Add bars for each performance category
#     for perf in ['Distinction', 'Pass', 'Fail']:
#         if perf in dist_data.columns:
#             fig.add_trace(go.Bar(
#                 x=dist_data['exam_year'].to_list(),
#                 y=dist_data[perf].to_list(),
#                 name=perf,
#                 marker_color=COLORS.get(perf.lower(), COLORS['neutral']),
#                 hovertemplate=f'<b>{perf}</b><br>Year: %{{x}}<br>Count: %{{y:,}}<extra></extra>'
#             ))
    
#     fig.update_layout(
#         barmode='stack',
#         xaxis_title="Academic Year",
#         yaxis_title="Number of Exam Attempts",
#         height=350,
#         template="plotly_white",
#         legend=dict(orientation='h', y=-0.2, x=0.5, xanchor='center')
#     )
    
#     return fig
