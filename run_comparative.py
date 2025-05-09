#!/usr/bin/env python3
"""
Script para ejecutar benchmarks comparativos con diferentes cantidades de ejecuciones.
Este script ejecuta los mismos algoritmos con 10, 100 y 1000 ejecuciones cada uno para
proveer análisis estadístico riguroso sobre la influencia del número de ejecuciones.
"""

import click
import os
import subprocess
import time
from datetime import datetime

@click.command()
@click.option('--instances', '-i', multiple=True, help='Instancias para el benchmark')
@click.option('--algorithms', '-a', multiple=True, help='Algoritmos para el benchmark')
@click.option('--iterations', '-n', default=50, help='Número de iteraciones por ejecución')
@click.option('--population', '-p', default=30, help='Tamaño de población')
@click.option('--parallel/--no-parallel', default=True, help='Usar ejecución paralela')
@click.option('--optimize/--no-optimize', default=False, help='Aplicar optimización local')
@click.option('--base-dir', '-d', default="results/comparative", help='Directorio base para resultados')
def main(instances, algorithms, iterations, population, parallel, optimize, base_dir):
    """
    Ejecuta benchmarks con 10, 100 y 1000 ejecuciones para análisis estadístico comparativo.
    
    Este script ejecuta automáticamente los tres escenarios y genera informes individuales
    y comparativos para entender la influencia del número de ejecuciones en la calidad del análisis.
    """
    # Verificar que se han proporcionado instancias y algoritmos
    if not instances:
        instances = ['P-n16-k8']  # Instancia pequeña por defecto
        click.echo(f"No se especificaron instancias, usando por defecto: {', '.join(instances)}")
    
    if not algorithms:
        algorithms = ['sho', 'egto', 'foa']  # Algoritmos por defecto
        click.echo(f"No se especificaron algoritmos, usando por defecto: {', '.join(algorithms)}")
    
    # Configurar directorios de salida
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    base_output_dir = f"{base_dir}/{timestamp}"
    os.makedirs(base_output_dir, exist_ok=True)
    
    # Escenarios a ejecutar
    scenarios = [
        {"runs": 10, "name": "10_runs"},
        {"runs": 100, "name": "100_runs"},
        {"runs": 1000, "name": "1000_runs"}
    ]
    
    # Archivo para almacenar tiempos de ejecución
    timing_info = []
    
    # Ejecutar cada escenario
    for scenario in scenarios:
        runs = scenario["runs"]
        scenario_name = scenario["name"]
        output_dir = f"{base_output_dir}/{scenario_name}"
        
        click.echo(f"\n\n{'='*80}")
        click.echo(f"Ejecutando escenario: {runs} ejecuciones")
        click.echo(f"{'='*80}")
        
        # Construir comando
        cmd = ["python", "analyze_results.py", "--run-benchmark"]
        
        # Añadir instancias
        for instance in instances:
            cmd.extend(["--instances", instance])
        
        # Añadir algoritmos
        for algorithm in algorithms:
            cmd.extend(["--algorithms", algorithm])
        
        # Añadir parámetros
        cmd.extend([
            "--runs", str(runs),
            "--iterations", str(iterations),
            "--population", str(population),
            "--output-dir", output_dir
        ])
        
        # Añadir flags opcionales
        if parallel:
            cmd.append("--parallel")
        
        if optimize:
            cmd.append("--optimize")
        
        # Registrar tiempo de inicio
        start_time = time.time()
        
        # Ejecutar comando
        click.echo(f"Ejecutando comando: {' '.join(cmd)}")
        try:
            process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            
            # Mostrar salida en tiempo real
            while True:
                output = process.stdout.readline()
                if output == '' and process.poll() is not None:
                    break
                if output:
                    click.echo(output.strip())
            
            # Capturar errores
            stderr = process.stderr.read()
            if stderr:
                click.echo(f"Error: {stderr}")
            
            # Verificar código de salida
            if process.returncode != 0:
                click.echo(f"Error: El comando terminó con código {process.returncode}")
            
        except Exception as e:
            click.echo(f"Error al ejecutar el comando: {str(e)}")
        
        # Registrar tiempo de fin
        execution_time = time.time() - start_time
        
        # Guardar información de tiempos
        timing_info.append({
            "scenario": scenario_name,
            "runs": runs,
            "execution_time": execution_time,
            "algorithms": list(algorithms),
            "instances": list(instances),
            "iterations": iterations,
            "parallel": parallel
        })
        
        click.echo(f"Escenario {scenario_name} completado en {execution_time:.2f} segundos")
    
    # Generar informe comparativo básico
    comparative_report_path = os.path.join(base_output_dir, "comparative_report.md")
    
    with open(comparative_report_path, "w") as f:
        f.write("# Informe Comparativo de Escenarios\n\n")
        f.write(f"Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        
        f.write("## Configuración del experimento\n\n")
        f.write(f"- Instancias: {', '.join(instances)}\n")
        f.write(f"- Algoritmos: {', '.join(algorithms)}\n")
        f.write(f"- Iteraciones por ejecución: {iterations}\n")
        f.write(f"- Tamaño de población: {population}\n")
        f.write(f"- Ejecución paralela: {'Sí' if parallel else 'No'}\n")
        f.write(f"- Optimización local: {'Sí' if optimize else 'No'}\n\n")
        
        f.write("## Resumen de tiempos de ejecución\n\n")
        f.write("| Escenario | Ejecuciones | Tiempo total (s) | Tiempo por ejecución (ms) |\n")
        f.write("|-----------|-------------|------------------|---------------------------|\n")
        
        for info in timing_info:
            time_per_run = (info["execution_time"] * 1000) / info["runs"]
            f.write(f"| {info['scenario']} | {info['runs']} | {info['execution_time']:.2f} | {time_per_run:.2f} |\n")
        
        f.write("\n## Rutas a los informes detallados\n\n")
        
        for scenario in scenarios:
            scenario_dir = f"{base_output_dir}/{scenario['name']}"
            f.write(f"### Escenario: {scenario['name']} ({scenario['runs']} ejecuciones)\n\n")
            
            # Listar archivos generados
            if os.path.exists(scenario_dir):
                report_files = [f for f in os.listdir(scenario_dir) if f.endswith('.html')]
                
                if report_files:
                    f.write("Informes generados:\n\n")
                    for report_file in report_files:
                        f.write(f"- [{report_file}]({scenario['name']}/{report_file})\n")
                else:
                    f.write("No se encontraron informes HTML en este directorio.\n")
            else:
                f.write("Directorio no encontrado. Es posible que la ejecución haya fallado.\n")
            
            f.write("\n")
        
        f.write("\n## Conclusiones preliminares\n\n")
        f.write("Para un análisis detallado de los resultados, por favor consultar los informes individuales de cada escenario.\n")
    
    click.echo(f"\nTodos los escenarios completados. Informe comparativo generado en {comparative_report_path}")
    click.echo(f"Ruta base de resultados: {base_output_dir}")

if __name__ == "__main__":
    main()