# ==============================================================================
# FILE: dashboard/callbacks.py (FIXED VERSION)
# ==============================================================================
"""
Dashboard callbacks - handles all interactivity and data updates.
FIXES:
1. Only updates dashboard when search button is clicked
2. Subject dropdown filters based on selected department
"""

import math

import dash_bootstrap_components as dbc
from dash import html, Input, Output, State
from data.processor import filter_data
from utils.calculations import (
    calculate_rates,
    get_yearly_data,
    get_department_stats,
    get_assessment_yearly_summary,
    get_assessment_department_summary,
    get_subject_difficulty,
    get_department_leaderboard,
)
from utils.visualizations import (
    create_yoy_trends_chart,
    create_department_comparison_chart,
    create_distribution_chart,
    create_assessment_trend_chart,
    create_subject_difficulty_chart,
    create_top_bottom_departments_chart,
)
from .components import create_trend_indicator
from config import (
    HIGH_FAILURE_THRESHOLD,
    LOW_DISTINCTION_THRESHOLD,
    EXCELLENT_PERFORMANCE_THRESHOLD,
    CRITICAL_PASS_RATE,
    HIGH_PERFORMANCE_PASS_RATE,
    CRITICAL_DEPARTMENTS_DISPLAY,
    HIGH_PERFORMERS_DISPLAY,
)
import polars as pl


def register_callbacks(app, df):
    """
    Register all dashboard callbacks.
    
    Args:
        app: Dash app instance
        df (pl.DataFrame): Main DataFrame
    """
    
    # NEW CALLBACK: Update subject dropdown based on department selection
    @app.callback(
        Output('subject-filter', 'options'),
        Output('subject-filter', 'value'),
        Input('department-filter', 'value')
    )
    def update_subject_dropdown(selected_dept):
        """
        Update subject dropdown options based on selected department.
        
        Args:
            selected_dept (str): Selected department
            
        Returns:
            tuple: (subject_options, default_value)
        """
        if selected_dept == 'All':
            subjects = sorted([s for s in df['subject'].unique().to_list() if s])
        else:
            subjects = sorted(
                [
                    s
                    for s in df.filter(pl.col('department') == selected_dept)['subject'].unique().to_list()
                    if s
                ]
            )
        
        # Create dropdown options (always include All)
        options = [{'label': 'All Subjects', 'value': 'All'}] + [
            {'label': subj, 'value': subj} for subj in subjects
        ]
        
        return options, 'All'
    
    
    # MAIN CALLBACK: Only triggers on search button click (using State instead of Input)
    @app.callback(
        [
            Output('kpi-total', 'children'),
            Output('kpi-total-change', 'children'),
            Output('kpi-pass', 'children'),
            Output('kpi-pass-trend', 'children'),
            Output('kpi-distinction', 'children'),
            Output('kpi-distinction-trend', 'children'),
            Output('kpi-fail', 'children'),
            Output('kpi-fail-trend', 'children'),
            Output('kpi-cia-theory', 'children'),
            Output('kpi-cia-theory-trend', 'children'),
            Output('kpi-ese-theory', 'children'),
            Output('kpi-ese-theory-trend', 'children'),
            Output('kpi-cia-practical', 'children'),
            Output('kpi-cia-practical-trend', 'children'),
            Output('alerts-section', 'children'),
            Output('yoy-trends', 'figure'),
            Output('dept-comparison', 'figure'),
            Output('distribution-chart', 'figure'),
            Output('assessment-trend', 'figure'),
            Output('subject-difficulty-chart', 'figure'),
            Output('dept-leaderboard-chart', 'figure'),
            Output('detail-table', 'children'),
            Output('recommendations', 'children'),
            Output('loading-output', 'children'),
        ],
        Input('search-button', 'n_clicks'),  # Only input is the search button
        [
            State('year-range-slider', 'value'),
            State('department-filter', 'value'),
            State('semester-filter', 'value'),
            State('subject-filter', 'value'),
        ],
        prevent_initial_call=False  # Allow initial load
    )
    def update_dashboard(n_clicks, year_range, dept, sem, subj):
        """
        Main callback to update all dashboard components.
        Only triggers when search button is clicked.
        
        Args:
            n_clicks: Number of times search button clicked
            year_range: Selected year range (State)
            dept: Selected department (State)
            sem: Selected semester (State)
            subj: Selected subject (State)
        """
        
        # Filter data based on user selections
        filtered = filter_data(df, year_range, dept, sem, subj)
        
        def safe_mean(frame: pl.DataFrame, column: str):
            if column not in frame.columns or frame.height == 0:
                return None
            series = (
                frame.select(pl.col(column).cast(pl.Float64, strict=False))
                .to_series()
                .drop_nulls()
            )
            if len(series) == 0:
                return None
            value = float(series.mean())
            if math.isnan(value):
                return None
            return value

        def format_percentage(value):
            return f"{value:.1f}%" if value is not None else "N/A"

        def build_trend(current, baseline, label="overall avg", inverse=False, unit="%"):
            if current is None or baseline is None:
                return create_trend_indicator(None, None, label, inverse, unit=unit)
            return create_trend_indicator(current, baseline, label, inverse, unit=unit)

        # Calculate overall metrics for filtered data
        pass_rate, dist_rate, fail_rate, unique_students, total_exams = calculate_rates(filtered)
        
        # Calculate overall dataset average for comparison
        overall_pass, overall_dist, overall_fail, overall_unique, overall_exams = calculate_rates(df)
        
        # ===== KPIs =====
        kpi_total = f"{unique_students:,}"
        kpi_total_change = f"{total_exams:,} exam attempts"
        kpi_pass = f"{pass_rate:.1f}%"
        kpi_distinction = f"{dist_rate:.1f}%"
        kpi_fail = f"{fail_rate:.1f}%"
        
        # Trends vs overall average
        kpi_pass_trend = create_trend_indicator(pass_rate, overall_pass, "overall avg", inverse_colors=False)
        kpi_dist_trend = create_trend_indicator(dist_rate, overall_dist, "overall avg", inverse_colors=False)
        kpi_fail_trend = create_trend_indicator(fail_rate, overall_fail, "overall avg", inverse_colors=True)

        # CIA / ESE Metrics
        # Use correct derived column names from loader
        cia_theory_avg = safe_mean(filtered, "cia_theory_avg")
        ese_theory_avg = safe_mean(filtered, "ese_theory_internal")
        cia_practical_avg = safe_mean(filtered, "cia_practical_avg")

        cia_theory_overall = safe_mean(df, "cia_theory_avg")
        ese_theory_overall = safe_mean(df, "ese_theory_internal")
        cia_practical_overall = safe_mean(df, "cia_practical_avg")

        assessment_gap = (
            ese_theory_avg - cia_theory_avg
            if ese_theory_avg is not None and cia_theory_avg is not None
            else None
        )
        kpi_cia_theory = format_percentage(cia_theory_avg)
        kpi_ese_theory = format_percentage(ese_theory_avg)
        kpi_cia_practical = format_percentage(cia_practical_avg)

        kpi_cia_theory_trend = build_trend(
            cia_theory_avg, cia_theory_overall, "overall avg", inverse=False
        )
        kpi_ese_theory_trend = build_trend(
            ese_theory_avg, ese_theory_overall, "overall avg", inverse=False
        )
        kpi_cia_practical_trend = build_trend(
            cia_practical_avg, cia_practical_overall, "overall avg", inverse=False
        )
        
        # ===== CHARTS =====
        yearly_data = get_yearly_data(filtered)
        assessment_yearly = get_assessment_yearly_summary(filtered)
        dept_assessment = get_assessment_department_summary(filtered)
        
        yoy_fig = create_yoy_trends_chart(yearly_data)
        dept_fig = create_department_comparison_chart(filtered, dept)
        dist_fig = create_distribution_chart(filtered)
        assessment_trend_fig = create_assessment_trend_chart(assessment_yearly)
        # Get full subject difficulty data
        subject_difficulty_df = get_subject_difficulty(filtered)

        # Select only bottom 10 subjects (most difficult = lowest avg_total_marks)
        if subject_difficulty_df is not None and len(subject_difficulty_df) > 0:
            subject_difficulty_df = (
                subject_difficulty_df
                .sort("avg_total_marks")            # ascending by default
                .sort("avg_total_marks", descending=True)  # for descending
                .head(10)
            )

        # Create chart from filtered data
        subject_difficulty_fig = create_subject_difficulty_chart(subject_difficulty_df)

        dept_leaderboard_data = get_department_leaderboard(filtered)
        dept_leaderboard_fig = create_top_bottom_departments_chart(dept_leaderboard_data)
        
        # ===== DETAILED TABLE =====
        detail_source = yearly_data.join(assessment_yearly, on='exam_year', how='left')
        detail_table = create_detailed_table(detail_source)
        
        # ===== ALERTS =====
        alert_section = create_alerts(pass_rate, dist_rate, fail_rate)
        
        # ===== RECOMMENDATIONS =====
        recommendations_div = create_recommendations(
            filtered,
            year_range,
            pass_rate,
            unique_students,
            total_exams,
            cia_theory_avg,
            ese_theory_avg,
            assessment_gap,
            dept_assessment,
            subject_difficulty_df,
            dept_leaderboard_data,
        )
        
        return (
            kpi_total, kpi_total_change,
            kpi_pass, kpi_pass_trend,
            kpi_distinction, kpi_dist_trend,
            kpi_fail, kpi_fail_trend,
            kpi_cia_theory, kpi_cia_theory_trend,
            kpi_ese_theory, kpi_ese_theory_trend,
            kpi_cia_practical, kpi_cia_practical_trend,
            alert_section,
            yoy_fig, dept_fig, dist_fig,
            assessment_trend_fig,
            subject_difficulty_fig,
            dept_leaderboard_fig,
            detail_table, recommendations_div,
            ""  # loading-output
        )


