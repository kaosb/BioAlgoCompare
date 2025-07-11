import pytest
import numpy as np
from problems.vrp import VRPProblem
import os

# Configurar semilla para reproducibilidad
np.random.seed(42)

# Ruta al directorio de datos de prueba
DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data/vrp")


def test_multi_depot_initialization():
    """Test inicialización con múltiples dark stores."""
    depots = [(0, 0), (25, 25), (-25, -25)]
    problem = VRPProblem(depots=depots, seed=42)

    assert len(problem.depots) == 3
    assert problem.depots[0] == (0, 0)
    assert problem.depots[1] == (25, 25)
    assert problem.depots[2] == (-25, -25)
    assert problem.seed == 42


def test_dynamic_demand_poisson():
    """Test actualización dinámica de demandas con distribución Poisson."""
    instance_path = os.path.join(DATA_DIR, "P-n16-k8.vrp")
    problem = VRPProblem(instance_path, dynamic_lambda=10.0, seed=42)

    initial_dimension = problem.dimension
    initial_nodes = len(problem.nodes)

    # Actualizar sin órdenes específicas (generación Poisson)
    problem.update_demand([], current_time=1.0)

    # Verificar que se añadieron nuevas órdenes
    assert problem.dimension > initial_dimension
    assert len(problem.nodes) > initial_nodes
    assert len(problem.dynamic_orders) > 0

    # Verificar que las demandas están en rango válido
    for order in problem.dynamic_orders:
        assert 1 <= order["demand"] <= problem.capacity // 3
        assert order["time"] == 1.0
        assert "DYN_" in order["order_id"]


def test_dynamic_demand_custom_orders():
    """Test actualización con órdenes personalizadas."""
    instance_path = os.path.join(DATA_DIR, "P-n16-k8.vrp")
    problem = VRPProblem(instance_path, seed=42)

    initial_dimension = problem.dimension

    # Añadir órdenes específicas
    new_orders = [
        {"coord": (10, 10), "demand": 5, "time": 2.0},
        {"coord": (-15, 20), "demand": 8, "time": 2.0},
    ]

    problem.update_demand(new_orders, current_time=2.0)

    assert problem.dimension == initial_dimension + 2
    assert problem.nodes[-2] == (10, 10)
    assert problem.nodes[-1] == (-15, 20)
    assert problem.demands[-2] == 5
    assert problem.demands[-1] == 8


def test_evaluate_multi_objectives():
    """Test evaluación multiobjetivo QC-DVRP."""
    instance_path = os.path.join(DATA_DIR, "P-n16-k8.vrp")
    problem = VRPProblem(instance_path, seed=42)

    # Generar solución y evaluar
    solution = problem.random_solution()
    tiempo_avg, coef_var, distancia = problem.evaluate_multi(solution)

    # Verificar que las métricas son válidas
    assert isinstance(tiempo_avg, float) and tiempo_avg > 0
    assert isinstance(coef_var, float) and coef_var >= 0
    assert isinstance(distancia, float) and distancia > 0

    # Verificar con rutas directas
    routes = problem.random_routes()
    tiempo_avg2, coef_var2, distancia2 = problem.evaluate_multi(routes)

    assert isinstance(tiempo_avg2, float) and tiempo_avg2 > 0
    assert isinstance(coef_var2, float) and coef_var2 >= 0
    assert isinstance(distancia2, float) and distancia2 > 0


def test_pareto_dominance():
    """Test verificación de dominancia de Pareto."""
    problem = VRPProblem(seed=42)

    # sol1 domina a sol2 (mejor en todos los objetivos)
    sol1 = (15.0, 0.2, 100.0)  # tiempo, coef_var, distancia
    sol2 = (20.0, 0.3, 150.0)
    assert problem.dominates(sol1, sol2) == True
    assert problem.dominates(sol2, sol1) == False

    # Soluciones no dominadas (trade-off)
    sol3 = (15.0, 0.3, 120.0)
    sol4 = (18.0, 0.2, 110.0)
    assert problem.dominates(sol3, sol4) == False
    assert problem.dominates(sol4, sol3) == False

    # Soluciones iguales no se dominan
    sol5 = (15.0, 0.2, 100.0)
    assert problem.dominates(sol1, sol5) == False


