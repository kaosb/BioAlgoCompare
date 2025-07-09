#!/usr/bin/env python3
"""
Demo benchmark script for algorithm comparison.
Runs a small benchmark to demonstrate the corrected statistical analysis.
"""

import subprocess
import os
import sys
import time


def run_benchmark():
    """Run a benchmark comparing algorithms."""
    print("=== Running Algorithm Benchmark ===")

    # Use small instances for demo
    instances = ["E-n22-k4", "P-n16-k8", "A-n32-k5"]
    algorithms = ["hho", "foa", "egto", "ewa", "opa"]

    # Create output directory
    output_dir = "results/demo_benchmark"
    os.makedirs(output_dir, exist_ok=True)

    # Run benchmark
    cmd = [
        "python", "scripts/analyze.py", "benchmark",
        "--run-benchmark",
        "--instances", ",".join(instances),
        "--algorithms", ",".join(algorithms),
        "--runs", "10",  # 10 runs per algorithm/instance
        "--iterations", "50",  # 50 iterations per run
        "--population", "20",  # Small population
        "--output-dir", output_dir,
        "--parallel",  # Use parallel execution
        "--seed", "42"  # Fixed seed for reproducibility
    ]

    print(f"Running command: {' '.join(cmd)}")
    result = subprocess.run(cmd, capture_output=True, text=True)

    if result.returncode != 0:
        print(f"Error running benchmark: {result.stderr}")
        return None

    # Convert JSON results to CSV for analysis
    json_path = os.path.join(output_dir, "benchmark_results.json")
    if not os.path.exists(json_path):
        print("No benchmark results found")
        return None

    # Convert to CSV format
    import json
    import pandas as pd

    with open(json_path, 'r') as f:
        data = json.load(f)

    # Create CSV from JSON data
    rows = []
    for result in data:
        fitness_values = result['detailed_results']['fitness_values']
        exec_times = result['detailed_results']['execution_times']

        for i, fitness in enumerate(fitness_values):
            rows.append({
                'Algorithm': result['algorithm'],
                'Instance': result['instance'],
                'Run': i + 1,
                'Best': fitness,
                'Time': exec_times[i] if i < len(exec_times) else 0
            })

    df = pd.DataFrame(rows)
    csv_path = os.path.join(output_dir, "benchmark_results.csv")
    df.to_csv(csv_path, index=False)

    print(f"\nBenchmark results saved to: {csv_path}")
    return csv_path


def run_statistical_analysis(csv_path):
    """Run the corrected statistical analysis."""
    print("\n=== Running Statistical Analysis (v2) ===")

    output_dir = os.path.dirname(csv_path)
    stats_dir = os.path.join(output_dir, "statistical_analysis")

    # Run the v2 analysis with corrected CD calculation
    cmd = [
        "python", "scripts/analyze_v2.py", "stats",
        "--csv", csv_path,
        "--out", stats_dir,
        "--extended-tests"  # Include Quade test
    ]

    print(f"Running command: {' '.join(cmd)}")
    result = subprocess.run(cmd, capture_output=True, text=True)

    if result.returncode != 0:
        print(f"Error running analysis: {result.stderr}")
        return False

    print(f"\nStatistical analysis completed. Results saved to: {stats_dir}")

    # Display the report
    report_path = os.path.join(stats_dir, "stats_report.md")
    if os.path.exists(report_path):
        print("\n=== Statistical Report ===")
        with open(report_path, "r") as f:
            print(f.read())

    return True


def run_effect_size_analysis(csv_path):
    """Run effect size analysis."""
    print("\n=== Running Effect Size Analysis ===")

    output_dir = os.path.dirname(csv_path)

    # Run effect size analysis
    cmd = [
        "python", "scripts/analyze_v2.py", "effect-size",
        "--csv", csv_path,
        "--out", output_dir
    ]

    print(f"Running command: {' '.join(cmd)}")
    result = subprocess.run(cmd, capture_output=True, text=True)

    if result.returncode != 0:
        print(f"Error running effect size analysis: {result.stderr}")
        return False

    # Display effect sizes
    effect_csv = os.path.join(output_dir, "effect_sizes.csv")
    if os.path.exists(effect_csv):
        print("\n=== Effect Sizes ===")
        subprocess.run(["head", "-20", effect_csv])

    return True


def main():
    """Main function."""
    print("BioAlgoCompare Demo: Algorithm Comparison with Corrected Statistical Analysis")
    print("=" * 80)

    # Step 1: Run benchmark
    csv_path = run_benchmark()
    if not csv_path:
        print("Benchmark failed")
        sys.exit(1)

    # Step 2: Run statistical analysis
    if not run_statistical_analysis(csv_path):
        print("Statistical analysis failed")
        sys.exit(1)

    # Step 3: Run effect size analysis
    if not run_effect_size_analysis(csv_path):
        print("Effect size analysis failed")
        sys.exit(1)

    print("\n" + "=" * 80)
    print("Demo completed successfully!")
    print(f"All results saved in: {os.path.dirname(csv_path)}")


if __name__ == "__main__":
    main()
