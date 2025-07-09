#!/usr/bin/env python3
"""
BioAlgoCompare - CLI unificado para algoritmos bio-inspirados en VRP

Interfaz de línea de comandos principal que integra todas las funcionalidades:
- Ejecución de algoritmos
- Análisis de resultados
- Benchmarking
- Gestión de datasets
- Migración de algoritmos
"""

import click
import sys
import os
import re
from pathlib import Path
import glob
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np

from scripts.core.run import main as run_main
from scripts.benchmark import BenchmarkRunner
from scripts.utilities.manage_datasets import DatasetManager, extract_data_from_solomon, convert_to_vrp_format
from scripts.utilities.migrate_algorithm import AlgorithmMigrator
from scripts.utilities.inventory import scan_repository, detect_data_usage, generate_inventory_report
from scripts.algorithms_v2 import ALGORITHMS_V2

# Añadir el directorio del proyecto al path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


@click.group()
@click.version_option(version='2.0.0', prog_name='BioAlgoCompare')
@click.pass_context
def cli(ctx):
    """
    BioAlgoCompare - Framework para algoritmos bio-inspirados en VRP
    
    Una suite completa para experimentación con metaheurísticas bio-inspiradas
    aplicadas al Problema de Ruteo de Vehículos (VRP).
    
    Ejemplos de uso:
    
    \b
    # Ejecutar un algoritmo
    bioalgocompare run woa P-n16-k8.vrp
    
    \b
    # Ejecutar benchmark completo
    bioalgocompare benchmark --algorithms woa,sma,gto --instances P-n16-k8,P-n19-k2
    
    \b
    # Analizar resultados
    bioalgocompare analyze results/experiment_20240101_120000.json
    
    \b
    # Gestionar datasets
    bioalgocompare datasets check
    """
    # Asegurar que existen los directorios necesarios
    directories = ['results', 'plots', 'checkpoints', 'data/vrp']
    for directory in directories:
        Path(directory).mkdir(parents=True, exist_ok=True)


@cli.command()
@click.argument('algorithm', type=click.Choice([
    'sho', 'apo', 'egto', 'fsa', 'foa', 'woa', 'hho', 'mrfo',
    'sma', 'gto', 'ewa', 'aha', 'rro', 'gvoa', 'smo', 'opa',
    'hoa', 'fgo'
]))
@click.argument('instance')
@click.option('--population', '-p', default=30, help='Tamaño de población')
@click.option('--iterations', '-n', default=100, help='Número de iteraciones')
@click.option('--runs', '-r', default=30, help='Número de ejecuciones')
@click.option('--seed', '-s', type=int, help='Semilla aleatoria')
@click.option('--parallel/--no-parallel', default=True, help='Ejecución paralela')
@click.option('--workers', '-w', type=int, help='Número de workers paralelos')
@click.option('--mode', type=click.Choice(['standard', 'massive', 'experiment']), 
              default='standard', help='Modo de ejecución')
@click.option('--checkpoint-interval', default=100, 
              help='Intervalo de checkpoint (modo massive)')
