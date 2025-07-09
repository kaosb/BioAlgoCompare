"""
Tests para los mixins de algoritmos.

Este módulo contiene pruebas unitarias para todos los mixins
de operadores VRP, selección, inicialización y convergencia.
"""

import pytest
import numpy as np
import tempfile
import os
from unittest.mock import Mock, patch

from algorithms.mixins import (
    # VRP operators
    VRPCrossoverMixin,
    VRPMutationMixin,
    VRPLocalSearchMixin,
    VRPRepairMixin,
    VRPDiversityMixin,
    # Selection operators
    TournamentSelectionMixin,
    RouletteSelectionMixin,
    RankSelectionMixin,
    ElitismMixin,
    # Initialization operators
    RandomInitializationMixin,
    NearestNeighborInitializationMixin,
    SavingsInitializationMixin,
    ClusterInitializationMixin,
    # Convergence operators
    ConvergenceTrackingMixin,
    AdaptiveParameterMixin,
    StagnationDetectionMixin,
    RestartMixin
)


class MockIndividual:
    """Mock individual para testing."""
    def __init__(self, fitness_value, position=None):
        self._fitness = fitness_value
        self.position = position if position is not None else np.random.rand(10)
    
    def fitness(self):
        return self._fitness


class TestVRPCrossoverMixin:
    """Tests para VRPCrossoverMixin."""
    
    class CrossoverTest(VRPCrossoverMixin):
        pass
    
    def setup_method(self):
        self.mixin = self.CrossoverTest()
    
    def test_order_crossover(self):
        """Test Order Crossover."""
        parent1 = np.array([1, 2, 3, 4, 5, 6, 7, 8])
        parent2 = np.array([2, 7, 5, 8, 4, 1, 6, 3])
        
        child1, child2 = self.mixin.order_crossover(parent1, parent2)
        
        # Verificar que son permutaciones válidas
        assert len(child1) == len(parent1)
        assert len(child2) == len(parent2)
        assert set(child1) == set(parent1)
        assert set(child2) == set(parent2)
        assert len(np.unique(child1)) == len(child1)
        assert len(np.unique(child2)) == len(child2)
    
    def test_pmx_crossover(self):
        """Test Partially Mapped Crossover."""
        parent1 = np.array([1, 2, 3, 4, 5, 6, 7, 8])
        parent2 = np.array([2, 7, 5, 8, 4, 1, 6, 3])
        
        child1, child2 = self.mixin.pmx_crossover(parent1, parent2)
        
        # Verificar que son permutaciones válidas
        assert len(child1) == len(parent1)
        assert len(child2) == len(parent2)
        assert set(child1) == set(parent1)
        assert set(child2) == set(parent2)
        assert len(np.unique(child1)) == len(child1)
        assert len(np.unique(child2)) == len(child2)


class TestVRPMutationMixin:
    """Tests para VRPMutationMixin."""
    
    class MutationTest(VRPMutationMixin):
        pass
    
    def setup_method(self):
        self.mixin = self.MutationTest()
    
    def test_swap_mutation(self):
        """Test swap mutation."""
        original = np.array([1, 2, 3, 4, 5])
        mutated = self.mixin.swap_mutation(original.copy())
        
        # Debe mantener los mismos elementos
        assert set(mutated) == set(original)
        assert len(mutated) == len(original)
    
    def test_insertion_mutation(self):
        """Test insertion mutation."""
        original = np.array([1, 2, 3, 4, 5])
        mutated = self.mixin.insertion_mutation(original.copy())
        
        # Debe mantener los mismos elementos
        assert set(mutated) == set(original)
        assert len(mutated) == len(original)
    
    def test_inversion_mutation(self):
        """Test inversion mutation."""
        original = np.array([1, 2, 3, 4, 5])
        mutated = self.mixin.inversion_mutation(original.copy())
        
        # Debe mantener los mismos elementos
        assert set(mutated) == set(original)
        assert len(mutated) == len(original)
    
    def test_scramble_mutation(self):
        """Test scramble mutation."""
        original = np.array([1, 2, 3, 4, 5])
        mutated = self.mixin.scramble_mutation(original.copy(), mutation_rate=1.0)
        
        # Debe mantener los mismos elementos
        assert set(mutated) == set(original)
        assert len(mutated) == len(original)


