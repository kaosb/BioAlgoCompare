#!/usr/bin/env python3
"""
Massive benchmarking command for BioAlgoCompare.

Handles large-scale benchmarking with 1000+ runs, including
checkpointing, resumption, and parallel execution.
"""

import click
from pathlib import Path
import json
import time
from typing import List, Dict, Any
import multiprocessing as mp


@click.command()
@click.option('--algorithms', '-a', multiple=True, required=True,
              help='Algorithms to benchmark (can specify multiple)')
@click.option('--instances', '-i', multiple=True, required=True,
              help='Instances to use (can specify multiple)')
@click.option('--runs', '-r', default=1000, type=int,
              help='Number of runs per algorithm-instance combination (default: 1000)')
@click.option('--population', '-p', default=30, type=int,
              help='Population size (default: 30)')
@click.option('--iterations', default=100, type=int,
              help='Maximum iterations (default: 100)')
@click.option('--seed', default=42, type=int,
              help='Base random seed (default: 42)')
@click.option('--checkpoint-interval', default=100, type=int,
              help='Save checkpoint every N runs (default: 100)')
@click.option('--resume/--no-resume', default=True,
              help='Resume from checkpoint if available')
@click.option('--parallel/--no-parallel', default=True,
              help='Use parallel execution')
@click.option('--workers', '-w', type=int,
              help='Number of parallel workers (default: CPU count)')
@click.option('--output-dir', '-o', type=click.Path(),
              help='Output directory for results')
@click.option('--timeout', default=300, type=int,
              help='Timeout per run in seconds (default: 300)')
@click.option('--metadata/--no-metadata', default=True,
              help='Capture system metadata')
@click.option('--monitor/--no-monitor', default=False,
              help='Monitor resource usage')
@click.option('--verbose', '-v', is_flag=True,
              help='Verbose output')
def massive(algorithms, instances, runs, population, iterations, seed, 
           checkpoint_interval, resume, parallel, workers, output_dir, 
           timeout, metadata, monitor, verbose):
    """Run massive benchmarks with 1000+ runs."""
    import sys
    
    # Validate inputs
    if runs < 100:
        click.echo("⚠️  Warning: Use 'benchmark' command for runs < 100")
        click.confirm("Continue with massive benchmark?", abort=True)
    
    # Setup
    output_path = Path(output_dir) if output_dir else Path("results/massive")
    output_path.mkdir(parents=True, exist_ok=True)
    
    if not workers:
        workers = min(mp.cpu_count(), 8)  # Cap at 8 for massive runs
    
    if verbose:
        click.echo(f"🚀 Massive benchmarking setup:")
        click.echo(f"   Algorithms: {', '.join(algorithms)}")
        click.echo(f"   Instances: {', '.join(instances)}")
        click.echo(f"   Runs per combination: {runs}")
        click.echo(f"   Total runs: {len(algorithms) * len(instances) * runs}")
        click.echo(f"   Workers: {workers}")
        click.echo(f"   Output: {output_path}")
        click.echo(f"   Checkpoint interval: {checkpoint_interval}")
    
    try:
        # Import required modules
        from scripts.config.algorithms import ALGORITHMS
        from utils.benchmarking_v2 import MetadataEnhancedBenchmark
        from algorithms import get_algorithm_class
        
        # Validate algorithms
        invalid_algos = [a for a in algorithms if a not in ALGORITHMS]
        if invalid_algos:
            click.echo(f"❌ Invalid algorithms: {', '.join(invalid_algos)}")
            click.echo(f"Available: {', '.join(ALGORITHMS.keys())}")
            sys.exit(1)
        
        # Get algorithm classes
        algo_classes = []
        for algo_name in algorithms:
            try:
                algo_class = get_algorithm_class(algo_name)
                algo_classes.append(algo_class)
            except ImportError as e:
                click.echo(f"❌ Failed to import {algo_name}: {e}")
                sys.exit(1)
        
        # Create checkpoint file path
        checkpoint_file = output_path / "massive_checkpoint.json"
        
        # Check for existing checkpoint
        start_run = 0
        completed_combinations = set()
        
        if resume and checkpoint_file.exists():
            try:
                with open(checkpoint_file) as f:
                    checkpoint = json.load(f)
                
                start_run = checkpoint.get('completed_runs', 0)
                completed_combinations = set(tuple(c) for c in checkpoint.get('completed_combinations', []))
                
                if verbose:
                    click.echo(f"📂 Resuming from checkpoint: {start_run} runs completed")
                    click.echo(f"   Completed combinations: {len(completed_combinations)}")
                
            except Exception as e:
                if verbose:
                    click.echo(f"⚠️  Warning: Could not load checkpoint: {e}")
                start_run = 0
                completed_combinations = set()
        
        # Create massive benchmark runner
        benchmark = MassiveBenchmarkRunner(
            algorithms=algo_classes,
            instances=list(instances),
            runs_per_instance=runs,
            population_size=population,
            max_iterations=iterations,
            base_seed=seed,
            parallel=parallel,
            workers=workers,
            checkpoint_interval=checkpoint_interval,
            checkpoint_file=checkpoint_file,
            output_dir=output_path,
            timeout=timeout,
            capture_metadata=metadata,
            monitor_resources=monitor,
            verbose=verbose
        )
        
        # Run massive benchmark
        benchmark.run_massive(
            start_run=start_run,
            completed_combinations=completed_combinations
        )
        
        if verbose:
            click.echo("✅ Massive benchmark completed successfully!")
        
    except ImportError as e:
        click.echo(f"❌ Missing dependencies: {e}")
        sys.exit(1)
    except KeyboardInterrupt:
        click.echo("\n⏹️  Benchmark interrupted by user")
        click.echo("Resume with --resume to continue from checkpoint")
        sys.exit(1)
    except Exception as e:
        click.echo(f"❌ Error during massive benchmark: {e}")
        if verbose:
            import traceback
            traceback.print_exc()
        sys.exit(1)