@click.option('--plot/--no-plot', default=False, help='Generar gráficos')
@click.option('--v2/--v1', default=True, help='Usar versión v2 del algoritmo')
def run(algorithm, instance, population, iterations, runs, seed, 
        parallel, workers, mode, checkpoint_interval, plot, v2):
    """
    Ejecuta un algoritmo en una instancia VRP.
    
    \b
    ALGORITHM: Algoritmo a ejecutar (woa, sma, gto, etc.)
    INSTANCE: Archivo de instancia VRP (ej: P-n16-k8.vrp)
    
    Ejemplos:
    
    \b
    # Ejecución básica
    bioalgocompare run woa P-n16-k8.vrp
    
    \b
    # Ejecución con parámetros personalizados
    bioalgocompare run sma P-n19-k2.vrp -p 50 -n 200 -r 50
    
    \b
    # Modo massive con checkpoint
    bioalgocompare run gto P-n16-k8.vrp --mode massive --checkpoint-interval 100
    """
    # Preparar argumentos para el script run
    args = [
        '--mode', mode,
        '--algorithm', algorithm,
        '--instance', instance,
        '--population', str(population),
        '--iterations', str(iterations),
        '--runs', str(runs),
    ]
    
    if seed:
        args.extend(['--seed', str(seed)])
    
    if parallel:
        args.append('--parallel')
    else:
        args.append('--no-parallel')
    
    if workers:
        args.extend(['--workers', str(workers)])
    
    if mode == 'massive':
        args.extend(['--massive-runs', '1000'])
        args.extend(['--checkpoint-interval', str(checkpoint_interval)])
    
    if plot:
        args.append('--plot')
    
    if v2:
        args.append('--v2')
    else:
        args.append('--v1')
    
    # Ejecutar con contexto simulado
    ctx = click.Context(run_main)
    ctx.invoke(run_main, **{
        'mode': mode,
        'algorithm': algorithm,
        'instance': instance,
        'population': population,
        'iterations': iterations,
        'runs': runs,
        'massive_runs': 1000 if mode == 'massive' else runs,
        'seed': seed,
        'parallel': parallel,
        'workers': workers,
        'checkpoint_interval': checkpoint_interval,
        'resume': False,
        'experiment_seeds': None,
        'output_dir': 'results',
        'plot': plot,
        'v2': v2
    })


@cli.command()
@click.option('--algorithms', '-a', required=True, 
              help='Algoritmos a ejecutar (separados por coma)')
@click.option('--instances', '-i', default=None,
              help='Instancias VRP (separadas por coma). Si no se especifica, se usarán todas las instancias Solomon de la serie especificada.')
@click.option('--population', '-p', default=30, help='Tamaño de población')
@click.option('--iterations', '-n', default=100, help='Número de iteraciones')
@click.option('--runs', '-r', default=30, help='Número de ejecuciones por algoritmo')
@click.option('--parallel/--no-parallel', default=True, help='Ejecución paralela')
@click.option('--series', type=click.Choice(["101", "201", "all"]),
              default="all", help="Serie de instancias Solomon a utilizar (101, 201, o all). Solo aplica si no se especifican instancias manualmente.")
@click.option('--output-dir', '-o', default='results', help='Directorio de salida')
def benchmark(algorithms, instances, population, iterations, runs, parallel, series, output_dir):
    """
    Ejecuta un benchmark completo con múltiples algoritmos e instancias.
    
    Ejemplos:
    
    \b
    # Benchmark básico
    bioalgocompare benchmark -a woa,sma,gto -i P-n16-k8,P-n19-k2
    
    \b
    # Benchmark con parámetros personalizados
    bioalgocompare benchmark -a woa,sma,gto,mrfo -i P-n16-k8,P-n19-k2,P-n20-k2 \
        -p 50 -n 200 -r 50
    
    \b
    # Benchmark de todas las instancias Solomon 101
    bioalgocompare benchmark -a woa,sma --series 101
    """
    # Parsear algoritmos e instancias
    algo_list = [a.strip() for a in algorithms.split(',')]
    instance_list = [i.strip() for i in instances.split(',')] if instances else []
    
    # Crear runner
    runner = BenchmarkRunner(result_base_dir=output_dir)
    
    click.echo("🚀 Iniciando benchmark")
    click.echo(f"📊 Algoritmos: {', '.join(algo_list)}")
    click.echo(f"📁 Instancias: {', '.join(instance_list) if instance_list else series}")
    click.echo(f"🔢 Configuración: {population} individuos, {iterations} iteraciones, {runs} runs")
    
    # Ejecutar benchmark
    try:
        result_dir = runner.run_benchmark(
            algorithms=algo_list,
            instances=instance_list,
            runs=runs,
            iterations=iterations,
            population=population,
            parallel=parallel,
            series=series
        )
        
        click.echo("\n✅ Benchmark completado")
        click.echo(f"📁 Resultados guardados en: {result_dir}")
        
    except Exception as e:
        click.echo(f"❌ Error durante el benchmark: {str(e)}", err=True)
        sys.exit(1)