class TestVRPLocalSearchMixin:
    """Tests para VRPLocalSearchMixin."""
    
    class LocalSearchTest(VRPLocalSearchMixin):
        def __init__(self):
            self.problem = Mock()
            # Matriz de distancias simple
            self.problem.distance_matrix = np.array([
                [0, 10, 15, 20, 25],
                [10, 0, 35, 25, 30],
                [15, 35, 0, 30, 20],
                [20, 25, 30, 0, 15],
                [25, 30, 20, 15, 0]
            ])
            
        def _route_cost(self, route, distance_matrix):
            """Calcula el costo de una ruta."""
            cost = 0
            for i in range(len(route) - 1):
                cost += distance_matrix[route[i]][route[i+1]]
            return cost
    
    def setup_method(self):
        self.mixin = self.LocalSearchTest()
    
    def test_two_opt(self):
        """Test 2-opt improvement."""
        route = [0, 1, 2, 3, 4, 0]
        improved = self.mixin.two_opt(route, self.mixin.problem.distance_matrix)
        
        # Debe ser una ruta válida
        assert improved[0] == 0
        assert improved[-1] == 0
        assert set(improved[1:-1]) == {1, 2, 3, 4}
    
    def test_three_opt(self):
        """Test 3-opt improvement."""
        # Skip test if method doesn't exist
        if not hasattr(self.mixin, 'three_opt'):
            pytest.skip("three_opt not implemented")
        
        route = [0, 1, 2, 3, 4, 0]
        improved = self.mixin.three_opt(route, self.mixin.problem.distance_matrix)
        
        # Debe ser una ruta válida
        assert improved[0] == 0
        assert improved[-1] == 0
        assert set(improved[1:-1]) == {1, 2, 3, 4}
    
    def test_or_opt(self):
        """Test Or-opt improvement."""
        route = [0, 1, 2, 3, 4, 0]
        improved = self.mixin.or_opt(route, self.mixin.problem.distance_matrix)
        
        # Debe ser una ruta válida
        assert improved[0] == 0
        assert improved[-1] == 0
        assert set(improved[1:-1]) == {1, 2, 3, 4}


class TestSelectionOperators:
    """Tests para operadores de selección."""
    
    def setup_method(self):
        # Crear población de prueba
        self.population = [
            MockIndividual(10),
            MockIndividual(20),
            MockIndividual(30),
            MockIndividual(40),
            MockIndividual(50)
        ]
    
    def test_tournament_selection(self):
        """Test tournament selection."""
        class TournamentTest(TournamentSelectionMixin):
            pass
        
        mixin = TournamentTest()
        selected = mixin.tournament_selection(self.population, tournament_size=3, n_select=2)
        
        assert len(selected) == 2
        assert all(ind in self.population for ind in selected)
    
    def test_roulette_selection(self):
        """Test roulette wheel selection."""
        class RouletteTest(RouletteSelectionMixin):
            pass
        
        mixin = RouletteTest()
        selected = mixin.roulette_wheel_selection(self.population, n_select=2)
        
        assert len(selected) == 2
        assert all(ind in self.population for ind in selected)
    
    def test_rank_selection(self):
        """Test rank-based selection."""
        class RankTest(RankSelectionMixin):
            pass
        
        mixin = RankTest()
        selected = mixin.rank_selection(self.population, n_select=2)
        
        assert len(selected) == 2
        assert all(ind in self.population for ind in selected)
    
    def test_elitism(self):
        """Test elitism operations."""
        class ElitismTest(ElitismMixin):
            pass
        
        mixin = ElitismTest()
        elite = mixin.select_elite(self.population, n_elite=2)
        
        assert len(elite) == 2
        assert elite[0].fitness() <= elite[1].fitness()
        assert elite[0].fitness() == 10  # Best individual


