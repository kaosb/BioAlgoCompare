"""
Tests para Raven Roosting Optimization (RRO) v2.
"""

import pytest
import numpy as np
from algorithms.rro_v2 import RROV2, RavenV2
from algorithms.base_v2 import MoveContext
from problems.continuous.unconstrained import SphereProblem, RastriginProblem


class TestRavenV2:
    """Tests para la clase RavenV2."""
    
    def test_raven_initialization(self):
        """Prueba la inicialización de un cuervo."""
        problem = SphereProblem(dimension=5)
        raven = RavenV2(problem)
        
        assert raven.dimension == 5
        assert raven.position is None  # No inicializado aún
        assert raven.personal_best_position is None
        assert raven.personal_best_fitness == float('inf')
        
        # Inicializar
        raven.initialize()
        
        assert len(raven.position) == 5
        assert np.all(raven.position >= 0) and np.all(raven.position <= 1)
        assert np.array_equal(raven.personal_best_position, raven.position)
    
    def test_update_personal_best(self):
        """Prueba la actualización del mejor personal."""
        problem = SphereProblem(dimension=3)
        raven = RavenV2(problem)
        raven.initialize()
        
        # Primera evaluación
        initial_fitness = raven.fitness()
        raven.personal_best_fitness = initial_fitness
        
        # Cambiar posición a una mejor
        raven.position = np.array([0.1, 0.1, 0.1])
        raven.invalidate_fitness()
        new_fitness = raven.fitness()
        
        # Verificar que se actualiza si mejora
        if new_fitness < raven.personal_best_fitness:
            old_pb = raven.personal_best_fitness
            raven.personal_best_fitness = new_fitness
            raven.personal_best_position = np.copy(raven.position)
            assert raven.personal_best_fitness < old_pb
    
    def test_raven_copy(self):
        """Prueba la copia de un cuervo."""
        problem = SphereProblem(dimension=3)
        raven = RavenV2(problem)
        raven.initialize()
        raven.personal_best_fitness = 10.0
        raven.personal_best_position = np.array([0.2, 0.3, 0.4])
        
        copy = raven.clone()
        
        assert isinstance(copy, RavenV2)
        assert np.array_equal(copy.position, raven.position)
        assert copy.personal_best_fitness == raven.personal_best_fitness
        assert np.array_equal(copy.personal_best_position, raven.personal_best_position)
        
        # Verificar que es una copia profunda
        copy.position[0] = 0.99
        assert not np.array_equal(copy.position, raven.position)
    
    def test_move_method(self):
        """Prueba el método move del cuervo."""
        problem = SphereProblem(dimension=3)
        raven = RavenV2(problem)
        raven.initialize()
        
        initial_pos = np.copy(raven.position)
        
        # Crear contexto de movimiento
        context = MoveContext(
            population=[raven],
            best_individual=raven,
            iteration=0,
            max_iterations=100,
            algorithm_params={
                'target_position': np.array([0.5, 0.5, 0.5]),
                'Rpcpt': 0.1,
                'Npcpt': 5,
                'Nsteps': 5,
                'Pstop': 0.1
            }
        )
        
        raven.move(context)
        
        # La posición debería cambiar
        assert not np.array_equal(raven.position, initial_pos)
        # Debería estar dentro de los límites
        assert np.all(raven.position >= 0)
        assert np.all(raven.position <= 1)


