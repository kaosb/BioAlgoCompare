"""
Comando reproducibility para gestión de reproducibilidad en experimentos.
"""

import click
import json
from pathlib import Path
import sys
from typing import Optional, List, Dict, Any

from utils.reproducibility import (
    ReproducibilityManager, 
    create_reproducible_experiment,
    set_global_seed
)
from utils.reproducibility.reproducibility_validator import (
    AlgorithmReproducibilityValidator,
    ExperimentReproducibilityValidator,
    validate_all_algorithms,
    generate_reproducibility_report
)
from algorithms import ALGORITHMS
from problems.vrp import VRPProblem


@click.group()
def reproducibility():
    """Reproducibility management commands."""
    pass


@reproducibility.command()
@click.option('--algorithm', '-a', multiple=True,
              help='Specific algorithms to validate (default: all)')
@click.option('--output', '-o', type=click.Path(),
              help='Output file for report')
@click.option('--format', type=click.Choice(['text', 'markdown', 'json']),
              default='markdown',
              help='Report format')
def validate(algorithm: List[str], output: Optional[str], format: str):
    """
    Validate reproducibility compliance of algorithms.
    
    Checks that algorithms follow reproducibility standards including
    proper seed handling, deterministic behavior, and state isolation.
    
    Examples:
    
        # Validate all algorithms
        bioalgo reproducibility validate
        
        # Validate specific algorithms
        bioalgo reproducibility validate -a HOA -a FOA
        
        # Save report to file
        bioalgo reproducibility validate -o report.md
    """
    click.echo("🔍 Validating algorithm reproducibility...")
    
    validator = AlgorithmReproducibilityValidator()
    
    # Determine which algorithms to validate
    if algorithm:
        algorithms_to_validate = {
            name: cls for name, cls in ALGORITHMS.items() 
            if name.upper() in [a.upper() for a in algorithm]
        }
    else:
        algorithms_to_validate = ALGORITHMS
    
    # Validate each algorithm
    all_violations = {}
    total_passed = 0
    total_failed = 0
    
    with click.progressbar(
        algorithms_to_validate.items(),
        label='Validating algorithms',
        show_pos=True
    ) as algorithms:
        for name, algo_class in algorithms:
            violations = validator.validate_algorithm_class(algo_class)
            if violations:
                all_violations[name] = violations
                total_failed += 1
            else:
                total_passed += 1
    
    # Generate report based on format
    if format == 'markdown':
        report = generate_reproducibility_report()
    elif format == 'json':
        report_data = {
            'summary': {
                'total_algorithms': len(algorithms_to_validate),
                'passed': total_passed,
                'failed': total_failed
            },
            'violations': {
                alg: [
                    {
                        'severity': v.severity,
                        'component': v.component,
                        'issue': v.issue,
                        'suggestion': v.suggestion
                    }
                    for v in violations
                ]
                for alg, violations in all_violations.items()
            }
        }
        report = json.dumps(report_data, indent=2)
    else:  # text
        report = f"Reproducibility Validation Report\n"
        report += f"{'='*50}\n"
        report += f"Total algorithms: {len(algorithms_to_validate)}\n"
        report += f"Passed: {total_passed}\n"
        report += f"Failed: {total_failed}\n\n"
        
        if all_violations:
            report += "Violations found:\n"
            for alg, violations in all_violations.items():
                report += f"\n{alg}:\n"
                for v in violations:
                    report += f"  - [{v.severity}] {v.issue}\n"
                    if v.suggestion:
                        report += f"    Suggestion: {v.suggestion}\n"
    
    # Display summary
    click.echo(f"\n✅ Passed: {total_passed}")
    click.echo(f"❌ Failed: {total_failed}")
    
    if all_violations:
        click.echo("\n⚠️  Issues found in:")
        for alg in all_violations:
            click.echo(f"  - {alg}")
    
    # Save report if requested
    if output:
        Path(output).write_text(report)
        click.echo(f"\n📄 Report saved to: {output}")
    elif format == 'markdown' and all_violations:
        # Show brief excerpt for markdown
        click.echo("\nFor detailed report, use -o flag to save to file")


