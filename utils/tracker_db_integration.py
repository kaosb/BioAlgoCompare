"""
Integración del sistema de tracking con la base de datos SQLite.

Este módulo proporciona decoradores y utilidades para que el sistema
de tracking automáticamente persista resultados en la base de datos.
"""

import logging
from pathlib import Path
from typing import Optional, Union, Callable
from functools import wraps

from utils.experiment_tracker import ExperimentTracker, ExperimentRecord
from utils.results_database import ResultsDatabase
from utils.result_integration import ResultIntegration
from utils.result_schema import StandardResult


logger = logging.getLogger(__name__)


class TrackerWithDatabase(ExperimentTracker):
    """
    ExperimentTracker extendido con persistencia automática en base de datos.
    """
    
    def __init__(
        self,
        base_dir: str = "experiments",
        auto_save: bool = True,
        db_path: Optional[Union[str, Path]] = None,
        auto_persist: bool = True
    ):
        """
        Inicializa el tracker con soporte de base de datos.
        
        Args:
            base_dir: Directorio base para experimentos
            auto_save: Guardar automáticamente cambios
            db_path: Ruta a la base de datos (None usa default)
            auto_persist: Persistir automáticamente en DB
        """
        super().__init__(base_dir, auto_save)
        
        # Inicializar base de datos
        if db_path is None:
            db_path = Path(base_dir) / "results.db"
        
        self.db = ResultsDatabase(db_path)
        self.auto_persist = auto_persist
        
        logger.info(f"Tracker inicializado con DB en {db_path}")
    
    def save_current(self) -> None:
        """Guarda el experimento actual en archivos y base de datos."""
        # Guardar en archivos (método padre)
        super().save_current()
        
        # Persistir en base de datos si está habilitado
        if self.auto_persist and self.current_experiment:
            self._persist_to_database(self.current_experiment)
    
    def _persist_to_database(self, experiment: ExperimentRecord) -> bool:
        """
        Persiste un experimento en la base de datos.
        
        Args:
            experiment: Registro de experimento
            
        Returns:
            True si se persistió correctamente
        """
        try:
            # Convertir a formato estándar
            standard_result = ResultIntegration.experiment_to_standard(experiment)
            
            # Insertar en base de datos
            success = self.db.insert_result(standard_result)
            
            if success:
                logger.info(f"Experimento {experiment.experiment_id} persistido en DB")
            else:
                logger.warning(f"Experimento {experiment.experiment_id} ya existe en DB")
            
            return success
            
        except Exception as e:
            logger.error(f"Error persistiendo en DB: {e}")
            return False
    
    def sync_to_database(self, force: bool = False) -> None:
        """
        Sincroniza todos los experimentos locales con la base de datos.
        
        Args:
            force: Forzar re-inserción incluso si ya existe
        """
        records_dir = Path(self.base_dir) / "records"
        if not records_dir.exists():
            logger.warning("No hay experimentos para sincronizar")
            return
        
        synced = 0
        errors = 0
        
        for record_file in records_dir.glob("*.json"):
            try:
                # Cargar experimento
                experiment = self.load_experiment(record_file.stem)
                
                if force:
                    # Eliminar si existe
                    # Nota: Requeriría añadir método delete en ResultsDatabase
                    pass
                
                # Persistir
                if self._persist_to_database(experiment):
                    synced += 1
                    
            except Exception as e:
                logger.error(f"Error sincronizando {record_file}: {e}")
                errors += 1
        
        logger.info(f"Sincronización completada: {synced} exitosos, {errors} errores")
    
    def search_in_database(self, **criteria) -> list:
        """
        Busca experimentos en la base de datos.
        
        Args:
            **criteria: Criterios de búsqueda
            
        Returns:
            Lista de resultados
        """
        return self.db.search_results(**criteria)
    
    def get_from_database(self, result_id: str) -> Optional[StandardResult]:
        """
        Obtiene un resultado de la base de datos.
        
        Args:
            result_id: ID del resultado
            
        Returns:
            StandardResult o None
        """
        return self.db.get_result(result_id)
    
    def get_database_stats(self) -> dict:
        """Obtiene estadísticas de la base de datos."""
        return self.db.get_statistics()