def load_benchmark_results(results_dir):
    """Carga los resultados del benchmark desde un directorio"""
    summary_path = Path(results_dir) / "massive_benchmark_summary.csv"
    
    if not summary_path.exists():
        click.echo(f"Error: No se encontró el archivo de resumen en {summary_path}", err=True)
        return None
    
    try:
        df = pd.read_csv(summary_path)
        return df
    except Exception as e:
        click.echo(f"Error al cargar el archivo CSV: {e}", err=True)
        return None

def create_comparison_charts(df, output_dir="benchmark_comparisons"):
    """Crea gráficos comparativos entre algoritmos y series de Solomon"""
    output_path = Path(output_dir)
    output_path.mkdir(exist_ok=True, parents=True)
    
    click.echo(f"Generando gráficos comparativos en {output_dir}")
    
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
    summary_table = df.groupby("Algorithm")["Best", "Mean", "Std", "Time"].mean().reset_index()
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
    
    click.echo(f"Análisis completado. Gráficos guardados en {output_dir}")
    return output_path

@cli.command()
@click.argument('results_dir', type=click.Path(exists=True))
@click.option('--output-dir', '-o', default="benchmark_comparisons", help='Directorio para guardar análisis')
def analyze(results_dir, output_dir):
    """
    Analiza resultados de benchmarks en instancias Solomon.
    
    \b
    RESULTS_DIR: Directorio con resultados del benchmark (ej: results/massive_benchmark_YYYYMMDD_HHMMSS)
    
    Ejemplos:
    
    \b
    # Análisis básico
    bioalgocompare analyze results/massive_benchmark_20240101_120000
    
    \b
    # Análisis y guardar en directorio específico
    bioalgocompare analyze results/massive_benchmark_20240101_120000 -o my_analysis_plots
    """
    click.echo(f"📊 Analizando resultados en: {results_dir}")
    
    # Cargar resultados
    df = load_benchmark_results(results_dir)
    if df is None:
        return
    
    click.echo(f"📈 Cargados datos de {len(df)} filas con {len(df['Algorithm'].unique())} algoritmos")
    
    # Crear gráficos
    output_path = create_comparison_charts(df, output_dir)
    
    # Mostrar un resumen
    click.echo("\nResumen de resultados:")
    algo_summary = df.groupby("Algorithm")["Best"].agg(["min", "mean", "std"]).reset_index()
    algo_summary.columns = ["Algoritmo", "Mejor", "Promedio", "Desv. Std."]
    click.echo(algo_summary.to_string(index=False))
    
    click.echo(f"\nAnálisis completo disponible en: {output_path}")
    click.echo("\n✅ Análisis completado")


@cli.group()
def datasets():
    """Gestiona los datasets VRP."""
    pass




@datasets.command()
def check():
    """
    Verifica la disponibilidad de datasets.
    
    Ejemplo:
    bioalgocompare datasets check
    """
    manager = DatasetManager()
    manager.check_datasets()
    manager.generate_report()


@datasets.command()
@click.option('--source', default='standard', help='Fuente de datasets')
def download():
    """
    Descarga datasets faltantes.
    
    Ejemplo:
    bioalgocompare datasets download
    """
    manager = DatasetManager()
    manager.download_missing_datasets()


