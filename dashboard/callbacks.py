"""
Dashboard callbacks for interactivity.
"""

from dash import Input, Output, State, callback_context, no_update
from dash.exceptions import PreventUpdate
import plotly.graph_objs as go
import plotly.express as px
from datetime import datetime
import pandas as pd
import json


def register_callbacks(app, dashboard):
    """
    Register all dashboard callbacks.
    
    Args:
        app: Dash app instance
        dashboard: DashboardApp instance
    """
    
    @app.callback(
        Output("current-time", "children"),
        Input("interval-component", "n_intervals")
    )
    def update_time(n):
        """Update current time display."""
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    
    @app.callback(
        [Output("algorithm-status-content", "children"),
         Output("overall-progress", "value"),
         Output("overall-progress", "label"),
         Output("convergence-algorithm-select", "options")],
        [Input("interval-component", "n_intervals"),
         State("paused-state", "data")]
    )
    def update_algorithm_status(n, is_paused):
        """Update algorithm status display."""
        if is_paused:
            raise PreventUpdate
            
        # Update algorithm data
        for run_id in dashboard.active_algorithms:
            if dashboard.active_algorithms[run_id]['status'] == 'running':
                dashboard.update_algorithm_data(run_id)
        
        # Get active algorithms
        active_algos = dashboard.get_active_algorithms()
        
        if not active_algos:
            return (
                [html.P("No active algorithms", className="text-muted text-center")],
                0,
                "No algorithms running",
                []
            )
        
        # Create status items
        from .layouts import create_algorithm_status_item
        status_items = []
        total_progress = 0
        
        for algo in active_algos:
            status_items.append(
                create_algorithm_status_item(
                    algo['run_id'],
                    algo['algorithm'],
                    algo['status'],
                    algo['metrics']
                )
            )
            # Assuming 100 iterations max for progress calculation
            progress = algo['metrics'].get('current_iteration', 0)
            total_progress += progress
        
        # Calculate overall progress
        avg_progress = total_progress / len(active_algos) if active_algos else 0
        
        # Create options for algorithm selector
        options = [
            {"label": f"{algo['algorithm']} ({algo['run_id'][:8]}...)", 
             "value": algo['run_id']}
            for algo in active_algos
        ]
        
        return (
            status_items,
            avg_progress,
            f"{int(avg_progress)}% Complete",
            options
        )
    
    
    @app.callback(
        Output("convergence-plot", "figure"),
        [Input("interval-component", "n_intervals"),
         Input("convergence-algorithm-select", "value"),
         State("display-options", "value"),
         State("max-points-input", "value"),
         State("paused-state", "data")]
    )
    def update_convergence_plot(n, selected_run_id, display_options, max_points, is_paused):
        """Update convergence plot."""
        if is_paused or not selected_run_id:
            raise PreventUpdate
        
        # Get convergence data
        data = dashboard.get_convergence_data(selected_run_id)
        
        if not data:
            return {
                'data': [],
                'layout': {
                    'title': 'No data available',
                    'xaxis': {'title': 'Iteration'},
                    'yaxis': {'title': 'Fitness'}
                }
            }
        
        # Limit data points
        if max_points and len(data) > max_points:
            # Sample data points evenly
            step = len(data) // max_points
            data = data[::step] + [data[-1]]  # Always include last point
        
        # Create traces
        traces = []
        
        # Best fitness trace
        traces.append(go.Scatter(
            x=[d['iteration'] for d in data],
            y=[d['best_fitness'] for d in data],
            mode='lines+markers',
            name='Best Fitness',
            line=dict(color='#1f77b4', width=2),
            marker=dict(size=4)
        ))
        
        # Mean fitness trace
        traces.append(go.Scatter(
            x=[d['iteration'] for d in data],
            y=[d['mean_fitness'] for d in data],
            mode='lines',
            name='Mean Fitness',
            line=dict(color='#ff7f0e', width=1, dash='dash')
        ))
        
        # Std deviation band
        if display_options and 'autoscale' in display_options:
            upper_bound = [d['mean_fitness'] + d['std_fitness'] for d in data]
            lower_bound = [d['mean_fitness'] - d['std_fitness'] for d in data]
            
            traces.append(go.Scatter(
                x=[d['iteration'] for d in data] + [d['iteration'] for d in data[::-1]],
                y=upper_bound + lower_bound[::-1],
                fill='toself',
                fillcolor='rgba(255,127,14,0.2)',
                line=dict(color='rgba(255,255,255,0)'),
                name='Std Dev',
                showlegend=False
            ))
        
        # Layout
        layout = {
            'title': f'Convergence Plot - {dashboard.active_algorithms[selected_run_id]["algorithm"].__class__.__name__}',
            'xaxis': {'title': 'Iteration'},
            'yaxis': {'title': 'Fitness', 'type': 'log' if min(d['best_fitness'] for d in data) > 0 else 'linear'},
            'hovermode': 'x unified',
            'showlegend': 'legend' in display_options if display_options else True,
            'plot_bgcolor': 'white',
            'margin': {'l': 60, 'r': 30, 't': 80, 'b': 60}
        }
        
        if display_options and 'grid' in display_options:
            layout['xaxis']['showgrid'] = True
            layout['yaxis']['showgrid'] = True
            layout['xaxis']['gridcolor'] = '#f0f0f0'
            layout['yaxis']['gridcolor'] = '#f0f0f0'
        
        return {'data': traces, 'layout': layout}
    
    
    @app.callback(
        [Output("best-fitness-value", "children"),
         Output("iterations-value", "children"),
         Output("execution-time-value", "children"),
         Output("convergence-rate-value", "children")],
        [Input("interval-component", "n_intervals"),
         Input("convergence-algorithm-select", "value"),
         State("paused-state", "data")]
    )
    def update_performance_metrics(n, selected_run_id, is_paused):
        """Update performance metrics display."""
        if is_paused or not selected_run_id:
            return ["--", "--", "--", "--"]
        
        if selected_run_id not in dashboard.active_algorithms:
            return ["--", "--", "--", "--"]
        
        metrics = dashboard.active_algorithms[selected_run_id].get('metrics', {})
        
        return [
            f"{metrics.get('best_fitness', 0):.4f}",
            str(metrics.get('current_iteration', 0)),
            f"{metrics.get('execution_time', 0):.1f}s",
            f"{metrics.get('convergence_rate', 0):.2f}%"
        ]
    
    
    @app.callback(
        Output("comparison-table-content", "children"),
        [Input("interval-component", "n_intervals"),
         State("paused-state", "data")]
    )
    def update_comparison_table(n, is_paused):
        """Update comparison table."""
        if is_paused:
            raise PreventUpdate
        
        comparison_data = dashboard.get_comparison_data()
        
        from .layouts import create_comparison_table
        return create_comparison_table(comparison_data)
    
    
    @app.callback(
        Output("population-distribution-plot", "figure"),
        [Input("interval-component", "n_intervals"),
         Input("convergence-algorithm-select", "value"),
         State("paused-state", "data")]
    )
    def update_population_distribution(n, selected_run_id, is_paused):
        """Update population distribution plot."""
        if is_paused or not selected_run_id:
            raise PreventUpdate
        
        if selected_run_id not in dashboard.active_algorithms:
            raise PreventUpdate
        
        algorithm = dashboard.active_algorithms[selected_run_id]['algorithm']
        
        # Get population fitnesses
        if hasattr(algorithm, 'population') and algorithm.population:
            fitnesses = [ind.fitness() for ind in algorithm.population]
        else:
            fitnesses = []
        
        if not fitnesses:
            return {
                'data': [],
                'layout': {
                    'title': 'No population data',
                    'margin': {'l': 40, 'r': 20, 't': 40, 'b': 40}
                }
            }
        
        # Create histogram
        fig = go.Figure()
        fig.add_trace(go.Histogram(
            x=fitnesses,
            nbinsx=20,
            name='Population',
            marker_color='#2ca02c',
            opacity=0.7
        ))
        
        # Add mean line
        mean_fitness = sum(fitnesses) / len(fitnesses)
        fig.add_vline(
            x=mean_fitness,
            line_dash="dash",
            line_color="red",
            annotation_text=f"Mean: {mean_fitness:.2f}"
        )
        
        fig.update_layout(
            title='Population Fitness Distribution',
            xaxis_title='Fitness',
            yaxis_title='Count',
            showlegend=False,
            margin={'l': 40, 'r': 20, 't': 60, 'b': 40},
            plot_bgcolor='white'
        )
        
        return fig
    
    
    @app.callback(
        Output("performance-history-plot", "figure"),
        [Input("interval-component", "n_intervals"),
         Input("convergence-algorithm-select", "value"),
         Input("history-metric-select", "value"),
         State("paused-state", "data")]
    )
    def update_performance_history(n, selected_run_id, metric, is_paused):
        """Update performance history plot."""
        if is_paused or not selected_run_id:
            raise PreventUpdate
        
        history = dashboard.get_performance_history(selected_run_id)
        
        if not history or metric not in ['best', 'mean', 'std']:
            raise PreventUpdate
        
        # Map metric to data key
        metric_map = {
            'best': 'best_fitness',
            'mean': 'mean_fitness',
            'std': 'std_fitness'
        }
        
        data_key = metric_map[metric]
        data = history.get(data_key, [])
        
        if not data:
            return {
                'data': [],
                'layout': {
                    'title': 'No history data',
                    'margin': {'l': 40, 'r': 20, 't': 40, 'b': 40}
                }
            }
        
        # Create line plot
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=list(range(len(data))),
            y=data[-50:],  # Show last 50 points
            mode='lines',
            name=metric.capitalize(),
            line=dict(color='#d62728', width=2)
        ))
        
        fig.update_layout(
            title=f'{metric.capitalize()} Fitness History',
            xaxis_title='Time Steps',
            yaxis_title='Fitness',
            showlegend=False,
            margin={'l': 40, 'r': 20, 't': 60, 'b': 40},
            plot_bgcolor='white',
            xaxis=dict(showgrid=True, gridcolor='#f0f0f0'),
            yaxis=dict(showgrid=True, gridcolor='#f0f0f0')
        )
        
        return fig
    
    
    @app.callback(
        [Output("interval-component", "interval"),
         Output("update-interval-input", "value")],
        [Input("update-interval-input", "value")]
    )
    def update_interval(interval_value):
        """Update refresh interval."""
        if interval_value and interval_value >= 100:
            return interval_value, interval_value
        return no_update, no_update
    
    
    @app.callback(
        [Output("paused-state", "data"),
         Output("pause-btn", "children"),
         Output("pause-btn", "color")],
        [Input("pause-btn", "n_clicks")],
        [State("paused-state", "data")]
    )
    def toggle_pause(n_clicks, is_paused):
        """Toggle pause state."""
        if n_clicks is None:
            raise PreventUpdate
        
        new_paused = not is_paused
        btn_text = "Resume Updates" if new_paused else "Pause Updates"
        btn_color = "success" if new_paused else "warning"
        
        return new_paused, btn_text, btn_color
    
    
    @app.callback(
        Output("download-dataframe-csv", "data"),
        [Input("export-comparison-btn", "n_clicks")],
        prevent_initial_call=True
    )
    def export_comparison_data(n_clicks):
        """Export comparison data as CSV."""
        if n_clicks is None:
            raise PreventUpdate
        
        comparison_data = dashboard.get_comparison_data()
        if not comparison_data:
            raise PreventUpdate
        
        df = pd.DataFrame(comparison_data)
        return dict(
            content=df.to_csv(index=False),
            filename=f"algorithm_comparison_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        )
    
    
    @app.callback(
        Output("notification-toast", "children"),
        [Input("snapshot-btn", "n_clicks")],
        [State("convergence-algorithm-select", "value")],
        prevent_initial_call=True
    )
    def save_snapshot(n_clicks, selected_run_id):
        """Save dashboard snapshot."""
        if n_clicks is None or not selected_run_id:
            raise PreventUpdate
        
        # Save snapshot
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filepath = f"dashboard_snapshots/snapshot_{selected_run_id}_{timestamp}.json"
        
        try:
            dashboard.save_snapshot(selected_run_id, filepath)
            
            import dash_bootstrap_components as dbc
            return dbc.Toast(
                "Snapshot saved successfully!",
                id="snapshot-toast",
                header="Success",
                is_open=True,
                dismissable=True,
                duration=3000,
                icon="success",
                style={"position": "fixed", "top": 66, "right": 10, "width": 350}
            )
        except Exception as e:
            import dash_bootstrap_components as dbc
            return dbc.Toast(
                f"Failed to save snapshot: {str(e)}",
                id="snapshot-toast",
                header="Error",
                is_open=True,
                dismissable=True,
                duration=5000,
                icon="danger",
                style={"position": "fixed", "top": 66, "right": 10, "width": 350}
            )