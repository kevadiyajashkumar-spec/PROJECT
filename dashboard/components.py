# ==============================================================================
# FILE: dashboard/components.py (ENHANCED FIX)
# ==============================================================================
"""
Reusable UI components for the dashboard.
FIXES:
1. Enhanced z-index styling to dropdowns so they appear above KPI cards
2. Added overflow visible to all parent containers
"""

import dash_bootstrap_components as dbc
from dash import dcc, html
from config import COLORS


def create_filter_card(filter_options):
    """
    Create filter card with all dropdown filters and a search button.
    FIXED: Enhanced z-index and overflow handling for dropdowns.
    
    Args:
        filter_options (dict): Dictionary with filter options
        
    Returns:
        dbc.Card: Filter card component
    """
    return dbc.Card([
        dbc.CardBody([
            dbc.Row([
                dbc.Col([
                    html.Label("Department", className="fw-bold"),
                    dcc.Dropdown(
                        id='department-filter',
                        options=[{'label': d, 'value': d} for d in filter_options['departments']],
                        value='All',
                        clearable=False,
                        optionHeight=40,
                        maxHeight=300,
                        style={
                            'zIndex': 9999
                        }
                    )
                ], md=4, style={'position': 'relative', 'zIndex': 9999, 'overflow': 'visible'}),
                dbc.Col([
                    html.Label("Semester", className="fw-bold"),
                    dcc.Dropdown(
                        id='semester-filter',
                        options=[{'label': ('All Semesters' if s == 'All' else f'Sem {s}'), 
                                'value': s} for s in filter_options['semesters']],
                        value='All',
                        clearable=False,
                        optionHeight=40,
                        maxHeight=300,
                        style={
                            'zIndex': 9998
                        }
                    )
                ], md=4, style={'position': 'relative', 'zIndex': 9998, 'overflow': 'visible'}),
                dbc.Col([
                    html.Label("Subject/Course", className="fw-bold"),
                    dcc.Dropdown(
                        id='subject-filter',
                        options=[{'label': s, 'value': s} for s in filter_options['subjects']],
                        value='All',
                        clearable=False,
                        optionHeight=40,
                        maxHeight=300,
                        style={
                            'zIndex': 9997
                        }
                    )
                ], md=4, style={'position': 'relative', 'zIndex': 9997, 'overflow': 'visible'}),
            ], style={'overflow': 'visible'}),
            dbc.Row([
                dbc.Col([
                    html.Label("Year Range", className="fw-bold mt-3"),
                    dcc.RangeSlider(
                        id='year-range-slider',
                        min=min(filter_options['years'][1:]),
                        max=max(filter_options['years'][1:]),
                        value=[min(filter_options['years'][1:]), max(filter_options['years'][1:])],
                        marks={int(year): str(int(year)) for year in filter_options['years'][1:]},
                        step=1,
                        tooltip={"placement": "bottom", "always_visible": True}
                    )
                ], md=10),
                dbc.Col([
                    html.Label("\u00A0", className="fw-bold mt-3"),
                    dbc.Button(
                        "🔍 Search",
                        id='search-button',
                        color="primary",
                        className="w-100",
                        size="lg",
                        style={'marginTop': '8px'}
                    )
                ], md=2, className="d-flex align-items-end")
            ], style={'overflow': 'visible'})
        ], style={'overflow': 'visible'})
    ], className="mb-4 shadow-sm", style={
        'position': 'relative', 
        'zIndex': 100,
        'overflow': 'visible',
        'backgroundColor': COLORS['card'],
        'border': 'none',
        'borderRadius': '16px'
    })


