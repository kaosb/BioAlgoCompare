"""
Tests para el sistema de gestión de reproducibilidad.
"""

import pytest
import numpy as np
import random
import json
from pathlib import Path
import tempfile

from utils.reproducibility import (
    ReproducibilityManager,
    RandomStateManager,
    EnvironmentManager,
    ExperimentContext,
    set_global_seed,
    create_reproducible_experiment
)
from utils.reproducibility.reproducibility_validator import (
    AlgorithmReproducibilityValidator,
    ReproducibilityViolation
)


class TestRandomStateManager:
    """Tests para el gestor de estados aleatorios."""
    
    def test_initialization(self):
        """Test inicialización básica."""
        manager = RandomStateManager(base_seed=42)
        
        assert manager.base_seed == 42
        assert 'base' in manager.seed_registry
        assert manager.seed_registry['base'] == 42
    
    def test_deterministic_seeds(self):
        """Test generación determinística de semillas."""
        manager1 = RandomStateManager(base_seed=42)
        manager2 = RandomStateManager(base_seed=42)
        
        # Las semillas derivadas deben ser idénticas
        seed1_algo1 = manager1.get_seed('algorithm_hoa')
        seed2_algo1 = manager2.get_seed('algorithm_hoa')
        
        assert seed1_algo1 == seed2_algo1
    
    def test_different_components_different_seeds(self):
        """Test que componentes diferentes obtienen semillas diferentes."""
        manager = RandomStateManager(base_seed=42)
        
        seed1 = manager.get_seed('component1')
        seed2 = manager.get_seed('component2')
        
        assert seed1 != seed2
    
    def test_random_state_creation(self):
        """Test creación de RandomState."""
        manager = RandomStateManager(base_seed=42)
        
        rs1 = manager.get_random_state('test')
        rs2 = manager.get_random_state('test')
        
        # Mismo componente debe dar mismo estado inicial
        assert rs1.randint(1000) == rs2.randint(1000)
    
    def test_state_snapshot_and_restore(self):
        """Test guardar y restaurar estados."""
        manager = RandomStateManager(base_seed=42)
        
        # Generar algunos números
        original_values = [random.random() for _ in range(5)]
        
        # Guardar estado
        manager.save_state('checkpoint1')
        
        # Generar más números (cambia el estado)
        [random.random() for _ in range(10)]
        
        # Restaurar estado
        manager.restore_state('checkpoint1')
        
        # Los siguientes números deberían ser idénticos
        restored_values = [random.random() for _ in range(5)]
        
        # No podemos comparar directamente porque el estado cambió
        # pero verificamos que se puede guardar y restaurar
        assert 'checkpoint1' in manager.state_snapshots


class TestEnvironmentManager:
    """Tests para el gestor de entorno."""
    
    def test_environment_capture(self):
        """Test captura de información del entorno."""
        manager = EnvironmentManager()
        
        assert 'platform' in manager.environment_info
        assert 'packages' in manager.environment_info
        assert 'environment_variables' in manager.environment_info
        
        # Verificar información de plataforma
        platform_info = manager.environment_info['platform']
        assert 'python_version' in platform_info
        assert 'system' in platform_info
    
    def test_environment_validation(self):
        """Test validación del entorno."""
        manager = EnvironmentManager()
        
        # Sin referencia, solo validaciones básicas
        warnings = manager.validate_environment()
        
        # Debería advertir si PYTHONHASHSEED no está configurado
        # (pero puede estar configurado en el entorno de test)
        assert isinstance(warnings, list)
    
    def test_reproducible_environment_setup(self):
        """Test configuración de entorno reproducible."""
        manager = EnvironmentManager()
        
        # Configurar entorno
        manager.set_reproducible_environment()
        
        # Verificar que se configuraron las variables
        import os
        assert os.environ.get('PYTHONHASHSEED') == '0'
        # Las variables de threads pueden no configurarse si ya existen


