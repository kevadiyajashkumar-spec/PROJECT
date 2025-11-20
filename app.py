from dash import Dash
import dash_bootstrap_components as dbc

from data.loader import load_data
from data.processor import add_performance_column, get_filter_options
from dashboard.layout import create_layout
from dashboard.callbacks import register_callbacks
from config import HOST, PORT, DEBUG


# 🔹 Create Dash App
app = Dash(
    __name__,
    external_stylesheets=[dbc.themes.BOOTSTRAP],
    suppress_callback_exceptions=True
)

server = app.server  # 🔥 Needed by Gunicorn and Render

app.title = "Student Analytics Dashboard"

# 🔹 Load data ONCE at import time (not inside main)
df = load_data()
df = add_performance_column(df)

# 🔹 Prepare filters and layout BEFORE first request
filter_options = get_filter_options(df)
app.layout = create_layout(filter_options)

# 🔹 Register callbacks BEFORE run
register_callbacks(app, df)


# 🔹 Local development runner
def main():
    print("=" * 60)
    print("🎓 Student Analytics Dashboard")
    print("=" * 60)
    print(f"📁 Loaded data: {df.shape[0]:,} records")
    print(f"🌐 Open: http://localhost:{PORT}")
    app.run_server(host=HOST, port=PORT, debug=DEBUG)


if __name__ == "__main__":
    main()





# # ==============================================================================
# # FILE: app.py
# # ==============================================================================
# """
# Main application entry point.
# Run this file to start the dashboard.
# """

# from dash import Dash
# import dash_bootstrap_components as dbc

# from data.loader import load_data
# from data.processor import add_performance_column, get_filter_options
# from dashboard.layout import create_layout
# from dashboard.callbacks import register_callbacks
# from config import HOST, PORT, DEBUG


# def create_app():
#     """
#     Create and configure the Dash application.
#     """
#     app = Dash(
#         __name__,
#         external_stylesheets=[dbc.themes.BOOTSTRAP],
#         suppress_callback_exceptions=True
#     )

#     # Set page title
#     app.title = "Student Analytics Dashboard"

#     # Custom loading style
#     app.index_string = '''
#     <!DOCTYPE html>
#     <html>
#         <head>
#             {%metas%}
#             <title>{%title%}</title>
#             {%favicon%}
#             {%css%}
#             <style>
#                 .loading-spinner {
#                     border: 3px solid #f3f4f6;
#                     border-top: 3px solid #3b82f6;
#                     border-radius: 50%;
#                     width: 40px;
#                     height: 40px;
#                     animation: spin 1s linear infinite;
#                     margin: 20px auto;
#                 }
#                 @keyframes spin {
#                     0% { transform: rotate(0deg); }
#                     100% { transform: rotate(360deg); }
#                 }
#             </style>
#         </head>
#         <body>
#             {%app_entry%}
#             <footer>
#                 {%config%}
#                 {%scripts%}
#                 {%renderer%}
#             </footer>
#         </body>
#     </html>
#     '''
#     return app


# # 🔹 Create Dash app globally (Gunicorn needs this)
# app = create_app()
# server = app.server  # Required for Render/Gunicorn


# def main():
#     """Main function to run the dashboard."""
#     print("=" * 60)
#     print("🎓 Student Analytics Dashboard")
#     print("=" * 60)

#     # Load and process data
#     print("\n📊 Loading data...")
#     df = load_data()
#     df = add_performance_column(df)

#     # Get filter options
#     print("🔍 Preparing filters...")
#     filter_options = get_filter_options(df)

#     # Set layout and callbacks
#     app.layout = create_layout(filter_options)
#     register_callbacks(app, df)

#     # Local run
#     print(f"\n🌐 Open your browser at: http://localhost:{PORT}")
#     print(f"📁 Loaded data: {df.shape[0]:,} records\n")
    
#     app.run_server(host=HOST, port=PORT, debug=DEBUG)


# if __name__ == '__main__':
#     main()



# # ==============================================================================
# # FILE: app.py
# # ==============================================================================
# """
# Main application entry point.
# Run this file to start the dashboard.
# """

# print(">>> app.py loaded")


# from dash import Dash
# import dash_bootstrap_components as dbc
# from data.loader import load_data
# from data.processor import add_performance_column, get_filter_options
# from dashboard.layout import create_layout
# from dashboard.callbacks import register_callbacks
# from config import HOST, PORT, DEBUG


# def create_app():
#     """
#     Create and configure the Dash application.
    
#     Returns:
#         Dash: Configured Dash app
#     """
#     # Initialize Dash app
#     app = Dash(
#         __name__,
#         external_stylesheets=[dbc.themes.BOOTSTRAP],
#         suppress_callback_exceptions=True
#     )
    
#     # Set page title
#     app.title = "Student Analytics Dashboard"
    
#     # Custom loading style
#     app.index_string = '''
#     <!DOCTYPE html>
#     <html>
#         <head>
#             {%metas%}
#             <title>{%title%}</title>
#             {%favicon%}
#             {%css%}
#             <style>
#                 .loading-spinner {
#                     border: 3px solid #f3f4f6;
#                     border-top: 3px solid #3b82f6;
#                     border-radius: 50%;
#                     width: 40px;
#                     height: 40px;
#                     animation: spin 1s linear infinite;
#                     margin: 20px auto;
#                 }
#                 @keyframes spin {
#                     0% { transform: rotate(0deg); }
#                     100% { transform: rotate(360deg); }
#                 }
#             </style>
#         </head>
#         <body>
#             {%app_entry%}
#             <footer>
#                 {%config%}
#                 {%scripts%}
#                 {%renderer%}
#             </footer>
#         </body>
#     </html>
#     '''
    
#     return app


# def main():
#     """Main function to run the application."""
    
#     print("=" * 60)
#     print("🎓 Student Analytics Dashboard")
#     print("=" * 60)
    
#     # Load and process data
#     print("\n📊 Loading data...")
#     df = load_data()
#     df = add_performance_column(df)
    
#     # Get filter options
#     print("🔍 Preparing filters...")
#     filter_options = get_filter_options(df)
    
#     # Create app
#     print("🚀 Initializing dashboard...")
#     app = create_app()
    
#     # Set layout
#     app.layout = create_layout(filter_options)
    
#     # Register callbacks
#     register_callbacks(app, df)
    
#     # Start server
#     print(f"\n✅ Dashboard ready!")
#     print(f"🌐 Open your browser and navigate to: http://localhost:{PORT}")
#     print(f"📁 Using data from: {df.shape[0]:,} records")
#     print("\n⏹  Press Ctrl+C to stop the server\n")
#     print("=" * 60)
    
#     app.run_server(host=HOST, port=PORT, debug=DEBUG)


# if __name__ == '__main__':
#     main()
