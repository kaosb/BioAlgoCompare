"""
Tests for the unified result system (StandardResultV2).
"""

import pytest
import json
import tempfile
from pathlib import Path
from datetime import datetime
import numpy as np

from utils.result_schema_v2 import (
    StandardResultV2, SystemInfo, GitInfo, ExecutionInfoV2,
    DependencyInfo, ResultBuilderV2, migrate_v1_to_v2
)
from utils.result_schema import (
    StandardResult, ProblemInfo, AlgorithmInfo, 
    SingleRunResult, MultiRunStatistics
)
from utils.result_adapter import ResultAdapter, get_result_adapter


class TestStandardResultV2:
    """Test the extended result schema."""
    
    def test_system_info_capture(self):
        """Test system information capture."""
        sys_info = SystemInfo.capture()
        
        assert sys_info.platform is not None
        assert sys_info.cpu_count > 0
        assert sys_info.memory_total_gb > 0
        assert 'Python' in sys_info.python_version
        
        # Test serialization
        data = sys_info.to_dict()
        assert isinstance(data, dict)
        assert 'platform' in data
    
    def test_git_info_capture(self):
        """Test git information capture."""
        git_info = GitInfo.capture()
        
        # May be None if not in a git repo
        if git_info:
            assert git_info.commit_hash is not None
            assert git_info.branch is not None
            assert isinstance(git_info.is_dirty, bool)
    
    def test_execution_info_v2(self):
        """Test execution info tracking."""
        exec_info = ExecutionInfoV2.start_tracking(seed=42, parallel=False)
        
        assert exec_info.random_seed == 42
        assert exec_info.parallel is False
        assert exec_info.start_time is not None
        
        # Simulate some execution
        import time
        time.sleep(0.1)
        
        # Finalize with samples
        exec_info.finalize(
            cpu_samples=[10.5, 15.2, 12.8],
            memory_samples=[100.0, 105.5, 102.3]
        )
        
        assert exec_info.duration_seconds > 0
        assert exec_info.cpu_percent_avg == pytest.approx(12.83, rel=0.01)
        assert exec_info.memory_peak_mb == 105.5
    
    def test_result_v2_creation(self):
        """Test creating a StandardResultV2."""
        # Create minimal components
        problem_info = ProblemInfo(name="test_problem", dimension=10)
        algorithm_info = AlgorithmInfo(name="test_algo", seed=42)
        
        run = SingleRunResult(
            run_id=0,
            seed=42,
            best_fitness=100.0,
            best_solution=[1, 2, 3],
            convergence_curve=[150.0, 120.0, 100.0],
            execution_time=1.5,
            iterations_completed=3,
            evaluations=90
        )
        
        stats = MultiRunStatistics.from_runs([run])
        
        # Create result
        result = StandardResultV2(
            result_type='single_run',
            problem_info=problem_info,
            algorithm_info=algorithm_info,
            runs=[run],
            statistics=stats
        )
        
        # Verify automatic fields
        assert result.result_id is not None
        assert result.version == "2.0.0"
        assert result.timestamp is not None
        assert result.system_info is not None
        assert result.checksum is not None
        assert result.validated
    
    def test_result_validation(self):
        """Test result validation."""
        # Create invalid result (no runs)
        problem_info = ProblemInfo(name="test", dimension=5)
        algorithm_info = AlgorithmInfo(name="test", seed=None)  # No seed
        
        result = StandardResultV2(
            result_type='single_run',
            problem_info=problem_info,
            algorithm_info=algorithm_info,
            runs=[],  # Empty runs
            statistics=MultiRunStatistics(
                n_runs=0, best_fitness=0, worst_fitness=0,
                mean_fitness=0, std_fitness=0, median_fitness=0,
                q1_fitness=0, q3_fitness=0, iqr_fitness=0,
                cv_fitness=0, success_rate=0, mean_convergence_rate=0,
                mean_execution_time=0, total_execution_time=0,
                confidence_interval_95=(0, 0)
            )
        )
        
        assert not result.validated
        assert len(result.validation_errors) > 0
        assert any("at least one run" in err for err in result.validation_errors)
    
    def test_checksum_integrity(self):
        """Test checksum calculation and verification."""
        # Create two identical results
        problem_info = ProblemInfo(name="test", dimension=5)
        algorithm_info = AlgorithmInfo(name="test", seed=42, parameters={'a': 1})
        
        run = SingleRunResult(
            run_id=0, seed=42, best_fitness=100.0,
            best_solution=[1, 2, 3], convergence_curve=[100],
            execution_time=1.0, iterations_completed=1, evaluations=30
        )
        
        result1 = StandardResultV2(
            result_type='single_run',
            problem_info=problem_info,
            algorithm_info=algorithm_info,
            runs=[run],
            statistics=MultiRunStatistics.from_runs([run])
        )
        
        result2 = StandardResultV2(
            result_type='single_run',
            problem_info=problem_info,
            algorithm_info=algorithm_info,
            runs=[run],
            statistics=MultiRunStatistics.from_runs([run])
        )
        
        # Same data should produce same checksum
        assert result1.checksum == result2.checksum
        assert result1.verify_integrity()
        assert result2.verify_integrity()
        
        # Modify result
        result2.runs[0].best_fitness = 200.0
        result2.checksum = result2.calculate_checksum()
        
        # Different data should produce different checksum
        assert result1.checksum != result2.checksum
    
    def test_json_serialization(self):
        """Test JSON serialization and deserialization."""
        # Create result
        problem_info = ProblemInfo(name="test", dimension=5)
        algorithm_info = AlgorithmInfo(name="test", seed=42)
        
        run = SingleRunResult(
            run_id=0, seed=42, best_fitness=100.0,
            best_solution=np.array([1, 2, 3]), 
            convergence_curve=[150, 120, 100],
            execution_time=1.5, iterations_completed=3, evaluations=90
        )
        
        result = StandardResultV2(
            result_type='single_run',
            problem_info=problem_info,
            algorithm_info=algorithm_info,
            runs=[run],
            statistics=MultiRunStatistics.from_runs([run])
        )
        
        # Serialize to JSON
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            result.to_json(f.name)
            temp_path = f.name
        
        try:
            # Deserialize
            loaded = StandardResultV2.from_json(temp_path)
            
            # Verify key fields
            assert loaded.result_id == result.result_id
            assert loaded.checksum == result.checksum
            assert loaded.algorithm_info.name == "test"
            assert loaded.runs[0].best_fitness == 100.0
            
        finally:
            Path(temp_path).unlink()
    
    def test_reproducibility_info(self):
        """Test reproducibility information extraction."""
        exec_info = ExecutionInfoV2.start_tracking(seed=12345)
        
        result = StandardResultV2(
            result_type='single_run',
            problem_info=ProblemInfo(name="test", dimension=5),
            algorithm_info=AlgorithmInfo(name="test", seed=12345, parameters={'p': 0.5}),
            runs=[SingleRunResult(
                run_id=0, seed=12345, best_fitness=100,
                best_solution=[], convergence_curve=[100],
                execution_time=1, iterations_completed=1, evaluations=30
            )],
            statistics=MultiRunStatistics.from_runs([]),
            execution_info=exec_info
        )
        
        repro_info = result.get_reproducibility_info()
        
        assert repro_info['algorithm']['seed'] == 12345
        assert repro_info['algorithm']['parameters']['p'] == 0.5
        assert repro_info['seeds'] == [12345]
        assert repro_info['execution']['random_seed'] == 12345
        assert 'dependencies' in repro_info
        assert isinstance(repro_info['dependencies'], list)


