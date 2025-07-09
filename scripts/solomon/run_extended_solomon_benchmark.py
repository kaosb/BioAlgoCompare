#!/usr/bin/env python3
"""
Script para ejecutar benchmarks extendidos en instancias Solomon VRP
con más iteraciones y ejecuciones
"""

import os
import sys
import argparse
import subprocess
import time
from pathlib import Path
from datetime import datetime

def main():
    """Función principal"""
    parser = argparse.ArgumentParser(description="Ejecuta benchmark extendido en instancias Solomon VRP")
    parser.add_argument("--runs", type=int, default=50, help="Número de ejecuciones (default: 50)")
    parser.add_argument("--iterations", type=int, default=100, help="Número de iteraciones (default: 100)")
    parser.add_argument("--algorithms", type=str, default="woa,sma,gto", 
                        help="Algoritmos a ejecutar separados por comas (default: woa,sma,gto)")
    parser.add_argument("--series", type=str, default="all", 
                        help="Series a ejecutar: 101, 201 o all (default: all)")
    parser.add_argument("--output-dir", type=str, default=None,
                        help="Directorio de salida personalizado (opcional)")
    
    args = parser.parse_args()
    
    # Crear directorio de resultados con timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_dir = args.output_dir or f"results/extended_benchmark_{timestamp}"
    Path(output_dir).mkdir(exist_ok=True, parents=True)
    
    log_file = Path(output_dir) / "extended_benchmark.log"
    
    print("=== Benchmark Extendido en Instancias Solomon ===")
    print("Configuración:")
    print(f"  - Ejecuciones: {args.runs}")
    print(f"  - Iteraciones: {args.iterations}")
    print(f"  - Algoritmos: {args.algorithms}")
    print(f"  - Series: {args.series}")
    print(f"  - Directorio de salida: {output_dir}")
    print(f"  - Log: {log_file}")
    
    # Grabar configuración en log
    with open(log_file, "w") as f:
        f.write("=== Benchmark Extendido VRP Solomon ===\n")
        f.write(f"Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"Ejecuciones: {args.runs}\n")
        f.write(f"Iteraciones: {args.iterations}\n")
        f.write(f"Algoritmos: {args.algorithms}\n")
        f.write(f"Series: {args.series}\n\n")
    
    # Paso 1: Ejecutar benchmark
    start_time = time.time()
    benchmark_cmd = [
        "python", "run_full_solomon_benchmark.py",
        "--runs", str(args.runs),
        "--iterations", str(args.iterations),
        "--algorithms", args.algorithms,
        "--series", args.series
    ]
    
    print("\nIniciando benchmark...")
    print(f"Comando: {' '.join(benchmark_cmd)}")
    
    try:
        # Ejecutar benchmark y capturar salida
        result = subprocess.run(
            benchmark_cmd, 
            capture_output=True, 
            text=True,
            env=dict(os.environ, PYTHONPATH=".")
        )
        
        # Guardar salida en log
        with open(log_file, "a") as f:
            f.write("=== SALIDA DEL BENCHMARK ===\n")
            f.write(result.stdout)
            if result.stderr:
                f.write("\n=== ERRORES ===\n")
                f.write(result.stderr)
        
        # Extraer directorio de resultados del benchmark
        benchmark_dir = None
        for line in result.stdout.splitlines():
            if "Directorio de salida: results/massive_benchmark_" in line:
                benchmark_dir = line.split(":", 1)[1].strip()
                break
        
        if not benchmark_dir:
            raise ValueError("No se pudo extraer el directorio de resultados del benchmark")
        
        # Paso 2: Copiar resultados importantes al directorio de salida
        print("\nCopiando resultados importantes...")
        files_to_copy = [
            "massive_benchmark_summary.csv",
            "massive_benchmark_report.html",
            "manifest.json"
        ]
        
        for file in files_to_copy:
            src = Path(benchmark_dir) / file
            dst = Path(output_dir) / file
            if src.exists():
                import shutil
                shutil.copy2(src, dst)
                print(f"  - Copiado: {file}")
        
        # Paso 3: Ejecutar análisis y generar gráficos
        print("\nGenerando análisis y gráficos...")
        
        analysis_dir = Path(output_dir) / "analysis"
        analysis_dir.mkdir(exist_ok=True)
        
        analysis_cmd = [
            "python", "analyze_solomon_results.py",
            "--results", benchmark_dir,
            "--output", str(analysis_dir)
        ]
        
        analysis_result = subprocess.run(
            analysis_cmd,
            capture_output=True, 
            text=True,
            env=dict(os.environ, PYTHONPATH=".")
        )
        
        # Guardar resultado del análisis en log
        with open(log_file, "a") as f:
            f.write("\n\n=== SALIDA DEL ANÁLISIS ===\n")
            f.write(analysis_result.stdout)
            if analysis_result.stderr:
                f.write("\n=== ERRORES DE ANÁLISIS ===\n")
                f.write(analysis_result.stderr)
        
        # Paso 4: Generar informe markdown
        print("\nGenerando informe resumen...")
        
        md_file = Path(output_dir) / "benchmark_report.md"
        
        # Leer resumen de algoritmos
        summary_csv = Path(analysis_dir) / "resumen_algoritmos.csv"
        summary_data = []
        if summary_csv.exists():
            import csv
            with open(summary_csv, 'r') as f:
                reader = csv.DictReader(f)
                summary_data = list(reader)
        
        # Generar informe
        with open(md_file, 'w') as f:
            f.write("# Informe de Benchmark Extendido Solomon VRP\n\n")
            f.write(f"Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            f.write("## Configuración\n\n")
            f.write(f"- Ejecuciones por algoritmo/instancia: {args.runs}\n")
            f.write(f"- Iteraciones por ejecución: {args.iterations}\n")
            f.write(f"- Algoritmos: {args.algorithms}\n")
            f.write(f"- Series Solomon: {args.series}\n\n")
            
            f.write("## Resumen de Resultados\n\n")
            
            if summary_data:
                f.write("| Algoritmo | Mejor Fitness | Fitness Promedio | Desviación Std | Tiempo (s) |\n")
                f.write("|-----------|--------------|------------------|----------------|------------|\n")
                
                for row in summary_data:
                    f.write(f"| {row['Algorithm']} | {float(row['Best']):.2f} | {float(row['Mean']):.2f} | ")
                    f.write(f"{float(row['Std']):.2f} | {float(row['Time']):.4f} |\n")
            
            f.write("\n## Gráficos\n\n")
            f.write(f"Los gráficos detallados se encuentran en el directorio `{analysis_dir}`:\n\n")
            f.write("- Comparación por serie\n")
            f.write("- Comparación por tipo de instancia\n")
            f.write("- Tiempos de ejecución\n")
            f.write("- Variabilidad (desviación estándar)\n")
            f.write("- Ranking de algoritmos\n\n")
            
            f.write("## Conclusiones\n\n")
            
            if summary_data:
                # Ordenar por mejor fitness
                sorted_data = sorted(summary_data, key=lambda x: float(x['Best']))
                best_algo = sorted_data[0]['Algorithm']
                
                # Ordenar por tiempo
                time_sorted = sorted(summary_data, key=lambda x: float(x['Time']))
                fastest_algo = time_sorted[0]['Algorithm']
                
                # Ordenar por estabilidad
                stability_sorted = sorted(summary_data, key=lambda x: float(x['Std']))
                most_stable = stability_sorted[0]['Algorithm']
                
                f.write(f"- El algoritmo **{best_algo}** obtuvo los mejores resultados (menor distancia).\n")
                f.write(f"- El algoritmo **{fastest_algo}** fue el más rápido.\n")
                f.write(f"- El algoritmo **{most_stable}** mostró mayor estabilidad (menor desviación estándar).\n\n")
            
            f.write(f"Para más detalles, consulte el reporte HTML completo: `{output_dir}/massive_benchmark_report.html`\n")
        
        print(f"\nBenchmark extendido completado en {(time.time() - start_time) / 60:.1f} minutos.")
        print(f"Resultados disponibles en: {output_dir}")
        print(f"Informe: {md_file}")
        
    except Exception as e:
        print(f"Error durante la ejecución del benchmark: {str(e)}")
        with open(log_file, "a") as f:
            f.write(f"\n\nERROR: {str(e)}\n")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
