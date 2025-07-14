"""
Tests for operators module.
"""
import pytest
import numpy as np
from unittest.mock import MagicMock
from utils.operators import (
    sbx_crossover,
    polynomial_mutation,
    repair_bounds,
    check_route_capacity,
    calculate_route_distance,
    split_vrp
)


class TestSBXCrossover:
    """Tests for SBX crossover operator."""
    
    def test_no_crossover(self):
        """Test when crossover is not applied."""
        parent1 = np.array([0.1, 0.2, 0.3, 0.4, 0.5])
        parent2 = np.array([0.6, 0.7, 0.8, 0.9, 1.0])
        
        # With probability 0, should return copy of parent1
        child = sbx_crossover(parent1, parent2, probability=0.0)
        assert np.array_equal(child, parent1)
    
    def test_identical_parents(self):
        """Test crossover with identical parents."""
        parent = np.array([0.5, 0.5, 0.5])
        child = sbx_crossover(parent, parent.copy())
        # Should return identical to parents
        assert np.allclose(child, parent)
    
    def test_crossover_basic(self):
        """Test basic crossover operation."""
        np.random.seed(42)
        parent1 = np.array([0.1, 0.3, 0.5, 0.7, 0.9])
        parent2 = np.array([0.2, 0.4, 0.6, 0.8, 1.0])
        
        child = sbx_crossover(parent1, parent2, probability=1.0)
        
        # Child should be different from parents (with high probability)
        assert child.shape == parent1.shape
        # Check bounds
        assert np.all(child >= 0.0) and np.all(child <= 1.0)
    
    def test_crossover_distribution_index(self):
        """Test crossover with different distribution indices."""
        parent1 = np.array([0.3, 0.4, 0.5])
        parent2 = np.array([0.7, 0.6, 0.5])
        
        # Low distribution index = more exploration
        np.random.seed(42)
        child_low = sbx_crossover(parent1, parent2, distribution_index=5)
        
        # High distribution index = more exploitation
        np.random.seed(42)
        child_high = sbx_crossover(parent1, parent2, distribution_index=30)
        
        assert child_low.shape == child_high.shape == parent1.shape


class TestPolynomialMutation:
    """Tests for polynomial mutation operator."""
    
    def test_no_mutation(self):
        """Test when mutation is not applied."""
        solution = np.array([0.5, 0.5, 0.5])
        mutated = polynomial_mutation(solution, probability=0.0)
        assert np.array_equal(mutated, solution)
    
    def test_mutation_basic(self):
        """Test basic mutation operation."""
        np.random.seed(42)
        solution = np.array([0.1, 0.5, 0.9])
        mutated = polynomial_mutation(solution, probability=1.0)
        
        # Should be different
        assert not np.array_equal(mutated, solution)
        # Should maintain bounds
        assert np.all(mutated >= 0.0) and np.all(mutated <= 1.0)
    
    def test_mutation_boundary_values(self):
        """Test mutation on boundary values."""
        solution = np.array([0.0, 0.5, 1.0])
        mutated = polynomial_mutation(solution, probability=1.0)
        
        # Should maintain bounds
        assert np.all(mutated >= 0.0) and np.all(mutated <= 1.0)
    
    def test_mutation_distribution_index(self):
        """Test mutation with different distribution indices."""
        solution = np.array([0.5, 0.5, 0.5, 0.5])
        
        # Low distribution index = more mutation
        np.random.seed(42)
        mutated_low = polynomial_mutation(solution, distribution_index=5)
        
        # High distribution index = less mutation
        np.random.seed(42)
        mutated_high = polynomial_mutation(solution, distribution_index=50)
        
        assert mutated_low.shape == mutated_high.shape == solution.shape


