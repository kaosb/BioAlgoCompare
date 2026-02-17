import pytest
import numpy as np
from problems.vrp import VRPProblem
import os

# Ruta al directorio de datos de prueba
DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data/vrp")


def test_vrp_problem_load():
    """Test que el parser carga correctamente una instancia VRP."""
    # Cargar una instancia conocida
    instance_path = os.path.join(DATA_DIR, "P-n16-k8.vrp")
    problem = VRPProblem(instance_path)

    # Verificar propiedades básicas
    assert problem.name == "P-n16-k8"
    assert problem.dimension == 16
    assert problem.capacity == 35
    assert problem.depot_index == 0  # El depósito debe ser el nodo 0

    # Verificar que se cargaron todos los nodos
    assert len(problem.nodes) == 16
    assert len(problem.demands) == 16

    # Verificar que el depósito tiene demanda 0
    assert problem.demands[problem.depot_index] == 0


def test_vrp_distance_matrix():
    """Test que la matriz de distancias se calcula correctamente."""
    instance_path = os.path.join(DATA_DIR, "P-n16-k8.vrp")
    problem = VRPProblem(instance_path)

    # Verificar forma de la matriz
    assert problem.distance_matrix.shape == (16, 16)

    # Verificar algunas propiedades básicas de la matriz de distancias
    # La distancia desde un nodo a sí mismo debe ser 0
    for i in range(problem.dimension):
        assert problem.distance_matrix[i, i] == 0

    # Las distancias deben ser simétricas: d(i,j) = d(j,i)
    for i in range(problem.dimension):
        for j in range(i + 1, problem.dimension):
            assert np.isclose(
                problem.distance_matrix[i, j], problem.distance_matrix[j, i]
            )

    # Verificar que no hay distancias negativas
    assert np.all(problem.distance_matrix >= 0)


def test_decode_solution():
    """Test que la decodificación de una solución funciona correctamente."""
    instance_path = os.path.join(DATA_DIR, "P-n16-k8.vrp")
    problem = VRPProblem(instance_path)

    # Crear una solución simple para probar
    solution = np.linspace(0, 1, problem.get_dimension())

    # Decodificar la solución
    routes, total_distance, is_feasible = problem.decode_solution(solution)

    # Verificaciones básicas
    assert isinstance(routes, list)
    assert isinstance(total_distance, float) or isinstance(total_distance, np.float64)
    assert isinstance(is_feasible, bool)

    # Todas las rutas deben comenzar y terminar en el depósito
    for route in routes:
        assert route[0] == problem.depot_index
        assert route[-1] == problem.depot_index

    # Todos los clientes deben estar cubiertos exactamente una vez
    covered_nodes = set()
    for route in routes:
        for node in route[1:-1]:  # Excluir depósito al inicio y fin
            covered_nodes.add(node)

    required_nodes = set(range(1, problem.dimension))
    assert (
        covered_nodes == required_nodes
    ), f"Missing nodes: {required_nodes - covered_nodes}"


def test_evaluate_solution():
    """Test que la evaluación de una solución funciona correctamente."""
    instance_path = os.path.join(DATA_DIR, "P-n16-k8.vrp")
    problem = VRPProblem(instance_path)

    # Evaluar una solución aleatoria
    solution = problem.random_solution()
    fitness = problem.evaluate(solution)

    # El fitness debe ser un número positivo
    assert isinstance(fitness, float) or isinstance(fitness, np.float64)
    assert fitness > 0

    # Evaluar rutas directamente
    routes = problem.random_routes()
    fitness_routes = problem.evaluate_routes(routes)

    assert isinstance(fitness_routes, float) or isinstance(fitness_routes, np.float64)
    assert fitness_routes > 0


def test_feasibility_check():
    """Test que la verificación de factibilidad funciona correctamente."""
    instance_path = os.path.join(DATA_DIR, "P-n16-k8.vrp")
    problem = VRPProblem(instance_path)

    # Generar rutas factibles
    routes = problem.random_routes()

    # Verificar que las rutas generadas son factibles
    is_feasible, errors = problem.routes_are_feasible(routes)
    assert is_feasible
    assert len(errors) == 0

    # Crear una ruta infactible (excede capacidad)
    infeasible_route = [
        [problem.depot_index]
        + list(range(1, problem.dimension))
        + [problem.depot_index]
    ]
    is_feasible, errors = problem.routes_are_feasible(infeasible_route)
    assert not is_feasible
    assert any("excede capacidad" in msg for msg in errors)

    # Crear una ruta con cliente faltante
    missing_client_routes = [
        [problem.depot_index, 1, problem.depot_index],
        [problem.depot_index, 3, 4, 5, problem.depot_index],
    ]
    is_feasible, errors = problem.routes_are_feasible(missing_client_routes)
    assert not is_feasible
    assert any("Nodos faltantes" in msg for msg in errors)


def test_repair_mechanism():
    """Test que el mecanismo de reparación funciona correctamente."""
    instance_path = os.path.join(DATA_DIR, "P-n16-k8.vrp")
    problem = VRPProblem(instance_path)

    # Crear rutas infactibles (clientes duplicados, faltantes)
    infeasible_routes = [
        [0, 1, 2, 0],
        [0, 2, 3, 0],  # Cliente 2 duplicado
        [0, 4, 5, 0],  # Faltan clientes 6-15
    ]

    # Reparar las rutas
    repaired_routes = problem.repair_routes(infeasible_routes)

    # Verificar que las rutas reparadas son factibles
    is_feasible, errors = problem.routes_are_feasible(repaired_routes)
    assert is_feasible
    assert len(errors) == 0


def test_different_instances():
    """Test que el parser funciona con diferentes instancias."""
    # Probar con varias instancias si están disponibles
    instances = ["P-n16-k8.vrp", "E-n22-k4.vrp", "E-n51-k5.vrp"]

    for instance_name in instances:
        instance_path = os.path.join(DATA_DIR, instance_name)
        if os.path.exists(instance_path):
            problem = VRPProblem(instance_path)

            # Verificar propiedades básicas
            assert problem.name == instance_name.split(".")[0]
            assert problem.dimension > 0
            assert problem.capacity > 0
            assert len(problem.nodes) == problem.dimension
            assert len(problem.demands) == problem.dimension
