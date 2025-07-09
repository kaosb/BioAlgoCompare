"""
Sistema de registro de experimentos para BioAlgoCompare.

Este módulo proporciona un sistema robusto y profesional para registrar,
rastrear y gestionar todos los experimentos ejecutados, asegurando
reproducibilidad completa y trazabilidad científica.
"""

import json
import hashlib
import platform
import psutil
import git
import uuid
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional, Union, Callable
from dataclasses import dataclass, field, asdict
import pandas as pd
import numpy as np
from functools import wraps
import logging
import os
import sys


@dataclass
class SystemInfo:
    """Información del sistema donde se ejecuta el experimento."""
    platform: str
    platform_version: str
    python_version: str
    cpu_count: int
    cpu_model: str
    total_memory_gb: float
    hostname: str
    
    @classmethod
    def capture(cls) -> 'SystemInfo':
        """Captura la información actual del sistema."""
        return cls(
            platform=platform.system(),
            platform_version=platform.version(),
            python_version=sys.version,
            cpu_count=psutil.cpu_count(),
            cpu_model=platform.processor() or "Unknown",
            total_memory_gb=round(psutil.virtual_memory().total / (1024**3), 2),
            hostname=platform.node()
        )


@dataclass
class GitInfo:
    """Información del repositorio Git."""
    commit_hash: str
    branch: str
    is_dirty: bool
    commit_message: str
    commit_date: str
    
    @classmethod
    def capture(cls, repo_path: str = ".") -> Optional['GitInfo']:
        """Captura la información del repositorio Git."""
        try:
            repo = git.Repo(repo_path)
            commit = repo.head.commit
            
            return cls(
                commit_hash=str(commit.hexsha),
                branch=repo.active_branch.name,
                is_dirty=repo.is_dirty(),
                commit_message=commit.message.strip(),
                commit_date=datetime.fromtimestamp(commit.committed_date).isoformat()
            )
        except:
            return None


@dataclass
class ExperimentConfig:
    """Configuración del experimento."""
    algorithm: str
    problem_instance: str
    population_size: int
    max_iterations: int
    algorithm_params: Dict[str, Any] = field(default_factory=dict)
    seed: Optional[int] = None
    
    def to_hash(self) -> str:
        """Genera un hash único para esta configuración."""
        config_str = json.dumps(asdict(self), sort_keys=True)
        return hashlib.md5(config_str.encode()).hexdigest()[:8]


@dataclass
class ExperimentResult:
    """Resultado de una ejecución individual."""
    run_id: int
    seed: int
    best_fitness: float
    convergence_curve: List[float]
    execution_time: float
    final_solution: Any
    iterations_completed: int
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ExperimentRecord:
    """Registro completo de un experimento."""
    experiment_id: str
    timestamp: str
    config: ExperimentConfig
    system_info: SystemInfo
    git_info: Optional[GitInfo]
    results: List[ExperimentResult] = field(default_factory=list)
    summary_stats: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def add_result(self, result: ExperimentResult) -> None:
        """Añade un resultado al experimento."""
        self.results.append(result)
        self._update_summary_stats()
    
    def _update_summary_stats(self) -> None:
        """Actualiza las estadísticas resumen."""
        if not self.results:
            return
            
        fitness_values = [r.best_fitness for r in self.results]
        execution_times = [r.execution_time for r in self.results]
        
        self.summary_stats = {
            'total_runs': len(self.results),
            'best_fitness': min(fitness_values),
            'worst_fitness': max(fitness_values),
            'mean_fitness': np.mean(fitness_values),
            'std_fitness': np.std(fitness_values),
            'median_fitness': np.median(fitness_values),
            'q1_fitness': np.percentile(fitness_values, 25),
            'q3_fitness': np.percentile(fitness_values, 75),
            'mean_execution_time': np.mean(execution_times),
            'total_execution_time': sum(execution_times),
            'convergence_rate': self._calculate_convergence_rate()
        }
    
    def _calculate_convergence_rate(self) -> float:
        """Calcula la tasa de convergencia promedio."""
        if not self.results:
            return 0.0
            
        rates = []
        for result in self.results:
            if len(result.convergence_curve) > 1:
                initial = result.convergence_curve[0]
                final = result.convergence_curve[-1]
                if initial > 0:
                    rate = (initial - final) / initial
                    rates.append(rate)
        
        return np.mean(rates) if rates else 0.0


