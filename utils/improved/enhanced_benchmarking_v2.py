#!/usr/bin/env python3
"""
Enhanced benchmarking module v2 with software version tracking.
"""

import os
import json
import gzip
import time
import pickle
import hashlib
import logging
import platform
from datetime import datetime
from typing import Dict, List, Tuple, Optional, Any
import numpy as np
import pandas as pd
from tqdm import tqdm
from multiprocessing import Pool, Manager, cpu_count

# Import existing modules
from utils.benchmarking import BenchmarkResult, OPTIMAL_VALUES
from utils.improved.timing import setup_parallel_timers, cleanup_timers
from problems.vrp import VRPProblem

logger = logging.getLogger("enhanced_benchmarking_v2")


def get_software_versions() -> Dict[str, str]:
    """Get versions of key software components."""
    import sys
    try:
        import scipy
        scipy_version = scipy.__version__
    except:
        scipy_version = "not installed"

    try:
        import matplotlib
        matplotlib_version = matplotlib.__version__
    except:
        matplotlib_version = "not installed"

    versions = {
        "python": sys.version.split()[0],
        "numpy": np.__version__,
        "pandas": pd.__version__,
        "scipy": scipy_version,
        "matplotlib": matplotlib_version,
        "platform": platform.platform(),
        "processor": platform.processor() or "unknown",
        "machine": platform.machine(),
        "python_implementation": platform.python_implementation(),
        "timestamp": datetime.now().isoformat()
    }
    return versions


def save_software_versions(output_dir: str) -> str:
    """Save software versions to JSON file."""
    versions = get_software_versions()
    versions_file = os.path.join(output_dir, 'software_versions.json')

    with open(versions_file, 'w') as f:
        json.dump(versions, f, indent=2)

    logger.info(f"Software versions saved to {versions_file}")
    return versions_file


class EnhancedBenchmarkResult(BenchmarkResult):
    """Extended benchmark result with additional metrics."""

    def __init__(self, algorithm_name, instance_name):
        super().__init__(
            algorithm=algorithm_name,
            instance=instance_name,
            best_fitness=float('inf'),
            execution_time=0
        )
        self.algorithm_name = algorithm_name
        self.instance_name = instance_name
        self.fitness_values = []
        self.execution_times = []
        self.convergence_data = []
        self.seeds_used = []
        self.completed = False
        self.mean_fitness = None
        self.std_fitness = None
        self.mean_time = None
        self.std_time = None
        self.gap_to_optimal = None
        self.success_rate = None

    def add_run(self, fitness, exec_time, convergence=None, seed=None):
        """Add a single run result."""
        self.fitness_values.append(fitness)
        self.execution_times.append(exec_time)
        if convergence:
            self.convergence_data.append(convergence)
        if seed:
            self.seeds_used.append(seed)

        # Update best fitness
        if fitness < self.best_fitness:
            self.best_fitness = fitness

    def compute_metrics(self):
        """Compute summary metrics."""
        if self.fitness_values:
            self.mean_fitness = np.mean(self.fitness_values)
            self.std_fitness = np.std(self.fitness_values)
            self.mean_time = np.mean(self.execution_times)
            self.std_time = np.std(self.execution_times)

            # Calculate gap to optimal if available
            if self.instance_name in OPTIMAL_VALUES:
                optimal = OPTIMAL_VALUES[self.instance_name]
                self.gap_to_optimal = ((self.best_fitness - optimal) / optimal) * 100

                # Success rate (within 1% of optimal)
                successes = sum(1 for f in self.fitness_values if ((f - optimal) / optimal) <= 0.01)
                self.success_rate = (successes / len(self.fitness_values)) * 100

    def to_dict(self):
        """Convert to dictionary for serialization."""
        return {
            'algorithm_name': self.algorithm_name,
            'instance_name': self.instance_name,
            'fitness_values': self.fitness_values,
            'execution_times': self.execution_times,
            'convergence_data': self.convergence_data,
            'seeds_used': self.seeds_used,
            'best_fitness': self.best_fitness,
            'mean_fitness': self.mean_fitness,
            'std_fitness': self.std_fitness,
            'mean_time': self.mean_time,
            'std_time': self.std_time,
            'gap_to_optimal': self.gap_to_optimal,
            'success_rate': self.success_rate,
            'completed': self.completed
        }

    @classmethod
    def from_dict(cls, data):
        """Create instance from dictionary."""
        result = cls(data['algorithm_name'], data['instance_name'])
        result.fitness_values = data.get('fitness_values', [])
        result.execution_times = data.get('execution_times', [])
        result.convergence_data = data.get('convergence_data', [])
        result.seeds_used = data.get('seeds_used', [])
        result.best_fitness = data.get('best_fitness', float('inf'))
        result.mean_fitness = data.get('mean_fitness')
        result.std_fitness = data.get('std_fitness')
        result.mean_time = data.get('mean_time')
        result.std_time = data.get('std_time')
        result.gap_to_optimal = data.get('gap_to_optimal')
        result.success_rate = data.get('success_rate')
        result.completed = data.get('completed', False)
        return result


