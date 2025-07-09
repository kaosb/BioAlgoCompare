"""
Sistema unificado de exportación científica para BioAlgoCompare.

Este módulo proporciona un pipeline completo para exportar resultados
en múltiples formatos científicos, asegurando reproducibilidad y
cumpliendo con estándares de publicación académica.
"""

import json
import pandas as pd
import numpy as np
from pathlib import Path
from typing import Dict, List, Any, Optional, Union, Tuple
from datetime import datetime
import hashlib
import logging
from abc import ABC, abstractmethod
import matplotlib.pyplot as plt
import seaborn as sns
from scipy import stats
import yaml
import zipfile
import csv

from ..result_schema_v2 import StandardResultV2
from ..results_database import ResultsDatabase
from ..statistics import UnifiedStatisticalAnalysis
from ..benchmarking import OPTIMAL_VALUES

logger = logging.getLogger(__name__)


class ExportFormat(ABC):
    """Clase base abstracta para formatos de exportación."""
    
    @abstractmethod
    def export(self, data: pd.DataFrame, metadata: Dict[str, Any], output_path: Path) -> Path:
        """Exporta los datos en el formato específico."""
        pass
    
    @abstractmethod
    def get_file_extension(self) -> str:
        """Retorna la extensión del archivo para este formato."""
        pass


class CSVExporter(ExportFormat):
    """Exportador para formato CSV estándar."""
    
    def export(self, data: pd.DataFrame, metadata: Dict[str, Any], output_path: Path) -> Path:
        """Exporta a CSV con metadatos en header."""
        csv_path = output_path.with_suffix('.csv')
        
        # Escribir metadatos como comentarios
        with open(csv_path, 'w', newline='') as f:
            # Header con metadatos
            f.write(f"# BioAlgoCompare Export - {metadata.get('export_date', datetime.now())}\n")
            f.write(f"# Experiment: {metadata.get('experiment_name', 'Unknown')}\n")
            f.write(f"# Total runs: {len(data)}\n")
            f.write(f"# Algorithms: {', '.join(data['algorithm'].unique())}\n")
            f.write(f"# Instances: {', '.join(data['instance'].unique())}\n")
            f.write("#\n")
            
            # Datos
            data.to_csv(f, index=False)
        
        return csv_path
    
    def get_file_extension(self) -> str:
        return '.csv'


class JSONExporter(ExportFormat):
    """Exportador para formato JSON con estructura completa."""
    
    def export(self, data: pd.DataFrame, metadata: Dict[str, Any], output_path: Path) -> Path:
        """Exporta a JSON con estructura jerárquica."""
        json_path = output_path.with_suffix('.json')
        
        # Estructurar datos por algoritmo e instancia
        structured_data = {
            'metadata': metadata,
            'summary': {
                'total_runs': len(data),
                'algorithms': sorted(data['algorithm'].unique().tolist()),
                'instances': sorted(data['instance'].unique().tolist()),
                'metrics': list(data.columns)
            },
            'results': {}
        }
        
        # Organizar resultados
        for algorithm in data['algorithm'].unique():
            algo_data = data[data['algorithm'] == algorithm]
            structured_data['results'][algorithm] = {}
            
            for instance in algo_data['instance'].unique():
                instance_data = algo_data[algo_data['instance'] == instance]
                structured_data['results'][algorithm][instance] = instance_data.to_dict('records')
        
        # Guardar con formato legible
        with open(json_path, 'w') as f:
            json.dump(structured_data, f, indent=2, default=str)
        
        return json_path
    
    def get_file_extension(self) -> str:
        return '.json'


