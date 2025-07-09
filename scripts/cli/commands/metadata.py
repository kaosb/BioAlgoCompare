"""
Comandos CLI para gestión de metadatos y trazabilidad experimental.
"""

import click
import json
from pathlib import Path
from datetime import datetime
from typing import Optional, List
import pandas as pd

from utils.metadata.metadata_manager import MetadataManager, MetadataLevel
from utils.metadata.traceability import TraceabilityDB, EventType
from algorithms import ALGORITHMS
from problems.vrp import VRPProblem


@click.group()
def metadata():
    """Metadata and experimental traceability management."""
    pass


@metadata.command()
@click.option('--experiment', '-e', help='Specific experiment ID')
@click.option('--algorithm', '-a', help='Filter by algorithm')
@click.option('--problem', '-p', help='Filter by problem instance')
@click.option('--date-from', help='Start date (YYYY-MM-DD)')
@click.option('--date-to', help='End date (YYYY-MM-DD)')
@click.option('--tags', multiple=True, help='Filter by tags')
@click.option('--format', type=click.Choice(['table', 'json', 'detailed']), 
              default='table', help='Output format')
def list(experiment, algorithm, problem, date_from, date_to, tags, format):
    """
    List experiments with their metadata.
    
    Examples:
    
        # List all experiments
        bioalgo metadata list
        
        # List experiments for specific algorithm
        bioalgo metadata list -a HOA
        
        # List experiments from last week
        bioalgo metadata list --date-from 2024-01-01
        
        # List with specific tags
        bioalgo metadata list --tags benchmark --tags published
    """
    manager = MetadataManager()
    
    # Parse dates if provided
    from_date = datetime.fromisoformat(date_from) if date_from else None
    to_date = datetime.fromisoformat(date_to) if date_to else None
    
    # Search experiments
    experiments = manager.search_experiments(
        algorithm=algorithm,
        problem=problem,
        tags=list(tags) if tags else None,
        date_from=from_date,
        date_to=to_date
    )
    
    if experiment:
        # Filter by specific experiment
        experiments = [e for e in experiments if experiment in e.get('experiment_id', '')]
    
    if not experiments:
        click.echo("No experiments found matching criteria")
        return
    
    if format == 'json':
        click.echo(json.dumps(experiments, indent=2, default=str))
    
    elif format == 'detailed':
        for exp in experiments:
            click.echo(f"\n{'='*60}")
            click.echo(f"Experiment: {exp['experiment_id']}")
            click.echo(f"{'='*60}")
            _print_experiment_details(exp)
    
    else:  # table
        # Create DataFrame for nice table display
        data = []
        for exp in experiments:
            data.append({
                'ID': exp['experiment_id'][:20] + '...' if len(exp['experiment_id']) > 20 else exp['experiment_id'],
                'Algorithm': exp['algorithm']['name'],
                'Problem': exp['problem']['instance'],
                'Best Fitness': exp['result']['best_fitness'] if exp.get('result') else 'N/A',
                'Duration': f"{exp['execution'].get('duration_seconds', 0):.1f}s",
                'Timestamp': exp['system']['timestamp'][:19]
            })
        
        df = pd.DataFrame(data)
        click.echo(df.to_string(index=False))
        click.echo(f"\nTotal experiments: {len(experiments)}")


@metadata.command()
@click.argument('experiment_id')
@click.option('--level', type=click.Choice(['minimal', 'standard', 'detailed', 'complete']),
              default='standard', help='Level of detail')
