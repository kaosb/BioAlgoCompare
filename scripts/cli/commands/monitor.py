"""
Real-time monitoring commands for BioAlgoCompare.
"""

import click
import time
import sys
from pathlib import Path
from typing import Optional
import logging


@click.group()
def monitor():
    """Real-time performance monitoring tools."""
    pass


@monitor.command()
@click.option('--dashboard', type=click.Choice(['terminal', 'web', 'both']), 
              default='terminal', help='Dashboard type to display')
@click.option('--port', type=int, default=8080, help='Port for web dashboard')
@click.option('--export', type=click.Path(), help='Export metrics to file')
@click.option('--interval', type=float, default=1.0, help='Collection interval (seconds)')
@click.option('--no-system', is_flag=True, help='Disable system monitoring')
def start(dashboard, port, export, interval, no_system):
    """
    Start real-time monitoring dashboard.
    
    Launches a monitoring dashboard that can display metrics from running
    algorithms or system resources in real-time.
    
    Examples:
    
        # Start terminal dashboard
        bioalgo monitor start
        
        # Start web dashboard
        bioalgo monitor start --dashboard web --port 8080
        
        # Monitor with export
        bioalgo monitor start --dashboard both --export metrics.json
    """
    from utils.monitoring import PerformanceMonitor
    
    click.echo(f"🔍 Starting {dashboard} monitoring dashboard...")
    
    try:
        monitor = PerformanceMonitor(
            dashboard_type=dashboard,
            export_metrics=export is not None,
            export_file=export,
            web_port=port,
            collection_interval=interval,
            enable_system_monitoring=not no_system
        )
        
        with monitor:
            if dashboard in ['web', 'both']:
                url = monitor.get_dashboard_url()
                click.echo(f"🌐 Web dashboard: {url}")
            
            if dashboard in ['terminal', 'both']:
                click.echo("📊 Terminal dashboard active")
                click.echo("Press Ctrl+C to stop monitoring")
            
            try:
                # Keep running until interrupted
                while True:
                    time.sleep(1)
            except KeyboardInterrupt:
                click.echo("\n⏹️  Stopping monitor...")
                
    except Exception as e:
        click.echo(f"❌ Error starting monitor: {e}", err=True)
        sys.exit(1)


@monitor.command()
@click.argument('algorithm')
@click.argument('instance')
@click.option('--dashboard', type=click.Choice(['terminal', 'web', 'both', 'none']), 
              default='terminal', help='Dashboard type')
@click.option('--iterations', type=int, default=100, help='Maximum iterations')
@click.option('--population', type=int, default=30, help='Population size')
@click.option('--seed', type=int, help='Random seed')
@click.option('--export', type=click.Path(), help='Export metrics file')
@click.option('--port', type=int, default=8080, help='Web dashboard port')
def run(algorithm, instance, dashboard, iterations, population, seed, export, port):
    """
    Run algorithm with real-time monitoring.
    
    Executes an algorithm on a VRP instance while displaying real-time
    performance metrics and system resource usage.
    
    Examples:
    
        # Run with terminal monitoring
        bioalgo monitor run HOA E-n22-k4
        
        # Run with web dashboard
        bioalgo monitor run FOA P-n16-k8 --dashboard web
        
        # Run with export
        bioalgo monitor run EGTO E-n33-k4 --export metrics.json
    """
    from algorithms import get_algorithm_class
    from problems.vrp import VRPProblem
    from utils.monitoring import PerformanceMonitor
    
    click.echo(f"🚀 Running {algorithm} on {instance} with monitoring...")
    
    try:
        # Load problem
        problem = VRPProblem(instance)
        click.echo(f"📦 Loaded instance: {instance} ({problem.dimension} customers)")
        
        # Get algorithm class
        algorithm_class = get_algorithm_class(algorithm.upper())
        if not algorithm_class:
            click.echo(f"❌ Unknown algorithm: {algorithm}", err=True)
            sys.exit(1)
        
        # Create algorithm instance
        algo = algorithm_class(
            problem=problem,
            population_size=population,
            max_iterations=iterations,
            seed=seed
        )
        
        # Setup monitoring
        monitor = PerformanceMonitor(
            dashboard_type=dashboard,
            export_metrics=export is not None,
            export_file=export,
            web_port=port
        )
        
        # Run with monitoring
        with monitor:
            if dashboard in ['web', 'both']:
                url = monitor.get_dashboard_url()
                click.echo(f"🌐 Dashboard: {url}")
            
            # Start algorithm execution
            start_time = time.time()
            
            # Initialize population with monitoring
            algo.initialize_population()
            monitor.update_algorithm_metrics(
                iteration=0,
                current_fitness=algo.best_fitness,
                best_fitness=algo.best_fitness,
                population=algo.population,
                max_iterations=iterations
            )
            
            # Main algorithm loop
            for iteration in range(1, iterations + 1):
                # Run one iteration
                algo.update_population()  # This would be algorithm-specific
                
                # Update monitoring
                monitor.update_algorithm_metrics(
                    iteration=iteration,
                    current_fitness=algo.best_fitness,
                    best_fitness=algo.best_fitness,
                    population=algo.population,
                    max_iterations=iterations
                )
                
                # Optional: Early stopping or user interaction
                # (This would be implemented in the actual algorithm)
            
            # Final results
            execution_time = time.time() - start_time
            
            click.echo(f"\n✅ Algorithm completed!")
            click.echo(f"Best fitness: {algo.best_fitness:.6f}")
            click.echo(f"Execution time: {execution_time:.2f} seconds")
            
            if export:
                export_path = monitor.export_current_metrics()
                click.echo(f"📊 Metrics exported to: {export_path}")
                
    except Exception as e:
        click.echo(f"❌ Error running algorithm: {e}", err=True)
        sys.exit(1)


