#!/usr/bin/env python3
"""
Script para análisis global de resultados de múltiples benchmarks VRP.
Consolida, analiza y genera visualizaciones comparativas de algoritmos metaheurísticos.
"""

import os
import glob
import json
import click
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime
from scipy import stats
import scikit_posthocs as sp
from math import sqrt

# Configuración de visualización
plt.style.use('seaborn-v0_8-darkgrid')
sns.set_context("paper", font_scale=1.2)
colors = sns.color_palette("viridis", 11)  # Colores para 11 algoritmos

# Constantes
ALGORITHM_NAMES = {
    'hho': 'Harris Hawks Optimization',
    'woa': 'Whale Optimization Algorithm',
    'ewa': 'Earthworm Algorithm',
    'sma': 'Slime Mould Algorithm',
    'mrfo': 'Manta Ray Foraging Optimization',
    'gto': 'Gorilla Troops Optimizer',
    'egto': 'Enhanced Gorilla Troops Optimizer',
    'foa': 'Fossa Optimization Algorithm',
    'fsa': 'Flamingo Search Algorithm',
    'sho': 'Spotted Hyena Optimizer',
    'apo': 'Artificial Protozoa Optimizer'
}

INSTANCE_DETAILS = {
    'P-n16-k8': {'nodes': 16, 'vehicles': 8, 'optimal': 450},
    'E-n22-k4': {'nodes': 22, 'vehicles': 4, 'optimal': 375},
    'M-n151-k12': {'nodes': 151, 'vehicles': 12, 'optimal': 1015}
}

def load_benchmark_results(input_dir):
    """
    Carga resultados de todos los archivos benchmark_results.json en el directorio.
    
    Args:
        input_dir: Directorio o patrón glob para buscar archivos de resultados
        
    Returns:
        DataFrame consolidado con todos los resultados
    """
    all_results = []
    
    # Buscar todos los archivos benchmark_results.json
    if os.path.isdir(input_dir):
        result_files = glob.glob(os.path.join(input_dir, "**/benchmark_results.json"), recursive=True)
    else:
        result_files = glob.glob(input_dir)
    
    if not result_files:
        raise ValueError(f"No se encontraron archivos benchmark_results.json en {input_dir}")
    
    print(f"Encontrados {len(result_files)} archivos de resultados")
    
    # Cargar y procesar cada archivo
    for file_path in result_files:
        try:
            with open(file_path, 'r') as f:
                results = json.load(f)
                
            for result in results:
                algorithm = result['algorithm'].lower()
                instance = result['instance']
                
                # Extraer métricas principales
                metrics = {
                    'algorithm': algorithm,
                    'instance': instance,
                    'best_fitness': result['metrics']['best_fitness'],
                    'worst_fitness': result['metrics']['worst_fitness'],
                    'mean_fitness': result['metrics']['mean_fitness'],
                    'std_fitness': result['metrics']['std_fitness'],
                    'mean_time': result['metrics']['mean_time'],
                    'std_time': result['metrics']['std_time'],
                    'gap_to_optimal': result['metrics']['gap_to_optimal'],
                    'success_rate': result['metrics']['success_rate'],
                    'runs': result['runs'],
                    'optimal_value': result['optimal_value'],
                    'source_file': os.path.basename(file_path)
                }
                
                # Añadir cada ejecución individual para análisis detallado
                if 'detailed_results' in result:
                    for i, (fitness, time) in enumerate(zip(
                            result['detailed_results']['fitness_values'],
                            result['detailed_results']['execution_times'])):
                        run_data = metrics.copy()
                        run_data['run_id'] = i + 1
                        run_data['fitness'] = fitness
                        run_data['time'] = time
                        all_results.append(run_data)
        except Exception as e:
            print(f"Error al procesar {file_path}: {str(e)}")
    
    # Crear DataFrame
    if all_results:
        df = pd.DataFrame(all_results)
        print(f"Datos cargados: {len(df)} filas con {df['algorithm'].nunique()} algoritmos y {df['instance'].nunique()} instancias")
        return df
    else:
        raise ValueError("No se pudieron cargar datos de los archivos de resultados")

