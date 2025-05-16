#!/usr/bin/env python3
"""
Script para ejecutar un benchmark de algoritmos metaheurísticos y almacenar resultados en un directorio organizado.
"""

import os
import json
import click
import subprocess
from datetime import datetime
from algorithms import ALGORITHMS  # Asegúrate de que los algoritmos estén importados adecuadamente


@click.command()
@click.option("--algorithms", "-a", multiple=True, type=click.Choice(list(ALGORITHMS.keys())), required=True, help="Lista de algoritmos a ejecutar")
@click.option("--instances", "-i", multiple=True, help="Lista de instancias a evaluar")
@click.option("--instances", "-i", multiple=True, help="Lista de instancias a evaluar")
@click.option("--runs", "-r", default=30, help="Número de ejecuciones por algoritmo por instancia")
@click.option("--iterations", "-n", default=100, help="Número de iteraciones por ejecución")
@click.option("--population", "-p", default=30, help="Tamaño de la población")
@click.option("--parallel/--no-parallel", default=True, help="Ejecutar en paralelo")
@click.option("--seed", "-s", default=None, type=int, help="Semilla para reproducibilidad (aleatoria si no se especifica)")
@click.option("--seed", "-s", default=None, type=int, help="Semilla para reproducibilidad (aleatoria si no se especifica)")

def ejecutar_benchmark(algorithms, instances, runs, iterations, population, parallel):
    """
    Ejecuta el benchmark de los algoritmos seleccionados en las instancias dadas y almacena resultados en un directorio estructurado.
    """

    # Crear nombre de directorio de resultados basado en tiempo actual
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    result_dir = f'results/benchmark_{timestamp}'
    os.makedirs(result_dir, exist_ok=True)

    # Ejecutar cada algoritmo para cada instancia
    for instance in instances:
        for algorithm in algorithms:
            # Comando a ejecutar
            command = ["python", "scripts/run.py", "--algorithm", algorithm, "--instance", instance, "--iterations", str(iterations), "--population", str(population), "--runs", str(runs)]

            if parallel:
                command.append("--parallel")

            # Ejecutar el comando
            subprocess.run(command)

    # Generar informes y análisis
    # Aquí puedes incluir lógica para analizar los datos y generar informes en markdown o HTML
    # Guardar resultados de análisis
    report = {
        "message": "Resultados almacenados con éxito.",
        "algorithms": algorithms,
        "instances": instances,
        "runs": runs,
        "iterations": iterations,
        "population": population,
    }

    with open(f'{result_dir}/summary_report.json', 'w') as report_file:
        json.dump(report, report_file, indent=4)

    click.echo(f"Los resultados del benchmark han sido almacenados en {result_dir}")


if __name__ == '__main__':
    ejecutar_benchmark()