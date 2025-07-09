#!/usr/bin/env python3
"""
Publication export command for BioAlgoCompare.

Generates publication-ready materials from benchmark results including
LaTeX tables, figures, and statistical analysis for scientific papers.
"""

import click
from pathlib import Path
import sys


@click.command()
@click.option('--input', '-i', required=True, type=click.Path(exists=True),
              help='Input directory with benchmark results')
@click.option('--output', '-o', type=click.Path(),
              help='Output directory for publication materials (default: input/publication)')
@click.option('--format', 'output_format', 
              type=click.Choice(['latex', 'ieee', 'acm', 'springer', 'all']),
              default='latex', help='Publication format (default: latex)')
@click.option('--conference', default='CISTI 2025',
              help='Target conference/journal (default: CISTI 2025)')
@click.option('--include', multiple=True,
              type=click.Choice(['tables', 'figures', 'data', 'summary', 'all']),
              default=['all'], help='Components to include (default: all)')
@click.option('--statistical-tests/--no-statistical-tests', default=True,
              help='Include statistical significance tests')
@click.option('--convergence-plots/--no-convergence-plots', default=True,
              help='Generate convergence plots')
@click.option('--distribution-analysis/--no-distribution-analysis', default=True,
              help='Include distribution analysis')
@click.option('--replication-data/--no-replication-data', default=True,
              help='Export replication data')
@click.option('--compress/--no-compress', default=False,
              help='Create compressed archive of all materials')
@click.option('--verbose', '-v', is_flag=True,
              help='Verbose output')
def publish(input, output, output_format, conference, include, statistical_tests,
           convergence_plots, distribution_analysis, replication_data, 
           compress, verbose):
    """Export publication-ready materials from benchmark results.
    
    This command generates LaTeX tables, statistical analysis, figures, and 
    replication data suitable for scientific publication in conferences and journals.
    
    Examples:
    
        # Export all materials for CISTI 2025
        bioalgo publish -i results/benchmark_results/ --conference "CISTI 2025"
        
        # Export only tables and figures
        bioalgo publish -i results/ --include tables --include figures
        
        # IEEE format with compression
        bioalgo publish -i results/ --format ieee --compress
        
        # Custom output directory
        bioalgo publish -i results/ -o publication_materials/
    """
    
    input_path = Path(input)
    output_path = Path(output) if output else input_path / "publication"
    
    if verbose:
        click.echo(f"📊 Publication Export for {conference}")
        click.echo(f"📂 Input: {input_path}")
        click.echo(f"📂 Output: {output_path}")
        click.echo(f"📄 Format: {output_format}")
        click.echo(f"📦 Components: {', '.join(include)}")
    
    try:
        # Import publication exporter
        from utils.publication_export import PublicationExporter
        
        # Create exporter with configuration
        exporter = PublicationExporter(input_path, output_path)
        
        # Configure what to export based on options
        export_config = {
            'statistical_tests': statistical_tests,
            'convergence_plots': convergence_plots,
            'distribution_analysis': distribution_analysis,
            'replication_data': replication_data
        }
        
        generated_files = {}
        
        # Export based on selected components
        if 'all' in include or 'tables' in include:
            if verbose:
                click.echo("📊 Generating statistical tables...")
            table_files = exporter.export_statistical_tables()
            generated_files.update(table_files)
        
        if 'all' in include or 'figures' in include:
            if convergence_plots:
                if verbose:
                    click.echo("📈 Creating convergence figures...")
                convergence_files = exporter.export_convergence_figures()
                generated_files.update(convergence_files)
            
            if distribution_analysis:
                if verbose:
                    click.echo("📉 Creating distribution analysis...")
                distribution_files = exporter.export_distribution_analysis()
                generated_files.update(distribution_files)
            
            # Rankings
            if verbose:
                click.echo("🏆 Creating rankings...")
            ranking_files = exporter.export_rankings()
            generated_files.update(ranking_files)
        
        if 'all' in include or 'data' in include:
            if replication_data:
                if verbose:
                    click.echo("🔬 Exporting replication data...")
                replication_files = exporter.export_replication_data()
                generated_files.update(replication_files)
        
        if 'all' in include or 'summary' in include:
            if verbose:
                click.echo("📋 Creating executive summary...")
            summary_files = exporter.export_executive_summary()
            generated_files.update(summary_files)
        
        # Create format-specific adaptations
        if output_format != 'latex':
            if verbose:
                click.echo(f"🔧 Adapting for {output_format} format...")
            _adapt_format(generated_files, output_format, output_path, verbose)
        
        # Create conference-specific package
        if verbose:
            click.echo(f"📦 Creating {conference} package...")
        _create_conference_package(generated_files, conference, output_path, verbose)
        
        # Compress if requested
        if compress:
            if verbose:
                click.echo("🗜️ Creating compressed archive...")
            archive_path = _create_archive(output_path, verbose)
            generated_files['archive'] = archive_path
        
        # Summary report
        click.echo(f"\n✅ Publication materials exported successfully!")
        click.echo(f"📂 Output directory: {output_path}")
        
        if verbose:
            click.echo(f"\n📋 Generated files:")
            for category, file_path in generated_files.items():
                click.echo(f"  📄 {category}: {file_path.name}")
        
        click.echo(f"\n📄 Total files: {len(generated_files)}")
        
        # Next steps guidance
        click.echo(f"\n📋 Next steps for {conference}:")
        click.echo("  1. Review generated LaTeX tables")
        click.echo("  2. Include figures in your manuscript")
        click.echo("  3. Cite statistical significance results")
        click.echo("  4. Include replication data as supplementary material")
        
    except ImportError as e:
        click.echo(f"❌ Missing dependencies for publication export: {e}")
        click.echo("Install required packages: pip install matplotlib seaborn scipy")
        sys.exit(1)
    except Exception as e:
        click.echo(f"❌ Error during publication export: {e}")
        if verbose:
            import traceback
            traceback.print_exc()
        sys.exit(1)