def run_massive_benchmark(
    algorithm_classes,
    instances,
    runs=1000,
    iterations=100,
    population=30,
    seed=42,
    parallel=True,
    checkpoint_interval=50,
    output_dir=None,
    resume=False,
    save_versions=True
):
    """
    Run massive benchmark with checkpoint support and software version tracking.

    Args:
        algorithm_classes: Dictionary of algorithms to evaluate
        instances: List of instance names
        runs: Number of runs per algorithm/instance combination
        iterations: Number of iterations per run
        population: Population size
        seed: Base seed for reproducibility
        parallel: Whether to run in parallel
        checkpoint_interval: How often to save checkpoints
        output_dir: Directory to save results
        resume: Whether to resume from checkpoint
        save_versions: Whether to save software versions

    Returns:
        List of EnhancedBenchmarkResult objects
    """
    # Setup output directory
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    if output_dir is None:
        output_dir = f"results/massive_benchmark_{timestamp}"

    # Create directories
    os.makedirs(output_dir, exist_ok=True)
    checkpoint_dir = os.path.join(output_dir, "checkpoints")
    os.makedirs(checkpoint_dir, exist_ok=True)

    # Save software versions
    if save_versions:
        save_software_versions(output_dir)

    # Global checkpoint file
    checkpoint_file = os.path.join(output_dir, "benchmark_state.json.gz")

    # Check if resuming
    benchmark_results = []
    completed_tasks = set()

    if resume and os.path.exists(checkpoint_file):
        try:
            logger.info(f"Resuming benchmark from {checkpoint_file}")
            with gzip.open(checkpoint_file, "rt") as f:
                checkpoint_data = json.load(f)

            # Recover saved results
            for result_data in checkpoint_data.get("results", []):
                benchmark_results.append(EnhancedBenchmarkResult.from_dict(result_data))

            # Recover completed tasks
            completed_tasks = set(checkpoint_data.get("completed_tasks", []))

            logger.info(f"Resumed with {len(benchmark_results)} results, {len(completed_tasks)} completed tasks")
        except Exception as e:
            logger.error(f"Error resuming benchmark: {str(e)}")
            logger.info("Starting benchmark from scratch")
            benchmark_results = []
            completed_tasks = set()

    # Validate instances
    valid_instances = []
    for instance_name in instances:
        # Check main path
        instance_path = f"data/vrp/{instance_name}.vrp"
        # Check Solomon path
        solomon_path = f"data/vrp/Solomon/{instance_name}.vrp"

        if os.path.exists(instance_path):
            valid_instances.append((instance_name, instance_path))
        elif os.path.exists(solomon_path):
            valid_instances.append((instance_name, solomon_path))
            logger.info(f"Instance found in Solomon path: {solomon_path}")
        else:
            logger.warning(f"Instance not found: {instance_name}")

    if not valid_instances:
        logger.error("No valid instances found")
        return []

    # Create all tasks
    all_tasks = []
    for algo_name, algo_class in algorithm_classes.items():
        for instance_name, instance_path in valid_instances:
            # Check if result exists
            existing_result = None
            for result in benchmark_results:
                if (result.algorithm_name == algo_class.__name__ and
                    result.instance_name == instance_name):
                    existing_result = result
                    break

            # Create tasks for missing runs
            if existing_result is None:
                # Create new result
                new_result = EnhancedBenchmarkResult(algo_class.__name__, instance_name)
                benchmark_results.append(new_result)

                # Add all runs as tasks
                for run_id in range(1, runs + 1):
                    task_id = f"{algo_class.__name__}_{instance_name}_{run_id}"
                    if task_id not in completed_tasks:
                        all_tasks.append((
                            algo_class, instance_name, instance_path,
                            run_id, iterations, population, seed, checkpoint_dir
                        ))

            elif len(existing_result.fitness_values) < runs:
                # Continue incomplete result
                completed_runs = len(existing_result.fitness_values)
                logger.info(f"Continuing {algo_class.__name__} on {instance_name} from run {completed_runs+1}")

                for run_id in range(completed_runs + 1, runs + 1):
                    task_id = f"{algo_class.__name__}_{instance_name}_{run_id}"
                    if task_id not in completed_tasks:
                        all_tasks.append((
                            algo_class, instance_name, instance_path,
                            run_id, iterations, population, seed, checkpoint_dir
                        ))

    # Exit if no pending tasks
    if not all_tasks:
        logger.info("No pending tasks, benchmark is complete")
        return benchmark_results

    # Setup multiprocessing
    if parallel:
        num_processes = min(cpu_count(), len(all_tasks))
        logger.info(f"Parallel mode enabled. Using {num_processes} processes.")
        setup_parallel_timers()
    else:
        num_processes = 1

    # Checkpoint function
    def save_checkpoint(silent=False):
        checkpoint_data = {
            "timestamp": datetime.now().isoformat(),
            "results": [result.to_dict() for result in benchmark_results],
            "completed_tasks": list(completed_tasks),
            "total_tasks": len(all_tasks) + len(completed_tasks),
            "software_versions": get_software_versions() if save_versions else {}
        }

        with gzip.open(checkpoint_file, "wt") as f:
            json.dump(checkpoint_data, f)

        if not silent:
            logger.info(f"Checkpoint saved ({len(completed_tasks)} tasks completed)")

    # Process results function
    def process_result(result_data):
        if "error" in result_data:
            logger.error(f"Error in task: {result_data['error']}")
            return

        # Find corresponding benchmark result
        for br in benchmark_results:
            if (br.algorithm_name == result_data['algorithm'] and
                br.instance_name == result_data['instance']):
                br.add_run(
                    result_data['fitness'],
                    result_data['time'],
                    result_data.get('convergence'),
                    result_data['seed']
                )
                break

        # Mark task as completed
        task_id = f"{result_data['algorithm']}_{result_data['instance']}_{result_data['run_id']}"
        completed_tasks.add(task_id)

    # Run benchmark
    task_count = len(all_tasks)
    completed_count = 0
    start_time = time.time()

    logger.info(f"Starting {task_count} pending tasks...")

    try:
        with tqdm(total=task_count, desc="Benchmark Progress") as pbar:
            if parallel:
                # Parallel execution
                with Pool(processes=num_processes) as pool:
                    for i, result_data in enumerate(pool.imap_unordered(run_single_benchmark, all_tasks)):
                        process_result(result_data)
                        completed_count += 1
                        pbar.update(1)

                        # Save checkpoint periodically
                        if completed_count % checkpoint_interval == 0:
                            save_checkpoint(silent=True)
            else:
                # Sequential execution
                for task in all_tasks:
                    result_data = run_single_benchmark(task)
                    process_result(result_data)
                    completed_count += 1
                    pbar.update(1)

                    # Save checkpoint periodically
                    if completed_count % checkpoint_interval == 0:
                        save_checkpoint(silent=True)

    except KeyboardInterrupt:
        logger.warning("Benchmark interrupted by user")
    except Exception as e:
        logger.error(f"Error in benchmark: {str(e)}")
    finally:
        # Calculate metrics and save final checkpoint
        for result in benchmark_results:
            result.compute_metrics()
            result.completed = len(result.fitness_values) >= runs

        save_checkpoint()

        # Save results
        duration = time.time() - start_time
        logger.info(f"Benchmark completed in {duration/60:.2f} minutes")
        logger.info(f"Completed {completed_count}/{task_count} tasks")

        # Generate summary CSV
        summary_df = create_summary_dataframe(benchmark_results)
        summary_file = os.path.join(output_dir, "massive_benchmark_summary.csv")
        summary_df.to_csv(summary_file, index=False)
        logger.info(f"Summary saved to {summary_file}")

        # Save extended metadata
        metadata = {
            "start_time": start_time,
            "end_time": time.time(),
            "duration_minutes": duration / 60,
            "total_runs": sum(len(r.fitness_values) for r in benchmark_results),
            "algorithms": list(algorithm_classes.keys()),
            "instances": instances,
            "parameters": {
                "runs": runs,
                "iterations": iterations,
                "population": population,
                "seed": seed,
                "parallel": parallel
            }
        }

        metadata_file = os.path.join(output_dir, "benchmark_metadata.json")
        with open(metadata_file, 'w') as f:
            json.dump(metadata, f, indent=2)

        return benchmark_results