@datasets.command()
@click.argument('files', nargs=-1, type=click.Path(exists=True))
@click.option('--output-dir', '-o', default=None, help='Directorio de salida (por defecto, sobrescribe los originales)')
def convert(files, output_dir):
    """
    Convierte archivos Solomon 101 al formato requerido por VRPProblem.
    
    \b
    FILES: Archivos o patrones a convertir (ej: data/vrp/Solomon/*.txt)
    
    Ejemplos:
    
    \b
    # Convertir un solo archivo
    bioalgocompare datasets convert data/vrp/Solomon/C101.txt
    
    \b
    # Convertir múltiples archivos usando un patrón
    bioalgocompare datasets convert "data/vrp/Solomon/*.txt" -o data/vrp/converted
    """
    all_files = []
    for pattern in files:
        matched = glob.glob(pattern)
        if matched:
            all_files.extend(matched)
        else:
            click.echo(f"Advertencia: No se encontraron archivos para '{pattern}'", err=True)
    
    if not all_files:
        click.echo("Error: No se encontraron archivos para procesar", err=True)
        sys.exit(1)
    
    for file_path in all_files:
        try:
            click.echo(f"Procesando: {file_path}")
            data = extract_data_from_solomon(file_path)
            
            # Determinar ruta de salida
            if output_dir:
                output_dir_path = Path(output_dir)
                output_dir_path.mkdir(exist_ok=True, parents=True)
                output_path = output_dir_path / Path(file_path).name
            else:
                output_path = Path(file_path)
            
            # Convertir y guardar
            convert_to_vrp_format(data, output_path)
            click.echo(f"  Convertido exitosamente: {output_path}")
        
        except Exception as e:
            click.echo(f"  Error al procesar {file_path}: {str(e)}", err=True)
    
    click.echo("Conversión completada.")


@cli.group()
def migrate():
    """Herramientas de migración v1 a v2."""
    pass




@migrate.command()
@click.argument('algorithm')
@click.option('--output', '-o', help='Archivo de salida')
@click.option('--force', is_flag=True, help='Sobrescribir si existe')
@click.option('--list-algos', is_flag=True, help='Listar algoritmos disponibles para migrar')
@click.option('--all', is_flag=True, help='Migrar todos los algoritmos pendientes')
def algorithm(algorithm, output, force, list_algos, all):
    """
    Migra un algoritmo de v1 a v2.
    
    \b
    ALGORITHM: Nombre del algoritmo a migrar
    
    Ejemplo:
    bioalgocompare migrate algorithm my_algorithm --output algorithms/my_algorithm_v2.py
    """
    migrated = ['sho', 'hho', 'foa'] # This list should ideally be dynamic or from a config
    
    # Buscar todos los algoritmos
    algo_dir = Path('algorithms')
    all_algos = []
    
    for file in algo_dir.glob('*.py'):
        if (not file.name.startswith('_') and 
            not file.name.endswith('_v2.py') and
            file.name not in ['base.py', 'base_v2.py', 'factories.py', '__init__.py']):
            algo_name = file.stem
            if algo_name not in migrated:
                all_algos.append(algo_name)
    
    all_algos.sort()
    
    if list_algos:
        click.echo("\n📋 Algoritmos disponibles para migrar:")
        for algo in all_algos:
            click.echo(f"  - {algo}")
        click.echo(f"\n✅ Ya migrados: {', '.join(migrated)}")
        return
    
    if all:
        click.echo(f"\n🚀 Migrando {len(all_algos)} algoritmos...")
        success = 0
        for algo in all_algos:
            migrator = AlgorithmMigrator(algo)
            if migrator.migrate():
                success += 1
            click.echo("")
        
        click.echo(f"\n✨ Migración completa: {success}/{len(all_algos)} exitosos")
        return
    
    if not algorithm:
        click.echo("❌ Debe especificar un algoritmo o usar --list-algos o --all para ver opciones")
        return
    
    if algorithm in migrated:
        click.echo(f"ℹ️  {algorithm} ya está migrado")
        return
    
    migrator = AlgorithmMigrator(algorithm)
    if migrator.migrate():
        click.echo("\n✨ Migración completada. Revisa los TODOs en los archivos generados.")
    else:
        click.echo("\n❌ Error en la migración")


