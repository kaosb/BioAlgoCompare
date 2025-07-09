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
from pathlib import Path

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
    from scripts.core.run import main as run_main
    
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
@click.option('--instances', '-i', required=True,
              help='Instancias VRP (separadas por coma)')
@click.option('--population', '-p', default=30, help='Tamaño de población')
@click.option('--iterations', '-n', default=100, help='Número de iteraciones')
@click.option('--runs', '-r', default=30, help='Número de ejecuciones por algoritmo')
@click.option('--parallel/--no-parallel', default=True, help='Ejecución paralela')
@click.option('--output-dir', '-o', default='results', help='Directorio de salida')
def benchmark(algorithms, instances, population, iterations, runs, parallel, output_dir):
    """
    Ejecuta un benchmark completo con múltiples algoritmos e instancias.
    
    Ejemplos:
    
    \b
    # Benchmark básico
    bioalgocompare benchmark -a woa,sma,gto -i P-n16-k8,P-n19-k2
    
    \b
    # Benchmark con parámetros personalizados
    bioalgocompare benchmark -a woa,sma,gto,mrfo -i P-n16-k8,P-n19-k2,P-n20-k2 \\
        -p 50 -n 200 -r 50
    """
    from scripts.benchmark import BenchmarkRunner
    
    # Parsear algoritmos e instancias
    algo_list = [a.strip() for a in algorithms.split(',')]
    instance_list = [i.strip() for i in instances.split(',')]
    
    # Crear runner
    runner = BenchmarkRunner(result_base_dir=output_dir)
    
    click.echo(f"🚀 Iniciando benchmark")
    click.echo(f"📊 Algoritmos: {', '.join(algo_list)}")
    click.echo(f"📁 Instancias: {', '.join(instance_list)}")
    click.echo(f"🔢 Configuración: {population} individuos, {iterations} iteraciones, {runs} runs")
    
    # Ejecutar benchmark
    try:
        result_dir = runner.run_benchmark(
            algorithms=algo_list,
            instances=instance_list,
            runs=runs,
            iterations=iterations,
            population=population,
            parallel=parallel
        )
        
        click.echo(f"\n✅ Benchmark completado")
        click.echo(f"📁 Resultados guardados en: {result_dir}")
        
    except Exception as e:
        click.echo(f"❌ Error durante el benchmark: {str(e)}", err=True)
        sys.exit(1)


@cli.command()
@click.argument('results_file', type=click.Path(exists=True))
@click.option('--format', type=click.Choice(['summary', 'detailed', 'statistical']), 
              default='summary', help='Formato de análisis')
@click.option('--compare/--no-compare', default=False, 
              help='Comparar múltiples algoritmos')