def run_single_benchmark(args):
    """Run a single benchmark task (for multiprocessing)."""
    (algo_class, instance_name, instance_path, run_id,
     iterations, population, seed, checkpoint_dir) = args

    try:
        # Load problem
        problem = VRPProblem(instance_path)

        # Set seed
        run_seed = seed + run_id
        np.random.seed(run_seed)

        # Sanitize instance name for file paths
        safe_instance_name = instance_name.replace("/", "_")

        # Check if checkpoint exists
        checkpoint_file = os.path.join(
            checkpoint_dir, f"{algo_class.__name__}_{safe_instance_name}_run{run_id}.pkl"
        )

        if os.path.exists(checkpoint_file):
            # Load from checkpoint
            with open(checkpoint_file, 'rb') as f:
                result_data = pickle.load(f)
            return result_data

        # Run algorithm
        start_time = time.time()

        algorithm = algo_class(
            problem=problem,
            population_size=population,
            iterations=iterations,
            seed=run_seed
        )

        result = algorithm.execute()

        exec_time = time.time() - start_time

        # Prepare result data
        result_data = {
            'algorithm': algo_class.__name__,
            'instance': instance_name,
            'run_id': run_id,
            'fitness': result['best_fitness'],
            'time': exec_time,
            'convergence': result.get('convergence', []),
            'seed': run_seed
        }

        # Save checkpoint
        os.makedirs(os.path.dirname(checkpoint_file), exist_ok=True)
        with open(checkpoint_file, 'wb') as f:
            pickle.dump(result_data, f)

        # Save CSV with run data
        algo_dir = os.path.join(checkpoint_dir, algo_class.__name__)
        os.makedirs(algo_dir, exist_ok=True)
        csv_file = os.path.join(algo_dir, f"{safe_instance_name}_seed{run_seed}.csv")

        # Save convergence data if available
        if 'convergence' in result and result['convergence']:
            convergence_df = pd.DataFrame({
                'iteration': range(len(result['convergence'])),
                'best_fitness': result['convergence']
            })
            convergence_df.to_csv(csv_file, index=False)

        return result_data

    except Exception as e:
        logger.error(f"Error in {algo_class.__name__} on {instance_name} run {run_id}: {str(e)}")
        return {
            'algorithm': algo_class.__name__,
            'instance': instance_name,
            'run_id': run_id,
            'error': str(e)
        }