@monitor.command()
@click.argument('metrics_file', type=click.Path(exists=True))
@click.option('--dashboard', type=click.Choice(['terminal', 'web']), 
              default='web', help='Dashboard type for replay')
@click.option('--speed', type=float, default=1.0, help='Replay speed multiplier')
@click.option('--port', type=int, default=8080, help='Web dashboard port')
def replay(metrics_file, dashboard, speed, port):
    """
    Replay metrics from exported file.
    
    Load previously exported metrics and replay them in the dashboard
    for analysis and visualization.
    
    Examples:
    
        # Replay in web dashboard
        bioalgo monitor replay metrics.json
        
        # Replay at 2x speed
        bioalgo monitor replay metrics.json --speed 2.0
    """
    import json
    from utils.monitoring import PerformanceMonitor, MetricsCollector
    
    click.echo(f"📼 Replaying metrics from {metrics_file}...")
    
    try:
        # Load metrics data
        with open(metrics_file) as f:
            data = json.load(f)
        
        if 'full_history' not in data:
            click.echo("❌ Invalid metrics file format", err=True)
            sys.exit(1)
        
        history = data['full_history']
        click.echo(f"📊 Loaded {len(history)} data points")
        
        # Create monitor with empty collector
        collector = MetricsCollector(enable_system_monitoring=False)
        
        if dashboard == 'web':
            from utils.monitoring import WebDashboard
            dashboard_obj = WebDashboard(collector, port=port)
            dashboard_obj.start()
            url = dashboard_obj.get_url()
            click.echo(f"🌐 Replay dashboard: {url}")
        else:
            from utils.monitoring import TerminalDashboard
            dashboard_obj = TerminalDashboard(collector)
            dashboard_obj.start()
        
        # Replay data
        click.echo("▶️  Starting replay (Press Ctrl+C to stop)...")
        
        try:
            for i, record in enumerate(history):
                # Update collector with historical data
                algo_data = record['algorithm']
                collector.algorithm_metrics.iteration = algo_data['iteration']
                collector.algorithm_metrics.current_fitness = algo_data['current_fitness']
                collector.algorithm_metrics.best_fitness = algo_data['best_fitness']
                collector.algorithm_metrics.population_diversity = algo_data['population_diversity']
                collector.algorithm_metrics.convergence_rate = algo_data['convergence_rate']
                collector.algorithm_metrics.elapsed_time = algo_data['elapsed_time']
                
                # System data
                sys_data = record['system']
                collector.system_metrics.cpu_percent = sys_data['cpu_percent']
                collector.system_metrics.memory_percent = sys_data['memory_percent']
                collector.system_metrics.memory_used_mb = sys_data['memory_used_mb']
                
                # Calculate sleep time based on speed
                if i < len(history) - 1:
                    time_diff = history[i + 1]['timestamp'] - record['timestamp']
                    sleep_time = time_diff / speed
                    time.sleep(max(0.1, sleep_time))  # Minimum 0.1s
                
                # Progress indicator
                if i % 10 == 0:
                    progress = (i + 1) / len(history) * 100
                    click.echo(f"\r🔄 Progress: {progress:.1f}%", nl=False)
            
            click.echo(f"\n✅ Replay completed!")
            
        except KeyboardInterrupt:
            click.echo(f"\n⏹️  Replay stopped")
        finally:
            dashboard_obj.stop()
            
    except Exception as e:
        click.echo(f"❌ Error replaying metrics: {e}", err=True)
        sys.exit(1)