@reproducibility.command()
@click.option('--seed', '-s', type=int, default=42,
              help='Base seed for reproducibility')
@click.option('--algorithms', '-a', multiple=True,
              help='Algorithms to test')
@click.option('--instance', '-i', default='E-n22-k4',
              help='Problem instance')
@click.option('--runs', '-r', type=int, default=3,
              help='Number of runs per algorithm')
def test(seed: int, algorithms: List[str], instance: str, runs: int):
    """
    Test reproducibility of algorithms.
    
    Runs algorithms multiple times with same seed to verify
    deterministic behavior.
    
    Examples:
    
        # Test all algorithms
        bioalgo reproducibility test
        
        # Test specific algorithms with custom seed
        bioalgo reproducibility test -a HOA -a FOA -s 12345
        
        # Test with multiple runs
        bioalgo reproducibility test -r 5
    """
    click.echo(f"🧪 Testing reproducibility with seed={seed}")
    
    # Initialize reproducibility manager
    manager = ReproducibilityManager(base_seed=seed, enforce_determinism=True)
    
    # Load problem
    try:
        problem = VRPProblem(instance)
    except Exception as e:
        click.echo(f"❌ Error loading problem {instance}: {e}", err=True)
        sys.exit(1)
    
    # Determine algorithms
    if algorithms:
        test_algorithms = {
            name: cls for name, cls in ALGORITHMS.items()
            if name.upper() in [a.upper() for a in algorithms]
        }
    else:
        test_algorithms = dict(list(ALGORITHMS.items())[:3])  # Test first 3 by default
    
    results = {}
    
    click.echo(f"\nTesting {len(test_algorithms)} algorithms with {runs} runs each...")
    
    for algo_name, algo_class in test_algorithms.items():
        click.echo(f"\n{algo_name}:")
        algo_results = []
        
        for run_idx in range(runs):
            # Create reproducible experiment
            experiment = manager.create_experiment(
                experiment_id=f"{algo_name}_run{run_idx}",
                algorithm=algo_name,
                problem=instance,
                parameters={
                    'population_size': 30,
                    'max_iterations': 50
                }
            )
            
            # Run algorithm with experiment context
            with experiment.algorithm_context() as random_state:
                algo = algo_class(
                    problem=problem,
                    population_size=30,
                    max_iterations=50,
                    seed=experiment.algorithm_seed
                )
                result = algo.run()
                algo_results.append(result['best_fitness'])
                click.echo(f"  Run {run_idx + 1}: {result['best_fitness']:.4f}")
        
        # Check consistency
        unique_results = set(algo_results)
        if len(unique_results) == 1:
            click.echo(f"  ✅ Perfectly reproducible!")
        else:
            variance = np.var(algo_results) if len(algo_results) > 1 else 0
            click.echo(f"  ❌ Non-deterministic! Variance: {variance:.6f}")
        
        results[algo_name] = {
            'results': algo_results,
            'unique_values': len(unique_results),
            'reproducible': len(unique_results) == 1
        }
    
    # Summary
    reproducible_count = sum(1 for r in results.values() if r['reproducible'])
    click.echo(f"\n{'='*50}")
    click.echo(f"Summary: {reproducible_count}/{len(results)} algorithms are reproducible")
    
    # Save detailed results
    manager.save_reproducibility_info('reproducibility_test_results.json')
    click.echo(f"\n📄 Detailed results saved to: reproducibility_test_results.json")


@reproducibility.command()
@click.option('--apply', is_flag=True,
              help='Apply fixes (default is dry run)')
@click.option('--directory', '-d', default='algorithms',
              help='Directory to process')
@click.option('--report', '-r', default='reproducibility_fixes.md',
              help='Report file path')
