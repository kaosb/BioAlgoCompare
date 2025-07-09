"""
Tests para verificar la migración de HOA a la nueva arquitectura v2.
"""

import pytest
import numpy as np
from pathlib import Path

# Importar ambas versiones
from algorithms.hoa_v2 import HOAV2
from algorithms.hoa_v2 import HOAV2, HyenaV2
from problems.vrp_v2 import VRPProblemV2


class TestHOAV2Migration:
    """Tests para la migración de HOA a v2."""
    
    @pytest.fixture
    def test_problem(self):
        """Crea un problema de prueba pequeño."""
        # Usar una instancia pequeña para pruebas rápidas
        data_dir = Path("data/vrp")
        instance_path = data_dir / "P-n16-k8.vrp"
        
        if not instance_path.exists():
            pytest.skip(f"Instancia de prueba no encontrada: {instance_path}")
            
        return VRPProblem(str(instance_path))
    
    def test_initialization_compatibility(self, test_problem):
        """Verifica que ambas versiones se inicialicen de forma similar."""
        seed = 42
        pop_size = 10
        max_iter = 5
        
        # Crear instancias de ambas versiones
        hoa_v1 = HOA(test_problem, population_size=pop_size, 
                     max_iterations=max_iter, seed=seed)
        hoa_v2 = HOAV2(test_problem, population_size=pop_size, 
                       max_iterations=max_iter, seed=seed)
        
        # Verificar parámetros básicos
        assert hoa_v1.population_size == hoa_v2.population_size
        assert hoa_v1.max_iterations == hoa_v2.max_iterations
        # v2 almacena seed, v1 no
        assert hoa_v2.seed == seed
    
    def test_individual_creation(self, test_problem):
        """Verifica que los individuos se creen correctamente."""
        # Crear individuos de ambas versiones
        hyena_v1 = Hyena(test_problem)
        hyena_v2 = HyenaV2(test_problem)
        
        # Inicializar la posición de hyena_v2 (v1 lo hace automáticamente)
        hyena_v2.initialize()
        
        # Verificar propiedades básicas
        assert hyena_v1.dimension == hyena_v2.dimension
        assert len(hyena_v1.position) == len(hyena_v2.position)
        assert hyena_v1.position.shape == hyena_v2.position.shape
        
        # Verificar que las posiciones estén en [0,1]
        assert np.all(hyena_v1.position >= 0) and np.all(hyena_v1.position <= 1)
        assert np.all(hyena_v2.position >= 0) and np.all(hyena_v2.position <= 1)
    
    def test_fitness_evaluation(self, test_problem):
        """Verifica que la evaluación de fitness sea consistente."""
        # Crear individuos con la misma posición
        position = np.random.uniform(0, 1, test_problem.get_dimension())
        
        hyena_v1 = Hyena(test_problem)
        hyena_v1.position = position.copy()
        
        hyena_v2 = HyenaV2(test_problem)
        hyena_v2.initialize()  # Primero inicializar
        hyena_v2.position = position.copy()  # Luego establecer la misma posición
        hyena_v2.invalidate_fitness()  # Invalidar para recalcular
        
        # Evaluar fitness
        fitness_v1 = hyena_v1.fitness()
        fitness_v2 = hyena_v2.fitness()
        
        # Deben ser iguales
        assert fitness_v1 == fitness_v2
    
    def test_reproducibility(self, test_problem):
        """Verifica que ambas versiones sean reproducibles con la misma semilla."""
        seed = 12345
        pop_size = 20
        max_iter = 10
        
        # Ejecutar v2 dos veces
        hoa_v2 = HOAV2(test_problem, population_size=pop_size, 
                       max_iterations=max_iter, seed=seed)
        best_v2_run1 = hoa_v2.execute()
        
        hoa_v2_again = HOAV2(test_problem, population_size=pop_size, 
                             max_iterations=max_iter, seed=seed)
        best_v2_run2 = hoa_v2_again.execute()
        
        # Verificar reproducibilidad
        assert best_v2_run1.fitness() == best_v2_run2.fitness()
        assert hoa_v2.convergence_curve == hoa_v2_again.convergence_curve
    
    def test_convergence_behavior(self, test_problem):
        """Verifica que la versión v2 muestre comportamiento de convergencia."""
        seed = 999
        pop_size = 15
        max_iter = 20
        
        # Ejecutar v2
        hoa_v2 = HOAV2(test_problem, population_size=pop_size, 
                       max_iterations=max_iter, seed=seed)
        best_v2 = hoa_v2.execute()
        
        # Verificar convergencia
        curve_v2 = hoa_v2.get_convergence_curve()
        
        # v2 tiene al menos 1 valor (puede tener hasta max_iter + 1)
        assert len(curve_v2) >= 1
        assert len(curve_v2) <= max_iter + 1
        
        # Debe mostrar mejora (o al menos no empeorar)
        for i in range(1, len(curve_v2)):
            assert curve_v2[i] <= curve_v2[i-1] + 1e-6  # Permitir pequeño error numérico
        
        # El valor final debe ser mejor que el inicial
        assert curve_v2[-1] <= curve_v2[0]
    
    def test_leaders_initialization(self, test_problem):
        """Verifica que los líderes se inicialicen correctamente."""
        hoa_v2 = HOAV2(test_problem, population_size=30, max_iterations=10, seed=42)
        hoa_v2.initialize_population()
        
        # Verificar que los líderes estén asignados
        assert hoa_v2.alpha is not None
        assert hoa_v2.beta is not None
        assert hoa_v2.delta is not None
        
        # Verificar que los líderes estén ordenados por fitness
        assert hoa_v2.alpha.fitness() <= hoa_v2.beta.fitness()
        assert hoa_v2.beta.fitness() <= hoa_v2.delta.fitness()
    
    def test_move_context_usage(self, test_problem):
        """Verifica que la nueva versión use correctamente MoveContext."""
        from algorithms.base_v2 import MoveContext
        
        # Crear población pequeña
        hoa_v2 = HOAV2(test_problem, population_size=5, max_iterations=3, seed=42)
        hoa_v2.initialize_population()
        
        # Crear contexto de prueba con líderes
        context = MoveContext(
            iteration=1,
            max_iterations=3,
            population=hoa_v2.population,
            best_individual=hoa_v2.best_solution,
            algorithm_params={
                'alpha': hoa_v2.alpha,
                'beta': hoa_v2.beta,
                'delta': hoa_v2.delta
            }
        )
        
        # Verificar que move funcione con context
        hyena = hoa_v2.population[3]  # No es un líder
        old_position = hyena.position.copy()
        
        hyena.move(context)
        
        # La posición debe haber cambiado
        assert not np.array_equal(old_position, hyena.position)
        
        # La posición debe estar en límites válidos
        assert np.all(hyena.position >= 0) and np.all(hyena.position <= 1)
    
    def test_summary_information(self, test_problem):
        """Verifica que el resumen incluya información específica de HOA."""
        hoa_v2 = HOAV2(test_problem, population_size=10, max_iterations=5)
        summary = hoa_v2.summary()
        
        # Verificar información básica
        assert summary["algorithm"] == "HOA v2"
        assert "problem" in summary
        assert summary["population_size"] == 10
        
        # Verificar información específica de HOA
        assert "leaders" in summary
        assert len(summary["leaders"]) == 3
        assert "alpha" in summary["leaders"]
        assert "beta" in summary["leaders"]
        assert "delta" in summary["leaders"]
        assert "exploration_exploitation" in summary
        assert summary["exploration_exploitation"] == "adaptive balance"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])