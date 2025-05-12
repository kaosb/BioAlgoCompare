#!/usr/bin/env python3
"""
Test de funciones de visualización.
"""

import numpy as np
import pytest
import matplotlib.pyplot as plt
from unittest.mock import patch, MagicMock
from utils.visualization import plot_vrp_solution, plot_convergence, compare_algorithms


class MockVRPProblem:
    """Mock de un problema VRP para pruebas."""
    
    def __init__(self):
        self.nodes = [(0, 0), (1, 1), (2, 2), (3, 3), (4, 4)]
        self.depot_index = 0


@pytest.fixture
def close_all_plots():
    """Fixture para cerrar todas las figuras después de cada test."""
    yield
    plt.close('all')


def test_plot_vrp_solution(close_all_plots):
    """Test de la función plot_vrp_solution."""
    # Crear un problema mock
    problem = MockVRPProblem()
    
    # Definir rutas para la solución
    routes = [[0, 1, 2, 0], [0, 3, 4, 0]]
    
    # Verificar que la función devuelve un objeto plt
    plt_obj = plot_vrp_solution(problem, routes)
    assert plt_obj is plt
    
    # Verificar que se ha creado una figura
    assert plt.gcf() is not None
    
    # Verificar que el título se establece correctamente cuando no se proporciona uno
    assert plt.gca().get_title() == "VRP Solution - 2 routes"
    
    # Verificar con título personalizado
    plt.close()
    plt_obj = plot_vrp_solution(problem, routes, title="Test Solution")
    assert plt.gca().get_title() == "Test Solution"


def test_plot_convergence(close_all_plots):
    """Test de la función plot_convergence."""
    # Crear una curva de convergencia de prueba
    convergence_curve = [100, 90, 80, 75, 70]
    
    # Verificar que la función devuelve un objeto plt
    plt_obj = plot_convergence(convergence_curve)
    assert plt_obj is plt
    
    # Verificar que se ha creado una figura
    assert plt.gcf() is not None
    
    # Verificar que el título se establece correctamente cuando no se proporciona uno
    assert plt.gca().get_title() == "Convergence Curve"
    
    # Verificar con título personalizado
    plt.close()
    plt_obj = plot_convergence(convergence_curve, title="Test Convergence")
    assert plt.gca().get_title() == "Test Convergence"
    
    # Verificar las etiquetas de los ejes
    assert plt.gca().get_xlabel() == "Iteration"
    assert plt.gca().get_ylabel() == "Fitness (Distance)"


def test_compare_algorithms(close_all_plots):
    """Test de la función compare_algorithms."""
    # Crear diccionario de resultados de prueba
    results_dict = {
        "Algorithm 1": [100, 90, 80, 75, 70],
        "Algorithm 2": [95, 85, 75, 70, 65]
    }
    
    # Verificar que la función devuelve un objeto plt
    plt_obj = compare_algorithms(results_dict)
    assert plt_obj is plt
    
    # Verificar que se ha creado una figura
    assert plt.gcf() is not None
    
    # Verificar que el título se establece correctamente cuando no se proporciona uno
    assert plt.gca().get_title() == "Algorithm Comparison"
    
    # Verificar con título personalizado
    plt.close()
    plt_obj = compare_algorithms(results_dict, title="Test Comparison")
    assert plt.gca().get_title() == "Test Comparison"
    
    # Verificar las etiquetas de los ejes
    assert plt.gca().get_xlabel() == "Iteration"
    assert plt.gca().get_ylabel() == "Fitness (Distance)"
    
    # Verificar que la leyenda contiene los nombres de los algoritmos
    legend_texts = [text.get_text() for text in plt.gca().get_legend().get_texts()]
    assert set(legend_texts) == set(results_dict.keys())