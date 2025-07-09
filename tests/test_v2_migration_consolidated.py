"""
Tests consolidados para verificar la migración de TODOS los algoritmos a v2.

Este archivo reemplaza los 18 archivos individuales de migración usando
parametrización de pytest para máxima eficiencia y mantenibilidad.
"""

import pytest
import numpy as np
from pathlib import Path
import importlib

# Lista de todos los algoritmos para testear
ALGORITHMS = [
    'aha', 'apo', 'egto', 'ewa', 'fgo', 'foa', 'fsa', 'gto', 
    'gvoa', 'hho', 'hoa', 'mrfo', 'opa', 'rro', 'sho', 'sma', 
    'smo', 'woa'
]

# Mapeo de nombres de algoritmos a clases
ALGORITHM_CLASSES = {
    'aha': ('AHAV2', 'HummingbirdV2'),
    'apo': ('APOV2', 'ProtozoaV2'),
    'egto': ('EGTOV2', 'EnhancedGorillaV2'),
    'ewa': ('EWAV2', 'EarthwormV2'),
    'fgo': ('FGOV2', 'FlamingoV2'),
    'foa': ('FOAV2', 'FossaV2'),
    'fsa': ('FSAV2', 'FireworksV2'),
    'gto': ('GTOV2', 'GorillaV2'),
    'gvoa': ('GVOAV2', 'VultureV2'),
    'hho': ('HHOV2', 'HawkV2'),
    'hoa': ('HOAV2', 'HyenaV2'),
    'mrfo': ('MRFOV2', 'MantaRayV2'),
    'opa': ('OPAV2', 'OrcaV2'),
    'rro': ('RROV2', 'RavenV2'),
    'sho': ('SHOV2', 'SpottedHyenaV2'),
    'sma': ('SMAV2', 'SlimeMouldV2'),
    'smo': ('SMOV2', 'StarlingV2'),
    'woa': ('WOAV2', 'WhaleV2')
}


