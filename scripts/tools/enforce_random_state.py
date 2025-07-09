#!/usr/bin/env python3
"""
Script to enforce RandomStateManager usage across all algorithms.

This script:
1. Analyzes existing algorithms for direct random seed usage
2. Generates migration code for each algorithm
3. Creates tests to verify random state management
4. Provides a report of compliance
"""

import os
import sys
import ast
import click
from pathlib import Path
from typing import List, Dict, Any, Tuple
import importlib.util
import inspect
import re

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from utils.random_state import RandomStateManager
from utils.random_enforcement import migrate_algorithm_to_managed_random


class RandomStateAnalyzer:
    """Analyzes algorithms for random state management compliance."""
    
    def __init__(self):
        self.violations = []
        self.compliant = []
        self.analysis_results = {}
    
    def analyze_file(self, file_path: Path) -> Dict[str, Any]:
        """
        Analyze a single algorithm file for random state usage.
        
        Args:
            file_path: Path to algorithm file
            
        Returns:
            Analysis results
        """
        with open(file_path, 'r') as f:
            content = f.read()
        
        # Parse AST
        try:
            tree = ast.parse(content)
        except SyntaxError as e:
            return {
                'file': str(file_path),
                'error': f"Syntax error: {e}",
                'violations': [],
                'uses_manager': False
            }
        
        # Find violations
        violations = self._find_violations(content, tree)
        uses_manager = self._uses_random_manager(content, tree)
        
        result = {
            'file': str(file_path),
            'violations': violations,
            'uses_manager': uses_manager,
            'needs_migration': len(violations) > 0 and not uses_manager
        }
        
        # Categorize
        if uses_manager:
            self.compliant.append(file_path)
        elif violations:
            self.violations.append(file_path)
        
        return result
    
    def _find_violations(self, content: str, tree: ast.Module) -> List[Dict[str, Any]]:
        """Find direct random seed usage violations."""
        violations = []
        
        # Patterns to check
        patterns = [
            (r'np\.random\.seed\s*\(', 'Direct numpy seed setting'),
            (r'numpy\.random\.seed\s*\(', 'Direct numpy seed setting'),
            (r'random\.seed\s*\(', 'Direct Python random seed setting'),
            (r'np\.random\.RandomState\s*\(', 'Direct RandomState creation'),
            (r'numpy\.random\.RandomState\s*\(', 'Direct RandomState creation'),
        ]
        
        for pattern, description in patterns:
            for match in re.finditer(pattern, content):
                line_num = content[:match.start()].count('\n') + 1
                violations.append({
                    'line': line_num,
                    'type': description,
                    'code': content.split('\n')[line_num - 1].strip()
                })
        
        return violations
    
    def _uses_random_manager(self, content: str, tree: ast.Module) -> bool:
        """Check if file uses RandomStateManager."""
        # Check imports
        if 'RandomStateManager' in content:
            return True
        
        # Check for ManagedRandomMixin
        if 'ManagedRandomMixin' in content:
            return True
        
        # Check for managed base classes
        if 'ManagedMetaheuristicAlgorithm' in content:
            return True
        
        return False
    
    def analyze_directory(self, directory: Path) -> Dict[str, Any]:
        """Analyze all algorithm files in a directory."""
        results = {}
        
        for file_path in directory.glob('*_v2.py'):
            if file_path.name.startswith('test_'):
                continue
            
            result = self.analyze_file(file_path)
            results[file_path.name] = result
            self.analysis_results[file_path.name] = result
        
        return results
    
    def generate_report(self) -> str:
        """Generate compliance report."""
        report = ["Random State Management Compliance Report", "=" * 50, ""]
        
        # Summary
        total = len(self.compliant) + len(self.violations)
        if total > 0:
            compliance_rate = (len(self.compliant) / total) * 100
        else:
            compliance_rate = 0
        
        report.append(f"Total algorithms analyzed: {total}")
        report.append(f"Compliant: {len(self.compliant)} ({compliance_rate:.1f}%)")
        report.append(f"Non-compliant: {len(self.violations)} ({100 - compliance_rate:.1f}%)")
        report.append("")
        
        # Violations detail
        if self.violations:
            report.append("Non-compliant Algorithms:")
            report.append("-" * 30)
            
            for file_path in self.violations:
                file_name = file_path.name
                result = self.analysis_results.get(file_name, {})
                violations = result.get('violations', [])
                
                report.append(f"\n{file_name}:")
                for violation in violations:
                    report.append(f"  Line {violation['line']}: {violation['type']}")
                    report.append(f"    Code: {violation['code']}")
        
        # Compliant algorithms
        if self.compliant:
            report.append("\nCompliant Algorithms:")
            report.append("-" * 30)
            for file_path in self.compliant:
                report.append(f"  ✓ {file_path.name}")
        
        return "\n".join(report)


