"""
Test metadata integration in algorithm results.
"""

import pytest
import json
from pathlib import Path
import tempfile

from algorithms.hoa_v2 import HOAV2
from algorithms.egto_v2 import EGTOV2
from problems.vrp_v2 import VRPProblemV2
from utils.result_metadata_integration import (
    MetadataEnhancedAlgorithm, wrap_algorithm_with_metadata,
    ensure_metadata_in_result, ResourceMonitor
)
from utils.result_schema_v2 import (
    StandardResultV2, SystemInfo, GitInfo, ExecutionInfoV2,
    DependencyInfo
)


class TestMetadataIntegration:
    """Test suite for metadata integration."""
    
    @pytest.fixture
    def problem(self):
        """Create a test problem."""
        return VRPProblemV2("data/vrp/A-n32-k5.vrp")
    
    def test_resource_monitor(self):
        """Test resource monitoring functionality."""
        monitor = ResourceMonitor(sample_interval=0.1)
        
        # Start monitoring
        monitor.start()
        
        # Do some work
        import time
        import numpy as np
        for _ in range(5):
            _ = np.random.rand(1000, 1000)
            time.sleep(0.1)
        
        # Stop and get stats
        stats = monitor.stop()
        
        # Verify we got samples
        assert len(stats['cpu_samples']) > 0
        assert len(stats['memory_samples']) > 0
        assert stats['cpu_avg'] >= 0
        assert stats['memory_peak_mb'] > 0
    
    def test_wrap_algorithm(self, problem):
        """Test wrapping an algorithm with metadata capture."""
        # Wrap HOA algorithm
        MetadataHOA = wrap_algorithm_with_metadata(HOAV2)
        
        # Create instance
        algo = MetadataHOA(
            problem=problem,
            population_size=10,
            max_iterations=5,
            seed=42
        )
        
        # Verify it's wrapped correctly
        assert hasattr(algo, 'capture_metadata')
        assert hasattr(algo, 'monitor_resources')
        assert algo.capture_metadata is True
        assert algo.monitor_resources is True
    
    def test_metadata_capture(self, problem):
        """Test that metadata is captured during execution."""
        # Create wrapped algorithm
        MetadataHOA = wrap_algorithm_with_metadata(HOAV2)
        algo = MetadataHOA(
            problem=problem,
            population_size=10,
            max_iterations=5,
            seed=42
        )
        
        # Run algorithm
        result = algo.execute()
        
        # Verify metadata was captured
        assert algo.system_info is not None
        assert isinstance(algo.system_info, SystemInfo)
        assert algo.execution_info is not None
        assert isinstance(algo.execution_info, ExecutionInfoV2)
        assert algo.dependencies is not None
        assert len(algo.dependencies) > 0
    
    def test_complete_result_generation(self, problem):
        """Test generation of complete result with metadata."""
        # Create and run wrapped algorithm
        MetadataHOA = wrap_algorithm_with_metadata(HOAV2)
        algo = MetadataHOA(
            problem=problem,
            population_size=10,
            max_iterations=5,
            seed=42
        )
        algo.execute()
        
        # Get complete result
        result = algo.get_complete_result()
        
        # Verify result structure
        assert isinstance(result, StandardResultV2)
        assert result.result_id is not None
        assert result.version == "2.0.0"
        
        # Verify metadata presence
        assert result.system_info is not None
        assert result.execution_info is not None
        assert result.dependencies is not None
        assert result.checksum is not None
        
        # Verify problem info
        assert result.problem_info.type == "VRPProblemV2"
        assert result.problem_info.dimension == problem.dimension
        
        # Verify algorithm info
        assert result.algorithm_info.name == "MetadataHOAV2"
        assert result.algorithm_info.seed == 42
        
        # Verify execution info
        assert result.execution_info.random_seed == 42
        assert result.execution_info.duration_seconds > 0
    
    def test_ensure_metadata_in_result(self):
        """Test ensuring metadata in existing results."""
        # Create a simple result dictionary
        simple_result = {
            'algorithm_name': 'TestAlgorithm',
            'instance_name': 'test-instance',
            'fitness': 100.5,
            'execution_time': 1.23,
            'seed': 42,
            'convergence_curve': [150, 120, 100.5]
        }
        
        # Ensure metadata
        enhanced_result = ensure_metadata_in_result(simple_result)
        
        # Verify it's now a StandardResultV2
        assert isinstance(enhanced_result, StandardResultV2)
        assert enhanced_result.system_info is not None
        assert enhanced_result.dependencies is not None
        assert enhanced_result.checksum is not None
    
    def test_reproducibility_with_metadata(self, problem):
        """Test that same seed produces same results with metadata."""
        results = []
        
        # Run twice with same seed
        for _ in range(2):
            MetadataHOA = wrap_algorithm_with_metadata(HOAV2)
            algo = MetadataHOA(
                problem=problem,
                population_size=10,
                max_iterations=10,
                seed=42
            )
            algo.execute()
            results.append(algo.get_complete_result())
        
        # Verify results match
        assert results[0].runs[0].best_fitness == results[1].runs[0].best_fitness
        assert results[0].runs[0].convergence_curve == results[1].runs[0].convergence_curve
        assert results[0].execution_info.random_seed == results[1].execution_info.random_seed
    
    def test_result_serialization(self, problem):
        """Test that results can be serialized and deserialized."""
        # Create and run algorithm
        MetadataHOA = wrap_algorithm_with_metadata(HOAV2)
        algo = MetadataHOA(
            problem=problem,
            population_size=10,
            max_iterations=5,
            seed=42
        )
        algo.execute()
        
        # Get result
        result = algo.get_complete_result()
        
        # Serialize to JSON
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(result.to_dict(), f, default=str)
            temp_path = f.name
        
        try:
            # Read back
            with open(temp_path, 'r') as f:
                loaded_data = json.load(f)
            
            # Verify key fields
            assert loaded_data['result_id'] == result.result_id
            assert loaded_data['checksum'] == result.checksum
            assert loaded_data['system_info']['platform'] == result.system_info.platform
            assert loaded_data['runs'][0]['best_fitness'] == result.runs[0].best_fitness
            
        finally:
            # Clean up
            Path(temp_path).unlink()
    
    def test_resource_monitoring_accuracy(self, problem):
        """Test that resource monitoring provides reasonable values."""
        # Run with resource monitoring
        MetadataHOA = wrap_algorithm_with_metadata(
            HOAV2,
            monitor_resources=True
        )
        algo = MetadataHOA(
            problem=problem,
            population_size=20,
            max_iterations=10,
            seed=42
        )
        algo.execute()
        
        # Get result
        result = algo.get_complete_result()
        
        # Verify resource metrics
        assert result.execution_info.cpu_percent_avg >= 0
        assert result.execution_info.cpu_percent_avg <= 100 * algo.system_info.cpu_count
        assert result.execution_info.memory_peak_mb > 0
        assert result.execution_info.memory_avg_mb > 0
        assert result.execution_info.memory_peak_mb >= result.execution_info.memory_avg_mb
    
    def test_different_algorithms_metadata(self, problem):
        """Test metadata capture works for different algorithms."""
        algorithms = [HOAV2, EGTOV2]
        
        for AlgoClass in algorithms:
            # Wrap algorithm
            MetadataAlgo = wrap_algorithm_with_metadata(AlgoClass)
            
            # Run
            algo = MetadataAlgo(
                problem=problem,
                population_size=10,
                max_iterations=5,
                seed=42
            )
            algo.execute()
            
            # Get result
            result = algo.get_complete_result()
            
            # Verify metadata
            assert result.system_info is not None
            assert result.algorithm_info.name == f"Metadata{AlgoClass.__name__}"
            assert result.checksum is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])