def generate_summary(df):
    """
    Genera un DataFrame de resumen con métricas agregadas por algoritmo e instancia.
    
    Args:
        df: DataFrame con datos detallados de ejecuciones
        
    Returns:
        DataFrame con métricas resumidas
    """
    # Agrupar por algoritmo e instancia
    summary = df.groupby(['algorithm', 'instance']).agg({
        'fitness': ['min', 'mean', 'max', 'std', 'count'],
        'time': ['mean', 'std'],
        'optimal_value': 'first'
    }).reset_index()
    
    # Aplanar la estructura MultiIndex de las columnas
    summary.columns = ['_'.join(col).strip('_') for col in summary.columns.values]
    
    # Calcular gap al óptimo
    summary['gap_percent'] = 100 * (summary['fitness_mean'] - summary['optimal_value_first']) / summary['optimal_value_first']
    
    # Ordenar por instancia y gap
    summary = summary.sort_values(['instance', 'gap_percent'])
    
    return summary

def generate_confidence_intervals(df):
    """
    Genera intervalos de confianza del 95% para el fitness.
    
    Args:
        df: DataFrame con datos detallados de ejecuciones
        
    Returns:
        DataFrame con intervalos de confianza
    """
    # Agrupar por algoritmo e instancia
    grouped = df.groupby(['algorithm', 'instance'])
    
    ci_data = []
    
    for (algo, inst), group in grouped:
        mean = group['fitness'].mean()
        std = group['fitness'].std()
        n = len(group)
        
        # Error estándar de la media
        se = std / sqrt(n)
        
        # Intervalo de confianza del 95% (distribución t)
        t_value = stats.t.ppf(0.975, n-1)  # Valor crítico para 95%
        margin = t_value * se
        
        ci_lower = mean - margin
        ci_upper = mean + margin
        
        ci_data.append({
            'algorithm': algo,
            'instance': inst,
            'mean_fitness': mean,
            'ci_lower': ci_lower,
            'ci_upper': ci_upper,
            'margin': margin,
            'n': n
        })
    
    return pd.DataFrame(ci_data)

def run_statistical_tests(df):
    """
    Ejecuta pruebas estadísticas (Friedman, Wilcoxon, etc.) sobre los resultados.
    
    Args:
        df: DataFrame con datos detallados de ejecuciones
        
    Returns:
        Diccionario con resultados de las pruebas
    """
    results = {}
    
    # Obtener las instancias únicas
    instances = df['instance'].unique()
    
    for instance in instances:
        inst_df = df[df['instance'] == instance]
        
        # Preparar datos para test de Friedman
        algorithms = inst_df['algorithm'].unique()
        
        # Verificar que tenemos suficientes datos
        if len(algorithms) < 2:
            print(f"Instancia {instance}: Se requieren al menos 2 algoritmos para análisis estadístico")
            continue
        
        # Matriz de resultados por algoritmo y ejecución
        pivot_df = inst_df.pivot_table(
            index='run_id',
            columns='algorithm',
            values='fitness',
            aggfunc='first'
        )
        
        # Prueba de Friedman
        try:
            friedman_result = stats.friedmanchisquare(*(pivot_df[algo].dropna() for algo in algorithms))
            
            results[instance] = {
                'friedman_statistic': friedman_result.statistic,
                'friedman_pvalue': friedman_result.pvalue,
                'reject_h0': friedman_result.pvalue < 0.05
            }
            
            # Si rechazamos H0, realizamos pruebas post-hoc
            if friedman_result.pvalue < 0.05:
                # Wilcoxon pareado con corrección de Bonferroni
                p_values = {}
                for i, algo1 in enumerate(algorithms):
                    for algo2 in algorithms[i+1:]:
                        data1 = pivot_df[algo1].dropna()
                        data2 = pivot_df[algo2].dropna()
                        
                        # Asegurar longitud igual (tomar min)
                        min_len = min(len(data1), len(data2))
                        data1 = data1.iloc[:min_len]
                        data2 = data2.iloc[:min_len]
                        
                        if len(data1) >= 5:  # Mínimo recomendado para Wilcoxon
                            wilcoxon_result = stats.wilcoxon(data1, data2)
                            p_values[f"{algo1}_vs_{algo2}"] = wilcoxon_result.pvalue
                
                results[instance]['pairwise_tests'] = p_values
                
                # Nemenyi post-hoc test (usando scikit_posthocs)
                try:
                    posthoc = sp.posthoc_nemenyi_friedman(pivot_df)
                    results[instance]['nemenyi_matrix'] = posthoc.to_dict()
                except Exception as e:
                    print(f"Error en test de Nemenyi para {instance}: {str(e)}")
        
        except Exception as e:
            print(f"Error en pruebas estadísticas para {instance}: {str(e)}")
    
    return results

