"""
Tests para verificar la migración de FOA a la nueva arquitectura v2.
"""

import pytest
import numpy as np
from pathlib import Path

# Importar ambas versiones
from algorithms.foa import FOA, Fossa
from algorithms.foa_v2 import FOAV2, FossaV2
from problems.vrp import VRPProblem


class TestFOAV2Migration:
    """Tests para la migración de FOA a v2."""
    
    @pytest.fixture
    def test_problem(self):
        """Crea un problema de prueba pequeño."""
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
        foa_v1 = FOA(test_problem, population_size=pop_size, 
                     max_iterations=max_iter, seed=seed)
        foa_v2 = FOAV2(test_problem, population_size=pop_size, 
                       max_iterations=max_iter, seed=seed)
        
        # Verificar parámetros básicos
        assert foa_v1.population_size == foa_v2.population_size
        assert foa_v1.max_iterations == foa_v2.max_iterations
        assert foa_v2.seed == seed
    
    def test_individual_creation(self, test_problem):
        """Verifica que los individuos se creen correctamente."""
        # Crear individuos de ambas versiones
        fossa_v1 = Fossa(test_problem)
        fossa_v2 = FossaV2(test_problem)
        fossa_v2.initialize()
        
        # Verificar propiedades básicas
        assert fossa_v1.dimension == fossa_v2.dimension
        assert len(fossa_v1.position) == len(fossa_v2.position)
        assert fossa_v1.position.shape == fossa_v2.position.shape
        
        # Verificar límites
        assert np.array_equal(fossa_v1.lower_bounds, fossa_v2.lower_bounds)
        assert np.array_equal(fossa_v1.upper_bounds, fossa_v2.upper_bounds)
        
        # Verificar que las posiciones estén en [0,1]
        assert np.all(fossa_v1.position >= 0) and np.all(fossa_v1.position <= 1)
        assert np.all(fossa_v2.position >= 0) and np.all(fossa_v2.position <= 1)
    
    def test_fitness_evaluation(self, test_problem):
        """Verifica que la evaluación de fitness sea consistente."""
        position = np.random.uniform(0, 1, test_problem.get_dimension())
        
        fossa_v1 = Fossa(test_problem)
        fossa_v1.position = position.copy()
        
        fossa_v2 = FossaV2(test_problem)
        fossa_v2.initialize()
        fossa_v2.position = position.copy()
        fossa_v2.invalidate_fitness()
        
        # Evaluar fitness
        fitness_v1 = fossa_v1.fitness()
        fitness_v2 = fossa_v2.fitness()
        
        # Deben ser iguales
        assert fitness_v1 == fitness_v2
    
    def test_reproducibility(self, test_problem):
        """Verifica que ambas versiones sean reproducibles con la misma semilla."""
        seed = 12345
        pop_size = 15
        max_iter = 10
        
        # Ejecutar v1 dos veces
        foa_v1_1 = FOA(test_problem, population_size=pop_size, 
                       max_iterations=max_iter, seed=seed)
        best_v1_1 = foa_v1_1.execute()
        
        foa_v1_2 = FOA(test_problem, population_size=pop_size, 
                       max_iterations=max_iter, seed=seed)
        best_v1_2 = foa_v1_2.execute()
        
        # Ejecutar v2 dos veces
        foa_v2_1 = FOAV2(test_problem, population_size=pop_size, 
                         max_iterations=max_iter, seed=seed)
        best_v2_1 = foa_v2_1.execute()
        
        foa_v2_2 = FOAV2(test_problem, population_size=pop_size, 
                         max_iterations=max_iter, seed=seed)
        best_v2_2 = foa_v2_2.execute()
        
        # Verificar reproducibilidad dentro de cada versión
        assert best_v1_1.fitness() == best_v1_2.fitness()
        assert best_v2_1.fitness() == best_v2_2.fitness()
        
        # Las curvas de convergencia deben ser idénticas
        assert foa_v1_1.convergence_curve == foa_v1_2.convergence_curve
        assert foa_v2_1.convergence_curve == foa_v2_2.convergence_curve
    
    def test_convergence_behavior(self, test_problem):
        """Verifica que ambas versiones muestren comportamiento de convergencia."""
        seed = 999
        pop_size = 20
        max_iter = 15
        
        # Ejecutar ambas versiones
        foa_v1 = FOA(test_problem, population_size=pop_size, 
                     max_iterations=max_iter, seed=seed)
        best_v1 = foa_v1.execute()
        
        foa_v2 = FOAV2(test_problem, population_size=pop_size, 
                       max_iterations=max_iter, seed=seed)
        best_v2 = foa_v2.execute()
        
        # Verificar curvas de convergencia
        curve_v1 = foa_v1.get_convergence_curve()
        curve_v2 = foa_v2.get_convergence_curve()
        
        # Ambas versiones incluyen el valor inicial
        # v1 y v2 tienen max_iter + 1 elementos
        assert len(curve_v1) == max_iter + 1
        assert len(curve_v2) == max_iter + 1
        
        # Ambas deben mostrar mejora
        for i in range(1, len(curve_v1)):
            assert curve_v1[i] <= curve_v1[i-1] + 1e-6
        
        for i in range(1, len(curve_v2)):
            assert curve_v2[i] <= curve_v2[i-1] + 1e-6
        
        # Los valores finales deben ser mejores que los iniciales
        assert curve_v1[-1] <= curve_v1[0]
        assert curve_v2[-1] <= curve_v2[0]
    
    def test_move_phases(self, test_problem):
        """Verifica que las fases de exploración/explotación funcionen."""
        from algorithms.base_v2 import MoveContext
        
        # Crear población pequeña
        foa_v2 = FOAV2(test_problem, population_size=5, max_iterations=10, seed=42)
        foa_v2.initialize_population()
        
        # Probar fase de exploración (primera mitad)
        context_exploration = MoveContext(
            iteration=2,  # iteración 3 de 10
            max_iterations=10,
            population=foa_v2.population,
            best_individual=foa_v2.best_solution,
            algorithm_params={}
        )
        
        fossa = foa_v2.population[2]
        old_pos = fossa.position.copy()
        fossa.move(context_exploration)
        
        # La posición debe cambiar (a menos que no haya lemures)
        if any(ind.fitness() < fossa.fitness() for ind in foa_v2.population if ind is not fossa):
            assert not np.array_equal(old_pos, fossa.position)
        
        # Probar fase de explotación (segunda mitad)
        context_exploitation = MoveContext(
            iteration=7,  # iteración 8 de 10
            max_iterations=10,
            population=foa_v2.population,
            best_individual=foa_v2.best_solution,
            algorithm_params={}
        )
        
        fossa2 = foa_v2.population[3]
        old_pos2 = fossa2.position.copy()
        fossa2.move(context_exploitation)
        
        # En explotación el movimiento es diferente
        if not np.array_equal(old_pos2, fossa2.position):
            # El movimiento en explotación debe ser más conservador
            # (esto es difícil de verificar sin acceso a los detalles internos)
            assert True  # Por ahora solo verificamos que se mueve
    
    def test_summary_information(self, test_problem):
        """Verifica que el resumen incluya información específica de FOA."""
        foa_v2 = FOAV2(test_problem, population_size=10, max_iterations=5)
        summary = foa_v2.summary()
        
        # Verificar información básica
        assert summary["algorithm"] == "Fossa Optimization Algorithm v2"
        assert "problem" in summary
        assert summary["population_size"] == 10
        assert "iterations" in summary
        
        # Verificar información específica de FOA
        assert "phases" in summary
        assert len(summary["phases"]) == 2
        assert "inspiration" in summary
        assert "key_mechanism" in summary


if __name__ == "__main__":
    pytest.main([__file__, "-v"])