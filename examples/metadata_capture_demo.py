#!/usr/bin/env python3
"""
Demonstration of complete metadata capture in algorithm results.

This example shows how the enhanced result system captures all necessary
metadata for scientific reproducibility.
"""

import json
from pathlib import Path

# Add parent directory to path
import sys
sys.path.append(str(Path(__file__).parent.parent))

from algorithms.hoa_v2 import HOAV2
from problems.vrp_v2 import VRPProblemV2
from utils.result_metadata_integration import (
    MetadataEnhancedAlgorithm, wrap_algorithm_with_metadata
)
from utils.result_schema_v2 import StandardResultV2


def demo_basic_metadata_capture():
    """Demonstrate basic metadata capture with a single algorithm run."""
    print("=== Basic Metadata Capture Demo ===\n")
    
    # Load a problem
    problem = VRPProblemV2("data/vrp/A-n32-k5.vrp")
    print(f"Problem: {problem.name} (dimension: {problem.dimension})")
    
    # Create algorithm with metadata capture
    print("\nCreating HOA with automatic metadata capture...")
    
    # Wrap the algorithm to capture metadata
    MetadataHOA = wrap_algorithm_with_metadata(HOAV2, capture_metadata=True, monitor_resources=True)
    
    # Run algorithm
    algorithm = MetadataHOA(
        problem=problem,
        population_size=20,
        max_iterations=50,
        seed=42
    )
    
    print("Running algorithm...")
    best_solution = algorithm.execute()
    
    print(f"\nBest fitness found: {best_solution.fitness():.2f}")
    print(f"Execution time: {algorithm.get_execution_time():.2f} seconds")
    
    # Get complete result with metadata
    print("\nCapturing complete result with metadata...")
    complete_result = algorithm.get_complete_result()
    
    # Display captured metadata
    print("\n--- CAPTURED METADATA ---")
    
    # System info
    print("\nSystem Information:")
    print(f"  Platform: {complete_result.system_info.platform}")
    print(f"  CPU: {complete_result.system_info.processor}")
    print(f"  CPU Cores: {complete_result.system_info.cpu_count}")
    print(f"  Memory: {complete_result.system_info.memory_total_gb:.1f} GB")
    print(f"  Python: {complete_result.system_info.python_version.split()[0]}")
    
    # Git info
    if complete_result.git_info:
        print("\nGit Information:")
        print(f"  Branch: {complete_result.git_info.branch}")
        print(f"  Commit: {complete_result.git_info.commit_hash[:8]}")
        print(f"  Dirty: {complete_result.git_info.is_dirty}")
    
    # Execution info
    if complete_result.execution_info:
        print("\nExecution Information:")
        print(f"  Start time: {complete_result.execution_info.start_time}")
        print(f"  Duration: {complete_result.execution_info.duration_seconds:.2f} seconds")
        print(f"  CPU usage (avg): {complete_result.execution_info.cpu_percent_avg:.1f}%")
        print(f"  Memory peak: {complete_result.execution_info.memory_peak_mb:.1f} MB")
        print(f"  Random seed: {complete_result.execution_info.random_seed}")
    
    # Dependencies (first 5)
    if complete_result.dependencies:
        print("\nKey Dependencies:")
        for dep in complete_result.dependencies[:5]:
            print(f"  {dep.name}: {dep.version}")
    
    # Result info
    print("\nResult Information:")
    print(f"  Result ID: {complete_result.result_id}")
    print(f"  Checksum: {complete_result.checksum}")
    print(f"  Validated: {complete_result.validated}")
    
    return complete_result


def demo_metadata_comparison():
    """Demonstrate how metadata helps verify reproducibility."""
    print("\n\n=== Metadata Comparison Demo ===\n")
    
    problem = VRPProblemV2("data/vrp/A-n32-k5.vrp")
    
    # Run same algorithm twice with same seed
    print("Running algorithm twice with same seed (42)...")
    
    results = []
    for i in range(2):
        MetadataHOA = wrap_algorithm_with_metadata(HOAV2)
        algo = MetadataHOA(problem, population_size=10, max_iterations=20, seed=42)
        algo.execute()
        results.append(algo.get_complete_result())
    
    # Compare results
    print("\nComparing results:")
    print(f"Run 1 - Fitness: {results[0].runs[0].best_fitness:.4f}")
    print(f"Run 2 - Fitness: {results[1].runs[0].best_fitness:.4f}")
    print(f"Results match: {results[0].runs[0].best_fitness == results[1].runs[0].best_fitness}")
    
    # Compare metadata
    print("\nMetadata comparison:")
    print(f"Same system: {results[0].system_info.platform == results[1].system_info.platform}")
    print(f"Same Python: {results[0].system_info.python_version == results[1].system_info.python_version}")
    print(f"Same seed: {results[0].execution_info.random_seed == results[1].execution_info.random_seed}")


def demo_save_with_metadata():
    """Demonstrate saving results with complete metadata."""
    print("\n\n=== Save with Metadata Demo ===\n")
    
    problem = VRPProblemV2("data/vrp/A-n32-k5.vrp")
    
    # Run algorithm
    MetadataHOA = wrap_algorithm_with_metadata(HOAV2)
    algo = MetadataHOA(problem, population_size=15, max_iterations=30, seed=123)
    algo.execute()
    
    # Get complete result
    result = algo.get_complete_result()
    
    # Save to file
    output_dir = Path("results/metadata_demo")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    filename = f"hoa_result_{result.timestamp.strftime('%Y%m%d_%H%M%S')}.json"
    filepath = output_dir / filename
    
    with open(filepath, 'w') as f:
        json.dump(result.to_dict(), f, indent=2, default=str)
    
    print(f"Saved complete result to: {filepath}")
    print(f"File size: {filepath.stat().st_size / 1024:.1f} KB")
    
    # Show structure
    print("\nResult structure:")
    data = result.to_dict()
    for key in data.keys():
        if isinstance(data[key], dict):
            print(f"  {key}: {len(data[key])} fields")
        elif isinstance(data[key], list):
            print(f"  {key}: {len(data[key])} items")
        else:
            print(f"  {key}: {type(data[key]).__name__}")


def main():
    """Run all demonstrations."""
    # Basic metadata capture
    result = demo_basic_metadata_capture()
    
    # Comparison demo
    demo_metadata_comparison()
    
    # Save demo
    demo_save_with_metadata()
    
    print("\n\n=== Demo Complete ===")
    print("Metadata capture ensures complete reproducibility and traceability.")


if __name__ == "__main__":
    main()