def generate_plots(df, summary_df, ci_df, stats_results, output_dir):
    """
    Genera gráficas comparativas de los algoritmos.
    
    Args:
        df: DataFrame con datos detallados
        summary_df: DataFrame de resumen
        ci_df: DataFrame con intervalos de confianza
        stats_results: Resultados de pruebas estadísticas
        output_dir: Directorio para guardar gráficas
    """
    # Crear directorio para gráficas
    figures_dir = os.path.join(output_dir, 'figures')
    os.makedirs(figures_dir, exist_ok=True)
    
    # 1. Gráficas de caja por instancia
    instances = df['instance'].unique()
    algorithms = df['algorithm'].unique()
    
    for instance in instances:
        plt.figure(figsize=(12, 8))
        inst_df = df[df['instance'] == instance]
        
        # Ordenar algoritmos por mediana de fitness
        algo_order = inst_df.groupby('algorithm')['fitness'].median().sort_values().index
        
        sns.boxplot(data=inst_df, x='algorithm', y='fitness', order=algo_order, palette=colors[:len(algo_order)])
        plt.title(f'Comparación de fitness para instancia {instance}')
        plt.xlabel('Algoritmo')
        plt.ylabel('Fitness (menor es mejor)')
        plt.xticks(rotation=45)
        plt.tight_layout()
        plt.savefig(os.path.join(figures_dir, f'{instance}_boxplot.png'), dpi=300)
        plt.close()
        
        # Gráfica de tiempos
        plt.figure(figsize=(12, 8))
        sns.boxplot(data=inst_df, x='algorithm', y='time', order=algo_order, palette=colors[:len(algo_order)])
        plt.title(f'Comparación de tiempos para instancia {instance}')
        plt.xlabel('Algoritmo')
        plt.ylabel('Tiempo (s)')
        plt.xticks(rotation=45)
        plt.tight_layout()
        plt.savefig(os.path.join(figures_dir, f'{instance}_time_boxplot.png'), dpi=300)
        plt.close()
    
    # 2. Gráfica de barras con intervalos de confianza
    for instance in instances:
        plt.figure(figsize=(12, 8))
        inst_ci = ci_df[ci_df['instance'] == instance]
        
        # Ordenar por fitness medio
        inst_ci = inst_ci.sort_values('mean_fitness')
        
        plt.errorbar(
            x=range(len(inst_ci)), 
            y=inst_ci['mean_fitness'],
            yerr=inst_ci['margin'],
            fmt='o',
            capsize=5,
            capthick=2,
            ecolor='red',
            markersize=8
        )
        
        plt.xticks(range(len(inst_ci)), inst_ci['algorithm'], rotation=45)
        plt.title(f'Fitness medio con IC-95% para instancia {instance}')
        plt.ylabel('Fitness (menor es mejor)')
        plt.grid(True, linestyle='--', alpha=0.7)
        plt.tight_layout()
        plt.savefig(os.path.join(figures_dir, f'{instance}_ci_errorbar.png'), dpi=300)
        plt.close()
    
    # 3. Mapa de calor para p-values de comparaciones pareadas
    for instance, stats in stats_results.items():
        if 'nemenyi_matrix' in stats:
            plt.figure(figsize=(10, 8))
            
            matrix_data = pd.DataFrame(stats['nemenyi_matrix'])
            mask = np.triu(np.ones_like(matrix_data, dtype=bool))
            
            sns.heatmap(
                matrix_data,
                annot=True,
                mask=mask,
                cmap='viridis_r',
                vmin=0,
                vmax=0.05,
                cbar_kws={'label': 'p-value (< 0.05 es significativo)'}
            )
            
            plt.title(f'Matriz de p-values (Nemenyi) para {instance}')
            plt.tight_layout()
            plt.savefig(os.path.join(figures_dir, f'{instance}_pvalues_heatmap.png'), dpi=300)
            plt.close()
    
    # 4. Gráfica comparativa de gap al óptimo
    plt.figure(figsize=(12, 8))
    
    # Para cada instancia, crear grupos de barras
    instance_groups = []
    for i, instance in enumerate(instances):
        inst_summary = summary_df[summary_df['instance'] == instance]
        inst_summary = inst_summary.sort_values('gap_percent')
        
        # Posiciones de las barras para esta instancia
        group_size = len(inst_summary)
        width = 0.8 / group_size
        offsets = [j - (group_size-1)/2 * width for j in range(group_size)]
        
        for j, (_, row) in enumerate(inst_summary.iterrows()):
            plt.bar(
                i + offsets[j],
                row['gap_percent'],
                width=width,
                label=row['algorithm'] if i == 0 and j < len(algorithms) else "",
                color=colors[j % len(colors)]
            )
    
    plt.axhline(y=0, color='black', linestyle='-', alpha=0.3)
    plt.xticks(range(len(instances)), instances)
    plt.xlabel('Instancia')
    plt.ylabel('Gap al óptimo (%)')
    plt.title('Comparación de gap al óptimo por instancia')
    
    # Añadir leyenda solo para los algoritmos
    handles, labels = plt.gca().get_legend_handles_labels()
    unique_algorithms = summary_df['algorithm'].unique()
    unique_handles = [handles[labels.index(algo)] for algo in unique_algorithms if algo in labels]
    unique_labels = [algo for algo in unique_algorithms if algo in labels]
    
    plt.legend(unique_handles, unique_labels, loc='upper center', bbox_to_anchor=(0.5, -0.05), ncol=5)
    
    plt.tight_layout()
    plt.savefig(os.path.join(figures_dir, 'gap_comparison.png'), dpi=300)
    plt.close()