def create_kpi_card(title, value_id, trend_id=None, color=None, border_color=None):
    """
    Create KPI card component.
    FIXED: Set lower z-index to appear below dropdowns.
    
    Args:
        title (str): Card title
        value_id (str): ID for value display
        trend_id (str): ID for trend indicator
        color (str): Text color class
        border_color (str): Left border color
        
    Returns:
        dbc.Col: Column containing KPI card
    """
    card_style = {
        'position': 'relative', 
        'zIndex': 1,
        'overflow': 'visible'
    }
    if border_color:
        card_style['borderLeft'] = f'4px solid {border_color}'
    
    card_body = [
        html.H6(title, className="text-muted"),
        html.H2(id=value_id, className=f"mb-0 {color}" if color else "mb-0"),
    ]
    
    if trend_id:
        card_body.append(html.Div(id=trend_id))
    else:
        card_body.append(html.Small(id=f'{value_id}-change', className="text-muted"))
    
    return dbc.Col(
        dbc.Card([
            dbc.CardBody(card_body)
        ], className="shadow-sm", style={**card_style, 'backgroundColor': COLORS['card'], 'border': 'none', 'borderRadius': '16px'}),
        md=3,
        style={'position': 'relative', 'zIndex': 1}
    )


def create_chart_card(title, chart_id, icon="📈"):
    """
    Create chart card component.
    
    Args:
        title (str): Card title
        chart_id (str): ID for chart
        icon (str): Title icon
        
    Returns:
        dbc.Card: Chart card component
    """
    return dbc.Card([
        dbc.CardBody([
            html.H5(f"{icon} {title}", className="mb-3"),
            dcc.Graph(id=chart_id, config={'displayModeBar': False})
        ])
    ], className="shadow-sm", style={
        'position': 'relative',
        'zIndex': 1,
        'backgroundColor': COLORS['card'],
        'border': 'none',
        'borderRadius': '16px'
    })


def create_trend_indicator(current, previous, label="average", inverse_colors=False, unit="%"):
    """
    Create HTML trend indicator with descriptive label.
    
    Args:
        current (float): Current value
        previous (float): Previous/comparison value
        label (str): Description label
        inverse_colors (bool): If True, decreasing is good (green), increasing is bad (red)
        unit (str): Suffix to display after the change (default '%')
        
    Returns:
        html.Span: Trend indicator component
    """
    if current is None or previous is None:
        return html.Span("→ N/A", style={'color': '#6b7280', 'fontSize': '0.875rem'})

    if previous == 0:
        return html.Span("→ N/A", style={'color': '#6b7280', 'fontSize': '0.875rem'})
    
    change = current - previous
    suffix = unit or ""
    
    # Determine colors based on inverse_colors flag
    if inverse_colors:
        good_color = '#10b981'  # green
        bad_color = '#ef4444'   # red
    else:
        good_color = '#10b981'  # green
        bad_color = '#ef4444'   # red
    
    if abs(change) < 0.5:
        return html.Span(
            f"→ {change:+.1f}{suffix} from {label}",
            style={'color': '#6b7280', 'fontSize': '0.875rem'}
        )
    elif change > 0:
        color = bad_color if inverse_colors else good_color
        return html.Span(
            f"↑ {change:+.1f}{suffix} from {label}",
            style={'color': color, 'fontWeight': 'bold', 'fontSize': '0.875rem'}
        )
    else:
        color = good_color if inverse_colors else bad_color
        return html.Span(
            f"↓ {change:+.1f}{suffix} from {label}",
            style={'color': color, 'fontWeight': 'bold', 'fontSize': '0.875rem'}
        )













# # ==============================================================================
# # FILE: dashboard/components.py (FIXED VERSION)
# # ==============================================================================
# """
# Reusable UI components for the dashboard.
# FIXES:
# 1. Added z-index styling to dropdowns so they appear above KPI cards
# """

# import dash_bootstrap_components as dbc
# from dash import dcc, html
# from config import COLORS


# def create_filter_card(filter_options):
#     """
#     Create filter card with all dropdown filters and a search button.
#     FIXED: Added z-index to dropdown containers to appear above cards.
    
#     Args:
#         filter_options (dict): Dictionary with filter options
        
#     Returns:
#         dbc.Card: Filter card component
#     """
#     # Style for dropdown containers to ensure they appear on top
#     dropdown_container_style = {
#         'position': 'relative',
#         'zIndex': 1000
#     }
    
