#!/usr/bin/env python3
"""
Enhanced benchmarking script with complete metadata capture.

This script extends the standard benchmarking functionality to ensure all results
include complete system metadata for reproducibility.
"""

import click
import os
import sys
from pathlib import Path
from datetime import datetime
import json

# Add project root to Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

# Import enhanced benchmarking
from utils.benchmarking_v2 import (
    MetadataEnhancedBenchmark,
    run_benchmark_with_metadata
)

# Import v2 algorithms
from algorithms.sho_v2 import SHOV2
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
from algorithms.hoa_v2 import HOAV2
from algorithms.fgo_v2 import FGOV2

# Algorithm mapping
ALGORITHMS_V2 = {
    "sho": SHOV2,
    "apo": APOV2,
    "egto": EGTOV2,
    "fsa": FSAV2,
    "foa": FOAV2,
    "woa": WOAV2,
    "hho": HHOV2,
    "mrfo": MRFOV2,
    "sma": SMAV2,
    "gto": GTOV2,
    "ewa": EWAV2,
    "aha": AHAV2,
    "rro": RROV2,
    "gvoa": GVOAV2,
    "smo": SMOV2,
    "opa": OPAV2,
    "hoa": HOAV2,
    "fgo": FGOV2,
}

# Standard benchmark instances
STANDARD_INSTANCES = {
    "small": ["P-n16-k8", "E-n22-k4", "A-n32-k5"],
    "medium": ["A-n45-k7", "B-n50-k7", "E-n51-k5"],
    "large": ["A-n60-k9", "B-n78-k10", "E-n101-k8"],
    "all": ["P-n16-k8", "E-n22-k4", "A-n32-k5", "A-n45-k7", "B-n50-k7", 
            "E-n51-k5", "A-n60-k9", "B-n78-k10", "E-n101-k8"]
}


@click.command()
@click.option('--algorithms', '-a', type=str, required=True,
              help='Algorithms to benchmark (comma-separated or "all")')
@click.option('--instances', '-i', type=str, required=True,
              help='Instances to use (comma-separated or "small"/"medium"/"large"/"all")')
@click.option('--runs', '-r', default=30, type=int,
              help='Number of runs per algorithm/instance')
@click.option('--iterations', '-n', default=100, type=int,
              help='Number of iterations per run')
@click.option('--population', '-p', default=30, type=int,
              help='Population size')
@click.option('--seed', '-s', default=42, type=int,
              help='Base random seed')
@click.option('--parallel/--no-parallel', default=True,
              help='Run in parallel')
@click.option('--workers', '-w', type=int,
              help='Number of parallel workers')
@click.option('--capture-metadata/--no-capture-metadata', default=True,
              help='Capture system metadata')
@click.option('--monitor-resources/--no-monitor-resources', default=True,
              help='Monitor resource usage')
@click.option('--checkpoint-interval', default=50, type=int,
              help='Checkpoint interval for saving progress')
@click.option('--resume/--no-resume', default=True,
              help='Resume from checkpoint if available')
@click.option('--output-dir', '-o', type=str,
              help='Output directory (auto-generated if not specified)')
@click.option('--timeout', type=int, default=300,
              help='Timeout per task in seconds')
@click.option('--generate-report/--no-generate-report', default=True,
              help='Generate HTML report after benchmark')