@monitor.command()
@click.option('--output', '-o', type=click.Path(), help='Output file')
@click.option('--duration', type=int, default=60, help='Monitoring duration (seconds)')
@click.option('--interval', type=float, default=1.0, help='Collection interval')
def system(output, duration, interval):
    """
    Monitor system resources only.
    
    Collect and display system resource metrics (CPU, memory, etc.)
    without algorithm execution.
    
    Examples:
    
        # Monitor for 60 seconds
        bioalgo monitor system
        
        # Monitor and export
        bioalgo monitor system --output system_metrics.json --duration 120
    """
    from utils.monitoring import MetricsCollector
    import signal
    
    click.echo(f"💻 Monitoring system resources for {duration} seconds...")
    
    # Setup signal handler for graceful exit
    interrupted = False
    def signal_handler(sig, frame):
        nonlocal interrupted
        interrupted = True
    
    signal.signal(signal.SIGINT, signal_handler)
    
    try:
        with MetricsCollector(
            collection_interval=interval,
            enable_system_monitoring=True
        ) as collector:
            
            start_time = time.time()
            last_display = 0
            
            while not interrupted and (time.time() - start_time) < duration:
                current_time = time.time()
                
                # Display every 5 seconds
                if current_time - last_display >= 5:
                    sys_metrics = collector.system_metrics
                    elapsed = current_time - start_time
                    
                    click.echo(f"\r⏱️  {elapsed:.0f}s | "
                             f"CPU: {sys_metrics.cpu_percent:.1f}% | "
                             f"Memory: {sys_metrics.memory_percent:.1f}% | "
                             f"Processes: {sys_metrics.process_count}", nl=False)
                    
                    last_display = current_time
                
                time.sleep(0.5)
            
            click.echo("\n")  # New line after monitoring
            
            # Export if requested
            if output:
                data = collector.export_metrics()
                
                output_path = Path(output)
                if output_path.suffix.lower() == '.json':
                    import json
                    with open(output_path, 'w') as f:
                        json.dump(data, f, indent=2, default=str)
                else:
                    # Default to JSON
                    output_path = output_path.with_suffix('.json')
                    import json
                    with open(output_path, 'w') as f:
                        json.dump(data, f, indent=2, default=str)
                
                click.echo(f"📊 System metrics exported to: {output_path}")
            
            # Display summary
            final_metrics = collector.system_metrics
            click.echo(f"\n📋 Final System State:")
            click.echo(f"  CPU Usage: {final_metrics.cpu_percent:.1f}%")
            click.echo(f"  Memory Usage: {final_metrics.memory_percent:.1f}%")
            click.echo(f"  Memory Used: {final_metrics.memory_used_mb:.0f} MB")
            click.echo(f"  Active Processes: {final_metrics.process_count}")
            
            if final_metrics.temperature:
                click.echo(f"  CPU Temperature: {final_metrics.temperature:.1f}°C")
                
    except Exception as e:
        click.echo(f"❌ Error monitoring system: {e}", err=True)
        sys.exit(1)


