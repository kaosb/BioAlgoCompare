#!/usr/bin/env python3
"""
Test del algoritmo FGO (Flamingo Optimization Algorithm).
"""

import numpy as np
import pytest
from unittest.mock import MagicMock, patch
from algorithms.fgo_v2 import FGOV2, FlamingoV2
from algorithms.base_v2 import MetaheuristicAlgorithm


class MockProblem:
    """Problema mock para pruebas."""
    
    def __init__(self, dimension=5):
        self.dimension = dimension
        self.eval_count = 0
    
    def get_dimension(self):
        return self.dimension
    
    @property
    def lower_bounds(self):
        return np.zeros(self.dimension)
    
    @property
    def upper_bounds(self):
        return np.ones(self.dimension)
    
    def evaluate(self, solution):
        """Función de evaluación simple para test."""
        self.eval_count += 1
        # Función simple: suma de los elementos
        return np.sum(solution)


def test_flamingo_initialization():
    """Test de inicialización del individuo Flamingo."""
    np.random.seed(42)  # Para reproducibilidad
    
    problem = MockProblem(dimension=5)
    flamingo = FlamingoV2(problem)
    
    # Verificar inicialización
    assert flamingo.problem == problem
    assert flamingo.dimension == 5
    assert flamingo.position.shape == (5,)
    assert flamingo._fitness is None
    assert np.array_equal(flamingo.personal_best_position, flamingo.position)
    assert flamingo.personal_best_fitness == float("inf")
    
    # Verificar que la posición está en el rango [0, 1]
    assert np.all(flamingo.position >= 0) and np.all(flamingo.position <= 1)


def test_flamingo_fitness():
    """Test del cálculo de fitness del Flamingo."""
    problem = MockProblem(dimension=3)
    flamingo = FlamingoV2(problem)
    
    # Establecer una posición conocida
    flamingo.position = np.array([0.1, 0.2, 0.3])
    
    # Verificar cálculo de fitness (usar almost equal para floats)
    fitness = flamingo.fitness()
    assert np.isclose(fitness, 0.6)  # 0.1 + 0.2 + 0.3
    
    # Verificar que se actualizó el mejor fitness personal
    assert np.isclose(flamingo.personal_best_fitness, 0.6)
    assert np.array_equal(flamingo.personal_best_position, np.array([0.1, 0.2, 0.3]))
    
    # Verificar que el fitness se almacena en caché
    flamingo.position = np.array([0.4, 0.5, 0.6])  # Cambiar posición
    assert np.isclose(flamingo.fitness(), 0.6)  # Debería seguir siendo 0.6 porque está en caché
    
    # Invalidar fitness y recalcular
    flamingo._fitness = None
    assert np.isclose(flamingo.fitness(), 1.5)  # 0.4 + 0.5 + 0.6
    
    # Verificar que se actualizó el mejor fitness personal al ser peor
    assert np.isclose(flamingo.personal_best_fitness, 0.6)  # No debería cambiar
    assert np.array_equal(flamingo.personal_best_position, np.array([0.1, 0.2, 0.3]))


def test_flamingo_comparison():
    """Test de comparación entre Flamingos."""
    problem = MockProblem()
    
    flamingo1 = FlamingoV2(problem)
    flamingo1._fitness = 10
    
    flamingo2 = FlamingoV2(problem)
    flamingo2._fitness = 20
    
    # Verificar comparación
    assert flamingo1.is_better_than(flamingo2)
    assert not flamingo2.is_better_than(flamingo1)


def test_flamingo_is_feasible():
    """Test para verificar si la solución es factible."""
    problem = MockProblem()
    flamingo = FlamingoV2(problem)
    
    # En el contexto de VRP, todas las soluciones son factibles
    assert flamingo.is_feasible()


def test_flamingo_move_forage():
    """Test del movimiento de forrajeo del Flamingo."""
    np.random.seed(42)
    problem = MockProblem(dimension=3)
    
    flamingo = FlamingoV2(problem)
    flamingo.position = np.array([0.1, 0.2, 0.3])
    flamingo._fitness = 0.6
    
    best = Flamingo(problem)
    best.position = np.array([0.05, 0.15, 0.25])
    best._fitness = 0.45
    
    # Mock para el cálculo de fitness para que siempre devuelva un valor menor (mejora)
    problem.evaluate = MagicMock(return_value=0.4)
    
    # Patchar random.choice para tener valores predecibles
    with patch('random.choice', side_effect=lambda x: x[0]):
        # Test de movimiento de forrajeo
        flamingo.move(best, 0, 100, mode="forage")
    
    # Verificar que se actualizó el fitness
    assert flamingo._fitness == 0.4


