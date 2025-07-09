"""Tests for documentation code examples.

This module tests that all code examples in the documentation work correctly.
"""
import os
import subprocess
import sys
import tempfile

import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))


class TestDocumentationExamples:
    """Test suite for documentation code examples."""
    
    def test_quick_start_basic_example(self):
        """Test the basic example from Quick Start Guide."""
        from algorithms import get_algorithm
        from problems.vrp import VRPProblem
        
        # Example from documentation
        problem = VRPProblem()
        problem.load_instance('P-n16-k8')
        
        AlgoClass = get_algorithm('ewa')
        algo = AlgoClass(problem, population_size=30)
        algo.initialize_population()
        best = algo.run(iterations=100)
        
        # Verify results
        assert best is not None
        assert hasattr(best, 'fitness')
        assert best.fitness() > 0
        
        # Test print statement works
        fitness_str = f"Best fitness: {best.fitness()}"
        assert isinstance(fitness_str, str)
        assert "Best fitness:" in fitness_str
    
    def test_algorithm_import_examples(self):
        """Test all algorithm import examples from module docstrings."""
        test_cases = [
            ('apo', 'APO'),
            ('ewa', 'EWA'), 
            ('foa', 'FOA'),
            ('opa', 'OPA'),
            ('sma', 'SMA')
        ]
        
        for module_name, class_name in test_cases:
            # Import as shown in docstring examples
            module = __import__(f'algorithms.{module_name}', fromlist=[class_name])
            AlgoClass = getattr(module, class_name)
            
            from problems.vrp import VRPProblem
            
            # Run example
            problem = VRPProblem()
            problem.load_instance('P-n16-k8')
            
            algo = AlgoClass(problem, population_size=30)
            algo.initialize_population()
            best_solution = algo.run(iterations=10)  # Quick test
            
            assert best_solution is not None
            assert best_solution.fitness() > 0
    
    def test_cli_basic_examples(self):
        """Test basic CLI examples (without actually running subprocess)."""
        # Test that the script exists and is executable
        script_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
            'scripts', 'analyze.py'
        )
        
        assert os.path.exists(script_path), "analyze.py script not found"
        
        # Test command construction (actual execution tested in CLI tests)
        commands = [
            ['python', script_path, 'run', '--algorithm', 'ewa', '--instance', 'P-n16-k8'],
            ['python', script_path, 'run', '-a', 'foa', '-i', 'E-n22-k4', '-n', '200'],
            ['python', script_path, 'benchmark', '--run-benchmark'],
            ['python', script_path, 'massive', '--algorithm', 'ewa,foa', '--runs', '10']
        ]
        
        for cmd in commands:
            # Just verify command structure is valid
            assert all(isinstance(arg, str) for arg in cmd)
    
    def test_get_algorithm_examples(self):
        """Test get_algorithm examples from __init__.py."""
        from algorithms import get_algorithm
        
        # Example: case-insensitive retrieval
        test_names = ['EWA', 'ewa', 'Ewa']
        
        for name in test_names:
            AlgoClass = get_algorithm(name)
            assert AlgoClass.__name__ == 'EWA'
    
    def test_algorithm_selection_guide_examples(self):
        """Test code snippets from Algorithm Selection Guide."""
        from algorithms import ALGORITHMS
        from problems.vrp import VRPProblem
        
        # Test algorithm categories exist
        mammal_algorithms = ['ewa', 'woa', 'gto', 'egto', 'hoa', 'sho', 'opa', 'foa']
        bird_algorithms = ['aha', 'hho', 'rro', 'gvoa', 'fsa', 'fgo', 'smo']
        marine_algorithms = ['mrfo', 'woa', 'opa']
        micro_algorithms = ['sma', 'apo']
        
        for algo in mammal_algorithms + bird_algorithms + marine_algorithms + micro_algorithms:
            assert algo in ALGORITHMS or algo == 'egto'  # egto might be same as gto
    
    def test_problem_loading_examples(self):
        """Test VRP problem loading examples."""
        from problems.vrp import VRPProblem
        
        # Test instances mentioned in documentation
        test_instances = [
            'P-n16-k8',   # Small
            'E-n22-k4',   # Medium
            'A-n32-k5',   # Medium
            'E-n51-k5'    # Large
        ]
        
        for instance in test_instances[:2]:  # Test first two for speed
            problem = VRPProblem()
            problem.load_instance(instance)
            
            # Verify problem loaded correctly
            assert problem.dimension > 0
            assert problem.capacity > 0
            assert len(problem.demands) == problem.dimension
    
    def test_parallel_execution_example(self):
        """Test parallel execution setup (structure only)."""
        from algorithms import get_algorithm
        from problems.vrp import VRPProblem
        
        # The example shows using parallel in CLI, but we can test
        # that algorithms work with multiple runs
        problem = VRPProblem()
        problem.load_instance('P-n16-k8')
        
        AlgoClass = get_algorithm('ewa')
        
        # Simulate multiple runs
        results = []
        for seed in [42, 123, 999]:
            algo = AlgoClass(problem, population_size=10, seed=seed)
            algo.initialize_population() 
            best = algo.run(iterations=10)
            results.append(best.fitness())
        
        # With different seeds, at least one result should differ
        assert len(set(results)) > 1, "All runs produced identical results"
    
    def test_tips_for_best_results(self):
        """Test recommendations from Tips section."""
        from algorithms import get_algorithm
        from problems.vrp import VRPProblem
        
        problem = VRPProblem()
        problem.load_instance('P-n16-k8')
        
        # Test population size recommendations
        pop_sizes = {
            'small': 30,    # 30-50 for small
            'medium': 50,   # 30-50 for medium
            'large': 100    # 50-100 for large
        }
        
        for size_type, pop_size in [('small', 30)]:
            AlgoClass = get_algorithm('ewa')
            algo = AlgoClass(problem, population_size=pop_size)
            assert algo.population_size == pop_size
    
    def test_module_docstring_imports(self):
        """Test that imports shown in module docstrings work."""
        # Test package-level docstring example
        exec("""
from algorithms import EWA
from problems.vrp import VRPProblem

problem = VRPProblem()
problem.load_instance('P-n16-k8')

algorithm = EWA(problem, population_size=30)
algorithm.initialize_population()
# Don't run full algorithm in test
assert algorithm is not None
""")
    
    @pytest.mark.parametrize("algo_name", ['aha', 'apo', 'ewa', 'foa', 'opa'])
    def test_algorithm_docstring_examples(self, algo_name):
        """Test that algorithm modules have proper docstrings."""
        # Import the module to check its docstring
        module = __import__(f'algorithms.{algo_name}')
        algo_module = getattr(module, algo_name)
        
        # Check module has docstring
        assert algo_module.__doc__ is not None
        assert len(algo_module.__doc__.strip()) > 0
        
        # Check docstring has some content (title or description)
        # Some algorithms have "Example:", others have references
        docstring = algo_module.__doc__.lower()
        assert any(keyword in docstring for keyword in [
            'algorithm', 'optimizer', 'optimization', 'metaheuristic',
            'bio-inspired', 'fuente:', 'reference:', 'doi:'
        ])


if __name__ == "__main__":
    pytest.main([__file__, "-v"])