#!/usr/bin/env python3
"""
Unified benchmark command for BioAlgoCompare.

This command consolidates all benchmarking functionality including:
- Standard benchmarking
- Benchmarking with metadata
- Analysis of existing results
- Report generation
"""

import click
import os
import sys
from pathlib import Path
from datetime import datetime
import json

# Import benchmarking utilities
from utils.benchmarking import (
    BenchmarkRunner,
    BenchmarkResult,
    BenchmarkVisualizer,
    OPTIMAL_VALUES,
    load_benchmark_results
)
from utils.benchmarking_v2 import MetadataEnhancedBenchmark

# Import algorithms
from algorithms.hoa_v2 import HOAV2
from algorithms.apo_v2 import APOV2
from algorithms.egto_v2 import EGTOV2
from algorithms.fsa_v2 import FSAV2
from algorithms.foa_v2 import FOAV2
from algorithms.woa_v2 import WOAV2
from algorithms.hho_v2 import HHOV2
from algorithms.mrfo_v2 import MRFOV2
from algorithms.sma_v2 import SMAV2
from algorithms.gto_v2 import GTOV2
from algorithms.ewa_v2 import EWAV2
from algorithms.aha_v2 import AHAV2
from algorithms.rro_v2 import RROV2
from algorithms.gvoa_v2 import GVOAV2
from algorithms.smo_v2 import SMOV2
from algorithms.opa_v2 import OPAV2
from algorithms.fgo_v2 import FGOV2
from algorithms.sho_v2 import SHOV2

# Algorithm mapping
ALGORITHMS_V2 = {
    "hoa": HOAV2, "apo": APOV2, "egto": EGTOV2, "fsa": FSAV2,
    "foa": FOAV2, "woa": WOAV2, "hho": HHOV2, "mrfo": MRFOV2,
    "sma": SMAV2, "gto": GTOV2, "ewa": EWAV2, "aha": AHAV2,
    "rro": RROV2, "gvoa": GVOAV2, "smo": SMOV2, "opa": OPAV2,
    "fgo": FGOV2, "sho": SHOV2,
}

# Predefined instance sets
INSTANCE_SETS = {
    "tiny": ["P-n16-k8", "E-n22-k4"],
    "small": ["P-n16-k8", "E-n22-k4", "A-n32-k5"],
    "medium": ["A-n45-k7", "B-n50-k7", "E-n51-k5"],
    "large": ["A-n60-k9", "B-n78-k10", "E-n101-k8"],
    "standard": ["P-n16-k8", "E-n22-k4", "A-n32-k5", "A-n45-k7", "B-n50-k7"],
    "all": ["P-n16-k8", "E-n22-k4", "A-n32-k5", "A-n45-k7", "B-n50-k7", 
            "E-n51-k5", "A-n60-k9", "B-n78-k10", "E-n101-k8"]
}


@click.command()
# Mode selection
@click.option('--mode', 
              type=click.Choice(['run', 'analyze', 'compare']), 
              default='run',
              help='Benchmark mode: run new benchmark, analyze results, or compare algorithms')
# Algorithm selection
@click.option('--algorithms', '-a',
              type=str,
              help='Algorithms to benchmark (comma-separated or "all")')
@click.option('--exclude', '-e',
              type=str,
              help='Algorithms to exclude (comma-separated)')
# Instance selection
@click.option('--instances', '-i',
              type=str,
              help='Instances to use (comma-separated or predefined set: tiny/small/medium/large/standard/all)')
# Run configuration
@click.option('--runs', '-r',
              default=30,
              type=int,
              help='Number of runs per algorithm/instance pair')
@click.option('--iterations', '-n',
              default=100,
              type=int,
              help='Maximum iterations per run')
@click.option('--population', '-p',
              default=30,
              type=int,
              help='Population size')
@click.option('--seed', '-s',
              default=42,
              type=int,
              help='Base random seed')
# Execution options
@click.option('--parallel/--no-parallel',
              default=True,
              help='Use parallel execution')
@click.option('--workers', '-w',
              type=int,
              help='Number of parallel workers')
@click.option('--timeout',
              default=300,
              type=int,
              help='Timeout per task in seconds')
# Checkpoint options
@click.option('--checkpoint-interval',
              default=50,
              type=int,
              help='Save checkpoint every N tasks')