def generate_markdown_table(summary_df, output_file):
    """
    Genera una tabla en formato Markdown con los resultados.
    
    Args:
        summary_df: DataFrame de resumen
        output_file: Ruta al archivo markdown de salida
    """
    # Agrupar por algoritmo
    algo_summary = summary_df.groupby('algorithm').agg({
        'gap_percent': ['mean', 'std'],
        'fitness_mean': ['mean', 'std'],
        'time_mean': ['mean', 'std'],
        'fitness_min': 'min',
        'gap_percent': 'min'
    }).reset_index()
    
    # Aplanar la estructura MultiIndex de las columnas
    algo_summary.columns = ['_'.join(col).strip('_') for col in algo_summary.columns.values]
    
    # Ordenar por gap promedio
    algo_summary = algo_summary.sort_values('gap_percent_mean')
    
    # Crear tabla markdown
    markdown = "# Comparativa Global de Algoritmos Metaheurísticos para VRP\n\n"
    markdown += f"*Generado el {datetime.now().strftime('%d-%m-%Y %H:%M:%S')}*\n\n"
    
    markdown += "## Configuración Experimental\n\n"
    markdown += "- **Instancias evaluadas:** "
    markdown += ", ".join([f"{inst} ({INSTANCE_DETAILS.get(inst, {}).get('nodes', 'N/A')} nodos, {INSTANCE_DETAILS.get(inst, {}).get('vehicles', 'N/A')} vehículos)" 
                          for inst in summary_df['instance'].unique()])
    markdown += "\n"
    
    markdown += "- **Algoritmos evaluados:** "
    markdown += ", ".join([f"{algo.upper()} ({ALGORITHM_NAMES.get(algo, algo)})" for algo in algo_summary['algorithm_']])
    markdown += "\n"
    
    markdown += "- **Ejecuciones por algoritmo/instancia:** "
    markdown += f"{summary_df['fitness_count'].values[0]}\n\n"
    
    markdown += "## Tabla Comparativa Global\n\n"
    
    # Cabecera de la tabla
    markdown += "| Ranking | Algoritmo | Mejor Gap (%) | Gap Promedio (%) | σ Gap | Tiempo Promedio (s) | σ Tiempo |\n"
    markdown += "|---------|-----------|---------------|------------------|-------|---------------------|----------|\n"
    
    # Filas de la tabla
    for i, (_, row) in enumerate(algo_summary.iterrows()):
        algorithm = row['algorithm_']
        markdown += f"| {i+1} | {algorithm.upper()} | "
        markdown += f"{row['gap_percent_min']:.2f} | "
        markdown += f"{row['gap_percent_mean']:.2f} | "
        markdown += f"{row['gap_percent_std']:.2f} | "
        markdown += f"{row['time_mean_mean']:.4f} | "
        markdown += f"{row['time_mean_std']:.4f} |\n"
    
    markdown += "\n## Detalles por Instancia\n\n"
    
    for instance in summary_df['instance'].unique():
        markdown += f"### Instancia {instance}\n\n"
        
        inst_summary = summary_df[summary_df['instance'] == instance].sort_values('gap_percent')
        
        # Cabecera de la tabla
        markdown += "| Algoritmo | Mejor Fitness | Fitness Promedio | σ Fitness | Gap (%) | Tiempo (s) |\n"
        markdown += "|-----------|---------------|------------------|-----------|---------|------------|\n"
        
        # Filas de la tabla
        for _, row in inst_summary.iterrows():
            markdown += f"| {row['algorithm'].upper()} | "
            markdown += f"{row['fitness_min']:.2f} | "
            markdown += f"{row['fitness_mean']:.2f} | "
            markdown += f"{row['fitness_std']:.2f} | "
            markdown += f"{row['gap_percent']:.2f} | "
            markdown += f"{row['time_mean']:.4f} |\n"
        
        markdown += "\n"
    
    # Sección de visualizaciones
    markdown += "## Visualizaciones\n\n"
    
    for instance in summary_df['instance'].unique():
        markdown += f"### {instance}\n\n"
        
        markdown += f"![Boxplot de fitness para {instance}](figures/{instance}_boxplot.png)\n\n"
        markdown += f"![Tiempos de ejecución para {instance}](figures/{instance}_time_boxplot.png)\n\n"
        markdown += f"![Intervalos de confianza para {instance}](figures/{instance}_ci_errorbar.png)\n\n"
    
    markdown += "### Comparativa de Gap al Óptimo\n\n"
    markdown += "![Comparativa de gap al óptimo](figures/gap_comparison.png)\n\n"
    
    # Escribir a archivo
    with open(output_file, 'w') as f:
        f.write(markdown)
    
    print(f"Tabla Markdown generada en {output_file}")

