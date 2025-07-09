"""
Dashboard layouts and components.
"""

from dash import html, dcc
import dash_bootstrap_components as dbc
from datetime import datetime


def get_header():
    """Get dashboard header."""
    return dbc.Navbar(
        dbc.Container([
            dbc.Row([
                dbc.Col([
                    html.Img(src="/assets/logo.png", height="40px", className="me-2"),
                    dbc.NavbarBrand("BioAlgoCompare Dashboard", className="ms-2")
                ], width="auto"),
                dbc.Col([
                    html.Div(id="current-time", className="text-muted")
                ], width="auto", className="ms-auto")
            ], align="center", className="g-0 w-100"),
        ]),
        color="primary",
        dark=True,
        className="mb-4"
    )


def get_algorithm_status_card():
    """Get algorithm status card."""
    return dbc.Card([
        dbc.CardHeader(html.H5("Active Algorithms", className="mb-0")),
        dbc.CardBody([
            html.Div(id="algorithm-status-content"),
            dbc.Progress(id="overall-progress", className="mt-3")
        ])
    ], className="h-100")


def get_convergence_plot_card():
    """Get convergence plot card."""
    return dbc.Card([
        dbc.CardHeader([
            dbc.Row([
                dbc.Col(html.H5("Convergence Plot", className="mb-0")),
                dbc.Col([
                    dbc.Select(
                        id="convergence-algorithm-select",
                        options=[],
                        placeholder="Select algorithm...",
                        size="sm"
                    )
                ], width=4)
            ])
        ]),
        dbc.CardBody([
            dcc.Graph(
                id="convergence-plot",
                config={'displayModeBar': True},
                style={'height': '400px'}
            )
        ])
    ], className="h-100")


def get_performance_metrics_card():
    """Get performance metrics card."""
    return dbc.Card([
        dbc.CardHeader(html.H5("Performance Metrics", className="mb-0")),
        dbc.CardBody([
            dbc.Row([
                dbc.Col([
                    html.H6("Best Fitness", className="text-muted"),
                    html.H3(id="best-fitness-value", children="--")
                ], width=3),
                dbc.Col([
                    html.H6("Iterations", className="text-muted"),
                    html.H3(id="iterations-value", children="--")
                ], width=3),
                dbc.Col([
                    html.H6("Execution Time", className="text-muted"),
                    html.H3(id="execution-time-value", children="--")
                ], width=3),
                dbc.Col([
                    html.H6("Convergence Rate", className="text-muted"),
                    html.H3(id="convergence-rate-value", children="--")
                ], width=3),
            ])
        ])
    ], className="h-100")


def get_comparison_table_card():
    """Get algorithm comparison table card."""
    return dbc.Card([
        dbc.CardHeader([
            dbc.Row([
                dbc.Col(html.H5("Algorithm Comparison", className="mb-0")),
                dbc.Col([
                    dbc.Button(
                        "Export CSV",
                        id="export-comparison-btn",
                        color="secondary",
                        size="sm",
                        className="me-2"
                    ),
                    dbc.Button(
                        "Clear",
                        id="clear-comparison-btn",
                        color="danger",
                        size="sm"
                    )
                ], width="auto")
            ])
        ]),
        dbc.CardBody([
            html.Div(id="comparison-table-content")
        ])
    ], className="h-100")


def get_population_distribution_card():
    """Get population distribution card."""
    return dbc.Card([
        dbc.CardHeader(html.H5("Population Distribution", className="mb-0")),
        dbc.CardBody([
            dcc.Graph(
                id="population-distribution-plot",
                config={'displayModeBar': False},
                style={'height': '300px'}
            )
        ])
    ], className="h-100")


def get_performance_history_card():
    """Get performance history card."""
    return dbc.Card([
        dbc.CardHeader([
            dbc.Row([
                dbc.Col(html.H5("Performance History", className="mb-0")),
                dbc.Col([
                    dbc.RadioItems(
                        id="history-metric-select",
                        options=[
                            {"label": "Best", "value": "best"},
                            {"label": "Mean", "value": "mean"},
                            {"label": "Std Dev", "value": "std"}
                        ],
                        value="best",
                        inline=True,
                        className="radio-group"
                    )
                ], width="auto")
            ])
        ]),
        dbc.CardBody([
            dcc.Graph(
                id="performance-history-plot",
                config={'displayModeBar': False},
                style={'height': '300px'}
            )
        ])
    ], className="h-100")