def _adapt_format(files: dict, format_type: str, output_dir: Path, verbose: bool):
    """Adapt files for specific publication formats."""
    
    if format_type == 'ieee':
        # IEEE specific adaptations
        if verbose:
            click.echo("  📝 Applying IEEE formatting standards...")
        _apply_ieee_format(files, output_dir)
    
    elif format_type == 'acm':
        # ACM specific adaptations
        if verbose:
            click.echo("  📝 Applying ACM formatting standards...")
        _apply_acm_format(files, output_dir)
    
    elif format_type == 'springer':
        # Springer specific adaptations
        if verbose:
            click.echo("  📝 Applying Springer formatting standards...")
        _apply_springer_format(files, output_dir)


def _apply_ieee_format(files: dict, output_dir: Path):
    """Apply IEEE formatting standards."""
    
    # IEEE typically uses specific table formatting
    ieee_dir = output_dir / "ieee_format"
    ieee_dir.mkdir(exist_ok=True)
    
    # Copy and modify LaTeX files for IEEE style
    for category, file_path in files.items():
        if file_path.suffix == '.tex' and 'table' in category:
            ieee_file = ieee_dir / f"ieee_{file_path.name}"
            
            # Read original content
            content = file_path.read_text()
            
            # IEEE modifications
            content = content.replace('\\toprule', '\\hline')
            content = content.replace('\\midrule', '\\hline')
            content = content.replace('\\bottomrule', '\\hline')
            content = content.replace('[htbp]', '[t]')  # IEEE prefers top placement
            
            # Write IEEE version
            ieee_file.write_text(content)


def _apply_acm_format(files: dict, output_dir: Path):
    """Apply ACM formatting standards."""
    
    acm_dir = output_dir / "acm_format"
    acm_dir.mkdir(exist_ok=True)
    
    # ACM specific table formatting
    for category, file_path in files.items():
        if file_path.suffix == '.tex' and 'table' in category:
            acm_file = acm_dir / f"acm_{file_path.name}"
            
            content = file_path.read_text()
            
            # ACM modifications
            content = content.replace('\\centering', '\\centering\\small')
            content = content.replace('[htbp]', '[tb]')
            
            acm_file.write_text(content)


def _apply_springer_format(files: dict, output_dir: Path):
    """Apply Springer formatting standards."""
    
    springer_dir = output_dir / "springer_format"
    springer_dir.mkdir(exist_ok=True)
    
    # Springer LNCS formatting
    for category, file_path in files.items():
        if file_path.suffix == '.tex' and 'table' in category:
            springer_file = springer_dir / f"springer_{file_path.name}"
            
            content = file_path.read_text()
            
            # Springer modifications
            content = content.replace('\\begin{table}[htbp]', '\\begin{table}')
            content = content.replace('\\centering', '\\centering\\footnotesize')
            
            springer_file.write_text(content)


def _create_conference_package(files: dict, conference: str, output_dir: Path, verbose: bool):
    """Create conference-specific package."""
    
    package_dir = output_dir / f"{conference.lower().replace(' ', '_')}_package"
    package_dir.mkdir(exist_ok=True)
    
    # Create submission checklist
    checklist_content = f"""# {conference} Submission Checklist

## Generated Materials

✅ Statistical tables (LaTeX format)
✅ Convergence plots (PDF format) 
✅ Distribution analysis figures
✅ Replication data (CSV format)
✅ Executive summary

## Submission Requirements

### Tables
- Include descriptive statistics table in Results section
- Reference statistical significance tests in Discussion
- Use optimal comparison table if applicable

### Figures  
- Include convergence plots as Figure 1 or 2
- Add distribution analysis to support claims
- Ensure all figures are PDF format for print quality

### Reproducibility
- Include replication_data.csv as supplementary material
- Reference experiment_metadata.json for complete setup
- Mention BioAlgoCompare v2.0 platform in methodology

### Statistical Rigor
- Report all statistical test results
- Include effect size calculations
- Use appropriate non-parametric tests for algorithm comparison

## File Manifest

"""
    
    for category, file_path in files.items():
        checklist_content += f"- {category}: {file_path.name}\n"
    
    checklist_file = package_dir / "submission_checklist.md"
    checklist_file.write_text(checklist_content)
    
    if verbose:
        click.echo(f"  📋 Created submission checklist: {checklist_file}")


def _create_archive(output_dir: Path, verbose: bool) -> Path:
    """Create compressed archive of all materials."""
    
    import shutil
    from datetime import datetime
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    archive_name = f"publication_materials_{timestamp}"
    
    # Create archive
    archive_path = output_dir.parent / archive_name
    shutil.make_archive(str(archive_path), 'zip', str(output_dir))
    
    final_archive = Path(f"{archive_path}.zip")
    
    if verbose:
        click.echo(f"  📦 Archive created: {final_archive}")
        click.echo(f"  💾 Size: {final_archive.stat().st_size / 1024:.1f} KB")
    
    return final_archive