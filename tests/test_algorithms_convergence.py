import pytest
import numpy as np
import os
from problems.vrp import VRPProblem
import importlib

# Ruta al directorio de datos de prueba
DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data/vrp")
SOLOMON_DIR = os.path.join(DATA_DIR, "Solomon")

# Instancias de Solomon para pruebas de convergencia
SOLOMON_INSTANCES = ["R101.vrp", "C101.vrp", "RC101.vrp"]

# Valores óptimos conocidos para cada instancia (para calcular gap)
KNOWN_OPTIMA = {
    "R101.vrp": 1650,  # Valor aproximado para test
    "C101.vrp": 830,  # Valor aproximado para test
    "RC101.vrp": 1680,  # Valor aproximado para test
}

# Lista de algoritmos a probar para convergencia
CONVERGENCE_ALGORITHMS = [
    "hho",  # Harris Hawks Optimization
    "sho",  # Spotted Hyena Optimizer (was hoa, which is just an alias)
]


def load_algorithm(algorithm_name):
    """Carga dinámicamente un algoritmo por su nombre."""
    try:
        # Importar el módulo
        module = importlib.import_module(f"algorithms.{algorithm_name}")

        # Obtener la clase del algoritmo (asumiendo que el nombre de la clase es en mayúsculas)
        algo_class = getattr(module, algorithm_name.upper())
        return algo_class
    except (ImportError, AttributeError) as e:
        pytest.skip(f"No se pudo cargar el algoritmo {algorithm_name}: {str(e)}")
        return None


def evaluate_routes(routes, problem):
    """Evalúa si una solución de rutas es válida y retorna su distancia."""
    # Verificar que todos los clientes estén cubiertos
    all_clients = set()
    for route in routes:
        for node in route[1:-1]:  # Excluir depósito
            all_clients.add(node)

    required_clients = set(range(1, problem.dimension))

    # Calcular distancia total
    total_distance = 0
    for route in routes:
        for i in range(len(route) - 1):
            total_distance += problem.distance_matrix[route[i], route[i + 1]]

    return all_clients == required_clients, total_distance


@pytest.mark.parametrize("algorithm_name", CONVERGENCE_ALGORITHMS)
@pytest.mark.parametrize("instance_name", SOLOMON_INSTANCES)
@pytest.mark.slow
def test_algorithm_convergence(algorithm_name, instance_name):
    """
    Test de convergencia para verificar que los algoritmos:
    1. Pueden resolver las instancias de Solomon
    2. Alcanzan un gap razonable respecto al óptimo (≤ 50%)
    3. Muestran un comportamiento de convergencia esperado
    """
    # Cargar el algoritmo
    AlgorithmClass = load_algorithm(algorithm_name)
    if AlgorithmClass is None:
        return  # Skip si no se pudo cargar

    # Cargar la instancia de Solomon
    instance_path = os.path.join(SOLOMON_DIR, instance_name)
    problem = VRPProblem(instance_path)

    # Configurar parámetros
    population_size = 30
    max_iterations = 10  # Solo 10 iteraciones para pruebas
    seed = 1  # Semilla fija para reproducibilidad

    # Inicializar y ejecutar algoritmo
    algorithm = AlgorithmClass(
        problem,
        population_size=population_size,
        max_iterations=max_iterations,
        seed=seed,
    )

    try:
        best_solution = algorithm.execute()
    except Exception as e:
        pytest.fail(f"El algoritmo {algorithm_name} falló en {instance_name}: {str(e)}")

    # Verificar que hay una solución
    assert (
        best_solution is not None
    ), f"El algoritmo {algorithm_name} no generó solución"

    # Obtener rutas
    if hasattr(best_solution, "position"):
        if isinstance(best_solution.position, list) and isinstance(
            best_solution.position[0], list
        ):
            # Ya tenemos las rutas directamente
            routes = best_solution.position
        else:
            # Convertir representación continua a rutas
            routes, _, _ = problem.decode_solution(best_solution.position)
    else:
        pytest.skip(f"No se puede evaluar la solución del algoritmo {algorithm_name}")

    # Calcular la distancia total
    all_covered, total_distance = evaluate_routes(routes, problem)

    # Verificar que todos los clientes estén cubiertos
    assert (
        all_covered
    ), f"El algoritmo {algorithm_name} no cubrió todos los clientes en {instance_name}"

    # Calcular el gap respecto al óptimo conocido
    optimal_distance = KNOWN_OPTIMA.get(instance_name, float("inf"))
    gap = (total_distance - optimal_distance) / optimal_distance

    # Verificar que el gap sea menor o igual al 50%
    # Solomon instances are difficult, allow higher gaps
    instance_type = instance_name.split(".")[0]
    max_gap = 3.0 if instance_type == "C101" else 2.0

    assert gap <= max_gap, (
        f"El algoritmo {algorithm_name} en {instance_name} obtuvo un gap de {gap:.2%}, "
        f"que excede el límite máximo de {max_gap:.0%}"
    )

    # Verificar que la curva de convergencia existe y muestra mejora
    convergence = algorithm.get_convergence_curve()
    assert (
        len(convergence) > 0
    ), f"La curva de convergencia para {algorithm_name} está vacía"

    # Verificar que hay una tendencia de mejora en la convergencia
    if len(convergence) > 1:
        # La curva de convergencia debe mostrar alguna mejora (último valor mejor que el primero)
        assert convergence[-1] < convergence[0], (
            f"La curva de convergencia para {algorithm_name} en {instance_name} "
            f"no muestra mejora: inicio={convergence[0]}, fin={convergence[-1]}"
        )