class RandomStateMigrator:
    """Generates migration code for algorithms."""
    
    def __init__(self, output_dir: Path):
        self.output_dir = output_dir
        self.output_dir.mkdir(exist_ok=True)
    
    def migrate_algorithm(self, file_path: Path) -> Tuple[bool, str]:
        """
        Generate migration code for an algorithm.
        
        Args:
            file_path: Path to algorithm file
            
        Returns:
            Tuple of (success, message)
        """
        try:
            # Import the module
            spec = importlib.util.spec_from_file_location(
                file_path.stem,
                file_path
            )
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            
            # Find algorithm class
            algorithm_class = None
            for name, obj in inspect.getmembers(module):
                if (inspect.isclass(obj) and 
                    name.endswith('V2') and
                    hasattr(obj, 'execute')):
                    algorithm_class = obj
                    break
            
            if not algorithm_class:
                return False, f"No algorithm class found in {file_path.name}"
            
            # Generate migration code
            output_file = self.output_dir / f"{file_path.stem}_managed.py"
            migrate_algorithm_to_managed_random(
                algorithm_class,
                str(output_file)
            )
            
            return True, f"Migration code generated: {output_file.name}"
            
        except Exception as e:
            return False, f"Error migrating {file_path.name}: {str(e)}"
    
    def generate_test(self, algorithm_name: str) -> str:
        """Generate test code for random state management."""
        return f'''"""
Test random state management for {algorithm_name}.
"""

import pytest
import numpy as np
from algorithms.{algorithm_name.lower()}_managed import {algorithm_name}V3, {algorithm_name}V3Mixin
from problems.vrp import VRPProblem


class TestRandomStateManagement:
    """Test that {algorithm_name} properly manages random state."""
    
    @pytest.fixture
    def problem(self):
        """Create a test problem."""
        return VRPProblem("data/vrp/A-n32-k5.vrp")
    
    @pytest.mark.parametrize("algorithm_class", [{algorithm_name}V3, {algorithm_name}V3Mixin])
    def test_reproducibility(self, problem, algorithm_class):
        """Test that same seed produces same results."""
        # Run with same seed twice
        alg1 = algorithm_class(problem, population_size=10, max_iterations=5, seed=42)
        result1 = alg1.execute()
        
        alg2 = algorithm_class(problem, population_size=10, max_iterations=5, seed=42)
        result2 = alg2.execute()
        
        # Results should be identical
        assert result1.fitness() == result2.fitness()
        assert np.allclose(result1.position, result2.position)
    
    @pytest.mark.parametrize("algorithm_class", [{algorithm_name}V3, {algorithm_name}V3Mixin])
    def test_different_seeds(self, problem, algorithm_class):
        """Test that different seeds produce different results."""
        # Run with different seeds
        alg1 = algorithm_class(problem, population_size=10, max_iterations=5, seed=42)
        result1 = alg1.execute()
        
        alg2 = algorithm_class(problem, population_size=10, max_iterations=5, seed=123)
        result2 = alg2.execute()
        
        # Results should be different (with high probability)
        assert result1.fitness() != result2.fitness() or not np.allclose(result1.position, result2.position)
    
    @pytest.mark.parametrize("algorithm_class", [{algorithm_name}V3, {algorithm_name}V3Mixin])
    def test_checkpoint_restore(self, problem, algorithm_class):
        """Test checkpoint and restore functionality."""
        alg = algorithm_class(problem, population_size=10, max_iterations=10, seed=42)
        
        # Run for 5 iterations
        for _ in range(5):
            alg.update_population()
            alg.iteration += 1
        
        # Create checkpoint
        checkpoint = alg.checkpoint_random()
        state_before = alg.get_random_state()
        
        # Run for more iterations
        for _ in range(3):
            alg.update_population()
        
        # Restore checkpoint
        alg.restore_random_checkpoint(checkpoint)
        state_after = alg.get_random_state()
        
        # States should match
        assert state_before.seed == state_after.seed
'''