def test_flamingo_move_migrate():
    """Test del movimiento de migración del Flamingo."""
    np.random.seed(42)
    problem = MockProblem(dimension=3)
    
    flamingo = FlamingoV2(problem)
    flamingo.position = np.array([0.1, 0.2, 0.3])
    flamingo._fitness = 0.6
    
    best = Flamingo(problem)
    best.position = np.array([0.05, 0.15, 0.25])
    best._fitness = 0.45
    
    # Mock para el cálculo de fitness para que siempre devuelva un valor menor (mejora)
    problem.evaluate = MagicMock(return_value=0.4)
    
    # Test de movimiento de migración
    flamingo.move(best, 0, 100, mode="migrate")
    
    # Verificar que se actualizó el fitness
    assert flamingo._fitness == 0.4


def test_flamingo_copy():
    """Test de la función de copia de Flamingo."""
    problem = MockProblem()
    
    flamingo1 = FlamingoV2(problem)
    flamingo1.position = np.array([0.1, 0.2, 0.3])
    flamingo1._fitness = 0.6
    flamingo1.personal_best_position = np.array([0.1, 0.2, 0.3])
    flamingo1.personal_best_fitness = 0.6
    
    flamingo2 = FlamingoV2(problem)
    flamingo2.copy(flamingo1)
    
    # Verificar que se han copiado los valores
    assert np.array_equal(flamingo2.position, flamingo1.position)
    assert flamingo2._fitness == flamingo1._fitness
    assert np.array_equal(flamingo2.personal_best_position, flamingo1.personal_best_position)
    assert flamingo2.personal_best_fitness == flamingo1.personal_best_fitness
    
    # Verificar que son objetos diferentes (deep copy)
    flamingo1.position[0] = 0.9
    assert flamingo2.position[0] == 0.1


def test_fgo_initialization():
    """Test de inicialización del algoritmo FGO."""
    np.random.seed(42)
    problem = MockProblem()
    
    # Inicialización del algoritmo
    fgo = FGO(problem, population_size=10, max_iterations=50, seed=42)
    
    # Verificar parámetros
    assert fgo.problem == problem
    assert fgo.population_size == 10
    assert fgo.max_iterations == 50
    
    # Inicializar la población
    fgo.initialize_population()
    
    # Verificar que la población se ha creado
    assert len(fgo.population) == 10
    assert all(isinstance(ind, Flamingo) for ind in fgo.population)
    
    # Verificar que se ha calculado el fitness de cada individuo
    assert all(ind._fitness is not None for ind in fgo.population)
    
    # Verificar que la población está ordenada por fitness
    fitnesses = [ind.fitness() for ind in fgo.population]
    assert fitnesses == sorted(fitnesses)
    
    # Verificar que se ha guardado la mejor solución
    assert isinstance(fgo.best_solution, Flamingo)
    assert fgo.best_solution._fitness == fgo.population[0]._fitness
    
    # Verificar la curva de convergencia
    assert len(fgo.convergence_curve) == 1
    assert fgo.convergence_curve[0] == fgo.best_solution.fitness()


def test_fgo_update_population():
    """Test de actualización de la población en FGO."""
    np.random.seed(42)
    problem = MockProblem()
    
    # Inicialización del algoritmo
    fgo = FGO(problem, population_size=10, max_iterations=50, seed=42)
    fgo.initialize_population()
    
    # Guardar fitness inicial
    initial_best_fitness = fgo.best_solution.fitness()
    
    # Actualizar la población
    fgo.update_population()
    
    # Verificar que se ha actualizado la curva de convergencia
    assert len(fgo.convergence_curve) == 2
    
    # Como estamos minimizando, el nuevo fitness debería ser menor o igual
    assert fgo.best_solution.fitness() <= initial_best_fitness


def test_fgo_full_execution():
    """Test de ejecución completa del algoritmo FGO."""
    np.random.seed(42)
    problem = MockProblem()

    # Inicialización del algoritmo
    fgo = FGO(problem, population_size=10, max_iterations=5, seed=42)

    # Ejecutar el algoritmo
    best_solution = fgo.execute()

    # Verificar que la ejecución completó las iteraciones
    assert len(fgo.convergence_curve) == 6  # Iteración inicial + 5 iteraciones

    # Verificar que la mejor solución es una instancia de Flamingo
    assert isinstance(best_solution, Flamingo)
