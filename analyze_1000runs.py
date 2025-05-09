#!/usr/bin/env python3
"""
Script para analizar y comparar los resultados de los 3 escenarios (10, 100 y 1000 ejecuciones).
Genera gráficas comparativas y tablas de resumen.
"""

import os
import json
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime

# Configurar estilo de las gráficas
plt.style.use('ggplot')
sns.set_style("whitegrid")
sns.set_palette("colorblind")

# Rutas a los directorios de resultados
RESULTS_10 = "results/test_10runs"
RESULTS_100 = "results/test_100runs"
RESULTS_1000 = "results/test_1000runs"
OUTPUT_DIR = "results/comparative_analysis"

# Asegurar que existe el directorio de salida
os.makedirs(OUTPUT_DIR, exist_ok=True)

def load_benchmark_results(json_path):
    """Carga resultados de un archivo JSON de benchmark."""
    with open(json_path, 'r') as f:
        data = json.load(f)
    return data

def extract_summary_statistics(results_data):
    """Extrae estadísticas resumidas de los resultados del benchmark."""
    summary = []
    
    for result in results_data:
        summary.append({
            'algorithm': result['algorithm'],
            'instance': result['instance'],
            'best_fitness': result['metrics']['best_fitness'],
            'mean_fitness': result['metrics']['mean_fitness'],
            'std_fitness': result['metrics']['std_fitness'],
            'mean_time': result['metrics']['mean_time'],
            'std_time': result['metrics']['std_time'],
            'gap_to_optimal': result['metrics']['gap_to_optimal'],
            'success_rate': result['metrics']['success_rate'],
            'runs': result['runs']
        })
    
    return pd.DataFrame(summary)

def create_comparison_table():
    """Crea una tabla comparativa de los tres escenarios."""
    try:
        # Cargar resultados
        results_10 = load_benchmark_results(os.path.join(RESULTS_10, "benchmark_results.json"))
        results_100 = load_benchmark_results(os.path.join(RESULTS_100, "benchmark_results.json"))
        results_1000 = load_benchmark_results(os.path.join(RESULTS_1000, "benchmark_results.json"))
        
        # Extraer estadísticas
        summary_10 = extract_summary_statistics(results_10)
        summary_100 = extract_summary_statistics(results_100)
        summary_1000 = extract_summary_statistics(results_1000)
        
        # Añadir columna para identificar el escenario
        summary_10['scenario'] = '10 runs'
        summary_100['scenario'] = '100 runs'
        summary_1000['scenario'] = '1000 runs'
        
        # Combinar todos los resultados
        all_summary = pd.concat([summary_10, summary_100, summary_1000])
        
        # Guardar tabla completa
        table_path = os.path.join(OUTPUT_DIR, "comparison_table.csv")
        all_summary.to_csv(table_path, index=False)
        print(f"Tabla de comparación guardada en {table_path}")
        
        return all_summary
    except Exception as e:
        print(f"Error al crear la tabla de comparación: {str(e)}")
        return None

def plot_best_fitness_comparison(summary_df):
    """Gráfica comparativa del mejor fitness por algoritmo y escenario."""
    if summary_df is None:
        return
    
    plt.figure(figsize=(10, 6))
    
    # Crear gráfico de barras agrupadas
    sns.barplot(x='algorithm', y='best_fitness', hue='scenario', data=summary_df)
    
    plt.title('Mejor Fitness por Algoritmo y Cantidad de Ejecuciones', fontsize=14)
    plt.xlabel('Algoritmo', fontsize=12)
    plt.ylabel('Mejor Fitness (Menor es Mejor)', fontsize=12)
    plt.grid(True, linestyle='--', alpha=0.7)
    plt.legend(title='Escenario')
    
    # Añadir valor óptimo conocido
    plt.axhline(y=450, color='red', linestyle='--', label='Óptimo Conocido (450)')
    plt.legend()
    
    # Guardar gráfica
    plt.tight_layout()
    output_path = os.path.join(OUTPUT_DIR, "best_fitness_comparison.png")
    plt.savefig(output_path, dpi=300)
    plt.close()
    print(f"Gráfica de mejor fitness guardada en {output_path}")