class TestRepairBounds:
    """Tests for repair bounds function."""
    
    def test_repair_within_bounds(self):
        """Test repair with values already within bounds."""
        solution = np.array([0.2, 0.5, 0.8])
        repaired = repair_bounds(solution, lb=0.0, ub=1.0)
        assert np.array_equal(repaired, solution)
    
    def test_repair_below_lower_bound(self):
        """Test repair of values below lower bound."""
        solution = np.array([-0.5, -1.0, 0.5])
        repaired = repair_bounds(solution, lb=0.0, ub=1.0)
        expected = np.array([0.0, 0.0, 0.5])
        assert np.array_equal(repaired, expected)
    
    def test_repair_above_upper_bound(self):
        """Test repair of values above upper bound."""
        solution = np.array([0.5, 1.5, 2.0])
        repaired = repair_bounds(solution, lb=0.0, ub=1.0)
        expected = np.array([0.5, 1.0, 1.0])
        assert np.array_equal(repaired, expected)
    
    def test_repair_custom_bounds(self):
        """Test repair with custom bounds."""
        solution = np.array([0.0, 5.0, 10.0, 15.0])
        repaired = repair_bounds(solution, lb=2.0, ub=8.0)
        expected = np.array([2.0, 5.0, 8.0, 8.0])
        assert np.array_equal(repaired, expected)
    
    def test_repair_with_inplace(self):
        """Test that repair creates a copy."""
        solution = np.array([1.5, -0.5, 0.5])
        original = solution.copy()
        repaired = repair_bounds(solution)
        
        # Original should not be modified
        assert np.array_equal(solution, original)
        # Repaired should be different
        assert not np.array_equal(repaired, original)


class TestCheckRouteCapacity:
    """Tests for route capacity checking."""
    
    def test_empty_route(self):
        """Test capacity check for empty route."""
        assert check_route_capacity([], [10, 20, 30], 100) == True
    
    def test_route_within_capacity(self):
        """Test route within capacity."""
        route = [0, 1, 2, 3, 0]  # Route with depot at start and end
        demands = [0, 10, 20, 15, 30, 40]  # Index 0 is depot
        capacity = 50
        # Total demand: 10 + 20 + 15 = 45 < 50 (depot not counted)
        assert check_route_capacity(route, demands, capacity) == True
    
    def test_route_exceeds_capacity(self):
        """Test route exceeding capacity."""
        route = [0, 1, 2, 3, 0]  # Route with depot at start and end
        demands = [0, 20, 25, 30]
        capacity = 50
        # Total demand: 20 + 25 + 30 = 75 > 50 (depot not counted)
        assert check_route_capacity(route, demands, capacity) == False
    
    def test_route_equals_capacity(self):
        """Test route exactly at capacity."""
        route = [0, 1, 2, 0]  # Route with depot
        demands = [0, 25, 25]
        capacity = 50
        # Total demand: 25 + 25 = 50
        assert check_route_capacity(route, demands, capacity) == True
    
    def test_depot_in_route(self):
        """Test route containing depot (index 0)."""
        route = [0, 1, 2, 0]  # Depot at start and end
        demands = [0, 20, 30]
        capacity = 60
        # Should ignore depot (index 0)
        # Total demand: 20 + 30 = 50 < 60
        assert check_route_capacity(route, demands, capacity) == True


class TestCalculateRouteDistance:
    """Tests for route distance calculation."""
    
    def test_empty_route(self):
        """Test distance for empty route."""
        distance_matrix = np.array([[0, 10], [10, 0]])
        assert calculate_route_distance([], distance_matrix) == 0.0
    
    def test_single_customer_route(self):
        """Test distance for single customer route."""
        distance_matrix = np.array([
            [0, 10, 20],
            [10, 0, 15],
            [20, 15, 0]
        ])
        route = [0, 1, 0]  # Depot -> Customer 1 -> Depot
        # Distance: 0->1 (10) + 1->0 (10) = 20
        assert calculate_route_distance(route, distance_matrix) == 20.0
    
    def test_multiple_customers_route(self):
        """Test distance for multiple customers."""
        distance_matrix = np.array([
            [0, 10, 20, 30],
            [10, 0, 15, 25],
            [20, 15, 0, 12],
            [30, 25, 12, 0]
        ])
        route = [0, 1, 2, 3, 0]
        # Distance: 0->1 (10) + 1->2 (15) + 2->3 (12) + 3->0 (30) = 67
        assert calculate_route_distance(route, distance_matrix) == 67.0
    
    def test_route_without_return(self):
        """Test route that doesn't return to depot."""
        distance_matrix = np.array([
            [0, 5, 10],
            [5, 0, 8],
            [10, 8, 0]
        ])
        route = [0, 1, 2]  # No return to depot
        # Distance: 0->1 (5) + 1->2 (8) = 13
        assert calculate_route_distance(route, distance_matrix) == 13.0