class TestInitializationOperators:
    """Tests para operadores de inicialización."""
    
    def test_random_initialization(self):
        """Test random initialization."""
        class RandomTest(RandomInitializationMixin):
            pass
        
        mixin = RandomTest()
        
        # Test random permutation
        perm = mixin.random_permutation(10)
        assert len(perm) == 10
        assert set(perm) == set(range(1, 11))
        
        # Test random keys
        keys = mixin.random_keys_initialization(10)
        assert len(keys) == 10
        assert all(0 <= k <= 1 for k in keys)
    
    def test_nearest_neighbor_initialization(self):
        """Test nearest neighbor initialization."""
        class NNTest(NearestNeighborInitializationMixin):
            pass
        
        mixin = NNTest()
        
        # Matriz de distancias simple
        distance_matrix = np.array([
            [0, 10, 20, 30],
            [10, 0, 15, 25],
            [20, 15, 0, 12],
            [30, 25, 12, 0]
        ])
        
        capacity = 100
        demands = np.array([0, 20, 30, 25])  # depot + 3 customers
        
        routes = mixin.nearest_neighbor_solution(distance_matrix, capacity, demands)
        
        # Verificar que es una solución válida
        assert all(route[0] == 0 and route[-1] == 0 for route in routes)
        visited = set()
        for route in routes:
            visited.update(route[1:-1])
        assert visited == {1, 2, 3}
    
    def test_savings_initialization(self):
        """Test savings algorithm initialization."""
        class SavingsTest(SavingsInitializationMixin):
            pass
        
        mixin = SavingsTest()
        
        # Matriz de distancias simple
        distance_matrix = np.array([
            [0, 10, 20, 30],
            [10, 0, 15, 25],
            [20, 15, 0, 12],
            [30, 25, 12, 0]
        ])
        
        capacity = 100
        demands = np.array([0, 20, 30, 25])
        
        routes = mixin.savings_algorithm(distance_matrix, capacity, demands)
        
        # Verificar que es una solución válida
        assert all(route[0] == 0 and route[-1] == 0 for route in routes)


class TestConvergenceOperators:
    """Tests para operadores de convergencia."""
    
    def test_convergence_tracking(self):
        """Test convergence tracking."""
        class TrackingTest(ConvergenceTrackingMixin):
            def __init__(self):
                super().__init__()
        
        mixin = TrackingTest()
        
        # Simular algunas iteraciones
        population = [MockIndividual(100 - i*10) for i in range(5)]
        
        for i in range(10):
            # Mejorar población
            for ind in population:
                ind._fitness -= 1
            
            mixin.track_iteration(population, i, i * 0.1)
        
        # Verificar métricas
        metrics = mixin.get_convergence_metrics()
        assert metrics['total_iterations'] == 10
        assert metrics['best_fitness'] < 100
        assert metrics['total_improvement'] > 0
    
    def test_adaptive_parameters(self):
        """Test adaptive parameter control."""
        class AdaptiveTest(AdaptiveParameterMixin):
            def __init__(self):
                super().__init__()
        
        mixin = AdaptiveTest()
        
        # Registrar parámetro
        mixin.register_adaptive_parameter('mutation_rate', 0.5, 0.1, 1.0)
        
        # Verificar valor inicial
        assert mixin.get_adaptive_parameter('mutation_rate') == 0.5
        
        # Actualizar parámetros
        mixin.update_adaptive_parameters(50, 100)
        
        # Verificar que cambió
        new_value = mixin.get_adaptive_parameter('mutation_rate')
        assert 0.1 <= new_value <= 1.0
        assert new_value != 0.5  # Debería haber cambiado
    
    def test_stagnation_detection(self):
        """Test stagnation detection."""
        class StagnationTest(StagnationDetectionMixin):
            def __init__(self):
                super().__init__()
        
        mixin = StagnationTest()
        mixin.configure_stagnation_detection(window=5, threshold=0.001)
        
        # Simular estancamiento
        for i in range(10):
            stagnation = mixin.check_stagnation(100.0, 0.5)  # Sin mejora
        
        # Después de suficientes iteraciones sin mejora
        assert stagnation['fitness_stagnation'] == True
    
    def test_restart_strategies(self):
        """Test restart strategies."""
        class RestartTest(RestartMixin):
            def __init__(self):
                super().__init__()
                
            def _create_individual(self):
                return MockIndividual(np.random.rand() * 100)
        
        mixin = RestartTest()
        mixin.configure_restart(enabled=True, threshold=10, strategy='partial')
        
        # Crear población
        population = [MockIndividual(i * 10) for i in range(10)]
        
        # Verificar condición de reinicio
        should_restart = mixin.check_restart_condition(15)  # > threshold
        assert should_restart == True
        
        # Ejecutar reinicio
        new_population = mixin.perform_restart(population, 100)
        assert len(new_population) == len(population)
        assert mixin.restart_count == 1


if __name__ == '__main__':
    pytest.main([__file__, '-v'])