@click.option('--resume/--no-resume',
              default=True,
              help='Resume from checkpoint if available')
# Metadata options
@click.option('--metadata/--no-metadata',
              default=True,
              help='Capture system metadata')
@click.option('--monitor/--no-monitor',
              default=False,
              help='Monitor resource usage')
# Output options
@click.option('--output-dir', '-o',
              type=str,
              help='Output directory (auto-generated if not specified)')
@click.option('--formats',
              type=str,
              default='json,csv',
              help='Output formats (comma-separated: json,csv,pickle,html)')
# Analysis options
@click.option('--input', '-f',
              type=str,
              help='Input file for analyze mode')
@click.option('--statistical/--no-statistical',
              default=True,
              help='Perform statistical analysis')
@click.option('--report/--no-report',
              default=True,
              help='Generate HTML report')
# Verbosity
@click.option('--verbose', '-v',
              count=True,
              help='Increase verbosity')
@click.option('--quiet', '-q',
              is_flag=True,
              help='Suppress output')
def benchmark(mode, algorithms, exclude, instances, runs, iterations, population,
             seed, parallel, workers, timeout, checkpoint_interval, resume,
             metadata, monitor, output_dir, formats, input, statistical,
             report, verbose, quiet):
    """
    Run comprehensive benchmarks for bio-inspired algorithms.
    
    This command provides complete benchmarking functionality with support for
    parallel execution, checkpointing, metadata capture, and statistical analysis.
    
    Examples:
    
        # Run benchmark on small instances
        bioalgo benchmark -a "hoa,egto,foa" -i small
        
        # Run all algorithms on specific instances
        bioalgo benchmark -a all -i "P-n16-k8,E-n22-k4" -r 100
        
        # Analyze existing results
        bioalgo benchmark --mode analyze --input results/benchmark_20240115.json
        
        # Compare specific algorithms
        bioalgo benchmark --mode compare -a "hoa,egto" -i standard --statistical
    """
    
    # Set verbosity
    if quiet:
        verbose = -1
    
    if mode == 'analyze':
        # Analyze existing results
        if not input:
            click.echo("❌ Error: --input required for analyze mode", err=True)
            return
        
        analyze_results(input, output_dir, statistical, report, verbose)
        return
    
    # Parse algorithms
    if not algorithms:
        if mode == 'compare':
            click.echo("❌ Error: --algorithms required for compare mode", err=True)
            return
        algorithms = "hoa,egto,foa,ewa,sma"  # Default set
    
    if algorithms.lower() == 'all':
        algo_list = list(ALGORITHMS_V2.keys())
    else:
        algo_list = [a.strip() for a in algorithms.split(',') if a.strip()]
    
    # Handle exclusions
    if exclude:
        exclude_list = [e.strip() for e in exclude.split(',')]
        algo_list = [a for a in algo_list if a not in exclude_list]
    
    # Validate algorithms
    invalid_algos = [a for a in algo_list if a not in ALGORITHMS_V2]
    if invalid_algos:
        click.echo(f"❌ Error: Unknown algorithms: {', '.join(invalid_algos)}", err=True)
        click.echo(f"Available: {', '.join(sorted(ALGORITHMS_V2.keys()))}", err=True)
        return
    
    # Parse instances
    if not instances:
        instances = "small"  # Default set
    
    if instances.lower() in INSTANCE_SETS:
        instance_list = INSTANCE_SETS[instances.lower()]
    else:
        instance_list = [i.strip() for i in instances.split(',') if i.strip()]
    
    # Validate instances
    for inst in instance_list:
        inst_path = Path(f"data/vrp/{inst}.vrp")
        if not inst_path.exists():
            inst_path = Path(f"data/vrp/{inst}")
            if not inst_path.exists():
                click.echo(f"❌ Error: Instance '{inst}' not found", err=True)
                return
    
    # Configure output directory
    if output_dir is None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_dir = f"results/benchmark_{timestamp}"
    
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    
    # Configure workers
    if workers is None:
        import multiprocessing as mp
        workers = max(1, mp.cpu_count() - 1) if parallel else 1
    
    # Show configuration
    if verbose >= 0:
        click.echo(f"🚀 Starting benchmark")
        click.echo(f"📊 Configuration:")
        click.echo(f"  Mode: {mode}")
        click.echo(f"  Algorithms: {len(algo_list)} ({', '.join(algo_list[:3])}{'...' if len(algo_list) > 3 else ''})")
        click.echo(f"  Instances: {len(instance_list)} ({', '.join(instance_list[:3])}{'...' if len(instance_list) > 3 else ''})")
        click.echo(f"  Runs per pair: {runs}")
        click.echo(f"  Total tasks: {len(algo_list) * len(instance_list) * runs}")
        if parallel:
            click.echo(f"  Workers: {workers}")
        if metadata:
            click.echo(f"  Metadata capture: ✓")
        click.echo(f"  Output: {output_dir}")
    
    # Save configuration
    config = {
        "timestamp": datetime.now().isoformat(),
        "mode": mode,
        "algorithms": algo_list,
        "instances": instance_list,
        "runs": runs,
        "iterations": iterations,
        "population": population,
        "seed": seed,
        "parallel": parallel,
        "workers": workers if parallel else 1,
        "metadata": metadata,
        "monitor": monitor,
        "checkpoint_interval": checkpoint_interval
    }
    
    config_file = Path(output_dir) / "benchmark_config.json"
    with open(config_file, 'w') as f:
        json.dump(config, f, indent=2)
    
    # Get algorithm classes
    algorithm_classes = [ALGORITHMS_V2[a] for a in algo_list]
    
    # Create benchmark runner
    if metadata or monitor:
        # Use enhanced benchmark with metadata
        runner = MetadataEnhancedBenchmark(
            algorithms=algorithm_classes,
            instances=instance_list,
            runs_per_instance=runs,
            population_size=population,
            max_iterations=iterations,
            capture_metadata=metadata,
            monitor_resources=monitor,
            parallel=parallel,
            n_workers=workers,
            checkpoint_interval=checkpoint_interval,
            timeout=timeout,
            output_dir=output_dir
        )
    else:
        # Use standard benchmark
        runner = BenchmarkRunner(
            output_dir=output_dir,
            parallel=parallel,
            checkpoint_interval=checkpoint_interval,
            verbose=verbose >= 1
        )
    
    # Run benchmark
    if verbose >= 0:
        click.echo("\n⏳ Running benchmark...")
    
    try:
        if metadata or monitor:
            results = runner.run_benchmark(resume=resume)
            output_formats = [f.strip() for f in formats.split(',')]
            runner.save_results(results, formats=output_formats)
        else:
            # Prepare algorithm dictionary
            algo_dict = {name: ALGORITHMS_V2[name] for name in algo_list}
            
            results = runner.run_benchmark(
                algorithms=algo_dict,
                instances=instance_list,
                runs=runs,
                iterations=iterations,
                population=population,
                seed=seed,
                resume=resume
            )
            
            # Save results
            output_formats = [f.strip() for f in formats.split(',')]
            runner.save_results(results, formats=output_formats)
        
        # Show summary
        if verbose >= 0 and results:
            show_benchmark_summary(results, verbose)
        
        # Generate report if requested
        if report:
            if verbose >= 0:
                click.echo("\n📝 Generating report...")
            
            visualizer = BenchmarkVisualizer()
            report_path = visualizer.create_comprehensive_report(
                results,
                Path(output_dir),
                include_stats=statistical
            )
            
            if verbose >= 0:
                click.echo(f"📊 Report generated: {report_path}")
        
        if verbose >= 0:
            click.echo(f"\n✅ Benchmark completed successfully!")
            click.echo(f"📁 Results saved in: {output_dir}")
        
    except KeyboardInterrupt:
        click.echo("\n⚠️  Benchmark interrupted by user", err=True)
        if verbose >= 0:
            click.echo(f"Partial results saved in: {output_dir}")
    except Exception as e:
        click.echo(f"\n❌ Error during benchmark: {str(e)}", err=True)
        if verbose >= 2:
            import traceback
            traceback.print_exc()


