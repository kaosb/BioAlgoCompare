#!/usr/bin/env python3
"""
Script mejorado para ejecutar benchmarks de algoritmos metaheurísticos.
Incluye mejor manejo de errores y estructura para facilitar las pruebas.
"""

import os
import sys
import json
import click
import subprocess
import shutil
import re
import glob
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Import algorithms after adding to path
try:
    from scripts.config.algorithms import ALGORITHMS
except ImportError:
    # Fallback si no se encuentra el archivo
    ALGORITHMS = {
        "woa": "woa", "sma": "sma", "gto": "gto", "mrfo": "mrfo",
        "egto": "egto", "aha": "aha", "ewa": "ewa", "fsa": "fsa",
        "apo": "apo", "gvoa": "gvoa", "opa": "opa", "rro": "rro",
        "smo": "smo", "hoa": "hoa", "fgo": "fgo", "sho": "sho",
        "foa": "foa", "hho": "hho"
    }


def get_solomon_instances(series: str = "all") -> List[str]:
    """
    Obtiene la lista de instancias Solomon desde el directorio data/vrp/Solomon
    Filtrado por serie (101, 201 o all).
    """
    solomon_path = Path("data/vrp/Solomon")
    if not solomon_path.exists():
        click.echo("Error: No se encontró el directorio de instancias Solomon en data/vrp/Solomon/", err=True)
        return []
    
    instance_files = glob.glob(str(solomon_path / "*.vrp"))
    instances = []
    
    for f in instance_files:
        name = Path(f).stem
        if series == "all":
            instances.append(name)
        elif series == "101" and re.search(r'101$', name):
            instances.append(name)
        elif series == "201" and re.search(r'201$', name):
            instances.append(name)
    
    return sorted(instances)

def prepare_temp_files(instances: List[str]) -> None:
    """
    Prepara archivos temporales en data/vrp para las instancias Solomon.
    Copia las instancias desde data/vrp/Solomon a data/vrp.
    """
    for instance in instances:
        source = Path("data/vrp/Solomon") / f"{instance}.vrp"
        dest = Path("data/vrp") / f"{instance}.vrp"
        try:
            shutil.copy(source, dest)
            click.echo(f"Copiado: {source} -> {dest}")
        except Exception as e:
            click.echo(f"Error al copiar {source}: {str(e)}", err=True)

def cleanup_temp_files(instances: List[str]) -> None:
    """
    Elimina archivos temporales creados en data/vrp.
    """
    for instance in instances:
        dest = Path("data/vrp") / f"{instance}.vrp"
        try:
            if dest.exists():
                os.remove(dest)
                click.echo(f"Eliminado: {dest}")
        except Exception as e:
            click.echo(f"Error al eliminar {dest}: {str(e)}", err=True)


