#!/usr/bin/env python3
"""
Script para analizar los resultados de CSV de benchmark.
Genera estadísticas y visualizaciones.
"""

import os
import sys
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from scipy import stats
from datetime import datetime

def main():
    # Verificar argumentos
    if len(sys.argv) < 2:
        print("Uso: python analyze_csv.py <archivo_csv> [directorio_salida]")
        sys.exit(1)
    
    # Obtener rutas
    csv_file = sys.argv[1]
    output_dir = sys.argv[2] if len(sys.argv) > 2 else "results/analysis_csv"
    
    # Verificar que existe el archivo
    if not os.path.exists(csv_file):
        print(f"Error: No se encontró el archivo {csv_file}")
        sys.exit(1)
    
    # Crear directorio de salida
    os.makedirs(output_dir, exist_ok=True)
    print(f"Directorio de análisis: {output_dir}")
    
    # Cargar datos
    print(f"Cargando datos desde {csv_file}")
    df = pd.read_csv(csv_file)
    
    # Mostrar resumen
    print("\nResumen de datos:")
    print(df.to_string())
    
    # Análisis estadístico básico
    print("\nAnálisis estadístico:")
    algorithms = df['Algorithm'].unique()
    
    for algo in algorithms:
        algo_data = df[df['Algorithm'] == algo]
        print(f"\n{algo}:")
        print(f"  Ejecuciones: {algo_data['Runs'].iloc[0]}")
        print(f"  Mejor fitness: {algo_data['Best'].iloc[0]:.4f}")
        print(f"  Fitness promedio: {algo_data['Mean'].iloc[0]:.4f}")
        print(f"  Desviación estándar: {algo_data['Std'].iloc[0]:.4f}")
        print(f"  Tiempo promedio: {algo_data['Time'].iloc[0]:.4f}s")
    
    # Crear visualizaciones
    print("\nGenerando visualizaciones...")
    
    # Gráfico de barras para fitness promedio
    plt.figure(figsize=(10, 6))
    ax = sns.barplot(x='Algorithm', y='Mean', data=df)
    
    # Añadir barras de error
    for i, row in df.iterrows():
        ax.errorbar(i, row['Mean'], yerr=row['Std'], fmt='none', c='red', capsize=5)
    
    plt.title('Fitness promedio por algoritmo')
    plt.ylabel('Fitness')
    plt.tight_layout()
    
    # Guardar gráfico
    bar_plot = os.path.join(output_dir, "fitness_bar_plot.png")
    plt.savefig(bar_plot, dpi=300)
    plt.close()
    
    # Comparación de tiempo de ejecución
    plt.figure(figsize=(10, 6))
    ax = sns.barplot(x='Algorithm', y='Time', data=df)
    
    # Añadir barras de error
    for i, row in df.iterrows():
        ax.errorbar(i, row['Time'], yerr=row['Time_Std'], fmt='none', c='red', capsize=5)
    
    plt.title('Tiempo de ejecución por algoritmo')
    plt.ylabel('Tiempo (s)')
    plt.tight_layout()
    
    # Guardar gráfico
    time_plot = os.path.join(output_dir, "time_bar_plot.png")
    plt.savefig(time_plot, dpi=300)
    plt.close()
    
    # Generar informe HTML
    print("\nGenerando informe HTML...")
    html_file = os.path.join(output_dir, "analysis_report.html")
    
    with open(html_file, 'w') as f:
        f.write(f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Análisis de Benchmark</title>
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
            </style>
        </head>
        <body>
            <h1>Análisis de Benchmark</h1>
            <p>Generado: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}</p>
            
            <div class="section">
                <h2>Resumen</h2>
                <table>
                    <tr>
                        <th>Algoritmo</th>
                        <th>Instancia</th>
                        <th>Ejecuciones</th>
                        <th>Mejor Fitness</th>
                        <th>Promedio</th>
                        <th>Desv. Estándar</th>
                        <th>Tiempo (s)</th>
                    </tr>
        """)
        
        # Añadir filas
        for _, row in df.iterrows():
            f.write(f"""
                    <tr>
                        <td>{row['Algorithm']}</td>
                        <td>{row['Instance']}</td>
                        <td>{row['Runs']}</td>
                        <td>{row['Best']:.4f}</td>
                        <td>{row['Mean']:.4f}</td>
                        <td>{row['Std']:.4f}</td>
                        <td>{row['Time']:.4f}</td>
                    </tr>
            """)
        
        f.write("""
                </table>
            </div>
            
            <div class="section">
                <h2>Análisis Estadístico</h2>
        """)
        
        # Añadir resultados estadísticos
        for algo in algorithms:
            algo_data = df[df['Algorithm'] == algo]
            f.write(f"""
                <h3>{algo}</h3>
                <ul>
                    <li>Ejecuciones: {algo_data['Runs'].iloc[0]}</li>
                    <li>Mejor fitness: {algo_data['Best'].iloc[0]:.4f}</li>
                    <li>Fitness promedio: {algo_data['Mean'].iloc[0]:.4f} ± {algo_data['Std'].iloc[0]:.4f}</li>
                    <li>Error estándar: {algo_data['Std'].iloc[0] / np.sqrt(algo_data['Runs'].iloc[0]):.4f}</li>
                    <li>Tiempo promedio: {algo_data['Time'].iloc[0]:.4f}s ± {algo_data['Time_Std'].iloc[0]:.4f}s</li>
                </ul>
            """)
        
        f.write("""
            </div>
            
            <div class="section">
                <h2>Visualizaciones</h2>
                
                <div class="figure">
                    <img src="fitness_bar_plot.png" alt="Fitness por Algoritmo">
                    <p class="caption">Fitness promedio por algoritmo con barras de error</p>
                </div>
                
                <div class="figure">
                    <img src="time_bar_plot.png" alt="Tiempo por Algoritmo">
                    <p class="caption">Tiempo de ejecución por algoritmo con barras de error</p>
                </div>
            </div>
            
            <div class="section">
                <h2>Comparación Estadística</h2>
        """)
        
        # Añadir comparación si hay múltiples algoritmos
        if len(algorithms) > 1:
            # Crear comparación
            f.write("""
                <h3>Comparación relativa</h3>
                <table>
                    <tr>
                        <th>Métrica</th>
                        <th>Algoritmo mejor</th>
                        <th>Diferencia porcentual</th>
                    </tr>
            """)
            
            # Mejor fitness
            best_algo = df.loc[df['Best'].idxmin(), 'Algorithm']
            second_best = df[df['Algorithm'] != best_algo].loc[df[df['Algorithm'] != best_algo]['Best'].idxmin(), 'Algorithm']
            best_value = df.loc[df['Best'].idxmin(), 'Best']
            second_value = df[df['Algorithm'] == second_best]['Best'].iloc[0]
            diff_pct = (second_value - best_value) / best_value * 100
            
            f.write(f"""
                    <tr>
                        <td>Mejor fitness</td>
                        <td>{best_algo}</td>
                        <td>{diff_pct:.2f}% mejor que {second_best}</td>
                    </tr>
            """)
            
            # Fitness promedio
            best_algo = df.loc[df['Mean'].idxmin(), 'Algorithm']
            second_best = df[df['Algorithm'] != best_algo].loc[df[df['Algorithm'] != best_algo]['Mean'].idxmin(), 'Algorithm']
            best_value = df.loc[df['Mean'].idxmin(), 'Mean']
            second_value = df[df['Algorithm'] == second_best]['Mean'].iloc[0]
            diff_pct = (second_value - best_value) / best_value * 100
            
            f.write(f"""
                    <tr>
                        <td>Fitness promedio</td>
                        <td>{best_algo}</td>
                        <td>{diff_pct:.2f}% mejor que {second_best}</td>
                    </tr>
            """)
            
            # Consistencia (menor desviación)
            best_algo = df.loc[df['Std'].idxmin(), 'Algorithm']
            second_best = df[df['Algorithm'] != best_algo].loc[df[df['Algorithm'] != best_algo]['Std'].idxmin(), 'Algorithm']
            best_value = df.loc[df['Std'].idxmin(), 'Std']
            second_value = df[df['Algorithm'] == second_best]['Std'].iloc[0]
            diff_pct = (second_value - best_value) / best_value * 100
            
            f.write(f"""
                    <tr>
                        <td>Consistencia</td>
                        <td>{best_algo}</td>
                        <td>{diff_pct:.2f}% más consistente que {second_best}</td>
                    </tr>
            """)
            
            # Tiempo de ejecución
            best_algo = df.loc[df['Time'].idxmin(), 'Algorithm']
            second_best = df[df['Algorithm'] != best_algo].loc[df[df['Algorithm'] != best_algo]['Time'].idxmin(), 'Algorithm']
            best_value = df.loc[df['Time'].idxmin(), 'Time']
            second_value = df[df['Algorithm'] == second_best]['Time'].iloc[0]
            diff_pct = (second_value - best_value) / best_value * 100
            
            f.write(f"""
                    <tr>
                        <td>Tiempo de ejecución</td>
                        <td>{best_algo}</td>
                        <td>{diff_pct:.2f}% más rápido que {second_best}</td>
                    </tr>
            """)
            
            f.write("""
                </table>
            """)
            
            # Intervalos de confianza
            f.write("""
                <h3>Intervalos de Confianza (95%)</h3>
                <table>
                    <tr>
                        <th>Algoritmo</th>
                        <th>Promedio</th>
                        <th>Límite Inferior</th>
                        <th>Límite Superior</th>
                    </tr>
            """)
            
            # Calcular intervalos para cada algoritmo
            for algo in algorithms:
                algo_data = df[df['Algorithm'] == algo]
                mean = algo_data['Mean'].iloc[0]
                std = algo_data['Std'].iloc[0]
                n = algo_data['Runs'].iloc[0]
                sem = std / np.sqrt(n)
                
                # Calcular intervalo t-Student
                t_value = stats.t.ppf(0.975, n-1)  # 95% de confianza
                lower = mean - t_value * sem
                upper = mean + t_value * sem
                
                f.write(f"""
                    <tr>
                        <td>{algo}</td>
                        <td>{mean:.4f}</td>
                        <td>{lower:.4f}</td>
                        <td>{upper:.4f}</td>
                    </tr>
                """)
            
            f.write("""
                </table>
            """)
            
            # Prueba de significancia estadística
            if len(algorithms) == 2:
                # Estimar valor Z y p-valor
                algo1, algo2 = algorithms
                data1 = df[df['Algorithm'] == algo1]
                data2 = df[df['Algorithm'] == algo2]
                
                mean1 = data1['Mean'].iloc[0]
                mean2 = data2['Mean'].iloc[0]
                std1 = data1['Std'].iloc[0]
                std2 = data2['Std'].iloc[0]
                n1 = data1['Runs'].iloc[0]
                n2 = data2['Runs'].iloc[0]
                
                # Calcular estadístico Z
                se = np.sqrt((std1**2 / n1) + (std2**2 / n2))
                z = (mean1 - mean2) / se
                p_value = 2 * (1 - stats.norm.cdf(abs(z)))
                
                # Determinar significancia
                is_significant = p_value < 0.05
                
                f.write(f"""
                <h3>Prueba de Hipótesis ({algo1} vs {algo2})</h3>
                <p>Diferencia en medias: {mean1 - mean2:.4f}</p>
                <p>Estadístico Z: {z:.4f}</p>
                <p>p-valor: {p_value:.6f}</p>
                <p><strong>Conclusión:</strong> La diferencia es {"estadísticamente significativa" if is_significant else "NO estadísticamente significativa"} (α=0.05).</p>
                """)
        
        f.write("""
            </div>
            
            <div class="section">
                <h2>Conclusiones</h2>
        """)
        
        # Añadir conclusiones
        if len(algorithms) > 1:
            best_algo = df.loc[df['Mean'].idxmin(), 'Algorithm']
            most_consistent = df.loc[df['Std'].idxmin(), 'Algorithm']
            
            f.write(f"""
                <p>Basado en {df['Runs'].iloc[0]} ejecuciones por algoritmo:</p>
                <ul>
                    <li><strong>{best_algo}</strong> obtuvo el mejor rendimiento promedio.</li>
                    <li><strong>{most_consistent}</strong> mostró la mayor consistencia (menor variabilidad).</li>
                </ul>
            """)
            
            # Estimar intervalos y comparar
            algo1_data = df[df['Algorithm'] == algorithms[0]]
            algo2_data = df[df['Algorithm'] == algorithms[1]]
            mean1 = algo1_data['Mean'].iloc[0]
            mean2 = algo2_data['Mean'].iloc[0]
            
            better = algorithms[0] if mean1 < mean2 else algorithms[1]
            worse = algorithms[1] if mean1 < mean2 else algorithms[0]
            diff_pct = abs(mean1 - mean2) / min(mean1, mean2) * 100
            
            f.write(f"""
                <p><strong>Comparación:</strong> {better} fue un {diff_pct:.2f}% mejor que {worse} en promedio.</p>
            """)
            
            # Significancia
            if 'p_value' in locals():
                if is_significant:
                    f.write(f"""
                    <p>Esta diferencia es <strong>estadísticamente significativa</strong> (p={p_value:.6f}), lo que indica una ventaja real de {better} sobre {worse}.</p>
                    """)
                else:
                    f.write(f"""
                    <p>Esta diferencia <strong>no es estadísticamente significativa</strong> (p={p_value:.6f}), lo que sugiere que ambos algoritmos tienen rendimiento similar.</p>
                    """)
        
        f.write("""
            </div>
        </body>
        </html>
        """)
    
    print(f"Informe generado: {html_file}")
    print("\nAnálisis completado.")

if __name__ == "__main__":
    main()