class LaTeXExporter(ExportFormat):
    """Exportador para tablas LaTeX listas para publicación."""
    
    def __init__(self, style: str = 'ieee'):
        """
        Inicializa exportador LaTeX.
        
        Args:
            style: Estilo de formato ('ieee', 'acm', 'springer')
        """
        self.style = style
        
    def export(self, data: pd.DataFrame, metadata: Dict[str, Any], output_path: Path) -> Path:
        """Exporta múltiples tablas LaTeX."""
        latex_dir = output_path.parent / f"{output_path.stem}_latex"
        latex_dir.mkdir(exist_ok=True)
        
        # Tabla 1: Estadísticas descriptivas
        self._export_descriptive_stats(data, latex_dir / "descriptive_stats.tex")
        
        # Tabla 2: Comparación con óptimos
        self._export_optimal_comparison(data, latex_dir / "optimal_comparison.tex")
        
        # Tabla 3: Rankings
        self._export_rankings(data, latex_dir / "rankings.tex")
        
        # Tabla 4: Tests estadísticos
        self._export_statistical_tests(data, latex_dir / "statistical_tests.tex")
        
        # Crear archivo principal que incluye todas las tablas
        main_file = latex_dir / "main_tables.tex"
        with open(main_file, 'w') as f:
            f.write(self._generate_main_latex(metadata))
        
        return latex_dir
    
    def _export_descriptive_stats(self, data: pd.DataFrame, output_path: Path):
        """Exporta tabla de estadísticas descriptivas."""
        stats_data = []
        
        for algorithm in sorted(data['algorithm'].unique()):
            algo_data = data[data['algorithm'] == algorithm]
            
            for instance in sorted(algo_data['instance'].unique()):
                instance_data = algo_data[algo_data['instance'] == instance]
                fitness_values = instance_data['fitness']
                
                stats_data.append({
                    'Algorithm': algorithm,
                    'Instance': instance,
                    'Best': f"{fitness_values.min():.2f}",
                    'Mean': f"{fitness_values.mean():.2f}",
                    'Std': f"{fitness_values.std():.2f}",
                    'Median': f"{fitness_values.median():.2f}"
                })
        
        # Generar LaTeX
        latex = self._dataframe_to_latex(
            pd.DataFrame(stats_data),
            caption="Descriptive statistics for all algorithms on VRP instances",
            label="tab:descriptive_stats"
        )
        
        output_path.write_text(latex)
    
    def _export_optimal_comparison(self, data: pd.DataFrame, output_path: Path):
        """Exporta comparación con valores óptimos."""
        comparisons = []
        
        for instance in data['instance'].unique():
            if instance not in OPTIMAL_VALUES:
                continue
                
            optimal = OPTIMAL_VALUES[instance]
            instance_data = data[data['instance'] == instance]
            
            for algorithm in sorted(instance_data['algorithm'].unique()):
                algo_data = instance_data[instance_data['algorithm'] == algorithm]
                best = algo_data['fitness'].min()
                mean = algo_data['fitness'].mean()
                
                best_gap = ((best - optimal) / optimal) * 100
                mean_gap = ((mean - optimal) / optimal) * 100
                
                comparisons.append({
                    'Algorithm': algorithm,
                    'Instance': instance,
                    'Optimal': optimal,
                    'Best': f"{best:.2f}",
                    'Gap (%)': f"{best_gap:.2f}"
                })
        
        if comparisons:
            latex = self._dataframe_to_latex(
                pd.DataFrame(comparisons),
                caption="Comparison with known optimal values",
                label="tab:optimal_comparison"
            )
            output_path.write_text(latex)
    
    def _export_rankings(self, data: pd.DataFrame, output_path: Path):
        """Exporta tabla de rankings."""
        # Calcular ranking promedio
        rankings = []
        
        for instance in data['instance'].unique():
            instance_data = data[data['instance'] == instance]
            algo_means = instance_data.groupby('algorithm')['fitness'].mean().sort_values()
            
            for rank, (algorithm, mean_fitness) in enumerate(algo_means.items(), 1):
                rankings.append({
                    'Algorithm': algorithm,
                    'Instance': instance,
                    'Rank': rank,
                    'Mean Fitness': f"{mean_fitness:.2f}"
                })
        
        # Calcular ranking promedio por algoritmo
        rank_df = pd.DataFrame(rankings)
        avg_ranks = rank_df.groupby('Algorithm')['Rank'].mean().sort_values()
        
        final_rankings = []
        for algorithm, avg_rank in avg_ranks.items():
            final_rankings.append({
                'Rank': len(final_rankings) + 1,
                'Algorithm': algorithm,
                'Average Rank': f"{avg_rank:.2f}",
                'Instances': len(rank_df[rank_df['Algorithm'] == algorithm])
            })
        
        latex = self._dataframe_to_latex(
            pd.DataFrame(final_rankings),
            caption="Overall algorithm ranking across all instances",
            label="tab:rankings"
        )
        
        output_path.write_text(latex)
    
    def _export_statistical_tests(self, data: pd.DataFrame, output_path: Path):
        """Exporta resultados de tests estadísticos."""
        try:
            analyzer = UnifiedStatisticalAnalysis()
            
            # Preparar datos para análisis
            algorithm_data = {}
            for instance in data['instance'].unique():
                algorithm_data[instance] = {}
                instance_data = data[data['instance'] == instance]
                
                for algorithm in instance_data['algorithm'].unique():
                    algo_data = instance_data[instance_data['algorithm'] == algorithm]
                    algorithm_data[instance][algorithm] = algo_data['fitness'].values
            
            # Ejecutar tests
            results = analyzer.friedman_test(algorithm_data)
            
            # Crear tabla
            test_results = [{
                'Test': 'Friedman',
                'Statistic': f"{results['statistic']:.4f}",
                'p-value': f"{results['p_value']:.4f}",
                'df': results.get('df', 'N/A'),
                'Significant': 'Yes' if results['p_value'] < 0.05 else 'No'
            }]
            
            latex = self._dataframe_to_latex(
                pd.DataFrame(test_results),
                caption="Statistical test results for algorithm comparison",
                label="tab:statistical_tests"
            )
            
            output_path.write_text(latex)
            
        except Exception as e:
            logger.error(f"Error in statistical tests: {e}")
            output_path.write_text(f"% Error generating statistical tests: {e}\n")
    
    def _dataframe_to_latex(self, df: pd.DataFrame, caption: str, label: str) -> str:
        """Convierte DataFrame a tabla LaTeX con formato apropiado."""
        # Estilos por formato
        styles = {
            'ieee': {
                'column_format': 'l' + 'r' * (len(df.columns) - 1),
                'position': 'htbp',
                'font_size': 'small'
            },
            'acm': {
                'column_format': 'l' + 'c' * (len(df.columns) - 1),
                'position': 'h!',
                'font_size': 'footnotesize'
            },
            'springer': {
                'column_format': '|' + 'l|' * len(df.columns),
                'position': 'H',
                'font_size': 'small'
            }
        }
        
        style = styles.get(self.style, styles['ieee'])
        
        latex = f"\\begin{{table}}[{style['position']}]\n"
        latex += f"\\centering\n"
        latex += f"\\{style['font_size']}\n"
        latex += f"\\caption{{{caption}}}\n"
        latex += f"\\label{{{label}}}\n"
        latex += f"\\begin{{tabular}}{{{style['column_format']}}}\n"
        latex += "\\toprule\n"
        
        # Headers
        headers = ' & '.join(df.columns) + ' \\\\'
        latex += headers + '\n'
        latex += "\\midrule\n"
        
        # Datos
        for _, row in df.iterrows():
            row_str = ' & '.join(str(v) for v in row.values) + ' \\\\'
            latex += row_str + '\n'
        
        latex += "\\bottomrule\n"
        latex += "\\end{tabular}\n"
        latex += "\\end{table}\n"
        
        return latex
    
    def _generate_main_latex(self, metadata: Dict[str, Any]) -> str:
        """Genera archivo LaTeX principal."""
        return f"""% BioAlgoCompare Export - {metadata.get('export_date', datetime.now())}
% This file includes all generated tables

\\documentclass{{article}}
\\usepackage{{booktabs}}
\\usepackage{{float}}
\\usepackage{{caption}}

\\begin{{document}}

\\section{{Experimental Results}}

\\subsection{{Descriptive Statistics}}
\\input{{descriptive_stats.tex}}

\\subsection{{Comparison with Optimal Values}}
\\input{{optimal_comparison.tex}}

\\subsection{{Algorithm Rankings}}
\\input{{rankings.tex}}

\\subsection{{Statistical Analysis}}
\\input{{statistical_tests.tex}}

\\end{{document}}
"""
    
    def get_file_extension(self) -> str:
        return '.tex'