class BenchmarkRunner:
    """Clase para ejecutar benchmarks de forma testeable."""
    
    def __init__(self, result_base_dir: str = 'results'):
        """
        Inicializa el runner de benchmarks.
        
        Args:
            result_base_dir: Directorio base para almacenar resultados
        """
        self.result_base_dir = result_base_dir
        self.results: List[Dict[str, Any]] = []
        
    def create_result_directory(self, timestamp: Optional[str] = None) -> str:
        """
        Crea el directorio de resultados.
        
        Args:
            timestamp: Timestamp para el nombre del directorio (opcional)
            
        Returns:
            Path al directorio creado
        """
        if timestamp is None:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        result_dir = os.path.join(self.result_base_dir, f'massive_benchmark_{timestamp}')
        os.makedirs(result_dir, exist_ok=True)
        
        return result_dir
    
    def validate_instances(self, instances: List[str]) -> List[str]:
        """
        Valida que las instancias existan.
        
        Args:
            instances: Lista de nombres de instancias
            
        Returns:
            Lista de instancias válidas
            
        Raises:
            ValueError: Si alguna instancia no existe
        """
        data_dir = Path('data/vrp')
        valid_instances = []
        
        for instance in instances:
            # Añadir .vrp si no tiene extensión
            if not instance.endswith('.vrp'):
                instance_file = f"{instance}.vrp"
            else:
                instance_file = instance
                
            instance_path = data_dir / instance_file
            
            # Verificar en subdirectorios también
            if not instance_path.exists():
                # Buscar en Solomon
                solomon_path = data_dir / 'Solomon' / instance_file
                if solomon_path.exists():
                    instance_path = solomon_path
                else:
                    raise ValueError(f"Instancia no encontrada: {instance}")
            
            valid_instances.append(instance_file.replace('.vrp', ''))
            
        return valid_instances
    
    def run_algorithm(
        self,
        algorithm: str,
        instance: str,
        iterations: int,
        population: int,
        runs: int,
        parallel: bool = False
    ) -> Dict[str, Any]:
        """
        Ejecuta un algoritmo en una instancia.
        
        Args:
            algorithm: Nombre del algoritmo
            instance: Nombre de la instancia
            iterations: Número de iteraciones
            population: Tamaño de población
            runs: Número de ejecuciones
            parallel: Si ejecutar en paralelo
            
        Returns:
            Diccionario con resultados de la ejecución
        """
        # Construir comando (usa el nuevo run.py unificado)
        command = [
            sys.executable,  # Usar el mismo intérprete de Python
            str(Path("scripts/core/run.py")), # Usar Path para asegurar el formato correcto
            "--mode", "standard",
            "--algorithm", algorithm,
            "--instance", instance,
            "--iterations", str(iterations),
            "--population", str(population),
            "--runs", str(runs),
            "--v2"  # Usar versión v2 de los algoritmos
        ]
        
        if parallel:
            command.append("--parallel")
        
        # Ejecutar comando
        try:
            result = subprocess.run(
                command,
                capture_output=True,
                text=True,
                check=True
            )
            
            return {
                "algorithm": algorithm,
                "instance": instance,
                "status": "success",
                "stdout": result.stdout,
                "stderr": result.stderr,
                "returncode": result.returncode
            }
            
        except subprocess.CalledProcessError as e:
            return {
                "algorithm": algorithm,
                "instance": instance,
                "status": "error",
                "stdout": e.stdout,
                "stderr": e.stderr,
                "returncode": e.returncode,
                "error": str(e)
            }
    
    def run_benchmark(
        self,
        algorithms: List[str],
        instances: List[str],
        runs: int,
        iterations: int,
        population: int,
        parallel: bool = False,
        series: str = "all" # Nuevo parámetro para filtrar por serie
    ) -> str:
        """
        Ejecuta el benchmark completo.
        
        Args:
            algorithms: Lista de algoritmos
            instances: Lista de instancias
            runs: Número de ejecuciones por algoritmo
            iterations: Número de iteraciones
            population: Tamaño de población
            parallel: Si ejecutar en paralelo
            series: Filtro de series Solomon (101, 201, all)
            
        Returns:
            Path al directorio de resultados
        """
        # Si no se especifican instancias, obtenerlas de Solomon
        if not instances:
            selected_instances = get_solomon_instances(series)
            if not selected_instances:
                raise ValueError(f"No se encontraron instancias Solomon para la serie {series}")
            click.echo(f"Instancias Solomon seleccionadas ({len(selected_instances)}): {', '.join(selected_instances)}")
        else:
            selected_instances = self.validate_instances(instances)
        
        # Preparar archivos temporales (copiar de Solomon a data/vrp)
        click.echo("Preparando archivos temporales...")
        prepare_temp_files(selected_instances)

        # Crear directorio de resultados
        result_dir = self.create_result_directory()
        
        # Ejecutar benchmarks
        self.results = []
        total = len(selected_instances) * len(algorithms)
        current = 0
        
        try:
            for instance in selected_instances:
                for algorithm in algorithms:
                    current += 1
                    click.echo(f"[{current}/{total}] Ejecutando {algorithm} en {instance}...")
                    
                    result = self.run_algorithm(
                        algorithm, instance, iterations, 
                        population, runs, parallel
                    )
                    
                    self.results.append(result)
                    
                    # Mostrar estado
                    if result["status"] == "success":
                        click.echo(f"  ✓ Completado")
                    else:
                        click.echo(f"  ✗ Error: {result.get('error', 'Unknown')}")
            
            # Guardar resumen
            self.save_summary(result_dir, algorithms, selected_instances, 
                             runs, iterations, population)
            
        finally:
            # Limpiar archivos temporales
            click.echo("Limpiando archivos temporales...")
            cleanup_temp_files(selected_instances)
        
        return result_dir
    
    def save_summary(
        self,
        result_dir: str,
        algorithms: List[str],
        instances: List[str],
        runs: int,
        iterations: int,
        population: int
    ) -> None:
        """
        Guarda el resumen del benchmark.
        
        Args:
            result_dir: Directorio de resultados
            algorithms: Lista de algoritmos ejecutados
            instances: Lista de instancias evaluadas
            runs: Número de ejecuciones
            iterations: Número de iteraciones
            population: Tamaño de población
        """
        # Contar éxitos y errores
        successes = sum(1 for r in self.results if r["status"] == "success")
        errors = sum(1 for r in self.results if r["status"] == "error")
        
        summary = {
            "timestamp": datetime.now().isoformat(),
            "parameters": {
                "algorithms": algorithms,
                "instances": instances,
                "runs": runs,
                "iterations": iterations,
                "population": population
            },
            "results": {
                "total": len(self.results),
                "successes": successes,
                "errors": errors
            },
            "executions": self.results
        }
        
        # Guardar JSON
        summary_path = os.path.join(result_dir, 'summary_report.json')
        with open(summary_path, 'w') as f:
            json.dump(summary, f, indent=4)
        
        # Guardar reporte en texto
        report_path = os.path.join(result_dir, 'report.txt')
        with open(report_path, 'w') as f:
            f.write(f"Benchmark Report\n")
            f.write(f"================\n\n")
            f.write(f"Timestamp: {summary['timestamp']}\n")
            f.write(f"Algorithms: {', '.join(algorithms)}\n")
            f.write(f"Instances: {', '.join(instances)}\n")
            f.write(f"Runs per algorithm: {runs}\n")
            f.write(f"Iterations: {iterations}\n")
            f.write(f"Population size: {population}\n\n")
            f.write(f"Results:\n")
            f.write(f"  Total executions: {summary['results']['total']}\n")
            f.write(f"  Successful: {summary['results']['successes']}\n")
            f.write(f"  Errors: {summary['results']['errors']}\n")