def fix(apply: bool, directory: str, report: str):
    """
    Fix reproducibility issues in algorithm implementations.
    
    Automatically applies common fixes for reproducibility issues
    such as proper seed handling and random state usage.
    
    Examples:
    
        # Dry run to see what would be fixed
        bioalgo reproducibility fix
        
        # Apply fixes
        bioalgo reproducibility fix --apply
        
        # Fix specific directory
        bioalgo reproducibility fix -d algorithms/experimental --apply
    """
    from scripts.enforce_reproducibility import ReproducibilityEnforcer
    
    mode = "APPLYING FIXES" if apply else "DRY RUN"
    click.echo(f"🔧 {mode} - Checking reproducibility issues...")
    
    # Create enforcer
    enforcer = ReproducibilityEnforcer(dry_run=not apply)
    
    # Process directory
    dir_path = Path(directory)
    if not dir_path.exists():
        click.echo(f"❌ Directory {directory} not found", err=True)
        sys.exit(1)
    
    # Process files
    results = enforcer.process_directory(dir_path)
    
    # Display results
    if not results:
        click.echo("✅ All files comply with reproducibility standards!")
    else:
        click.echo(f"\n{'Would fix' if not apply else 'Fixed'} {len(results)} files:")
        
        for filepath, changes in sorted(results.items()):
            click.echo(f"\n{filepath}:")
            for change in changes:
                click.echo(f"  - {change}")
    
    # Generate report
    report_content = enforcer.generate_report(results)
    Path(report).write_text(report_content)
    click.echo(f"\n📄 Report saved to: {report}")
    
    if not apply and results:
        click.echo("\n💡 To apply these fixes, run with --apply flag")


@reproducibility.command()
@click.option('--output', '-o', default='reproducibility_info.json',
              help='Output file path')
def info(output: str):
    """
    Display current reproducibility configuration.
    
    Shows information about the current reproducibility setup
    including seeds, environment, and configuration.
    
    Examples:
    
        # Show reproducibility info
        bioalgo reproducibility info
        
        # Save to custom file
        bioalgo reproducibility info -o my_repro_info.json
    """
    manager = ReproducibilityManager()
    info = manager.get_reproducibility_info()
    
    click.echo("📊 Reproducibility Configuration")
    click.echo("=" * 50)
    
    # Display key information
    click.echo(f"\nBase seed: {info['base_seed']}")
    click.echo(f"Enforce determinism: {info['enforce_determinism']}")
    click.echo(f"Registered seeds: {len(info['random_state']['seed_registry'])}")
    
    if 'environment' in info:
        env = info['environment']
        click.echo(f"\nEnvironment:")
        click.echo(f"  Python: {env['platform']['python_version']}")
        click.echo(f"  System: {env['platform']['system']} {env['platform']['release']}")
        click.echo(f"  NumPy: {env['packages'].get('numpy', 'Not installed')}")
        
        # Check critical environment variables
        critical_vars = ['PYTHONHASHSEED', 'OMP_NUM_THREADS']
        click.echo(f"\nEnvironment variables:")
        for var in critical_vars:
            value = env['environment_variables'].get(var, 'Not set')
            status = "✅" if value != 'Not set' else "⚠️"
            click.echo(f"  {status} {var}: {value}")
    
    # Save full info
    Path(output).write_text(json.dumps(info, indent=2, default=str))
    click.echo(f"\n📄 Full info saved to: {output}")


@reproducibility.command()
@click.argument('seed', type=int)
def set_seed(seed: int):
    """
    Set global seed for reproducibility.
    
    Sets the base seed that will be used for all subsequent
    experiments and operations.
    
    Examples:
    
        # Set seed to 12345
        bioalgo reproducibility set-seed 12345
    """
    set_global_seed(seed)
    click.echo(f"✅ Global seed set to: {seed}")
    
    # Verify
    manager = get_global_manager()
    click.echo(f"Base seed: {manager.base_seed}")
    click.echo(f"Random state seeds: {len(manager.random_state_manager.seed_registry)}")


# Import numpy for variance calculation
import numpy as np
from utils.reproducibility import get_global_manager