@monitor.command()
@click.argument('metrics_file', type=click.Path(exists=True))
@click.option('--format', type=click.Choice(['text', 'json']), default='text')
@click.option('--metric', help='Specific metric to analyze')
def analyze(metrics_file, format, metric):
    """
    Analyze exported metrics file.
    
    Load and analyze metrics data, showing statistics and insights
    about algorithm performance and system resource usage.
    
    Examples:
    
        # Analyze metrics file
        bioalgo monitor analyze metrics.json
        
        # Analyze specific metric
        bioalgo monitor analyze metrics.json --metric fitness
        
        # JSON output
        bioalgo monitor analyze metrics.json --format json
    """
    import json
    import statistics
    
    click.echo(f"📊 Analyzing metrics from {metrics_file}...")
    
    try:
        with open(metrics_file) as f:
            data = json.load(f)
        
        # Basic info
        metadata = data.get('metadata', {})
        click.echo(f"\n📋 Metrics Summary:")
        click.echo(f"  Duration: {metadata.get('duration', 0):.2f} seconds")
        click.echo(f"  Total Samples: {metadata.get('total_samples', 0)}")
        click.echo(f"  Collection Rate: {metadata.get('total_samples', 0) / max(metadata.get('duration', 1), 1):.2f} samples/sec")
        
        # Time series analysis
        time_series = data.get('time_series', {})
        
        if metric:
            # Analyze specific metric
            if metric in time_series:
                values = [v for _, v in time_series[metric]]
                if values:
                    if format == 'json':
                        analysis = {
                            'metric': metric,
                            'count': len(values),
                            'min': min(values),
                            'max': max(values),
                            'mean': statistics.mean(values),
                            'median': statistics.median(values),
                            'stdev': statistics.stdev(values) if len(values) > 1 else 0
                        }
                        click.echo(json.dumps(analysis, indent=2))
                    else:
                        click.echo(f"\n📈 {metric.title()} Analysis:")
                        click.echo(f"  Count: {len(values)}")
                        click.echo(f"  Min: {min(values):.6f}")
                        click.echo(f"  Max: {max(values):.6f}")
                        click.echo(f"  Mean: {statistics.mean(values):.6f}")
                        click.echo(f"  Median: {statistics.median(values):.6f}")
                        if len(values) > 1:
                            click.echo(f"  Std Dev: {statistics.stdev(values):.6f}")
                else:
                    click.echo(f"❌ No data for metric: {metric}")
            else:
                click.echo(f"❌ Metric not found: {metric}")
                click.echo(f"Available metrics: {', '.join(time_series.keys())}")
        else:
            # Analyze all metrics
            analysis_results = {}
            
            for metric_name, metric_data in time_series.items():
                if metric_data:
                    values = [v for _, v in metric_data]
                    if values:
                        stats = {
                            'count': len(values),
                            'min': min(values),
                            'max': max(values),
                            'mean': statistics.mean(values),
                            'median': statistics.median(values),
                            'stdev': statistics.stdev(values) if len(values) > 1 else 0
                        }
                        analysis_results[metric_name] = stats
            
            if format == 'json':
                click.echo(json.dumps(analysis_results, indent=2))
            else:
                for metric_name, stats in analysis_results.items():
                    click.echo(f"\n📈 {metric_name.title()}:")
                    click.echo(f"  Count: {stats['count']}")
                    click.echo(f"  Range: {stats['min']:.4f} - {stats['max']:.4f}")
                    click.echo(f"  Mean: {stats['mean']:.4f}")
                    click.echo(f"  Std Dev: {stats['stdev']:.4f}")
        
        # Current state
        current = data.get('current_metrics', {})
        if current and format == 'text':
            click.echo(f"\n🎯 Final State:")
            algo = current.get('algorithm', {})
            sys_info = current.get('system', {})
            
            if algo:
                click.echo(f"  Best Fitness: {algo.get('best_fitness', 'N/A')}")
                click.echo(f"  Iterations: {algo.get('iteration', 'N/A')}")
                click.echo(f"  Diversity: {algo.get('population_diversity', 'N/A')}")
            
            if sys_info:
                click.echo(f"  CPU: {sys_info.get('cpu_percent', 'N/A'):.1f}%")
                click.echo(f"  Memory: {sys_info.get('memory_percent', 'N/A'):.1f}%")
                
    except Exception as e:
        click.echo(f"❌ Error analyzing metrics: {e}", err=True)
        sys.exit(1)