class MassiveBenchmarkRunner:
    """Runner for massive-scale benchmarks with checkpointing."""
    
    def __init__(self, algorithms, instances, runs_per_instance, population_size,
                 max_iterations, base_seed, parallel, workers, checkpoint_interval,
                 checkpoint_file, output_dir, timeout, capture_metadata, 
                 monitor_resources, verbose):
        
        self.algorithms = algorithms
        self.instances = instances
        self.runs_per_instance = runs_per_instance
        self.population_size = population_size
        self.max_iterations = max_iterations
        self.base_seed = base_seed
        self.parallel = parallel
        self.workers = workers
        self.checkpoint_interval = checkpoint_interval
        self.checkpoint_file = checkpoint_file
        self.output_dir = output_dir
        self.timeout = timeout
        self.capture_metadata = capture_metadata
        self.monitor_resources = monitor_resources
        self.verbose = verbose
        
        self.total_combinations = len(algorithms) * len(instances)
        self.total_runs = self.total_combinations * runs_per_instance
        
    def run_massive(self, start_run=0, completed_combinations=None):
        """Run massive benchmark with checkpointing."""
        if completed_combinations is None:
            completed_combinations = set()
        
        current_run = start_run
        
        # Process each algorithm-instance combination
        for i, algo_class in enumerate(self.algorithms):
            for j, instance in enumerate(self.instances):
                combination_key = (algo_class.__name__, instance)
                
                # Skip if already completed
                if combination_key in completed_combinations:
                    if self.verbose:
                        click.echo(f"⏭️  Skipping completed: {combination_key[0]} on {combination_key[1]}")
                    current_run += self.runs_per_instance
                    continue
                
                if self.verbose:
                    click.echo(f"🔄 Processing: {algo_class.__name__} on {instance}")
                
                # Create benchmark for this combination
                benchmark = MetadataEnhancedBenchmark(
                    algorithms=[algo_class],
                    instances=[instance],
                    runs_per_instance=self.runs_per_instance,
                    population_size=self.population_size,
                    max_iterations=self.max_iterations,
                    base_seed=self.base_seed + current_run,
                    parallel=self.parallel,
                    workers=self.workers,
                    timeout=self.timeout,
                    capture_metadata=self.capture_metadata,
                    monitor_resources=self.monitor_resources,
                    results_dir=self.output_dir
                )
                
                # Run benchmark for this combination
                results = benchmark.run()
                
                # Save results immediately
                benchmark.save_results(results, formats=['json', 'csv', 'metadata'])
                
                # Update progress
                current_run += self.runs_per_instance
                completed_combinations.add(combination_key)
                
                # Save checkpoint
                if current_run % self.checkpoint_interval == 0:
                    self._save_checkpoint(current_run, completed_combinations)
                
                # Progress report
                progress = (current_run / self.total_runs) * 100
                if self.verbose:
                    click.echo(f"📊 Progress: {current_run}/{self.total_runs} runs ({progress:.1f}%)")
        
        # Final checkpoint
        self._save_checkpoint(current_run, completed_combinations)
        
        # Generate final summary
        self._generate_summary(current_run)
    
    def _save_checkpoint(self, completed_runs, completed_combinations):
        """Save checkpoint to disk."""
        checkpoint = {
            'timestamp': time.time(),
            'completed_runs': completed_runs,
            'total_runs': self.total_runs,
            'completed_combinations': [list(c) for c in completed_combinations],
            'progress_percent': (completed_runs / self.total_runs) * 100
        }
        
        with open(self.checkpoint_file, 'w') as f:
            json.dump(checkpoint, f, indent=2)
        
        if self.verbose:
            click.echo(f"💾 Checkpoint saved: {completed_runs}/{self.total_runs} runs")
    
    def _generate_summary(self, total_runs):
        """Generate final summary of massive benchmark."""
        summary = {
            'massive_benchmark_summary': {
                'total_runs': total_runs,
                'algorithms': [algo.__name__ for algo in self.algorithms],
                'instances': self.instances,
                'runs_per_combination': self.runs_per_instance,
                'configuration': {
                    'population_size': self.population_size,
                    'max_iterations': self.max_iterations,
                    'parallel': self.parallel,
                    'workers': self.workers,
                    'timeout': self.timeout
                },
                'completed_at': time.time(),
                'output_directory': str(self.output_dir)
            }
        }
        
        summary_file = self.output_dir / 'massive_summary.json'
        with open(summary_file, 'w') as f:
            json.dump(summary, f, indent=2, default=str)
        
        if self.verbose:
            click.echo(f"📋 Summary saved to {summary_file}")
        
        # Clean up checkpoint file
        if self.checkpoint_file.exists():
            self.checkpoint_file.unlink()
            if self.verbose:
                click.echo("🧹 Checkpoint file cleaned up")