"""
Integración entre el esquema estandarizado de resultados y el sistema de tracking.

Este módulo facilita la conversión bidireccional entre el esquema estandarizado
(StandardResult) y el sistema de tracking (ExperimentRecord), permitiendo
una transición suave y manteniendo compatibilidad hacia atrás.
"""

from typing import Dict, Any, List, Optional, Union
from datetime import datetime
from pathlib import Path
import json

from utils.result_schema import (
    StandardResult, SingleRunResult, MultiRunStatistics, 
    ProblemInfo, AlgorithmInfo, ExecutionInfo,
    ResultType, ResultBuilder
)
from utils.experiment_tracker import (
    ExperimentRecord, ExperimentConfig, ExperimentResult,
    SystemInfo, GitInfo
)
from dataclasses import asdict


class ResultIntegration:
    """Integra el esquema estandarizado con el sistema de tracking."""
    
    @staticmethod
    def experiment_to_standard(record: ExperimentRecord) -> StandardResult:
        """
        Convierte un ExperimentRecord al formato StandardResult.
        
        Args:
            record: Registro de experimento del sistema de tracking
            
        Returns:
            StandardResult con todos los datos convertidos
        """
        # Información del problema
        problem_info = ProblemInfo(
            name=record.config.problem_instance.replace('.vrp', ''),
            type="VRP",
            instance_file=f"data/vrp/{record.config.problem_instance}",
            metadata=record.metadata.get('problem_metadata', {})
        )
        
        # Información del algoritmo
        algorithm_info = AlgorithmInfo(
            name=record.config.algorithm,
            version="v2",  # Asumimos v2 por defecto
            population_size=record.config.population_size,
            max_iterations=record.config.max_iterations,
            parameters=record.config.algorithm_params,
            seed=record.config.seed
        )
        
        # Información de ejecución
        start_time = datetime.fromisoformat(record.timestamp)
        total_time = sum(r.execution_time for r in record.results)
        end_time = datetime.fromtimestamp(start_time.timestamp() + total_time)
        
        execution_info = ExecutionInfo(
            start_time=start_time,
            end_time=end_time,
            duration_seconds=total_time,
            platform=record.system_info.platform,
            python_version=record.system_info.python_version,
            cpu_count=record.system_info.cpu_count,
            memory_gb=record.system_info.total_memory_gb,
            parallel=record.metadata.get('parallel', False),
            n_workers=record.metadata.get('n_workers')
        )
        
        # Convertir runs individuales
        runs = []
        for result in record.results:
            run = SingleRunResult(
                run_id=result.run_id,
                seed=result.seed,
                best_fitness=result.best_fitness,
                best_solution=result.final_solution,
                convergence_curve=result.convergence_curve or [],
                execution_time=result.execution_time,
                iterations_completed=result.iterations_completed,
                evaluations=result.metadata.get('evaluations', 0),
                custom_metrics=result.metadata
            )
            runs.append(run)
        
        # Calcular estadísticas
        statistics = MultiRunStatistics.from_runs(
            runs, 
            success_threshold=record.metadata.get('success_threshold')
        )
        
        # Crear resultado estándar
        return StandardResult(
            result_id=record.experiment_id,
            result_type=ResultType.MULTI_RUN if len(runs) > 1 else ResultType.SINGLE_RUN,
            timestamp=start_time,
            problem_info=problem_info,
            algorithm_info=algorithm_info,
            execution_info=execution_info,
            runs=runs,
            statistics=statistics,
            metadata={
                'original_metadata': record.metadata,
                'git_info': asdict(record.git_info) if record.git_info else None,
                'system_info': asdict(record.system_info)
            }
        )
    
    @staticmethod
    def standard_to_experiment(result: StandardResult) -> ExperimentRecord:
        """
        Convierte un StandardResult al formato ExperimentRecord.
        
        Args:
            result: Resultado en formato estándar
            
        Returns:
            ExperimentRecord compatible con el sistema de tracking
        """
        # Configuración del experimento
        config = ExperimentConfig(
            algorithm=result.algorithm_info.name,
            problem_instance=f"{result.problem_info.name}.vrp",
            population_size=result.algorithm_info.population_size,
            max_iterations=result.algorithm_info.max_iterations,
            algorithm_params=result.algorithm_info.parameters,
            seed=result.algorithm_info.seed
        )
        
        # Información del sistema
        system_info_data = result.metadata.get('system_info', {})
        system_info = SystemInfo(
            platform=system_info_data.get('platform', result.execution_info.platform),
            platform_version=system_info_data.get('platform_version', 'unknown'),
            python_version=system_info_data.get('python_version', result.execution_info.python_version),
            cpu_count=system_info_data.get('cpu_count', result.execution_info.cpu_count),
            cpu_model=system_info_data.get('cpu_model', 'unknown'),
            total_memory_gb=system_info_data.get('total_memory_gb', result.execution_info.memory_gb),
            hostname=system_info_data.get('hostname', 'unknown')
        )
        
        # Información de Git
        git_info = None
        git_info_data = result.metadata.get('git_info')
        if git_info_data:
            git_info = GitInfo(**git_info_data)
        
        # Convertir runs a ExperimentResult
        results = []
        for run in result.runs:
            exp_result = ExperimentResult(
                run_id=run.run_id,
                seed=run.seed,
                best_fitness=run.best_fitness,
                convergence_curve=run.convergence_curve,
                execution_time=run.execution_time,
                final_solution=run.best_solution,
                iterations_completed=run.iterations_completed,
                metadata=run.custom_metrics or {}
            )
            results.append(exp_result)
        
        # Estadísticas resumen
        summary_stats = {
            'n_runs': result.statistics.n_runs,
            'best_fitness': result.statistics.best_fitness,
            'worst_fitness': result.statistics.worst_fitness,
            'mean_fitness': result.statistics.mean_fitness,
            'std_fitness': result.statistics.std_fitness,
            'median_fitness': result.statistics.median_fitness,
            'mean_execution_time': result.statistics.mean_execution_time,
            'total_execution_time': result.statistics.total_execution_time
        }
        
        # Crear ExperimentRecord
        return ExperimentRecord(
            experiment_id=result.result_id,
            timestamp=result.timestamp.isoformat(),
            config=config,
            system_info=system_info,
            git_info=git_info,
            results=results,
            summary_stats=summary_stats,
            metadata=result.metadata.get('original_metadata', {})
        )
    
    @staticmethod
    def migrate_legacy_results(
        legacy_path: Union[str, Path],
        output_dir: Union[str, Path]
    ) -> List[str]:
        """
        Migra resultados legacy al nuevo esquema estandarizado.
        
        Args:
            legacy_path: Ruta a archivos legacy (JSON/CSV)
            output_dir: Directorio de salida para resultados migrados
            
        Returns:
            Lista de IDs de resultados migrados
        """
        legacy_path = Path(legacy_path)
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        
        migrated_ids = []
        
        # Procesar archivos JSON de experimentos
        if legacy_path.is_file() and legacy_path.suffix == '.json':
            files = [legacy_path]
        else:
            files = list(legacy_path.glob('*.json'))
        
        for file in files:
            try:
                # Cargar datos legacy
                with open(file, 'r') as f:
                    data = json.load(f)
                
                # Determinar tipo de datos
                if 'experiment_id' in data and 'config' in data:
                    # Es un ExperimentRecord
                    record = ExperimentRecord(**data)
                    standard_result = ResultIntegration.experiment_to_standard(record)
                    
                    # Guardar resultado migrado
                    output_file = output_dir / f"{standard_result.result_id}_migrated.json"
                    standard_result.to_json(output_file)
                    migrated_ids.append(standard_result.result_id)
                    
                elif 'algorithm' in data and 'instance' in data:
                    # Es un formato legacy simple
                    standard_result = ResultIntegration._migrate_simple_format(data)
                    
                    # Guardar resultado migrado
                    output_file = output_dir / f"{standard_result.result_id}_migrated.json"
                    standard_result.to_json(output_file)
                    migrated_ids.append(standard_result.result_id)
                    
            except Exception as e:
                print(f"Error migrando {file}: {e}")
                continue
        
        return migrated_ids
    
    @staticmethod
    def _migrate_simple_format(data: Dict[str, Any]) -> StandardResult:
        """Migra formato simple legacy a StandardResult."""
        # Extraer información básica
        algorithm = data.get('algorithm', 'unknown')
        instance = data.get('instance', 'unknown')
        
        # Crear estructuras necesarias
        problem_info = ProblemInfo(
            name=instance,
            dimension=data.get('dimension', 0)
        )
        
        algorithm_info = AlgorithmInfo(
            name=algorithm,
            population_size=data.get('population_size', 30),
            max_iterations=data.get('iterations', 100)
        )
        
        # Ejecución básica
        execution_info = ExecutionInfo(
            start_time=datetime.now(),
            end_time=datetime.now(),
            duration_seconds=data.get('execution_time', 0),
            platform="unknown",
            python_version="unknown",
            cpu_count=1,
            memory_gb=0.0
        )
        
        # Run único
        run = SingleRunResult(
            run_id=0,
            seed=data.get('seed', 42),
            best_fitness=data.get('best_fitness', float('inf')),
            best_solution=data.get('best_solution'),
            convergence_curve=data.get('convergence', []),
            execution_time=data.get('execution_time', 0),
            iterations_completed=data.get('iterations', 100),
            evaluations=0
        )
        
        # Estadísticas
        statistics = MultiRunStatistics.from_runs([run])
        
        # Crear resultado
        result_id = f"{algorithm}_{instance}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        return StandardResult(
            result_id=result_id,
            result_type=ResultType.SINGLE_RUN,
            timestamp=datetime.now(),
            problem_info=problem_info,
            algorithm_info=algorithm_info,
            execution_info=execution_info,
            runs=[run],
            statistics=statistics,
            metadata={'migrated_from': 'legacy_simple'}
        )


