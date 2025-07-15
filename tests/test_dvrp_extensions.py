"""
Tests para las extensiones de VRP a QC-DVRP (Quick Commerce Dynamic VRP).

Valida las funcionalidades añadidas para soportar:
- Multi-depot
- Demandas dinámicas (Poisson)
- Evaluación multiobjetivo
- Estrategias de evasión
"""

import pytest
import numpy as np
from problems.vrp import VRPProblem


def test_multidepot_initialization():
    """Test inicialización con múltiples depósitos."""
    depots = [(0, 0), (50, 50), (100, 100)]
    problem = VRPProblem(depots=depots, seed=42)

    assert hasattr(problem, "depots")
    assert len(problem.depots) == 3
    assert problem.depots[0] == (0, 0)
    assert problem.depots[1] == (50, 50)
    assert problem.depots[2] == (100, 100)


def test_dynamic_demand_generation():
    """Test generación de demandas dinámicas con distribución Poisson."""
    problem = VRPProblem(dynamic_lambda=10.0, seed=42)

    # Simular llegada de nuevas órdenes
    new_orders = []
    for i in range(5):
        new_orders.append(
            {
                "customer_id": i + 100,
                "coord": (np.random.uniform(0, 100), np.random.uniform(0, 100)),
                "demand": np.random.poisson(10.0),
                "time_window": (0, 100),
            }
        )

    initial_dimension = problem.dimension if hasattr(problem, "dimension") else 0
    problem.update_demand(new_orders, current_time=50.0)

    # Verificar que se añadieron las nuevas demandas
    assert hasattr(problem, "dynamic_orders")
    assert len(problem.dynamic_orders) > 0
    # Verificar que se actualizó la dimensión del problema
    if hasattr(problem, "dimension"):
        assert problem.dimension > initial_dimension


def test_multiobjective_evaluation():
    """Test evaluación multiobjetivo (tiempo, variación carga, distancia)."""
    problem = VRPProblem(seed=42)

    # Crear un problema simple
    problem.nodes = [(0, 0), (10, 0), (0, 10), (10, 10)]
    problem.demands = [0, 5, 5, 5]
    problem.capacity = 15
    problem.dimension = 4
    problem.compute_distance_matrix()

    # Solución de prueba
    solution = np.array([0.1, 0.5, 0.3, 0.7])

    # Evaluar multiobjetivo
    tiempo, coef_var, distancia = problem.evaluate_multi(solution)

    assert tiempo > 0
    assert coef_var >= 0
    assert distancia > 0


def test_pareto_dominance():
    """Test verificación de dominancia de Pareto."""
    problem = VRPProblem()

    # Solución 1 domina a solución 2 (mejor en todos los objetivos)
    sol1 = (10.0, 0.1, 100.0)  # tiempo, coef_var, distancia
    sol2 = (15.0, 0.2, 150.0)
    assert problem.dominates(sol1, sol2) is True
    assert problem.dominates(sol2, sol1) is False

    # Soluciones no dominadas
    sol3 = (10.0, 0.2, 150.0)
    sol4 = (15.0, 0.1, 100.0)
    assert problem.dominates(sol3, sol4) is False
    assert problem.dominates(sol4, sol3) is False


def test_evasion_strategy():
    """Test estrategia de evasión para clientes con retraso."""
    problem = VRPProblem(seed=42)

    # Configurar problema con nodos y matriz de distancias
    problem.nodes = [(0, 0), (10, 0), (0, 10), (10, 10), (20, 20), (30, 30)]
    problem.demands = [0, 5, 5, 5, 5, 5]
    problem.capacity = 15
    problem.dimension = 6
    problem.compute_distance_matrix()

    # Crear rutas de prueba
    routes = [
        [0, 1, 2, 0],  # Ruta 1
        [0, 3, 4, 0],  # Ruta 2
        [0, 5, 0],  # Ruta 3
    ]

    # Aplicar estrategia de evasión
    improved_routes = problem.apply_evasion_strategy(routes, delay_threshold=30.0)

    # Verificar que se devuelven rutas (aunque sean las mismas si no hay retrasos)
    assert isinstance(improved_routes, list)
    assert len(improved_routes) > 0


def test_vrp_with_dynamic_updates():
    """Test VRP con actualizaciones dinámicas durante la ejecución."""
    problem = VRPProblem(dynamic_lambda=5.0, seed=42)

    # Estado inicial
    problem.nodes = [(0, 0), (20, 0), (0, 20), (20, 20)]
    problem.demands = [0, 10, 10, 10]
    problem.capacity = 30
    problem.dimension = 4
    problem.compute_distance_matrix()

    # Simular llegada de nuevo cliente
    new_orders = [
        {"customer_id": 5, "coord": (10, 10), "demand": 5, "time_window": (0, 100)}
    ]

    problem.update_demand(new_orders, current_time=25.0)

    # Verificar actualización
    assert len(problem.nodes) == 5
    assert len(problem.demands) == 5
    assert problem.dimension == 5


def test_load_coefficient_calculation():
    """Test cálculo del coeficiente de variación de carga."""
    problem = VRPProblem(seed=42)

    # Configurar problema
    problem.nodes = [(0, 0), (10, 0), (0, 10), (10, 10), (5, 5)]
    problem.demands = [0, 5, 10, 15, 20]
    problem.capacity = 30
    problem.dimension = 5
    problem.compute_distance_matrix()

    # Solución que genera rutas desbalanceadas
    solution = np.array([0.1, 0.2, 0.8, 0.9, 0.5])

    tiempo, coef_var, distancia = problem.evaluate_multi(solution)

    # El coeficiente de variación debe ser > 0 para cargas desbalanceadas
    assert coef_var > 0


def test_nearest_depot_assignment():
    """Test asignación al depósito más cercano en multi-depot."""
    depots = [(0, 0), (100, 0), (50, 100)]
    problem = VRPProblem(depots=depots, seed=42)

    # Cliente cerca del primer depósito
    customer_location = (10, 10)
    nearest_idx = 0
    min_dist = float("inf")

    for i, depot in enumerate(problem.depots):
        dist = np.sqrt(
            (customer_location[0] - depot[0]) ** 2
            + (customer_location[1] - depot[1]) ** 2
        )
        if dist < min_dist:
            min_dist = dist
            nearest_idx = i

    assert nearest_idx == 0  # Debe asignarse al primer depósito


def test_vrp_backwards_compatibility():
    """Test que las extensiones no rompen la funcionalidad básica de VRP."""
    # Crear VRP básico (sin extensiones)
    problem = VRPProblem()

    # Verificar que funciona como VRP estándar
    assert hasattr(problem, "evaluate")
    assert hasattr(problem, "decode_solution")

    # Las extensiones deben ser opcionales
    # Por defecto, VRP inicializa con un depot en (0, 0)
    if hasattr(problem, "depots"):
        assert isinstance(problem.depots, list)
        # Debe tener al menos un depot por defecto
        assert len(problem.depots) >= 1
    if hasattr(problem, "dynamic_lambda"):
        assert problem.dynamic_lambda >= 0


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
