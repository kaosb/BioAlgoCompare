"""
Sistema unificado de gestión de reproducibilidad para BioAlgoCompare.

Este módulo garantiza la reproducibilidad total de todos los experimentos
mediante control estricto de semillas aleatorias, estados y entornos.
"""

import numpy as np
import random
import hashlib
import json
import os
import sys
import platform
import logging
from typing import Dict, Any, Optional, List, Tuple, Union
from datetime import datetime
from pathlib import Path
import pickle
from contextlib import contextmanager
import warnings

logger = logging.getLogger(__name__)


class ReproducibilityError(Exception):
    """Error específico de reproducibilidad."""
    pass


class RandomStateManager:
    """
    Gestor centralizado de estados aleatorios.
    
    Garantiza que todos los componentes del sistema usen semillas
    consistentes y rastreables para reproducibilidad total.
    """
    
    def __init__(self, base_seed: Optional[int] = None):
        """
        Inicializa el gestor de estados aleatorios.
        
        Args:
            base_seed: Semilla base para derivar todas las demás
        """
        self.base_seed = base_seed if base_seed is not None else self._generate_seed()
        self.seed_registry = {}
        self.state_snapshots = {}
        self.call_counter = 0
        
        # Inicializar generadores
        self._init_random_generators()
        
        logger.info(f"RandomStateManager initialized with base seed: {self.base_seed}")
    
    def _generate_seed(self) -> int:
        """Genera una semilla aleatoria válida."""
        return random.randint(0, 2**32 - 1)
    
    def _init_random_generators(self):
        """Inicializa todos los generadores aleatorios."""
        # Python random
        random.seed(self.base_seed)
        
        # NumPy random
        np.random.seed(self.base_seed)
        
        # Crear generador principal de NumPy
        self.np_generator = np.random.RandomState(self.base_seed)
        
        # Registrar semilla base
        self.seed_registry['base'] = self.base_seed
        self.seed_registry['python_random'] = self.base_seed
        self.seed_registry['numpy_global'] = self.base_seed
    
    def get_seed(self, component: str) -> int:
        """
        Obtiene una semilla determinística para un componente.
        
        Args:
            component: Nombre del componente (e.g., 'algorithm_hoa', 'problem_vrp')
            
        Returns:
            Semilla determinística única para el componente
        """
        if component in self.seed_registry:
            return self.seed_registry[component]
        
        # Generar semilla derivada usando hash
        hash_input = f"{self.base_seed}:{component}".encode()
        hash_value = hashlib.sha256(hash_input).hexdigest()
        derived_seed = int(hash_value[:8], 16)  # Usar primeros 8 caracteres hex
        
        self.seed_registry[component] = derived_seed
        logger.debug(f"Generated seed for '{component}': {derived_seed}")
        
        return derived_seed
    
    def get_random_state(self, component: Optional[str] = None) -> np.random.RandomState:
        """
        Obtiene un RandomState para un componente.
        
        Args:
            component: Nombre del componente (opcional)
            
        Returns:
            RandomState inicializado con semilla apropiada
        """
        if component is None:
            component = f"anonymous_{self.call_counter}"
            self.call_counter += 1
        
        seed = self.get_seed(component)
        return np.random.RandomState(seed)
    
    def set_global_seed(self, seed: Optional[int] = None):
        """
        Establece la semilla global para todos los generadores.
        
        Args:
            seed: Nueva semilla (usa base_seed si None)
        """
        if seed is None:
            seed = self.base_seed
        
        random.seed(seed)
        np.random.seed(seed)
        
        # Actualizar registro
        self.seed_registry['python_random'] = seed
        self.seed_registry['numpy_global'] = seed
        
        logger.debug(f"Global seed set to: {seed}")
    
    def save_state(self, name: str):
        """
        Guarda el estado actual de todos los generadores.
        
        Args:
            name: Nombre para identificar el snapshot
        """
        state = {
            'python_random': random.getstate(),
            'numpy_global': np.random.get_state(),
            'np_generator': self.np_generator.get_state(),
            'seed_registry': self.seed_registry.copy(),
            'timestamp': datetime.now().isoformat()
        }
        
        self.state_snapshots[name] = state
        logger.debug(f"Saved random state snapshot: '{name}'")
    
    def restore_state(self, name: str):
        """
        Restaura un estado guardado previamente.
        
        Args:
            name: Nombre del snapshot a restaurar
        """
        if name not in self.state_snapshots:
            raise ReproducibilityError(f"State snapshot '{name}' not found")
        
        state = self.state_snapshots[name]
        
        random.setstate(state['python_random'])
        np.random.set_state(state['numpy_global'])
        self.np_generator.set_state(state['np_generator'])
        self.seed_registry = state['seed_registry'].copy()
        
        logger.debug(f"Restored random state snapshot: '{name}'")
    
    def get_state_info(self) -> Dict[str, Any]:
        """Obtiene información del estado actual."""
        return {
            'base_seed': self.base_seed,
            'seed_registry': self.seed_registry.copy(),
            'snapshots': list(self.state_snapshots.keys()),
            'call_counter': self.call_counter
        }


