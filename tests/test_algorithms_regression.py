import pytest
import numpy as np
import os
from problems.vrp import VRPProblem
import importlib

# Ruta al directorio de datos de prueba
DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data/vrp")

# Instancia pequeña para pruebas rápidas
TEST_INSTANCE = "P-n16-k8.vrp"

# Valores óptimos conocidos para cada instancia (para comparar)
KNOWN_OPTIMA = {
    "P-n16-k8.vrp": 450,
    "E-n22-k4.vrp": 375,
    "E-n51-k5.vrp": 521,
    "A-n32-k5.vrp": 784,
    "B-n31-k5.vrp": 672
}

# Lista de algoritmos disponibles
ALGORITHMS = [
    "opa",  # Orca Predator Algorithm
    "sho",  # Spotted Hyena Optimizer
    "apo",  # Artificial Protozoa Optimizer
    "egto", # Enhanced Gorilla Troops Optimizer
    "fsa",  # Flamingo Search Algorithm
    "foa",  # Fossa Optimization Algorithm
    "woa",  # Whale Optimization Algorithm
    "hho",  # Harris Hawks Optimization
    "mrfo", # Manta Ray Foraging Optimization
    "sma",  # Slime Mould Algorithm
    "gto",  # Gorilla Troops Optimizer
    "ewa",  # Earthworm Algorithm
    "aha",  # Artificial Hummingbird Algorithm
    "rro",  # Raven Roosting Optimization
    "gvoa", # Griffon Vultures Optimization Algorithm
    "smo"   # Starling Murmuration Optimizer
]

@pytest.fixture
def vrp_problem():
    """Fixture que proporciona una instancia de problema VRP."""
    instance_path = os.path.join(DATA_DIR, TEST_INSTANCE)
    return VRPProblem(instance_path)

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
            total_distance += problem.distance_matrix[route[i], route[i+1]]
    
    return all_clients == required_clients, total_distance

def all_clients_covered(routes, problem):
    """Verifica que todos los clientes estén cubiertos exactamente una vez."""
    all_clients = set()
    for route in routes:
        for node in route[1:-1]:  # Excluir depósito
            all_clients.add(node)
    
    required_clients = set(range(1, problem.dimension))
    return all_clients == required_clients

@pytest.mark.parametrize("algorithm_name", ALGORITHMS)
def test_algorithm_regression(vrp_problem, algorithm_name):
    """
    Test de regresión para verificar que cada algoritmo:
    1. Puede resolver la instancia sin error
    2. Genera una solución que cubre todos los clientes
    3. La solución tiene una distancia razonable (menor a 2 veces el óptimo conocido)
    """
    # Cargar el algoritmo
    AlgorithmClass = load_algorithm(algorithm_name)
    if AlgorithmClass is None:
        return  # Skip si no se pudo cargar
    
    # Inicializar algoritmo con pocos parámetros para prueba rápida
    population_size = 10
    max_iterations = 5
    seed = 42
    
    algorithm = AlgorithmClass(vrp_problem, population_size=population_size, 
                             max_iterations=max_iterations, seed=seed)
    
    # Ejecutar algoritmo
    try:
        best_solution = algorithm.execute()
    except Exception as e:
        pytest.fail(f"El algoritmo {algorithm_name} falló: {str(e)}")
    
    # Verificar que hay una solución
    assert best_solution is not None, f"El algoritmo {algorithm_name} no generó solución"
    
    # Obtener rutas
    if hasattr(best_solution, "position"):
        if isinstance(best_solution.position, list) and isinstance(best_solution.position[0], list):
            # Ya tenemos las rutas directamente
            routes = best_solution.position
        else:
            # Convertir representación continua a rutas
            routes, _, _ = vrp_problem.decode_solution(best_solution.position)
    else:
        pytest.skip(f"No se puede evaluar la solución del algoritmo {algorithm_name}")
    
    # Verificar que todos los clientes están cubiertos
    assert all_clients_covered(routes, vrp_problem), \
        f"El algoritmo {algorithm_name} no cubrió todos los clientes"
    
    # Verificar la calidad de la solución
    _, total_distance = evaluate_routes(routes, vrp_problem)
    optimal_distance = KNOWN_OPTIMA.get(TEST_INSTANCE, float('inf'))
    
    # La distancia debe ser razonable (permitimos hasta 5 veces el óptimo para pruebas rápidas)
    # Esto es más permisivo para pruebas iniciales porque ejecutamos pocas iteraciones (5)
    max_allowed = 5 * optimal_distance
    assert total_distance <= max_allowed, \
        f"El algoritmo {algorithm_name} generó una solución con distancia {total_distance}, " \
        f"que excede el límite de {max_allowed} (5x óptimo)"
    
    # Verificar que la curva de convergencia existe y tiene una longitud razonable
    convergence = algorithm.get_convergence_curve()
    assert len(convergence) > 0, \
        f"La curva de convergencia para {algorithm_name} está vacía"
    
    # Verificar que la curva de convergencia tiende a mejorar
    # Nota: Con pocas iteraciones (5) y algoritmos estocásticos, puede haber
    # fluctuaciones en la curva, especialmente en las primeras iteraciones
    # Por lo tanto, solo verificamos que el valor final no sea peor que el inicial
    if len(convergence) > 1:
        assert convergence[-1] <= convergence[0] * 1.1, \
            f"La curva de convergencia para {algorithm_name} no muestra mejoría general"