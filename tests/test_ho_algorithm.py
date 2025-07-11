import pytest
import numpy as np
from algorithms.ho import HO, Hippopotamus, levy_flight
from problems.vrp import VRPProblem
import os
import math

# Configurar semilla para reproducibilidad
np.random.seed(42)


class CECTestFunction:
    """Funciones de prueba CEC para validación del algoritmo."""

    def __init__(self, function_type="sphere"):
        self.function_type = function_type
        self.dimension = 10

    def get_dimension(self):
        return self.dimension

    def evaluate(self, x):
        """Evalúa la función objetivo."""
        if self.function_type == "sphere":
            # Función Sphere: f(x) = sum(x_i^2)
            return np.sum(x**2)
        elif self.function_type == "rosenbrock":
            # Función Rosenbrock: f(x) = sum(100*(x_{i+1} - x_i^2)^2 + (1 - x_i)^2)
            result = 0
            for i in range(len(x) - 1):
                result += 100 * (x[i + 1] - x[i] ** 2) ** 2 + (1 - x[i]) ** 2
            return result
        else:
            return np.sum(x**2)

    def is_valid(self, x):
        """Verifica si la solución es válida."""
        return np.all(x >= -5) and np.all(x <= 5)


def test_levy_flight():
    """Test de la función de vuelo de Levy."""
    dim = 10
    levy_vector = levy_flight(dim)

    # Verificar dimensión
    assert len(levy_vector) == dim

    # Verificar que genera valores no cero
    assert not np.allclose(levy_vector, 0)

    # Verificar variabilidad
    assert np.std(levy_vector) > 0


def test_hippopotamus_initialization():
    """Test de inicialización de individuos Hippopotamus."""
    problem = CECTestFunction("sphere")
    hippo = Hippopotamus(problem)

    # Verificar atributos
    assert hasattr(hippo, "position")
    assert hasattr(hippo, "velocity")
    assert hasattr(hippo, "fitness_value")
    assert hasattr(hippo, "is_leader")
    assert hasattr(hippo, "group_id")

    # Verificar dimensión
    assert len(hippo.position) == problem.get_dimension()
    assert len(hippo.velocity) == problem.get_dimension()

    # Verificar límites [0, 1]
    assert np.all(hippo.position >= 0) and np.all(hippo.position <= 1)


def test_ho_initialization():
    """Test de inicialización del algoritmo HO."""
    problem = CECTestFunction("sphere")
    ho = HO(problem, population_size=20, max_iterations=50, seed=42)

    # Verificar parámetros
    assert ho.population_size == 20
    assert ho.max_iterations == 50
    assert ho.seed == 42

    # Verificar rangos de parámetros del algoritmo
    assert 0.1 <= ho.alpha_min <= ho.alpha_max <= 0.9
    assert 0.2 <= ho.beta_min <= ho.beta_max <= 0.8
    assert 0.3 <= ho.gamma_min <= ho.gamma_max <= 1.0
    assert 0.4 <= ho.theta <= 0.6


def test_ho_convergence_sphere():
    """Test de convergencia en función Sphere."""
    problem = CECTestFunction("sphere")
    ho = HO(problem, population_size=30, max_iterations=100, seed=42)

    # Ejecutar algoritmo
    best_solution = ho.execute()

    # Verificar convergencia
    assert best_solution.fitness() < 0.1  # Debería converger cerca de 0

    # Verificar curva de convergencia
    curve = ho.get_convergence_curve()
    assert len(curve) == ho.max_iterations + 1
    assert curve[-1] <= curve[0]  # Mejora monótona

    # Verificar mejora significativa
    improvement = (curve[0] - curve[-1]) / curve[0]
    assert improvement > 0.9  # Al menos 90% de mejora


def test_ho_convergence_rosenbrock():
    """Test de convergencia en función Rosenbrock."""
    problem = CECTestFunction("rosenbrock")
    ho = HO(problem, population_size=50, max_iterations=200, seed=42)

    # Ejecutar algoritmo
    best_solution = ho.execute()

    # La función Rosenbrock es más difícil, esperamos convergencia razonable
    assert best_solution.fitness() < 100  # Valor razonable para Rosenbrock

    # Verificar mejora
    curve = ho.get_convergence_curve()
    assert curve[-1] < curve[0]


def test_ho_reproducibility():
    """Test de reproducibilidad con semilla fija."""
    problem = CECTestFunction("sphere")

    # Ejecutar dos veces con la misma semilla
    ho1 = HO(problem, population_size=20, max_iterations=50, seed=42)
    best1 = ho1.execute()
    curve1 = ho1.get_convergence_curve()

    ho2 = HO(problem, population_size=20, max_iterations=50, seed=42)
    best2 = ho2.execute()
    curve2 = ho2.get_convergence_curve()

    # Verificar que los resultados son idénticos
    assert best1.fitness() == best2.fitness()
    assert np.allclose(curve1, curve2)
    assert np.allclose(best1.position, best2.position)


