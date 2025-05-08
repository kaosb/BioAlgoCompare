#!/usr/bin/env python3
"""
Script para analizar los resultados de benchmarks masivos.
Aplica análisis estadístico y genera visualizaciones avanzadas.
"""

import click
import os
import logging
from datetime import datetime
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("analyze_massive.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("analyze_massive")

# Importar módulos personalizados
from utils.improved.enhanced_benchmarking import EnhancedBenchmarkResult, load_results
from utils.improved.enhanced_statistics import EnhancedStatisticalAnalysis
from utils.improved.advanced_visualization import create_full_visualization_set, create_visual_report

@click.command()
@click.option('--input-dir', '-i', required=True, help='Directorio con resultados del benchmark masivo')
@click.option('--output-dir', '-o', default=None, help='Directorio para resultados del análisis')
@click.option('--visualize/--no-visualize', default=True, help='Generar visualizaciones avanzadas')
def main(input_dir, output_dir, visualize):
    """
    Analiza resultados de benchmarks masivos con alta rigurosidad estadística.
    Genera informes detallados y visualizaciones avanzadas.
    """
    start_time = datetime.now()
    
    # Configurar directorio de salida
    if output_dir is None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_dir = f"results/analysis_{timestamp}"
    
    os.makedirs(output_dir, exist_ok=True)
    logger.info(f"Directorio de análisis: {output_dir}")
    
    # Cargar resultados del benchmark
    logger.info(f"Cargando resultados desde {input_dir}")
    results = load_results(input_dir)
    
    if not results:
        logger.error(f"No se encontraron resultados en {input_dir}")
        return
    
    # Mostrar resumen de resultados cargados
    logger.info(f"Cargados {len(results)} resultados de benchmark")
    for result in results:
        logger.info(f"  {result.algorithm_name} - {result.instance_name}: {len(result.fitness_values)} runs")
    
    # Extraer datos a nivel de ejecución individual para análisis
    logger.info("Preparando datos para análisis")
    raw_data = EnhancedStatisticalAnalysis.prepare_raw_data_for_statistics(results)
    
    # Crear DataFrame con resumen
    summary_df = pd.DataFrame([
        {
            'Algorithm': r.algorithm_name,
            'Instance': r.instance_name,
            'Runs': len(r.fitness_values),
            'Best': r.best_fitness,
            'Mean': r.mean_fitness,
            'Std': r.std_fitness,
            'Time': r.mean_time,
            'Time_Std': r.std_time,
            'Gap (%)': r.gap_to_optimal if r.gap_to_optimal is not None else np.nan,
            'Success (%)': r.success_rate if r.success_rate is not None else np.nan
        }
        for r in results
    ])
    
    # Guardar resumen
    summary_file = os.path.join(output_dir, "summary.csv")
    summary_df.to_csv(summary_file, index=False)
    logger.info(f"Resumen guardado en {summary_file}")
    
    # Análisis estadístico completo
    logger.info("Realizando análisis estadístico completo")
    metrics = ['best_fitness', 'mean_fitness', 'execution_time']
    if any(r.gap_to_optimal is not None for r in results):
        metrics.append('gap_to_optimal')
    
    try:
        stat_dir = os.path.join(output_dir, "statistics")
        os.makedirs(stat_dir, exist_ok=True)
        
        report_paths = EnhancedStatisticalAnalysis.run_comprehensive_statistical_analysis(
            results, metrics=metrics, output_dir=stat_dir
        )
        
        logger.info(f"Análisis estadístico completado. Informes guardados en {stat_dir}")
    except Exception as e:
        logger.error(f"Error en análisis estadístico: {str(e)}")
    
    # Análisis de bootstrap
    logger.info("Realizando análisis de bootstrap")
    try:
        bootstrap_results = EnhancedStatisticalAnalysis.perform_bootstrap_analysis(
            raw_data, metric='fitness', n_bootstrap=2000, confidence=0.95
        )
        
        bootstrap_file = os.path.join(output_dir, "bootstrap_analysis.csv")
        bootstrap_results.to_csv(bootstrap_file, index=False)
        logger.info(f"Análisis de bootstrap guardado en {bootstrap_file}")
        
        # Crear gráfico de intervalos de confianza
        plt.figure(figsize=(10, 6))
        
        # Ordenar por algoritmo
        bootstrap_results = bootstrap_results.sort_values('Algorithm')
        
        # Crear gráfico de barras con intervalos de confianza
        ax = sns.barplot(
            x='Algorithm',
            y='Mean',
            data=bootstrap_results,
            palette='viridis'
        )
        
        # Añadir intervalos de confianza
        for i, row in bootstrap_results.iterrows():
            ax.errorbar(
                i, row['Mean'],
                yerr=[[row['Mean'] - row['CI_Lower']], [row['CI_Upper'] - row['Mean']]],
                fmt='none', c='red', capsize=5
            )
        
        plt.title('Fitness promedio con intervalos de confianza (95%)')
        plt.ylabel('Fitness')
        plt.xlabel('Algoritmo')
        plt.tight_layout()
        
        # Guardar gráfico
        bootstrap_plot = os.path.join(output_dir, "bootstrap_intervals.png")
        plt.savefig(bootstrap_plot, dpi=300)
        plt.close()
    except Exception as e:
        logger.error(f"Error en análisis de bootstrap: {str(e)}")
    
    # Análisis con prueba de Wilcoxon
    logger.info("Realizando pruebas de Wilcoxon")
    try:
        wilcoxon_results = EnhancedStatisticalAnalysis.perform_wilcoxon_test(raw_data, alpha=0.01)
        
        wilcoxon_file = os.path.join(output_dir, "wilcoxon_tests.csv")
        wilcoxon_results.to_csv(wilcoxon_file, index=False)
        logger.info(f"Resultados de Wilcoxon guardados en {wilcoxon_file}")
    except Exception as e:
        logger.error(f"Error en pruebas de Wilcoxon: {str(e)}")
    
    # Visualizaciones avanzadas
    if visualize:
        logger.info("Generando visualizaciones avanzadas")
        try:
            vis_dir = os.path.join(output_dir, "visualizations")
            os.makedirs(vis_dir, exist_ok=True)
            
            figures = create_full_visualization_set(results, raw_data, output_dir=vis_dir)
            
            # Crear informe visual
            report_path = os.path.join(output_dir, "visual_report.html")
            create_visual_report(figures, output_file=report_path)
            
            logger.info(f"Visualizaciones generadas en {vis_dir}")
            logger.info(f"Informe visual: {report_path}")
        except Exception as e:
            logger.error(f"Error en generación de visualizaciones: {str(e)}")
    
    # Generar informe final
    logger.info("Generando informe final")
    try:
        report_file = os.path.join(output_dir, "final_report.html")
        
        # Crear contenido del informe
        with open(report_file, 'w') as f:
            f.write(f"""
            <!DOCTYPE html>
            <html>
            <head>
                <title>Análisis Estadístico de Benchmark Masivo</title>
                <style>
                    body {{
                        font-family: Arial, sans-serif;
                        margin: 20px;
                        line-height: 1.6;
                    }}
                    h1, h2, h3 {{
                        color: #2c3e50;
                    }}
                    table {{
                        border-collapse: collapse;
                        width: 100%;
                        margin-bottom: 20px;
                    }}
                    th, td {{
                        text-align: left;
                        padding: 8px;
                        border: 1px solid #ddd;
                    }}
                    th {{
                        background-color: #f2f2f2;
                    }}
                    tr:nth-child(even) {{
                        background-color: #f9f9f9;
                    }}
                    .section {{
                        margin-bottom: 30px;
                    }}
                    .figure {{
                        margin: 20px 0;
                        text-align: center;
                    }}
                    .figure img {{
                        max-width: 100%;
                        height: auto;
                    }}
                    .caption {{
                        margin-top: 10px;
                        font-style: italic;
                        color: #666;
                    }}
                    .navbar {{
                        position: fixed;
                        top: 0;
                        width: 100%;
                        background-color: #2c3e50;
                        padding: 10px 0;
                        z-index: 1000;
                        left: 0;
                    }}
                    .navbar a {{
                        color: white;
                        padding: 10px 15px;
                        text-decoration: none;
                        display: inline-block;
                    }}
                    .navbar a:hover {{
                        background-color: #1a252f;
                    }}
                    .content {{
                        margin-top: 60px;
                    }}
                </style>
            </head>
            <body>
                <div class="navbar">
                    <a href="#summary">Resumen</a>
                    <a href="#statistics">Estadísticas</a>
                    <a href="#visualizations">Visualizaciones</a>
                    <a href="#conclusion">Conclusiones</a>
                </div>
                
                <div class="content">
                    <h1>Análisis Estadístico de Benchmark Masivo</h1>
                    <p>Generado: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}</p>
                    
                    <div class="section" id="summary">
                        <h2>Resumen de Resultados</h2>
                        <table>
                            <tr>
                                <th>Algoritmo</th>
                                <th>Instancia</th>
                                <th>Ejecuciones</th>
                                <th>Mejor Fitness</th>
                                <th>Fitness Promedio</th>
                                <th>Desv. Estándar</th>
                                <th>Tiempo (s)</th>
                            </tr>
            """)
            
            # Añadir filas de resumen
            for _, row in summary_df.iterrows():
                f.write(f"""
                            <tr>
                                <td>{row['Algorithm']}</td>
                                <td>{row['Instance']}</td>
                                <td>{row['Runs']}</td>
                                <td>{row['Best']:.2f}</td>
                                <td>{row['Mean']:.2f}</td>
                                <td>{row['Std']:.2f}</td>
                                <td>{row['Time']:.2f}</td>
                            </tr>
                """)
            
            f.write("""
                        </table>
                    </div>
                    
                    <div class="section" id="statistics">
                        <h2>Análisis Estadístico</h2>
            """)
            
            # Añadir enlaces a informes estadísticos
            if 'report_paths' in locals():
                f.write("""
                        <h3>Informes Estadísticos</h3>
                        <ul>
                """)
                
                for metric, path in report_paths.items():
                    if metric != 'index':
                        rel_path = os.path.relpath(path, output_dir)
                        f.write(f"""
                            <li><a href="{rel_path}" target="_blank">Análisis de {metric}</a></li>
                        """)
                
                f.write("""
                        </ul>
                """)
            
            # Añadir resultados de bootstrap
            if 'bootstrap_plot' in locals():
                rel_path = os.path.relpath(bootstrap_plot, output_dir)
                f.write(f"""
                        <h3>Análisis de Bootstrap</h3>
                        <div class="figure">
                            <img src="{rel_path}" alt="Intervalos de Confianza">
                            <p class="caption">Intervalos de confianza del 95% calculados con bootstrap (2000 iteraciones)</p>
                        </div>
                """)
            
            f.write("""
                    </div>
                    
                    <div class="section" id="visualizations">
                        <h2>Visualizaciones</h2>
            """)
            
            # Añadir enlace al informe visual
            if 'report_path' in locals():
                rel_path = os.path.relpath(report_path, output_dir)
                f.write(f"""
                        <p><a href="{rel_path}" target="_blank">Ver informe visual completo</a></p>
                """)
            
            f.write("""
                    </div>
                    
                    <div class="section" id="conclusion">
                        <h2>Conclusiones</h2>
                        <p>Este análisis se ha realizado con un alto rigor estadístico, utilizando pruebas no paramétricas y técnicas de bootstrap para obtener conclusiones robustas.</p>
                        
                        <h3>Hallazgos Principales</h3>
                        <ul>
            """)
            
            # Obtener algoritmo con mejor fitness y más consistente
            best_algo = summary_df.loc[summary_df['Best'].idxmin(), 'Algorithm']
            most_consistent = summary_df.loc[summary_df['Std'].idxmin(), 'Algorithm']
            
            f.write(f"""
                            <li>El algoritmo <strong>{best_algo}</strong> obtuvo el mejor fitness en las pruebas realizadas.</li>
                            <li>El algoritmo <strong>{most_consistent}</strong> mostró la mayor consistencia (menor variabilidad).</li>
            """)
            
            # Añadir conclusiones basadas en pruebas estadísticas
            if 'wilcoxon_results' in locals() and not wilcoxon_results.empty:
                significant_pairs = wilcoxon_results[wilcoxon_results['Significant']]
                
                if not significant_pairs.empty:
                    f.write("""
                            <li>Se encontraron las siguientes diferencias estadísticamente significativas:</li>
                            <ul>
                    """)
                    
                    for _, row in significant_pairs.iterrows():
                        f.write(f"""
                                <li>{row['Algorithm1']} vs {row['Algorithm2']}: {row['Winner']} es significativamente mejor (p={row['p_value']:.6f})</li>
                        """)
                    
                    f.write("""
                            </ul>
                    """)
                else:
                    f.write("""
                            <li>No se encontraron diferencias estadísticamente significativas entre los algoritmos evaluados.</li>
                    """)
            
            f.write("""
                        </ul>
                    </div>
                </div>
            </body>
            </html>
            """)
        
        logger.info(f"Informe final generado: {report_file}")
    except Exception as e:
        logger.error(f"Error en generación de informe final: {str(e)}")
    
    # Calcular tiempo total de análisis
    elapsed = (datetime.now() - start_time).total_seconds()
    logger.info(f"Análisis completado en {elapsed:.1f} segundos")
    logger.info(f"Resultados guardados en {output_dir}")

if __name__ == '__main__':
    main()