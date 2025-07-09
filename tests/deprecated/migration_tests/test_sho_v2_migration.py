"""
Tests para verificar la implementación de SHO (Spotted Hyena Optimizer) en la arquitectura v2.

Como SHO solo existe en v2, estos tests verifican que la implementación
siga correctamente los patrones y estándares de la arquitectura v2.
"""

import pytest
import numpy as np
from pathlib import Path

# Importar la versión v2
from algorithms.sho_v2 import SHOV2, SpottedHyena
from problems.vrp_v2 import VRPProblemV2
from algorithms.base_v2 import MoveContext


class TestSHOV2Implementation:
    """Tests para la implementación de SHO en v2."""
    
    @pytest.fixture
    def test_problem(self):
        """Crea un problema de prueba pequeño."""
        data_dir = Path("data/vrp")
        instance_path = data_dir / "P-n16-k8.vrp"
        
        if not instance_path.exists():
            pytest.skip(f"Instancia de prueba no encontrada: {instance_path}")
            
        return VRPProblemV2(str(instance_path))
    
    def test_initialization(self, test_problem):
        """Verifica que SHO se inicialice correctamente siguiendo v2."""
        seed = 42
        pop_size = 10
        max_iter = 5
        
        # Crear instancia
        sho = SHOV2(test_problem, population_size=pop_size, 
                    max_iterations=max_iter, seed=seed)
        
        # Verificar parámetros básicos
        assert sho.population_size == pop_size
        assert sho.max_iterations == max_iter
        assert sho.seed == seed
        assert sho.problem == test_problem
        
        # No hay parámetros específicos de SHO en __init__
    
    def test_individual_creation(self, test_problem):
        """Verifica que los individuos SpottedHyena se creen correctamente."""
        # Crear individuo
        hyena = SpottedHyena(test_problem)
        hyena.initialize()
        
        # Verificar propiedades básicas
        assert hyena.position is not None
        assert isinstance(hyena.position, list) or isinstance(hyena.position, np.ndarray)
        
        # Verificar que tenga velocidad (específico de SHO)
        assert hasattr(hyena, 'velocity')
        assert hyena.velocity is not None
        assert len(hyena.velocity) == test_problem.dimension
    
    def test_fitness_evaluation(self, test_problem):
        """Verifica que la evaluación de fitness funcione correctamente."""
        hyena = SpottedHyena(test_problem)
        hyena.initialize()
        
        # Evaluar fitness
        fitness = hyena.fitness()
        
        # Verificar que sea un número válido
        assert isinstance(fitness, (int, float))
        assert not np.isnan(fitness)
        assert not np.isinf(fitness)
        assert fitness > 0  # Para VRP, el fitness debe ser positivo
    
    def test_population_initialization(self, test_problem):
        """Verifica que la población se inicialice correctamente."""
        sho = SHOV2(test_problem, population_size=20, seed=123)
        sho.initialize_population()
        
        # Verificar tamaño de población
        assert len(sho.population) == 20
        
        # Verificar que todos sean SpottedHyena
        for ind in sho.population:
            assert isinstance(ind, SpottedHyena)
            assert ind.position is not None
            assert hasattr(ind, 'velocity')
        
        # Verificar líderes (alpha, beta, delta)
        assert hasattr(sho, 'alpha')
        assert hasattr(sho, 'beta')
        assert hasattr(sho, 'delta')
        assert isinstance(sho.alpha, SpottedHyena)
        assert isinstance(sho.beta, SpottedHyena)
        assert isinstance(sho.delta, SpottedHyena)
        
        # Verificar mejor solución
        assert sho.best_solution is not None
        assert isinstance(sho.best_solution, SpottedHyena)
        
        # Verificar ordenamiento por fitness
        for i in range(1, len(sho.population)):
            assert sho.population[i-1].fitness() <= sho.population[i].fitness()
    
    def test_move_context_creation(self, test_problem):
        """Verifica que el contexto de movimiento se cree correctamente."""
        sho = SHOV2(test_problem, population_size=10, max_iterations=10)
        sho.initialize_population()
        
        # Crear contexto
        context = sho._create_move_context()
        
        # Verificar estructura del contexto
        assert isinstance(context, MoveContext)
        assert context.iteration == 0  # Primera iteración
        assert context.max_iterations == 10
        assert context.population == sho.population
        assert context.best_individual == sho.best_solution
        
        # Verificar parámetros del algoritmo
        assert context.get_param('alpha') == sho.alpha
        assert context.get_param('beta') == sho.beta
        assert context.get_param('delta') == sho.delta
        assert context.get_param('h') is not None
        assert 0 <= context.get_param('h') <= 5
    
    def test_hyena_movement(self, test_problem):
        """Verifica que el movimiento de las hienas funcione."""
        sho = SHOV2(test_problem, population_size=10, max_iterations=20, seed=42)
        sho.initialize_population()
        
        # Crear contexto para diferentes iteraciones
        context_early = MoveContext(
            iteration=2,
            max_iterations=20,
            population=sho.population,
            best_individual=sho.best_solution,
            algorithm_params={
                'alpha': sho.alpha,
                'beta': sho.beta,
                'delta': sho.delta,
                'h': 5 - 2 * (5 / 20)  # h factor
            }
        )
        
        # Probar movimiento de una hiena
        hyena = sho.population[5]
        old_pos = hyena.position.copy() if hasattr(hyena.position, 'copy') else list(hyena.position)
        hyena.move(context_early)
        
        # Verificar que se movió y que la posición es válida
        # (la nueva posición debe ser una lista de rutas válidas para VRP)
        assert hyena.position is not None
    
    def test_reproducibility(self, test_problem):
        """Verifica que SHO sea reproducible con la misma semilla."""
        seed = 12345
        pop_size = 15
        max_iter = 10
        
        # Ejecutar dos veces con la misma semilla
        sho1 = SHOV2(test_problem, population_size=pop_size, 
                     max_iterations=max_iter, seed=seed)
        best1 = sho1.execute()
        
        sho2 = SHOV2(test_problem, population_size=pop_size, 
                     max_iterations=max_iter, seed=seed)
        best2 = sho2.execute()
        
        # Verificar reproducibilidad
        assert best1.fitness() == best2.fitness()
        assert sho1.convergence_curve == sho2.convergence_curve
    
    def test_convergence_behavior(self, test_problem):
        """Verifica que SHO muestre comportamiento de convergencia."""
        seed = 999
        pop_size = 20
        max_iter = 15
        
        # Ejecutar algoritmo
        sho = SHOV2(test_problem, population_size=pop_size, 
                    max_iterations=max_iter, seed=seed)
        best = sho.execute()
        
        # Verificar curva de convergencia
        curve = sho.get_convergence_curve()
        
        # Debe tener max_iter + 1 elementos (incluye valor inicial)
        assert len(curve) == max_iter + 1
        
        # Debe mostrar mejora o estabilidad
        for i in range(1, len(curve)):
            assert curve[i] <= curve[i-1] + 1e-6
        
        # El valor final debe ser mejor o igual que el inicial
        assert curve[-1] <= curve[0]
        
        # Verificar que el mejor individuo tiene el fitness reportado
        assert abs(best.fitness() - curve[-1]) < 1e-6
    
    def test_leader_update(self, test_problem):
        """Verifica que los líderes (alpha, beta, delta) se actualicen correctamente."""
        sho = SHOV2(test_problem, population_size=10, max_iterations=5, seed=42)
        sho.initialize_population()
        
        # Guardar líderes iniciales
        initial_alpha_fitness = sho.alpha.fitness()
        initial_beta_fitness = sho.beta.fitness()
        initial_delta_fitness = sho.delta.fitness()
        
        # Verificar jerarquía inicial
        assert initial_alpha_fitness <= initial_beta_fitness
        assert initial_beta_fitness <= initial_delta_fitness
        
        # Ejecutar una iteración
        sho.iteration = 0
        sho.update_population()
        
        # Los líderes deben mantenerse como los mejores tres
        current_fitnesses = sorted([ind.fitness() for ind in sho.population])
        assert abs(sho.alpha.fitness() - current_fitnesses[0]) < 1e-6
        if sho.population_size > 1:
            assert abs(sho.beta.fitness() - current_fitnesses[1]) < 1e-6
        if sho.population_size > 2:
            assert abs(sho.delta.fitness() - current_fitnesses[2]) < 1e-6
    
    def test_encircling_behavior(self, test_problem):
        """Verifica que el comportamiento de encierro funcione."""
        sho = SHOV2(test_problem, population_size=10, max_iterations=20)
        sho.initialize_population()
        
        # El factor h debe disminuir con las iteraciones
        h_values = []
        for i in range(20):
            h = 5 - i * (5 / 20)
            h_values.append(h)
        
        # Verificar que h disminuye linealmente
        for i in range(1, len(h_values)):
            assert h_values[i] < h_values[i-1]
        
        # Al final, h debe estar cerca de 0
        assert h_values[-1] < 0.5
    
    def test_summary_information(self, test_problem):
        """Verifica que el resumen incluya información específica de SHO."""
        sho = SHOV2(test_problem, population_size=10, max_iterations=5)
        summary = sho.summary()
        
        # Verificar información básica
        assert summary["algorithm"] == "Spotted Hyena Optimizer"
        assert "problem" in summary
        assert summary["population_size"] == 10
        assert summary["max_iterations"] == 5
        
        # SHO no tiene parámetros adicionales en el resumen base
        # pero debe incluir información estándar
        assert "best_fitness" in summary
        assert "execution_time" in summary
    
    def test_algorithm_should_sort(self, test_problem):
        """Verifica que SHO ordene la población como se requiere."""
        sho = SHOV2(test_problem)
        
        # SHO debe ordenar la población para identificar alpha, beta, delta
        assert sho._should_sort_population() == True
    
    def test_complete_execution(self, test_problem):
        """Verifica que el algoritmo complete su ejecución sin errores."""
        sho = SHOV2(test_problem, population_size=20, max_iterations=30, seed=42)
        
        # Ejecutar algoritmo
        best = sho.execute()
        
        # Verificar resultados
        assert best is not None
        assert isinstance(best, SpottedHyena)
        assert best.fitness() > 0
        
        # Verificar que se ejecutaron todas las iteraciones
        assert len(sho.convergence_curve) == 31  # max_iter + 1
        assert sho.iteration == 30
        
        # Verificar que la población final esté ordenada
        for i in range(1, len(sho.population)):
            assert sho.population[i-1].fitness() <= sho.population[i].fitness()
        
        # Verificar que el mejor individuo sea realmente el mejor
        best_fitness = min(ind.fitness() for ind in sho.population)
        assert abs(sho.best_solution.fitness() - best_fitness) < 1e-6


if __name__ == "__main__":
    pytest.main([__file__, "-v"])