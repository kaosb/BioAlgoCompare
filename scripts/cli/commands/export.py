"""
Comando export para exportación científica de resultados.
"""

import click
from pathlib import Path
import sys
from typing import Optional, List

from utils.scientific_export import ScientificExportPipeline, export_scientific_results
from utils.results_database import ResultsDatabase


@click.command()
@click.argument('source', type=click.Path(exists=True))
@click.option('--output', '-o', type=click.Path(), 
              help='Output directory for exports')
@click.option('--format', '-f', 'formats', multiple=True,
              type=click.Choice(['csv', 'json', 'latex', 'excel', 'all']),
              default=['all'],
              help='Export formats (can specify multiple)')
@click.option('--conference', '-c', 
              type=click.Choice(['cisti2025', 'gecco2025', 'default']),
              help='Use conference-specific presets')
@click.option('--include-plots/--no-plots', default=True,
              help='Include visualization plots')
@click.option('--archive/--no-archive', default=True,
              help='Create ZIP archive of all exports')
@click.option('--from-db', is_flag=True,
              help='Source is a database file')
@click.option('--filter-algorithm', '-a', multiple=True,
              help='Filter by algorithm names')
@click.option('--filter-instance', '-i', multiple=True,
              help='Filter by instance names')
@click.option('--min-runs', type=int, default=1,
              help='Minimum runs per algorithm/instance combination')
def export(source: str,
          output: Optional[str],
          formats: List[str],
          conference: Optional[str],
          include_plots: bool,
          archive: bool,
          from_db: bool,
          filter_algorithm: List[str],
          filter_instance: List[str],
          min_runs: int):
    """
    Export results for scientific publication.
    
    Export benchmark results in multiple formats suitable for academic
    publications, including LaTeX tables, CSV data, and visualizations.
    
    Examples:
    
        # Export from directory with all formats
        bioalgo export results/
        
        # Export specific formats
        bioalgo export results/ -f csv -f latex
        
        # Export for CISTI 2025 conference
        bioalgo export results/ --conference cisti2025
        
        # Export from database with filters
        bioalgo export results.db --from-db -a HOA -a FOA -i E-n22-k4
        
        # Export without plots and archive
        bioalgo export results/ --no-plots --no-archive
    """
    try:
        # Preparar source
        if from_db:
            results_source = ResultsDatabase(source)
        else:
            results_source = Path(source)
        
        # Si se especifica 'all', usar todos los formatos
        if 'all' in formats:
            formats_list = ['csv', 'json', 'latex', 'excel']
        else:
            formats_list = list(formats)
        
        # Crear pipeline
        click.echo(f"📊 Initializing export pipeline...")
        pipeline = ScientificExportPipeline(
            results_source=results_source,
            output_dir=Path(output) if output else None
        )
        
        # Aplicar filtros si se especifican
        if filter_algorithm or filter_instance or min_runs > 1:
            click.echo("🔍 Applying filters...")
            data = pipeline.load_results()
            
            if filter_algorithm:
                data = data[data['algorithm'].isin(filter_algorithm)]
                click.echo(f"  - Filtered algorithms: {', '.join(filter_algorithm)}")
            
            if filter_instance:
                data = data[data['instance'].isin(filter_instance)]
                click.echo(f"  - Filtered instances: {', '.join(filter_instance)}")
            
            if min_runs > 1:
                # Filtrar combinaciones con suficientes runs
                counts = data.groupby(['algorithm', 'instance']).size()
                valid_combos = counts[counts >= min_runs].index
                
                data = data[
                    data.apply(lambda x: (x['algorithm'], x['instance']) in valid_combos, axis=1)
                ]
                click.echo(f"  - Min runs filter: {min_runs}")
            
            # Actualizar cache del pipeline
            pipeline._data_cache = data
            
            if len(data) == 0:
                click.echo("❌ No data remaining after filters!", err=True)
                sys.exit(1)
            
            click.echo(f"  - Remaining records: {len(data)}")
        
        # Ejecutar exportación
        if conference:
            click.echo(f"🎯 Exporting for conference: {conference}")
            files = pipeline.export_for_conference(
                conference=conference,
                include_supplementary=True
            )
        else:
            click.echo(f"📁 Exporting formats: {', '.join(formats_list)}")
            files = pipeline.export(
                formats=formats_list if formats_list else None,
                include_plots=include_plots,
                create_archive=archive
            )
        
        # Mostrar resultados
        click.echo("\n✅ Export completed successfully!")
        click.echo("\n📄 Generated files:")
        
        for file_type, file_path in sorted(files.items()):
            if isinstance(file_path, Path):
                if file_path.exists():
                    size = file_path.stat().st_size if file_path.is_file() else 0
                    size_str = f" ({size/1024:.1f} KB)" if size > 0 else ""
                    click.echo(f"  - {file_type}: {file_path}{size_str}")
        
        # Mostrar estadísticas
        metadata = pipeline.generate_metadata()
        exp_info = metadata.get('experiment_info', {})
        
        click.echo("\n📊 Export summary:")
        click.echo(f"  - Total runs: {exp_info.get('total_runs', 0)}")
        click.echo(f"  - Algorithms: {len(exp_info.get('unique_algorithms', []))}")
        click.echo(f"  - Instances: {len(exp_info.get('unique_instances', []))}")
        
        # Si hay archivo ZIP, destacarlo
        if 'archive' in files:
            click.echo(f"\n📦 Complete archive: {files['archive']}")
        
    except FileNotFoundError:
        click.echo(f"❌ Source not found: {source}", err=True)
        sys.exit(1)
    except PermissionError:
        click.echo(f"❌ Permission denied accessing: {source}", err=True)
        sys.exit(1)
    except Exception as e:
        click.echo(f"❌ Export failed: {str(e)}", err=True)
        if click.get_current_context().obj.get('debug'):
            import traceback
            traceback.print_exc()
        sys.exit(1)


@click.command()
@click.option('--list-formats', is_flag=True,
              help='List available export formats')
@click.option('--list-conferences', is_flag=True,
              help='List available conference presets')
def export_info(list_formats: bool, list_conferences: bool):
    """
    Show information about export capabilities.
    
    Display available export formats and conference presets.
    """
    if list_formats:
        click.echo("📄 Available export formats:")
        click.echo("  - csv:   Comma-separated values with metadata")
        click.echo("  - json:  Hierarchical JSON structure")
        click.echo("  - latex: Publication-ready LaTeX tables")
        click.echo("  - excel: Multi-sheet Excel workbook")
        click.echo("  - all:   Export in all formats")
    
    if list_conferences:
        click.echo("\n🎓 Available conference presets:")
        click.echo("  - cisti2025: IEEE format, includes supplementary materials")
        click.echo("  - gecco2025: ACM format, focused on core results")
        click.echo("  - default:   Standard format for general use")
    
    if not list_formats and not list_conferences:
        click.echo("Use --list-formats or --list-conferences to see available options")


# Grupo de comandos de exportación
@click.group()
def export_group():
    """Scientific export commands."""
    pass


export_group.add_command(export, name='export')
export_group.add_command(export_info, name='info')