def get_control_panel():
    """Get control panel."""
    return dbc.Card([
        dbc.CardHeader(html.H5("Control Panel", className="mb-0")),
        dbc.CardBody([
            dbc.Row([
                dbc.Col([
                    html.Label("Update Interval (ms)"),
                    dbc.Input(
                        id="update-interval-input",
                        type="number",
                        value=1000,
                        min=100,
                        max=10000,
                        step=100
                    )
                ], width=6),
                dbc.Col([
                    html.Label("Max Data Points"),
                    dbc.Input(
                        id="max-points-input",
                        type="number",
                        value=100,
                        min=10,
                        max=1000,
                        step=10
                    )
                ], width=6)
            ], className="mb-3"),
            dbc.Row([
                dbc.Col([
                    dbc.Checklist(
                        id="display-options",
                        options=[
                            {"label": "Show Grid", "value": "grid"},
                            {"label": "Show Legend", "value": "legend"},
                            {"label": "Auto-scale", "value": "autoscale"}
                        ],
                        value=["grid", "legend", "autoscale"],
                        inline=True
                    )
                ])
            ], className="mb-3"),
            dbc.Row([
                dbc.Col([
                    dbc.Button(
                        "Pause Updates",
                        id="pause-btn",
                        color="warning",
                        className="me-2"
                    ),
                    dbc.Button(
                        "Save Snapshot",
                        id="snapshot-btn",
                        color="info"
                    )
                ])
            ])
        ])
    ])


def get_main_layout(update_interval: int = 1000):
    """
    Get main dashboard layout.
    
    Args:
        update_interval: Update interval in milliseconds
        
    Returns:
        Dashboard layout
    """
    return dbc.Container([
        # Header
        get_header(),
        
        # Hidden elements for state management
        dcc.Interval(id="interval-component", interval=update_interval),
        dcc.Store(id="current-algorithm-store"),
        dcc.Store(id="paused-state", data=False),
        
        # Main content
        dbc.Row([
            # Left column - Status and control
            dbc.Col([
                dbc.Row([
                    dbc.Col(get_algorithm_status_card(), width=12, className="mb-3")
                ]),
                dbc.Row([
                    dbc.Col(get_performance_metrics_card(), width=12, className="mb-3")
                ]),
                dbc.Row([
                    dbc.Col(get_control_panel(), width=12)
                ])
            ], width=3),
            
            # Middle column - Main visualizations
            dbc.Col([
                dbc.Row([
                    dbc.Col(get_convergence_plot_card(), width=12, className="mb-3")
                ]),
                dbc.Row([
                    dbc.Col(get_comparison_table_card(), width=12)
                ])
            ], width=6),
            
            # Right column - Additional visualizations
            dbc.Col([
                dbc.Row([
                    dbc.Col(get_population_distribution_card(), width=12, className="mb-3")
                ]),
                dbc.Row([
                    dbc.Col(get_performance_history_card(), width=12)
                ])
            ], width=3)
        ]),
        
        # Footer
        html.Hr(className="mt-4"),
        dbc.Row([
            dbc.Col([
                html.P(
                    "BioAlgoCompare Dashboard v1.0 | Real-time Algorithm Monitoring",
                    className="text-muted text-center mb-2"
                )
            ])
        ]),
        
        # Download component
        dcc.Download(id="download-dataframe-csv"),
        
        # Notification toast
        html.Div(id="notification-toast")
        
    ], fluid=True)


def create_algorithm_status_item(run_id: str, algorithm_name: str, 
                               status: str, metrics: dict) -> html.Div:
    """Create a single algorithm status item."""
    status_color = {
        'running': 'success',
        'paused': 'warning',
        'completed': 'info',
        'failed': 'danger'
    }.get(status, 'secondary')
    
    return html.Div([
        dbc.Row([
            dbc.Col([
                html.Strong(algorithm_name),
                html.Br(),
                html.Small(f"Run ID: {run_id}", className="text-muted")
            ], width=6),
            dbc.Col([
                dbc.Badge(status.upper(), color=status_color),
                html.Br(),
                html.Small(f"Iter: {metrics.get('current_iteration', 0)}")
            ], width=6, className="text-end")
        ], className="mb-2"),
        dbc.Progress(
            value=metrics.get('current_iteration', 0),
            max=100,  # Should be max_iterations
            className="mb-2",
            style={"height": "5px"}
        )
    ], className="algorithm-status-item p-2 border rounded mb-2")


def create_comparison_table(comparison_data: list) -> dbc.Table:
    """Create comparison table."""
    if not comparison_data:
        return html.P("No data available", className="text-muted text-center")
    
    # Sort by best fitness
    sorted_data = sorted(comparison_data, key=lambda x: x['best_fitness'])
    
    # Create table rows
    rows = []
    for i, data in enumerate(sorted_data):
        rows.append(
            html.Tr([
                html.Td(str(i + 1)),
                html.Td(data['algorithm']),
                html.Td(f"{data['best_fitness']:.4f}"),
                html.Td(f"{data['execution_time']:.2f}s"),
                html.Td(str(data['iterations'])),
                html.Td(f"{data['convergence_rate']:.2f}%")
            ])
        )
    
    return dbc.Table([
        html.Thead([
            html.Tr([
                html.Th("Rank"),
                html.Th("Algorithm"),
                html.Th("Best Fitness"),
                html.Th("Time"),
                html.Th("Iterations"),
                html.Th("Conv. Rate")
            ])
        ]),
        html.Tbody(rows)
    ], striped=True, hover=True, responsive=True, size="sm")