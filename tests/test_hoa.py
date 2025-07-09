#!/usr/bin/env python3
"""
Test del algoritmo HOA (Hyena Optimization Algorithm).
"""

import numpy as np
import pytest
from unittest.mock import MagicMock, patch
from algorithms.hoa import Hyena, HOA
from algorithms.base import MetaheuristicAlgorithm


class MockProblem:
    """Problema mock para pruebas."""

    def __init__(self, dimension=5):
        self.dimension = dimension
        self.eval_count = 0

    def get_dimension(self):
        return self.dimension

    def evaluate(self, solution):
        """Función de evaluación simple para test."""
        self.eval_count += 1
        # Función simple: suma de los elementos
        return np.sum(solution)


def test_hyena_initialization():
    """Test de inicialización del individuo Hyena."""
    np.random.seed(42)  # Para reproducibilidad

    problem = MockProblem(dimension=5)
    hyena = Hyena(problem)

    # Verificar inicialización
    assert hyena.problem == problem
    assert hyena.dimension == 5
    assert hyena.position.shape == (5,)
    assert hyena._fitness is None

    # Verificar que la posición está en el rango [0, 1]
    assert np.all(hyena.position >= 0) and np.all(hyena.position <= 1)


def test_hyena_fitness():
    """Test del cálculo de fitness del Hyena."""
    problem = MockProblem(dimension=3)
    hyena = Hyena(problem)

    # Establecer una posición conocida
    hyena.position = np.array([0.1, 0.2, 0.3])

    # Verificar cálculo de fitness
    fitness = hyena.fitness()
    assert np.isclose(fitness, 0.6)  # 0.1 + 0.2 + 0.3

    # Verificar que el fitness se almacena en caché
    hyena.position = np.array([0.4, 0.5, 0.6])  # Cambiar posición
    assert np.isclose(
        hyena.fitness(), 0.6
    )  # Debería seguir siendo 0.6 porque está en caché

    # Invalidar fitness y recalcular
    hyena._fitness = None
    assert np.isclose(hyena.fitness(), 1.5)  # 0.4 + 0.5 + 0.6


def test_hyena_comparison():
    """Test de comparación entre Hyenas."""
    problem = MockProblem()

    hyena1 = Hyena(problem)
    hyena1._fitness = 10

    hyena2 = Hyena(problem)
    hyena2._fitness = 20

    # Verificar comparación
    assert hyena1.is_better_than(hyena2)
    assert not hyena2.is_better_than(hyena1)


def test_hyena_is_feasible():
    """Test para verificar si la solución es factible."""
    problem = MockProblem()
    hyena = Hyena(problem)

    # En el contexto de VRP, todas las soluciones son factibles
    assert hyena.is_feasible()


def test_hyena_move_basic():
    """Test básico de movimiento de la Hyena."""
    problem = MockProblem(dimension=3)

    hyena = Hyena(problem)
    hyena.position = np.array([0.5, 0.5, 0.5])
    hyena._fitness = 1.5

    alpha = Hyena(problem)
    alpha.position = np.array([0.1, 0.2, 0.3])

    beta = Hyena(problem)
    beta.position = np.array([0.2, 0.3, 0.4])

    delta = Hyena(problem)
    delta.position = np.array([0.3, 0.4, 0.5])

    # Llamar al método move para verificar que no lanza excepciones
    hyena.move(alpha, beta, delta, 0, 100)

    # Verificar que el fitness fue invalidado
    assert hyena._fitness is None

    # Verificar que la posición sigue en el rango [0, 1]
    assert np.all(hyena.position >= 0) and np.all(hyena.position <= 1)


def test_hyena_copy():
    """Test de la función de copia de Hyena."""
    problem = MockProblem()

    hyena1 = Hyena(problem)
    hyena1.position = np.array([0.1, 0.2, 0.3])
    hyena1._fitness = 0.6

    hyena2 = Hyena(problem)
    hyena2.copy(hyena1)

    # Verificar que se han copiado los valores
    assert np.array_equal(hyena2.position, hyena1.position)
    assert hyena2._fitness == hyena1._fitness

    # Verificar que son objetos diferentes (deep copy)
    hyena1.position[0] = 0.9
    assert hyena2.position[0] == 0.1


def test_hoa_initialization():
    """Test de inicialización del algoritmo HOA."""
    np.random.seed(42)
    problem = MockProblem()

    # Inicialización del algoritmo
    hoa = HOA(problem, population_size=10, max_iterations=50, seed=42)

    # Verificar parámetros
    assert hoa.problem == problem
    assert hoa.population_size == 10
    assert hoa.max_iterations == 50
    assert hoa.alpha is None
    assert hoa.beta is None
    assert hoa.delta is None

    # Inicializar la población
    hoa.initialize_population()

    # Verificar que la población se ha creado
    assert len(hoa.population) == 10
    assert all(isinstance(ind, Hyena) for ind in hoa.population)

    # Verificar que se ha calculado el fitness de cada individuo
    assert all(ind._fitness is not None for ind in hoa.population)

    # Verificar que la población está ordenada por fitness
    fitnesses = [ind.fitness() for ind in hoa.population]
    assert fitnesses == sorted(fitnesses)

    # Verificar que se han asignado los líderes
    assert hoa.alpha == hoa.population[0]
    assert hoa.beta == hoa.population[1]
    assert hoa.delta == hoa.population[2]

    # Verificar que se ha guardado la mejor solución
    assert isinstance(hoa.best_solution, Hyena)
    assert hoa.best_solution._fitness == hoa.alpha._fitness

    # Verificar la curva de convergencia
    assert len(hoa.convergence_curve) == 1
    assert hoa.convergence_curve[0] == hoa.best_solution.fitness()


def test_hoa_update_population():
    """Test de actualización de la población en HOA."""
    np.random.seed(42)
    problem = MockProblem()

    # Inicialización del algoritmo
    hoa = HOA(problem, population_size=10, max_iterations=50, seed=42)
    hoa.initialize_population()

    # Guardar fitness inicial
    initial_best_fitness = hoa.best_solution.fitness()

    # Actualizar la población
    hoa.update_population()

    # Verificar que se ha actualizado la curva de convergencia
    assert len(hoa.convergence_curve) == 2

    # Verificar que se han actualizado los líderes
    assert hoa.alpha == hoa.population[0]
    assert hoa.beta == hoa.population[1]
    assert hoa.delta == hoa.population[2]

    # Como estamos minimizando, el nuevo fitness debería ser menor o igual
    assert hoa.best_solution.fitness() <= initial_best_fitness


def test_hoa_full_execution():
    """Test de ejecución completa del algoritmo HOA."""
    np.random.seed(42)
    problem = MockProblem()

    # Inicialización del algoritmo
    hoa = HOA(problem, population_size=10, max_iterations=5, seed=42)

    # Ejecutar el algoritmo
    best_solution = hoa.execute()

    # Verificar que la ejecución completó las iteraciones
    assert len(hoa.convergence_curve) == 6  # Iteración inicial + 5 iteraciones

    # Verificar que la mejor solución es una instancia de Hyena
    assert isinstance(best_solution, Hyena)