@click.option('--output', '-o', type=click.Path(), help='Save to file')
def show(experiment_id, level, output):
    """
    Show detailed metadata for an experiment.
    
    Examples:
    
        # Show standard metadata
        bioalgo metadata show HOA_E-n22-k4_abc123
        
        # Show complete metadata
        bioalgo metadata show HOA_E-n22-k4_abc123 --level complete
        
        # Save to file
        bioalgo metadata show HOA_E-n22-k4_abc123 -o experiment.json
    """
    manager = MetadataManager()
    
    try:
        experiment = manager.load_experiment(experiment_id)
        
        # Convert level string to enum
        from utils.metadata.metadata_manager import MetadataLevel
        level_enum = MetadataLevel[level.upper()]
        
        # Filter by level (simplified version)
        if level == 'minimal':
            filtered = {
                'experiment_id': experiment['experiment_id'],
                'algorithm': experiment['algorithm']['name'],
                'problem': experiment['problem']['instance'],
                'best_fitness': experiment.get('result', {}).get('best_fitness'),
                'timestamp': experiment['system']['timestamp']
            }
        else:
            filtered = experiment
        
        # Output
        output_text = json.dumps(filtered, indent=2, default=str)
        
        if output:
            Path(output).write_text(output_text)
            click.echo(f"Metadata saved to {output}")
        else:
            click.echo(output_text)
            
    except FileNotFoundError:
        click.echo(f"Experiment {experiment_id} not found", err=True)
    except Exception as e:
        click.echo(f"Error loading experiment: {e}", err=True)


@metadata.command()
@click.argument('experiment_id')
@click.option('--event-type', help='Filter by event type')
@click.option('--component', help='Filter by component')
@click.option('--limit', type=int, default=100, help='Limit number of events')
@click.option('--format', type=click.Choice(['timeline', 'json', 'summary']),
              default='timeline', help='Output format')
def trace(experiment_id, event_type, component, limit, format):
    """
    Show traceability timeline for an experiment.
    
    Examples:
    
        # Show timeline of events
        bioalgo metadata trace HOA_E-n22-k4_abc123
        
        # Show only errors
        bioalgo metadata trace HOA_E-n22-k4_abc123 --event-type ERROR_OCCURRED
        
        # Show summary
        bioalgo metadata trace HOA_E-n22-k4_abc123 --format summary
    """
    db = TraceabilityDB(Path("traceability.db"))
    
    # Get events
    event_type_enum = EventType[event_type] if event_type else None
    events = db.get_events(
        experiment_id=experiment_id,
        event_type=event_type_enum,
        component=component,
        limit=limit
    )
    
    if not events:
        click.echo("No events found for this experiment")
        return
    
    if format == 'json':
        click.echo(json.dumps([e.to_dict() for e in events], indent=2))
    
    elif format == 'summary':
        # Event count by type
        event_counts = {}
        for event in events:
            event_type = event.event_type.value
            event_counts[event_type] = event_counts.get(event_type, 0) + 1
        
        click.echo(f"\nEvent Summary for {experiment_id}")
        click.echo("="*50)
        for event_type, count in sorted(event_counts.items()):
            click.echo(f"{event_type:30} {count:>10}")
        click.echo(f"{'TOTAL':30} {len(events):>10}")
    
    else:  # timeline
        click.echo(f"\nTimeline for {experiment_id}")
        click.echo("="*80)
        
        for event in events:
            timestamp = event.timestamp[11:19]  # Just time
            event_type = event.event_type.value
            
            # Color coding
            if 'ERROR' in event_type:
                marker = click.style('●', fg='red')
            elif 'WARNING' in event_type:
                marker = click.style('●', fg='yellow')
            elif 'SOLUTION' in event_type:
                marker = click.style('●', fg='green')
            else:
                marker = '○'
            
            # Format summary
            if event.event_type == EventType.SOLUTION_FOUND:
                summary = f"Found solution: fitness={event.data.get('fitness', 'N/A')}"
            elif event.event_type == EventType.ERROR_OCCURRED:
                summary = f"Error: {event.data.get('error_type', 'Unknown')}"
            elif event.event_type == EventType.ITERATION_END:
                summary = f"Iteration {event.data.get('iteration', 'N/A')}"
            else:
                summary = event.event_type.value.replace('_', ' ').lower()
            
            click.echo(f"{timestamp} {marker} [{event.component:15}] {summary}")


