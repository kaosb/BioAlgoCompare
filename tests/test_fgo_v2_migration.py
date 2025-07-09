"""
Tests para verificar la migración de FGO a la nueva arquitectura v2.
"""

import pytest
import numpy as np
from pathlib import Path

# Importar ambas versiones
from algorithms.fgo import FGO, Flamingo
from algorithms.fgo_v2 import FGOV2, FlamingoV2
from problems.vrp import VRPProblem


class TestFGOV2Migration:
    """Tests para la migración de FGO a v2."""
    
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
        fgo_v1 = FGO(test_problem, population_size=pop_size, 
                     max_iterations=max_iter, seed=seed)
        fgo_v2 = FGOV2(test_problem, population_size=pop_size, 
                       max_iterations=max_iter, seed=seed)
        
        # Verificar parámetros básicos
        assert fgo_v1.population_size == fgo_v2.population_size
        assert fgo_v1.max_iterations == fgo_v2.max_iterations
        # v2 almacena seed
        assert fgo_v2.seed == seed
    
    def test_individual_creation(self, test_problem):
        """Verifica que los individuos se creen correctamente."""
        # Crear individuos de ambas versiones
        flamingo_v1 = Flamingo(test_problem)
        flamingo_v2 = FlamingoV2(test_problem)
        
        # Inicializar la posición de flamingo_v2 (v1 lo hace automáticamente)
        flamingo_v2.initialize()
        
        # Verificar propiedades básicas
        assert flamingo_v1.dimension == flamingo_v2.dimension
        assert len(flamingo_v1.position) == len(flamingo_v2.position)
        assert flamingo_v1.position.shape == flamingo_v2.position.shape
        
        # Verificar que las posiciones estén en [0,1]
        assert np.all(flamingo_v1.position >= 0) and np.all(flamingo_v1.position <= 1)
        assert np.all(flamingo_v2.position >= 0) and np.all(flamingo_v2.position <= 1)
    
    def test_fitness_evaluation(self, test_problem):
        """Verifica que la evaluación de fitness sea consistente."""
        # Crear individuos con la misma posición
        position = np.random.uniform(0, 1, test_problem.get_dimension())
        
        flamingo_v1 = Flamingo(test_problem)
        flamingo_v1.position = position.copy()
        
        flamingo_v2 = FlamingoV2(test_problem)
        flamingo_v2.initialize()  # Primero inicializar
        flamingo_v2.position = position.copy()  # Luego establecer la misma posición
        flamingo_v2.invalidate_fitness()  # Invalidar para recalcular
        
        # Evaluar fitness
        fitness_v1 = flamingo_v1.fitness()
        fitness_v2 = flamingo_v2.fitness()
        
        # Deben ser iguales
        assert fitness_v1 == fitness_v2
    
    def test_reproducibility(self, test_problem):
        """Verifica que ambas versiones sean reproducibles con la misma semilla."""
        seed = 12345
        pop_size = 20
        max_iter = 10
        
        # Ejecutar v2 dos veces
        fgo_v2 = FGOV2(test_problem, population_size=pop_size, 
                       max_iterations=max_iter, seed=seed)
        best_v2_run1 = fgo_v2.execute()
        
        fgo_v2_again = FGOV2(test_problem, population_size=pop_size, 
                             max_iterations=max_iter, seed=seed)
        best_v2_run2 = fgo_v2_again.execute()
        
        # Verificar reproducibilidad
        assert best_v2_run1.fitness() == best_v2_run2.fitness()
        assert fgo_v2.convergence_curve == fgo_v2_again.convergence_curve
    
    def test_convergence_behavior(self, test_problem):
        """Verifica que la versión v2 muestre comportamiento de convergencia."""
        seed = 999
        pop_size = 15
        max_iter = 20
        
        # Ejecutar v2
        fgo_v2 = FGOV2(test_problem, population_size=pop_size, 
                       max_iterations=max_iter, seed=seed)
        best_v2 = fgo_v2.execute()
        
        # Verificar convergencia
        curve_v2 = fgo_v2.get_convergence_curve()
        
        # v2 tiene al menos 1 valor (puede tener hasta max_iter + 1)
        assert len(curve_v2) >= 1
        assert len(curve_v2) <= max_iter + 1
        
        # Debe mostrar mejora (o al menos no empeorar)
        for i in range(1, len(curve_v2)):
            assert curve_v2[i] <= curve_v2[i-1] + 1e-6  # Permitir pequeño error numérico
        
        # El valor final debe ser mejor que el inicial
        assert curve_v2[-1] <= curve_v2[0]
    
    def test_group_allocation(self, test_problem):
        """Verifica que los grupos se asignen correctamente."""
        fgo_v2 = FGOV2(test_problem, population_size=30, max_iterations=10, seed=42)
        fgo_v2.initialize_population()
        
        # Calcular tamaños esperados de grupos
        MPb = int(fgo_v2.MPb_ratio * fgo_v2.population_size)
        assert MPb == 3  # 0.1 * 30 = 3
        
        # Verificar que MPb_ratio esté correctamente establecido
        assert fgo_v2.MPb_ratio == 0.1
    
    def test_move_context_usage(self, test_problem):
        """Verifica que la nueva versión use correctamente MoveContext."""
        from algorithms.base_v2 import MoveContext
        
        # Crear población pequeña
        fgo_v2 = FGOV2(test_problem, population_size=5, max_iterations=3, seed=42)
        fgo_v2.initialize_population()
        
        # Crear contexto de prueba para forrajeo
        context = MoveContext(
            iteration=1,
            max_iterations=3,
            population=fgo_v2.population,
            best_individual=fgo_v2.best_solution,
            algorithm_params={'mode': 'forage'}
        )
        
        # Verificar que move funcione con context
        flamingo = fgo_v2.population[1]  # No el mejor
        old_position = flamingo.position.copy()
        
        flamingo.move(context)
        
        # La posición debe haber cambiado
        assert not np.array_equal(old_position, flamingo.position)
        
        # La posición debe estar en límites válidos
        assert np.all(flamingo.position >= 0) and np.all(flamingo.position <= 1)
    
    def test_behaviors(self, test_problem):
        """Verifica que ambos comportamientos (forage y migrate) funcionen."""
        from algorithms.base_v2 import MoveContext
        
        fgo_v2 = FGOV2(test_problem, population_size=10, max_iterations=5, seed=42)
        fgo_v2.initialize_population()
        
        flamingo = fgo_v2.population[5]  # Un flamenco intermedio
        
        # Probar comportamiento de forrajeo
        old_pos_forage = flamingo.position.copy()
        context_forage = MoveContext(
            iteration=1,
            max_iterations=5,
            population=fgo_v2.population,
            best_individual=fgo_v2.best_solution,
            algorithm_params={'mode': 'forage'}
        )
        flamingo.move(context_forage)
        
        # Verificar que se movió
        assert not np.array_equal(old_pos_forage, flamingo.position)
        
        # Probar comportamiento de migración
        old_pos_migrate = flamingo.position.copy()
        context_migrate = MoveContext(
            iteration=2,
            max_iterations=5,
            population=fgo_v2.population,
            best_individual=fgo_v2.best_solution,
            algorithm_params={'mode': 'migrate'}
        )
        flamingo.move(context_migrate)
        
        # Verificar que se movió
        assert not np.array_equal(old_pos_migrate, flamingo.position)
    
    def test_summary_information(self, test_problem):
        """Verifica que el resumen incluya información específica de FGO."""
        fgo_v2 = FGOV2(test_problem, population_size=10, max_iterations=5)
        summary = fgo_v2.summary()
        
        # Verificar información básica
        assert summary["algorithm"] == "FGO v2"
        assert "problem" in summary
        assert summary["population_size"] == 10
        
        # Verificar información específica de FGO
        assert "MPb_ratio" in summary
        assert summary["MPb_ratio"] == 0.1
        assert "behaviors" in summary
        assert len(summary["behaviors"]) == 2
        assert "migrate" in summary["behaviors"]
        assert "forage" in summary["behaviors"]
        assert "groups" in summary
        assert len(summary["groups"]) == 3


if __name__ == "__main__":
    pytest.main([__file__, "-v"])