@click.option('--plot/--no-plot', default=True, help='Generar gráficos')
@click.option('--output', '-o', help='Archivo de salida para el reporte')
def analyze(results_file, format, compare, plot, output):
    """
    Analiza resultados de experimentos.
    
    \b
    RESULTS_FILE: Archivo JSON con resultados de experimento
    
    Ejemplos:
    
    \b
    # Análisis básico
    bioalgocompare analyze results/experiment_20240101.json
    
    \b
    # Análisis detallado con comparación
    bioalgocompare analyze results/benchmark_20240101.json --format detailed --compare
    
    \b
    # Análisis estadístico sin gráficos
    bioalgocompare analyze results/massive_run.json --format statistical --no-plot
    """
    from scripts.core.analyze import main as analyze_main
    import json
    
    click.echo(f"📊 Analizando: {results_file}")
    
    # Cargar datos
    with open(results_file, 'r') as f:
        data = json.load(f)
    
    # Determinar tipo de análisis
    if 'results' in data:
        # Es un archivo de resultados múltiples
        results = data['results']
        stats = data.get('stats', {})
    else:
        # Es un archivo simple
        results = [data]
        stats = {}
    
    click.echo(f"📈 Encontrados {len(results)} resultados")
    
    # Realizar análisis según formato
    if format == 'summary':
        # Mostrar resumen básico
        if stats:
            click.echo("\n📊 Estadísticas Generales:")
            click.echo(f"  Algoritmo: {stats.get('algorithm', 'N/A')}")
            click.echo(f"  Instancia: {stats.get('instance', 'N/A')}")
            click.echo(f"  Mejor fitness: {stats.get('best_fitness', 'N/A'):.4f}")
            click.echo(f"  Media ± Std: {stats.get('mean_fitness', 'N/A'):.4f} ± {stats.get('std_fitness', 'N/A'):.4f}")
            click.echo(f"  Mediana: {stats.get('median_fitness', 'N/A'):.4f}")
        
    elif format == 'detailed':
        # Análisis detallado
        click.echo("\n📊 Análisis Detallado:")
        # TODO: Implementar análisis detallado
        click.echo("  (Función en desarrollo)")
        
    elif format == 'statistical':
        # Análisis estadístico completo
        click.echo("\n📊 Análisis Estadístico:")
        # TODO: Implementar análisis estadístico
        click.echo("  (Función en desarrollo)")
    
    if plot:
        click.echo("\n📈 Generando gráficos...")
        # TODO: Generar gráficos
        click.echo("  (Función en desarrollo)")
    
    if output:
        click.echo(f"\n💾 Guardando reporte en: {output}")
        # TODO: Guardar reporte
    
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
    from scripts.utilities.manage_datasets import check_datasets_availability
    
    click.echo("🔍 Verificando datasets...")
    
    # Directorio de datos
    data_dir = Path("data/vrp")
    
    if not data_dir.exists():
        click.echo(f"❌ No existe el directorio: {data_dir}", err=True)
        return
    
    # Contar archivos VRP
    vrp_files = list(data_dir.glob("**/*.vrp"))
    
    click.echo(f"\n📁 Directorio de datos: {data_dir}")
    click.echo(f"📊 Archivos VRP encontrados: {len(vrp_files)}")
    
    # Listar algunos archivos
    if vrp_files:
        click.echo("\n📋 Primeros 10 archivos:")
        for i, file in enumerate(vrp_files[:10]):
            click.echo(f"  {i+1}. {file.name}")
        
        if len(vrp_files) > 10:
            click.echo(f"  ... y {len(vrp_files) - 10} más")
    
    # Verificar subdirectorios comunes
    subdirs = ['Solomon', 'Augerat', 'Christofides']
    click.echo("\n📂 Subdirectorios:")
    for subdir in subdirs:
        path = data_dir / subdir
        if path.exists():
            count = len(list(path.glob("*.vrp")))
            click.echo(f"  ✅ {subdir}: {count} archivos")
        else:
            click.echo(f"  ❌ {subdir}: no encontrado")


@datasets.command()
@click.option('--source', default='standard', help='Fuente de datasets')
def download():
    """
    Descarga datasets faltantes.
    
    Ejemplo:
    bioalgocompare datasets download
    """
    click.echo("📥 Descarga de datasets")
    click.echo("⚠️  Esta función está en desarrollo")
    # TODO: Implementar descarga de datasets


@cli.group()
def migrate():
    """Herramientas de migración v1 a v2."""
    pass


@migrate.command()
@click.argument('algorithm')
@click.option('--output', '-o', help='Archivo de salida')
@click.option('--force', is_flag=True, help='Sobrescribir si existe')
def algorithm(algorithm, output, force):
    """
    Migra un algoritmo de v1 a v2.
    
    \b
    ALGORITHM: Nombre del algoritmo a migrar
    
    Ejemplo:
    bioalgocompare migrate algorithm my_algorithm --output algorithms/my_algorithm_v2.py
    """
    from scripts.utilities.migrate_algorithm import main as migrate_main
    
    # Si no se especifica output, usar nombre por defecto
    if not output:
        output = f"algorithms/{algorithm}_v2.py"
    
    # Verificar si ya existe
    if Path(output).exists() and not force:
        click.echo(f"❌ El archivo {output} ya existe. Usa --force para sobrescribir.", err=True)
        return
    
    click.echo(f"🔄 Migrando {algorithm} a v2...")
    click.echo(f"📁 Salida: {output}")
    
    # TODO: Ejecutar migración
    click.echo("⚠️  Esta función está en desarrollo")


@cli.command()
def info():
    """
    Muestra información sobre el proyecto y algoritmos disponibles.
    
    Ejemplo:
    bioalgocompare info
    """
    from scripts.algorithms_v2 import ALGORITHMS_V2
    
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
def inventory():
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
    from scripts.utilities.inventory import main as inventory_main
    
    click.echo("📋 Generando inventario del repositorio...")
    
    # TODO: Ejecutar inventario
    click.echo("⚠️  Esta función está en desarrollo")
    
    if detailed:
        click.echo("  (Modo detallado activado)")


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