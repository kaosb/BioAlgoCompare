"""
Example demonstrating dashboard usage with algorithm monitoring.
"""

import time
from pathlib import Path
import numpy as np

from dashboard import create_app
from dashboard.monitor import DashboardRunner, create_monitored_algorithm
from algorithms.factories import AlgorithmFactory
from problems.vrp_v2 import VRPProblemV2
from utils.experiment_tracker import ExperimentTracker


def basic_dashboard_example():
    """Basic example of using the dashboard."""
    print("=== Basic Dashboard Example ===\n")
    
    # Create dashboard
    app = create_app(port=8050, debug=False)
    runner = DashboardRunner(app)
    
    # Load problem
    problem = VRPProblemV2("data/vrp/E-n22-k4.vrp")
    print(f"Loaded problem: {problem.name}")
    
    # Create algorithm
    algo_info = AlgorithmFactory.get_algorithm("HOA")
    algorithm = algo_info['class'](
        problem,
        population_size=30,
        max_iterations=50,
        seed=42
    )
    
    print(f"Created algorithm: {algorithm.__class__.__name__}")
    print(f"Dashboard available at: http://127.0.0.1:8050")
    print("\nRunning algorithm with monitoring...")
    
    # Run with monitoring
    result = runner.run_algorithm(algorithm, monitor=True, blocking=True)
    
    print(f"\nCompleted!")
    print(f"Best fitness: {result['best_fitness']:.2f}")
    print(f"Iterations: {result['iterations']}")
    
    # Keep dashboard running for a bit
    print("\nDashboard will remain open for 30 seconds...")
    time.sleep(30)
    
    runner.stop()
    print("Dashboard stopped.")


def comparison_example():
    """Example comparing multiple algorithms."""
    print("=== Algorithm Comparison Example ===\n")
    
    # Create dashboard with custom configuration
    tracker = ExperimentTracker()
    app = create_app(
        experiment_tracker=tracker,
        port=8051,  # Different port
        debug=False
    )
    runner = DashboardRunner(app)
    
    # Load problem
    problem = VRPProblemV2("data/vrp/E-n22-k4.vrp")
    
    # Create multiple algorithms
    algorithms = {}
    algo_configs = {
        'HOA': {'population_size': 30, 'max_iterations': 100},
        'FOA': {'population_size': 30, 'max_iterations': 100},
        'GTO': {'population_size': 30, 'max_iterations': 100},
        'EGTO': {'population_size': 30, 'max_iterations': 100}
    }
    
    for name, config in algo_configs.items():
        algo_info = AlgorithmFactory.get_algorithm(name)
        if algo_info:
            algorithms[name] = algo_info['class'](
                problem,
                seed=42,
                **config
            )
            print(f"Created {name} algorithm")
    
    print(f"\nDashboard available at: http://127.0.0.1:8051")
    print("Starting algorithm comparison...\n")
    
    # Run comparison
    results = runner.run_comparison(algorithms, blocking=False)
    
    # Monitor progress
    print("Algorithms running... Check the dashboard for real-time updates!")
    print("\nPress Ctrl+C to stop\n")
    
    try:
        while True:
            # Check if all algorithms completed
            all_done = True
            for name, algo in algorithms.items():
                if algo.current_iteration < algo.max_iterations:
                    all_done = False
                    print(f"{name}: {algo.current_iteration}/{algo.max_iterations} iterations", end='\r')
                    break
            
            if all_done:
                print("\n\nAll algorithms completed!")
                break
                
            time.sleep(1)
            
    except KeyboardInterrupt:
        print("\n\nStopping...")
    
    # Print final results
    print("\n=== Final Results ===")
    for name, algo in algorithms.items():
        print(f"{name}: Best fitness = {algo.best_solution.fitness():.2f}")
    
    # Keep dashboard open
    print("\nDashboard will remain open for 60 seconds...")
    time.sleep(60)
    
    runner.stop()
    print("Dashboard stopped.")