def create_detailed_table(yearly_data):
    """
    Create detailed performance table.
    
    Args:
        yearly_data (pl.DataFrame): Yearly aggregated data
        
    Returns:
        dbc.Table: Formatted table component
    """
    table_data = yearly_data.sort('exam_year', descending=True)
    table_rows = []
    
    for row in table_data.iter_rows(named=True):
        pass_rate = row.get('pass_rate') or 0
        pass_bg = '#d1fae5' if pass_rate >= 85 else (
            '#fef3c7' if pass_rate >= 75 else '#fee2e2'
        )
        
        table_rows.append(html.Tr([
            html.Td(str(int(row['exam_year'])), style={'fontWeight': 'bold'}),
            html.Td(f"{int(row['unique_students']):,}", style={'textAlign': 'center'}),
            html.Td(f"{int(row['total_exams']):,}", 
                   style={'textAlign': 'center', 'color': '#6b7280'}),
            html.Td(f"{pass_rate:.1f}%", 
                   style={'textAlign': 'center', 'backgroundColor': pass_bg, 
                          'padding': '8px', 'borderRadius': '4px'}),
            html.Td(f"{(row.get('dist_rate') or 0):.1f}%", style={'textAlign': 'center'}),
            html.Td(f"{(row.get('fail_rate') or 0):.1f}%", style={'textAlign': 'center'}),
        ]))
    
    return dbc.Table([
        html.Thead(html.Tr([
            html.Th("Year"),
            html.Th("Students", style={'textAlign': 'center'}),
            html.Th("Exam Attempts", style={'textAlign': 'center'}),
            html.Th("Pass Rate", style={'textAlign': 'center'}),
            html.Th("Distinction", style={'textAlign': 'center'}),
            html.Th("Failure", style={'textAlign': 'center'}),
        ])),
        html.Tbody(table_rows)
    ], bordered=True, hover=True, striped=True, responsive=True)


def create_alerts(pass_rate, dist_rate, fail_rate):
    """
    Create alert components based on performance thresholds.
    
    Args:
        pass_rate (float): Pass rate percentage
        dist_rate (float): Distinction rate percentage
        fail_rate (float): Failure rate percentage
        
    Returns:
        html.Div: Alert section
    """
    alerts = []
    
    if fail_rate > HIGH_FAILURE_THRESHOLD:
        alerts.append(dbc.Alert([
            html.Strong("⚠️ High Failure Rate: "),
            f"Current failure rate is {fail_rate:.1f}%, requiring immediate attention"
        ], color='danger'))
    
    if dist_rate < LOW_DISTINCTION_THRESHOLD:
        alerts.append(dbc.Alert([
            html.Strong("📉 Low Distinction Rate: "),
            f"Only {dist_rate:.1f}% achieving distinction - review grading standards"
        ], color='warning'))
    
    if pass_rate > EXCELLENT_PERFORMANCE_THRESHOLD:
        alerts.append(dbc.Alert([
            html.Strong("✅ Excellent Performance: "),
            f"Pass rate of {pass_rate:.1f}% indicates strong outcomes"
        ], color='success'))
    
    return html.Div(alerts) if alerts else html.Div()