@cli.command()
def info():
    """
    Muestra información sobre el proyecto y algoritmos disponibles.
    
    Ejemplo:
    bioalgocompare info
    """
    click.echo("🧬 BioAlgoCompare v2.0")
    click.echo("=" * 50)
    click.echo("\n📚 Framework para algoritmos bio-inspirados en VRP")
    click.echo("Desarrollado para investigación en metaheurísticas")
    
    click.echo(f"\n🔬 Algoritmos disponibles ({len(ALGORITHMS_V2)}):")
    
    # Información de cada algoritmo
    algo_info = {
        'sho': 'Spotted Hyena Optimizer',
        'apo': 'African Penguin Optimization',
        'egto': 'Enhanced Gorilla Troops Optimizer',
        'fsa': 'Fish School Algorithm',
        'foa': 'Fruit Fly Optimization Algorithm',
        'woa': 'Whale Optimization Algorithm',
        'hho': 'Harris Hawks Optimization',
        'mrfo': 'Manta Ray Foraging Optimization',
        'sma': 'Slime Mould Algorithm',
        'gto': 'Gorilla Troops Optimizer',
        'ewa': 'Earthworm Algorithm',
        'aha': 'Artificial Hummingbird Algorithm',
        'rro': 'Raven Roosting Optimization',
        'gvoa': 'Growth Variation Optimization Algorithm',
        'smo': 'Starling Murmuration Optimizer',
        'opa': 'Orca Predation Algorithm',
        'hoa': 'Hyena Optimization Algorithm',
        'fgo': 'Flamingo Optimization Algorithm'
    }
    
    for algo in ALGORITHMS_V2:
        desc = algo_info.get(algo, 'Sin descripción')
        click.echo(f"  • {algo.upper():<6} - {desc}")
    
    click.echo("\n📊 Características:")
    click.echo("  • Todos los algoritmos migrados a arquitectura v2")
    click.echo("  • Soporte para ejecución paralela")
    click.echo("  • Sistema de checkpoints para ejecuciones largas")
    click.echo("  • Análisis estadístico integrado")
    click.echo("  • Visualización de resultados")
    
    click.echo("\n💡 Para más ayuda:")
    click.echo("  bioalgocompare --help")
    click.echo("  bioalgocompare COMANDO --help")








@cli.command()
@click.option('--detailed', is_flag=True, help='Inventario detallado')
def inventory(detailed):
    """
    Genera inventario del repositorio.
    
    Ejemplos:
    
    \b
    # Inventario básico
    bioalgocompare inventory
    
    \b
    # Inventario detallado
    bioalgocompare inventory --detailed
    """
    repo_root = os.path.dirname(os.path.abspath(__file__))
    click.echo(f"📋 Generando inventario del repositorio en: {repo_root}")

    files_info, imports_map, module_list = scan_repository(repo_root)
    data_usages = detect_data_usage(files_info)

    # Generar reporte en Markdown
    report = generate_inventory_report(
        files_info, imports_map, module_list, data_usages
    )

    # Guardar reporte
    report_path = os.path.join(repo_root, "docs", "technical", "inventory_report.md")
    Path(report_path).parent.mkdir(parents=True, exist_ok=True)
    with open(report_path, "w", encoding="utf-8") as f:
        f.write(report)

    click.echo(f"Reporte de inventario generado en: {report_path}")
    click.echo("\n✅ Inventario completado")


@cli.command()
@click.option('--port', '-p', default=8050, help='Puerto para el servidor')
@click.option('--debug/--no-debug', default=False, help='Modo debug')
def dashboard(port, debug):
    """
    Lanza el dashboard de visualización.
    
    Ejemplo:
    bioalgocompare dashboard --port 8080
    """
    click.echo(f"🎯 Lanzando dashboard en puerto {port}...")
    click.echo("⚠️  Esta función está en desarrollo")
    
    # TODO: Implementar dashboard
    if debug:
        click.echo("  (Modo debug activado)")


if __name__ == '__main__':
    cli()