class ExperimentTracker:
    """
    Sistema principal de seguimiento de experimentos.
    
    Gestiona el registro, almacenamiento y recuperación de experimentos
    con soporte para múltiples backends de almacenamiento.
    """
    
    def __init__(self, base_dir: str = "experiments", auto_save: bool = True):
        """
        Inicializa el tracker de experimentos.
        
        Args:
            base_dir: Directorio base para almacenar experimentos
            auto_save: Si guardar automáticamente después de cada resultado
        """
        self.base_dir = Path(base_dir)
        self.base_dir.mkdir(parents=True, exist_ok=True)
        self.auto_save = auto_save
        
        # Crear subdirectorios
        self.records_dir = self.base_dir / "records"
        self.metadata_dir = self.base_dir / "metadata"
        self.summaries_dir = self.base_dir / "summaries"
        
        for dir_path in [self.records_dir, self.metadata_dir, self.summaries_dir]:
            dir_path.mkdir(exist_ok=True)
        
        # Estado actual
        self.current_experiment: Optional[ExperimentRecord] = None
        self._setup_logging()
    
    def _setup_logging(self) -> None:
        """Configura el sistema de logging."""
        log_file = self.base_dir / "experiment_tracker.log"
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
    
    def start_experiment(self, config: ExperimentConfig, 
                        metadata: Optional[Dict[str, Any]] = None) -> str:
        """
        Inicia un nuevo experimento.
        
        Args:
            config: Configuración del experimento
            metadata: Metadatos adicionales opcionales
            
        Returns:
            ID único del experimento
        """
        # Generar ID único
        timestamp = datetime.now()
        experiment_id = f"{config.algorithm}_{config.problem_instance}_{timestamp.strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:8]}"
        
        # Capturar información del sistema
        system_info = SystemInfo.capture()
        git_info = GitInfo.capture()
        
        # Crear registro del experimento
        self.current_experiment = ExperimentRecord(
            experiment_id=experiment_id,
            timestamp=timestamp.isoformat(),
            config=config,
            system_info=system_info,
            git_info=git_info,
            metadata=metadata or {}
        )
        
        self.logger.info(f"Experimento iniciado: {experiment_id}")
        
        # Guardar configuración inicial
        self._save_metadata()
        
        return experiment_id
    
    def log_result(self, result: ExperimentResult) -> None:
        """
        Registra un resultado en el experimento actual.
        
        Args:
            result: Resultado de una ejecución
        """
        if not self.current_experiment:
            raise RuntimeError("No hay experimento activo. Llama a start_experiment primero.")
        
        self.current_experiment.add_result(result)
        self.logger.info(f"Resultado registrado: Run {result.run_id}, Fitness: {result.best_fitness:.6f}")
        
        if self.auto_save:
            self.save_current()
    
    def save_current(self) -> None:
        """Guarda el experimento actual."""
        if not self.current_experiment:
            return
            
        # Guardar registro completo
        record_file = self.records_dir / f"{self.current_experiment.experiment_id}.json"
        with open(record_file, 'w') as f:
            json.dump(asdict(self.current_experiment), f, indent=2, default=str)
        
        # Actualizar resumen
        self._update_summary()
        
        self.logger.info(f"Experimento guardado: {record_file}")
    
    def _save_metadata(self) -> None:
        """Guarda los metadatos del experimento."""
        if not self.current_experiment:
            return
            
        metadata_file = self.metadata_dir / f"{self.current_experiment.experiment_id}_metadata.json"
        metadata = {
            'experiment_id': self.current_experiment.experiment_id,
            'timestamp': self.current_experiment.timestamp,
            'config': asdict(self.current_experiment.config),
            'system_info': asdict(self.current_experiment.system_info),
            'git_info': asdict(self.current_experiment.git_info) if self.current_experiment.git_info else None
        }
        
        with open(metadata_file, 'w') as f:
            json.dump(metadata, f, indent=2)
    
    def _update_summary(self) -> None:
        """Actualiza el archivo de resumen de experimentos."""
        summary_file = self.summaries_dir / "experiments_summary.csv"
        
        # Crear DataFrame con información resumida
        summaries = []
        for record_file in self.records_dir.glob("*.json"):
            with open(record_file, 'r') as f:
                record = json.load(f)
            
            summary = {
                'experiment_id': record['experiment_id'],
                'timestamp': record['timestamp'],
                'algorithm': record['config']['algorithm'],
                'instance': record['config']['problem_instance'],
                'population_size': record['config']['population_size'],
                'max_iterations': record['config']['max_iterations'],
                'total_runs': record['summary_stats'].get('total_runs', 0),
                'best_fitness': record['summary_stats'].get('best_fitness', None),
                'mean_fitness': record['summary_stats'].get('mean_fitness', None),
                'std_fitness': record['summary_stats'].get('std_fitness', None),
                'total_time': record['summary_stats'].get('total_execution_time', None)
            }
            summaries.append(summary)
        
        if summaries:
            df = pd.DataFrame(summaries)
            df.to_csv(summary_file, index=False)
    
    def load_experiment(self, experiment_id: str) -> ExperimentRecord:
        """
        Carga un experimento guardado.
        
        Args:
            experiment_id: ID del experimento
            
        Returns:
            Registro del experimento
        """
        record_file = self.records_dir / f"{experiment_id}.json"
        if not record_file.exists():
            raise FileNotFoundError(f"Experimento no encontrado: {experiment_id}")
        
        with open(record_file, 'r') as f:
            data = json.load(f)
        
        # Reconstruir objetos
        config = ExperimentConfig(**data['config'])
        system_info = SystemInfo(**data['system_info'])
        git_info = GitInfo(**data['git_info']) if data['git_info'] else None
        
        record = ExperimentRecord(
            experiment_id=data['experiment_id'],
            timestamp=data['timestamp'],
            config=config,
            system_info=system_info,
            git_info=git_info,
            metadata=data.get('metadata', {})
        )
        
        # Reconstruir resultados
        for result_data in data['results']:
            result = ExperimentResult(**result_data)
            record.results.append(result)
        
        record.summary_stats = data['summary_stats']
        
        return record
    
    def list_experiments(self, filter_criteria: Optional[Dict[str, Any]] = None) -> pd.DataFrame:
        """
        Lista todos los experimentos con filtros opcionales.
        
        Args:
            filter_criteria: Criterios de filtrado (algorithm, instance, etc.)
            
        Returns:
            DataFrame con resumen de experimentos
        """
        summary_file = self.summaries_dir / "experiments_summary.csv"
        
        if not summary_file.exists():
            self._update_summary()
        
        df = pd.read_csv(summary_file)
        
        # Aplicar filtros si se proporcionan
        if filter_criteria:
            for key, value in filter_criteria.items():
                if key in df.columns:
                    df = df[df[key] == value]
        
        return df
    
    def compare_experiments(self, experiment_ids: List[str]) -> pd.DataFrame:
        """
        Compara múltiples experimentos.
        
        Args:
            experiment_ids: Lista de IDs de experimentos
            
        Returns:
            DataFrame comparativo
        """
        comparisons = []
        
        for exp_id in experiment_ids:
            try:
                record = self.load_experiment(exp_id)
                comparison = {
                    'experiment_id': exp_id,
                    'algorithm': record.config.algorithm,
                    'instance': record.config.problem_instance,
                    **record.summary_stats
                }
                comparisons.append(comparison)
            except FileNotFoundError:
                self.logger.warning(f"Experimento no encontrado: {exp_id}")
        
        return pd.DataFrame(comparisons)
    
    def export_experiment(self, experiment_id: str, format: str = 'json',
                         output_dir: Optional[str] = None) -> str:
        """
        Exporta un experimento en el formato especificado.
        
        Args:
            experiment_id: ID del experimento
            format: Formato de exportación ('json', 'csv', 'latex', 'html')
            output_dir: Directorio de salida (por defecto: exports/)
            
        Returns:
            Ruta del archivo exportado
        """
        record = self.load_experiment(experiment_id)
        
        if output_dir is None:
            output_dir = self.base_dir / "exports"
        output_dir = Path(output_dir)
        output_dir.mkdir(exist_ok=True)
        
        if format == 'json':
            output_file = output_dir / f"{experiment_id}.json"
            with open(output_file, 'w') as f:
                json.dump(asdict(record), f, indent=2, default=str)
                
        elif format == 'csv':
            # Exportar resultados detallados
            results_data = []
            for result in record.results:
                row = {
                    'run_id': result.run_id,
                    'seed': result.seed,
                    'best_fitness': result.best_fitness,
                    'execution_time': result.execution_time,
                    'iterations': result.iterations_completed
                }
                results_data.append(row)
            
            df = pd.DataFrame(results_data)
            output_file = output_dir / f"{experiment_id}_results.csv"
            df.to_csv(output_file, index=False)
            
            # Exportar curvas de convergencia
            conv_file = output_dir / f"{experiment_id}_convergence.csv"
            conv_data = {}
            for result in record.results:
                conv_data[f'run_{result.run_id}'] = result.convergence_curve
            
            conv_df = pd.DataFrame(conv_data)
            conv_df.to_csv(conv_file, index=False)
            
        elif format == 'latex':
            # Generar tabla LaTeX con resultados
            output_file = output_dir / f"{experiment_id}_table.tex"
            latex_content = self._generate_latex_table(record)
            with open(output_file, 'w') as f:
                f.write(latex_content)
                
        elif format == 'html':
            # Generar reporte HTML
            output_file = output_dir / f"{experiment_id}_report.html"
            html_content = self._generate_html_report(record)
            with open(output_file, 'w') as f:
                f.write(html_content)
        
        else:
            raise ValueError(f"Formato no soportado: {format}")
        
        self.logger.info(f"Experimento exportado: {output_file}")
        return str(output_file)
    
    def _generate_latex_table(self, record: ExperimentRecord) -> str:
        """Genera una tabla LaTeX con los resultados."""
        stats = record.summary_stats
        
        latex = r"""\begin{table}[htbp]
\centering
\caption{Results for """ + record.config.algorithm + """ on """ + record.config.problem_instance + r"""}
\begin{tabular}{lr}
\toprule
\textbf{Metric} & \textbf{Value} \\
\midrule
Best Fitness & """ + f"{stats['best_fitness']:.4f}" + r""" \\
Mean Fitness & """ + f"{stats['mean_fitness']:.4f}" + r""" $\pm$ """ + f"{stats['std_fitness']:.4f}" + r""" \\
Median Fitness & """ + f"{stats['median_fitness']:.4f}" + r""" \\
Q1-Q3 & """ + f"[{stats['q1_fitness']:.4f}, {stats['q3_fitness']:.4f}]" + r""" \\
Total Runs & """ + str(stats['total_runs']) + r""" \\
Mean Time (s) & """ + f"{stats['mean_execution_time']:.2f}" + r""" \\
\bottomrule
\end{tabular}
\label{tab:""" + record.experiment_id + r"""}
\end{table}"""
        
        return latex
    
    def _generate_html_report(self, record: ExperimentRecord) -> str:
        """Genera un reporte HTML con los resultados."""
        html = f"""<!DOCTYPE html>
<html>
<head>
    <title>Experiment Report: {record.experiment_id}</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 40px; }}
        h1, h2 {{ color: #333; }}
        table {{ border-collapse: collapse; width: 100%; margin: 20px 0; }}
        th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
        th {{ background-color: #f2f2f2; }}
        .metadata {{ background-color: #f9f9f9; padding: 15px; border-radius: 5px; }}
        .stats {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 20px; }}
        .stat-box {{ background-color: #e9f5ff; padding: 15px; border-radius: 5px; }}
    </style>
</head>
<body>
    <h1>Experiment Report</h1>
    <h2>{record.experiment_id}</h2>
    
    <div class="metadata">
        <h3>Configuration</h3>
        <p><strong>Algorithm:</strong> {record.config.algorithm}</p>
        <p><strong>Instance:</strong> {record.config.problem_instance}</p>
        <p><strong>Population Size:</strong> {record.config.population_size}</p>
        <p><strong>Max Iterations:</strong> {record.config.max_iterations}</p>
        <p><strong>Timestamp:</strong> {record.timestamp}</p>
    </div>
    
    <h3>Summary Statistics</h3>
    <div class="stats">
        <div class="stat-box">
            <strong>Best Fitness</strong><br>
            {record.summary_stats['best_fitness']:.4f}
        </div>
        <div class="stat-box">
            <strong>Mean ± Std</strong><br>
            {record.summary_stats['mean_fitness']:.4f} ± {record.summary_stats['std_fitness']:.4f}
        </div>
        <div class="stat-box">
            <strong>Median</strong><br>
            {record.summary_stats['median_fitness']:.4f}
        </div>
        <div class="stat-box">
            <strong>Total Runs</strong><br>
            {record.summary_stats['total_runs']}
        </div>
    </div>
    
    <h3>Detailed Results</h3>
    <table>
        <tr>
            <th>Run</th>
            <th>Seed</th>
            <th>Best Fitness</th>
            <th>Time (s)</th>
            <th>Iterations</th>
        </tr>
        {''.join(f'''
        <tr>
            <td>{r.run_id}</td>
            <td>{r.seed}</td>
            <td>{r.best_fitness:.4f}</td>
            <td>{r.execution_time:.2f}</td>
            <td>{r.iterations_completed}</td>
        </tr>''' for r in record.results[:10])}
    </table>
    
    <p><em>Generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</em></p>
</body>
</html>"""
        
        return html