def create_recommendations(
    filtered,
    year_range,
    pass_rate,
    unique_students,
    total_exams,
    cia_theory_avg=None,
    ese_theory_avg=None,
    assessment_gap=None,
    dept_assessment=None,
    subject_difficulty=None,
    dept_leaderboard=None,
):
    """
    Create recommendations section based on data analysis.
    
    Args:
        filtered (pl.DataFrame): Filtered DataFrame
        year_range (list): Selected year range
        pass_rate (float): Overall pass rate
        unique_students (int): Number of unique students
        total_exams (int): Total exam attempts
        cia_theory_avg (float): Average CIA theory score
        ese_theory_avg (float): Average ESE theory score
        assessment_gap (float): Difference between ESE and CIA theory averages
        dept_assessment (pl.DataFrame): Department-level assessment summary
        subject_difficulty (pl.DataFrame): Subject difficulty metrics
        dept_leaderboard (dict): Top and bottom department performance data
        
    Returns:
        html.Div: Recommendations section
    """
    recommendations = []
    
    if len(filtered) > 0:
        dept_stats = get_department_stats(filtered)
        
        # Critical departments
        critical_depts = dept_stats.filter(
            pl.col('pass_rate') < CRITICAL_PASS_RATE
        ).head(CRITICAL_DEPARTMENTS_DISPLAY)
        
        if len(critical_depts) > 0:
            dept_items = []
            for row in critical_depts.iter_rows(named=True):
                dept_items.append(
                    html.Li(f"{row['department']}: {row['pass_rate']:.1f}% "
                           f"({int(row['students'])} students, {int(row['exams'])} exams)")
                )
            
            recommendations.append(html.Div([
                html.H6("🔴 Critical Departments (Pass Rate < 60%)", 
                       className="text-danger mb-2"),
                html.Ul(dept_items),
                html.P("Actions: Faculty intervention, curriculum review, student support programs",
                      className="text-muted small")
            ], className="mb-3"))
        
        # High performing departments
        high_performers = dept_stats.filter(
            pl.col('pass_rate') >= HIGH_PERFORMANCE_PASS_RATE
        ).sort('pass_rate', descending=True).head(HIGH_PERFORMERS_DISPLAY)
        
        if len(high_performers) > 0:
            perf_items = []
            for row in high_performers.iter_rows(named=True):
                perf_items.append(
                    html.Li(f"{row['department']}: {row['pass_rate']:.1f}% "
                           f"({int(row['students'])} students, {int(row['exams'])} exams)")
                )
            
            recommendations.append(html.Div([
                html.H6("🟢 High Performing Departments (Pass Rate ≥ 85%)", 
                       className="text-success mb-2"),
                html.Ul(perf_items),
                html.P("Document and share best practices across institution",
                      className="text-muted small")
            ], className="mb-3"))
    
        # Assessment gap insights
        if cia_theory_avg is not None and ese_theory_avg is not None:
            gap_text = (
                "Gap: N/A"
                if assessment_gap is None
                else f"Gap: {assessment_gap:+.1f} pts"
            )
            summary_text = (
                f"CIA Theory Avg: {cia_theory_avg:.1f}%, "
                f"ESE Theory Avg: {ese_theory_avg:.1f}%, "
                f"{gap_text}"
            )
            recommendations.append(html.Div([
                html.H6("📝 Assessment Insights", className="text-primary mb-2"),
                html.P(summary_text, className="mb-1"),
                html.P(
                    "Monitor subjects where end-semester performance significantly deviates from internal assessments.",
                    className="text-muted small"
                )
            ], className="mb-3"))

        if dept_assessment is not None and len(dept_assessment) > 0:
            high_gap_depts = (
                dept_assessment
                .filter(pl.col("theory_gap") > 5)
                .sort("theory_gap", descending=True)
                .head(3)
            )
            if len(high_gap_depts) > 0:
                gap_items = []
                for row in high_gap_depts.iter_rows(named=True):
                    gap_items.append(
                        html.Li(
                            f"{row['department']}: "
                            f"{row['theory_gap']:.1f} pts theory gap "
                            f"(CIA {row['cia_theory_avg']:.1f}%, ESE {row['ese_theory_avg']:.1f}%)"
                        )
                    )
                recommendations.append(html.Div([
                    html.H6("📊 Departments with High Theory Gap (ESE - CIA > 5 pts)",
                            className="text-warning mb-2"),
                    html.Ul(gap_items),
                    html.P(
                        "Consider aligning internal evaluations or providing targeted support before final exams.",
                        className="text-muted small"
                    )
                ], className="mb-3"))

    # Year range insights
    if year_range:
        year_span = year_range[1] - year_range[0] + 1
        avg_exams = total_exams / unique_students if unique_students > 0 else 0
        
        recommendations.append(html.Div([
            html.H6("📅 Selected Period Insights", className="text-info mb-2"),
            html.P(f"Analyzing {year_span} year(s) from {year_range[0]} to {year_range[1]}", 
                  className="mb-1"),
            html.P(f"Unique students: {unique_students:,} | Exam attempts: {total_exams:,}", 
                  className="mb-1"),
            html.P(f"Average exams per student: {avg_exams:.1f}" if unique_students > 0 else "", 
                  className="mb-1"),
            html.P(f"Overall pass rate: {pass_rate:.1f}%", className="mb-0")
        ], className="mb-3"))
    
    if subject_difficulty is not None and len(subject_difficulty) > 0:
        hardest = subject_difficulty.sort('avg_total_marks').head(3)
        easiest = subject_difficulty.sort('avg_total_marks', descending=True).head(3)
        
        def format_subject_item(row):
            avg_marks = f"{row['avg_total_marks']:.1f}" if row['avg_total_marks'] is not None else "N/A"
            pass_rate = f"{row['pass_rate']:.1f}" if row['pass_rate'] is not None else "N/A"
            return html.Li(f"{row['subject']}: {avg_marks} avg (Pass {pass_rate}%)")
        
        hardest_items = [format_subject_item(row) for row in hardest.iter_rows(named=True)]
        easiest_items = [format_subject_item(row) for row in easiest.iter_rows(named=True)]
        recommendations.append(html.Div([
            html.H6("🧠 Subject Difficulty Highlights", className="text-secondary mb-2"),
            html.Div([
                html.P("Most Challenging", className="fw-bold mb-1"),
                html.Ul(hardest_items, className="mb-2"),
                html.P("Most Accessible", className="fw-bold mb-1"),
                html.Ul(easiest_items, className="mb-0"),
            ]),
            html.P("Allocate mentoring and enrichment sessions based on difficulty bands.",
                   className="text-muted small mt-2")
        ], className="mb-3"))

    if dept_leaderboard and 'top' in dept_leaderboard and 'bottom' in dept_leaderboard:
        top_df = dept_leaderboard['top']
        bottom_df = dept_leaderboard['bottom']
        if top_df.height > 0 or bottom_df.height > 0:
            top_items = [
                html.Li(f"{row['department']}: {row['pass_rate']:.1f}% (Students {int(row['students'])})")
                for row in top_df.iter_rows(named=True)
            ]
            bottom_items = [
                html.Li(f"{row['department']}: {row['pass_rate']:.1f}% (Students {int(row['students'])})")
                for row in bottom_df.iter_rows(named=True)
            ]
            recommendations.append(html.Div([
                html.H6("🏅 Department Performance Snapshot", className="text-secondary mb-2"),
                html.Div([
                    html.P("Top Performers", className="fw-bold mb-1"),
                    html.Ul(top_items, className="mb-2"),
                    html.P("Needs Attention", className="fw-bold mb-1"),
                    html.Ul(bottom_items, className="mb-0"),
                ]),
            ], className="mb-3"))

    if len(recommendations) == 0:
        recommendations = [
            html.P("✅ Performance metrics are within acceptable ranges. Continue monitoring trends.",
                  className="text-muted")
        ]
    
    return html.Div(recommendations)














# # ==============================================================================
# # FILE: dashboard/callbacks.py (FIXED VERSION)
# # ==============================================================================
# """
# Dashboard callbacks - handles all interactivity and data updates.
# FIXES:
# 1. Only updates dashboard when search button is clicked
# 2. Subject dropdown filters based on selected department
# """