#     return dbc.Card([
#         dbc.CardBody([
#             dbc.Row([
#                 dbc.Col([
#                     html.Label("Department", className="fw-bold"),
#                     html.Div(
#                         dcc.Dropdown(
#                             id='department-filter',
#                             options=[{'label': d, 'value': d} for d in filter_options['departments']],
#                             value='All',
#                             clearable=False,
#                             style={'position': 'relative', 'zIndex': 1003}
#                         ),
#                         style=dropdown_container_style
#                     )
#                 ], md=4),
#                 dbc.Col([
#                     html.Label("Semester", className="fw-bold"),
#                     html.Div(
#                         dcc.Dropdown(
#                             id='semester-filter',
#                             options=[{'label': ('All Semesters' if s == 'All' else f'Sem {s}'), 
#                                     'value': s} for s in filter_options['semesters']],
#                             value='All',
#                             clearable=False,
#                             style={'position': 'relative', 'zIndex': 1002}
#                         ),
#                         style=dropdown_container_style
#                     )
#                 ], md=4),
#                 dbc.Col([
#                     html.Label("Subject/Course", className="fw-bold"),
#                     html.Div(
#                         dcc.Dropdown(
#                             id='subject-filter',
#                             options=[{'label': s, 'value': s} for s in filter_options['subjects']],
#                             value='All',
#                             clearable=False,
#                             style={'position': 'relative', 'zIndex': 1001}
#                         ),
#                         style=dropdown_container_style
#                     )
#                 ], md=4),
#             ]),
#             dbc.Row([
#                 dbc.Col([
#                     html.Label("Year Range", className="fw-bold mt-3"),
#                     dcc.RangeSlider(
#                         id='year-range-slider',
#                         min=min(filter_options['years'][1:]),
#                         max=max(filter_options['years'][1:]),
#                         value=[min(filter_options['years'][1:]), max(filter_options['years'][1:])],
#                         marks={int(year): str(int(year)) for year in filter_options['years'][1:]},
#                         step=1,
#                         tooltip={"placement": "bottom", "always_visible": True}
#                     )
#                 ], md=10),
#                 dbc.Col([
#                     html.Label("\u00A0", className="fw-bold mt-3"),
#                     dbc.Button(
#                         "🔍 Search",
#                         id='search-button',
#                         color="primary",
#                         className="w-100",
#                         size="lg",
#                         style={'marginTop': '8px'}
#                     )
#                 ], md=2, className="d-flex align-items-end")
#             ])
#         ])
#     ], className="mb-4 shadow-sm", style={'position': 'relative', 'zIndex': 999})


# def create_kpi_card(title, value_id, trend_id=None, color=None, border_color=None):
#     """
#     Create KPI card component.
#     FIXED: Reduced z-index to appear below dropdowns.
    
#     Args:
#         title (str): Card title
#         value_id (str): ID for value display
#         trend_id (str): ID for trend indicator
#         color (str): Text color class
#         border_color (str): Left border color
        
#     Returns:
#         dbc.Col: Column containing KPI card
#     """
#     card_style = {'position': 'relative', 'zIndex': 1}
#     if border_color:
#         card_style['borderLeft'] = f'4px solid {border_color}'
    
#     card_body = [
#         html.H6(title, className="text-muted"),
#         html.H2(id=value_id, className=f"mb-0 {color}" if color else "mb-0"),
#     ]
    
#     if trend_id:
#         card_body.append(html.Div(id=trend_id))
#     else:
#         card_body.append(html.Small(id=f'{value_id}-change', className="text-muted"))
    
#     return dbc.Col(
#         dbc.Card([
#             dbc.CardBody(card_body)
#         ], className="shadow-sm", style=card_style),
#         md=3
#     )


# def create_chart_card(title, chart_id, icon="📈"):
#     """
#     Create chart card component.
    
#     Args:
#         title (str): Card title
#         chart_id (str): ID for chart
#         icon (str): Title icon
        
#     Returns:
#         dbc.Card: Chart card component
#     """
#     return dbc.Card([
#         dbc.CardBody([
#             html.H5(f"{icon} {title}", className="mb-3"),
#             dcc.Graph(id=chart_id, config={'displayModeBar': False})
#         ])
#     ], className="shadow-sm", style={'position': 'relative', 'zIndex': 1})


