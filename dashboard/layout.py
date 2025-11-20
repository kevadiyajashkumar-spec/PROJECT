# ==============================================================================
# FILE: dashboard/layout.py (FIXED VERSION)
# ==============================================================================
"""
Dashboard layout definition.
FIXES: Added overflow: visible to main container and rows
"""

import dash_bootstrap_components as dbc
from dash import dcc, html
from config import COLORS
from .components import (
    create_filter_card,
    create_kpi_card,
    create_chart_card
)


def create_layout(filter_options):
    """
    Create the complete dashboard layout.
    
    Args:
        filter_options (dict): Filter dropdown options
        
    Returns:
        dbc.Container: Complete dashboard layout
    """
    return dbc.Container([
        # Loading overlay
        dcc.Loading(
            id="loading-main",
            type="default",
            fullscreen=True,
            children=html.Div(id="loading-output")
        ),
        
        # Header
        dbc.Row(
            dbc.Col([
                html.H1("🎓 Pass Rate & Distinction Trend Analysis", 
                       className="text-center my-4"),
                html.P("Comprehensive year-over-year performance tracking across departments, programs, and courses",
                       className="text-center text-muted mb-4")
            ], width=12),
            style={'position': 'relative', 'zIndex': 1}
        ),
        
        # Filters - HIGHEST Z-INDEX
        html.Div(
            create_filter_card(filter_options),
            style={'position': 'relative', 'zIndex': 100, 'overflow': 'visible'}
        ),
        
        # KPI Cards - LOWER Z-INDEX
        dcc.Loading(
            type="circle",
            children=[
                dbc.Row([
                    create_kpi_card("Unique Students", "kpi-total"),
                    create_kpi_card("Pass Rate", "kpi-pass", "kpi-pass-trend", 
                                  "text-success", "#10b981"),
                    create_kpi_card("Distinction Rate", "kpi-distinction", "kpi-distinction-trend",
                                  "text-warning", "#f59e0b"),
                    create_kpi_card("Failure Rate", "kpi-fail", "kpi-fail-trend",
                                  "text-danger", "#ef4444"),
                ], className="mb-4", style={'position': 'relative', 'zIndex': 1}),
            ]
        ),

        # Assessment KPI Cards
        dcc.Loading(
            type="circle",
            children=[
                dbc.Row([
                    create_kpi_card("Avg CIA (Theory)", "kpi-cia-theory", "kpi-cia-theory-trend",
                                    border_color="#2563eb"),
                    create_kpi_card("Avg ESE (Theory)", "kpi-ese-theory", "kpi-ese-theory-trend",
                                    border_color="#0ea5e9"),
                    create_kpi_card("Avg CIA (Practical)", "kpi-cia-practical", "kpi-cia-practical-trend",
                                    border_color="#f97316"),
                ], className="mb-4", style={'position': 'relative', 'zIndex': 1}),
            ]
        ),
        
        # Alerts
        dbc.Row(
            dbc.Col(html.Div(id='alerts-section'), width=12), 
            className="mb-3",
            style={'position': 'relative', 'zIndex': 1}
        ),
        
        # Year-over-Year Trends Chart
        dcc.Loading(
            type="default",
            children=[
                dbc.Row([
                    dbc.Col(create_chart_card(
                        "Year-over-Year Trends", 
                        "yoy-trends"
                    ), md=12)
                ], className="mb-4", style={'position': 'relative', 'zIndex': 1}),
            ]
        ),
        
        # Department Comparison Chart
        dcc.Loading(
            type="default",
            children=[
                dbc.Row([
                    dbc.Col(create_chart_card(
                        "Department Performance Comparison",
                        "dept-comparison",
                        "🏢"
                    ), md=12)
                ], className="mb-4", style={'position': 'relative', 'zIndex': 1}),
            ]
        ),
        
        # Distribution Chart
        dcc.Loading(
            type="default",
            children=[
                dbc.Row([
                    dbc.Col(create_chart_card(
                        "Performance Distribution by Year",
                        "distribution-chart",
                        "📊"
                    ), md=12)
                ], className="mb-4", style={'position': 'relative', 'zIndex': 1}),
            ]
        ),

        # Subject Difficulty & Department Leaderboard
        dcc.Loading(
            type="default",
            children=[
                dbc.Row([
                    dbc.Col(create_chart_card(
                        "Subject Difficulty Spotlight",
                        "subject-difficulty-chart",
                        "🧠"
                    ), md=6),
                    dbc.Col(create_chart_card(
                        "Department Leaderboard",
                        "dept-leaderboard-chart",
                        "🏅"
                    ), md=6)
                ], className="mb-4", style={'position': 'relative', 'zIndex': 1}),
            ]
        ),
        
        # Assessment Trend Chart
        dcc.Loading(
            type="default",
            children=[
                dbc.Row([
                    dbc.Col(create_chart_card(
                        "CIA vs ESE Trend",
                        "assessment-trend",
                        "📈"
                    ), md=12)
                ], className="mb-4", style={'position': 'relative', 'zIndex': 1}),
            ]
        ),

        # (Removed) Assessment Gap by Department chart

        # Detailed Table
        dcc.Loading(
            type="default",
            children=[
                dbc.Row([
                    dbc.Col(dbc.Card([
                        dbc.CardBody([
                            html.H5("📋 Detailed Performance Table", className="mb-3"),
                            html.Div(id='detail-table')
                        ])
                    ], className="shadow-sm"), md=12)
                ], className="mb-4", style={'position': 'relative', 'zIndex': 1}),
            ]
        ),
        
        # Insights & Recommendations
        dcc.Loading(
            type="default",
            children=[
                dbc.Row([
                    dbc.Col(dbc.Card([
                        dbc.CardBody([
                            html.H5("💡 Insights & Recommendations", className="mb-3"),
                            html.Div(id='recommendations')
                        ])
                    ], className="shadow-sm bg-light"), md=12)
                ], className="mb-4", style={'position': 'relative', 'zIndex': 1}),
            ]
        ),
        
    ], fluid=True, style={
        'backgroundColor': COLORS['background'],
        'paddingBottom': '40px',
        'overflow': 'visible',
        'position': 'relative'
    })











