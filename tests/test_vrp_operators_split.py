"""
Tests para operadores de VRP específicos para la función Split.
"""
import pytest
import numpy as np
import sys
import os

# Agregar el directorio raíz al path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

# ruff: noqa: E402
from utils import vrp_operators
from problems.vrp_v2 import VRPProblemV2


def test_vrp_split_method():
    """Test básico del método Split para VRP."""
    # Crear datos de prueba básicos
    # Simulamos una instancia VRP muy pequeña
    class MockVRPProblem:
        def __init__(self):
            self.depot_index = 0
            self.dimension = 5  # Depósito + 4 clientes
            self.capacity = 10
            self.demands = [0, 2, 3, 4, 1]  # Demanda de cada nodo, depósito = 0
            self.distance_matrix = np.array([
                [0, 1, 2, 3, 4],  # Distancias desde depósito
                [1, 0, 1, 2, 3],  # Distancias desde cliente 1
                [2, 1, 0, 1, 2],  # Distancias desde cliente 2
                [3, 2, 1, 0, 1],  # Distancias desde cliente 3
                [4, 3, 2, 1, 0],  # Distancias desde cliente 4
            ])
    
    # Crear problema mock
    problem = MockVRPProblem()
    
    # Crear una permutación de clientes (excluyendo depósito)
    permutation = [1, 2, 3, 4]  # Clientes en orden 1, 2, 3, 4
    
    # Aplicar algoritmo Split
    routes, total_cost = vrp_operators.split_vrp(permutation, problem)
    
    # Verificar que el resultado contiene rutas
    assert isinstance(routes, list)
    assert len(routes) > 0
    
    # Verificar que cada ruta comienza y termina en el depósito
    for route in routes:
        assert route[0] == problem.depot_index
        assert route[-1] == problem.depot_index
        
    # Verificar que todos los clientes están asignados a alguna ruta
    assigned_customers = []
    for route in routes:
        assigned_customers.extend(route[1:-1])  # Excluir depósito al inicio y fin
    
    assigned_customers.sort()
    assert assigned_customers == permutation


def test_vrp_route_distance():
    """Test del cálculo de distancia de ruta para VRP."""
    # Crear datos de prueba
    distance_matrix = np.array([
        [0, 1, 2, 3],
        [1, 0, 4, 5],
        [2, 4, 0, 6],
        [3, 5, 6, 0]
    ])
    
    # Ruta: Depósito (0) -> Cliente 1 -> Cliente 2 -> Depósito (0)
    route = [0, 1, 2, 0]
    
    # Calcular distancia de la ruta
    distance = vrp_operators.calculate_route_distance(route, distance_matrix)
    
    # Verificar resultado
    expected_distance = 1 + 4 + 2  # 0->1 + 1->2 + 2->0
    assert distance == expected_distance


def test_vrp_route_feasibility():
    """Test de factibilidad de ruta para VRP."""
    # Crear datos de prueba
    demands = [0, 2, 3, 4]  # Demanda de cada nodo, depósito = 0
    capacity = 10
    
    # Ruta 1: Depósito (0) -> Cliente 1 -> Cliente 2 -> Depósito (0) = Demanda total 5
    route1 = [0, 1, 2, 0]
    
    # Ruta 2: Depósito (0) -> Cliente 1 -> Cliente 2 -> Cliente 3 -> Depósito (0) = Demanda total 9
    route2 = [0, 1, 2, 3, 0]
    
    # Ruta 3: Depósito (0) -> Cliente 1 -> Cliente 2 -> Cliente 3 -> Cliente 1 -> Depósito (0) = Demanda total 11
    route3 = [0, 1, 2, 3, 1, 0]
    
    # Verificar factibilidad
    assert vrp_operators.check_route_capacity(route1, demands, capacity) is True
    assert vrp_operators.check_route_capacity(route2, demands, capacity) is True
    assert vrp_operators.check_route_capacity(route3, demands, capacity) is False