# def create_trend_indicator(current, previous, label="average", inverse_colors=False):
#     """
#     Create HTML trend indicator with descriptive label.
    
#     Args:
#         current (float): Current value
#         previous (float): Previous/comparison value
#         label (str): Description label
#         inverse_colors (bool): If True, decreasing is good (green), increasing is bad (red)
        
#     Returns:
#         html.Span: Trend indicator component
#     """
#     if previous == 0:
#         return html.Span("→ N/A", style={'color': '#6b7280', 'fontSize': '0.875rem'})
    
#     change = current - previous
    
#     # Determine colors based on inverse_colors flag
#     if inverse_colors:
#         good_color = '#10b981'  # green
#         bad_color = '#ef4444'   # red
#     else:
#         good_color = '#10b981'  # green
#         bad_color = '#ef4444'   # red
    
#     if abs(change) < 0.5:
#         return html.Span(
#             f"→ {change:+.1f}% from {label}",
#             style={'color': '#6b7280', 'fontSize': '0.875rem'}
#         )
#     elif change > 0:
#         color = bad_color if inverse_colors else good_color
#         return html.Span(
#             f"↑ {change:+.1f}% from {label}",
#             style={'color': color, 'fontWeight': 'bold', 'fontSize': '0.875rem'}
#         )
#     else:
#         color = good_color if inverse_colors else bad_color
#         return html.Span(
#             f"↓ {change:+.1f}% from {label}",
#             style={'color': color, 'fontWeight': 'bold', 'fontSize': '0.875rem'}
#         )






# # ==============================================================================
# # FILE: dashboard/components.py (UPDATED)
# # ==============================================================================
# """
# Reusable UI components for the dashboard.
# Cards, filters, and other UI elements.
# """

# import dash_bootstrap_components as dbc
# from dash import dcc, html
# from config import COLORS


# def create_filter_card(filter_options):
#     """
#     Create filter card with all dropdown filters and a search button.
    
#     Args:
#         filter_options (dict): Dictionary with filter options
        
#     Returns:
#         dbc.Card: Filter card component
#     """
#     return dbc.Card([
#         dbc.CardBody([
#             dbc.Row([
#                 dbc.Col([
#                     html.Label("Department", className="fw-bold"),
#                     dcc.Dropdown(
#                         id='department-filter',
#                         options=[{'label': d, 'value': d} for d in filter_options['departments']],
#                         value='All',
#                         clearable=False
#                     )
#                 ], md=4),
#                 dbc.Col([
#                     html.Label("Semester", className="fw-bold"),
#                     dcc.Dropdown(
#                         id='semester-filter',
#                         options=[{'label': ('All Semesters' if s == 'All' else f'Sem {s}'), 
#                                 'value': s} for s in filter_options['semesters']],
#                         value='All',
#                         clearable=False
#                     )
#                 ], md=4),
#                 dbc.Col([
#                     html.Label("Subject/Course", className="fw-bold"),
#                     dcc.Dropdown(
#                         id='subject-filter',
#                         options=[{'label': s, 'value': s} for s in filter_options['subjects']],
#                         value='All',
#                         clearable=False
#                     )
#                 ], md=4),
#             ]),
#             dbc.Row([
#                 dbc.Col([
#                     html.Label("Year Range", className="fw-bold mt-3"),
#                     dcc.RangeSlider(
#                         id='year-range-slider',
#                         min=min(filter_options['years'][1:]),
#                         max=max(filter_options['years'][1:]),
#                         value=[min(filter_options['years'][1:]), max(filter_options['years'][1:])],
#                         marks={int(year): str(int(year)) for year in filter_options['years'][1:]},
#                         step=1,
#                         tooltip={"placement": "bottom", "always_visible": True}
#                     )
#                 ], md=10),
#                 dbc.Col([
#                     html.Label("\u00A0", className="fw-bold mt-3"),  # Spacer
#                     dbc.Button(
#                         "🔍 Search",
#                         id='search-button',
#                         color="primary",
#                         className="w-100",
#                         size="lg",
#                         style={'marginTop': '8px'}
#                     )
#                 ], md=2, className="d-flex align-items-end")
#             ])
#         ])
#     ], className="mb-4 shadow-sm")


