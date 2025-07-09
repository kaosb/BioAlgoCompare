#!/usr/bin/env python3
"""
Script para gestionar la base de datos de resultados.

Proporciona comandos para importar, consultar, analizar y mantener
la base de datos SQLite de resultados experimentales.
"""

import sys
import os
from pathlib import Path
import click
import json
import pandas as pd
from datetime import datetime, timedelta
from typing import Optional
import logging

# Añadir el directorio raíz al path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from utils.results_database import ResultsDatabase, DatabaseQuery
from utils.result_schema import StandardResult
from utils.experiment_tracker import ExperimentTracker
from utils.result_integration import ResultIntegration


# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@click.group()
@click.option('--db-path', default='results.db', help='Ruta a la base de datos')
@click.pass_context
def cli(ctx, db_path):
    """Gestiona la base de datos de resultados experimentales."""
    ctx.ensure_object(dict)
    ctx.obj['db'] = ResultsDatabase(db_path)
    ctx.obj['query'] = DatabaseQuery(ctx.obj['db'])


@cli.command()
@click.argument('result_file', type=click.Path(exists=True))
@click.option('--format', type=click.Choice(['json', 'experiment']), 
              default='json', help='Formato del archivo')
@click.pass_context
def import_result(ctx, result_file, format):
    """Importa un resultado a la base de datos."""
    db = ctx.obj['db']
    
    try:
        if format == 'json':
            # Cargar resultado estándar
            result = StandardResult.from_json(result_file)
        else:
            # Cargar formato de experimento y convertir
            with open(result_file, 'r') as f:
                data = json.load(f)
            
            from utils.experiment_tracker import ExperimentRecord
            record = ExperimentRecord(**data)
            result = ResultIntegration.experiment_to_standard(record)
        
        # Insertar en base de datos
        if db.insert_result(result):
            click.echo(f"✅ Resultado {result.result_id} importado exitosamente")
        else:
            click.echo(f"⚠️  El resultado {result.result_id} ya existe en la base de datos")
            
    except Exception as e:
        click.echo(f"❌ Error importando resultado: {e}", err=True)


@cli.command()
@click.argument('directory', type=click.Path(exists=True))
@click.option('--pattern', default='*.json', help='Patrón de archivos')
@click.option('--format', type=click.Choice(['json', 'experiment']), 
              default='json', help='Formato de archivos')
@click.option('--recursive/--no-recursive', default=True, 
              help='Buscar recursivamente')
@click.pass_context
def import_directory(ctx, directory, pattern, format, recursive):
    """Importa todos los resultados de un directorio."""
    db = ctx.obj['db']
    directory = Path(directory)
    
    # Buscar archivos
    if recursive:
        files = list(directory.rglob(pattern))
    else:
        files = list(directory.glob(pattern))
    
    click.echo(f"Encontrados {len(files)} archivos para importar")
    
    imported = 0
    errors = 0
    
    with click.progressbar(files, label='Importando') as bar:
        for file in bar:
            try:
                if format == 'json':
                    result = StandardResult.from_json(file)
                else:
                    with open(file, 'r') as f:
                        data = json.load(f)
                    from utils.experiment_tracker import ExperimentRecord
                    record = ExperimentRecord(**data)
                    result = ResultIntegration.experiment_to_standard(record)
                
                if db.insert_result(result):
                    imported += 1
            except Exception as e:
                logger.error(f"Error con {file}: {e}")
                errors += 1
    
    click.echo(f"\n✅ Importados: {imported} resultados")
    if errors:
        click.echo(f"❌ Errores: {errors} archivos")


