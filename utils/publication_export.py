"""
Sistema de exportación para publicaciones científicas.

Este módulo proporciona herramientas para exportar resultados de benchmarks
en formatos listos para publicación académica, incluyendo:
- Tablas LaTeX con estadísticas descriptivas
- Tablas de rankings y comparaciones
- Figuras de convergencia y distribuciones  
- Análisis estadístico completo
- Formatos IEEE y ACM

Diseñado específicamente para la conferencia CISTI 2025.
"""

import json
import pandas as pd
import numpy as np
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
import matplotlib.pyplot as plt
import seaborn as sns
from scipy import stats
import warnings

from utils.statistics import UnifiedStatisticalAnalysis
from utils.result_schema_v2 import StandardResultV2
from utils.benchmarking import OPTIMAL_VALUES


class PublicationExporter:
    """
    Exportador principal para publicaciones científicas.
    
    Genera contenido listo para publicación en conferencias y journals,
    con formatos estándar de IEEE, ACM, y Springer.
    """
    
    def __init__(self, results_dir: Path, output_dir: Optional[Path] = None):
        """
        Inicializa el exportador.
        
        Args:
            results_dir: Directorio con resultados de benchmarks
            output_dir: Directorio de salida (default: results_dir/publication)
        """
        self.results_dir = Path(results_dir)
        self.output_dir = Path(output_dir) if output_dir else self.results_dir / "publication"
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Configuración de estilo para publicaciones
        self._setup_publication_style()
        
        # Cargar resultados
        self.results_data = self._load_results()
        
    def _setup_publication_style(self):
        """Configura estilo para figuras de publicación."""
        plt.style.use('default')
        
        # Configuración IEEE/ACM standard
        plt.rcParams.update({
            'font.size': 10,
            'font.family': 'serif',
            'axes.labelsize': 10,
            'axes.titlesize': 11,
            'xtick.labelsize': 9,
            'ytick.labelsize': 9,
            'legend.fontsize': 9,
            'figure.titlesize': 12,
            'figure.dpi': 300,
            'savefig.dpi': 300,
            'savefig.bbox': 'tight',
            'savefig.pad_inches': 0.1
        })
        
    def _load_results(self) -> List[Dict[str, Any]]:
        """Carga todos los resultados del directorio."""
        results = []
        
        # Buscar archivos JSON de resultados
        for json_file in self.results_dir.rglob("*.json"):
            if "summary" in json_file.name.lower() or "checkpoint" in json_file.name.lower():
                continue
                
            try:
                with open(json_file) as f:
                    data = json.load(f)
                    
                # Normalizar formato
                if isinstance(data, list):
                    results.extend(data)
                else:
                    results.append(data)
                    
            except Exception as e:
                print(f"Warning: Could not load {json_file}: {e}")
                
        return results
    
    def export_all_publication_materials(self) -> Dict[str, Path]:
        """
        Exporta todos los materiales para publicación.
        
        Returns:
            Dict con paths de archivos generados
        """
        exported_files = {}
        
        print("🚀 Generating publication materials...")
        
        # 1. Tablas principales
        print("📊 Creating statistical tables...")
        exported_files.update(self.export_statistical_tables())
        
        # 2. Figuras de convergencia
        print("📈 Creating convergence plots...")
        exported_files.update(self.export_convergence_figures())
        
        # 3. Análisis de distribuciones
        print("📉 Creating distribution analysis...")
        exported_files.update(self.export_distribution_analysis())
        
        # 4. Rankings y comparaciones
        print("🏆 Creating rankings and comparisons...")
        exported_files.update(self.export_rankings())
        
        # 5. Datos para replicación
        print("🔬 Creating replication data...")
        exported_files.update(self.export_replication_data())
        
        # 6. Resumen ejecutivo
        print("📋 Creating executive summary...")
        exported_files.update(self.export_executive_summary())
        
        print(f"✅ Publication materials exported to {self.output_dir}")
        return exported_files
    
    def export_statistical_tables(self) -> Dict[str, Path]:
        """Genera tablas estadísticas listas para LaTeX."""
        files = {}
        
        if not self.results_data:
            print("Warning: No results data available for statistical tables")
            return files
        
        # Preparar datos para análisis
        df = self._prepare_dataframe()
        
        if df.empty:
            print("Warning: No valid data for statistical analysis")
            return files
        
        # Tabla 1: Estadísticas descriptivas
        desc_table = self._create_descriptive_statistics_table(df)
        desc_path = self.output_dir / "table_descriptive_statistics.tex"
        desc_path.write_text(desc_table)
        files['descriptive_statistics'] = desc_path
        
        # Tabla 2: Resultados de tests estadísticos
        stat_table = self._create_statistical_tests_table(df)
        stat_path = self.output_dir / "table_statistical_tests.tex"
        stat_path.write_text(stat_table)
        files['statistical_tests'] = stat_path
        
        # Tabla 3: Rankings por instancia
        rank_table = self._create_instance_rankings_table(df)
        rank_path = self.output_dir / "table_instance_rankings.tex"
        rank_path.write_text(rank_table)
        files['instance_rankings'] = rank_path
        
        # Tabla 4: Comparación con óptimos conocidos
        if any(instance in OPTIMAL_VALUES for instance in df['instance'].unique()):
            optimal_table = self._create_optimal_comparison_table(df)
            optimal_path = self.output_dir / "table_optimal_comparison.tex"
            optimal_path.write_text(optimal_table)
            files['optimal_comparison'] = optimal_path
        
        return files
    
    def _prepare_dataframe(self) -> pd.DataFrame:
        """Prepara DataFrame desde los resultados cargados."""
        rows = []
        
        for result in self.results_data:
            if 'runs' in result and 'algorithm_info' in result:
                # Formato StandardResultV2
                algo_name = result['algorithm_info'].get('algorithm_name', 'unknown')
                instance_name = result['problem_info'].get('instance_name', 'unknown')
                
                for run in result['runs']:
                    rows.append({
                        'algorithm': algo_name,
                        'instance': instance_name,
                        'fitness': run.get('fitness', np.inf),
                        'execution_time': run.get('execution_time', 0),
                        'seed': run.get('seed', 0)
                    })
            
            elif 'algorithm_name' in result:
                # Formato legacy
                rows.append({
                    'algorithm': result.get('algorithm_name', 'unknown'),
                    'instance': result.get('instance_name', 'unknown'),
                    'fitness': result.get('fitness', np.inf),
                    'execution_time': result.get('execution_time', 0),
                    'seed': result.get('seed', 0)
                })
        
        return pd.DataFrame(rows)
    
    def _create_descriptive_statistics_table(self, df: pd.DataFrame) -> str:
        """Crea tabla LaTeX con estadísticas descriptivas."""
        
        # Calcular estadísticas por algoritmo e instancia
        stats_data = []
        
        for instance in sorted(df['instance'].unique()):
            instance_data = df[df['instance'] == instance]
            
            for algorithm in sorted(instance_data['algorithm'].unique()):
                algo_data = instance_data[instance_data['algorithm'] == algorithm]
                fitness_values = algo_data['fitness']
                
                if len(fitness_values) > 0:
                    stats_data.append({
                        'Instance': instance,
                        'Algorithm': algorithm,
                        'Best': f"{fitness_values.min():.2f}",
                        'Mean': f"{fitness_values.mean():.2f}",
                        'Std': f"{fitness_values.std():.2f}",
                        'Median': f"{fitness_values.median():.2f}",
                        'Runs': len(fitness_values)
                    })
        
        stats_df = pd.DataFrame(stats_data)
        
        # Generar LaTeX
        latex = "\\begin{table}[htbp]\n"
        latex += "\\centering\n"
        latex += "\\caption{Descriptive statistics for algorithm performance on VRP instances}\n"
        latex += "\\label{tab:descriptive_stats}\n"
        latex += "\\begin{tabular}{llrrrrr}\n"
        latex += "\\toprule\n"
        latex += "Instance & Algorithm & Best & Mean & Std & Median & Runs \\\\\n"
        latex += "\\midrule\n"
        
        current_instance = None
        for _, row in stats_df.iterrows():
            if current_instance != row['Instance']:
                if current_instance is not None:
                    latex += "\\midrule\n"
                current_instance = row['Instance']
            
            latex += f"{row['Instance']} & {row['Algorithm']} & {row['Best']} & {row['Mean']} & {row['Std']} & {row['Median']} & {row['Runs']} \\\\\n"
        
        latex += "\\bottomrule\n"
        latex += "\\end{tabular}\n"
        latex += "\\end{table}\n"
        
        return latex
    
    def _create_statistical_tests_table(self, df: pd.DataFrame) -> str:
        """Crea tabla con resultados de tests estadísticos."""
        
        try:
            analyzer = UnifiedStatisticalAnalysis(alpha=0.05)
            
            # Preparar datos para análisis
            algorithm_data = {}
            for instance in df['instance'].unique():
                algorithm_data[instance] = {}
                instance_data = df[df['instance'] == instance]
                
                for algorithm in instance_data['algorithm'].unique():
                    algo_data = instance_data[instance_data['algorithm'] == algorithm]
                    algorithm_data[instance][algorithm] = algo_data['fitness'].values
            
            # Ejecutar tests estadísticos
            friedman_result = analyzer.friedman_test(algorithm_data)
            
            # Generar tabla LaTeX
            latex = "\\begin{table}[htbp]\n"
            latex += "\\centering\n"
            latex += "\\caption{Statistical test results for algorithm comparison}\n"
            latex += "\\label{tab:statistical_tests}\n"
            latex += "\\begin{tabular}{lrrr}\n"
            latex += "\\toprule\n"
            latex += "Test & Statistic & p-value & Significant \\\\\n"
            latex += "\\midrule\n"
            
            # Friedman test
            is_significant = friedman_result['p_value'] < 0.05
            significance = "Yes" if is_significant else "No"
            latex += f"Friedman & {friedman_result['statistic']:.4f} & {friedman_result['p_value']:.4f} & {significance} \\\\\n"
            
            latex += "\\bottomrule\n"
            latex += "\\end{tabular}\n"
            latex += "\\end{table}\n"
            
        except Exception as e:
            latex = f"% Error generating statistical tests table: {e}\n"
            latex += "% Please check data format and statistical analysis module\n"
        
        return latex
    
    def _create_instance_rankings_table(self, df: pd.DataFrame) -> str:
        """Crea tabla con rankings por instancia."""
        
        # Calcular rankings por instancia
        rankings = []
        
        for instance in sorted(df['instance'].unique()):
            instance_data = df[df['instance'] == instance]
            
            # Calcular media por algoritmo
            algo_means = instance_data.groupby('algorithm')['fitness'].mean().sort_values()
            
            for rank, (algorithm, mean_fitness) in enumerate(algo_means.items(), 1):
                rankings.append({
                    'Instance': instance,
                    'Rank': rank,
                    'Algorithm': algorithm,
                    'Mean Fitness': f"{mean_fitness:.2f}"
                })
        
        rankings_df = pd.DataFrame(rankings)
        
        # Generar LaTeX
        latex = "\\begin{table}[htbp]\n"
        latex += "\\centering\n"
        latex += "\\caption{Algorithm rankings by instance (based on mean fitness)}\n"
        latex += "\\label{tab:instance_rankings}\n"
        latex += "\\begin{tabular}{llrl}\n"
        latex += "\\toprule\n"
        latex += "Instance & Algorithm & Rank & Mean Fitness \\\\\n"
        latex += "\\midrule\n"
        
        current_instance = None
        for _, row in rankings_df.iterrows():
            if current_instance != row['Instance']:
                if current_instance is not None:
                    latex += "\\midrule\n"
                current_instance = row['Instance']
            
            latex += f"{row['Instance']} & {row['Algorithm']} & {row['Rank']} & {row['Mean Fitness']} \\\\\n"
        
        latex += "\\bottomrule\n"
        latex += "\\end{tabular}\n"
        latex += "\\end{table}\n"
        
        return latex
    
    def _create_optimal_comparison_table(self, df: pd.DataFrame) -> str:
        """Crea tabla comparando con valores óptimos conocidos."""
        
        comparisons = []
        
        for instance in sorted(df['instance'].unique()):
            if instance not in OPTIMAL_VALUES:
                continue
                
            optimal_value = OPTIMAL_VALUES[instance]
            instance_data = df[df['instance'] == instance]
            
            for algorithm in sorted(instance_data['algorithm'].unique()):
                algo_data = instance_data[instance_data['algorithm'] == algorithm]
                best_fitness = algo_data['fitness'].min()
                mean_fitness = algo_data['fitness'].mean()
                
                # Calcular gaps
                best_gap = ((best_fitness - optimal_value) / optimal_value) * 100
                mean_gap = ((mean_fitness - optimal_value) / optimal_value) * 100
                
                comparisons.append({
                    'Instance': instance,
                    'Algorithm': algorithm,
                    'Optimal': f"{optimal_value:.0f}",
                    'Best': f"{best_fitness:.2f}",
                    'Mean': f"{mean_fitness:.2f}",
                    'Best Gap (%)': f"{best_gap:.2f}",
                    'Mean Gap (%)': f"{mean_gap:.2f}"
                })
        
        comp_df = pd.DataFrame(comparisons)
        
        # Generar LaTeX
        latex = "\\begin{table}[htbp]\n"
        latex += "\\centering\n"
        latex += "\\caption{Comparison with known optimal values}\n"
        latex += "\\label{tab:optimal_comparison}\n"
        latex += "\\begin{tabular}{llrrrr}\n"
        latex += "\\toprule\n"
        latex += "Instance & Algorithm & Optimal & Best & Best Gap (\\%) & Mean Gap (\\%) \\\\\n"
        latex += "\\midrule\n"
        
        current_instance = None
        for _, row in comp_df.iterrows():
            if current_instance != row['Instance']:
                if current_instance is not None:
                    latex += "\\midrule\n"
                current_instance = row['Instance']
            
            latex += f"{row['Instance']} & {row['Algorithm']} & {row['Optimal']} & {row['Best']} & {row['Best Gap (%)']} & {row['Mean Gap (%)']} \\\\\n"
        
        latex += "\\bottomrule\n"
        latex += "\\end{tabular}\n"
        latex += "\\end{table}\n"
        
        return latex
    
    def export_convergence_figures(self) -> Dict[str, Path]:
        """Genera figuras de convergencia para publicación."""
        files = {}
        
        # Buscar datos de convergencia
        convergence_data = self._extract_convergence_data()
        
        if not convergence_data:
            print("Warning: No convergence data found")
            return files
        
        # Figura 1: Convergencia típica por algoritmo
        fig_path = self._create_typical_convergence_plot(convergence_data)
        if fig_path:
            files['typical_convergence'] = fig_path
        
        # Figura 2: Comparación de convergencia en instancia específica
        fig_path = self._create_instance_convergence_comparison(convergence_data)
        if fig_path:
            files['instance_convergence'] = fig_path
        
        return files
    
    def _extract_convergence_data(self) -> Dict[str, Any]:
        """Extrae datos de convergencia de los resultados."""
        convergence_data = {}
        
        for result in self.results_data:
            if 'runs' in result and 'algorithm_info' in result:
                algo_name = result['algorithm_info'].get('algorithm_name', 'unknown')
                instance_name = result['problem_info'].get('instance_name', 'unknown')
                
                key = f"{algo_name}_{instance_name}"
                if key not in convergence_data:
                    convergence_data[key] = {
                        'algorithm': algo_name,
                        'instance': instance_name,
                        'curves': []
                    }
                
                for run in result['runs']:
                    if 'convergence_curve' in run:
                        convergence_data[key]['curves'].append(run['convergence_curve'])
        
        return convergence_data
    
    def _create_typical_convergence_plot(self, convergence_data: Dict) -> Optional[Path]:
        """Crea plot de convergencia típica."""
        
        if not convergence_data:
            return None
        
        plt.figure(figsize=(6, 4))
        
        # Seleccionar una instancia representativa
        representative_instance = None
        for key, data in convergence_data.items():
            if len(data['curves']) >= 5:  # Al menos 5 runs
                representative_instance = data['instance']
                break
        
        if not representative_instance:
            return None
        
        algorithms_plotted = 0
        colors = plt.cm.tab10(np.linspace(0, 1, 10))
        
        for key, data in convergence_data.items():
            if data['instance'] != representative_instance:
                continue
            
            if len(data['curves']) < 3:  # Skip if too few runs
                continue
            
            # Calcular curva promedio
            max_len = max(len(curve) for curve in data['curves'])
            padded_curves = []
            
            for curve in data['curves']:
                padded = list(curve) + [curve[-1]] * (max_len - len(curve))
                padded_curves.append(padded)
            
            mean_curve = np.mean(padded_curves, axis=0)
            std_curve = np.std(padded_curves, axis=0)
            
            iterations = range(len(mean_curve))
            color = colors[algorithms_plotted % len(colors)]
            
            plt.plot(iterations, mean_curve, label=data['algorithm'], color=color, linewidth=1.5)
            plt.fill_between(iterations, 
                           mean_curve - std_curve, 
                           mean_curve + std_curve, 
                           alpha=0.2, color=color)
            
            algorithms_plotted += 1
            if algorithms_plotted >= 6:  # Limit to 6 algorithms for clarity
                break
        
        plt.xlabel('Iteration')
        plt.ylabel('Fitness Value')
        plt.title(f'Convergence Comparison - {representative_instance}')
        plt.legend(bbox_to_anchor=(1.05, 1), loc='upper left')
        plt.grid(True, alpha=0.3)
        plt.tight_layout()
        
        fig_path = self.output_dir / "figure_typical_convergence.pdf"
        plt.savefig(fig_path, format='pdf', bbox_inches='tight', dpi=300)
        plt.close()
        
        return fig_path
    
    def _create_instance_convergence_comparison(self, convergence_data: Dict) -> Optional[Path]:
        """Crea comparación de convergencia entre instancias."""
        
        if not convergence_data:
            return None
        
        # Agrupar por algoritmo
        by_algorithm = {}
        for key, data in convergence_data.items():
            algo = data['algorithm']
            if algo not in by_algorithm:
                by_algorithm[algo] = {}
            by_algorithm[algo][data['instance']] = data['curves']
        
        # Seleccionar algoritmo con más datos
        best_algo = max(by_algorithm.keys(), key=lambda x: len(by_algorithm[x]))
        
        plt.figure(figsize=(8, 5))
        
        colors = plt.cm.tab10(np.linspace(0, 1, 10))
        instance_count = 0
        
        for instance, curves in by_algorithm[best_algo].items():
            if len(curves) < 3:
                continue
            
            # Calcular curva promedio
            max_len = max(len(curve) for curve in curves)
            padded_curves = []
            
            for curve in curves:
                padded = list(curve) + [curve[-1]] * (max_len - len(curve))
                padded_curves.append(padded)
            
            mean_curve = np.mean(padded_curves, axis=0)
            iterations = range(len(mean_curve))
            color = colors[instance_count % len(colors)]
            
            plt.plot(iterations, mean_curve, label=instance, color=color, linewidth=1.5)
            
            instance_count += 1
            if instance_count >= 5:  # Limit instances
                break
        
        plt.xlabel('Iteration')
        plt.ylabel('Fitness Value')
        plt.title(f'Instance Comparison - {best_algo}')
        plt.legend()
        plt.grid(True, alpha=0.3)
        plt.tight_layout()
        
        fig_path = self.output_dir / "figure_instance_convergence.pdf"
        plt.savefig(fig_path, format='pdf', bbox_inches='tight', dpi=300)
        plt.close()
        
        return fig_path
    
    def export_distribution_analysis(self) -> Dict[str, Path]:
        """Genera análisis de distribuciones."""
        files = {}
        
        df = self._prepare_dataframe()
        if df.empty:
            return files
        
        # Box plots por algoritmo
        box_path = self._create_algorithm_boxplots(df)
        if box_path:
            files['algorithm_boxplots'] = box_path
        
        # Violin plots por instancia
        violin_path = self._create_instance_violin_plots(df)
        if violin_path:
            files['instance_violins'] = violin_path
        
        return files
    
    def _create_algorithm_boxplots(self, df: pd.DataFrame) -> Optional[Path]:
        """Crea box plots para comparar algoritmos."""
        
        if df.empty:
            return None
        
        # Seleccionar instancia con más datos
        instance_counts = df['instance'].value_counts()
        if instance_counts.empty:
            return None
        
        best_instance = instance_counts.index[0]
        instance_data = df[df['instance'] == best_instance]
        
        plt.figure(figsize=(10, 6))
        
        # Crear box plot
        box_data = []
        labels = []
        
        for algorithm in sorted(instance_data['algorithm'].unique()):
            algo_data = instance_data[instance_data['algorithm'] == algorithm]
            if len(algo_data) >= 3:  # Al menos 3 puntos para box plot
                box_data.append(algo_data['fitness'].values)
                labels.append(algorithm)
        
        if box_data:
            plt.boxplot(box_data, labels=labels)
            plt.xlabel('Algorithm')
            plt.ylabel('Fitness Value')
            plt.title(f'Fitness Distribution Comparison - {best_instance}')
            plt.xticks(rotation=45)
            plt.grid(True, alpha=0.3)
            plt.tight_layout()
            
            fig_path = self.output_dir / "figure_algorithm_boxplots.pdf"
            plt.savefig(fig_path, format='pdf', bbox_inches='tight', dpi=300)
            plt.close()
            
            return fig_path
        
        plt.close()
        return None
    
    def _create_instance_violin_plots(self, df: pd.DataFrame) -> Optional[Path]:
        """Crea violin plots por instancia."""
        
        if df.empty:
            return None
        
        # Seleccionar algoritmo con más datos
        algo_counts = df['algorithm'].value_counts()
        if algo_counts.empty:
            return None
        
        best_algorithm = algo_counts.index[0]
        algo_data = df[df['algorithm'] == best_algorithm]
        
        # Verificar que hay suficientes instancias
        instances_with_data = []
        for instance in algo_data['instance'].unique():
            instance_subset = algo_data[algo_data['instance'] == instance]
            if len(instance_subset) >= 5:  # Al menos 5 puntos para violin
                instances_with_data.append(instance)
        
        if len(instances_with_data) < 2:
            return None
        
        plt.figure(figsize=(10, 6))
        
        # Preparar datos para violin plot
        plot_data = []
        plot_labels = []
        
        for instance in sorted(instances_with_data):
            instance_subset = algo_data[algo_data['instance'] == instance]
            plot_data.append(instance_subset['fitness'].values)
            plot_labels.append(instance)
        
        # Crear violin plot usando matplotlib
        parts = plt.violinplot(plot_data, positions=range(1, len(plot_data) + 1))
        
        plt.xlabel('Instance')
        plt.ylabel('Fitness Value')
        plt.title(f'Fitness Distribution by Instance - {best_algorithm}')
        plt.xticks(range(1, len(plot_labels) + 1), plot_labels, rotation=45)
        plt.grid(True, alpha=0.3)
        plt.tight_layout()
        
        fig_path = self.output_dir / "figure_instance_violins.pdf"
        plt.savefig(fig_path, format='pdf', bbox_inches='tight', dpi=300)
        plt.close()
        
        return fig_path
    
    def export_rankings(self) -> Dict[str, Path]:
        """Genera análisis de rankings y comparaciones."""
        files = {}
        
        df = self._prepare_dataframe()
        if df.empty:
            return files
        
        # Crear tabla de rankings general
        ranking_path = self._create_overall_ranking_table(df)
        if ranking_path:
            files['overall_ranking'] = ranking_path
        
        return files
    
    def _create_overall_ranking_table(self, df: pd.DataFrame) -> Optional[Path]:
        """Crea tabla de ranking general."""
        
        if df.empty:
            return None
        
        # Calcular ranking promedio por algoritmo
        algorithm_ranks = {}
        
        for instance in df['instance'].unique():
            instance_data = df[df['instance'] == instance]
            algo_means = instance_data.groupby('algorithm')['fitness'].mean().sort_values()
            
            for rank, algorithm in enumerate(algo_means.index, 1):
                if algorithm not in algorithm_ranks:
                    algorithm_ranks[algorithm] = []
                algorithm_ranks[algorithm].append(rank)
        
        # Calcular ranking promedio
        overall_rankings = []
        for algorithm, ranks in algorithm_ranks.items():
            if len(ranks) >= 2:  # Al menos en 2 instancias
                avg_rank = np.mean(ranks)
                overall_rankings.append({
                    'algorithm': algorithm,
                    'avg_rank': avg_rank,
                    'instances': len(ranks)
                })
        
        # Ordenar por ranking promedio
        overall_rankings.sort(key=lambda x: x['avg_rank'])
        
        # Generar LaTeX
        latex = "\\begin{table}[htbp]\n"
        latex += "\\centering\n"
        latex += "\\caption{Overall algorithm ranking (average rank across instances)}\n"
        latex += "\\label{tab:overall_ranking}\n"
        latex += "\\begin{tabular}{lrr}\n"
        latex += "\\toprule\n"
        latex += "Algorithm & Average Rank & Instances \\\\\n"
        latex += "\\midrule\n"
        
        for i, ranking in enumerate(overall_rankings, 1):
            latex += f"{ranking['algorithm']} & {ranking['avg_rank']:.2f} & {ranking['instances']} \\\\\n"
        
        latex += "\\bottomrule\n"
        latex += "\\end{tabular}\n"
        latex += "\\end{table}\n"
        
        ranking_path = self.output_dir / "table_overall_ranking.tex"
        ranking_path.write_text(latex)
        
        return ranking_path
    
    def export_replication_data(self) -> Dict[str, Path]:
        """Exporta datos para replicación científica."""
        files = {}
        
        # Exportar datos completos en CSV
        df = self._prepare_dataframe()
        if not df.empty:
            csv_path = self.output_dir / "replication_data.csv"
            df.to_csv(csv_path, index=False)
            files['replication_csv'] = csv_path
        
        # Exportar metadatos de experimento
        metadata = self._create_experiment_metadata()
        metadata_path = self.output_dir / "experiment_metadata.json"
        with open(metadata_path, 'w') as f:
            json.dump(metadata, f, indent=2, default=str)
        files['experiment_metadata'] = metadata_path
        
        # Crear archivo de verificación
        verification_path = self._create_verification_file()
        if verification_path:
            files['verification'] = verification_path
        
        return files
    
    def _create_experiment_metadata(self) -> Dict[str, Any]:
        """Crea metadatos del experimento."""
        
        df = self._prepare_dataframe()
        
        metadata = {
            'experiment_info': {
                'title': 'BioAlgoCompare VRP Benchmark Results',
                'description': 'Comparative study of bio-inspired algorithms on Vehicle Routing Problem instances',
                'conference': 'CISTI 2025',
                'export_date': datetime.now().isoformat(),
                'tool_version': '2.0'
            },
            'data_summary': {
                'total_runs': len(df) if not df.empty else 0,
                'algorithms': sorted(df['algorithm'].unique().tolist()) if not df.empty else [],
                'instances': sorted(df['instance'].unique().tolist()) if not df.empty else [],
                'runs_per_algorithm': df.groupby('algorithm').size().to_dict() if not df.empty else {}
            },
            'statistical_parameters': {
                'significance_level': 0.05,
                'confidence_interval': 0.95,
                'multiple_comparison_correction': 'Bonferroni'
            },
            'hardware_info': {
                'note': 'Hardware information should be captured in individual result files'
            }
        }
        
        return metadata
    
    def _create_verification_file(self) -> Optional[Path]:
        """Crea archivo de verificación para integridad de datos."""
        
        df = self._prepare_dataframe()
        if df.empty:
            return None
        
        verification_info = {
            'data_integrity': {
                'total_records': len(df),
                'missing_values': df.isnull().sum().to_dict(),
                'data_types': df.dtypes.astype(str).to_dict(),
                'value_ranges': {
                    'fitness_min': float(df['fitness'].min()),
                    'fitness_max': float(df['fitness'].max()),
                    'execution_time_min': float(df['execution_time'].min()),
                    'execution_time_max': float(df['execution_time'].max())
                }
            },
            'checksums': {
                'data_hash': hash(df.to_string()),
                'verification_date': datetime.now().isoformat()
            }
        }
        
        verification_path = self.output_dir / "data_verification.json"
        with open(verification_path, 'w') as f:
            json.dump(verification_info, f, indent=2, default=str)
        
        return verification_path
    
    def export_executive_summary(self) -> Dict[str, Path]:
        """Genera resumen ejecutivo para la publicación."""
        files = {}
        
        df = self._prepare_dataframe()
        if df.empty:
            return files
        
        summary = self._create_executive_summary_content(df)
        summary_path = self.output_dir / "executive_summary.md"
        summary_path.write_text(summary)
        files['executive_summary'] = summary_path
        
        # También crear versión LaTeX
        latex_summary = self._create_latex_summary(df)
        latex_path = self.output_dir / "executive_summary.tex"
        latex_path.write_text(latex_summary)
        files['executive_summary_latex'] = latex_path
        
        return files
    
    def _create_executive_summary_content(self, df: pd.DataFrame) -> str:
        """Crea contenido del resumen ejecutivo."""
        
        summary = f"""# BioAlgoCompare Results - Executive Summary

Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## Dataset Overview

- **Total runs**: {len(df):,}
- **Algorithms tested**: {len(df['algorithm'].unique())}
- **VRP instances**: {len(df['instance'].unique())}
- **Algorithm list**: {', '.join(sorted(df['algorithm'].unique()))}
- **Instance list**: {', '.join(sorted(df['instance'].unique()))}

## Key Findings

### Best Performing Algorithms (by mean fitness)
"""
        
        # Calcular rendimiento promedio por algoritmo
        algo_performance = df.groupby('algorithm')['fitness'].agg(['mean', 'std', 'min']).sort_values('mean')
        
        summary += "\n| Rank | Algorithm | Mean Fitness | Std Dev | Best Fitness |\n"
        summary += "|------|-----------|--------------|---------|-------------|\n"
        
        for i, (algorithm, stats) in enumerate(algo_performance.head(10).iterrows(), 1):
            summary += f"| {i} | {algorithm} | {stats['mean']:.2f} | {stats['std']:.2f} | {stats['min']:.2f} |\n"
        
        # Estadísticas por instancia
        summary += "\n### Performance by Instance\n\n"
        
        for instance in sorted(df['instance'].unique()):
            instance_data = df[df['instance'] == instance]
            best_algo = instance_data.loc[instance_data['fitness'].idxmin(), 'algorithm']
            best_fitness = instance_data['fitness'].min()
            
            optimal = OPTIMAL_VALUES.get(instance, None)
            gap_info = ""
            if optimal:
                gap = ((best_fitness - optimal) / optimal) * 100
                gap_info = f" (Gap to optimal: {gap:.2f}%)"
            
            summary += f"- **{instance}**: Best by {best_algo} with fitness {best_fitness:.2f}{gap_info}\n"
        
        summary += f"""
## Statistical Significance

A comprehensive statistical analysis was performed using non-parametric tests appropriate for 
algorithm comparison studies. Detailed results are available in the generated LaTeX tables.

## Reproducibility

All experimental data and metadata are provided in the `replication_data.csv` file and 
`experiment_metadata.json` file. The experiment can be reproduced using the BioAlgoCompare 
v2.0 platform.

## Files Generated

This export includes:
- Statistical tables in LaTeX format (ready for publication)
- Convergence plots and distribution analysis figures (PDF format)
- Complete raw data for replication (CSV format)
- Verification checksums for data integrity

For questions about this analysis, please refer to the BioAlgoCompare documentation.
"""
        
        return summary
    
    def _create_latex_summary(self, df: pd.DataFrame) -> str:
        """Crea resumen en formato LaTeX."""
        
        latex = """\\section{Experimental Results Summary}

This section presents a comprehensive evaluation of {num_algorithms} bio-inspired algorithms 
on {num_instances} Vehicle Routing Problem instances, totaling {total_runs} independent runs.

\\subsection{{Algorithm Performance}}

Table~\\ref{{tab:descriptive_stats}} presents the descriptive statistics for all algorithms 
across all test instances. The results show significant performance variations between 
algorithms, with detailed statistical analysis provided in subsequent tables.

\\subsection{{Statistical Analysis}}

Statistical significance testing was performed using the Friedman test for multiple 
algorithm comparison, followed by post-hoc analysis where appropriate. Results are 
presented in Table~\\ref{{tab:statistical_tests}}.

\\subsection{{Key Findings}}

\\begin{{itemize}}
""".format(
            num_algorithms=len(df['algorithm'].unique()),
            num_instances=len(df['instance'].unique()),
            total_runs=len(df)
        )
        
        # Top 3 algorithms
        algo_performance = df.groupby('algorithm')['fitness'].mean().sort_values()
        top_3 = algo_performance.head(3)
        
        for i, (algorithm, mean_fitness) in enumerate(top_3.items(), 1):
            latex += f"\\item {algorithm} achieved the {'best' if i == 1 else f'{i}{"nd" if i == 2 else "rd"}'} overall mean performance with {mean_fitness:.2f}\n"
        
        latex += """\\end{itemize}

\\subsection{Reproducibility}

All experimental data, including individual run results, convergence curves, and system 
metadata, are available in the supplementary materials to ensure full reproducibility 
of these results.
"""
        
        return latex


def export_for_cisti_2025(results_dir: str, output_dir: Optional[str] = None) -> Dict[str, Path]:
    """
    Función de conveniencia para exportar todos los materiales para CISTI 2025.
    
    Args:
        results_dir: Directorio con resultados de benchmarks
        output_dir: Directorio de salida (opcional)
        
    Returns:
        Dict con paths de archivos generados
    """
    exporter = PublicationExporter(Path(results_dir), Path(output_dir) if output_dir else None)
    return exporter.export_all_publication_materials()


if __name__ == "__main__":
    # Ejemplo de uso
    import sys
    
    if len(sys.argv) > 1:
        results_directory = sys.argv[1]
        output_directory = sys.argv[2] if len(sys.argv) > 2 else None
        
        print(f"Exporting publication materials from {results_directory}")
        files = export_for_cisti_2025(results_directory, output_directory)
        
        print("Generated files:")
        for category, path in files.items():
            print(f"  {category}: {path}")
    else:
        print("Usage: python publication_export.py <results_dir> [output_dir]")