class EnvironmentManager:
    """
    Gestor del entorno de ejecución para reproducibilidad.
    
    Captura y valida el entorno de ejecución para asegurar
    que los experimentos se ejecuten en condiciones consistentes.
    """
    
    def __init__(self):
        """Inicializa el gestor de entorno."""
        self.environment_info = self._capture_environment()
        self.warnings = []
    
    def _capture_environment(self) -> Dict[str, Any]:
        """Captura información completa del entorno."""
        import importlib.metadata
        
        env_info = {
            'timestamp': datetime.now().isoformat(),
            'platform': {
                'system': platform.system(),
                'release': platform.release(),
                'version': platform.version(),
                'machine': platform.machine(),
                'processor': platform.processor(),
                'python_version': platform.python_version(),
                'python_implementation': platform.python_implementation()
            },
            'packages': {},
            'environment_variables': {},
            'numpy_config': {},
            'paths': {
                'working_directory': os.getcwd(),
                'python_executable': sys.executable,
                'python_path': sys.path.copy()
            }
        }
        
        # Capturar versiones de paquetes clave
        key_packages = [
            'numpy', 'scipy', 'pandas', 'matplotlib', 
            'seaborn', 'networkx', 'scikit-learn'
        ]
        
        for package in key_packages:
            try:
                version = importlib.metadata.version(package)
                env_info['packages'][package] = version
            except importlib.metadata.PackageNotFoundError:
                env_info['packages'][package] = 'Not installed'
        
        # Capturar variables de entorno relevantes
        relevant_env_vars = [
            'PYTHONHASHSEED', 'OMP_NUM_THREADS', 'MKL_NUM_THREADS',
            'NUMEXPR_NUM_THREADS', 'OPENBLAS_NUM_THREADS'
        ]
        
        for var in relevant_env_vars:
            env_info['environment_variables'][var] = os.environ.get(var, 'Not set')
        
        # Configuración de NumPy
        try:
            import numpy as np
            env_info['numpy_config'] = {
                'version': np.__version__,
                'mkl_version': getattr(np, '__mkl_version__', 'Not available'),
                'blas_info': np.__config__.blas_info() if hasattr(np.__config__, 'blas_info') else {},
                'lapack_info': np.__config__.lapack_info() if hasattr(np.__config__, 'lapack_info') else {}
            }
        except Exception as e:
            env_info['numpy_config']['error'] = str(e)
        
        return env_info
    
    def validate_environment(self, reference_env: Optional[Dict[str, Any]] = None) -> List[str]:
        """
        Valida el entorno actual contra uno de referencia.
        
        Args:
            reference_env: Entorno de referencia para comparar
            
        Returns:
            Lista de advertencias sobre diferencias encontradas
        """
        warnings = []
        
        if reference_env is None:
            # Validaciones básicas sin referencia
            if self.environment_info['environment_variables'].get('PYTHONHASHSEED') == 'Not set':
                warnings.append("PYTHONHASHSEED not set - dictionary ordering may vary")
            
            return warnings
        
        # Comparar con referencia
        current = self.environment_info
        
        # Comparar versiones de Python
        if current['platform']['python_version'] != reference_env['platform']['python_version']:
            warnings.append(
                f"Python version mismatch: {current['platform']['python_version']} "
                f"vs {reference_env['platform']['python_version']}"
            )
        
        # Comparar paquetes
        for package, version in reference_env['packages'].items():
            current_version = current['packages'].get(package, 'Not installed')
            if current_version != version:
                warnings.append(f"Package {package}: {current_version} vs {version}")
        
        # Comparar variables de entorno críticas
        critical_env_vars = ['PYTHONHASHSEED', 'OMP_NUM_THREADS']
        for var in critical_env_vars:
            if current['environment_variables'].get(var) != reference_env['environment_variables'].get(var):
                warnings.append(
                    f"Environment variable {var}: "
                    f"{current['environment_variables'].get(var)} vs "
                    f"{reference_env['environment_variables'].get(var)}"
                )
        
        return warnings
    
    def set_reproducible_environment(self):
        """Configura el entorno para máxima reproducibilidad."""
        # Establecer PYTHONHASHSEED
        if 'PYTHONHASHSEED' not in os.environ:
            os.environ['PYTHONHASHSEED'] = '0'
            logger.info("Set PYTHONHASHSEED=0 for reproducibility")
        
        # Limitar threads para operaciones paralelas
        thread_vars = [
            'OMP_NUM_THREADS', 'MKL_NUM_THREADS', 
            'NUMEXPR_NUM_THREADS', 'OPENBLAS_NUM_THREADS'
        ]
        
        for var in thread_vars:
            if var not in os.environ:
                os.environ[var] = '1'
                logger.info(f"Set {var}=1 for reproducibility")
        
        # Deshabilitar operaciones no determinísticas en bibliotecas
        try:
            import torch
            torch.use_deterministic_algorithms(True)
            torch.backends.cudnn.deterministic = True
            torch.backends.cudnn.benchmark = False
            logger.info("Set PyTorch to deterministic mode")
        except ImportError:
            pass
        
        # Configurar NumPy
        np.seterr(all='raise')  # Raise errors instead of warnings
        
        # Suprimir advertencias no determinísticas
        warnings.filterwarnings('ignore', category=RuntimeWarning)


