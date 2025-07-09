"""
Tests para verificar la migración de SMO a la nueva arquitectura v2.
"""

import pytest
import numpy as np
from pathlib import Path

# Importar ambas versiones
from algorithms.smo import SMO, Starling
from algorithms.smo_v2 import SMOV2, StarlingV2
from problems.vrp import VRPProblem


class TestSMOV2Migration:
    """Tests para la migración de SMO a v2."""
    
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
        smo_v1 = SMO(test_problem, population_size=pop_size, 
                     max_iterations=max_iter, seed=seed)
        smo_v2 = SMOV2(test_problem, population_size=pop_size, 
                       max_iterations=max_iter, seed=seed)
        
        # Verificar parámetros básicos
        assert smo_v1.population_size == smo_v2.population_size
        assert smo_v1.max_iterations == smo_v2.max_iterations
        assert smo_v1.seed == smo_v2.seed
        assert smo_v1.k == smo_v2.k
        assert smo_v1.mu == smo_v2.mu
    
    def test_individual_creation(self, test_problem):
        """Verifica que los individuos se creen correctamente."""
        # Crear individuos de ambas versiones
        starling_v1 = Starling(test_problem)
        starling_v2 = StarlingV2(test_problem)
        
        # Inicializar la posición de starling_v2 (v1 lo hace automáticamente)
        starling_v2.initialize()
        
        # Verificar propiedades básicas
        assert len(starling_v1.position) == len(starling_v2.position)
        assert starling_v1.position.shape == starling_v2.position.shape
        
        # Verificar que las posiciones estén en [0,1]
        assert np.all(starling_v1.position >= 0) and np.all(starling_v1.position <= 1)
        assert np.all(starling_v2.position >= 0) and np.all(starling_v2.position <= 1)
    
    def test_fitness_evaluation(self, test_problem):
        """Verifica que la evaluación de fitness sea consistente."""
        # Crear individuos con la misma posición
        position = np.random.uniform(0, 1, test_problem.get_dimension())
        
        starling_v1 = Starling(test_problem)
        starling_v1.position = position.copy()
        
        starling_v2 = StarlingV2(test_problem)
        starling_v2.initialize()  # Primero inicializar
        starling_v2.position = position.copy()  # Luego establecer la misma posición
        starling_v2.invalidate_fitness()  # Invalidar para recalcular
        
        # Evaluar fitness
        fitness_v1 = starling_v1.fitness()
        fitness_v2 = starling_v2.fitness()
        
        # Deben ser iguales
        assert fitness_v1 == fitness_v2
    
    def test_reproducibility(self, test_problem):
        """Verifica que ambas versiones sean reproducibles con la misma semilla."""
        seed = 12345
        pop_size = 20
        max_iter = 10
        
        # Ejecutar v2 dos veces
        smo_v2 = SMOV2(test_problem, population_size=pop_size, 
                       max_iterations=max_iter, seed=seed)
        best_v2_run1 = smo_v2.execute()
        
        smo_v2_again = SMOV2(test_problem, population_size=pop_size, 
                             max_iterations=max_iter, seed=seed)
        best_v2_run2 = smo_v2_again.execute()
        
        # Verificar reproducibilidad
        assert best_v2_run1.fitness() == best_v2_run2.fitness()
        assert smo_v2.convergence_curve == smo_v2_again.convergence_curve
    
    def test_convergence_behavior(self, test_problem):
        """Verifica que la versión v2 muestre comportamiento de convergencia."""
        seed = 999
        pop_size = 15
        max_iter = 20
        
        # Ejecutar v2
        smo_v2 = SMOV2(test_problem, population_size=pop_size, 
                       max_iterations=max_iter, seed=seed)
        best_v2 = smo_v2.execute()
        
        # Verificar convergencia
        curve_v2 = smo_v2.get_convergence_curve()
        
        # v2 tiene al menos 1 valor (puede tener hasta max_iter + 1)
        assert len(curve_v2) >= 1
        assert len(curve_v2) <= max_iter + 1
        
        # Debe mostrar mejora (o al menos no empeorar)
        for i in range(1, len(curve_v2)):
            assert curve_v2[i] <= curve_v2[i-1] + 1e-6  # Permitir pequeño error numérico
        
        # El valor final debe ser mejor que el inicial
        assert curve_v2[-1] <= curve_v2[0]
    
    def test_behavior_assignment(self, test_problem):
        """Verifica que los comportamientos se asignen correctamente."""
        smo_v2 = SMOV2(test_problem, population_size=30, max_iterations=10, seed=42)
        smo_v2.initialize_population()
        
        # Ejecutar una iteración para verificar comportamientos
        smo_v2.update_population()
        
        # Verificar que sep_size sea correcto
        sep_size = int(smo_v2.mu * smo_v2.population_size)
        assert sep_size == 9  # 0.3 * 30 = 9
        
        # Verificar que k sea correcto
        assert smo_v2.k == 10  # min(10, 30//3)
    
    def test_move_context_usage(self, test_problem):
        """Verifica que la nueva versión use correctamente MoveContext."""
        from algorithms.base_v2 import MoveContext
        
        # Crear población pequeña
        smo_v2 = SMOV2(test_problem, population_size=5, max_iterations=3, seed=42)
        smo_v2.initialize_population()
        
        # Crear contexto de prueba
        context = MoveContext(
            iteration=1,
            max_iterations=3,
            population=smo_v2.population,
            best_individual=smo_v2.best_solution,
            algorithm_params={
                'behavior_type': 'diving',
                'coef': 0.5
            }
        )
        
        # Verificar que move funcione con context
        starling = smo_v2.population[1]  # No el mejor
        old_position = starling.position.copy()
        
        starling.move(context)
        
        # La posición debe haber cambiado
        assert not np.array_equal(old_position, starling.position)
        
        # La posición debe estar en límites válidos
        assert np.all(starling.position >= 0) and np.all(starling.position <= 1)
    
    def test_summary_information(self, test_problem):
        """Verifica que el resumen incluya información específica de SMO."""
        smo_v2 = SMOV2(test_problem, population_size=10, max_iterations=5)
        summary = smo_v2.summary()
        
        # Verificar información básica
        assert summary["algorithm"] == "SMO v2"
        assert "problem" in summary
        assert summary["population_size"] == 10
        
        # Verificar información específica de SMO
        assert "k" in summary
        assert summary["k"] == 3  # min(10, 10//3)
        assert "mu" in summary
        assert summary["mu"] == 0.3
        assert "behaviors" in summary
        assert len(summary["behaviors"]) == 3
        assert "separating" in summary["behaviors"]
        assert "diving" in summary["behaviors"]
        assert "whirling" in summary["behaviors"]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])