@metadata.command()
@click.argument('experiment_id')
@click.option('--output', '-o', default='audit_report.md', help='Output file')
@click.option('--verify-integrity', is_flag=True, help='Include integrity verification')
def audit(experiment_id, output, verify_integrity):
    """
    Generate audit report for an experiment.
    
    Examples:
    
        # Generate basic audit report
        bioalgo metadata audit HOA_E-n22-k4_abc123
        
        # Include integrity verification
        bioalgo metadata audit HOA_E-n22-k4_abc123 --verify-integrity
    """
    from utils.metadata.traceability import ExperimentTracer
    
    manager = MetadataManager()
    tracer = ExperimentTracer(manager)
    
    click.echo(f"Generating audit report for {experiment_id}...")
    
    try:
        report = tracer.generate_audit_report(
            experiment_id,
            include_integrity_check=verify_integrity
        )
        
        Path(output).write_text(report)
        click.echo(f"✅ Audit report saved to {output}")
        
        # Show summary
        if verify_integrity:
            if "✅ All events passed integrity check" in report:
                click.echo("✅ Integrity verification: PASSED")
            else:
                click.echo("❌ Integrity verification: FAILED")
                
    except Exception as e:
        click.echo(f"Error generating report: {e}", err=True)


@metadata.command()
@click.option('--algorithm', '-a', required=True, help='Algorithm to run')
@click.option('--instance', '-i', required=True, help='Problem instance')
@click.option('--iterations', type=int, default=100, help='Max iterations')
@click.option('--population', type=int, default=30, help='Population size')
@click.option('--seed', type=int, default=42, help='Random seed')
@click.option('--trace-level', type=click.Choice(['minimal', 'standard', 'detailed']),
              default='standard', help='Tracing detail level')
@click.option('--metadata-level', type=click.Choice(['minimal', 'standard', 'detailed', 'complete']),
              default='standard', help='Metadata detail level')
@click.option('--tags', multiple=True, help='Tags for the experiment')
def track(algorithm, instance, iterations, population, seed, trace_level, metadata_level, tags):
    """
    Run algorithm with full metadata tracking.
    
    Examples:
    
        # Run with standard tracking
        bioalgo metadata track -a HOA -i E-n22-k4
        
        # Run with detailed tracking and tags
        bioalgo metadata track -a FOA -i P-n16-k8 --trace-level detailed --tags test --tags debug
    """
    from utils.metadata.algorithm_integration import create_tracked_algorithm
    from utils.metadata.metadata_manager import MetadataLevel
    
    click.echo(f"🔬 Running {algorithm} on {instance} with metadata tracking...")
    
    try:
        # Load problem
        problem = VRPProblem(instance)
        
        # Create tracked algorithm
        algo = create_tracked_algorithm(
            algorithm,
            problem,
            population_size=population,
            max_iterations=iterations,
            seed=seed,
            metadata_config={
                'enable': True,
                'level': MetadataLevel[metadata_level.upper()],
                'trace_level': trace_level
            }
        )
        
        # Add tags to metadata
        if tags and hasattr(algo, '_experiment_metadata'):
            algo._experiment_metadata.tags.extend(list(tags))
        
        # Run algorithm
        start_time = datetime.now()
        result = algo.run()
        end_time = datetime.now()
        
        # Display results
        click.echo(f"\n✅ Experiment completed!")
        click.echo(f"Experiment ID: {algo._experiment_metadata.experiment_id}")
        click.echo(f"Best fitness: {result['best_fitness']:.4f}")
        click.echo(f"Duration: {(end_time - start_time).total_seconds():.2f}s")
        
        # Show where metadata is saved
        metadata_file = Path("metadata") / f"{algo._experiment_metadata.experiment_id}_metadata.json"
        if metadata_file.exists():
            click.echo(f"\n📊 Metadata saved to: {metadata_file}")
            
            # Show brief summary
            click.echo("\nMetadata summary:")
            with open(metadata_file) as f:
                meta = json.load(f)
                click.echo(f"- System: {meta['system']['platform']['system']} {meta['system']['platform']['release']}")
                click.echo(f"- Python: {meta['system']['platform']['python_version']}")
                click.echo(f"- Iterations: {meta['execution']['iterations_completed']}")
                if meta.get('result'):
                    indicators = meta['result'].get('quality_indicators', {})
                    if 'gap_to_optimal' in indicators:
                        click.echo(f"- Gap to optimal: {indicators['gap_to_optimal']:.2f}%")
        
    except Exception as e:
        click.echo(f"❌ Error: {e}", err=True)
        raise