def track_experiment(tracker: ExperimentTracker) -> Callable:
    """
    Decorador para rastrear automáticamente experimentos.
    
    Uso:
        @track_experiment(tracker)
        def run_algorithm(config: ExperimentConfig):
            # código del algoritmo
            return result
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(config: ExperimentConfig, *args, **kwargs):
            # Iniciar experimento
            exp_id = tracker.start_experiment(config)
            
            try:
                # Ejecutar función
                result = func(config, *args, **kwargs)
                
                # Si el resultado es un ExperimentResult, registrarlo
                if isinstance(result, ExperimentResult):
                    tracker.log_result(result)
                elif isinstance(result, list) and all(isinstance(r, ExperimentResult) for r in result):
                    for r in result:
                        tracker.log_result(r)
                
                # Guardar experimento
                tracker.save_current()
                
                return result
                
            except Exception as e:
                # Registrar error
                tracker.current_experiment.metadata['error'] = str(e)
                tracker.save_current()
                raise
        
        return wrapper
    return decorator


# Función de utilidad para integración fácil
def create_experiment_result(run_id: int, seed: int, algorithm_result: Any,
                           execution_time: float) -> ExperimentResult:
    """
    Crea un ExperimentResult a partir del resultado de un algoritmo.
    
    Args:
        run_id: ID de la ejecución
        seed: Semilla utilizada
        algorithm_result: Resultado del algoritmo (debe tener fitness() y get_convergence_curve())
        execution_time: Tiempo de ejecución
        
    Returns:
        ExperimentResult listo para registrar
    """
    return ExperimentResult(
        run_id=run_id,
        seed=seed,
        best_fitness=algorithm_result.fitness(),
        convergence_curve=algorithm_result.get_convergence_curve() if hasattr(algorithm_result, 'get_convergence_curve') else [],
        execution_time=execution_time,
        final_solution=algorithm_result.position if hasattr(algorithm_result, 'position') else None,
        iterations_completed=len(algorithm_result.get_convergence_curve()) - 1 if hasattr(algorithm_result, 'get_convergence_curve') else 0
    )