# import dash_bootstrap_components as dbc
# from dash import html, Input, Output, State
# from data.processor import filter_data
# from utils.calculations import calculate_rates, get_yearly_data, get_department_stats
# from utils.visualizations import (
#     create_yoy_trends_chart,
#     create_department_comparison_chart,
#     create_distribution_chart
# )
# from .components import create_trend_indicator
# from config import (
#     HIGH_FAILURE_THRESHOLD,
#     LOW_DISTINCTION_THRESHOLD,
#     EXCELLENT_PERFORMANCE_THRESHOLD,
#     CRITICAL_PASS_RATE,
#     HIGH_PERFORMANCE_PASS_RATE,
#     CRITICAL_DEPARTMENTS_DISPLAY,
#     HIGH_PERFORMERS_DISPLAY,
#     TOP_SUBJECTS_DISPLAY
# )
# import polars as pl


# def register_callbacks(app, df):
#     """
#     Register all dashboard callbacks.
    
#     Args:
#         app: Dash app instance
#         df (pl.DataFrame): Main DataFrame
#     """
    
#     # NEW CALLBACK: Update subject dropdown based on department selection
#     @app.callback(
#         Output('subject-filter', 'options'),
#         Output('subject-filter', 'value'),
#         Input('department-filter', 'value')
#     )
#     def update_subject_dropdown(selected_dept):
#         """
#         Update subject dropdown options based on selected department.
        
#         Args:
#             selected_dept (str): Selected department
            
#         Returns:
#             tuple: (subject_options, default_value)
#         """
#         if selected_dept == 'All':
#             # Show top subjects across all departments
#             top_subjects = (df.group_by('name')
#                             .agg(pl.count().alias('count'))
#                             .sort('count', descending=True)
#                             .head(TOP_SUBJECTS_DISPLAY)['name'].to_list())
#         else:
#             # Show only subjects from selected department
#             dept_subjects = (df.filter(pl.col('offering_department') == selected_dept)
#                             .group_by('name')
#                             .agg(pl.count().alias('count'))
#                             .sort('count', descending=True)
#                             ['name'].to_list())
#             top_subjects = dept_subjects[:TOP_SUBJECTS_DISPLAY]
        
#         # Create dropdown options
#         options = [{'label': 'All Subjects', 'value': 'All'}] + \
#                   [{'label': s, 'value': s} for s in sorted(top_subjects)]
        
#         # Reset to 'All' when department changes
#         return options, 'All'
    
    
#     # MAIN CALLBACK: Only triggers on search button click (using State instead of Input)
#     @app.callback(
#         [
#             Output('kpi-total', 'children'),
#             Output('kpi-total-change', 'children'),
#             Output('kpi-pass', 'children'),
#             Output('kpi-pass-trend', 'children'),
#             Output('kpi-distinction', 'children'),
#             Output('kpi-distinction-trend', 'children'),
#             Output('kpi-fail', 'children'),
#             Output('kpi-fail-trend', 'children'),
#             Output('alerts-section', 'children'),
#             Output('yoy-trends', 'figure'),
#             Output('dept-comparison', 'figure'),
#             Output('distribution-chart', 'figure'),
#             Output('detail-table', 'children'),
#             Output('recommendations', 'children'),
#             Output('loading-output', 'children'),
#         ],
#         Input('search-button', 'n_clicks'),  # Only input is the search button
#         [
#             State('year-range-slider', 'value'),
#             State('department-filter', 'value'),
#             State('semester-filter', 'value'),
#             State('subject-filter', 'value'),
#         ],
#         prevent_initial_call=False  # Allow initial load
#     )
#     def update_dashboard(n_clicks, year_range, dept, sem, subj):
#         """
#         Main callback to update all dashboard components.
#         Only triggers when search button is clicked.
        
#         Args:
#             n_clicks: Number of times search button clicked
#             year_range: Selected year range (State)
#             dept: Selected department (State)
#             sem: Selected semester (State)
#             subj: Selected subject (State)
#         """
        
#         # Filter data based on user selections
#         filtered = filter_data(df, year_range, dept, sem, subj)
        
#         # Calculate overall metrics for filtered data
#         pass_rate, dist_rate, fail_rate, unique_students, total_exams = calculate_rates(filtered)
        
#         # Calculate overall dataset average for comparison
#         overall_pass, overall_dist, overall_fail, overall_unique, overall_exams = calculate_rates(df)
        
#         # ===== KPIs =====
#         kpi_total = f"{unique_students:,}"
#         kpi_total_change = f"{total_exams:,} exam attempts"
#         kpi_pass = f"{pass_rate:.1f}%"
#         kpi_distinction = f"{dist_rate:.1f}%"
#         kpi_fail = f"{fail_rate:.1f}%"
        
#         # Trends vs overall average
#         kpi_pass_trend = create_trend_indicator(pass_rate, overall_pass, "overall avg", inverse_colors=False)
#         kpi_dist_trend = create_trend_indicator(dist_rate, overall_dist, "overall avg", inverse_colors=False)
#         kpi_fail_trend = create_trend_indicator(fail_rate, overall_fail, "overall avg", inverse_colors=True)
        
#         # ===== CHARTS =====
#         yearly_data = get_yearly_data(filtered)
        
#         yoy_fig = create_yoy_trends_chart(yearly_data)
#         dept_fig = create_department_comparison_chart(filtered, dept)
#         dist_fig = create_distribution_chart(filtered)
        
#         # ===== DETAILED TABLE =====
#         detail_table = create_detailed_table(yearly_data)
        
#         # ===== ALERTS =====
#         alert_section = create_alerts(pass_rate, dist_rate, fail_rate)
        
#         # ===== RECOMMENDATIONS =====
#         recommendations_div = create_recommendations(
#             filtered, year_range, pass_rate, unique_students, total_exams
#         )
        
#         return (
#             kpi_total, kpi_total_change,
#             kpi_pass, kpi_pass_trend,
#             kpi_distinction, kpi_dist_trend,
#             kpi_fail, kpi_fail_trend,
#             alert_section,
#             yoy_fig, dept_fig, dist_fig,
#             detail_table, recommendations_div,
#             ""  # loading-output
#         )


# def create_detailed_table(yearly_data):
#     """
#     Create detailed performance table.
    
#     Args:
#         yearly_data (pl.DataFrame): Yearly aggregated data
        
#     Returns:
#         dbc.Table: Formatted table component
#     """
#     table_data = yearly_data.sort('exam_year', descending=True)
#     table_rows = []
    
#     for row in table_data.iter_rows(named=True):
#         pass_bg = '#d1fae5' if row['pass_rate'] >= 85 else (
#             '#fef3c7' if row['pass_rate'] >= 75 else '#fee2e2'
#         )
        