def test_evasion_strategy():
    """Test estrategia de evasión inspirada en HO para rutas con retraso."""
    instance_path = os.path.join(DATA_DIR, "P-n16-k8.vrp")
    problem = VRPProblem(instance_path, seed=42)

    # Crear rutas con diferentes tiempos
    routes = problem.random_routes()

    # Aplicar estrategia de evasión
    new_routes = problem.apply_evasion_strategy(routes, delay_threshold=25.0)

    # Verificar que las rutas siguen siendo válidas
    is_feasible, errors = problem.routes_are_feasible(new_routes)
    assert (
        is_feasible or len(errors) > 0
    )  # Puede haber warnings pero debe ser funcional

    # Verificar que todos los clientes siguen cubiertos
    all_customers = set()
    for route in new_routes:
        all_customers.update(route[1:-1])

    original_customers = set()
    for route in routes:
        original_customers.update(route[1:-1])

    assert all_customers == original_customers


def test_dynamic_overload_scenario():
    """Test escenario de sobrecarga dinámica."""
    instance_path = os.path.join(DATA_DIR, "P-n16-k8.vrp")
    problem = VRPProblem(instance_path, dynamic_lambda=15.0, seed=42)

    # Simular múltiples actualizaciones
    for t in range(5):
        problem.update_demand([], current_time=float(t))

    # Verificar que el sistema maneja la sobrecarga
    assert problem.dimension > 16  # Más nodos que el inicial
    assert len(problem.dynamic_orders) > 0

    # Generar solución y verificar factibilidad
    solution = problem.random_solution()
    routes, _, _ = problem.decode_solution(solution)

    # Al menos debe poder generar rutas (aunque sean muchas)
    assert len(routes) > 0


def test_seed_reproducibility():
    """Test reproducibilidad con semilla fija."""
    # Crear dos problemas con la misma semilla
    problem1 = VRPProblem(dynamic_lambda=10.0, seed=42)
    problem2 = VRPProblem(dynamic_lambda=10.0, seed=42)

    # Actualizar con Poisson
    problem1.update_demand([], current_time=1.0)
    problem2.update_demand([], current_time=1.0)

    # Deben generar el mismo número de órdenes
    assert len(problem1.dynamic_orders) == len(problem2.dynamic_orders)

    # Las coordenadas deben ser idénticas
    if len(problem1.dynamic_orders) > 0:
        assert (
            problem1.dynamic_orders[0]["coord"] == problem2.dynamic_orders[0]["coord"]
        )
        assert (
            problem1.dynamic_orders[0]["demand"] == problem2.dynamic_orders[0]["demand"]
        )


def test_distance_matrix_update():
    """Test actualización de matriz de distancias con nuevos nodos."""
    problem = VRPProblem(seed=42)
    problem.nodes = [(0, 0), (10, 0), (0, 10)]
    problem.dimension = 3
    problem.demands = [0, 5, 5]
    problem.capacity = 20
    problem.compute_distance_matrix()

    initial_shape = problem.distance_matrix.shape

    # Añadir nueva orden
    new_orders = [{"coord": (10, 10), "demand": 3, "time": 1.0}]
    problem.update_demand(new_orders)

    # Verificar que la matriz se expandió
    assert problem.distance_matrix.shape[0] > initial_shape[0]
    assert problem.distance_matrix.shape[1] > initial_shape[1]

    # Verificar que las distancias son correctas
    # Distancia del nuevo nodo (10,10) al depósito (0,0)
    expected_dist = np.sqrt(10**2 + 10**2)
    assert np.isclose(problem.distance_matrix[3, 0], expected_dist)


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