class ReproducibilityManager:
    """
    Gestor principal de reproducibilidad.
    
    Coordina todos los aspectos de reproducibilidad incluyendo
    semillas aleatorias, entorno y metadatos.
    """
    
    def __init__(self, 
                 base_seed: Optional[int] = None,
                 enforce_determinism: bool = True,
                 capture_environment: bool = True):
        """
        Inicializa el gestor de reproducibilidad.
        
        Args:
            base_seed: Semilla base para todos los experimentos
            enforce_determinism: Si forzar configuración determinística
            capture_environment: Si capturar información del entorno
        """
        self.base_seed = base_seed if base_seed is not None else 42
        self.enforce_determinism = enforce_determinism
        
        # Inicializar componentes
        self.random_state_manager = RandomStateManager(self.base_seed)
        self.environment_manager = EnvironmentManager() if capture_environment else None
        
        # Configurar entorno si se solicita
        if enforce_determinism and self.environment_manager:
            self.environment_manager.set_reproducible_environment()
        
        # Registro de experimentos
        self.experiment_registry = {}
        
        logger.info(f"ReproducibilityManager initialized with base seed: {self.base_seed}")
    
    def create_experiment(self, 
                         experiment_id: str,
                         algorithm: str,
                         problem: str,
                         parameters: Dict[str, Any]) -> 'ExperimentContext':
        """
        Crea un contexto de experimento reproducible.
        
        Args:
            experiment_id: Identificador único del experimento
            algorithm: Nombre del algoritmo
            problem: Nombre del problema
            parameters: Parámetros del experimento
            
        Returns:
            Contexto de experimento configurado
        """
        # Generar semillas determinísticas
        algorithm_seed = self.random_state_manager.get_seed(f"algorithm_{algorithm}_{experiment_id}")
        problem_seed = self.random_state_manager.get_seed(f"problem_{problem}_{experiment_id}")
        
        # Crear contexto
        context = ExperimentContext(
            experiment_id=experiment_id,
            algorithm=algorithm,
            problem=problem,
            parameters=parameters,
            algorithm_seed=algorithm_seed,
            problem_seed=problem_seed,
            manager=self
        )
        
        # Registrar experimento
        self.experiment_registry[experiment_id] = {
            'context': context,
            'created_at': datetime.now().isoformat(),
            'status': 'created'
        }
        
        logger.info(f"Created experiment '{experiment_id}' with algorithm seed {algorithm_seed}")
        
        return context
    
    def get_reproducibility_info(self) -> Dict[str, Any]:
        """Obtiene información completa de reproducibilidad."""
        info = {
            'base_seed': self.base_seed,
            'enforce_determinism': self.enforce_determinism,
            'random_state': self.random_state_manager.get_state_info(),
            'experiments': {
                exp_id: {
                    'created_at': exp_info['created_at'],
                    'status': exp_info['status'],
                    'algorithm': exp_info['context'].algorithm,
                    'problem': exp_info['context'].problem
                }
                for exp_id, exp_info in self.experiment_registry.items()
            }
        }
        
        if self.environment_manager:
            info['environment'] = self.environment_manager.environment_info
        
        return info
    
    def save_reproducibility_info(self, filepath: Union[str, Path]):
        """
        Guarda información de reproducibilidad a archivo.
        
        Args:
            filepath: Ruta del archivo
        """
        info = self.get_reproducibility_info()
        
        filepath = Path(filepath)
        filepath.parent.mkdir(parents=True, exist_ok=True)
        
        with open(filepath, 'w') as f:
            json.dump(info, f, indent=2, default=str)
        
        logger.info(f"Saved reproducibility info to {filepath}")
    
    @classmethod
    def load_from_file(cls, filepath: Union[str, Path]) -> 'ReproducibilityManager':
        """
        Carga configuración de reproducibilidad desde archivo.
        
        Args:
            filepath: Ruta del archivo
            
        Returns:
            ReproducibilityManager configurado
        """
        with open(filepath) as f:
            info = json.load(f)
        
        manager = cls(
            base_seed=info['base_seed'],
            enforce_determinism=info['enforce_determinism']
        )
        
        # Restaurar estado de semillas
        for component, seed in info['random_state']['seed_registry'].items():
            if component not in ['base', 'python_random', 'numpy_global']:
                manager.random_state_manager.seed_registry[component] = seed
        
        logger.info(f"Loaded reproducibility config from {filepath}")
        
        return manager