def generate_latex_table(summary_df, output_file):
    """
    Genera una tabla en formato LaTeX con los resultados.
    
    Args:
        summary_df: DataFrame de resumen
        output_file: Ruta al archivo LaTeX de salida
    """
    # Agrupar por algoritmo
    algo_summary = summary_df.groupby('algorithm').agg({
        'gap_percent': ['mean', 'std'],
        'fitness_mean': ['mean', 'std'],
        'time_mean': ['mean', 'std'],
        'fitness_min': 'min',
        'gap_percent': 'min'
    }).reset_index()
    
    # Aplanar la estructura MultiIndex de las columnas
    algo_summary.columns = ['_'.join(col).strip('_') for col in algo_summary.columns.values]
    
    # Ordenar por gap promedio
    algo_summary = algo_summary.sort_values('gap_percent_mean')
    
    # Crear tabla LaTeX
    latex = "\\documentclass{article}\n"
    latex += "\\usepackage{booktabs}\n"
    latex += "\\usepackage{colortbl}\n"
    latex += "\\usepackage{xcolor}\n"
    latex += "\\usepackage[table]{xcolor}\n"
    latex += "\\usepackage{caption}\n"
    latex += "\\begin{document}\n\n"
    
    # Tabla comparativa global
    latex += "\\begin{table}[ht]\n"
    latex += "\\centering\n"
    latex += "\\caption{Comparativa Global de Algoritmos Metaheurísticos para VRP}\n"
    latex += "\\begin{tabular}{lccccc}\n"
    latex += "\\toprule\n"
    latex += "\\textbf{Algoritmo} & \\textbf{Mejor Gap (\\%)} & \\textbf{Gap Promedio (\\%)} & \\textbf{$\\sigma$ Gap} & \\textbf{Tiempo (s)} & \\textbf{$\\sigma$ Tiempo} \\\\\n"
    latex += "\\midrule\n"
    
    # Filas de la tabla
    for i, (_, row) in enumerate(algo_summary.iterrows()):
        algorithm = row['algorithm_'].upper()
        
        # Destacar mejor algoritmo
        if i == 0:
            latex += f"\\rowcolor{{lightgray}} "
        
        latex += f"{algorithm} & "
        latex += f"{row['gap_percent_min']:.2f} & "
        latex += f"{row['gap_percent_mean']:.2f} & "
        latex += f"{row['gap_percent_std']:.2f} & "
        latex += f"{row['time_mean_mean']:.4f} & "
        latex += f"{row['time_mean_std']:.4f} \\\\\n"
    
    latex += "\\bottomrule\n"
    latex += "\\end{tabular}\n"
    latex += "\\end{table}\n\n"
    
    # Tablas por instancia
    for instance in summary_df['instance'].unique():
        latex += f"\\begin{{table}}[ht]\n"
        latex += f"\\centering\n"
        latex += f"\\caption{{Resultados para instancia {instance}}}\n"
        latex += f"\\begin{{tabular}}{{lccccc}}\n"
        latex += f"\\toprule\n"
        latex += f"\\textbf{{Algoritmo}} & \\textbf{{Mejor Fitness}} & \\textbf{{Fitness Promedio}} & \\textbf{{$\\sigma$ Fitness}} & \\textbf{{Gap (\\%)}} & \\textbf{{Tiempo (s)}} \\\\\n"
        latex += f"\\midrule\n"
        
        inst_summary = summary_df[summary_df['instance'] == instance].sort_values('gap_percent')
        
        for i, (_, row) in enumerate(inst_summary.iterrows()):
            algorithm = row['algorithm'].upper()
            
            # Destacar mejor algoritmo
            if i == 0:
                latex += f"\\rowcolor{{lightgray}} "
            
            latex += f"{algorithm} & "
            latex += f"{row['fitness_min']:.2f} & "
            latex += f"{row['fitness_mean']:.2f} & "
            latex += f"{row['fitness_std']:.2f} & "
            latex += f"{row['gap_percent']:.2f} & "
            latex += f"{row['time_mean']:.4f} \\\\\n"
        
        latex += f"\\bottomrule\n"
        latex += f"\\end{{tabular}}\n"
        latex += f"\\end{{table}}\n\n"
    
    latex += "\\end{document}\n"
    
    # Escribir a archivo
    with open(output_file, 'w') as f:
        f.write(latex)
    
    print(f"Tabla LaTeX generada en {output_file}")

