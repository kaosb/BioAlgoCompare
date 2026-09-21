"""
Tests para operadores de soluciones VRP.
"""
import pytest
import numpy as np
import sys
import os

# Agregar el directorio raíz al path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

# ruff: noqa: E402
from utils import operators


def test_crossover_operations():
    """Test de operaciones básicas de cruce."""
    # Crear soluciones de prueba
    solution1 = np.array([0.1, 0.2, 0.3, 0.4, 0.5])
    solution2 = np.array([0.9, 0.8, 0.7, 0.6, 0.5])

    # Test de cruce binario simulado (SBX)
    result = operators.sbx_crossover(
        solution1, solution2, probability=1.0, distribution_index=20
    )

    # Verificar que el resultado es del tipo y forma esperados
    assert isinstance(result, np.ndarray)
    assert result.shape == solution1.shape

    # Verificar que el resultado está en el rango [0, 1]
    assert np.all(result >= 0) and np.all(result <= 1)

    # Test para cubrir el caso en que y1 > y2 (línea 30)
    solution3 = np.array([0.9, 0.8, 0.7, 0.6, 0.5])
    solution4 = np.array([0.1, 0.2, 0.3, 0.4, 0.5])

    # Forzamos np.random.random() a devolver 0.5 para entrar en la condición
    np.random.seed(42)
    result2 = operators.sbx_crossover(
        solution3, solution4, probability=1.0, distribution_index=20
    )

    # Verificar que el resultado está en el rango [0, 1]
    assert np.all(result2 >= 0) and np.all(result2 <= 1)


def test_mutation_operations():
    """Test de operaciones básicas de mutación."""
    # Crear soluciones de prueba
    solution = np.array([0.1, 0.2, 0.3, 0.4, 0.5])

    # Test de mutación polinomial
    result = operators.polynomial_mutation(
        solution, probability=1.0, distribution_index=20
    )

    # Verificar que el resultado es del tipo y forma esperados
    assert isinstance(result, np.ndarray)
    assert result.shape == solution.shape

    # Verificar que el resultado está en el rango [0, 1]
    assert np.all(result >= 0) and np.all(result <= 1)


def test_repair_operations():
    """Test de operaciones básicas de reparación."""
    # Crear soluciones de prueba fuera de rango
    solution = np.array([-0.1, 1.2, 0.3, 1.5, -0.5])

    # Test de reparación de límites
    result = operators.repair_bounds(solution, 0.0, 1.0)

    # Verificar que el resultado es del tipo y forma esperados
    assert isinstance(result, np.ndarray)
    assert result.shape == solution.shape

    # Verificar que el resultado está en el rango [0, 1]
    assert np.all(result >= 0) and np.all(result <= 1)

    # Verificar que los valores se repararon correctamente
    assert result[0] == 0.0  # -0.1 -> 0.0
    assert result[1] == 1.0  # 1.2 -> 1.0
    assert result[3] == 1.0  # 1.5 -> 1.0
    assert result[4] == 0.0  # -0.5 -> 0.0