def test_ho_phases():
    """Test de las tres fases del algoritmo."""
    problem = CECTestFunction("sphere")
    ho = HO(problem, population_size=30, max_iterations=30, seed=42)

    # Inicializar población
    ho.initialize_population()
    initial_fitness = [h.fitness() for h in ho.population]

    # Test fase de posición
    ho._position_phase(alpha=0.5, beta=0.5)
    position_fitness = [h.fitness() for h in ho.population]

    # Test fase de defensa
    ho._defense_phase()
    defense_fitness = [h.fitness() for h in ho.population]

    # Test fase de evasión
    ho._evasion_phase(gamma=0.5)
    evasion_fitness = [h.fitness() for h in ho.population]

    # Verificar que las fases no empeoran drásticamente
    assert np.mean(position_fitness) <= np.mean(initial_fitness) * 1.1
    assert np.mean(defense_fitness) <= np.mean(position_fitness) * 1.1
    assert np.mean(evasion_fitness) <= np.mean(defense_fitness) * 1.1


def test_ho_with_vrp():
    """Test de HO con problema VRP real."""
    # Cargar instancia VRP
    data_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data/vrp")
    instance_path = os.path.join(data_dir, "P-n16-k8.vrp")

    if os.path.exists(instance_path):
        problem = VRPProblem(instance_path, seed=42)
        ho = HO(problem, population_size=20, max_iterations=50, seed=42)

        # Ejecutar algoritmo
        best_solution = ho.execute()

        # Verificar solución válida
        assert best_solution.fitness() > 0
        assert best_solution.is_feasible()

        # Verificar mejora
        curve = ho.get_convergence_curve()
        assert curve[-1] <= curve[0]


def test_ho_multiobjective_vrp():
    """Test de HO con VRP multiobjetivo."""
    # Crear problema VRP dinámico
    problem = VRPProblem(seed=42)
    problem.nodes = [(0, 0), (10, 0), (0, 10), (10, 10), (5, 5)]
    problem.demands = [0, 5, 5, 5, 5]
    problem.capacity = 15
    problem.dimension = 5
    problem.compute_distance_matrix()

    ho = HO(problem, population_size=20, max_iterations=30, seed=42)

    # Verificar que detecta capacidad multiobjetivo
    assert ho.use_multiobjective == True

    # Ejecutar algoritmo
    best_solution = ho.execute()

    # Verificar evaluación multiobjetivo
    if hasattr(problem, "evaluate_multi"):
        tiempo, coef_var, distancia = problem.evaluate_multi(best_solution.position)
        assert tiempo > 0
        assert coef_var >= 0
        assert distancia > 0


def test_ho_parameter_adaptation():
    """Test de adaptación de parámetros durante la ejecución."""
    problem = CECTestFunction("sphere")
    ho = HO(problem, population_size=10, max_iterations=100, seed=42)

    # Simular diferentes etapas del algoritmo
    # Inicio (progress = 0)
    progress = 0
    alpha_start = ho.alpha_max - (ho.alpha_max - ho.alpha_min) * progress
    beta_start = ho.beta_max - (ho.beta_max - ho.beta_min) * progress
    gamma_start = ho.gamma_min + (ho.gamma_max - ho.gamma_min) * progress

    assert alpha_start == ho.alpha_max
    assert beta_start == ho.beta_max
    assert gamma_start == ho.gamma_min

    # Mitad (progress = 0.5)
    progress = 0.5
    alpha_mid = ho.alpha_max - (ho.alpha_max - ho.alpha_min) * progress
    beta_mid = ho.beta_max - (ho.beta_max - ho.beta_min) * progress
    gamma_mid = ho.gamma_min + (ho.gamma_max - ho.gamma_min) * progress

    assert ho.alpha_min < alpha_mid < ho.alpha_max
    assert ho.beta_min < beta_mid < ho.beta_max
    assert ho.gamma_min < gamma_mid < ho.gamma_max

    # Final (progress = 1)
    progress = 1
    alpha_end = ho.alpha_max - (ho.alpha_max - ho.alpha_min) * progress
    beta_end = ho.beta_max - (ho.beta_max - ho.beta_min) * progress
    gamma_end = ho.gamma_min + (ho.gamma_max - ho.gamma_min) * progress

    assert np.isclose(alpha_end, ho.alpha_min)
    assert np.isclose(beta_end, ho.beta_min)
    assert np.isclose(gamma_end, ho.gamma_max)


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