@click.command()
@click.option('--input-dir', required=True, help='Directorio o patrón glob con resultados de benchmark')
@click.option('--outfile', default='results/summary_all.csv', help='Archivo CSV para guardar resultados consolidados')
@click.option('--generate-graphs/--no-generate-graphs', default=True, help='Generar gráficas comparativas')
@click.option('--output-dir', default=None, help='Directorio para resultados (por defecto: results/global_analysis_TIMESTAMP)')
def main(input_dir, outfile, generate_graphs, output_dir):
    """
    Consolidar y analizar resultados de múltiples benchmarks VRP.
    
    Este script combina resultados de diferentes ejecuciones de benchmark,
    realiza análisis estadístico riguroso y genera visualizaciones comparativas
    para facilitar la interpretación de los resultados.
    """
    # Configurar directorio de salida
    if output_dir is None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_dir = f"results/global_analysis_{timestamp}"
    
    os.makedirs(output_dir, exist_ok=True)
    print(f"Directorio de análisis: {output_dir}")
    
    # Cargar todos los resultados
    try:
        df = load_benchmark_results(input_dir)
        
        # Generar resumen
        summary_df = generate_summary(df)
        
        # Guardar resumen a CSV
        summary_df.to_csv(outfile, index=False)
        print(f"Resumen guardado en {outfile}")
        
        # Generar intervalos de confianza
        ci_df = generate_confidence_intervals(df)
        
        # Ejecutar pruebas estadísticas
        stats_results = run_statistical_tests(df)
        
        # Generar visualizaciones si se solicita
        if generate_graphs:
            generate_plots(df, summary_df, ci_df, stats_results, output_dir)
        
        # Generar tabla Markdown
        markdown_file = os.path.join(output_dir, 'tabla_markdown.md')
        generate_markdown_table(summary_df, markdown_file)
        
        # Generar tabla LaTeX
        latex_file = os.path.join(output_dir, 'tabla_latex.tex')
        generate_latex_table(summary_df, latex_file)
        
        print(f"Análisis completo guardado en {output_dir}")
    
    except Exception as e:
        print(f"Error en el análisis: {str(e)}")
        raise

if __name__ == "__main__":
    main()