#         table_rows.append(html.Tr([
#             html.Td(str(int(row['exam_year'])), style={'fontWeight': 'bold'}),
#             html.Td(f"{int(row['unique_students']):,}", style={'textAlign': 'center'}),
#             html.Td(f"{int(row['total_exams']):,}", 
#                    style={'textAlign': 'center', 'color': '#6b7280'}),
#             html.Td(f"{row['pass_rate']:.1f}%", 
#                    style={'textAlign': 'center', 'backgroundColor': pass_bg, 
#                           'padding': '8px', 'borderRadius': '4px'}),
#             html.Td(f"{row['dist_rate']:.1f}%", style={'textAlign': 'center'}),
#             html.Td(f"{row['fail_rate']:.1f}%", style={'textAlign': 'center'}),
#         ]))
    
#     return dbc.Table([
#         html.Thead(html.Tr([
#             html.Th("Year"),
#             html.Th("Students", style={'textAlign': 'center'}),
#             html.Th("Exam Attempts", style={'textAlign': 'center'}),
#             html.Th("Pass Rate", style={'textAlign': 'center'}),
#             html.Th("Distinction", style={'textAlign': 'center'}),
#             html.Th("Failure", style={'textAlign': 'center'})
#         ])),
#         html.Tbody(table_rows)
#     ], bordered=True, hover=True, striped=True, responsive=True)


# def create_alerts(pass_rate, dist_rate, fail_rate):
#     """
#     Create alert components based on performance thresholds.
    
#     Args:
#         pass_rate (float): Pass rate percentage
#         dist_rate (float): Distinction rate percentage
#         fail_rate (float): Failure rate percentage
        
#     Returns:
#         html.Div: Alert section
#     """
#     alerts = []
    
#     if fail_rate > HIGH_FAILURE_THRESHOLD:
#         alerts.append(dbc.Alert([
#             html.Strong("⚠️ High Failure Rate: "),
#             f"Current failure rate is {fail_rate:.1f}%, requiring immediate attention"
#         ], color='danger'))
    
#     if dist_rate < LOW_DISTINCTION_THRESHOLD:
#         alerts.append(dbc.Alert([
#             html.Strong("📉 Low Distinction Rate: "),
#             f"Only {dist_rate:.1f}% achieving distinction - review grading standards"
#         ], color='warning'))
    
#     if pass_rate > EXCELLENT_PERFORMANCE_THRESHOLD:
#         alerts.append(dbc.Alert([
#             html.Strong("✅ Excellent Performance: "),
#             f"Pass rate of {pass_rate:.1f}% indicates strong outcomes"
#         ], color='success'))
    
#     return html.Div(alerts) if alerts else html.Div()


# def create_recommendations(filtered, year_range, pass_rate, unique_students, total_exams):
#     """
#     Create recommendations section based on data analysis.
    
#     Args:
#         filtered (pl.DataFrame): Filtered DataFrame
#         year_range (list): Selected year range
#         pass_rate (float): Overall pass rate
#         unique_students (int): Number of unique students
#         total_exams (int): Total exam attempts
        
#     Returns:
#         html.Div: Recommendations section
#     """
#     recommendations = []
    
#     if len(filtered) > 0:
#         dept_stats = get_department_stats(filtered)
        
#         # Critical departments
#         critical_depts = dept_stats.filter(
#             pl.col('pass_rate') < CRITICAL_PASS_RATE
#         ).head(CRITICAL_DEPARTMENTS_DISPLAY)
        
#         if len(critical_depts) > 0:
#             dept_items = []
#             for row in critical_depts.iter_rows(named=True):
#                 dept_items.append(
#                     html.Li(f"{row['offering_department']}: {row['pass_rate']:.1f}% "
#                            f"({int(row['students'])} students, {int(row['exams'])} exams)")
#                 )
            
#             recommendations.append(html.Div([
#                 html.H6("🔴 Critical Departments (Pass Rate < 60%)", 
#                        className="text-danger mb-2"),
#                 html.Ul(dept_items),
#                 html.P("Actions: Faculty intervention, curriculum review, student support programs",
#                       className="text-muted small")
#             ], className="mb-3"))
        
#         # High performing departments
#         high_performers = dept_stats.filter(
#             pl.col('pass_rate') >= HIGH_PERFORMANCE_PASS_RATE
#         ).sort('pass_rate', descending=True).head(HIGH_PERFORMERS_DISPLAY)
        
#         if len(high_performers) > 0:
#             perf_items = []
#             for row in high_performers.iter_rows(named=True):
#                 perf_items.append(
#                     html.Li(f"{row['offering_department']}: {row['pass_rate']:.1f}% "
#                            f"({int(row['students'])} students, {int(row['exams'])} exams)")
#                 )
            
#             recommendations.append(html.Div([
#                 html.H6("🟢 High Performing Departments (Pass Rate ≥ 85%)", 
#                        className="text-success mb-2"),
#                 html.Ul(perf_items),
#                 html.P("Document and share best practices across institution",
#                       className="text-muted small")
#             ], className="mb-3"))
    
#     # Year range insights
#     if year_range:
#         year_span = year_range[1] - year_range[0] + 1
#         avg_exams = total_exams / unique_students if unique_students > 0 else 0
        
#         recommendations.append(html.Div([
#             html.H6("📅 Selected Period Insights", className="text-info mb-2"),
#             html.P(f"Analyzing {year_span} year(s) from {year_range[0]} to {year_range[1]}", 
#                   className="mb-1"),
#             html.P(f"Unique students: {unique_students:,} | Exam attempts: {total_exams:,}", 
#                   className="mb-1"),
#             html.P(f"Average exams per student: {avg_exams:.1f}" if unique_students > 0 else "", 
#                   className="mb-1"),
#             html.P(f"Overall pass rate: {pass_rate:.1f}%", className="mb-0")
#         ], className="mb-3"))
    
#     if len(recommendations) == 0:
#         recommendations = [
#             html.P("✅ Performance metrics are within acceptable ranges. Continue monitoring trends.",
#                   className="text-muted")
#         ]
    
#     return html.Div(recommendations)











# # ==============================================================================
# # FILE: dashboard/callbacks.py (UPDATED)
# # ==============================================================================
# """
# Dashboard callbacks - handles all interactivity and data updates.
# """

# import dash_bootstrap_components as dbc
# from dash import html, Input, Output
# from data.processor import filter_data
# from utils.calculations import calculate_rates, get_yearly_data, get_department_stats
# from utils.visualizations import (
#     create_yoy_trends_chart,
#     create_department_comparison_chart,
#     create_distribution_chart
# )
# from .components import create_trend_indicator
# from config import (
#     HIGH_FAILURE_THRESHOLD,
#     LOW_DISTINCTION_THRESHOLD,
#     EXCELLENT_PERFORMANCE_THRESHOLD,
#     CRITICAL_PASS_RATE,
#     HIGH_PERFORMANCE_PASS_RATE,
#     CRITICAL_DEPARTMENTS_DISPLAY,
#     HIGH_PERFORMERS_DISPLAY
# )
# import polars as pl


# def register_callbacks(app, df):
#     """
#     Register all dashboard callbacks.
    
#     Args:
#         app: Dash app instance
#         df (pl.DataFrame): Main DataFrame
#     """
    