def with_database_persistence(
    db_path: Optional[Union[str, Path]] = None,
    auto_persist: bool = True
):
    """
    Decorador para añadir persistencia en base de datos a una función
    que retorna ExperimentRecord o StandardResult.
    
    Args:
        db_path: Ruta a la base de datos
        auto_persist: Persistir automáticamente
        
    Ejemplo:
        @with_database_persistence()
        def run_experiment():
            # ... código del experimento ...
            return experiment_record
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Ejecutar función original
            result = func(*args, **kwargs)
            
            if not auto_persist:
                return result
            
            # Determinar path de DB
            if db_path is None:
                _db_path = "experiments/results.db"
            else:
                _db_path = db_path
            
            # Crear base de datos
            db = ResultsDatabase(_db_path)
            
            # Persistir según tipo de resultado
            if isinstance(result, ExperimentRecord):
                # Convertir y persistir
                standard_result = ResultIntegration.experiment_to_standard(result)
                db.insert_result(standard_result)
                
            elif isinstance(result, StandardResult):
                # Persistir directamente
                db.insert_result(result)
            
            elif isinstance(result, list):
                # Lista de resultados
                for item in result:
                    if isinstance(item, ExperimentRecord):
                        standard = ResultIntegration.experiment_to_standard(item)
                        db.insert_result(standard)
                    elif isinstance(item, StandardResult):
                        db.insert_result(item)
            
            return result
        
        return wrapper
    return decorator


class DatabaseBackedTracker:
    """
    Tracker simplificado que usa la base de datos como backend principal.
    """
    
    def __init__(self, db_path: Union[str, Path] = "results.db"):
        """
        Inicializa el tracker respaldado por DB.
        
        Args:
            db_path: Ruta a la base de datos
        """
        self.db = ResultsDatabase(db_path)
        self.current_result = None
    
    def track_result(self, result: StandardResult) -> bool:
        """
        Registra un resultado en la base de datos.
        
        Args:
            result: Resultado a registrar
            
        Returns:
            True si se registró correctamente
        """
        success = self.db.insert_result(result)
        if success:
            self.current_result = result
        return success
    
    def search(self, **criteria) -> list:
        """Busca resultados según criterios."""
        return self.db.search_results(**criteria)
    
    def get(self, result_id: str) -> Optional[StandardResult]:
        """Obtiene un resultado por ID."""
        return self.db.get_result(result_id)
    
    def get_best_for_problem(self, problem: str, algorithm: Optional[str] = None) -> Optional[StandardResult]:
        """
        Obtiene el mejor resultado para un problema.
        
        Args:
            problem: Nombre del problema
            algorithm: Filtrar por algoritmo (opcional)
            
        Returns:
            Mejor resultado o None
        """
        results = self.db.search_results(
            problem=problem,
            algorithm=algorithm,
            limit=1
        )
        
        if results:
            return self.db.get_result(results[0]['result_id'])
        
        return None
    
    def compare_algorithms(self, algorithms: list, problems: Optional[list] = None) -> dict:
        """
        Compara múltiples algoritmos.
        
        Args:
            algorithms: Lista de algoritmos
            problems: Lista de problemas (opcional)
            
        Returns:
            Diccionario con comparación
        """
        from utils.results_database import DatabaseQuery
        query = DatabaseQuery(self.db)
        
        df = query.compare_algorithms(algorithms, problems)
        
        # Convertir a diccionario estructurado
        comparison = {}
        
        for problem in df['problem_name'].unique():
            comparison[problem] = {}
            problem_df = df[df['problem_name'] == problem]
            
            for _, row in problem_df.iterrows():
                comparison[problem][row['algorithm_name']] = {
                    'best_fitness': row['best_fitness'],
                    'avg_fitness': row['avg_fitness'],
                    'avg_std': row['avg_std'],
                    'n_experiments': row['n_experiments']
                }
        
        return comparison
    
    def export_all(self, output_dir: Union[str, Path]) -> None:
        """Exporta toda la base de datos."""
        self.db.export_to_csv(output_dir)
    
    def backup(self, backup_path: Union[str, Path]) -> None:
        """Crea respaldo de la base de datos."""
        self.db.backup(backup_path)
    
    def stats(self) -> dict:
        """Obtiene estadísticas."""
        return self.db.get_statistics()


# Funciones de utilidad para integración fácil

def setup_database_tracking(
    experiment_dir: str = "experiments",
    db_name: str = "results.db"
) -> TrackerWithDatabase:
    """
    Configura un tracker con base de datos.
    
    Args:
        experiment_dir: Directorio de experimentos
        db_name: Nombre del archivo de base de datos
        
    Returns:
        TrackerWithDatabase configurado
    """
    db_path = Path(experiment_dir) / db_name
    return TrackerWithDatabase(
        base_dir=experiment_dir,
        db_path=db_path,
        auto_persist=True
    )


def migrate_experiments_to_database(
    experiment_dir: str = "experiments",
    db_path: Optional[Union[str, Path]] = None,
    pattern: str = "*.json"
) -> tuple:
    """
    Migra experimentos existentes a la base de datos.
    
    Args:
        experiment_dir: Directorio con experimentos
        db_path: Ruta a la base de datos
        pattern: Patrón de archivos
        
    Returns:
        Tupla (exitosos, errores)
    """
    if db_path is None:
        db_path = Path(experiment_dir) / "results.db"
    
    db = ResultsDatabase(db_path)
    
    records_dir = Path(experiment_dir) / "records"
    if not records_dir.exists():
        return 0, 0
    
    migrated = 0
    errors = 0
    
    for file in records_dir.glob(pattern):
        try:
            # Cargar experimento
            import json
            with open(file, 'r') as f:
                data = json.load(f)
            
            record = ExperimentRecord(**data)
            
            # Convertir y persistir
            standard = ResultIntegration.experiment_to_standard(record)
            if db.insert_result(standard):
                migrated += 1
                
        except Exception as e:
            logger.error(f"Error migrando {file}: {e}")
            errors += 1
    
    return migrated, errors