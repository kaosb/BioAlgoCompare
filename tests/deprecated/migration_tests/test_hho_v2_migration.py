"""
Tests para verificar la migración de HHO a la nueva arquitectura v2.
Compara el comportamiento y resultados con la versión original.
"""

import pytest
import numpy as np
from pathlib import Path

# Importar ambas versiones
from algorithms.hho_v2 import HHOV2
from algorithms.hho_v2 import HHOV2, HawkV2
from problems.vrp_v2 import VRPProblemV2


class TestHHOV2Migration:
    """Tests para la migración de HHO a v2."""
    
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
        hho_v1 = HHO(test_problem, population_size=pop_size, 
                     max_iterations=max_iter, seed=seed)
        hho_v2 = HHOV2(test_problem, population_size=pop_size, 
                       max_iterations=max_iter, seed=seed)
        
        # Verificar parámetros básicos
        assert hho_v1.population_size == hho_v2.population_size
        assert hho_v1.max_iterations == hho_v2.max_iterations
        # Nota: HHO v1 no almacena seed como atributo, pero v2 sí
        assert hho_v2.seed == seed
    
    def test_individual_creation(self, test_problem):
        """Verifica que los individuos se creen correctamente."""
        # Crear individuos de ambas versiones
        hawk_v1 = Hawk(test_problem)
        hawk_v2 = HawkV2(test_problem)
        
        # Inicializar la posición de hawk_v2 (v1 lo hace automáticamente)
        hawk_v2.initialize()
        
        # Verificar propiedades básicas
        assert hawk_v1.dimension == hawk_v2.dimension
        assert len(hawk_v1.position) == len(hawk_v2.position)
        assert hawk_v1.position.shape == hawk_v2.position.shape
        
        # Verificar que las posiciones estén en [0,1]
        assert np.all(hawk_v1.position >= 0) and np.all(hawk_v1.position <= 1)
        assert np.all(hawk_v2.position >= 0) and np.all(hawk_v2.position <= 1)
    
    def test_fitness_evaluation(self, test_problem):
        """Verifica que la evaluación de fitness sea consistente."""
        # Crear individuos con la misma posición
        position = np.random.uniform(0, 1, test_problem.get_dimension())
        
        hawk_v1 = Hawk(test_problem)
        hawk_v1.position = position.copy()
        
        hawk_v2 = HawkV2(test_problem)
        hawk_v2.initialize()  # Primero inicializar
        hawk_v2.position = position.copy()  # Luego establecer la misma posición
        hawk_v2.invalidate_fitness()  # Invalidar para recalcular
        
        # Evaluar fitness
        fitness_v1 = hawk_v1.fitness()
        fitness_v2 = hawk_v2.fitness()
        
        # Deben ser iguales
        assert fitness_v1 == fitness_v2
    
    def test_reproducibility(self, test_problem):
        """Verifica que ambas versiones sean reproducibles con la misma semilla."""
        seed = 12345
        pop_size = 20
        max_iter = 10
        
        # Ejecutar v1
        hho_v1 = HHO(test_problem, population_size=pop_size, 
                     max_iterations=max_iter, seed=seed)
        best_v1_run1 = hho_v1.execute()
        
        # Ejecutar v1 nuevamente
        hho_v1_again = HHO(test_problem, population_size=pop_size, 
                           max_iterations=max_iter, seed=seed)
        best_v1_run2 = hho_v1_again.execute()
        
        # Ejecutar v2
        hho_v2 = HHOV2(test_problem, population_size=pop_size, 
                       max_iterations=max_iter, seed=seed)
        best_v2_run1 = hho_v2.execute()
        
        # Ejecutar v2 nuevamente
        hho_v2_again = HHOV2(test_problem, population_size=pop_size, 
                             max_iterations=max_iter, seed=seed)
        best_v2_run2 = hho_v2_again.execute()
        
        # Verificar reproducibilidad dentro de cada versión
        assert best_v1_run1.fitness() == best_v1_run2.fitness()
        assert best_v2_run1.fitness() == best_v2_run2.fitness()
        
        # Las curvas de convergencia deben ser idénticas para cada versión
        assert hho_v1.convergence_curve == hho_v1_again.convergence_curve
        assert hho_v2.convergence_curve == hho_v2_again.convergence_curve
    
    def test_convergence_behavior(self, test_problem):
        """Verifica que ambas versiones muestren comportamiento de convergencia."""
        seed = 999
        pop_size = 15
        max_iter = 20
        
        # Ejecutar ambas versiones
        hho_v1 = HHO(test_problem, population_size=pop_size, 
                     max_iterations=max_iter, seed=seed)
        best_v1 = hho_v1.execute()
        
        hho_v2 = HHOV2(test_problem, population_size=pop_size, 
                       max_iterations=max_iter, seed=seed)
        best_v2 = hho_v2.execute()
        
        # Verificar que ambas converjan (mejoren con el tiempo)
        curve_v1 = hho_v1.get_convergence_curve()
        curve_v2 = hho_v2.get_convergence_curve()
        
        # Verificar longitud de las curvas
        # v1 tiene exactamente max_iter elementos
        # v2 tiene max_iter + 1 (incluye el valor inicial)
        assert len(curve_v1) == max_iter
        assert len(curve_v2) == max_iter + 1
        
        # Ambas deben mostrar mejora (o al menos no empeorar)
        for i in range(1, len(curve_v1)):
            assert curve_v1[i] <= curve_v1[i-1] + 1e-6  # Permitir pequeño error numérico
        
        for i in range(1, len(curve_v2)):
            assert curve_v2[i] <= curve_v2[i-1] + 1e-6  # Permitir pequeño error numérico
        
        # Los valores finales deben ser mejores que los iniciales
        assert curve_v1[-1] <= curve_v1[0]
        assert curve_v2[-1] <= curve_v2[0]
    
    def test_move_context_usage(self, test_problem):
        """Verifica que la nueva versión use correctamente MoveContext."""
        from algorithms.base_v2 import MoveContext
        
        # Crear población pequeña
        hho_v2 = HHOV2(test_problem, population_size=5, max_iterations=3, seed=42)
        hho_v2.initialize_population()
        
        # Crear contexto de prueba
        context = MoveContext(
            iteration=1,
            max_iterations=3,
            population=hho_v2.population,
            best_individual=hho_v2.best_solution,
            algorithm_params={}
        )
        
        # Verificar que move funcione con context
        hawk = hho_v2.population[1]  # No el mejor
        old_position = hawk.position.copy()
        
        hawk.move(context)
        
        # La posición debe haber cambiado
        assert not np.array_equal(old_position, hawk.position)
        
        # La posición debe estar en límites válidos
        assert np.all(hawk.position >= 0) and np.all(hawk.position <= 1)
    
    def test_summary_information(self, test_problem):
        """Verifica que el resumen incluya información específica de HHO."""
        hho_v2 = HHOV2(test_problem, population_size=10, max_iterations=5)
        summary = hho_v2.summary()
        
        # Verificar información básica
        assert summary["algorithm"] == "Harris Hawks Optimization v2"
        assert "problem" in summary
        assert summary["population_size"] == 10
        # Note: summary incluye "iterations" (ejecutadas), no "max_iterations"
        assert "iterations" in summary
        
        # Verificar información específica de HHO
        assert "levy_beta" in summary
        assert summary["levy_beta"] == 1.5
        assert "exploration_exploitation" in summary
        assert "strategies" in summary
        assert len(summary["strategies"]) == 6  # 6 estrategias diferentes


if __name__ == "__main__":
    pytest.main([__file__, "-v"])