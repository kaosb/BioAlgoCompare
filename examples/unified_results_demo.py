"""
Demo of the unified result system with HOA v3.

This example shows how to:
1. Run algorithms with automatic result tracking
2. Export results in multiple formats
3. Perform multiple runs with statistics
4. Use callbacks for custom processing
"""

import numpy as np
from pathlib import Path
from datetime import datetime

# Import the new algorithm and result system
from algorithms.hoa_v3 import HippopotamusOptimizationV3
from problems.vrp_v2 import VRPProblemV2
from utils.result_schema_v2 import StandardResultV2
from utils.result_adapter import get_result_adapter


def print_result_summary(result: StandardResultV2):
    """Callback to print result summary."""
    print("\n" + "="*60)
    print("RESULT SUMMARY")
    print("="*60)
    
    summary = result.get_summary()
    for key, value in summary.items():
        if key != 'convergence_curve':  # Skip long lists
            print(f"{key:20s}: {value}")
    
    # Print validation status
    print(f"\nValidation Status: {'✓ PASSED' if result.validated else '✗ FAILED'}")
    if not result.validated:
        print("Validation Errors:")
        for error in result.validation_errors:
            print(f"  - {error}")
    
    # Print reproducibility info
    repro_info = result.get_reproducibility_info()
    print(f"\nGit Commit: {repro_info['git']['commit_hash'][:8] if repro_info.get('git') else 'N/A'}")
    print(f"Random Seed: {repro_info['execution']['random_seed']}")
    print(f"Dependencies: {len(repro_info['dependencies'])} packages tracked")


def export_for_publication(result: StandardResultV2):
    """Callback to export results for publication."""
    # Create exports directory
    export_dir = Path("exports") / datetime.now().strftime("%Y%m%d_%H%M%S")
    export_dir.mkdir(parents=True, exist_ok=True)
    
    # Export to different formats
    result.to_json(export_dir / "full_result.json")
    result.export_convergence_curves(export_dir / "convergence.csv")
    result.export_to_latex(export_dir / "summary_table.tex")
    
    # Export reproducibility information
    repro_info = result.get_reproducibility_info()
    import json
    (export_dir / "reproducibility.json").write_text(
        json.dumps(repro_info, indent=2, default=str)
    )
    
    print(f"\nResults exported to: {export_dir}")


def main():
    print("Unified Result System Demo")
    print("==========================\n")
    
    # Load problem
    problem_path = "data/vrp/E-n22-k4.vrp"
    problem = VRPProblemV2(problem_path)
    print(f"Loaded problem: {problem.name}")
    print(f"Dimension: {problem.dimension}")
    print(f"Vehicle capacity: {problem.vehicle_capacity}\n")
    
    # Example 1: Single run with automatic result tracking
    print("Example 1: Single Run with Result Tracking")
    print("-" * 40)
    
    algorithm = HippopotamusOptimizationV3(
        problem=problem,
        population_size=30,
        max_iterations=50,
        seed=42,
        # HOA parameters
        phase_probability=0.5,
        evasion_base_prob=0.1,
        evasion_scale=0.8,
        # Result tracking
        track_resources=True,
        auto_save=True,
        save_path="results/hoa_v3_{timestamp}.json",
        result_callbacks=[print_result_summary]
    )
    
    # Run algorithm (returns StandardResultV2)
    result = algorithm.run()
    
    # Access result data
    print(f"\nBest fitness found: {result.statistics.best_fitness:.2f}")
    print(f"Execution time: {result.execution_info.duration_seconds:.2f} seconds")
    print(f"CPU usage: {result.execution_info.cpu_percent_avg:.1f}%")
    print(f"Peak memory: {result.execution_info.memory_peak_mb:.1f} MB")
    
    # Verify integrity
    print(f"\nResult integrity check: {'✓ VALID' if result.verify_integrity() else '✗ INVALID'}")
    
    # Example 2: Multiple runs with statistics
    print("\n\nExample 2: Multiple Runs with Statistics")
    print("-" * 40)
    
    algorithm2 = HippopotamusOptimizationV3(
        problem=problem,
        population_size=20,
        max_iterations=30,
        result_callbacks=[export_for_publication]
    )
    
    # Run multiple times
    multi_result = algorithm2.run_multiple(n_runs=5, seeds=[42, 123, 456, 789, 999])
    
    # Print statistics
    stats = multi_result.statistics
    print(f"\nRuns completed: {stats.n_runs}")
    print(f"Best fitness: {stats.best_fitness:.2f}")
    print(f"Mean ± Std: {stats.mean_fitness:.2f} ± {stats.std_fitness:.2f}")
    print(f"Median: {stats.median_fitness:.2f}")
    print(f"IQR: {stats.iqr_fitness:.2f}")
    print(f"95% CI: [{stats.confidence_interval_95[0]:.2f}, {stats.confidence_interval_95[1]:.2f}]")
    print(f"Total execution time: {stats.total_execution_time:.2f} seconds")
    
    # Example 3: Result adapter for legacy compatibility
    print("\n\nExample 3: Result Adapter Usage")
    print("-" * 40)
    
    adapter = get_result_adapter(use_v2=True, auto_migrate=True)
    
    # Save to multiple locations
    locations = adapter.save_result(
        multi_result,
        path="results/multi_run_demo.json",
        save_to_db=True,
        save_to_tracker=True
    )
    
    print("Result saved to:")
    for location, value in locations.items():
        print(f"  - {location}: {value}")
    
    # Load result back
    loaded_result = adapter.load_result("results/multi_run_demo.json")
    print(f"\nLoaded result ID: {loaded_result.result_id}")
    print(f"Checksum match: {loaded_result.checksum == multi_result.checksum}")
    
    # Example 4: Export for publication
    print("\n\nExample 4: Publication-Ready Exports")
    print("-" * 40)
    
    # Create DataFrame for analysis
    df = multi_result.to_dataframe(include_metadata=True)
    print("\nDataFrame shape:", df.shape)
    print("\nDataFrame columns:")
    print(df.columns.tolist())
    
    # Summary statistics by run
    print("\nPer-run summary:")
    print(df[['run_id', 'seed', 'best_fitness', 'execution_time']].to_string())
    
    # Export convergence curves
    multi_result.export_convergence_curves(
        "exports/convergence_all_runs.csv",
        format='csv'
    )
    
    print("\nDemo completed successfully!")


if __name__ == "__main__":
    main()