@click.command()
@click.option(
    "--algorithms", "-a", 
    multiple=True, 
    type=click.Choice(list(ALGORITHMS.keys())),
    required=True,
    help="Lista de algoritmos a ejecutar"
)
@click.option(
    "--instances", "-i", 
    multiple=True,
    default=None,
    help="Lista de instancias a evaluar (sin extensión .vrp). Si no se especifica, se usarán todas las instancias Solomon de la serie especificada."
)
@click.option(
    "--runs", "-r", 
    default=30,
    help="Número de ejecuciones por algoritmo por instancia"
)
@click.option(
    "--iterations", "-n",
    default=100,
    help="Número de iteraciones por ejecución"
)
@click.option(
    "--population", "-p",
    default=30,
    help="Tamaño de la población"
)
@click.option(
    "--parallel/--no-parallel",
    default=True,
    help="Ejecutar en paralelo"
)
@click.option(
    "--series", 
    type=click.Choice(["101", "201", "all"]),
    default="all",
    help="Serie de instancias Solomon a utilizar (101, 201, o all). Solo aplica si no se especifican instancias manualmente."
)
@click.option(
    "--output-dir", "-o",
    default="results",
    help="Directorio base para resultados"
)
def ejecutar_benchmark(algorithms, instances, runs, iterations, population, parallel, series, output_dir):
    """
    Ejecuta el benchmark de los algoritmos seleccionados en las instancias dadas.
    """
    runner = BenchmarkRunner(output_dir)
    
    try:
        result_dir = runner.run_benchmark(
            list(algorithms),  # Convertir tupla a lista
            list(instances) if instances else [], # Pasar lista vacía si no hay instancias
            runs,
            iterations,
            population,
            parallel,
            series=series
        )
        
        click.echo(f"\n✓ Benchmark completado. Resultados en: {result_dir}")
        
        # Mostrar resumen
        successes = sum(1 for r in runner.results if r["status"] == "success")
        errors = sum(1 for r in runner.results if r["status"] == "error") 
        
        click.echo(f"\nResumen:")
        click.echo(f"  - Ejecuciones exitosas: {successes}")
        click.echo(f"  - Errores: {errors}")
        
    except ValueError as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)
    except Exception as e:
        click.echo(f"Error inesperado: {e}", err=True)
        sys.exit(1)


if __name__ == '__main__':
    ejecutar_benchmark()