@cli.command()
@click.option('-a', '--algorithm', help='Filtrar por algoritmo')
@click.option('-p', '--problem', help='Filtrar por problema')
@click.option('--min-fitness', type=float, help='Fitness mínimo')
@click.option('--max-fitness', type=float, help='Fitness máximo')
@click.option('--limit', type=int, default=20, help='Límite de resultados')
@click.option('--export', type=click.Path(), help='Exportar a CSV')
@click.pass_context
def search(ctx, algorithm, problem, min_fitness, max_fitness, limit, export):
    """Busca resultados en la base de datos."""
    db = ctx.obj['db']
    
    results = db.search_results(
        algorithm=algorithm,
        problem=problem,
        min_fitness=min_fitness,
        max_fitness=max_fitness,
        limit=limit
    )
    
    if not results:
        click.echo("No se encontraron resultados")
        return
    
    # Crear DataFrame para mostrar
    df = pd.DataFrame(results)
    
    # Mostrar resultados
    click.echo(f"\nEncontrados {len(results)} resultados:")
    click.echo("-" * 100)
    
    # Columnas a mostrar
    columns = ['result_id', 'algorithm_name', 'problem_name', 
               'best_fitness', 'mean_fitness', 'gap_to_optimal']
    
    for _, row in df[columns].iterrows():
        click.echo(
            f"{row['result_id'][:20]:20s} | "
            f"{row['algorithm_name']:10s} | "
            f"{row['problem_name']:12s} | "
            f"Best: {row['best_fitness']:8.2f} | "
            f"Mean: {row['mean_fitness']:8.2f} | "
            f"Gap: {row['gap_to_optimal']:6.2f}%"
        )
    
    # Exportar si se solicita
    if export:
        df.to_csv(export, index=False)
        click.echo(f"\n✅ Resultados exportados a {export}")


@cli.command()
@click.argument('result_id')
@click.option('--show-runs/--no-show-runs', default=False, 
              help='Mostrar runs individuales')
@click.option('--export', type=click.Path(), help='Exportar a JSON')
@click.pass_context
def show(ctx, result_id, show_runs, export):
    """Muestra detalles de un resultado específico."""
    db = ctx.obj['db']
    
    result = db.get_result(result_id)
    if not result:
        click.echo(f"❌ No se encontró el resultado {result_id}")
        return
    
    # Mostrar información general
    click.echo("\n" + "="*60)
    click.echo(f"RESULTADO: {result.result_id}")
    click.echo("="*60)
    
    click.echo(f"\nAlgoritmo: {result.algorithm_info.name} v{result.algorithm_info.version}")
    click.echo(f"Problema: {result.problem_info.name} (dim={result.problem_info.dimension})")
    click.echo(f"Configuración: pop={result.algorithm_info.population_size}, "
               f"iter={result.algorithm_info.max_iterations}")
    
    if result.algorithm_info.parameters:
        click.echo("Parámetros:")
        for k, v in result.algorithm_info.parameters.items():
            click.echo(f"  - {k}: {v}")
    
    click.echo(f"\nEjecuciones: {result.statistics.n_runs}")
    click.echo(f"Mejor fitness: {result.statistics.best_fitness:.4f}")
    click.echo(f"Media ± std: {result.statistics.mean_fitness:.4f} ± "
               f"{result.statistics.std_fitness:.4f}")
    click.echo(f"Mediana: {result.statistics.median_fitness:.4f}")
    click.echo(f"IQR: {result.statistics.iqr_fitness:.4f}")
    
    gap = result.get_gap_to_optimal()
    if gap is not None:
        click.echo(f"Gap al óptimo: {gap:.2f}%")
    
    click.echo(f"\nTiempo total: {result.statistics.total_execution_time:.2f}s")
    click.echo(f"Tiempo promedio: {result.statistics.mean_execution_time:.2f}s")
    
    click.echo(f"\nPlataforma: {result.execution_info.platform}")
    click.echo(f"CPUs: {result.execution_info.cpu_count}")
    click.echo(f"Timestamp: {result.timestamp}")
    
    # Mostrar runs individuales si se solicita
    if show_runs:
        click.echo("\nRuns individuales:")
        click.echo("-" * 60)
        for run in result.runs:
            click.echo(f"  Run {run.run_id}: fitness={run.best_fitness:.4f}, "
                      f"time={run.execution_time:.2f}s, seed={run.seed}")
    
    # Exportar si se solicita
    if export:
        result.to_json(export)
        click.echo(f"\n✅ Resultado exportado a {export}")