class ExcelExporter(ExportFormat):
    """Exportador para formato Excel con múltiples hojas."""
    
    def export(self, data: pd.DataFrame, metadata: Dict[str, Any], output_path: Path) -> Path:
        """Exporta a Excel con análisis completo."""
        excel_path = output_path.with_suffix('.xlsx')
        
        with pd.ExcelWriter(excel_path, engine='xlsxwriter') as writer:
            # Hoja 1: Datos crudos
            data.to_excel(writer, sheet_name='Raw Data', index=False)
            
            # Hoja 2: Estadísticas por algoritmo
            algo_stats = data.groupby('algorithm').agg({
                'fitness': ['mean', 'std', 'min', 'max', 'count'],
                'execution_time': ['mean', 'std']
            }).round(2)
            algo_stats.to_excel(writer, sheet_name='Algorithm Statistics')
            
            # Hoja 3: Estadísticas por instancia
            instance_stats = data.groupby('instance').agg({
                'fitness': ['mean', 'std', 'min', 'max', 'count']
            }).round(2)
            instance_stats.to_excel(writer, sheet_name='Instance Statistics')
            
            # Hoja 4: Pivot table
            pivot = data.pivot_table(
                values='fitness',
                index='instance',
                columns='algorithm',
                aggfunc='mean'
            ).round(2)
            pivot.to_excel(writer, sheet_name='Pivot Summary')
            
            # Hoja 5: Metadatos
            metadata_df = pd.DataFrame([metadata]).T
            metadata_df.columns = ['Value']
            metadata_df.to_excel(writer, sheet_name='Metadata')
            
            # Formatear
            workbook = writer.book
            header_format = workbook.add_format({
                'bold': True,
                'bg_color': '#D7E4BD',
                'border': 1
            })
            
            for sheet_name in writer.sheets:
                worksheet = writer.sheets[sheet_name]
                worksheet.set_column('A:Z', 15)
        
        return excel_path
    
    def get_file_extension(self) -> str:
        return '.xlsx'