def analyze_results(input_file, output_dir, statistical, report, verbose):
    """Analyze existing benchmark results."""
    if verbose >= 0:
        click.echo(f"📊 Analyzing results from: {input_file}")
    
    # Load results
    try:
        results = load_benchmark_results(input_file)
    except Exception as e:
        click.echo(f"❌ Error loading results: {str(e)}", err=True)
        return
    
    if not results:
        click.echo("❌ No results found in file", err=True)
        return
    
    # Configure output directory
    if output_dir is None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_dir = f"results/analysis_{timestamp}"
    
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    
    # Show summary
    if verbose >= 0:
        show_benchmark_summary(results, verbose)
    
    # Perform statistical analysis
    if statistical:
        if verbose >= 0:
            click.echo("\n📈 Performing statistical analysis...")
        
        from utils.statistics import UnifiedStatisticalAnalysis
        analyzer = UnifiedStatisticalAnalysis()
        
        # Prepare data for analysis
        summary_df = BenchmarkRunner.create_summary_dataframe(results)
        
        # Run analysis
        if len(summary_df['Algorithm'].unique()) >= 2:
            pivot_df = summary_df.pivot(
                index='Instance',
                columns='Algorithm',
                values='Mean'
            )
            
            analysis_result = analyzer.run_comprehensive_analysis(pivot_df)
            
            # Save analysis results
            analysis_file = Path(output_dir) / "statistical_analysis.json"
            with open(analysis_file, 'w') as f:
                json.dump(analysis_result.to_dict(), f, indent=2, default=str)
            
            if verbose >= 0:
                click.echo(f"📊 Statistical analysis saved: {analysis_file}")
        else:
            if verbose >= 0:
                click.echo("⚠️  Need at least 2 algorithms for statistical comparison")
    
    # Generate report
    if report:
        if verbose >= 0:
            click.echo("\n📝 Generating report...")
        
        visualizer = BenchmarkVisualizer()
        report_path = visualizer.create_comprehensive_report(
            results,
            Path(output_dir),
            include_stats=statistical
        )
        
        if verbose >= 0:
            click.echo(f"📊 Report generated: {report_path}")
    
    if verbose >= 0:
        click.echo(f"\n✅ Analysis completed!")
        click.echo(f"📁 Results saved in: {output_dir}")