def integrate_with_tracker(tracker_class: type) -> type:
    """
    Decorador para integrar automáticamente el esquema estandarizado
    con una clase de tracker existente.
    
    Ejemplo:
        @integrate_with_tracker
        class MyTracker(ExperimentTracker):
            pass
    """
    original_save = tracker_class.save_current
    original_load = tracker_class.load_experiment
    
    def save_with_standard(self) -> None:
        """Guarda tanto en formato tracking como estándar."""
        # Guardar formato original
        original_save(self)
        
        # También guardar en formato estándar
        if hasattr(self, 'current_experiment') and self.current_experiment:
            standard_result = ResultIntegration.experiment_to_standard(
                self.current_experiment
            )
            
            # Guardar en subdirectorio standard
            standard_dir = Path(self.base_dir) / "standard"
            standard_dir.mkdir(exist_ok=True)
            
            output_file = standard_dir / f"{standard_result.result_id}.json"
            standard_result.to_json(output_file)
    
    def load_with_standard(self, experiment_id: str) -> Any:
        """Carga experimento, con fallback a formato estándar."""
        try:
            # Intentar cargar formato original
            return original_load(self, experiment_id)
        except:
            # Intentar cargar formato estándar
            standard_file = Path(self.base_dir) / "standard" / f"{experiment_id}.json"
            if standard_file.exists():
                standard_result = StandardResult.from_json(standard_file)
                return ResultIntegration.standard_to_experiment(standard_result)
            raise
    
    tracker_class.save_current = save_with_standard
    tracker_class.load_experiment = load_with_standard
    
    return tracker_class


# Funciones de utilidad para conversión rápida

def quick_convert_to_standard(experiment_file: Union[str, Path]) -> StandardResult:
    """Convierte rápidamente un archivo de experimento a formato estándar."""
    with open(experiment_file, 'r') as f:
        data = json.load(f)
    
    record = ExperimentRecord(**data)
    return ResultIntegration.experiment_to_standard(record)


def quick_convert_to_experiment(standard_file: Union[str, Path]) -> ExperimentRecord:
    """Convierte rápidamente un archivo estándar a formato de experimento."""
    result = StandardResult.from_json(standard_file)
    return ResultIntegration.standard_to_experiment(result)