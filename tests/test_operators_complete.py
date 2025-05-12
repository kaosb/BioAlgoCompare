"""
Tests para asegurar cobertura completa de operadores.py
"""
import pytest
import numpy as np
from unittest.mock import patch
from utils import operators

def test_sbx_crossover_complete_coverage():
    """Test completo para SBX crossover."""
    # Caso en que y1 > y2 y luego forzar rand > 1.0/alpha para línea 40
    solution1 = np.array([0.9])
    solution2 = np.array([0.1])

    # Necesitamos muchos valores para cubrir todas las llamadas a random
    # en sbx_crossover debido a los bucles for y condicionales anidados
    mock_values = [0.1]  # Primero para probability check (< 0.9, entra al bucle)
    mock_values += [0.2]  # Para la condición if np.random.random() <= 0.5

    # Para el valor del beta_q - asegurarnos que cubre ambas ramas
    # Usar un valor grande que asegure que rand > 1.0/alpha
    mock_values += [0.99]

    with patch('numpy.random.random', side_effect=mock_values):
        result = operators.sbx_crossover(solution1, solution2, probability=0.9)

    # Verificaciones básicas
    assert isinstance(result, np.ndarray)
    assert result.shape == solution1.shape
    assert np.all(result >= 0) and np.all(result <= 1)

def test_sbx_crossover_different_scenarios():
    """Test para diferentes escenarios en SBX crossover."""
    # Caso donde la probabilidad no se cumple
    with patch('numpy.random.random') as mock_random:
        mock_random.return_value = 0.95  # > 0.9 (default probability)
        solution1 = np.array([0.1, 0.2, 0.3])
        solution2 = np.array([0.7, 0.8, 0.9])
        result = operators.sbx_crossover(solution1, solution2)
        # Debería ser una copia de solution1
        np.testing.assert_array_equal(result, solution1)
    
    # Caso donde abs(y1 - y2) <= 1e-10 (son casi iguales)
    with patch('numpy.random.random') as mock_random:
        mock_random.return_value = 0.1  # < 0.5 para entrar en el if interno
        solution1 = np.array([0.1, 0.2, 0.3])
        solution2 = np.array([0.1, 0.2 + 1e-11, 0.3])
        result = operators.sbx_crossover(solution1, solution2, probability=1.0)
        # Debería ser igual a solution1 para ese índice
        assert result[1] == solution1[1]

def test_mutation_different_scenarios():
    """Test para diferentes escenarios en polynomial_mutation."""
    # Caso donde la probabilidad no se cumple para ningún gen
    with patch('numpy.random.random') as mock_random:
        mock_random.return_value = 0.95  # > 0.1 (default probability)
        solution = np.array([0.1, 0.2, 0.3])
        result = operators.polynomial_mutation(solution)
        # Debería ser una copia exacta de solution
        np.testing.assert_array_equal(result, solution)
    
    # Casos para cubrir ambas ramas del if en la mutación
    # Caso rand < 0.5
    with patch('numpy.random.random') as mock_random:
        # Primero True para entrar en la mutación, luego 0.3 para rand < 0.5
        mock_random.side_effect = [0.05, 0.3]
        solution = np.array([0.5])
        result = operators.polynomial_mutation(solution, probability=1.0)
        # Solo verificamos que esté en rango
        assert 0 <= result[0] <= 1
    
    # Caso rand >= 0.5
    with patch('numpy.random.random') as mock_random:
        # Primero True para entrar en la mutación, luego 0.7 para rand >= 0.5
        mock_random.side_effect = [0.05, 0.7]
        solution = np.array([0.5])
        result = operators.polynomial_mutation(solution, probability=1.0)
        # Solo verificamos que esté en rango
        assert 0 <= result[0] <= 1