class ExperimentContext:
    """
    Contexto de ejecución para un experimento reproducible.
    
    Encapsula toda la configuración necesaria para ejecutar
    un experimento de forma completamente reproducible.
    """
    
    def __init__(self,
                 experiment_id: str,
                 algorithm: str,
                 problem: str,
                 parameters: Dict[str, Any],
                 algorithm_seed: int,
                 problem_seed: int,
                 manager: ReproducibilityManager):
        """
        Inicializa el contexto del experimento.
        
        Args:
            experiment_id: ID único del experimento
            algorithm: Nombre del algoritmo
            problem: Nombre del problema
            parameters: Parámetros del experimento
            algorithm_seed: Semilla para el algoritmo
            problem_seed: Semilla para el problema
            manager: Gestor de reproducibilidad
        """
        self.experiment_id = experiment_id
        self.algorithm = algorithm
        self.problem = problem
        self.parameters = parameters
        self.algorithm_seed = algorithm_seed
        self.problem_seed = problem_seed
        self.manager = manager
        
        # Estados aleatorios
        self.algorithm_random_state = np.random.RandomState(algorithm_seed)
        self.problem_random_state = np.random.RandomState(problem_seed)
        
        # Metadatos
        self.metadata = {
            'experiment_id': experiment_id,
            'algorithm': algorithm,
            'problem': problem,
            'algorithm_seed': algorithm_seed,
            'problem_seed': problem_seed,
            'parameters': parameters,
            'created_at': datetime.now().isoformat()
        }
    
    @contextmanager
    def algorithm_context(self):
        """
        Context manager para ejecución del algoritmo.
        
        Configura el entorno aleatorio para el algoritmo y lo
        restaura al salir.
        """
        # Guardar estado actual
        self.manager.random_state_manager.save_state(f"{self.experiment_id}_algo_before")
        
        # Establecer semilla del algoritmo
        self.manager.random_state_manager.set_global_seed(self.algorithm_seed)
        
        try:
            yield self.algorithm_random_state
        finally:
            # Restaurar estado (opcional, depende del caso de uso)
            pass
    
    @contextmanager
    def problem_context(self):
        """
        Context manager para operaciones del problema.
        
        Configura el entorno aleatorio para el problema y lo
        restaura al salir.
        """
        # Guardar estado actual
        self.manager.random_state_manager.save_state(f"{self.experiment_id}_prob_before")
        
        # Establecer semilla del problema
        self.manager.random_state_manager.set_global_seed(self.problem_seed)
        
        try:
            yield self.problem_random_state
        finally:
            # Restaurar estado (opcional)
            pass
    
    def get_algorithm_config(self) -> Dict[str, Any]:
        """Obtiene configuración completa para el algoritmo."""
        return {
            'seed': self.algorithm_seed,
            'random_state': self.algorithm_random_state,
            **self.parameters
        }
    
    def get_problem_config(self) -> Dict[str, Any]:
        """Obtiene configuración completa para el problema."""
        return {
            'seed': self.problem_seed,
            'random_state': self.problem_random_state
        }
    
    def save_checkpoint(self, filepath: Union[str, Path], data: Any):
        """
        Guarda un checkpoint del experimento.
        
        Args:
            filepath: Ruta del archivo
            data: Datos a guardar
        """
        checkpoint = {
            'metadata': self.metadata,
            'timestamp': datetime.now().isoformat(),
            'random_states': {
                'algorithm': self.algorithm_random_state.get_state(),
                'problem': self.problem_random_state.get_state()
            },
            'data': data
        }
        
        filepath = Path(filepath)
        filepath.parent.mkdir(parents=True, exist_ok=True)
        
        with open(filepath, 'wb') as f:
            pickle.dump(checkpoint, f)
        
        logger.info(f"Saved checkpoint for experiment '{self.experiment_id}' to {filepath}")
    
    def load_checkpoint(self, filepath: Union[str, Path]) -> Any:
        """
        Carga un checkpoint del experimento.
        
        Args:
            filepath: Ruta del archivo
            
        Returns:
            Datos del checkpoint
        """
        with open(filepath, 'rb') as f:
            checkpoint = pickle.load(f)
        
        # Restaurar estados aleatorios
        self.algorithm_random_state.set_state(checkpoint['random_states']['algorithm'])
        self.problem_random_state.set_state(checkpoint['random_states']['problem'])
        
        logger.info(f"Loaded checkpoint for experiment '{self.experiment_id}' from {filepath}")
        
        return checkpoint['data']