class TestAlgorithmV2Migration:
    """Tests consolidados para la migración de algoritmos a v2."""
    
    @pytest.fixture(scope="class")
    def test_problem(self):
        """Crea un problema de prueba pequeño."""
        # Importar aquí para evitar problemas circulares
        from problems.vrp_v2 import VRPProblemV2
        
        data_dir = Path("data/vrp")
        instance_path = data_dir / "P-n16-k8.vrp"
        
        if not instance_path.exists():
            pytest.skip(f"Instancia de prueba no encontrada: {instance_path}")
            
        return VRPProblemV2(str(instance_path))
    
    @pytest.mark.parametrize("algorithm_name", ALGORITHMS)
    def test_algorithm_import(self, algorithm_name):
        """Verifica que el algoritmo v2 se pueda importar correctamente."""
        try:
            module = importlib.import_module(f'algorithms.{algorithm_name}_v2')
            algo_class, individual_class = ALGORITHM_CLASSES[algorithm_name]
            
            # Verificar que las clases existan
            assert hasattr(module, algo_class), f"Clase {algo_class} no encontrada"
            assert hasattr(module, individual_class), f"Clase {individual_class} no encontrada"
            
        except ImportError as e:
            pytest.fail(f"No se pudo importar {algorithm_name}_v2: {e}")
    
    @pytest.mark.parametrize("algorithm_name", ALGORITHMS)
    def test_initialization(self, algorithm_name, test_problem):
        """Verifica que los algoritmos v2 se inicialicen correctamente."""
        module = importlib.import_module(f'algorithms.{algorithm_name}_v2')
        algo_class_name, _ = ALGORITHM_CLASSES[algorithm_name]
        AlgorithmClass = getattr(module, algo_class_name)
        
        # Parámetros estándar
        seed = 42
        pop_size = 10
        max_iter = 5
        
        # Crear instancia
        algorithm = AlgorithmClass(
            test_problem, 
            population_size=pop_size, 
            max_iterations=max_iter, 
            seed=seed
        )
        
        # Verificaciones básicas
        assert algorithm.population_size == pop_size
        assert algorithm.max_iterations == max_iter
        assert algorithm.seed == seed
        assert algorithm.problem == test_problem
    
    @pytest.mark.parametrize("algorithm_name", ALGORITHMS)
    def test_individual_creation(self, algorithm_name, test_problem):
        """Verifica que los individuos se creen correctamente."""
        module = importlib.import_module(f'algorithms.{algorithm_name}_v2')
        algo_class_name, individual_class_name = ALGORITHM_CLASSES[algorithm_name]
        
        AlgorithmClass = getattr(module, algo_class_name)
        IndividualClass = getattr(module, individual_class_name)
        
        # Crear algoritmo
        algorithm = AlgorithmClass(test_problem, population_size=5, seed=42)
        
        # Crear individuo directamente
        individual = algorithm._create_individual()
        
        # Verificaciones
        assert individual is not None
        assert isinstance(individual, IndividualClass)
        assert hasattr(individual, 'position')
        assert hasattr(individual, 'fitness')
        assert hasattr(individual, 'move')
    
    @pytest.mark.parametrize("algorithm_name", ALGORITHMS)
    def test_population_initialization(self, algorithm_name, test_problem):
        """Verifica la inicialización de población."""
        module = importlib.import_module(f'algorithms.{algorithm_name}_v2')
        algo_class_name, _ = ALGORITHM_CLASSES[algorithm_name]
        AlgorithmClass = getattr(module, algo_class_name)
        
        pop_size = 10
        algorithm = AlgorithmClass(
            test_problem, 
            population_size=pop_size, 
            seed=42
        )
        
        # Inicializar población
        algorithm.initialize_population()
        
        # Verificaciones
        assert len(algorithm.population) == pop_size
        assert all(ind.position is not None for ind in algorithm.population)
        assert all(ind.problem == test_problem for ind in algorithm.population)
    
    @pytest.mark.parametrize("algorithm_name", ALGORITHMS)
    def test_basic_execution(self, algorithm_name, test_problem):
        """Verifica que el algoritmo ejecute sin errores."""
        module = importlib.import_module(f'algorithms.{algorithm_name}_v2')
        algo_class_name, _ = ALGORITHM_CLASSES[algorithm_name]
        AlgorithmClass = getattr(module, algo_class_name)
        
        # Parámetros mínimos para ejecución rápida
        algorithm = AlgorithmClass(
            test_problem,
            population_size=5,
            max_iterations=2,
            seed=42
        )
        
        # Ejecutar
        try:
            best_solution = algorithm.execute()
            
            # Verificaciones básicas
            assert best_solution is not None
            assert hasattr(best_solution, 'position')
            assert hasattr(best_solution, 'fitness')
            assert len(algorithm.convergence_curve) > 0
            
        except Exception as e:
            pytest.fail(f"Algoritmo {algorithm_name} falló durante ejecución: {e}")
    
    @pytest.mark.parametrize("algorithm_name", ALGORITHMS)
    def test_reproducibility(self, algorithm_name, test_problem):
        """Verifica reproducibilidad con semilla fija."""
        module = importlib.import_module(f'algorithms.{algorithm_name}_v2')
        algo_class_name, _ = ALGORITHM_CLASSES[algorithm_name]
        AlgorithmClass = getattr(module, algo_class_name)
        
        seed = 12345
        params = {
            'population_size': 5,
            'max_iterations': 3,
            'seed': seed
        }
        
        # Ejecutar dos veces con misma semilla
        algo1 = AlgorithmClass(test_problem, **params)
        result1 = algo1.execute()
        curve1 = algo1.convergence_curve.copy()
        
        algo2 = AlgorithmClass(test_problem, **params)
        result2 = algo2.execute()
        curve2 = algo2.convergence_curve.copy()
        
        # Verificar reproducibilidad
        assert np.allclose(curve1, curve2), \
            f"Algoritmo {algorithm_name} no es reproducible con semilla fija"
        assert result1.fitness() == result2.fitness(), \
            f"Fitness final difiere para {algorithm_name} con misma semilla"
    
    @pytest.mark.parametrize("algorithm_name", ALGORITHMS)
    def test_convergence_behavior(self, algorithm_name, test_problem):
        """Verifica comportamiento básico de convergencia."""
        module = importlib.import_module(f'algorithms.{algorithm_name}_v2')
        algo_class_name, _ = ALGORITHM_CLASSES[algorithm_name]
        AlgorithmClass = getattr(module, algo_class_name)
        
        algorithm = AlgorithmClass(
            test_problem,
            population_size=10,
            max_iterations=10,
            seed=42
        )
        
        # Ejecutar
        algorithm.execute()
        
        # Verificar convergencia
        curve = algorithm.convergence_curve
        assert len(curve) == 10, f"Curva de convergencia incorrecta para {algorithm_name}"
        
        # Verificar que no empeora (puede mantenerse igual)
        for i in range(1, len(curve)):
            assert curve[i] <= curve[i-1] + 1e-6, \
                f"Convergencia empeora en iteración {i} para {algorithm_name}"
    
    @pytest.mark.parametrize("algorithm_name", ALGORITHMS)
    def test_parameter_validation(self, algorithm_name, test_problem):
        """Verifica validación de parámetros."""
        module = importlib.import_module(f'algorithms.{algorithm_name}_v2')
        algo_class_name, _ = ALGORITHM_CLASSES[algorithm_name]
        AlgorithmClass = getattr(module, algo_class_name)
        
        # Test población negativa
        with pytest.raises((ValueError, AssertionError)):
            AlgorithmClass(test_problem, population_size=-5)
        
        # Test iteraciones negativas
        with pytest.raises((ValueError, AssertionError)):
            AlgorithmClass(test_problem, max_iterations=-10)
    
    @pytest.mark.parametrize("algorithm_name", ALGORITHMS)
    def test_get_parameters(self, algorithm_name, test_problem):
        """Verifica que get_parameters retorne información correcta."""
        module = importlib.import_module(f'algorithms.{algorithm_name}_v2')
        algo_class_name, _ = ALGORITHM_CLASSES[algorithm_name]
        AlgorithmClass = getattr(module, algo_class_name)
        
        algorithm = AlgorithmClass(test_problem, population_size=20, seed=99)
        params = algorithm.get_parameters()
        
        # Verificaciones
        assert isinstance(params, dict)
        assert params['population_size'] == 20
        assert params['seed'] == 99
        assert 'max_iterations' in params


# Test adicional para verificar que no hay algoritmos faltantes
def test_algorithm_coverage():
    """Verifica que todos los algoritmos estén cubiertos."""
    algorithms_dir = Path('algorithms')
    v2_files = list(algorithms_dir.glob('*_v2.py'))
    
    # Excluir archivos base y template
    v2_algorithms = [
        f.stem.replace('_v2', '') 
        for f in v2_files 
        if not any(x in f.stem for x in ['base', 'template'])
    ]
    
    # Verificar que todos estén en nuestra lista
    missing = set(v2_algorithms) - set(ALGORITHMS)
    extra = set(ALGORITHMS) - set(v2_algorithms)
    
    assert not missing, f"Algoritmos v2 no testeados: {missing}"
    assert not extra, f"Algoritmos en tests que no existen: {extra}"