@click.group()
def cli():
    """Enforce RandomStateManager usage across algorithms."""
    pass


@cli.command()
@click.option('--directory', '-d', 
              default='algorithms',
              help='Directory containing algorithm files')
@click.option('--output', '-o',
              default='reports/random_state_compliance.txt',
              help='Output file for compliance report')
def analyze(directory: str, output: str):
    """Analyze algorithms for random state compliance."""
    analyzer = RandomStateAnalyzer()
    
    # Analyze directory
    algo_dir = project_root / directory
    if not algo_dir.exists():
        click.echo(f"Error: Directory {directory} not found", err=True)
        return
    
    click.echo(f"Analyzing algorithms in {algo_dir}...")
    results = analyzer.analyze_directory(algo_dir)
    
    # Generate report
    report = analyzer.generate_report()
    
    # Save report
    output_path = project_root / output
    output_path.parent.mkdir(exist_ok=True)
    
    with open(output_path, 'w') as f:
        f.write(report)
    
    # Display summary
    click.echo(report)
    click.echo(f"\nDetailed report saved to: {output}")


@cli.command()
@click.option('--directory', '-d',
              default='algorithms',
              help='Directory containing algorithm files')
@click.option('--output-dir', '-o',
              default='algorithms/managed',
              help='Output directory for migrated algorithms')
@click.option('--algorithms', '-a',
              help='Comma-separated list of algorithms to migrate')
def migrate(directory: str, output_dir: str, algorithms: str):
    """Generate migration code for algorithms."""
    analyzer = RandomStateAnalyzer()
    migrator = RandomStateMigrator(project_root / output_dir)
    
    # Get algorithms to migrate
    algo_dir = project_root / directory
    
    if algorithms:
        # Specific algorithms
        algo_files = []
        for algo in algorithms.split(','):
            algo = algo.strip()
            file_path = algo_dir / f"{algo}_v2.py"
            if file_path.exists():
                algo_files.append(file_path)
            else:
                click.echo(f"Warning: {algo}_v2.py not found", err=True)
    else:
        # All non-compliant algorithms
        results = analyzer.analyze_directory(algo_dir)
        algo_files = [
            algo_dir / name 
            for name, result in results.items()
            if result.get('needs_migration', False)
        ]
    
    if not algo_files:
        click.echo("No algorithms need migration")
        return
    
    # Migrate each algorithm
    click.echo(f"Migrating {len(algo_files)} algorithms...")
    
    for file_path in algo_files:
        success, message = migrator.migrate_algorithm(file_path)
        
        if success:
            click.echo(f"✓ {message}")
        else:
            click.echo(f"✗ {message}", err=True)
    
    click.echo(f"\nMigration complete. Files saved to: {output_dir}")


@cli.command()
@click.option('--algorithm', '-a',
              required=True,
              help='Algorithm name (e.g., HOA, EGTO)')
@click.option('--output', '-o',
              help='Output file for test code')
def generate_test(algorithm: str, output: str):
    """Generate test code for random state management."""
    migrator = RandomStateMigrator(Path.cwd())
    
    # Generate test code
    test_code = migrator.generate_test(algorithm.upper())
    
    if output:
        output_path = Path(output)
        output_path.parent.mkdir(exist_ok=True)
        
        with open(output_path, 'w') as f:
            f.write(test_code)
        
        click.echo(f"Test code saved to: {output}")
    else:
        # Display to console
        click.echo(test_code)


if __name__ == '__main__':
    cli()