#     @app.callback(
#         [
#             Output('kpi-total', 'children'),
#             Output('kpi-total-change', 'children'),
#             Output('kpi-pass', 'children'),
#             Output('kpi-pass-trend', 'children'),
#             Output('kpi-distinction', 'children'),
#             Output('kpi-distinction-trend', 'children'),
#             Output('kpi-fail', 'children'),
#             Output('kpi-fail-trend', 'children'),
#             Output('alerts-section', 'children'),
#             Output('yoy-trends', 'figure'),
#             Output('dept-comparison', 'figure'),
#             Output('distribution-chart', 'figure'),
#             Output('detail-table', 'children'),
#             Output('recommendations', 'children'),
#             Output('loading-output', 'children'),
#         ],
#         [
#             Input('search-button', 'n_clicks'),
#             Input('year-range-slider', 'value'),
#             Input('department-filter', 'value'),
#             Input('semester-filter', 'value'),
#             Input('subject-filter', 'value'),
#         ]
#     )
#     def update_dashboard(n_clicks, year_range, dept, sem, subj):
#         """Main callback to update all dashboard components."""
        
#         # Filter data based on user selections
#         filtered = filter_data(df, year_range, dept, sem, subj)
        
#         # Calculate overall metrics for filtered data
#         pass_rate, dist_rate, fail_rate, unique_students, total_exams = calculate_rates(filtered)
        
#         # Calculate overall dataset average for comparison
#         overall_pass, overall_dist, overall_fail, overall_unique, overall_exams = calculate_rates(df)
        
#         # ===== KPIs =====
#         kpi_total = f"{unique_students:,}"
#         kpi_total_change = f"{total_exams:,} exam attempts"
#         kpi_pass = f"{pass_rate:.1f}%"
#         kpi_distinction = f"{dist_rate:.1f}%"
#         kpi_fail = f"{fail_rate:.1f}%"
        
#         # Trends vs overall average
#         # For pass and distinction: increase is good (green), decrease is bad (red)
#         kpi_pass_trend = create_trend_indicator(pass_rate, overall_pass, "overall avg", inverse_colors=False)
#         kpi_dist_trend = create_trend_indicator(dist_rate, overall_dist, "overall avg", inverse_colors=False)
#         # For fail rate: decrease is good (green), increase is bad (red)
#         kpi_fail_trend = create_trend_indicator(fail_rate, overall_fail, "overall avg", inverse_colors=True)
        
#         # ===== CHARTS =====
#         yearly_data = get_yearly_data(filtered)
        
#         yoy_fig = create_yoy_trends_chart(yearly_data)
#         dept_fig = create_department_comparison_chart(filtered, dept)
#         dist_fig = create_distribution_chart(filtered)
        
#         # ===== DETAILED TABLE =====
#         detail_table = create_detailed_table(yearly_data)
        
#         # ===== ALERTS =====
#         alert_section = create_alerts(pass_rate, dist_rate, fail_rate)
        
#         # ===== RECOMMENDATIONS =====
#         recommendations_div = create_recommendations(
#             filtered, year_range, pass_rate, unique_students, total_exams
#         )
        
#         return (
#             kpi_total, kpi_total_change,
#             kpi_pass, kpi_pass_trend,
#             kpi_distinction, kpi_dist_trend,
#             kpi_fail, kpi_fail_trend,
#             alert_section,
#             yoy_fig, dept_fig, dist_fig,
#             detail_table, recommendations_div,
#             ""  # loading-output
#         )


# def create_detailed_table(yearly_data):
#     """
#     Create detailed performance table.
    
#     Args:
#         yearly_data (pl.DataFrame): Yearly aggregated data
        
#     Returns:
#         dbc.Table: Formatted table component
#     """
#     table_data = yearly_data.sort('exam_year', descending=True)
#     table_rows = []
    
#     for row in table_data.iter_rows(named=True):
#         pass_bg = '#d1fae5' if row['pass_rate'] >= 85 else (
#             '#fef3c7' if row['pass_rate'] >= 75 else '#fee2e2'
#         )
        
#         table_rows.append(html.Tr([
#             html.Td(str(int(row['exam_year'])), style={'fontWeight': 'bold'}),
#             html.Td(f"{int(row['unique_students']):,}", style={'textAlign': 'center'}),
#             html.Td(f"{int(row['total_exams']):,}", 
#                    style={'textAlign': 'center', 'color': '#6b7280'}),
#             html.Td(f"{row['pass_rate']:.1f}%", 
#                    style={'textAlign': 'center', 'backgroundColor': pass_bg, 
#                           'padding': '8px', 'borderRadius': '4px'}),
#             html.Td(f"{row['dist_rate']:.1f}%", style={'textAlign': 'center'}),
#             html.Td(f"{row['fail_rate']:.1f}%", style={'textAlign': 'center'}),
#         ]))
    
#     return dbc.Table([
#         html.Thead(html.Tr([
#             html.Th("Year"),
#             html.Th("Students", style={'textAlign': 'center'}),
#             html.Th("Exam Attempts", style={'textAlign': 'center'}),
#             html.Th("Pass Rate", style={'textAlign': 'center'}),
#             html.Th("Distinction", style={'textAlign': 'center'}),
#             html.Th("Failure", style={'textAlign': 'center'})
#         ])),
#         html.Tbody(table_rows)
#     ], bordered=True, hover=True, striped=True, responsive=True)


# def create_alerts(pass_rate, dist_rate, fail_rate):
#     """
#     Create alert components based on performance thresholds.
    
#     Args:
#         pass_rate (float): Pass rate percentage
#         dist_rate (float): Distinction rate percentage
#         fail_rate (float): Failure rate percentage
        
#     Returns:
#         html.Div: Alert section
#     """
#     alerts = []
    
#     if fail_rate > HIGH_FAILURE_THRESHOLD:
#         alerts.append(dbc.Alert([
#             html.Strong("⚠️ High Failure Rate: "),
#             f"Current failure rate is {fail_rate:.1f}%, requiring immediate attention"
#         ], color='danger'))
    
#     if dist_rate < LOW_DISTINCTION_THRESHOLD:
#         alerts.append(dbc.Alert([
#             html.Strong("📉 Low Distinction Rate: "),
#             f"Only {dist_rate:.1f}% achieving distinction - review grading standards"
#         ], color='warning'))
    
#     if pass_rate > EXCELLENT_PERFORMANCE_THRESHOLD:
#         alerts.append(dbc.Alert([
#             html.Strong("✅ Excellent Performance: "),
#             f"Pass rate of {pass_rate:.1f}% indicates strong outcomes"
#         ], color='success'))
    
#     return html.Div(alerts) if alerts else html.Div()


# def create_recommendations(filtered, year_range, pass_rate, unique_students, total_exams):
#     """
#     Create recommendations section based on data analysis.
    
#     Args:
#         filtered (pl.DataFrame): Filtered DataFrame
#         year_range (list): Selected year range
#         pass_rate (float): Overall pass rate
#         unique_students (int): Number of unique students
#         total_exams (int): Total exam attempts
        
