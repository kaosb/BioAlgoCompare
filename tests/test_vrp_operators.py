import pytest
import numpy as np
from utils.vrp_operators import VRPOperators, calculate_route_distance, check_route_capacity, split_vrp
from problems.vrp import VRPProblem
import os

# Ruta al directorio de datos de prueba
DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data/vrp")


@pytest.fixture
def vrp_problem():
    """Fixture que proporciona una instancia de problema VRP."""
    instance_path = os.path.join(DATA_DIR, "P-n16-k8.vrp")
    return VRPProblem(instance_path)


@pytest.fixture
def sample_route():
    """Fixture que proporciona una ruta de ejemplo."""
    # Ruta de ejemplo: depósito (0) -> nodos 1, 2, 3 -> depósito (0)
    return [0, 1, 2, 3, 0]


@pytest.fixture
def sample_routes(vrp_problem):
    """Fixture que proporciona un conjunto de rutas de ejemplo."""
    # Generar rutas aleatorias pero factibles para el problema
    return vrp_problem.random_routes()


def test_calculate_route_distance(vrp_problem, sample_route):
    """Test que la distancia de ruta se calcula correctamente."""
    distance = VRPOperators.calculate_route_distance(
        sample_route, vrp_problem.distance_matrix
    )

    # La distancia debe ser un valor positivo
    assert distance > 0

    # Calcular manualmente la distancia
    manual_distance = 0
    for i in range(len(sample_route) - 1):
        manual_distance += vrp_problem.distance_matrix[
            sample_route[i], sample_route[i + 1]
        ]

    # Verificar que los cálculos coinciden
    assert np.isclose(distance, manual_distance)


def test_calculate_route_load(vrp_problem, sample_route):
    """Test que la carga de ruta se calcula correctamente."""
    load = VRPOperators.calculate_route_load(sample_route, vrp_problem.demands)

    # Calcular manualmente la carga (excluyendo depósito)
    manual_load = sum(vrp_problem.demands[node] for node in sample_route[1:-1])

    # Verificar que los cálculos coinciden
    assert load == manual_load


def test_check_route_capacity(vrp_problem, sample_route):
    """Test que la verificación de factibilidad funciona correctamente."""
    # La ruta de ejemplo debería ser factible
    is_feasible = VRPOperators.check_route_capacity(
        sample_route, vrp_problem.demands, vrp_problem.capacity
    )

    # Verificar si la ruta es factible según la capacidad
    route_load = sum(vrp_problem.demands[node] for node in sample_route[1:-1])
    expected_feasibility = route_load <= vrp_problem.capacity

    assert is_feasible == expected_feasibility
    
    # Probar la función global también
    global_feasible = check_route_capacity(sample_route, vrp_problem.demands, vrp_problem.capacity)
    assert global_feasible == expected_feasibility


@pytest.mark.skip(reason="Función no implementada en esta versión")
def test_evaluate_solution(vrp_problem, sample_routes):
    """Test que la evaluación de la solución funciona correctamente."""
    pass


@pytest.mark.skip(reason="Función no implementada en esta versión")
def test_swap_nodes(vrp_problem, sample_route):
    """Test que el operador de intercambio de nodos funciona correctamente."""
    pass


@pytest.mark.skip(reason="Función no implementada en esta versión")
def test_two_opt_move(vrp_problem):
    """Test que el operador 2-opt funciona correctamente."""
    pass


@pytest.mark.skip(reason="Función no implementada en esta versión")
def test_relocate_node(vrp_problem):
    """Test que el operador de reubicación de nodos funciona correctamente."""
    pass


@pytest.mark.skip(reason="Función no implementada en esta versión")
def test_optimize_all_routes(vrp_problem, sample_routes):
    """Test que la optimización de todas las rutas funciona correctamente."""
    pass


@pytest.mark.skip(reason="Función no implementada en esta versión")
def test_repair_mechanism(vrp_problem):
    """Test que el mecanismo de optimización entre rutas funciona."""
    pass


def test_split_vrp(vrp_problem):
    """Test que el algoritmo Split para VRP funciona correctamente."""
    # Crear una permutación simple de clientes
    permutation = [1, 2, 3, 4, 5]
    
    # Ejecutar Split
    routes, total_cost = split_vrp(permutation, vrp_problem)
    
    # Verificar que se devuelven rutas
    assert isinstance(routes, list)
    assert len(routes) > 0
    
    # Verificar que cada ruta comienza y termina en el depósito
    for route in routes:
        assert route[0] == vrp_problem.depot_index
        assert route[-1] == vrp_problem.depot_index
        
    # Verificar que todos los clientes están incluidos en las rutas
    clients_in_routes = []
    for route in routes:
        clients_in_routes.extend(route[1:-1])  # Excluir depósito al inicio y fin
    
    clients_in_routes.sort()
    assert clients_in_routes == permutation
    
    # Verificar que el costo total es un valor positivo
    assert total_cost > 0
    
    # Verificar que todas las rutas respetan la capacidad
    for route in routes:
        load = sum(vrp_problem.demands[node] for node in route[1:-1])
        assert load <= vrp_problem.capacity