def create_summary_dataframe(benchmark_results):
    """Create a summary DataFrame from benchmark results."""
    summary_data = []

    for result in benchmark_results:
        if not result.fitness_values:
            continue

        row = {
            "Algorithm": result.algorithm_name,
            "Instance": result.instance_name,
            "Runs": len(result.fitness_values),
            "Best": result.best_fitness,
            "Mean": result.mean_fitness,
            "Std": result.std_fitness,
            "Time": result.mean_time,
            "Time_Std": result.std_time,
        }

        # Add gap to optimal if available
        if result.gap_to_optimal is not None:
            row["Gap (%)"] = result.gap_to_optimal

        # Add success rate if available
        if result.success_rate is not None:
            row["Success (%)"] = result.success_rate

        summary_data.append(row)

    # Create DataFrame
    if not summary_data:
        # Empty DataFrame with required columns
        summary_df = pd.DataFrame(columns=[
            "Algorithm", "Instance", "Runs", "Best", "Mean", "Std",
            "Time", "Time_Std", "Gap (%)", "Success (%)"
        ])
    else:
        summary_df = pd.DataFrame(summary_data)

    return summary_df


# Re-export original functions for compatibility
from utils.improved.enhanced_benchmarking import (
    run_benchmark_with_checkpoint,
    run_complete_analysis,
    generate_benchmark_id
)