@cli.command()
@click.pass_context
def best_results(ctx):
    """Muestra los mejores resultados por problema."""
    db = ctx.obj['db']
    
    df = db.get_best_results_by_problem()
    
    if df.empty:
        click.echo("No hay resultados en la base de datos")
        return
    
    click.echo("\nMEJORES RESULTADOS POR PROBLEMA")
    click.echo("="*80)
    
    current_problem = None
    for _, row in df.iterrows():
        if row['problem_name'] != current_problem:
            current_problem = row['problem_name']
            click.echo(f"\n{current_problem}:")
            click.echo("-" * 40)
        
        click.echo(f"  {row['algorithm_name']:10s}: {row['best_fitness']:8.2f} "
                  f"(gap={row['best_gap']:6.2f}%) - {row['n_experiments']} exp.")


@cli.command()
@click.argument('algorithms', nargs=-1, required=True)
@click.option('-p', '--problems', multiple=True, help='Problemas específicos')
@click.option('--export', type=click.Path(), help='Exportar comparación')
@click.pass_context
def compare(ctx, algorithms, problems, export):
    """Compara múltiples algoritmos."""
    query = ctx.obj['query']
    
    df = query.compare_algorithms(list(algorithms), list(problems) if problems else None)
    
    if df.empty:
        click.echo("No hay datos para comparar")
        return
    
    click.echo(f"\nCOMPARACIÓN: {', '.join(algorithms)}")
    click.echo("="*100)
    
    # Agrupar por problema
    for problem in df['problem_name'].unique():
        problem_df = df[df['problem_name'] == problem].sort_values('best_fitness')
        
        click.echo(f"\n{problem}:")
        click.echo("-" * 80)
        
        for _, row in problem_df.iterrows():
            click.echo(
                f"  {row['algorithm_name']:10s}: "
                f"Best={row['best_fitness']:8.2f}, "
                f"Avg={row['avg_fitness']:8.2f}±{row['avg_std']:6.2f}, "
                f"Time={row['avg_time']:6.2f}s, "
                f"N={row['n_experiments']}"
            )
    
    if export:
        df.to_csv(export, index=False)
        click.echo(f"\n✅ Comparación exportada a {export}")


@cli.command()
@click.argument('algorithm')
@click.option('--export', type=click.Path(), help='Exportar análisis')
@click.pass_context
def analyze_algorithm(ctx, algorithm, export):
    """Analiza el rendimiento de un algoritmo."""
    db = ctx.obj['db']
    
    df = db.get_algorithm_performance(algorithm)
    
    if df.empty:
        click.echo(f"No hay datos para {algorithm}")
        return
    
    click.echo(f"\nANÁLISIS DE {algorithm.upper()}")
    click.echo("="*80)
    
    # Estadísticas generales
    total_exp = df['n_experiments'].sum()
    avg_gap = df['best_gap'].mean()
    
    click.echo(f"\nTotal de experimentos: {total_exp}")
    click.echo(f"Problemas evaluados: {len(df)}")
    click.echo(f"Gap promedio al óptimo: {avg_gap:.2f}%")
    
    click.echo("\nRendimiento por problema:")
    click.echo("-" * 60)
    
    for _, row in df.iterrows():
        click.echo(
            f"{row['problem_name']:12s}: "
            f"Best={row['best_fitness']:8.2f}, "
            f"Gap={row['best_gap']:6.2f}%, "
            f"Time={row['avg_time']:6.2f}s"
        )
    
    if export:
        df.to_csv(export, index=False)
        click.echo(f"\n✅ Análisis exportado a {export}")


@cli.command()
@click.option('--output-dir', default='db_export', help='Directorio de salida')
@click.pass_context
def export_all(ctx, output_dir):
    """Exporta toda la base de datos a CSV."""
    db = ctx.obj['db']
    
    click.echo(f"Exportando base de datos a {output_dir}...")
    db.export_to_csv(output_dir)
    click.echo("✅ Exportación completada")


@cli.command()
@click.argument('backup_path')
@click.pass_context
def backup(ctx, backup_path):
    """Crea un respaldo de la base de datos."""
    db = ctx.obj['db']
    
    db.backup(backup_path)
    click.echo(f"✅ Respaldo creado en {backup_path}")


