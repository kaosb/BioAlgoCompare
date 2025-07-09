"""
Tests para verificar la migración de APO a la nueva arquitectura v2.
"""

import pytest
import numpy as np
from pathlib import Path

# Importar ambas versiones
from algorithms.apo_v2 import APOV2
from algorithms.apo_v2 import APOV2, ProtozoaV2
from problems.vrp_v2 import VRPProblemV2


class TestAPOV2Migration:
    """Tests para la migración de APO a v2."""
    
    @pytest.fixture
    def test_problem(self):
        """Crea un problema de prueba pequeño."""
        data_dir = Path("data/vrp/test")
        instance_path = data_dir / "test-n5-k2.vrp"
        
        if not instance_path.exists():
            # Usar otra instancia pequeña si no existe la de prueba
            data_dir = Path("data/vrp")
            instance_path = data_dir / "P-n16-k8.vrp"
            
            if not instance_path.exists():
                pytest.skip("Instancia de prueba no encontrada")
                
        return VRPProblem(str(instance_path))
    
    def test_initialization_compatibility(self, test_problem):
        """Verifica que ambas versiones se inicialicen de forma similar."""
        seed = 42
        pop_size = 10
        max_iter = 5
        
        # Crear instancias de ambas versiones
        v1 = APO(test_problem, population_size=pop_size, 
                                         max_iterations=max_iter, seed=seed)
        v2 = APOV2(test_problem, population_size=pop_size, 
                                           max_iterations=max_iter, seed=seed)
        
        # Verificar parámetros básicos
        assert v1.population_size == v2.population_size
        assert v1.max_iterations == v2.max_iterations
        assert v2.seed == seed
    
    def test_individual_creation(self, test_problem):
        """Verifica que los individuos se creen correctamente."""
        # Crear individuos de ambas versiones
        ind_v1 = Protozoa(test_problem)
        ind_v2 = ProtozoaV2(test_problem)
        ind_v2.initialize()
        
        # Verificar propiedades básicas
        assert ind_v1.dimension == ind_v2.dimension
        assert len(ind_v1.position) == len(ind_v2.position)
        assert ind_v1.position.shape == ind_v2.position.shape
        
        # Verificar que las posiciones estén en límites válidos
        assert np.all(ind_v1.position >= 0) and np.all(ind_v1.position <= 1)
        assert np.all(ind_v2.position >= 0) and np.all(ind_v2.position <= 1)
    
    def test_reproducibility(self, test_problem):
        """Verifica que ambas versiones sean reproducibles con la misma semilla."""
        seed = 12345
        pop_size = 15
        max_iter = 10
        
        # Ejecutar v2 dos veces
        v2_1 = APOV2(test_problem, population_size=pop_size, 
                                             max_iterations=max_iter, seed=seed)
        best_v2_1 = v2_1.execute()
        
        v2_2 = APOV2(test_problem, population_size=pop_size, 
                                             max_iterations=max_iter, seed=seed)
        best_v2_2 = v2_2.execute()
        
        # Verificar reproducibilidad
        assert best_v2_1.fitness() == best_v2_2.fitness()
        assert v2_1.convergence_curve == v2_2.convergence_curve
    
    # TODO: Agregar más tests según las particularidades del algoritmo


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