def main(algorithms, instances, runs, iterations, population, seed, parallel, workers,
         capture_metadata, monitor_resources, checkpoint_interval, resume, 
         output_dir, timeout, generate_report):
    """
    Run comprehensive benchmarks with complete metadata capture.
    
    Examples:
    
    # Benchmark specific algorithms on small instances
    python benchmark_with_metadata.py -a "hoa,egto,foa" -i small
    
    # Benchmark all algorithms on specific instances
    python benchmark_with_metadata.py -a all -i "P-n16-k8,E-n22-k4"
    
    # Large benchmark with custom settings
    python benchmark_with_metadata.py -a all -i all -r 100 --checkpoint-interval 100
    """
    
    # Parse algorithms
    if algorithms.lower() == 'all':
        algo_list = list(ALGORITHMS_V2.keys())
    else:
        algo_list = [a.strip() for a in algorithms.split(',')]
        # Validate algorithms
        invalid_algos = [a for a in algo_list if a not in ALGORITHMS_V2]
        if invalid_algos:
            click.echo(f"❌ Invalid algorithms: {', '.join(invalid_algos)}", err=True)
            click.echo(f"Available: {', '.join(ALGORITHMS_V2.keys())}", err=True)
            return
    
    # Parse instances
    if instances.lower() in STANDARD_INSTANCES:
        instance_list = STANDARD_INSTANCES[instances.lower()]
    else:
        instance_list = [i.strip() for i in instances.split(',')]
    
    # Create algorithm classes list
    algorithm_classes = [ALGORITHMS_V2[a] for a in algo_list]
    
    # Configure output directory
    if output_dir is None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_dir = f"results/benchmark_{timestamp}"
    
    # Create output directory
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    
    # Save benchmark configuration
    config = {
        "timestamp": datetime.now().isoformat(),
        "algorithms": algo_list,
        "instances": instance_list,
        "runs_per_instance": runs,
        "iterations": iterations,
        "population_size": population,
        "base_seed": seed,
        "parallel": parallel,
        "workers": workers,
        "capture_metadata": capture_metadata,
        "monitor_resources": monitor_resources,
        "checkpoint_interval": checkpoint_interval,
        "timeout": timeout
    }
    
    config_file = Path(output_dir) / "benchmark_config.json"
    with open(config_file, 'w') as f:
        json.dump(config, f, indent=2)
    
    click.echo(f"🚀 Starting benchmark with metadata capture")
    click.echo(f"📊 Configuration:")
    click.echo(f"  Algorithms: {len(algo_list)} ({', '.join(algo_list[:3])}{'...' if len(algo_list) > 3 else ''})")
    click.echo(f"  Instances: {len(instance_list)} ({', '.join(instance_list[:3])}{'...' if len(instance_list) > 3 else ''})")
    click.echo(f"  Runs per instance: {runs}")
    click.echo(f"  Total tasks: {len(algo_list) * len(instance_list) * runs}")
    click.echo(f"  Output directory: {output_dir}")
    click.echo(f"  Metadata capture: {capture_metadata}")
    click.echo(f"  Resource monitoring: {monitor_resources}")
    
    # Create benchmark runner
    benchmark = MetadataEnhancedBenchmark(
        algorithms=algorithm_classes,
        instances=instance_list,
        runs_per_instance=runs,
        population_size=population,
        max_iterations=iterations,
        capture_metadata=capture_metadata,
        monitor_resources=monitor_resources,
        parallel=parallel,
        n_workers=workers,
        checkpoint_interval=checkpoint_interval,
        timeout=timeout,
        output_dir=output_dir
    )
    
    # Run benchmark
    click.echo("\n⏳ Running benchmark...")
    try:
        results = benchmark.run_benchmark(resume=resume)
        
        # Save results
        benchmark.save_results(results, formats=['json', 'csv', 'pickle', 'metadata'])
        
        # Generate report if requested
        if generate_report:
            click.echo("\n📝 Generating report...")
            from utils.benchmarking import BenchmarkVisualizer
            visualizer = BenchmarkVisualizer()
            report_path = visualizer.create_comprehensive_report(
                results, 
                Path(output_dir),
                include_stats=True
            )
            click.echo(f"📊 Report generated: {report_path}")
        
        # Print summary
        click.echo("\n✅ Benchmark completed successfully!")
        click.echo(f"📁 Results saved in: {output_dir}")
        
        # Show basic statistics
        if results:
            total_runs = sum(r.runs for r in results)
            successful_runs = sum(len(r.fitness_values) for r in results)
            click.echo(f"\n📈 Summary:")
            click.echo(f"  Total runs: {total_runs}")
            click.echo(f"  Successful runs: {successful_runs}")
            click.echo(f"  Success rate: {successful_runs/total_runs*100:.1f}%")
            
            # Best results per instance
            click.echo("\n🏆 Best results per instance:")
            instance_bests = {}
            for result in results:
                if result.instance_name not in instance_bests:
                    instance_bests[result.instance_name] = []
                if result.best_fitness:
                    instance_bests[result.instance_name].append(
                        (result.algorithm_name, result.best_fitness)
                    )
            
            for instance, algo_results in sorted(instance_bests.items()):
                if algo_results:
                    best_algo, best_fitness = min(algo_results, key=lambda x: x[1])
                    click.echo(f"  {instance}: {best_algo} ({best_fitness:.2f})")
        
    except KeyboardInterrupt:
        click.echo("\n⚠️  Benchmark interrupted by user")
        click.echo(f"Partial results saved in: {output_dir}")
    except Exception as e:
        click.echo(f"\n❌ Error during benchmark: {str(e)}", err=True)
        import traceback
        traceback.print_exc()


if __name__ == '__main__':
    main()