@cli.command()
@click.pass_context
def stats(ctx):
    """Muestra estadísticas de la base de datos."""
    db = ctx.obj['db']
    
    stats = db.get_statistics()
    
    click.echo("\nESTADÍSTICAS DE LA BASE DE DATOS")
    click.echo("="*60)
    
    click.echo(f"Total de resultados: {stats['total_results']}")
    click.echo(f"Total de runs: {stats['total_runs']}")
    click.echo(f"Algoritmos únicos: {stats['unique_algorithms']}")
    click.echo(f"Problemas únicos: {stats['unique_problems']}")
    
    if 'best_result' in stats:
        best = stats['best_result']
        click.echo(f"\nMejor resultado global:")
        click.echo(f"  {best['algorithm_name']} en {best['problem_name']}: "
                  f"{best['best_fitness']:.4f}")
    
    if 'date_range' in stats:
        dates = stats['date_range']
        click.echo(f"\nRango de fechas:")
        click.echo(f"  Primer experimento: {dates['first']}")
        click.echo(f"  Último experimento: {dates['last']}")


@cli.command()
@click.option('--days', default=30, help='Días de antigüedad')
@click.option('--confirm/--no-confirm', default=True, 
              help='Confirmar eliminación')
@click.pass_context
def cleanup(ctx, days, confirm):
    """Elimina resultados antiguos."""
    db = ctx.obj['db']
    
    # Primero contar cuántos se eliminarían
    cutoff = datetime.now() - timedelta(days=days)
    
    results = db.search_results(end_date=cutoff)
    n_delete = len(results)
    
    if n_delete == 0:
        click.echo(f"No hay resultados con más de {days} días de antigüedad")
        return
    
    click.echo(f"Se encontraron {n_delete} resultados con más de {days} días")
    
    if confirm:
        if not click.confirm("¿Desea eliminarlos?"):
            click.echo("Operación cancelada")
            return
    
    deleted = db.cleanup_old_results(days)
    click.echo(f"✅ Eliminados {deleted} resultados")


@cli.command()
@click.argument('algorithm')
@click.argument('problem')
@click.option('-m', '--metric', default='best_fitness', 
              help='Métrica a optimizar')
@click.pass_context
def find_optimal(ctx, algorithm, problem, metric):
    """Encuentra los parámetros óptimos para un algoritmo."""
    query = ctx.obj['query']
    
    result = query.find_optimal_parameters(algorithm, problem, metric)
    
    if not result:
        click.echo(f"No se encontraron resultados para {algorithm} en {problem}")
        return
    
    click.echo(f"\nPARÁMETROS ÓPTIMOS: {algorithm} en {problem}")
    click.echo("="*60)
    click.echo(f"Result ID: {result['result_id']}")
    click.echo(f"{metric}: {result['metric_value']:.4f}")
    
    click.echo("\nParámetros:")
    for k, v in result['parameters'].items():
        click.echo(f"  - {k}: {v}")


@cli.command()
@click.argument('algorithm')
@click.argument('problem')
@click.option('--export', type=click.Path(), help='Exportar timeline')
@click.pass_context
def timeline(ctx, algorithm, problem, export):
    """Muestra la evolución temporal de mejoras."""
    query = ctx.obj['query']
    
    df = query.get_improvement_timeline(algorithm, problem)
    
    if df.empty:
        click.echo(f"No hay datos para {algorithm} en {problem}")
        return
    
    click.echo(f"\nTIMELINE: {algorithm} en {problem}")
    click.echo("="*60)
    
    for _, row in df.iterrows():
        timestamp = row['timestamp']
        if isinstance(timestamp, str):
            timestamp = timestamp.split('T')[0]
        
        improvement_str = f"+{row['improvement']:.2f}" if row['improvement'] > 0 else ""
        
        click.echo(
            f"{timestamp} | "
            f"Best: {row['best_fitness']:8.2f} {improvement_str:>8s} | "
            f"Gap: {row['gap_to_optimal']:6.2f}%"
        )
    
    if export:
        df.to_csv(export, index=False)
        click.echo(f"\n✅ Timeline exportado a {export}")


if __name__ == '__main__':
    cli()