class TestResultAdapter:
    """Test the result adapter for compatibility."""
    
    def test_adapter_creation(self):
        """Test creating result adapter."""
        adapter = ResultAdapter(use_v2=True, auto_migrate=True)
        
        assert adapter.use_v2 is True
        assert adapter.auto_migrate is True
        assert adapter.tracker is not None
        assert adapter.database is not None
    
    def test_create_v2_result(self):
        """Test creating v2 result through adapter."""
        adapter = get_result_adapter()
        
        # Mock algorithm and problem
        class MockAlgorithm:
            __class__.__name__ = 'MockAlgo'
            population_size = 30
            max_iterations = 100
            def get_parameters(self): return {'param1': 0.5}
        
        class MockProblem:
            name = 'mock_problem'
            dimension = 10
        
        result = adapter.create_result(
            algorithm=MockAlgorithm(),
            problem=MockProblem(),
            runs_data=[{
                'seed': 42,
                'best_fitness': 100.0,
                'best_solution': [1, 2, 3],
                'convergence_curve': [150, 120, 100],
                'execution_time': 1.5,
                'iterations': 3
            }]
        )
        
        assert isinstance(result, StandardResultV2)
        assert result.algorithm_info.name == 'MockAlgorithm'
        assert result.problem_info.name == 'mock_problem'
        assert len(result.runs) == 1
    
    def test_v1_to_v2_migration(self):
        """Test migrating v1 result to v2."""
        # Create v1 result
        from utils.result_schema import ExecutionInfo, ResultType
        
        v1_result = StandardResult(
            result_id="test_v1",
            result_type=ResultType.SINGLE_RUN,
            timestamp=datetime.now(),
            problem_info=ProblemInfo(name="test", dimension=5),
            algorithm_info=AlgorithmInfo(name="test", seed=42),
            execution_info=ExecutionInfo(
                start_time=datetime.now(),
                end_time=datetime.now(),
                duration_seconds=1.0,
                platform="test",
                python_version="3.8",
                cpu_count=4,
                memory_gb=8.0
            ),
            runs=[SingleRunResult(
                run_id=0, seed=42, best_fitness=100,
                best_solution=[1, 2, 3], convergence_curve=[100],
                execution_time=1, iterations_completed=1, evaluations=30
            )],
            statistics=MultiRunStatistics.from_runs([])
        )
        
        # Migrate
        v2_result = migrate_v1_to_v2(v1_result)
        
        assert isinstance(v2_result, StandardResultV2)
        assert v2_result.result_id == "test_v1"
        assert v2_result.version == "2.0.0"
        assert v2_result.algorithm_info.name == "test"
        assert v2_result.execution_info is not None
        assert v2_result.execution_info.random_seed == 42
    
    def test_save_and_load_result(self):
        """Test saving and loading results through adapter."""
        adapter = get_result_adapter()
        
        # Create a result
        result = StandardResultV2(
            result_type='single_run',
            problem_info=ProblemInfo(name="test", dimension=5),
            algorithm_info=AlgorithmInfo(name="test", seed=42),
            runs=[SingleRunResult(
                run_id=0, seed=42, best_fitness=100,
                best_solution=[1, 2, 3], convergence_curve=[100],
                execution_time=1, iterations_completed=1, evaluations=30
            )],
            statistics=MultiRunStatistics.from_runs([])
        )
        
        # Save to temp file
        with tempfile.NamedTemporaryFile(suffix='.json', delete=False) as f:
            temp_path = Path(f.name)
        
        try:
            # Save
            locations = adapter.save_result(
                result, 
                path=temp_path,
                save_to_db=False,  # Skip DB for test
                save_to_tracker=False  # Skip tracker for test
            )
            
            assert 'json_path' in locations
            assert temp_path.exists()
            
            # Load back
            loaded = adapter.load_result(temp_path)
            
            assert loaded.result_id == result.result_id
            assert loaded.algorithm_info.name == "test"
            assert loaded.checksum == result.checksum
            
        finally:
            if temp_path.exists():
                temp_path.unlink()