class TestSplitVRP:
    """Tests for Split algorithm for VRP."""
    
    @pytest.fixture
    def mock_problem(self):
        """Create a mock VRP problem."""
        problem = MagicMock()
        problem.dimension = 6  # 5 customers + 1 depot
        problem.capacity = 30
        problem.depot_index = 0  # Add depot index
        problem.demands = np.array([0, 10, 8, 12, 5, 15])  # depot=0, adjusted for capacity
        problem.distance_matrix = np.array([
            [0, 10, 20, 30, 40, 50],
            [10, 0, 12, 22, 32, 42],
            [20, 12, 0, 14, 24, 34],
            [30, 22, 14, 0, 16, 26],
            [40, 32, 24, 16, 0, 18],
            [50, 42, 34, 26, 18, 0]
        ])
        return problem
    
    def test_split_basic(self, mock_problem):
        """Test basic split operation."""
        # Permutation of customers (excluding depot)
        permutation = [1, 2, 3, 4, 5]  # Visit order
        
        routes, total_distance = split_vrp(permutation, mock_problem)
        
        # Check that routes are valid
        assert isinstance(routes, list)
        assert all(isinstance(route, list) for route in routes)
        
        # Check capacity constraints
        for route in routes:
            customers = [c for c in route if c != 0]
            total_demand = sum(mock_problem.demands[c] for c in customers)
            assert total_demand <= mock_problem.capacity
        
        # Check total distance is positive
        assert total_distance > 0
    
    def test_split_single_customer_routes(self, mock_problem):
        """Test split when each customer needs separate route."""
        # Set demands high so each customer needs own route
        mock_problem.demands = np.array([0, 25, 28, 30, 29, 27])
        permutation = [1, 2, 3, 4, 5]
        
        routes, total_distance = split_vrp(permutation, mock_problem)
        
        # Should have 5 routes (one per customer)
        assert len(routes) == 5
        # Each route should have one customer
        for route in routes:
            customers = [c for c in route if c != 0]
            assert len(customers) == 1
    
    def test_split_all_fit_one_route(self, mock_problem):
        """Test split when all customers fit in one route."""
        # Set small demands
        mock_problem.demands = np.array([0, 2, 3, 4, 5, 6])
        mock_problem.capacity = 25  # Total demand = 20
        permutation = [1, 2, 3, 4, 5]
        
        routes, total_distance = split_vrp(permutation, mock_problem)
        
        # Should have 1 route
        assert len(routes) == 1
        # Route should contain all customers
        customers = [c for c in routes[0] if c != 0]
        assert set(customers) == set(permutation)
    
    def test_split_empty_permutation(self, mock_problem):
        """Test split with empty permutation."""
        routes, total_distance = split_vrp([], mock_problem)
        
        assert routes == []
        assert total_distance == 0.0
    
    def test_split_respects_order(self, mock_problem):
        """Test that split respects customer order."""
        permutation = [5, 4, 3, 2, 1]
        routes, total_distance = split_vrp(permutation, mock_problem)
        
        # Flatten routes to get customer order
        customers_in_routes = []
        for route in routes:
            customers_in_routes.extend([c for c in route if c != 0])
        
        # Order should be preserved
        assert customers_in_routes == permutation


if __name__ == "__main__":
    pytest.main([__file__, "-v"])