# def create_kpi_card(title, value_id, trend_id=None, color=None, border_color=None):
#     """
#     Create KPI card component.
    
#     Args:
#         title (str): Card title
#         value_id (str): ID for value display
#         trend_id (str): ID for trend indicator
#         color (str): Text color class
#         border_color (str): Left border color
        
#     Returns:
#         dbc.Col: Column containing KPI card
#     """
#     card_style = {}
#     if border_color:
#         card_style['borderLeft'] = f'4px solid {border_color}'
    
#     card_body = [
#         html.H6(title, className="text-muted"),
#         html.H2(id=value_id, className=f"mb-0 {color}" if color else "mb-0"),
#     ]
    
#     if trend_id:
#         card_body.append(html.Div(id=trend_id))
#     else:
#         card_body.append(html.Small(id=f'{value_id}-change', className="text-muted"))
    
#     return dbc.Col(
#         dbc.Card([
#             dbc.CardBody(card_body)
#         ], className="shadow-sm", style=card_style),
#         md=3
#     )


# def create_chart_card(title, chart_id, icon="📈"):
#     """
#     Create chart card component.
    
#     Args:
#         title (str): Card title
#         chart_id (str): ID for chart
#         icon (str): Title icon
        
#     Returns:
#         dbc.Card: Chart card component
#     """
#     return dbc.Card([
#         dbc.CardBody([
#             html.H5(f"{icon} {title}", className="mb-3"),
#             dcc.Graph(id=chart_id, config={'displayModeBar': False})
#         ])
#     ], className="shadow-sm")


# def create_trend_indicator(current, previous, label="average", inverse_colors=False):
#     """
#     Create HTML trend indicator with descriptive label.
    
#     Args:
#         current (float): Current value
#         previous (float): Previous/comparison value
#         label (str): Description label
#         inverse_colors (bool): If True, decreasing is good (green), increasing is bad (red)
        
#     Returns:
#         html.Span: Trend indicator component
#     """
#     if previous == 0:
#         return html.Span("→ N/A", style={'color': '#6b7280', 'fontSize': '0.875rem'})
    
#     change = current - previous
    
#     # Determine colors based on inverse_colors flag
#     if inverse_colors:
#         # For fail rate: decrease is good (green), increase is bad (red)
#         good_color = '#10b981'  # green
#         bad_color = '#ef4444'   # red
#     else:
#         # For pass/distinction rate: increase is good (green), decrease is bad (red)
#         good_color = '#10b981'  # green
#         bad_color = '#ef4444'   # red
    
#     if abs(change) < 0.5:
#         return html.Span(
#             f"→ {change:+.1f}% from {label}",
#             style={'color': '#6b7280', 'fontSize': '0.875rem'}
#         )
#     elif change > 0:
#         color = bad_color if inverse_colors else good_color
#         return html.Span(
#             f"↑ {change:+.1f}% from {label}",
#             style={'color': color, 'fontWeight': 'bold', 'fontSize': '0.875rem'}
#         )
#     else:
#         color = good_color if inverse_colors else bad_color
#         return html.Span(
#             f"↓ {change:+.1f}% from {label}",
#             style={'color': color, 'fontWeight': 'bold', 'fontSize': '0.875rem'}
#         )






# # ==============================================================================
# # FILE: dashboard/components.py
# # ==============================================================================
# """
# Reusable UI components for the dashboard.
# Cards, filters, and other UI elements.
# """

# import dash_bootstrap_components as dbc
# from dash import dcc, html
# from config import COLORS


# def create_filter_card(filter_options):
#     """
#     Create filter card with all dropdown filters.
    
#     Args:
#         filter_options (dict): Dictionary with filter options
        