# Instancia global para uso conveniente
_global_manager = None


def get_global_manager() -> ReproducibilityManager:
    """Obtiene el gestor global de reproducibilidad."""
    global _global_manager
    if _global_manager is None:
        _global_manager = ReproducibilityManager()
    return _global_manager


def set_global_seed(seed: int):
    """
    Establece la semilla global para reproducibilidad.
    
    Args:
        seed: Semilla a establecer
    """
    manager = get_global_manager()
    manager.random_state_manager.set_global_seed(seed)
    
    # También actualizar semilla base
    manager.base_seed = seed
    manager.random_state_manager.base_seed = seed


def create_reproducible_experiment(
    experiment_id: str,
    algorithm: str,
    problem: str,
    parameters: Dict[str, Any],
    base_seed: Optional[int] = None
) -> ExperimentContext:
    """
    Crea un experimento reproducible.
    
    Args:
        experiment_id: ID único del experimento
        algorithm: Nombre del algoritmo
        problem: Nombre del problema
        parameters: Parámetros del experimento
        base_seed: Semilla base (opcional)
        
    Returns:
        Contexto del experimento
    """
    if base_seed is not None:
        set_global_seed(base_seed)
    
    manager = get_global_manager()
    return manager.create_experiment(experiment_id, algorithm, problem, parameters)