@metadata.command()
@click.option('--days', type=int, default=30, help='Clean metadata older than N days')
@click.option('--dry-run', is_flag=True, help='Show what would be deleted')
def clean(days, dry_run):
    """
    Clean old metadata files.
    
    Examples:
    
        # Show what would be deleted (older than 30 days)
        bioalgo metadata clean --dry-run
        
        # Clean metadata older than 7 days
        bioalgo metadata clean --days 7
    """
    from datetime import timedelta
    
    metadata_dir = Path("metadata")
    if not metadata_dir.exists():
        click.echo("No metadata directory found")
        return
    
    cutoff_date = datetime.now() - timedelta(days=days)
    files_to_delete = []
    total_size = 0
    
    for meta_file in metadata_dir.glob("*.json"):
        # Check file modification time
        mtime = datetime.fromtimestamp(meta_file.stat().st_mtime)
        if mtime < cutoff_date:
            files_to_delete.append(meta_file)
            total_size += meta_file.stat().st_size
    
    if not files_to_delete:
        click.echo(f"No metadata files older than {days} days found")
        return
    
    click.echo(f"Found {len(files_to_delete)} files to clean")
    click.echo(f"Total size: {total_size / 1024 / 1024:.2f} MB")
    
    if dry_run:
        click.echo("\nFiles that would be deleted:")
        for f in files_to_delete[:10]:
            click.echo(f"  - {f.name}")
        if len(files_to_delete) > 10:
            click.echo(f"  ... and {len(files_to_delete) - 10} more")
    else:
        if click.confirm(f"Delete {len(files_to_delete)} files?"):
            for f in files_to_delete:
                f.unlink()
            click.echo(f"✅ Deleted {len(files_to_delete)} files")


@metadata.command()
@click.argument('experiment_ids', nargs=-1, required=True)
@click.option('--output', '-o', default='traceability_report.md', help='Output file')
def report(experiment_ids, output):
    """
    Generate traceability report for multiple experiments.
    
    Examples:
    
        # Report for specific experiments
        bioalgo metadata report exp1 exp2 exp3
        
        # Save to custom file
        bioalgo metadata report exp1 exp2 -o my_report.md
    """
    manager = MetadataManager()
    
    click.echo(f"Generating traceability report for {len(experiment_ids)} experiments...")
    
    try:
        report = manager.generate_traceability_report(
            list(experiment_ids),
            output_path=Path(output)
        )
        
        click.echo(f"✅ Report saved to {output}")
        
        # Show summary
        successful = report.count("## Experiment:")
        errors = report.count("Error loading experiment")
        
        click.echo(f"\nSummary:")
        click.echo(f"- Successful: {successful}")
        click.echo(f"- Errors: {errors}")
        
    except Exception as e:
        click.echo(f"Error generating report: {e}", err=True)


def _print_experiment_details(exp: dict):
    """Helper to print experiment details."""
    # System info
    click.echo("\nSystem Information:")
    click.echo(f"  Host: {exp['system']['hostname']}")
    click.echo(f"  User: {exp['system']['username']}")
    click.echo(f"  Platform: {exp['system']['platform']['system']} {exp['system']['platform']['release']}")
    
    # Algorithm info
    click.echo("\nAlgorithm Configuration:")
    click.echo(f"  Name: {exp['algorithm']['name']} v{exp['algorithm']['version']}")
    click.echo(f"  Seed: {exp['algorithm']['random_seed']}")
    click.echo("  Parameters:")
    for k, v in exp['algorithm']['parameters'].items():
        click.echo(f"    {k}: {v}")
    
    # Execution info
    click.echo("\nExecution Details:")
    click.echo(f"  Start: {exp['execution']['start_time']}")
    click.echo(f"  End: {exp['execution'].get('end_time', 'N/A')}")
    click.echo(f"  Duration: {exp['execution'].get('duration_seconds', 0):.2f}s")
    click.echo(f"  Iterations: {exp['execution']['iterations_completed']}")
    
    # Results
    if exp.get('result'):
        click.echo("\nResults:")
        click.echo(f"  Best Fitness: {exp['result']['best_fitness']}")
        if exp['result'].get('quality_indicators'):
            click.echo("  Quality Indicators:")
            for k, v in exp['result']['quality_indicators'].items():
                click.echo(f"    {k}: {v:.4f}")