def show_benchmark_summary(results, verbose):
    """Show summary of benchmark results."""
    click.echo("\n📊 Benchmark Summary:")
    
    # Count statistics
    total_runs = sum(r.runs for r in results)
    algorithms = list(set(r.algorithm_name for r in results))
    instances = list(set(r.instance_name for r in results))
    
    click.echo(f"  Total runs: {total_runs}")
    click.echo(f"  Algorithms: {len(algorithms)}")
    click.echo(f"  Instances: {len(instances)}")
    
    if verbose >= 1:
        # Best results per instance
        click.echo("\n🏆 Best Results per Instance:")
        instance_bests = {}
        
        for result in results:
            if result.instance_name not in instance_bests:
                instance_bests[result.instance_name] = []
            
            if result.best_fitness:
                instance_bests[result.instance_name].append(
                    (result.algorithm_name, result.best_fitness, result.gap_to_optimal)
                )
        
        for instance in sorted(instance_bests.keys()):
            if instance_bests[instance]:
                best = min(instance_bests[instance], key=lambda x: x[1])
                algo, fitness, gap = best
                
                optimal = OPTIMAL_VALUES.get(instance)
                if optimal:
                    gap_str = f" (gap: {gap:.2f}%)" if gap else ""
                    click.echo(f"  {instance}: {algo} = {fitness:.2f}{gap_str} [optimal: {optimal}]")
                else:
                    click.echo(f"  {instance}: {algo} = {fitness:.2f}")
    
    if verbose >= 2:
        # Algorithm rankings
        click.echo("\n📈 Algorithm Rankings (by mean fitness):")
        
        algo_stats = {}
        for result in results:
            if result.algorithm_name not in algo_stats:
                algo_stats[result.algorithm_name] = []
            if result.mean_fitness:
                algo_stats[result.algorithm_name].append(result.mean_fitness)
        
        rankings = []
        for algo, values in algo_stats.items():
            if values:
                import numpy as np
                rankings.append((algo, np.mean(values)))
        
        rankings.sort(key=lambda x: x[1])
        
        for i, (algo, mean_fitness) in enumerate(rankings, 1):
            click.echo(f"  {i}. {algo}: {mean_fitness:.2f}")


if __name__ == '__main__':
    benchmark()