def monitored_algorithm_example():
    """Example using monitored algorithm wrapper."""
    print("=== Monitored Algorithm Example ===\n")
    
    # Create dashboard
    app = create_app(port=8052)
    
    # Load problem
    problem = VRPProblemV2("data/vrp/E-n22-k4.vrp")
    
    # Create monitored algorithm
    algo_info = AlgorithmFactory.get_algorithm("HOA")
    algorithm = create_monitored_algorithm(
        algo_info['class'],
        problem,
        dashboard=app,
        population_size=50,
        max_iterations=150,
        seed=42
    )
    
    print(f"Created monitored {algorithm.__class__.__name__}")
    print(f"Dashboard available at: http://127.0.0.1:8052")
    print("\nRunning algorithm (will automatically appear in dashboard)...")
    
    # Run normally - monitoring happens automatically
    algorithm.run()
    
    print(f"\nCompleted!")
    print(f"Best fitness: {algorithm.best_solution.fitness():.2f}")
    
    # Dashboard stays open
    print("\nPress Enter to close dashboard...")
    input()


def advanced_monitoring_example():
    """Advanced example with custom callbacks and metrics."""
    print("=== Advanced Monitoring Example ===\n")
    
    # Create dashboard
    app = create_app(port=8053)
    runner = DashboardRunner(app)
    
    # Load problem
    problem = VRPProblemV2("data/vrp/E-n22-k4.vrp")
    
    # Create algorithm with custom tracking
    algo_info = AlgorithmFactory.get_algorithm("HOA")
    algorithm = algo_info['class'](
        problem,
        population_size=40,
        max_iterations=200,
        seed=42
    )
    
    # Custom callback to track additional metrics
    custom_metrics = {
        'diversity': [],
        'best_improvement': [],
        'stagnation_count': 0
    }
    
    prev_best = float('inf')
    
    def custom_callback(algo, run_id):
        nonlocal prev_best
        
        # Calculate population diversity
        if hasattr(algo, 'population') and algo.population:
            positions = [ind.position for ind in algo.population]
            diversity = np.mean(np.std(positions, axis=0))
            custom_metrics['diversity'].append(diversity)
        
        # Track improvement
        current_best = algo.best_solution.fitness()
        improvement = prev_best - current_best
        custom_metrics['best_improvement'].append(improvement)
        
        if improvement < 0.001:
            custom_metrics['stagnation_count'] += 1
        else:
            custom_metrics['stagnation_count'] = 0
            
        prev_best = current_best
        
        # Log every 10 iterations
        if algo.current_iteration % 10 == 0:
            print(f"Iter {algo.current_iteration}: "
                  f"Best = {current_best:.2f}, "
                  f"Diversity = {diversity:.4f}, "
                  f"Stagnation = {custom_metrics['stagnation_count']}")
    
    print(f"Dashboard available at: http://127.0.0.1:8053")
    print("Running with advanced monitoring...\n")
    
    # Run with custom callback
    runner.run_algorithm(
        algorithm,
        run_id="advanced_hoa",
        monitor=True,
        blocking=True,
        callback=custom_callback
    )
    
    print("\n=== Custom Metrics Summary ===")
    print(f"Final diversity: {custom_metrics['diversity'][-1]:.4f}")
    print(f"Best improvement: {max(custom_metrics['best_improvement']):.4f}")
    print(f"Max stagnation count: {max(custom_metrics['stagnation_count'], 0)}")
    
    # Save snapshot
    app.save_snapshot("advanced_hoa", "dashboard_snapshots/advanced_example.json")
    print("\nSnapshot saved to dashboard_snapshots/advanced_example.json")
    
    print("\nPress Enter to close dashboard...")
    input()
    
    runner.stop()


def main():
    """Run all examples."""
    examples = [
        ("Basic Dashboard", basic_dashboard_example),
        ("Algorithm Comparison", comparison_example),
        ("Monitored Algorithm", monitored_algorithm_example),
        ("Advanced Monitoring", advanced_monitoring_example)
    ]
    
    print("BioAlgoCompare Dashboard Examples")
    print("=" * 50)
    print("\nAvailable examples:")
    for i, (name, _) in enumerate(examples, 1):
        print(f"{i}. {name}")
    print("0. Run all examples")
    
    choice = input("\nSelect example (0-4): ")
    
    try:
        choice = int(choice)
        if choice == 0:
            for name, func in examples:
                print(f"\n{'='*50}")
                func()
                print("\nPress Enter to continue to next example...")
                input()
        elif 1 <= choice <= len(examples):
            examples[choice-1][1]()
        else:
            print("Invalid choice")
    except ValueError:
        print("Invalid input")
    except KeyboardInterrupt:
        print("\n\nExiting...")


if __name__ == "__main__":
    main()