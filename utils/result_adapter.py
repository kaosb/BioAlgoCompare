"""
Adaptador para integración gradual del sistema de resultados v2.

Este módulo facilita la transición del código existente al nuevo
sistema de resultados unificado.
"""

from typing import Dict, List, Any, Optional, Union
from datetime import datetime
import warnings
from pathlib import Path

from .result_schema import StandardResult
from .result_schema_v2 import StandardResultV2, ExecutionInfoV2, ResultBuilderV2
from .experiment_tracker import ExperimentTracker, ExperimentRecord
from .results_database import ResultsDatabase


class ResultAdapter:
    """
    Adaptador principal para manejar diferentes formatos de resultados.
    
    Permite la transición gradual al nuevo sistema manteniendo
    compatibilidad con el código existente.
    """
    
    def __init__(self, use_v2: bool = True, auto_migrate: bool = True):
        """
        Inicializa el adaptador.
        
        Args:
            use_v2: Si usar el formato v2 por defecto
            auto_migrate: Si migrar automáticamente resultados v1 a v2
        """
        self.use_v2 = use_v2
        self.auto_migrate = auto_migrate
        self._tracker = None
        self._database = None
    
    @property
    def tracker(self) -> ExperimentTracker:
        """Obtiene la instancia de ExperimentTracker (lazy loading)."""
        if self._tracker is None:
            self._tracker = ExperimentTracker()
        return self._tracker
    
    @property
    def database(self) -> ResultsDatabase:
        """Obtiene la instancia de ResultsDatabase (lazy loading)."""
        if self._database is None:
            self._database = ResultsDatabase()
        return self._database
    
    def create_result(self, **kwargs) -> Union[StandardResult, StandardResultV2]:
        """
        Crea un resultado usando el formato configurado.
        
        Returns:
            StandardResult o StandardResultV2 según configuración
        """
        if self.use_v2:
            return self._create_v2_result(**kwargs)
        else:
            result = self._create_v1_result(**kwargs)
            if self.auto_migrate:
                warnings.warn(
                    "Creando resultado v1 pero auto_migrate está activo. "
                    "Considere usar directamente v2.",
                    DeprecationWarning
                )
            return result
    
    def _create_v2_result(self, **kwargs) -> StandardResultV2:
        """Crea un resultado v2."""
        # Si se proporciona algorithm y problem directamente
        if 'algorithm' in kwargs and 'problem' in kwargs:
            return ResultBuilderV2.create_from_algorithm_run(
                algorithm=kwargs['algorithm'],
                problem=kwargs['problem'],
                execution_info=kwargs.get('execution_info', ExecutionInfoV2.start_tracking(
                    seed=kwargs.get('seed', 42),
                    parallel=kwargs.get('parallel', False)
                )),
                runs_data=kwargs.get('runs_data', []),
                **kwargs
            )
        
        # Crear manualmente
        return StandardResultV2(**kwargs)
    
    def _create_v1_result(self, **kwargs) -> StandardResult:
        """Crea un resultado v1 (para compatibilidad)."""
        from .result_schema import ResultBuilder
        
        if 'runs_data' in kwargs and len(kwargs['runs_data']) == 1:
            return ResultBuilder.create_single_run(
                algorithm_name=kwargs.get('algorithm_name', 'Unknown'),
                problem_name=kwargs.get('problem_name', 'Unknown'),
                run_result=kwargs['runs_data'][0].get('best_solution'),
                execution_time=kwargs['runs_data'][0].get('execution_time', 0),
                **kwargs
            )
        else:
            return ResultBuilder.create_multi_run(
                algorithm_name=kwargs.get('algorithm_name', 'Unknown'),
                problem_name=kwargs.get('problem_name', 'Unknown'),
                run_results=kwargs.get('runs_data', []),
                **kwargs
            )
    
    def save_result(self, result: Union[StandardResult, StandardResultV2], 
                   path: Optional[Path] = None,
                   save_to_db: bool = True,
                   save_to_tracker: bool = True) -> Dict[str, Any]:
        """
        Guarda un resultado en múltiples formatos/ubicaciones.
        
        Args:
            result: Resultado a guardar
            path: Ruta para guardar JSON (opcional)
            save_to_db: Si guardar en base de datos
            save_to_tracker: Si guardar en experiment tracker
            
        Returns:
            Dict con rutas/IDs de donde se guardó
        """
        saved_locations = {}
        
        # Migrar a v2 si es necesario
        if isinstance(result, StandardResult) and self.auto_migrate:
            from .result_schema_v2 import migrate_v1_to_v2
            result = migrate_v1_to_v2(result)
            warnings.warn("Resultado v1 migrado automáticamente a v2", DeprecationWarning)
        
        # Guardar como JSON
        if path:
            json_path = Path(path)
            json_path.parent.mkdir(parents=True, exist_ok=True)
            result.to_json(json_path)
            saved_locations['json_path'] = str(json_path)
        
        # Guardar en base de datos
        if save_to_db and isinstance(result, StandardResultV2):
            try:
                # Convertir a formato de base de datos
                db_id = self.database.save_experiment(
                    algorithm_name=result.algorithm_info.name,
                    problem_name=result.problem_info.name,
                    parameters=result.algorithm_info.parameters,
                    results={
                        'best_fitness': result.statistics.best_fitness,
                        'mean_fitness': result.statistics.mean_fitness,
                        'std_fitness': result.statistics.std_fitness
                    },
                    metadata={
                        'result_id': result.result_id,
                        'version': result.version,
                        'git_info': result.git_info.to_dict() if result.git_info else None,
                        'system_info': result.system_info.to_dict() if result.system_info else None
                    }
                )
                saved_locations['database_id'] = db_id
            except Exception as e:
                warnings.warn(f"Error guardando en base de datos: {e}")
        
        # Guardar en experiment tracker
        if save_to_tracker and isinstance(result, StandardResultV2):
            try:
                # Crear registro de experimento
                experiment_id = self.tracker.start_experiment(
                    name=f"{result.algorithm_info.name}_{result.problem_info.name}",
                    description=f"Run with {result.statistics.n_runs} repetitions",
                    tags=['auto_saved', f'v{result.version}']
                )
                
                # Registrar configuración
                self.tracker.log_config({
                    'algorithm': result.algorithm_info.to_dict(),
                    'problem': result.problem_info.to_dict()
                })
                
                # Registrar resultados
                for run in result.runs:
                    self.tracker.log_metrics({
                        'best_fitness': run.best_fitness,
                        'execution_time': run.execution_time,
                        'iterations': run.iterations_completed
                    })
                
                self.tracker.end_experiment(
                    best_result=result.statistics.best_fitness,
                    final_metrics={
                        'mean_fitness': result.statistics.mean_fitness,
                        'std_fitness': result.statistics.std_fitness
                    }
                )
                
                saved_locations['tracker_id'] = experiment_id
            except Exception as e:
                warnings.warn(f"Error guardando en experiment tracker: {e}")
        
        return saved_locations
    
    def load_result(self, source: Union[str, Path, Dict], 
                   format: str = 'auto') -> StandardResultV2:
        """
        Carga un resultado desde diferentes fuentes.
        
        Args:
            source: Ruta de archivo, dict o ID
            format: Formato ('auto', 'v1', 'v2', 'tracker', 'database')
            
        Returns:
            StandardResultV2 (migrando si es necesario)
        """
        if format == 'auto':
            format = self._detect_format(source)
        
        if format == 'v2':
            if isinstance(source, dict):
                return StandardResultV2.from_dict(source)
            else:
                return StandardResultV2.from_json(source)
        
        elif format == 'v1':
            if isinstance(source, dict):
                v1_result = StandardResult.from_dict(source)
            else:
                v1_result = StandardResult.from_json(source)
            
            if self.auto_migrate:
                from .result_schema_v2 import migrate_v1_to_v2
                return migrate_v1_to_v2(v1_result)
            else:
                warnings.warn(
                    "Cargando resultado v1. Considere migrar a v2.",
                    DeprecationWarning
                )
                return v1_result
        
        elif format == 'tracker':
            # Cargar desde ExperimentTracker
            record = self.tracker.get_experiment(str(source))
            return self._convert_tracker_to_v2(record)
        
        elif format == 'database':
            # Cargar desde ResultsDatabase
            data = self.database.get_experiment(str(source))
            return self._convert_database_to_v2(data)
        
        else:
            raise ValueError(f"Formato no soportado: {format}")
    
    def _detect_format(self, source: Any) -> str:
        """Detecta el formato de la fuente."""
        if isinstance(source, dict):
            if 'version' in source and source['version'].startswith('2.'):
                return 'v2'
            elif 'result_id' in source and 'runs' in source:
                return 'v1'
            elif 'experiment_id' in source and 'config' in source:
                return 'tracker'
            else:
                return 'database'
        
        elif isinstance(source, (str, Path)):
            # Intentar cargar y detectar
            import json
            try:
                data = json.loads(Path(source).read_text())
                return self._detect_format(data)
            except:
                # Asumir que es un ID
                if source.startswith('exp_'):
                    return 'tracker'
                else:
                    return 'database'
        
        return 'v2'  # Por defecto
    
    def _convert_tracker_to_v2(self, record: ExperimentRecord) -> StandardResultV2:
        """Convierte un ExperimentRecord a StandardResultV2."""
        # Extraer información
        algorithm_info = AlgorithmInfo(
            name=record.config.get('algorithm_name', 'Unknown'),
            parameters=record.config.get('parameters', {})
        )
        
        problem_info = ProblemInfo(
            name=record.config.get('problem_name', 'Unknown')
        )
        
        # Crear runs desde resultados
        runs = []
        for i, result in enumerate(record.results):
            runs.append(SingleRunResult(
                run_id=i,
                seed=result.config.get('seed', 42),
                best_fitness=result.metrics.get('best_fitness', float('inf')),
                best_solution=None,
                convergence_curve=[],
                execution_time=result.duration_seconds,
                iterations_completed=result.metrics.get('iterations', 0),
                evaluations=result.metrics.get('evaluations', 0)
            ))
        
        # Crear resultado v2
        return StandardResultV2(
            result_id=record.experiment_id,
            result_type=ResultType.MULTI_RUN,
            timestamp=record.start_time,
            problem_info=problem_info,
            algorithm_info=algorithm_info,
            runs=runs,
            statistics=MultiRunStatistics.from_runs(runs),
            metadata={'source': 'experiment_tracker', 'original_id': record.experiment_id}
        )
    
    def _convert_database_to_v2(self, data: Dict[str, Any]) -> StandardResultV2:
        """Convierte datos de ResultsDatabase a StandardResultV2."""
        # Similar a _convert_tracker_to_v2 pero para formato de base de datos
        # Implementación simplificada
        warnings.warn(
            "Conversión desde base de datos puede perder información",
            UserWarning
        )
        
        # Crear estructura mínima
        algorithm_info = AlgorithmInfo(
            name=data.get('algorithm', 'Unknown'),
            parameters=data.get('parameters', {})
        )
        
        problem_info = ProblemInfo(
            name=data.get('problem', 'Unknown')
        )
        
        # Un solo run con información agregada
        run = SingleRunResult(
            run_id=0,
            seed=42,
            best_fitness=data.get('best_fitness', float('inf')),
            best_solution=None,
            convergence_curve=[],
            execution_time=data.get('execution_time', 0),
            iterations_completed=data.get('iterations', 0),
            evaluations=0
        )
        
        return StandardResultV2(
            result_id=str(data.get('id', 'unknown')),
            result_type=ResultType.SINGLE_RUN,
            timestamp=datetime.fromisoformat(data.get('timestamp', datetime.now().isoformat())),
            problem_info=problem_info,
            algorithm_info=algorithm_info,
            runs=[run],
            statistics=MultiRunStatistics.from_runs([run]),
            metadata={'source': 'results_database', 'original_data': data}
        )
    
    def batch_migrate(self, input_dir: Path, output_dir: Path,
                     input_format: str = 'v1') -> Dict[str, Any]:
        """
        Migra múltiples archivos de resultados a v2.
        
        Args:
            input_dir: Directorio con archivos de entrada
            output_dir: Directorio para archivos migrados
            input_format: Formato de entrada ('v1', 'tracker', 'database')
            
        Returns:
            Estadísticas de la migración
        """
        input_path = Path(input_dir)
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        stats = {
            'total': 0,
            'success': 0,
            'failed': 0,
            'errors': []
        }
        
        # Buscar archivos JSON
        for file_path in input_path.glob('**/*.json'):
            stats['total'] += 1
            
            try:
                # Cargar y migrar
                result = self.load_result(file_path, format=input_format)
                
                # Guardar en formato v2
                output_file = output_path / file_path.relative_to(input_path)
                output_file.parent.mkdir(parents=True, exist_ok=True)
                result.to_json(output_file)
                
                stats['success'] += 1
                
            except Exception as e:
                stats['failed'] += 1
                stats['errors'].append({
                    'file': str(file_path),
                    'error': str(e)
                })
        
        return stats


# Singleton global para facilitar el uso
_global_adapter = None


def get_result_adapter(use_v2: bool = True, 
                      auto_migrate: bool = True) -> ResultAdapter:
    """
    Obtiene la instancia global del adaptador.
    
    Args:
        use_v2: Si usar formato v2 por defecto
        auto_migrate: Si migrar automáticamente v1 a v2
        
    Returns:
        Instancia de ResultAdapter
    """
    global _global_adapter
    
    if _global_adapter is None:
        _global_adapter = ResultAdapter(use_v2=use_v2, auto_migrate=auto_migrate)
    
    return _global_adapter


# Funciones de conveniencia
def create_result(**kwargs) -> StandardResultV2:
    """Crea un resultado usando el adaptador global."""
    return get_result_adapter().create_result(**kwargs)


def save_result(result: Union[StandardResult, StandardResultV2], 
               path: Optional[Path] = None,
               **kwargs) -> Dict[str, Any]:
    """Guarda un resultado usando el adaptador global."""
    return get_result_adapter().save_result(result, path, **kwargs)


def load_result(source: Union[str, Path, Dict], 
               format: str = 'auto') -> StandardResultV2:
    """Carga un resultado usando el adaptador global."""
    return get_result_adapter().load_result(source, format)