class ScientificExportPipeline:
    """
    Pipeline unificado de exportación científica.
    
    Coordina la exportación en múltiples formatos y garantiza
    la reproducibilidad y trazabilidad de los resultados.
    """
    
    def __init__(self, 
                 results_source: Union[str, Path, ResultsDatabase],
                 output_dir: Optional[Path] = None):
        """
        Inicializa el pipeline de exportación.
        
        Args:
            results_source: Fuente de resultados (directorio, archivo o DB)
            output_dir: Directorio de salida (default: results_source/export)
        """
        self.results_source = results_source
        self.output_dir = Path(output_dir) if output_dir else self._get_default_output_dir()
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Registrar exportadores
        self.exporters = {
            'csv': CSVExporter(),
            'json': JSONExporter(),
            'latex': LaTeXExporter(),
            'excel': ExcelExporter()
        }
        
        # Cache de datos procesados
        self._data_cache = None
        self._metadata_cache = None
        
        logger.info(f"Scientific export pipeline initialized. Output: {self.output_dir}")
    
    def _get_default_output_dir(self) -> Path:
        """Determina directorio de salida por defecto."""
        if isinstance(self.results_source, (str, Path)):
            source_path = Path(self.results_source)
            if source_path.is_dir():
                return source_path / 'export'
            else:
                return source_path.parent / 'export'
        else:
            return Path.cwd() / 'export'
    
    def load_results(self) -> pd.DataFrame:
        """Carga y prepara los resultados para exportación."""
        if self._data_cache is not None:
            return self._data_cache
        
        logger.info("Loading results...")
        
        if isinstance(self.results_source, ResultsDatabase):
            # Cargar desde base de datos
            self._data_cache = self._load_from_database()
        elif isinstance(self.results_source, (str, Path)):
            source_path = Path(self.results_source)
            if source_path.is_file():
                # Cargar archivo individual
                self._data_cache = self._load_from_file(source_path)
            else:
                # Cargar directorio
                self._data_cache = self._load_from_directory(source_path)
        else:
            raise ValueError(f"Invalid results source: {type(self.results_source)}")
        
        logger.info(f"Loaded {len(self._data_cache)} results")
        return self._data_cache
    
    def _load_from_database(self) -> pd.DataFrame:
        """Carga resultados desde base de datos."""
        db = self.results_source
        results = db.get_all_results()
        
        rows = []
        for result in results:
            if hasattr(result, 'to_dict'):
                result_dict = result.to_dict()
            else:
                result_dict = result
            
            # Extraer runs individuales
            if 'runs' in result_dict:
                for run in result_dict['runs']:
                    rows.append({
                        'algorithm': result_dict.get('algorithm_info', {}).get('algorithm_name', 'unknown'),
                        'instance': result_dict.get('problem_info', {}).get('instance_name', 'unknown'),
                        'fitness': run.get('fitness', np.inf),
                        'execution_time': run.get('execution_time', 0),
                        'iterations': run.get('iterations', 0),
                        'seed': run.get('seed', 0),
                        'run_id': run.get('run_id', ''),
                        'result_id': result_dict.get('result_id', '')
                    })
        
        return pd.DataFrame(rows)
    
    def _load_from_file(self, file_path: Path) -> pd.DataFrame:
        """Carga resultados desde archivo."""
        if file_path.suffix == '.json':
            with open(file_path) as f:
                data = json.load(f)
            
            if isinstance(data, list):
                # Lista de resultados
                rows = []
                for item in data:
                    rows.extend(self._extract_runs(item))
                return pd.DataFrame(rows)
            else:
                # Resultado individual
                return pd.DataFrame(self._extract_runs(data))
        
        elif file_path.suffix == '.csv':
            return pd.read_csv(file_path)
        
        else:
            raise ValueError(f"Unsupported file format: {file_path.suffix}")
    
    def _load_from_directory(self, dir_path: Path) -> pd.DataFrame:
        """Carga resultados desde directorio."""
        all_rows = []
        
        # Buscar archivos JSON
        for json_file in dir_path.rglob("*.json"):
            if any(skip in json_file.name for skip in ['checkpoint', 'metadata', 'config']):
                continue
                
            try:
                df = self._load_from_file(json_file)
                all_rows.extend(df.to_dict('records'))
            except Exception as e:
                logger.warning(f"Could not load {json_file}: {e}")
        
        return pd.DataFrame(all_rows)
    
    def _extract_runs(self, result: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Extrae runs individuales de un resultado."""
        rows = []
        
        if 'runs' in result:
            # Formato StandardResultV2
            for run in result['runs']:
                rows.append({
                    'algorithm': result.get('algorithm_info', {}).get('algorithm_name', 'unknown'),
                    'instance': result.get('problem_info', {}).get('instance_name', 'unknown'),
                    'fitness': run.get('fitness', np.inf),
                    'execution_time': run.get('execution_time', 0),
                    'iterations': run.get('iterations', 0),
                    'seed': run.get('seed', 0),
                    'run_id': run.get('run_id', ''),
                    'result_id': result.get('result_id', '')
                })
        else:
            # Formato legacy
            rows.append({
                'algorithm': result.get('algorithm_name', 'unknown'),
                'instance': result.get('instance_name', 'unknown'),
                'fitness': result.get('fitness', np.inf),
                'execution_time': result.get('execution_time', 0),
                'iterations': result.get('iterations', 0),
                'seed': result.get('seed', 0)
            })
        
        return rows
    
    def generate_metadata(self) -> Dict[str, Any]:
        """Genera metadatos completos del experimento."""
        if self._metadata_cache is not None:
            return self._metadata_cache
        
        data = self.load_results()
        
        self._metadata_cache = {
            'export_info': {
                'export_date': datetime.now().isoformat(),
                'export_version': '2.0',
                'pipeline': 'ScientificExportPipeline'
            },
            'experiment_info': {
                'total_runs': len(data),
                'unique_algorithms': sorted(data['algorithm'].unique().tolist()),
                'unique_instances': sorted(data['instance'].unique().tolist()),
                'date_range': {
                    'start': data['result_id'].min() if 'result_id' in data.columns else 'N/A',
                    'end': data['result_id'].max() if 'result_id' in data.columns else 'N/A'
                }
            },
            'statistical_summary': {
                'algorithms_count': len(data['algorithm'].unique()),
                'instances_count': len(data['instance'].unique()),
                'runs_per_algorithm': data.groupby('algorithm').size().to_dict(),
                'runs_per_instance': data.groupby('instance').size().to_dict()
            },
            'data_integrity': {
                'total_records': len(data),
                'missing_values': data.isnull().sum().to_dict(),
                'data_hash': hashlib.sha256(data.to_string().encode()).hexdigest()
            }
        }
        
        return self._metadata_cache
    
    def export(self, 
               formats: Optional[List[str]] = None,
               include_plots: bool = True,
               create_archive: bool = True) -> Dict[str, Path]:
        """
        Ejecuta exportación completa en múltiples formatos.
        
        Args:
            formats: Lista de formatos a exportar (default: todos)
            include_plots: Si incluir visualizaciones
            create_archive: Si crear archivo ZIP con todo
            
        Returns:
            Dict con paths de archivos generados
        """
        if formats is None:
            formats = list(self.exporters.keys())
        
        logger.info(f"Starting export in formats: {formats}")
        
        # Preparar datos y metadatos
        data = self.load_results()
        metadata = self.generate_metadata()
        
        # Crear subdirectorio con timestamp
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        export_dir = self.output_dir / f"export_{timestamp}"
        export_dir.mkdir(exist_ok=True)
        
        exported_files = {}
        
        # 1. Exportar en cada formato
        for format_name in formats:
            if format_name in self.exporters:
                try:
                    exporter = self.exporters[format_name]
                    output_path = export_dir / f"results_{timestamp}"
                    file_path = exporter.export(data, metadata, output_path)
                    exported_files[format_name] = file_path
                    logger.info(f"Exported {format_name}: {file_path}")
                except Exception as e:
                    logger.error(f"Error exporting {format_name}: {e}")
        
        # 2. Generar visualizaciones si se solicita
        if include_plots:
            plots_dir = export_dir / 'plots'
            plots_dir.mkdir(exist_ok=True)
            plot_files = self._generate_plots(data, plots_dir)
            exported_files.update(plot_files)
        
        # 3. Guardar metadatos
        metadata_path = export_dir / 'metadata.yaml'
        with open(metadata_path, 'w') as f:
            yaml.dump(metadata, f, default_flow_style=False)
        exported_files['metadata'] = metadata_path
        
        # 4. Crear README
        readme_path = self._create_readme(export_dir, exported_files)
        exported_files['readme'] = readme_path
        
        # 5. Crear archivo ZIP si se solicita
        if create_archive:
            archive_path = self._create_archive(export_dir, timestamp)
            exported_files['archive'] = archive_path
        
        logger.info(f"Export completed. Files in: {export_dir}")
        return exported_files
    
    def _generate_plots(self, data: pd.DataFrame, output_dir: Path) -> Dict[str, Path]:
        """Genera visualizaciones científicas."""
        plots = {}
        
        # Configurar estilo de publicación
        plt.style.use('seaborn-v0_8-paper')
        plt.rcParams.update({
            'font.size': 10,
            'axes.labelsize': 10,
            'axes.titlesize': 12,
            'figure.dpi': 300,
            'savefig.dpi': 300
        })
        
        # 1. Box plots por algoritmo
        fig, ax = plt.subplots(figsize=(10, 6))
        algorithms = sorted(data['algorithm'].unique())
        box_data = [data[data['algorithm'] == alg]['fitness'].values for alg in algorithms]
        
        bp = ax.boxplot(box_data, labels=algorithms, patch_artist=True)
        ax.set_xlabel('Algorithm')
        ax.set_ylabel('Fitness Value')
        ax.set_title('Algorithm Performance Distribution')
        ax.grid(True, alpha=0.3)
        plt.xticks(rotation=45, ha='right')
        plt.tight_layout()
        
        box_path = output_dir / 'algorithm_boxplots.pdf'
        plt.savefig(box_path, bbox_inches='tight')
        plt.close()
        plots['boxplots'] = box_path
        
        # 2. Heatmap de rendimiento
        if len(data['instance'].unique()) > 1 and len(data['algorithm'].unique()) > 1:
            pivot = data.pivot_table(
                values='fitness',
                index='instance',
                columns='algorithm',
                aggfunc='mean'
            )
            
            fig, ax = plt.subplots(figsize=(12, 8))
            sns.heatmap(pivot, annot=True, fmt='.1f', cmap='YlOrRd_r', ax=ax)
            ax.set_title('Mean Performance Heatmap')
            plt.tight_layout()
            
            heatmap_path = output_dir / 'performance_heatmap.pdf'
            plt.savefig(heatmap_path, bbox_inches='tight')
            plt.close()
            plots['heatmap'] = heatmap_path
        
        # 3. Ranking plot
        avg_fitness = data.groupby('algorithm')['fitness'].mean().sort_values()
        
        fig, ax = plt.subplots(figsize=(8, 6))
        bars = ax.barh(range(len(avg_fitness)), avg_fitness.values)
        ax.set_yticks(range(len(avg_fitness)))
        ax.set_yticklabels(avg_fitness.index)
        ax.set_xlabel('Average Fitness')
        ax.set_title('Algorithm Ranking by Average Performance')
        ax.grid(True, alpha=0.3, axis='x')
        
        # Colorear las barras
        colors = plt.cm.RdYlGn_r(np.linspace(0.2, 0.8, len(bars)))
        for bar, color in zip(bars, colors):
            bar.set_color(color)
        
        plt.tight_layout()
        ranking_path = output_dir / 'algorithm_ranking.pdf'
        plt.savefig(ranking_path, bbox_inches='tight')
        plt.close()
        plots['ranking'] = ranking_path
        
        return plots
    
    def _create_readme(self, export_dir: Path, exported_files: Dict[str, Path]) -> Path:
        """Crea archivo README con documentación de la exportación."""
        readme_content = f"""# BioAlgoCompare Scientific Export

Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## Contents

This export contains comprehensive results from the BioAlgoCompare benchmarking platform,
formatted for scientific publication and analysis.

### Files Included

"""
        
        for format_name, file_path in exported_files.items():
            if format_name not in ['readme', 'archive']:
                if isinstance(file_path, Path):
                    if file_path.is_dir():
                        readme_content += f"- **{format_name}**: Directory `{file_path.name}/` - "
                    else:
                        readme_content += f"- **{format_name}**: `{file_path.name}` - "
                    
                    # Descripción por formato
                    descriptions = {
                        'csv': "Raw data in CSV format with metadata headers",
                        'json': "Structured JSON with hierarchical organization",
                        'latex': "Publication-ready LaTeX tables",
                        'excel': "Multi-sheet Excel workbook with analysis",
                        'metadata': "Complete experiment metadata in YAML",
                        'boxplots': "Algorithm performance distribution plots",
                        'heatmap': "Performance heatmap across instances",
                        'ranking': "Visual algorithm ranking"
                    }
                    readme_content += descriptions.get(format_name, "Export file") + "\n"
        
        readme_content += """
## Usage

### For Publication

1. LaTeX tables can be directly included in your paper:
   ```latex
   \\input{results_[timestamp]_latex/descriptive_stats.tex}
   ```

2. Plots are in PDF format, ready for inclusion in manuscripts

### For Analysis

1. Use the CSV or Excel files for further statistical analysis
2. JSON format preserves the complete hierarchical structure
3. All data includes metadata for full reproducibility

### Data Integrity

- Check `metadata.yaml` for data checksums
- All exports include timestamps and version information
- Results are traceable to original experiments

## Citation

If you use these results, please cite:

```bibtex
@software{bioalgocompare2024,
  title = {BioAlgoCompare: A Comprehensive Benchmarking Platform},
  year = {2024},
  version = {2.0}
}
```

## Contact

For questions about this export or the BioAlgoCompare platform,
please refer to the project documentation.
"""
        
        readme_path = export_dir / 'README.md'
        readme_path.write_text(readme_content)
        
        return readme_path
    
    def _create_archive(self, export_dir: Path, timestamp: str) -> Path:
        """Crea archivo ZIP con toda la exportación."""
        archive_path = self.output_dir / f"bioalgocompare_export_{timestamp}.zip"
        
        with zipfile.ZipFile(archive_path, 'w', zipfile.ZIP_DEFLATED) as zf:
            for file_path in export_dir.rglob('*'):
                if file_path.is_file():
                    arcname = file_path.relative_to(export_dir.parent)
                    zf.write(file_path, arcname)
        
        logger.info(f"Created archive: {archive_path}")
        return archive_path
    
    def export_for_conference(self, 
                             conference: str = 'cisti2025',
                             include_supplementary: bool = True) -> Dict[str, Path]:
        """
        Exportación especializada para conferencias específicas.
        
        Args:
            conference: Nombre de la conferencia
            include_supplementary: Si incluir material suplementario
            
        Returns:
            Dict con archivos generados
        """
        conference_configs = {
            'cisti2025': {
                'formats': ['latex', 'csv', 'json'],
                'latex_style': 'ieee',
                'include_plots': True,
                'supplementary': True
            },
            'gecco2025': {
                'formats': ['latex', 'excel'],
                'latex_style': 'acm',
                'include_plots': True,
                'supplementary': False
            },
            'default': {
                'formats': ['csv', 'json', 'latex'],
                'latex_style': 'ieee',
                'include_plots': True,
                'supplementary': True
            }
        }
        
        config = conference_configs.get(conference, conference_configs['default'])
        
        # Configurar exportador LaTeX con estilo apropiado
        self.exporters['latex'] = LaTeXExporter(style=config['latex_style'])
        
        # Ejecutar exportación
        files = self.export(
            formats=config['formats'],
            include_plots=config['include_plots'],
            create_archive=True
        )
        
        # Agregar material suplementario si se solicita
        if include_supplementary and config['supplementary']:
            supp_dir = Path(files.get('csv', files.get('json'))).parent / 'supplementary'
            supp_dir.mkdir(exist_ok=True)
            
            # Crear script de replicación
            replication_script = self._create_replication_script(supp_dir)
            files['replication_script'] = replication_script
            
            # Información de hardware/software
            env_info = self._create_environment_info(supp_dir)
            files['environment_info'] = env_info
        
        logger.info(f"Conference export for {conference} completed")
        return files
    
    def _create_replication_script(self, output_dir: Path) -> Path:
        """Crea script para replicar experimentos."""
        script_content = """#!/usr/bin/env python3
\"\"\"
Replication script for BioAlgoCompare experiments.
This script allows reproducing the exact experiments from the paper.
\"\"\"

import subprocess
import sys
from pathlib import Path

# Experiment configuration
ALGORITHMS = {algorithms}
INSTANCES = {instances}
RUNS = 30
ITERATIONS = 100
POPULATION_SIZE = 50

def run_experiment(algorithm, instance, seed):
    \"\"\"Run a single experiment.\"\"\"
    cmd = [
        'bioalgo', 'run',
        '--algorithm', algorithm,
        '--instance', instance,
        '--iterations', str(ITERATIONS),
        '--population', str(POPULATION_SIZE),
        '--seed', str(seed),
        '--save'
    ]
    
    print(f"Running: {algorithm} on {instance} (seed={seed})")
    result = subprocess.run(cmd, capture_output=True, text=True)
    
    if result.returncode != 0:
        print(f"Error: {result.stderr}")
        return False
    return True

def main():
    \"\"\"Run all experiments.\"\"\"
    print("BioAlgoCompare Replication Script")
    print("=" * 50)
    
    total_experiments = len(ALGORITHMS) * len(INSTANCES) * RUNS
    completed = 0
    
    for algorithm in ALGORITHMS:
        for instance in INSTANCES:
            for run in range(RUNS):
                seed = 42 + run  # Reproducible seeds
                
                if run_experiment(algorithm, instance, seed):
                    completed += 1
                    progress = (completed / total_experiments) * 100
                    print(f"Progress: {completed}/{total_experiments} ({progress:.1f}%)")
    
    print(f"\\nCompleted {completed} experiments")
    print("Results saved in current directory")

if __name__ == "__main__":
    main()
"""
        
        # Obtener listas de algoritmos e instancias
        data = self.load_results()
        algorithms = sorted(data['algorithm'].unique().tolist())
        instances = sorted(data['instance'].unique().tolist())
        
        script_content = script_content.format(
            algorithms=algorithms,
            instances=instances
        )
        
        script_path = output_dir / 'replicate_experiments.py'
        script_path.write_text(script_content)
        script_path.chmod(0o755)  # Hacer ejecutable
        
        return script_path
    
    def _create_environment_info(self, output_dir: Path) -> Path:
        """Crea información del entorno de ejecución."""
        import platform
        import importlib.metadata
        
        env_info = {
            'system': {
                'platform': platform.platform(),
                'python_version': platform.python_version(),
                'processor': platform.processor(),
                'machine': platform.machine()
            },
            'dependencies': {}
        }
        
        # Listar versiones de paquetes clave
        key_packages = [
            'numpy', 'pandas', 'scipy', 'matplotlib',
            'seaborn', 'networkx', 'scikit-learn'
        ]
        
        for package in key_packages:
            try:
                version = importlib.metadata.version(package)
                env_info['dependencies'][package] = version
            except:
                env_info['dependencies'][package] = 'Not installed'
        
        env_path = output_dir / 'environment_info.json'
        with open(env_path, 'w') as f:
            json.dump(env_info, f, indent=2)
        
        return env_path


def export_scientific_results(
    results_source: Union[str, Path, ResultsDatabase],
    output_dir: Optional[Path] = None,
    formats: Optional[List[str]] = None,
    conference: Optional[str] = None
) -> Dict[str, Path]:
    """
    Función de conveniencia para exportar resultados científicos.
    
    Args:
        results_source: Fuente de resultados
        output_dir: Directorio de salida
        formats: Formatos a exportar
        conference: Si exportar para conferencia específica
        
    Returns:
        Dict con archivos generados
    """
    pipeline = ScientificExportPipeline(results_source, output_dir)
    
    if conference:
        return pipeline.export_for_conference(conference)
    else:
        return pipeline.export(formats=formats)


if __name__ == "__main__":
    # Ejemplo de uso
    import argparse
    
    parser = argparse.ArgumentParser(description='Export scientific results')
    parser.add_argument('source', help='Results source (file, directory, or database)')
    parser.add_argument('--output', '-o', help='Output directory')
    parser.add_argument('--formats', '-f', nargs='+', 
                       choices=['csv', 'json', 'latex', 'excel'],
                       help='Export formats')
    parser.add_argument('--conference', '-c', help='Conference preset')
    
    args = parser.parse_args()
    
    files = export_scientific_results(
        args.source,
        args.output,
        args.formats,
        args.conference
    )
    
    print("\nExported files:")
    for name, path in files.items():
        print(f"  {name}: {path}")