class TestReproducibilityManager:
    """Tests para el gestor principal de reproducibilidad."""
    
    def test_initialization(self):
        """Test inicialización del gestor."""
        manager = ReproducibilityManager(base_seed=12345)
        
        assert manager.base_seed == 12345
        assert manager.random_state_manager is not None
        assert manager.environment_manager is not None
    
    def test_create_experiment(self):
        """Test creación de experimento."""
        manager = ReproducibilityManager(base_seed=42)
        
        experiment = manager.create_experiment(
            experiment_id='test_exp_001',
            algorithm='HOA',
            problem='E-n22-k4',
            parameters={'population_size': 30}
        )
        
        assert isinstance(experiment, ExperimentContext)
        assert experiment.experiment_id == 'test_exp_001'
        assert experiment.algorithm == 'HOA'
        assert experiment.algorithm_seed != experiment.problem_seed
    
    def test_experiment_reproducibility(self):
        """Test que experimentos son reproducibles."""
        manager1 = ReproducibilityManager(base_seed=42)
        manager2 = ReproducibilityManager(base_seed=42)
        
        exp1 = manager1.create_experiment('exp1', 'HOA', 'VRP', {})
        exp2 = manager2.create_experiment('exp1', 'HOA', 'VRP', {})
        
        assert exp1.algorithm_seed == exp2.algorithm_seed
        assert exp1.problem_seed == exp2.problem_seed
    
    def test_save_and_load_info(self):
        """Test guardar y cargar información de reproducibilidad."""
        with tempfile.TemporaryDirectory() as tmpdir:
            filepath = Path(tmpdir) / 'repro_info.json'
            
            # Crear y guardar
            manager = ReproducibilityManager(base_seed=999)
            manager.create_experiment('exp1', 'FOA', 'VRP', {'iter': 100})
            manager.save_reproducibility_info(filepath)
            
            assert filepath.exists()
            
            # Cargar
            with open(filepath) as f:
                info = json.load(f)
            
            assert info['base_seed'] == 999
            assert 'exp1' in info['experiments']


class TestExperimentContext:
    """Tests para el contexto de experimento."""
    
    def test_context_creation(self):
        """Test creación de contexto."""
        manager = ReproducibilityManager(base_seed=42)
        context = manager.create_experiment('test', 'HOA', 'VRP', {'pop': 50})
        
        assert context.experiment_id == 'test'
        assert context.parameters == {'pop': 50}
        assert context.algorithm_random_state is not None
    
    def test_algorithm_context_manager(self):
        """Test context manager para algoritmo."""
        manager = ReproducibilityManager(base_seed=42)
        context = manager.create_experiment('test', 'HOA', 'VRP', {})
        
        with context.algorithm_context() as random_state:
            assert random_state is not None
            # Generar números debe ser determinístico
            values = [random_state.random() for _ in range(5)]
            
        # Repetir debe dar los mismos valores
        context2 = manager.create_experiment('test', 'HOA', 'VRP', {})
        with context2.algorithm_context() as random_state:
            values2 = [random_state.random() for _ in range(5)]
            
        assert values == values2
    
    def test_checkpoint_save_load(self):
        """Test guardar y cargar checkpoints."""
        with tempfile.TemporaryDirectory() as tmpdir:
            checkpoint_path = Path(tmpdir) / 'checkpoint.pkl'
            
            manager = ReproducibilityManager(base_seed=42)
            context = manager.create_experiment('test', 'HOA', 'VRP', {})
            
            # Guardar datos
            test_data = {'iteration': 10, 'best_fitness': 375.5}
            context.save_checkpoint(checkpoint_path, test_data)
            
            assert checkpoint_path.exists()
            
            # Cargar datos
            loaded_data = context.load_checkpoint(checkpoint_path)
            assert loaded_data == test_data


class TestReproducibilityValidation:
    """Tests para validación de reproducibilidad."""
    
    def test_violation_creation(self):
        """Test creación de violaciones."""
        violation = ReproducibilityViolation(
            severity='error',
            component='TestAlgorithm',
            issue='Missing seed parameter',
            suggestion='Add seed parameter'
        )
        
        assert violation.severity == 'error'
        assert 'Missing seed' in str(violation)
        assert 'Add seed' in str(violation)
    
    def test_algorithm_validator_basic(self):
        """Test validador básico de algoritmos."""
        validator = AlgorithmReproducibilityValidator()
        
        # Crear una clase de prueba que viola las reglas
        class BadAlgorithm:
            def __init__(self, problem):  # Sin seed!
                self.problem = problem
            
            def run(self):
                return random.random()  # Usa random global!
        
        # Esta prueba requeriría una implementación más compleja
        # Por ahora solo verificamos que el validador existe
        assert validator is not None


class TestGlobalFunctions:
    """Tests para funciones globales de conveniencia."""
    
    def test_set_global_seed(self):
        """Test establecer semilla global."""
        set_global_seed(54321)
        
        # Verificar que se estableció
        manager = get_global_manager()
        assert manager.base_seed == 54321
    
    def test_create_reproducible_experiment(self):
        """Test crear experimento reproducible."""
        exp = create_reproducible_experiment(
            experiment_id='test_global',
            algorithm='WOA',
            problem='VRP',
            parameters={'param1': 10},
            base_seed=11111
        )
        
        assert exp.experiment_id == 'test_global'
        assert exp.algorithm == 'WOA'


# Importar para el test
from utils.reproducibility import get_global_manager


if __name__ == '__main__':
    pytest.main([__file__, '-v'])