#     Returns:
#         html.Div: Recommendations section
#     """
#     recommendations = []
    
#     if len(filtered) > 0:
#         dept_stats = get_department_stats(filtered)
        
#         # Critical departments
#         critical_depts = dept_stats.filter(
#             pl.col('pass_rate') < CRITICAL_PASS_RATE
#         ).head(CRITICAL_DEPARTMENTS_DISPLAY)
        
#         if len(critical_depts) > 0:
#             dept_items = []
#             for row in critical_depts.iter_rows(named=True):
#                 dept_items.append(
#                     html.Li(f"{row['offering_department']}: {row['pass_rate']:.1f}% "
#                            f"({int(row['students'])} students, {int(row['exams'])} exams)")
#                 )
            
#             recommendations.append(html.Div([
#                 html.H6("🔴 Critical Departments (Pass Rate < 60%)", 
#                        className="text-danger mb-2"),
#                 html.Ul(dept_items),
#                 html.P("Actions: Faculty intervention, curriculum review, student support programs",
#                       className="text-muted small")
#             ], className="mb-3"))
        
#         # High performing departments
#         high_performers = dept_stats.filter(
#             pl.col('pass_rate') >= HIGH_PERFORMANCE_PASS_RATE
#         ).sort('pass_rate', descending=True).head(HIGH_PERFORMERS_DISPLAY)
        
#         if len(high_performers) > 0:
#             perf_items = []
#             for row in high_performers.iter_rows(named=True):
#                 perf_items.append(
#                     html.Li(f"{row['offering_department']}: {row['pass_rate']:.1f}% "
#                            f"({int(row['students'])} students, {int(row['exams'])} exams)")
#                 )
            
#             recommendations.append(html.Div([
#                 html.H6("🟢 High Performing Departments (Pass Rate ≥ 85%)", 
#                        className="text-success mb-2"),
#                 html.Ul(perf_items),
#                 html.P("Document and share best practices across institution",
#                       className="text-muted small")
#             ], className="mb-3"))
    
#     # Year range insights
#     if year_range:
#         year_span = year_range[1] - year_range[0] + 1
#         avg_exams = total_exams / unique_students if unique_students > 0 else 0
        
#         recommendations.append(html.Div([
#             html.H6("📅 Selected Period Insights", className="text-info mb-2"),
#             html.P(f"Analyzing {year_span} year(s) from {year_range[0]} to {year_range[1]}", 
#                   className="mb-1"),
#             html.P(f"Unique students: {unique_students:,} | Exam attempts: {total_exams:,}", 
#                   className="mb-1"),
#             html.P(f"Average exams per student: {avg_exams:.1f}" if unique_students > 0 else "", 
#                   className="mb-1"),
#             html.P(f"Overall pass rate: {pass_rate:.1f}%", className="mb-0")
#         ], className="mb-3"))
    
#     if len(recommendations) == 0:
#         recommendations = [
#             html.P("✅ Performance metrics are within acceptable ranges. Continue monitoring trends.",
#                   className="text-muted")
#         ]
    
#     return html.Div(recommendations)






# # ==============================================================================
# # FILE: dashboard/callbacks.py
# # ==============================================================================
# """
# Dashboard callbacks - handles all interactivity and data updates.
# """

# import dash_bootstrap_components as dbc
# from dash import html, Input, Output
# from data.processor import filter_data
# from utils.calculations import calculate_rates, get_yearly_data, get_department_stats
# from utils.visualizations import (
#     create_yoy_trends_chart,
#     create_department_comparison_chart,
#     create_distribution_chart
# )
# from .components import create_trend_indicator
# from config import (
#     HIGH_FAILURE_THRESHOLD,
#     LOW_DISTINCTION_THRESHOLD,
#     EXCELLENT_PERFORMANCE_THRESHOLD,
#     CRITICAL_PASS_RATE,
#     HIGH_PERFORMANCE_PASS_RATE,
#     CRITICAL_DEPARTMENTS_DISPLAY,
#     HIGH_PERFORMERS_DISPLAY
# )
# import polars as pl


# def register_callbacks(app, df):
#     """
#     Register all dashboard callbacks.
    
#     Args:
#         app: Dash app instance
#         df (pl.DataFrame): Main DataFrame
#     """
    
#     @app.callback(
#         [
#             Output('kpi-total', 'children'),
#             Output('kpi-total-change', 'children'),
#             Output('kpi-pass', 'children'),
#             Output('kpi-pass-trend', 'children'),
#             Output('kpi-distinction', 'children'),
#             Output('kpi-distinction-trend', 'children'),
#             Output('kpi-fail', 'children'),
#             Output('kpi-fail-trend', 'children'),
#             Output('alerts-section', 'children'),
#             Output('yoy-trends', 'figure'),
#             Output('dept-comparison', 'figure'),
#             Output('distribution-chart', 'figure'),
#             Output('detail-table', 'children'),
#             Output('recommendations', 'children'),
#             Output('loading-output', 'children'),
#         ],
#         [
#             Input('year-range-slider', 'value'),
#             Input('department-filter', 'value'),
#             Input('semester-filter', 'value'),
#             Input('subject-filter', 'value'),
#         ]
#     )
#     def update_dashboard(year_range, dept, sem, subj):
#         """Main callback to update all dashboard components."""
        
#         # Filter data based on user selections
#         filtered = filter_data(df, year_range, dept, sem, subj)
        
#         # Calculate overall metrics for filtered data
#         pass_rate, dist_rate, fail_rate, unique_students, total_exams = calculate_rates(filtered)
        
#         # Calculate overall dataset average for comparison
#         overall_pass, overall_dist, overall_fail, overall_unique, overall_exams = calculate_rates(df)
        
#         # ===== KPIs =====
#         kpi_total = f"{unique_students:,}"
#         kpi_total_change = f"{total_exams:,} exam attempts"
#         kpi_pass = f"{pass_rate:.1f}%"
#         kpi_distinction = f"{dist_rate:.1f}%"
#         kpi_fail = f"{fail_rate:.1f}%"
        
#         # Trends vs overall average
#         kpi_pass_trend = create_trend_indicator(pass_rate, overall_pass, "overall avg")
#         kpi_dist_trend = create_trend_indicator(dist_rate, overall_dist, "overall avg")
#         kpi_fail_trend = create_trend_indicator(fail_rate, overall_fail, "overall avg")
        
#         # ===== CHARTS =====
#         yearly_data = get_yearly_data(filtered)
        
#         yoy_fig = create_yoy_trends_chart(yearly_data)
#         dept_fig = create_department_comparison_chart(filtered, dept)
#         dist_fig = create_distribution_chart(filtered)
        
#         # ===== DETAILED TABLE =====
#         detail_table = create_detailed_table(yearly_data)
        
#         # ===== ALERTS =====
#         alert_section = create_alerts(pass_rate, dist_rate, fail_rate)
        
#         # ===== RECOMMENDATIONS =====
#         recommendations_div = create_recommendations(
#             filtered, year_range, pass_rate, unique_students, total_exams
#         )
        