class TestRROV2:
    """Tests para el algoritmo RROV2."""
    
    def test_rro_initialization_defaults(self):
        """Prueba la inicialización con valores por defecto."""
        problem = SphereProblem(dimension=10)
        rro = RROV2(problem)
        
        assert rro.population_size == 30
        assert rro.max_iterations == 100
        assert rro.Npcpt == 10
        assert rro.Nsteps == 10
        assert rro.Percfollow == 0.2
        assert rro.Pstop == 0.1
        
        # Rpcpt y Rleader deberían calcularse automáticamente
        R = 1.0
        expected_radius = 0.1 * R * np.sqrt(10)
        assert rro.Rpcpt == pytest.approx(expected_radius)
        assert rro.Rleader == pytest.approx(expected_radius)
    
    def test_rro_initialization_custom(self):
        """Prueba la inicialización con valores personalizados."""
        problem = SphereProblem(dimension=5)
        rro = RROV2(
            problem,
            population_size=50,
            max_iterations=200,
            Rpcpt=0.5,
            Rleader=0.3,
            Npcpt=20,
            Nsteps=15,
            Percfollow=0.5,
            Pstop=0.2,
            seed=123
        )
        
        assert rro.population_size == 50
        assert rro.max_iterations == 200
        assert rro.Rpcpt == 0.5
        assert rro.Rleader == 0.3
        assert rro.Npcpt == 20
        assert rro.Nsteps == 15
        assert rro.Percfollow == 0.5
        assert rro.Pstop == 0.2
    
    def test_parameter_validation(self):
        """Prueba la validación de parámetros."""
        problem = SphereProblem(dimension=5)
        
        # Rpcpt inválido
        with pytest.raises(ValueError, match="Rpcpt"):
            RROV2(problem, Rpcpt=0.0)  # Debe ser > 0.01
        
        with pytest.raises(ValueError, match="Rpcpt"):
            RROV2(problem, Rpcpt=1.5)  # Debe ser <= 1.0
        
        # Rleader inválido
        with pytest.raises(ValueError, match="Rleader"):
            RROV2(problem, Rleader=-0.1)
        
        # Npcpt inválido
        with pytest.raises(ValueError, match="Npcpt"):
            RROV2(problem, Npcpt=0)
        
        with pytest.raises(ValueError, match="Npcpt"):
            RROV2(problem, Npcpt=100)  # Debe ser <= 50
        
        # Nsteps inválido
        with pytest.raises(ValueError, match="Nsteps"):
            RROV2(problem, Nsteps=-5)
        
        # Percfollow inválido
        with pytest.raises(ValueError, match="Percfollow"):
            RROV2(problem, Percfollow=1.5)
        
        # Pstop inválido
        with pytest.raises(ValueError, match="Pstop"):
            RROV2(problem, Pstop=-0.1)
    
    def test_edge_cases(self):
        """Prueba casos límite."""
        problem = SphereProblem(dimension=5)
        
        # Valores límite válidos
        rro = RROV2(
            problem,
            Rpcpt=0.01,  # Mínimo
            Rleader=1.0,  # Máximo
            Npcpt=1,      # Mínimo
            Nsteps=50,    # Máximo
            Percfollow=0.0,  # Mínimo
            Pstop=1.0     # Máximo
        )
        
        assert rro.Rpcpt == 0.01
        assert rro.Rleader == 1.0
        assert rro.Npcpt == 1
        assert rro.Nsteps == 50
        assert rro.Percfollow == 0.0
        assert rro.Pstop == 1.0
    
    def test_create_individual(self):
        """Prueba la creación de individuos."""
        problem = SphereProblem(dimension=5)
        rro = RROV2(problem)
        
        raven = rro._create_individual()
        
        assert isinstance(raven, RavenV2)
        assert raven.problem == problem
        assert raven.dimension == 5
    
    def test_algorithm_execution(self):
        """Prueba la ejecución completa del algoritmo."""
        problem = SphereProblem(dimension=5)
        rro = RROV2(
            problem,
            population_size=20,
            max_iterations=50,
            seed=42
        )
        
        best_solution = rro.execute()
        
        assert best_solution is not None
        assert hasattr(best_solution, 'fitness')
        assert hasattr(best_solution, 'position')
        assert len(rro.convergence_curve) == 51  # inicial + 50 iteraciones
        
        # Para Sphere, debería acercarse a 0
        assert best_solution.fitness() < 1.0
    
    def test_convergence_behavior(self):
        """Prueba el comportamiento de convergencia."""
        problem = SphereProblem(dimension=3)
        rro = RROV2(
            problem,
            population_size=30,
            max_iterations=100,
            Percfollow=0.8,  # Alta probabilidad de seguir al líder
            seed=123
        )
        
        rro.execute()
        
        # La convergencia debería ser monotónica no creciente
        for i in range(1, len(rro.convergence_curve)):
            assert rro.convergence_curve[i] <= rro.convergence_curve[i-1]
        
        # Debería mejorar significativamente desde el inicio
        assert rro.convergence_curve[-1] < rro.convergence_curve[0] * 0.1
    
    def test_reproducibility(self):
        """Prueba la reproducibilidad con semilla."""
        problem = RastriginProblem(dimension=5)
        
        rro1 = RROV2(problem, population_size=20, max_iterations=30, seed=42)
        result1 = rro1.execute()
        
        rro2 = RROV2(problem, population_size=20, max_iterations=30, seed=42)
        result2 = rro2.execute()
        
        assert result1.fitness() == result2.fitness()
        assert np.array_equal(result1.position, result2.position)
        assert rro1.convergence_curve == rro2.convergence_curve
    
    def test_get_name(self):
        """Prueba el método get_name."""
        problem = SphereProblem(dimension=5)
        rro = RROV2(problem)
        assert rro.get_name() == "RRO_v2"
    
    def test_get_parameters(self):
        """Prueba el método get_parameters."""
        problem = SphereProblem(dimension=5)
        rro = RROV2(
            problem,
            population_size=40,
            max_iterations=150,
            Rpcpt=0.2,
            Rleader=0.15,
            Npcpt=15,
            Nsteps=20,
            Percfollow=0.3,
            Pstop=0.05
        )
        
        params = rro.get_parameters()
        
        assert params["population_size"] == 40
        assert params["max_iterations"] == 150
        assert params["Rpcpt"] == 0.2
        assert params["Rleader"] == 0.15
        assert params["Npcpt"] == 15
        assert params["Nsteps"] == 20
        assert params["Percfollow"] == 0.3
        assert params["Pstop"] == 0.05
    
    def test_extreme_percfollow(self):
        """Prueba comportamiento con valores extremos de Percfollow."""
        problem = SphereProblem(dimension=3)
        
        # Percfollow = 0 (nunca sigue al líder)
        rro1 = RROV2(problem, Percfollow=0.0, max_iterations=20, seed=42)
        rro1.execute()
        
        # Percfollow = 1 (siempre sigue al líder)
        rro2 = RROV2(problem, Percfollow=1.0, max_iterations=20, seed=42)
        rro2.execute()
        
        # Ambos deberían funcionar correctamente
        assert len(rro1.convergence_curve) == 21
        assert len(rro2.convergence_curve) == 21
    
    def test_extreme_pstop(self):
        """Prueba comportamiento con valores extremos de Pstop."""
        problem = SphereProblem(dimension=3)
        
        # Pstop = 0 (nunca para anticipadamente)
        rro1 = RROV2(problem, Pstop=0.0, max_iterations=10, seed=42)
        rro1.execute()
        
        # Pstop = 1 (siempre para si mejora)
        rro2 = RROV2(problem, Pstop=1.0, max_iterations=10, seed=42)
        rro2.execute()
        
        # Ambos deberían completar la ejecución
        assert rro1.best_solution is not None
        assert rro2.best_solution is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])