def plot_mean_fitness_comparison(summary_df):
    """Gráfica comparativa del fitness promedio por algoritmo y escenario."""
    if summary_df is None:
        return
    
    plt.figure(figsize=(10, 6))
    
    # Preparar datos para mostrar barras de error
    ax = sns.barplot(x='algorithm', y='mean_fitness', hue='scenario', data=summary_df)
    
    # Añadir barras de error
    for i, row in enumerate(summary_df.itertuples()):
        x = i % len(summary_df['algorithm'].unique())
        x_offset = (i // len(summary_df['algorithm'].unique())) * 0.3 - 0.3
        
        ax.errorbar(x + x_offset, row.mean_fitness, yerr=row.std_fitness, 
                   fmt='none', capsize=5, ecolor='black', alpha=0.7)
    
    plt.title('Fitness Promedio por Algoritmo y Cantidad de Ejecuciones', fontsize=14)
    plt.xlabel('Algoritmo', fontsize=12)
    plt.ylabel('Fitness Promedio ± Desv. Est.', fontsize=12)
    plt.grid(True, linestyle='--', alpha=0.7)
    plt.legend(title='Escenario')
    
    # Añadir valor óptimo conocido
    plt.axhline(y=450, color='red', linestyle='--', label='Óptimo Conocido (450)')
    plt.legend()
    
    # Guardar gráfica
    plt.tight_layout()
    output_path = os.path.join(OUTPUT_DIR, "mean_fitness_comparison.png")
    plt.savefig(output_path, dpi=300)
    plt.close()
    print(f"Gráfica de fitness promedio guardada en {output_path}")

def plot_execution_time_comparison(summary_df):
    """Gráfica comparativa del tiempo de ejecución por algoritmo y escenario."""
    if summary_df is None:
        return
    
    plt.figure(figsize=(10, 6))
    
    # Crear gráfico de barras agrupadas
    sns.barplot(x='algorithm', y='mean_time', hue='scenario', data=summary_df)
    
    plt.title('Tiempo de Ejecución por Algoritmo y Cantidad de Ejecuciones', fontsize=14)
    plt.xlabel('Algoritmo', fontsize=12)
    plt.ylabel('Tiempo Promedio (segundos)', fontsize=12)
    plt.grid(True, linestyle='--', alpha=0.7)
    plt.legend(title='Escenario')
    
    # Guardar gráfica
    plt.tight_layout()
    output_path = os.path.join(OUTPUT_DIR, "execution_time_comparison.png")
    plt.savefig(output_path, dpi=300)
    plt.close()
    print(f"Gráfica de tiempo de ejecución guardada en {output_path}")

def plot_success_rate_comparison(summary_df):
    """Gráfica comparativa de la tasa de éxito por algoritmo y escenario."""
    if summary_df is None:
        return
    
    plt.figure(figsize=(10, 6))
    
    # Crear gráfico de barras agrupadas
    sns.barplot(x='algorithm', y='success_rate', hue='scenario', data=summary_df)
    
    plt.title('Tasa de Éxito por Algoritmo y Cantidad de Ejecuciones', fontsize=14)
    plt.xlabel('Algoritmo', fontsize=12)
    plt.ylabel('Tasa de Éxito (%)', fontsize=12)
    plt.grid(True, linestyle='--', alpha=0.7)
    plt.legend(title='Escenario')
    
    # Guardar gráfica
    plt.tight_layout()
    output_path = os.path.join(OUTPUT_DIR, "success_rate_comparison.png")
    plt.savefig(output_path, dpi=300)
    plt.close()
    print(f"Gráfica de tasa de éxito guardada en {output_path}")

def generate_summary_report(summary_df):
    """Genera un informe resumido en formato Markdown."""
    if summary_df is None:
        return
    
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    # Crear resumen por algoritmo y escenario
    algo_summary = summary_df.groupby(['algorithm', 'scenario']).agg({
        'best_fitness': 'min',
        'mean_fitness': 'mean',
        'std_fitness': 'mean',
        'mean_time': 'mean',
        'gap_to_optimal': 'min',
        'success_rate': 'mean'
    }).reset_index()
    
    # Formatear como tabla Markdown
    markdown = f"# Resumen Comparativo de Escenarios (10, 100, 1000 ejecuciones)\n\n"
    markdown += f"Generado el: {timestamp}\n\n"
    markdown += f"## Tabla Comparativa de Resultados\n\n"
    
    # Crear tabla por algoritmo
    for algo in algo_summary['algorithm'].unique():
        algo_data = algo_summary[algo_summary['algorithm'] == algo]
        
        markdown += f"### Algoritmo: {algo}\n\n"
        markdown += "| Métrica | 10 ejecuciones | 100 ejecuciones | 1000 ejecuciones |\n"
        markdown += "|---------|----------------|-----------------|------------------|\n"
        
        # Extraer datos para cada escenario
        for metric in ['best_fitness', 'mean_fitness', 'std_fitness', 'mean_time', 'gap_to_optimal', 'success_rate']:
            metric_name = {
                'best_fitness': 'Mejor Fitness',
                'mean_fitness': 'Fitness Promedio',
                'std_fitness': 'Desviación Estándar',
                'mean_time': 'Tiempo Promedio (s)',
                'gap_to_optimal': 'Gap al Óptimo (%)',
                'success_rate': 'Tasa de Éxito (%)'
            }[metric]
            
            # Formatear valores
            values = []
            for scenario in ['10 runs', '100 runs', '1000 runs']:
                scenario_data = algo_data[algo_data['scenario'] == scenario]
                
                if len(scenario_data) > 0:
                    if metric in ['gap_to_optimal', 'success_rate']:
                        values.append(f"{scenario_data[metric].values[0]:.2f}%")
                    elif metric == 'mean_time':
                        values.append(f"{scenario_data[metric].values[0]:.4f}")
                    else:
                        values.append(f"{scenario_data[metric].values[0]:.2f}")
                else:
                    values.append("N/A")
            
            markdown += f"| {metric_name} | {values[0]} | {values[1]} | {values[2]} |\n"
        
        markdown += "\n"
    
    # Añadir sección de observaciones
    markdown += "## Observaciones\n\n"
    markdown += "- La mejor solución global encontrada fue "
    best_overall = summary_df['best_fitness'].min()
    best_algo = summary_df.loc[summary_df['best_fitness'] == best_overall, 'algorithm'].iloc[0]
    best_scenario = summary_df.loc[summary_df['best_fitness'] == best_overall, 'scenario'].iloc[0]
    markdown += f"{best_overall:.2f} por el algoritmo {best_algo} en el escenario de {best_scenario}.\n"
    
    # Análisis de rendimiento computacional
    fastest_algo = summary_df.groupby('algorithm')['mean_time'].mean().idxmin()
    markdown += f"- El algoritmo más rápido en promedio fue {fastest_algo}.\n"
    
    # Tendencia de mejora
    markdown += "- Incrementar el número de ejecuciones de 10 a 100 resultó en "
    best_10 = summary_df[summary_df['scenario'] == '10 runs']['best_fitness'].min()
    best_100 = summary_df[summary_df['scenario'] == '100 runs']['best_fitness'].min()
    improvement_10_to_100 = (best_10 - best_100) / best_10 * 100
    markdown += f"una mejora del {improvement_10_to_100:.2f}% en el mejor fitness global encontrado.\n"
    
    # Tendencia de estabilidad
    markdown += "- La desviación estándar en los resultados fue "
    std_10 = summary_df[summary_df['scenario'] == '10 runs']['std_fitness'].mean()
    std_100 = summary_df[summary_df['scenario'] == '100 runs']['std_fitness'].mean()
    if std_100 < std_10:
        markdown += f"menor con 100 ejecuciones ({std_100:.2f}) que con 10 ejecuciones ({std_10:.2f}), "
        markdown += "lo que indica mayor estabilidad y confiabilidad estadística con más ejecuciones.\n"
    else:
        markdown += f"similar o mayor con más ejecuciones, lo que sugiere que algunos algoritmos pueden mostrar comportamiento más variable a largo plazo.\n"
    
    # Guardar informe
    output_path = os.path.join(OUTPUT_DIR, "comparative_summary.md")
    with open(output_path, 'w') as f:
        f.write(markdown)
    print(f"Informe resumido guardado en {output_path}")

def main():
    """Función principal que ejecuta todo el análisis comparativo."""
    print("Iniciando análisis comparativo de escenarios (10, 100, 1000 ejecuciones)...")
    
    # Crear tabla comparativa
    summary_df = create_comparison_table()
    
    if summary_df is not None:
        # Generar gráficas comparativas
        plot_best_fitness_comparison(summary_df)
        plot_mean_fitness_comparison(summary_df)
        plot_execution_time_comparison(summary_df)
        plot_success_rate_comparison(summary_df)
        
        # Generar informe resumido
        generate_summary_report(summary_df)
        
        print(f"Análisis comparativo completado. Resultados guardados en {OUTPUT_DIR}")
    else:
        print("No se pudo generar el análisis debido a errores en la carga de datos.")

if __name__ == "__main__":
    main()