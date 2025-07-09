"""
Pipeline unificado de resultados para BioAlgoCompare.

Este módulo proporciona un pipeline completo desde la generación
de resultados hasta su almacenamiento y exportación.
"""

import os
from pathlib import Path
from typing import Optional, Dict, Any, List, Union
from datetime import datetime
import logging

from ..result_schema_v2 import StandardResultV2
from ..results_database import ResultsDatabase
from ..result_validation import ResultValidator

logger = logging.getLogger(__name__)


class ResultPipeline:
    """
    Pipeline unificado para procesamiento de resultados.
    
    Proporciona un flujo completo:
    1. Captura de resultados
    2. Validación
    3. Almacenamiento
    4. Exportación
    """
    
    def __init__(self, 
                 storage_backend: Optional[str] = None,
                 auto_save: bool = True,
                 validate_on_save: bool = True):
        """
        Inicializa el pipeline.
        
        Args:
            storage_backend: Ruta a base de datos SQLite. Si None, usa default.
            auto_save: Si guardar automáticamente en base de datos
            validate_on_save: Si validar antes de guardar
        """
        self.storage_backend = storage_backend or self._get_default_db_path()
        self.auto_save = auto_save
        self.validate_on_save = validate_on_save
        
        # Inicializar componentes
        self._storage = None
        self._validator = ResultValidator()
        
        # Cache de resultados procesados
        self._cache = {}
        
    def _get_default_db_path(self) -> str:
        """Obtiene la ruta por defecto para la base de datos."""
        results_dir = Path.home() / '.bioalgocompare' / 'results'
        results_dir.mkdir(parents=True, exist_ok=True)
        return str(results_dir / 'results.db')
    
    @property
    def storage(self) -> ResultsDatabase:
        """Acceso lazy al storage."""
        if self._storage is None:
            self._storage = ResultsDatabase(self.storage_backend)
        return self._storage
    
    def process(self, result: StandardResultV2) -> StandardResultV2:
        """
        Procesa un resultado a través del pipeline completo.
        
        Args:
            result: Resultado a procesar
            
        Returns:
            Resultado procesado y validado
            
        Raises:
            ValidationError: Si la validación falla
        """
        logger.info(f"Processing result {result.result_id}")
        
        # 1. Completar metadatos si faltan
        if result.execution_info:
            result.execution_info.finalize()
        
        # 2. Calcular checksum
        if not result.checksum:
            result.checksum = result.calculate_checksum()
            logger.debug(f"Calculated checksum: {result.checksum[:12]}...")
        
        # 3. Validar
        if self.validate_on_save:
            is_valid = result.validate()
            if not is_valid:
                raise ValidationError(
                    f"Result validation failed: {result.validation_errors}"
                )
            logger.debug("Result validated successfully")
        
        # 4. Almacenar si auto_save está activo
        if self.auto_save:
            self.save(result)
        
        # 5. Cachear resultado
        self._cache[result.result_id] = result
        
        logger.info(f"Result {result.result_id} processed successfully")
        return result
    
    def save(self, result: StandardResultV2) -> None:
        """
        Guarda un resultado en el almacenamiento.
        
        Args:
            result: Resultado a guardar
        """
        # Guardar en base de datos
        self.storage.save_result(result)
        
        # También guardar JSON en directorio de resultados
        json_dir = Path(self.storage_backend).parent / 'json'
        json_dir.mkdir(exist_ok=True)
        
        timestamp = result.timestamp.strftime('%Y%m%d_%H%M%S')
        filename = f"{result.algorithm_info.name}_{result.problem_info.name}_{timestamp}.json"
        json_path = json_dir / filename
        
        result.to_json(json_path)
        logger.info(f"Result saved to {json_path}")
    
    def load(self, result_id: str) -> StandardResultV2:
        """
        Carga un resultado del almacenamiento.
        
        Args:
            result_id: ID del resultado
            
        Returns:
            Resultado cargado
        """
        # Verificar cache primero
        if result_id in self._cache:
            return self._cache[result_id]
        
        # Cargar de base de datos
        result = self.storage.get_result(result_id)
        if result:
            self._cache[result_id] = result
            return result
        
        raise ValueError(f"Result {result_id} not found")
    
    def export(self, 
               result_id: str, 
               format: str, 
               output_path: Optional[Union[str, Path]] = None,
               **kwargs) -> Any:
        """
        Exporta un resultado en el formato especificado.
        
        Args:
            result_id: ID del resultado
            format: Formato de exportación (json, csv, latex, hdf5)
            output_path: Ruta de salida opcional
            **kwargs: Argumentos adicionales para el exportador
            
        Returns:
            Datos exportados o ruta del archivo
        """
        result = self.load(result_id)
        
        # Mapeo de formatos a métodos
        exporters = {
            'json': self._export_json,
            'csv': self._export_csv,
            'latex': self._export_latex,
            'hdf5': self._export_hdf5,
            'summary': self._export_summary
        }
        
        if format not in exporters:
            raise ValueError(f"Unsupported format: {format}")
        
        return exporters[format](result, output_path, **kwargs)
    
    def _export_json(self, result: StandardResultV2, 
                     output_path: Optional[Path], **kwargs) -> str:
        """Exporta a JSON."""
        return result.to_json(output_path, **kwargs)
    
    def _export_csv(self, result: StandardResultV2, 
                    output_path: Optional[Path], **kwargs) -> Any:
        """Exporta a CSV."""
        df = result.to_dataframe(**kwargs)
        
        if output_path:
            df.to_csv(output_path, index=False)
            return str(output_path)
        return df
    
    def _export_latex(self, result: StandardResultV2, 
                      output_path: Optional[Path], **kwargs) -> str:
        """Exporta a LaTeX."""
        latex = result.to_latex(**kwargs)
        
        if output_path:
            Path(output_path).write_text(latex)
            return str(output_path)
        return latex
    
    def _export_hdf5(self, result: StandardResultV2, 
                     output_path: Optional[Path], **kwargs) -> str:
        """Exporta a HDF5."""
        if not output_path:
            raise ValueError("output_path required for HDF5 export")
        
        result.to_hdf5(output_path, **kwargs)
        return str(output_path)
    
    def _export_summary(self, result: StandardResultV2, 
                        output_path: Optional[Path], **kwargs) -> Dict[str, Any]:
        """Exporta resumen."""
        summary = result.get_summary()
        
        if output_path:
            import json
            Path(output_path).write_text(
                json.dumps(summary, indent=2, default=str)
            )
            return str(output_path)
        return summary
    
    def query(self, **filters) -> List[StandardResultV2]:
        """
        Consulta resultados con filtros.
        
        Args:
            **filters: Filtros para la consulta
            
        Returns:
            Lista de resultados que coinciden
        """
        return self.storage.query_results(**filters)
    
    def get_statistics(self, algorithm: Optional[str] = None,
                      problem: Optional[str] = None) -> Dict[str, Any]:
        """
        Obtiene estadísticas agregadas.
        
        Args:
            algorithm: Filtrar por algoritmo
            problem: Filtrar por problema
            
        Returns:
            Diccionario con estadísticas
        """
        results = self.query(algorithm=algorithm, problem=problem)
        
        if not results:
            return {}
        
        stats = {
            'total_results': len(results),
            'algorithms': list(set(r.algorithm_info.name for r in results)),
            'problems': list(set(r.problem_info.name for r in results)),
            'total_runs': sum(r.statistics.n_runs for r in results),
            'date_range': {
                'start': min(r.timestamp for r in results),
                'end': max(r.timestamp for r in results)
            }
        }
        
        # Estadísticas por algoritmo
        by_algorithm = {}
        for r in results:
            alg = r.algorithm_info.name
            if alg not in by_algorithm:
                by_algorithm[alg] = {
                    'count': 0,
                    'best_fitness': [],
                    'mean_fitness': [],
                    'execution_time': []
                }
            
            by_algorithm[alg]['count'] += 1
            by_algorithm[alg]['best_fitness'].append(r.statistics.best_fitness)
            by_algorithm[alg]['mean_fitness'].append(r.statistics.mean_fitness)
            by_algorithm[alg]['execution_time'].append(r.statistics.total_execution_time)
        
        # Calcular promedios
        for alg, data in by_algorithm.items():
            data['avg_best_fitness'] = sum(data['best_fitness']) / data['count']
            data['avg_mean_fitness'] = sum(data['mean_fitness']) / data['count']
            data['avg_execution_time'] = sum(data['execution_time']) / data['count']
        
        stats['by_algorithm'] = by_algorithm
        
        return stats
    
    def cleanup_cache(self) -> None:
        """Limpia la cache de resultados."""
        self._cache.clear()
        logger.info("Result cache cleared")
    
    def close(self) -> None:
        """Cierra conexiones y limpia recursos."""
        if self._storage:
            self._storage.close()
        self.cleanup_cache()


class ValidationError(Exception):
    """Error en validación de resultados."""
    pass


# Singleton global para facilitar uso
_default_pipeline = None


def get_default_pipeline() -> ResultPipeline:
    """Obtiene el pipeline por defecto."""
    global _default_pipeline
    if _default_pipeline is None:
        _default_pipeline = ResultPipeline()
    return _default_pipeline


def process_result(result: StandardResultV2) -> StandardResultV2:
    """Procesa un resultado con el pipeline por defecto."""
    return get_default_pipeline().process(result)