#     Returns:
#         dbc.Card: Filter card component
#     """
#     return dbc.Card([
#         dbc.CardBody([
#             dbc.Row([
#                 dbc.Col([
#                     html.Label("Department", className="fw-bold"),
#                     dcc.Dropdown(
#                         id='department-filter',
#                         options=[{'label': d, 'value': d} for d in filter_options['departments']],
#                         value='All',
#                         clearable=False
#                     )
#                 ], md=4),
#                 dbc.Col([
#                     html.Label("Semester", className="fw-bold"),
#                     dcc.Dropdown(
#                         id='semester-filter',
#                         options=[{'label': ('All Semesters' if s == 'All' else f'Sem {s}'), 
#                                 'value': s} for s in filter_options['semesters']],
#                         value='All',
#                         clearable=False
#                     )
#                 ], md=4),
#                 dbc.Col([
#                     html.Label("Subject/Course", className="fw-bold"),
#                     dcc.Dropdown(
#                         id='subject-filter',
#                         options=[{'label': s, 'value': s} for s in filter_options['subjects']],
#                         value='All',
#                         clearable=False
#                     )
#                 ], md=4),
#             ]),
#             dbc.Row([
#                 dbc.Col([
#                     html.Label("Year Range", className="fw-bold mt-3"),
#                     dcc.RangeSlider(
#                         id='year-range-slider',
#                         min=min(filter_options['years'][1:]),  # Skip 'All'
#                         max=max(filter_options['years'][1:]),
#                         value=[min(filter_options['years'][1:]), max(filter_options['years'][1:])],
#                         marks={int(year): str(int(year)) for year in filter_options['years'][1:]},
#                         step=1,
#                         tooltip={"placement": "bottom", "always_visible": True}
#                     )
#                 ], md=12)
#             ])
#         ])
#     ], className="mb-4 shadow-sm")


# def create_kpi_card(title, value_id, trend_id=None, color=None, border_color=None):
#     """
#     Create KPI card component.
    
#     Args:
#         title (str): Card title
#         value_id (str): ID for value display
#         trend_id (str): ID for trend indicator
#         color (str): Text color class
#         border_color (str): Left border color
        
#     Returns:
#         dbc.Col: Column containing KPI card
#     """
#     card_style = {}
#     if border_color:
#         card_style['borderLeft'] = f'4px solid {border_color}'
    
#     card_body = [
#         html.H6(title, className="text-muted"),
#         html.H2(id=value_id, className=f"mb-0 {color}" if color else "mb-0"),
#     ]
    
#     if trend_id:
#         card_body.append(html.Div(id=trend_id))
#     else:
#         card_body.append(html.Small(id=f'{value_id}-change', className="text-muted"))
    
#     return dbc.Col(
#         dbc.Card([
#             dbc.CardBody(card_body)
#         ], className="shadow-sm", style=card_style),
#         md=3
#     )


# def create_chart_card(title, chart_id, icon="📈"):
#     """
#     Create chart card component.
    
#     Args:
#         title (str): Card title
#         chart_id (str): ID for chart
#         icon (str): Title icon
        
#     Returns:
#         dbc.Card: Chart card component
#     """
#     return dbc.Card([
#         dbc.CardBody([
#             html.H5(f"{icon} {title}", className="mb-3"),
#             dcc.Graph(id=chart_id, config={'displayModeBar': False})
#         ])
#     ], className="shadow-sm")


# def create_trend_indicator(current, previous, label="average"):
#     """
#     Create HTML trend indicator with descriptive label.
    
#     Args:
#         current (float): Current value
#         previous (float): Previous/comparison value
#         label (str): Description label
        
#     Returns:
#         html.Span: Trend indicator component
#     """
#     if previous == 0:
#         return html.Span("→ N/A", style={'color': '#6b7280', 'fontSize': '0.875rem'})
    
#     change = current - previous
#     if abs(change) < 0.5:
#         return html.Span(
#             f"→ {change:+.1f}% from {label}",
#             style={'color': '#6b7280', 'fontSize': '0.875rem'}
#         )
#     elif change > 0:
#         return html.Span(
#             f"↑ {change:+.1f}% from {label}",
#             style={'color': '#10b981', 'fontWeight': 'bold', 'fontSize': '0.875rem'}
#         )
#     else:
#         return html.Span(
#             f"↓ {change:+.1f}% from {label}",
#             style={'color': '#ef4444', 'fontWeight': 'bold', 'fontSize': '0.875rem'}
#         )

