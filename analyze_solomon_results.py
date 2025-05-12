#!/usr/bin/env python3
"""
Script para analizar y comparar los resultados de benchmarks en instancias Solomon
"""

import os
import glob
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import argparse
from pathlib import Path
import numpy as np

def load_benchmark_results(results_dir):
    """Carga los resultados del benchmark desde un directorio"""
    summary_path = Path(results_dir) / "massive_benchmark_summary.csv"
    
    if not summary_path.exists():
        print(f"Error: No se encontró el archivo de resumen en {summary_path}")
        return None
    
    try:
        df = pd.read_csv(summary_path)
        return df
    except Exception as e:
        print(f"Error al cargar el archivo CSV: {e}")
        return None

def create_comparison_charts(df, output_dir="benchmark_comparisons"):
    """Crea gráficos comparativos entre algoritmos y series de Solomon"""
    output_path = Path(output_dir)
    output_path.mkdir(exist_ok=True, parents=True)
    
    print(f"Generando gráficos comparativos en {output_dir}")
    
    # Extraer series (100 o 200) de las instancias
    df["Series"] = df["Instance"].apply(lambda x: "100" if x.endswith("101") else "200")
    df["Type"] = df["Instance"].apply(lambda x: x[0])  # C, R, RC
    
    # 1. Comparación de algoritmos por serie
    plt.figure(figsize=(12, 8))
    sns.boxplot(x="Algorithm", y="Best", hue="Series", data=df)
    plt.title("Comparación de algoritmos por serie")
    plt.xlabel("Algoritmo")
    plt.ylabel("Mejor fitness (distancia)")
    plt.xticks(rotation=45)
    plt.legend(title="Series")
    plt.tight_layout()
    plt.savefig(output_path / "algoritmos_por_serie.png", dpi=300)
    plt.close()
    
    # 2. Comparación de algoritmos por tipo de instancia
    plt.figure(figsize=(12, 8))
    sns.boxplot(x="Algorithm", y="Best", hue="Type", data=df)
    plt.title("Comparación de algoritmos por tipo de instancia")
    plt.xlabel("Algoritmo")
    plt.ylabel("Mejor fitness (distancia)")
    plt.xticks(rotation=45)
    plt.legend(title="Tipo")
    plt.tight_layout()
    plt.savefig(output_path / "algoritmos_por_tipo.png", dpi=300)
    plt.close()
    
    # 3. Tiempo de ejecución por algoritmo
    plt.figure(figsize=(12, 8))
    sns.boxplot(x="Algorithm", y="Time", data=df)
    plt.title("Tiempo de ejecución por algoritmo")
    plt.xlabel("Algoritmo")
    plt.ylabel("Tiempo (segundos)")
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.savefig(output_path / "tiempo_por_algoritmo.png", dpi=300)
    plt.close()
    
    # 4. Variabilidad por algoritmo (desviación estándar)
    plt.figure(figsize=(12, 8))
    sns.boxplot(x="Algorithm", y="Std", data=df)
    plt.title("Variabilidad por algoritmo")
    plt.xlabel("Algoritmo")
    plt.ylabel("Desviación estándar")
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.savefig(output_path / "variabilidad_por_algoritmo.png", dpi=300)
    plt.close()
    
    # 5. Si hay datos de tiempo promedio por iteración
    if "avg_iter_time" in df.columns:
        plt.figure(figsize=(12, 8))
        sns.boxplot(x="Algorithm", y="avg_iter_time", data=df)
        plt.title("Tiempo promedio por iteración")
        plt.xlabel("Algoritmo")
        plt.ylabel("Tiempo por iteración (segundos)")
        plt.xticks(rotation=45)
        plt.tight_layout()
        plt.savefig(output_path / "tiempo_por_iteracion.png", dpi=300)
        plt.close()
    
    # 6. Ranking de algoritmos por instancia
    # Crear un ranking de algoritmos para cada instancia
    rankings = []
    for instance in df["Instance"].unique():
        instance_df = df[df["Instance"] == instance].copy()
        instance_df["Rank"] = instance_df["Best"].rank()
        rankings.append(instance_df)
    
    rankings_df = pd.concat(rankings)
    
    plt.figure(figsize=(12, 8))
    sns.boxplot(x="Algorithm", y="Rank", data=rankings_df)
    plt.title("Ranking de algoritmos por instancia")
    plt.xlabel("Algoritmo")
    plt.ylabel("Ranking (1 = mejor)")
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.savefig(output_path / "ranking_algoritmos.png", dpi=300)
    plt.close()
    
    # 7. Tabla resumen
    summary_table = df.groupby("Algorithm")[["Best", "Mean", "Std", "Time"]].mean().reset_index()
    summary_table = summary_table.sort_values("Best")
    
    # Guardar tabla como CSV
    summary_table.to_csv(output_path / "resumen_algoritmos.csv", index=False)
    
    # También crear una versión visual de la tabla
    fig, ax = plt.figure(figsize=(10, len(summary_table)*0.5)), plt.gca()
    ax.axis('tight')
    ax.axis('off')
    table = ax.table(cellText=summary_table.round(2).values, 
                    colLabels=summary_table.columns, 
                    loc='center')
    plt.title("Resumen de rendimiento por algoritmo")
    plt.tight_layout()
    plt.savefig(output_path / "tabla_resumen.png", dpi=300)
    plt.close()
    
    print("Análisis completado. Gráficos guardados en", output_dir)
    return output_path

def main():
    """Función principal"""
    parser = argparse.ArgumentParser(description="Analiza resultados de benchmarks en instancias Solomon")
    parser.add_argument("--results", type=str, help="Directorio con resultados del benchmark",
                        default=None)
    parser.add_argument("--output", type=str, help="Directorio para guardar análisis",
                        default="benchmark_comparisons")
    
    args = parser.parse_args()
    
    # Si no se especifica un directorio, buscar el más reciente
    if args.results is None:
        benchmark_dirs = glob.glob("results/massive_benchmark_*")
        if not benchmark_dirs:
            print("Error: No se encontraron directorios de resultados")
            return
        
        # Ordenar por fecha (más reciente primero)
        benchmark_dirs.sort(reverse=True)
        args.results = benchmark_dirs[0]
        print(f"Usando el directorio de resultados más reciente: {args.results}")
    
    # Cargar resultados
    df = load_benchmark_results(args.results)
    if df is None:
        return
    
    print(f"Cargados datos de {len(df)} filas con {len(df['Algorithm'].unique())} algoritmos")
    
    # Crear gráficos
    output_path = create_comparison_charts(df, args.output)
    
    # Mostrar un resumen
    print("\nResumen de resultados:")
    algo_summary = df.groupby("Algorithm")["Best"].agg(["min", "mean", "std"]).reset_index()
    algo_summary.columns = ["Algoritmo", "Mejor", "Promedio", "Desv. Std."]
    print(algo_summary.to_string(index=False))
    
    print(f"\nAnálisis completo disponible en: {output_path}")

if __name__ == "__main__":
    main()