#         return (
#             kpi_total, kpi_total_change,
#             kpi_pass, kpi_pass_trend,
#             kpi_distinction, kpi_dist_trend,
#             kpi_fail, kpi_fail_trend,
#             alert_section,
#             yoy_fig, dept_fig, dist_fig,
#             detail_table, recommendations_div,
#             ""  # loading-output
#         )


# def create_detailed_table(yearly_data):
#     """
#     Create detailed performance table.
    
#     Args:
#         yearly_data (pl.DataFrame): Yearly aggregated data
        
#     Returns:
#         dbc.Table: Formatted table component
#     """
#     table_data = yearly_data.sort('exam_year', descending=True)
#     table_rows = []
    
#     for row in table_data.iter_rows(named=True):
#         pass_bg = '#d1fae5' if row['pass_rate'] >= 85 else (
#             '#fef3c7' if row['pass_rate'] >= 75 else '#fee2e2'
#         )
        
#         table_rows.append(html.Tr([
#             html.Td(str(int(row['exam_year'])), style={'fontWeight': 'bold'}),
#             html.Td(f"{int(row['unique_students']):,}", style={'textAlign': 'center'}),
#             html.Td(f"{int(row['total_exams']):,}", 
#                    style={'textAlign': 'center', 'color': '#6b7280'}),
#             html.Td(f"{row['pass_rate']:.1f}%", 
#                    style={'textAlign': 'center', 'backgroundColor': pass_bg, 
#                           'padding': '8px', 'borderRadius': '4px'}),
#             html.Td(f"{row['dist_rate']:.1f}%", style={'textAlign': 'center'}),
#             html.Td(f"{row['fail_rate']:.1f}%", style={'textAlign': 'center'}),
#         ]))
    
#     return dbc.Table([
#         html.Thead(html.Tr([
#             html.Th("Year"),
#             html.Th("Students", style={'textAlign': 'center'}),
#             html.Th("Exam Attempts", style={'textAlign': 'center'}),
#             html.Th("Pass Rate", style={'textAlign': 'center'}),
#             html.Th("Distinction", style={'textAlign': 'center'}),
#             html.Th("Failure", style={'textAlign': 'center'})
#         ])),
#         html.Tbody(table_rows)
#     ], bordered=True, hover=True, striped=True, responsive=True)


# def create_alerts(pass_rate, dist_rate, fail_rate):
#     """
#     Create alert components based on performance thresholds.
    
#     Args:
#         pass_rate (float): Pass rate percentage
#         dist_rate (float): Distinction rate percentage
#         fail_rate (float): Failure rate percentage
        
#     Returns:
#         html.Div: Alert section
#     """
#     alerts = []
    
#     if fail_rate > HIGH_FAILURE_THRESHOLD:
#         alerts.append(dbc.Alert([
#             html.Strong("⚠️ High Failure Rate: "),
#             f"Current failure rate is {fail_rate:.1f}%, requiring immediate attention"
#         ], color='danger'))
    
#     if dist_rate < LOW_DISTINCTION_THRESHOLD:
#         alerts.append(dbc.Alert([
#             html.Strong("📉 Low Distinction Rate: "),
#             f"Only {dist_rate:.1f}% achieving distinction - review grading standards"
#         ], color='warning'))
    
#     if pass_rate > EXCELLENT_PERFORMANCE_THRESHOLD:
#         alerts.append(dbc.Alert([
#             html.Strong("✅ Excellent Performance: "),
#             f"Pass rate of {pass_rate:.1f}% indicates strong outcomes"
#         ], color='success'))
    
#     return html.Div(alerts) if alerts else html.Div()


# def create_recommendations(filtered, year_range, pass_rate, unique_students, total_exams):
#     """
#     Create recommendations section based on data analysis.
    
#     Args:
#         filtered (pl.DataFrame): Filtered DataFrame
#         year_range (list): Selected year range
#         pass_rate (float): Overall pass rate
#         unique_students (int): Number of unique students
#         total_exams (int): Total exam attempts
        
#     Returns:
#         html.Div: Recommendations section
#     """
#     recommendations = []
    
#     if len(filtered) > 0:
#         dept_stats = get_department_stats(filtered)
        
#         # Critical departments
#         critical_depts = dept_stats.filter(
#             pl.col('pass_rate') < CRITICAL_PASS_RATE
#         ).head(CRITICAL_DEPARTMENTS_DISPLAY)
        
#         if len(critical_depts) > 0:
#             dept_items = []
#             for row in critical_depts.iter_rows(named=True):
#                 dept_items.append(
#                     html.Li(f"{row['offering_department']}: {row['pass_rate']:.1f}% "
#                            f"({int(row['students'])} students, {int(row['exams'])} exams)")
#                 )
            
#             recommendations.append(html.Div([
#                 html.H6("🔴 Critical Departments (Pass Rate < 60%)", 
#                        className="text-danger mb-2"),
#                 html.Ul(dept_items),
#                 html.P("Actions: Faculty intervention, curriculum review, student support programs",
#                       className="text-muted small")
#             ], className="mb-3"))
        
#         # High performing departments
#         high_performers = dept_stats.filter(
#             pl.col('pass_rate') >= HIGH_PERFORMANCE_PASS_RATE
#         ).sort('pass_rate', descending=True).head(HIGH_PERFORMERS_DISPLAY)
        
#         if len(high_performers) > 0:
#             perf_items = []
#             for row in high_performers.iter_rows(named=True):
#                 perf_items.append(
#                     html.Li(f"{row['offering_department']}: {row['pass_rate']:.1f}% "
#                            f"({int(row['students'])} students, {int(row['exams'])} exams)")
#                 )
            
#             recommendations.append(html.Div([
#                 html.H6("🟢 High Performing Departments (Pass Rate ≥ 85%)", 
#                        className="text-success mb-2"),
#                 html.Ul(perf_items),
#                 html.P("Document and share best practices across institution",
#                       className="text-muted small")
#             ], className="mb-3"))
    
#     # Year range insights
#     if year_range:
#         year_span = year_range[1] - year_range[0] + 1
#         avg_exams = total_exams / unique_students if unique_students > 0 else 0
        
#         recommendations.append(html.Div([
#             html.H6("📅 Selected Period Insights", className="text-info mb-2"),
#             html.P(f"Analyzing {year_span} year(s) from {year_range[0]} to {year_range[1]}", 
#                   className="mb-1"),
#             html.P(f"Unique students: {unique_students:,} | Exam attempts: {total_exams:,}", 
#                   className="mb-1"),
#             html.P(f"Average exams per student: {avg_exams:.1f}" if unique_students > 0 else "", 
#                   className="mb-1"),
#             html.P(f"Overall pass rate: {pass_rate:.1f}%", className="mb-0")
#         ], className="mb-3"))
    
#     if len(recommendations) == 0:
#         recommendations = [
#             html.P("✅ Performance metrics are within acceptable ranges. Continue monitoring trends.",
#                   className="text-muted")
#         ]
    
#     return html.Div(recommendations)
