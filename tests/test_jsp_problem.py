"""
Tests for Job Shop Problem implementation.
"""

import pytest
import numpy as np
from problems.discrete.scheduling import JobShopProblem
from problems import ContinuousAdapter
from algorithms.woa_v2 import WOAV2
from algorithms.gto_v2 import GTOV2


class TestJobShopProblem:
    """Test Job Shop Problem implementation."""
    
    def test_jsp_initialization(self):
        """Test JSP initialization."""
        # Simple 2x2 instance
        jobs = [
            [(0, 3), (1, 2)],  # Job 0: Machine 0 (3 units), then Machine 1 (2 units)
            [(1, 2), (0, 1)]   # Job 1: Machine 1 (2 units), then Machine 0 (1 unit)
        ]
        
        jsp = JobShopProblem(jobs)
        
        assert jsp.n_jobs == 2
        assert jsp.n_machines == 2
        assert jsp.n_operations == 4
        assert jsp.dimension == 4
        assert jsp.name == "JSP-2x2"
    
    def test_operation_creation(self):
        """Test that operations are created correctly."""
        jobs = [
            [(0, 5), (1, 3)],
            [(1, 4), (0, 2)]
        ]
        
        jsp = JobShopProblem(jobs)
        
        # Check operations
        assert len(jsp.operations) == 4
        
        # Job 0 operations
        assert jsp.operations[0].job_id == 0
        assert jsp.operations[0].op_id == 0
        assert jsp.operations[0].machine_id == 0
        assert jsp.operations[0].processing_time == 5
        
        assert jsp.operations[1].job_id == 0
        assert jsp.operations[1].op_id == 1
        assert jsp.operations[1].machine_id == 1
        assert jsp.operations[1].processing_time == 3
    
    def test_continuous_encoding_decoding(self):
        """Test conversion between continuous and discrete representations."""
        jobs = [
            [(0, 3), (1, 2)],
            [(1, 2), (0, 1)]
        ]
        jsp = JobShopProblem(jobs)
        
        # Test encoding
        continuous = np.array([0.9, 0.3, 0.7, 0.5])
        sequence = jsp.encode_continuous(continuous)
        
        # Should order by priority (descending)
        assert len(sequence) == 4
        assert sequence[0] == 0  # Highest priority (0.9)
        assert sequence[1] == 2  # Second highest (0.7)
        assert sequence[2] == 3  # Third (0.5)
        assert sequence[3] == 1  # Lowest (0.3)
        
        # Test decoding
        continuous2 = jsp.decode_to_continuous(sequence)
        assert len(continuous2) == 4
        assert continuous2[sequence[0]] > continuous2[sequence[1]]
        assert continuous2[sequence[1]] > continuous2[sequence[2]]
        assert continuous2[sequence[2]] > continuous2[sequence[3]]
    
    def test_makespan_computation(self):
        """Test makespan calculation."""
        jobs = [
            [(0, 3), (1, 2)],  # Job 0: M0(3) -> M1(2)
            [(1, 2), (0, 1)]   # Job 1: M1(2) -> M0(1)
        ]
        jsp = JobShopProblem(jobs)
        
        # Valid sequence: J0-O0, J1-O0, J0-O1, J1-O1
        # This means: [0, 2, 1, 3]
        sequence = [0, 2, 1, 3]
        makespan = jsp.evaluate(sequence)
        
        # Timeline:
        # t=0-3: J0-O0 on M0
        # t=0-2: J1-O0 on M1
        # t=3-5: J0-O1 on M1 (waits for M1 and J0-O0)
        # t=3-4: J1-O1 on M0 (waits for M0 and J1-O0)
        # Makespan = 5
        
        assert makespan == 5.0
    
    def test_invalid_sequence(self):
        """Test that invalid sequences get penalty values."""
        jobs = [
            [(0, 3), (1, 2)],
            [(1, 2), (0, 1)]
        ]
        jsp = JobShopProblem(jobs)
        
        # Invalid sequence: tries to do J0-O1 before J0-O0
        sequence = [1, 0, 2, 3]  # [J0-O1, J0-O0, J1-O0, J1-O1]
        makespan = jsp.evaluate(sequence)
        
        # Should get a large penalty, not infinity
        assert makespan > 10000  # Penalty base
        assert makespan < float('inf')
    
    def test_feasibility_check(self):
        """Test feasibility checking."""
        jobs = [
            [(0, 3), (1, 2)],
            [(1, 2), (0, 1)]
        ]
        jsp = JobShopProblem(jobs)
        
        # Valid sequence
        valid = [0, 2, 1, 3]
        assert jsp.is_feasible(valid)
        
        # Invalid sequence (precedence violation)
        invalid = [1, 0, 2, 3]
        assert not jsp.is_feasible(invalid)
        
        # Test with continuous representation
        continuous = np.array([0.9, 0.3, 0.7, 0.5])
        assert jsp.is_feasible(continuous)
    
    def test_random_solution(self):
        """Test random solution generation."""
        jobs = [
            [(0, 3), (1, 2), (2, 4)],
            [(1, 2), (2, 1), (0, 3)],
            [(2, 3), (0, 2), (1, 1)]
        ]
        jsp = JobShopProblem(jobs)
        
        # Generate multiple random solutions
        for _ in range(10):
            solution = jsp.random_solution()
            assert len(solution) == 9  # 3 jobs × 3 operations
            assert jsp.is_feasible(solution)
            assert jsp.evaluate(solution) < 100000  # Below penalty threshold
    
    def test_generate_random_instance(self):
        """Test random instance generation."""
        jsp = JobShopProblem.generate_random(
            n_jobs=5,
            n_machines=4,
            min_time=1,
            max_time=10,
            seed=42
        )
        
        assert jsp.n_jobs == 5
        assert jsp.n_machines == 4
        assert jsp.n_operations == 20  # 5 jobs × 4 machines
        assert jsp.name == "Random-5x4"
        
        # Check that each job visits each machine exactly once
        for job_id in range(5):
            machines = [op.machine_id for op in jsp.job_operations[job_id]]
            assert len(set(machines)) == 4  # All different
            assert min(machines) == 0
            assert max(machines) == 3
    
    def test_gantt_data(self):
        """Test Gantt chart data generation."""
        jobs = [
            [(0, 3), (1, 2)],
            [(1, 2), (0, 1)]
        ]
        jsp = JobShopProblem(jobs)
        
        sequence = [0, 2, 1, 3]
        jsp.evaluate(sequence)
        
        gantt_data = jsp.get_schedule_gantt_data()
        
        assert len(gantt_data) == 4
        
        # Check first operation
        op0_data = next(d for d in gantt_data if d['operation'] == 'J0-O0')
        assert op0_data['job'] == 'Job 0'
        assert op0_data['machine'] == 'Machine 0'
        assert op0_data['start'] == 0
        assert op0_data['end'] == 3
    
    def test_with_continuous_adapter(self):
        """Test JSP with continuous optimization algorithms."""
        # Create JSP instance
        jsp = JobShopProblem.generate_random(
            n_jobs=3,
            n_machines=3,
            seed=123
        )
        
        # Adapt for continuous algorithms
        adapted = ContinuousAdapter(jsp)
        
        # Should work with algorithms
        algo = WOAV2(adapted, population_size=20, max_iterations=50)
        best = algo.execute()
        
        # Convert solution and verify
        sequence = jsp.encode_continuous(best.position)
        assert jsp.is_feasible(sequence)
        
        makespan = jsp.evaluate(sequence)
        assert makespan < float('inf')
        assert makespan > 0
    
    def test_cache_behavior(self):
        """Test that evaluation caching works correctly."""
        jobs = [
            [(0, 3), (1, 2)],
            [(1, 2), (0, 1)]
        ]
        jsp = JobShopProblem(jobs)
        
        continuous = np.array([0.9, 0.3, 0.7, 0.5])
        
        # First evaluation
        jsp.reset_evaluations()
        makespan1 = jsp.evaluate(continuous)
        evals1 = jsp.evaluations
        
        # Second evaluation (should use cache)
        makespan2 = jsp.evaluate(continuous)
        evals2 = jsp.evaluations
        
        assert makespan1 == makespan2
        assert evals2 == evals1 + 1  # Still counts as evaluation
        
        # Different solution should not use cache
        continuous2 = np.array([0.8, 0.4, 0.6, 0.5])
        makespan3 = jsp.evaluate(continuous2)
        evals3 = jsp.evaluations
        
        assert evals3 == evals2 + 1
    
    def test_compatibility_methods(self):
        """Test legacy interface compatibility."""
        jsp = JobShopProblem.generate_random(n_jobs=4, n_machines=3)
        
        assert jsp.get_dimension() == 12  # 4×3
        
        lower = jsp.get_lower_bounds()
        upper = jsp.get_upper_bounds()
        
        assert len(lower) == 12
        assert len(upper) == 12
        assert np.all(lower == 0)
        assert np.all(upper == 1)
    
    def test_larger_instance(self):
        """Test with a larger instance."""
        jsp = JobShopProblem.generate_random(
            n_jobs=10,
            n_machines=10,
            seed=999
        )
        
        assert jsp.n_operations == 100
        
        # Test that random solutions are feasible
        for _ in range(5):
            solution = jsp.random_solution()
            assert jsp.is_feasible(solution)
            makespan = jsp.evaluate(solution)
            assert makespan < 100000  # Below penalty threshold
            assert makespan > 0
    
    def test_precedence_enforcement(self):
        """Test that precedence constraints are properly enforced."""
        jobs = [
            [(0, 5), (1, 3), (2, 2)],  # Job 0
            [(2, 4), (0, 2), (1, 3)]   # Job 1
        ]
        jsp = JobShopProblem(jobs)
        
        # Try various invalid sequences
        # Trying J0-O2 before J0-O1
        invalid1 = [0, 3, 2, 1, 4, 5]
        assert not jsp.is_feasible(invalid1)
        
        # Trying J1-O1 before J1-O0
        invalid2 = [0, 4, 1, 3, 2, 5]
        assert not jsp.is_feasible(invalid2)
        
        # Valid sequence
        valid = [0, 3, 1, 4, 2, 5]
        assert jsp.is_feasible(valid)


class TestJobShopWithAlgorithms:
    """Test JSP with different optimization algorithms."""
    
    def test_multiple_algorithms(self):
        """Test JSP with multiple algorithms."""
        # Create smaller instance for testing
        jsp = JobShopProblem.generate_random(
            n_jobs=3,
            n_machines=3,
            seed=789
        )
        adapted = ContinuousAdapter(jsp)
        
        # Test with different algorithms
        algorithms = [
            WOAV2(adapted, population_size=50, max_iterations=200),
            GTOV2(adapted, population_size=50, max_iterations=200)
        ]
        
        results = []
        for algo in algorithms:
            best = algo.execute()
            sequence = jsp.encode_continuous(best.position)
            makespan = jsp.evaluate(sequence)
            results.append((makespan, jsp.is_feasible(sequence)))
        
        # Check that at least one algorithm found a feasible solution
        # (Since random continuous values often produce infeasible schedules)
        feasible_found = any(feasible for _, feasible in results)
        assert feasible_found, "No algorithm found a feasible solution"
        
        # If a feasible solution was found, it should have finite makespan
        for makespan, feasible in results:
            if feasible:
                assert makespan < float('inf')
                assert makespan > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])