# # ==============================================================================
# # FILE: dashboard/layout.py
# # ==============================================================================
# """
# Dashboard layout definition.
# Creates the complete UI structure.
# """

# import dash_bootstrap_components as dbc
# from dash import dcc, html
# from .components import (
#     create_filter_card, 
#     create_kpi_card, 
#     create_chart_card
# )


# def create_layout(filter_options):
#     """
#     Create the complete dashboard layout.
    
#     Args:
#         filter_options (dict): Filter dropdown options
        
#     Returns:
#         dbc.Container: Complete dashboard layout
#     """
#     return dbc.Container([
#         # Loading overlay
#         dcc.Loading(
#             id="loading-main",
#             type="default",
#             fullscreen=True,
#             children=html.Div(id="loading-output")
#         ),
        
#         # Header
#         dbc.Row(dbc.Col([
#             html.H1("🎓 Pass Rate & Distinction Trend Analysis", 
#                    className="text-center my-4"),
#             html.P("Comprehensive year-over-year performance tracking across departments, programs, and courses",
#                    className="text-center text-muted mb-4")
#         ], width=12)),
        
#         # Filters
#         create_filter_card(filter_options),
        
#         # KPI Cards
#         dcc.Loading(
#             type="circle",
#             children=[
#                 dbc.Row([
#                     create_kpi_card("Unique Students", "kpi-total"),
#                     create_kpi_card("Pass Rate", "kpi-pass", "kpi-pass-trend", 
#                                   "text-success", "#10b981"),
#                     create_kpi_card("Distinction Rate", "kpi-distinction", "kpi-distinction-trend",
#                                   "text-warning", "#f59e0b"),
#                     create_kpi_card("Failure Rate", "kpi-fail", "kpi-fail-trend",
#                                   "text-danger", "#ef4444"),
#                 ], className="mb-4"),
#             ]
#         ),
        
#         # Alerts
#         dbc.Row(dbc.Col(html.Div(id='alerts-section'), width=12), className="mb-3"),
        
#         # Year-over-Year Trends Chart
#         dcc.Loading(
#             type="default",
#             children=[
#                 dbc.Row([
#                     dbc.Col(create_chart_card(
#                         "Year-over-Year Trends", 
#                         "yoy-trends"
#                     ), md=12)
#                 ], className="mb-4"),
#             ]
#         ),
        
#         # Department Comparison Chart
#         dcc.Loading(
#             type="default",
#             children=[
#                 dbc.Row([
#                     dbc.Col(create_chart_card(
#                         "Department Performance Comparison",
#                         "dept-comparison",
#                         "🏢"
#                     ), md=12)
#                 ], className="mb-4"),
#             ]
#         ),
        
#         # Distribution Chart
#         dcc.Loading(
#             type="default",
#             children=[
#                 dbc.Row([
#                     dbc.Col(create_chart_card(
#                         "Performance Distribution by Year",
#                         "distribution-chart",
#                         "📊"
#                     ), md=12)
#                 ], className="mb-4"),
#             ]
#         ),
        
#         # Detailed Table
#         dcc.Loading(
#             type="default",
#             children=[
#                 dbc.Row([
#                     dbc.Col(dbc.Card([
#                         dbc.CardBody([
#                             html.H5("📋 Detailed Performance Table", className="mb-3"),
#                             html.Div(id='detail-table')
#                         ])
#                     ], className="shadow-sm"), md=12)
#                 ], className="mb-4"),
#             ]
#         ),
        
#         # Insights & Recommendations
#         dcc.Loading(
#             type="default",
#             children=[
#                 dbc.Row([
#                     dbc.Col(dbc.Card([
#                         dbc.CardBody([
#                             html.H5("💡 Insights & Recommendations", className="mb-3"),
#                             html.Div(id='recommendations')
#                         ])
#                     ], className="shadow-sm bg-light"), md=12)
#                 ], className="mb-4"),
#             ]
#         ),
        
#     ], fluid=True, style={'backgroundColor': '#f8fafc', 'paddingBottom': '40px'})

