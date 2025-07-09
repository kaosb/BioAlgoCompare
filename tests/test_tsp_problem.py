"""
Tests for TSP problem implementation.
"""

import pytest
import numpy as np
import os
from problems import TSPProblem, ContinuousAdapter
from problems.discrete.base import PermutationProblem
from algorithms.woa_v2 import WOAV2
from algorithms.gto_v2 import GTOV2


class TestTSPProblem:
    """Test TSP problem implementation."""
    
    def test_tsp_from_coordinates(self):
        """Test TSP creation from coordinates."""
        # Simple 4-city square
        coords = np.array([
            [0, 0],
            [1, 0],
            [1, 1],
            [0, 1]
        ])
        
        tsp = TSPProblem(coordinates=coords)
        
        # Check properties
        assert tsp.n_cities == 4
        assert tsp.dimension == 4
        assert tsp.search_space_size == 24  # 4!
        
        # Check distance matrix
        assert tsp.distance_matrix[0, 1] == 1.0
        assert tsp.distance_matrix[0, 2] == pytest.approx(np.sqrt(2))
        assert tsp.distance_matrix[0, 3] == 1.0
    
    def test_tsp_from_distance_matrix(self):
        """Test TSP creation from distance matrix."""
        # Create symmetric distance matrix
        dist_matrix = np.array([
            [0, 10, 15, 20],
            [10, 0, 35, 25],
            [15, 35, 0, 30],
            [20, 25, 30, 0]
        ])
        
        tsp = TSPProblem(distance_matrix=dist_matrix, name="Test")
        
        assert tsp.n_cities == 4
        assert tsp.name == "Test-4"
        assert tsp.get_distance(0, 2) == 15
    
    def test_tour_evaluation(self):
        """Test tour evaluation."""
        coords = np.array([
            [0, 0],
            [1, 0],
            [1, 1],
            [0, 1]
        ])
        tsp = TSPProblem(coordinates=coords)
        
        # Optimal tour for square: 0->1->2->3->0
        tour = [0, 1, 2, 3]
        distance = tsp.evaluate(tour)
        assert distance == 4.0  # Perimeter of unit square
        
        # Suboptimal tour: 0->2->1->3->0
        tour2 = [0, 2, 1, 3]
        distance2 = tsp.evaluate(tour2)
        assert distance2 > 4.0
    
    def test_continuous_encoding_decoding(self):
        """Test continuous to discrete conversion."""
        tsp = TSPProblem(coordinates=np.random.rand(5, 2))
        
        # Random continuous vector
        continuous = np.array([0.3, 0.8, 0.1, 0.6, 0.4])
        
        # Encode to permutation
        tour = tsp.encode_continuous(continuous)
        assert len(tour) == 5
        assert set(tour) == {0, 1, 2, 3, 4}
        assert tour == [2, 0, 4, 3, 1]  # Sorted by continuous values
        
        # Decode back
        continuous2 = tsp.decode_to_continuous(tour)
        assert len(continuous2) == 5
        assert np.all(continuous2 >= 0) and np.all(continuous2 <= 1)
    
    def test_nearest_neighbor_heuristic(self):
        """Test nearest neighbor construction."""
        # Create simple instance where NN is optimal
        coords = np.array([
            [0, 0],
            [1, 0],
            [2, 0],
            [3, 0]
        ])
        tsp = TSPProblem(coordinates=coords)
        
        tour, distance = tsp.nearest_neighbor_heuristic(start_city=0)
        
        # Should visit cities in order
        assert tour == [0, 1, 2, 3]
        assert distance == 6.0  # 1+1+1+3
    
    def test_two_opt_improvement(self):
        """Test 2-opt local search."""
        # Create instance where initial tour can be improved
        coords = np.array([
            [0, 0],
            [2, 0],
            [2, 2],
            [0, 2]
        ])
        tsp = TSPProblem(coordinates=coords)
        
        # Bad initial tour with crossing
        bad_tour = [0, 2, 1, 3]  # Creates an X shape
        initial_dist = tsp.evaluate(bad_tour)
        
        # Improve with 2-opt
        improved_tour, improved_dist = tsp.two_opt_improvement(bad_tour)
        
        # Should remove the crossing
        assert improved_dist < initial_dist
        assert improved_tour in [[0, 1, 2, 3], [0, 3, 2, 1]]  # Square tour
    
    def test_random_solution(self):
        """Test random solution generation."""
        tsp = TSPProblem(coordinates=np.random.rand(6, 2))
        
        # Generate multiple random solutions
        tours = [tsp.random_solution() for _ in range(10)]
        
        for tour in tours:
            assert len(tour) == 6
            assert set(tour) == set(range(6))
            assert tsp.is_feasible(tour)
    
    def test_tsplib_loading(self):
        """Test loading from TSPLIB format."""
        tsp = TSPProblem.from_tsplib("data/tsp/berlin10.tsp")
        
        assert tsp.n_cities == 10
        assert tsp.name == "berlin10-10"
        assert hasattr(tsp, 'coordinates')
        
        # Check that distances are computed correctly
        assert tsp.distance_matrix[0, 0] == 0
        assert tsp.distance_matrix[0, 1] > 0
    
    def test_generate_random(self):
        """Test random instance generation."""
        tsp = TSPProblem.generate_random(n_cities=15, seed=42)
        
        assert tsp.n_cities == 15
        assert tsp.name == "Random-15"
        assert tsp.coordinates.shape == (15, 2)
        
        # With same seed should generate same instance
        tsp2 = TSPProblem.generate_random(n_cities=15, seed=42)
        np.testing.assert_array_equal(tsp.coordinates, tsp2.coordinates)
    
    def test_with_continuous_adapter(self):
        """Test TSP with continuous adapter for algorithms."""
        # Create TSP instance
        tsp = TSPProblem.generate_random(n_cities=10, seed=123)
        
        # Adapt for continuous algorithms
        adapted = ContinuousAdapter(tsp)
        
        # Should work with algorithms
        algo = WOAV2(adapted, population_size=20, max_iterations=50)
        best = algo.execute()
        
        # Convert solution to tour
        tour = tsp.encode_continuous(best.position)
        distance = tsp.evaluate(tour)
        
        assert len(tour) == 10
        assert distance > 0
    
    def test_save_solution(self, tmp_path):
        """Test saving solution to file."""
        tsp = TSPProblem.generate_random(n_cities=5)
        tour = [0, 2, 4, 1, 3]
        
        filename = tmp_path / "solution.tour"
        tsp.save_solution(tour, str(filename))
        
        # Check file contents
        with open(filename, 'r') as f:
            content = f.read()
        
        assert "TOUR_SECTION" in content
        assert "1\n3\n5\n2\n4\n" in content  # 1-based indexing
    
    def test_get_neighbors(self):
        """Test 2-opt neighborhood generation."""
        tsp = TSPProblem.generate_random(n_cities=5)
        tour = [0, 1, 2, 3, 4]
        
        neighbors = tsp.get_neighbors(tour)
        
        # For n=5, should have C(5,2) - adjacent pairs = 10 - 4 = 6 neighbors
        assert len(neighbors) > 0
        
        # All neighbors should be valid tours
        for neighbor in neighbors:
            assert len(neighbor) == 5
            assert set(neighbor) == set(range(5))


class TestTSPWithAlgorithms:
    """Test TSP with different algorithms."""
    
    def test_multiple_algorithms(self):
        """Test TSP with multiple algorithms."""
        # Create medium-sized instance
        tsp = TSPProblem.generate_random(n_cities=20, seed=999)
        adapted = ContinuousAdapter(tsp)
        
        # Test with different algorithms
        algorithms = [
            WOAV2(adapted, population_size=30, max_iterations=100),
            GTOV2(adapted, population_size=30, max_iterations=100)
        ]
        
        results = []
        for algo in algorithms:
            best = algo.execute()
            tour = tsp.encode_continuous(best.position)
            distance = tsp.evaluate(tour)
            results.append(distance)
        
        # All should find reasonable solutions
        for dist in results:
            assert dist > 0
            assert dist < 1000  # Reasonable upper bound for random 20-city


if __name__ == "__main__":
    pytest.main([__file__, "-v"])