class TestResultBuilderV2:
    """Test the result builder for v2."""
    
    def test_create_from_algorithm_run(self):
        """Test creating result from algorithm run."""
        # Mock objects
        class MockAlgorithm:
            __class__.__name__ = 'TestAlgorithm'
            version = 'v2'
            population_size = 30
            max_iterations = 100
            def get_parameters(self): 
                return {'learning_rate': 0.1}
        
        class MockProblem:
            __class__.__name__ = 'TestProblem'
            name = 'test_instance'
            dimension = 20
            optimal_value = 50.0
        
        exec_info = ExecutionInfoV2.start_tracking(seed=999)
        exec_info.finalize()
        
        runs_data = [
            {
                'seed': 999,
                'best_fitness': 55.5,
                'best_solution': np.array([1, 2, 3]),
                'convergence_curve': [100, 80, 60, 55.5],
                'execution_time': 2.5,
                'iterations': 100,
                'evaluations': 3000
            }
        ]
        
        result = ResultBuilderV2.create_from_algorithm_run(
            algorithm=MockAlgorithm(),
            problem=MockProblem(),
            execution_info=exec_info,
            runs_data=runs_data,
            metadata={'test': True}
        )
        
        assert isinstance(result, StandardResultV2)
        assert result.algorithm_info.name == 'TestAlgorithm'
        assert result.algorithm_info.parameters['learning_rate'] == 0.1
        assert result.problem_info.name == 'test_instance'
        assert result.problem_info.optimal_value == 50.0
        assert result.statistics.best_fitness == 55.5
        assert result.statistics.n_runs == 1
        assert result.metadata['test'] is True


if __name__ == "__main__":
    pytest.main([__file__, "-v"])