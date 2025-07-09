#!/usr/bin/env python3
"""
Analyze command for BioAlgoCompare.

Provides statistical analysis of benchmark results.
"""

import click
from pathlib import Path
import json
import pandas as pd
from typing import List, Dict, Any


@click.command()
@click.option('--input', '-i', required=True, type=click.Path(exists=True),
              help='Input results file (JSON, CSV, or directory)')
@click.option('--output', '-o', type=click.Path(),
              help='Output directory for analysis')
@click.option('--format', 'output_format', type=click.Choice(['html', 'pdf', 'json']),
              default='html', help='Output format')
@click.option('--tests', multiple=True, type=click.Choice(['friedman', 'kruskal', 'mannwhitney', 'wilcoxon']),
              default=['friedman'], help='Statistical tests to perform')
@click.option('--alpha', default=0.05, type=float,
              help='Significance level (default: 0.05)')
@click.option('--effect-size/--no-effect-size', default=True,
              help='Calculate effect sizes')
@click.option('--plot/--no-plot', default=True,
              help='Generate plots')
@click.option('--verbose', '-v', is_flag=True,
              help='Verbose output')
def analyze(input, output, output_format, tests, alpha, effect_size, plot, verbose):
    """Analyze benchmark results with statistical tests."""
    import sys
    
    input_path = Path(input)
    output_dir = Path(output) if output else input_path.parent / 'analysis'
    output_dir.mkdir(exist_ok=True)
    
    if verbose:
        click.echo(f"📊 Analyzing results from {input_path}")
        click.echo(f"📂 Output directory: {output_dir}")
        click.echo(f"🧪 Tests: {', '.join(tests)}")
        click.echo(f"📈 Alpha level: {alpha}")
    
    try:
        # Import analysis modules
        from utils.statistical_analysis import StatisticalAnalyzer
        from utils.result_schema_v2 import StandardResultV2
        
        # Load results
        results = _load_results(input_path, verbose)
        
        if not results:
            click.echo("❌ No results found to analyze")
            return
        
        # Create analyzer
        analyzer = StatisticalAnalyzer(alpha=alpha)
        
        # Convert results to analysis format
        analysis_data = _prepare_analysis_data(results, verbose)
        
        # Perform statistical tests
        test_results = {}
        for test_name in tests:
            if verbose:
                click.echo(f"🧮 Running {test_name} test...")
            
            if test_name == 'friedman':
                test_results['friedman'] = analyzer.friedman_test(analysis_data)
            elif test_name == 'kruskal':
                test_results['kruskal'] = analyzer.kruskal_wallis_test(analysis_data)
            elif test_name == 'mannwhitney':
                test_results['mannwhitney'] = analyzer.mann_whitney_tests(analysis_data)
            elif test_name == 'wilcoxon':
                test_results['wilcoxon'] = analyzer.wilcoxon_tests(analysis_data)
        
        # Calculate effect sizes if requested
        if effect_size:
            if verbose:
                click.echo("📏 Calculating effect sizes...")
            test_results['effect_sizes'] = analyzer.calculate_effect_sizes(analysis_data)
        
        # Generate output
        if output_format == 'html':
            _generate_html_report(test_results, analysis_data, output_dir, plot)
        elif output_format == 'json':
            _generate_json_report(test_results, analysis_data, output_dir)
        elif output_format == 'pdf':
            _generate_pdf_report(test_results, analysis_data, output_dir, plot)
        
        if verbose:
            click.echo(f"✅ Analysis complete! Results saved to {output_dir}")
        
    except ImportError as e:
        click.echo(f"❌ Missing dependencies: {e}")
        click.echo("Please install required packages: pip install scipy matplotlib seaborn")
    except Exception as e:
        click.echo(f"❌ Error during analysis: {e}")
        if verbose:
            import traceback
            traceback.print_exc()
        sys.exit(1)


def _load_results(input_path: Path, verbose: bool = False) -> List[Dict[str, Any]]:
    """Load results from various formats."""
    results = []
    
    if input_path.is_file():
        if input_path.suffix == '.json':
            with open(input_path) as f:
                data = json.load(f)
                if isinstance(data, list):
                    results.extend(data)
                else:
                    results.append(data)
        elif input_path.suffix == '.csv':
            df = pd.read_csv(input_path)
            results = df.to_dict('records')
    elif input_path.is_dir():
        # Load all JSON files in directory
        for json_file in input_path.glob('*.json'):
            try:
                with open(json_file) as f:
                    data = json.load(f)
                    if isinstance(data, list):
                        results.extend(data)
                    else:
                        results.append(data)
            except Exception as e:
                if verbose:
                    click.echo(f"⚠️  Warning: Could not load {json_file}: {e}")
    
    if verbose:
        click.echo(f"📊 Loaded {len(results)} results")
    
    return results


def _prepare_analysis_data(results: List[Dict[str, Any]], verbose: bool = False) -> Dict[str, Any]:
    """Prepare data for statistical analysis."""
    # Group results by algorithm and instance
    algorithm_data = {}
    
    for result in results:
        algo_name = result.get('algorithm_name', 'unknown')
        instance_name = result.get('instance_name', 'unknown')
        
        if algo_name not in algorithm_data:
            algorithm_data[algo_name] = {}
        
        if instance_name not in algorithm_data[algo_name]:
            algorithm_data[algo_name][instance_name] = []
        
        # Extract fitness values
        if 'runs' in result:
            for run in result['runs']:
                algorithm_data[algo_name][instance_name].append(run.get('fitness', float('inf')))
        elif 'fitness' in result:
            algorithm_data[algo_name][instance_name].append(result['fitness'])
    
    if verbose:
        click.echo(f"📈 Prepared data for {len(algorithm_data)} algorithms")
    
    return algorithm_data


def _generate_html_report(test_results: Dict, analysis_data: Dict, output_dir: Path, plot: bool):
    """Generate HTML analysis report."""
    html_content = _create_html_template(test_results, analysis_data, plot)
    
    report_file = output_dir / 'analysis_report.html'
    with open(report_file, 'w') as f:
        f.write(html_content)
    
    click.echo(f"📄 HTML report saved to {report_file}")


def _generate_json_report(test_results: Dict, analysis_data: Dict, output_dir: Path):
    """Generate JSON analysis report."""
    report_data = {
        'test_results': test_results,
        'summary': {
            'n_algorithms': len(analysis_data),
            'n_instances': len(set(instance for algo_data in analysis_data.values() for instance in algo_data.keys()))
        }
    }
    
    report_file = output_dir / 'analysis_report.json'
    with open(report_file, 'w') as f:
        json.dump(report_data, f, indent=2, default=str)
    
    click.echo(f"📄 JSON report saved to {report_file}")


def _generate_pdf_report(test_results: Dict, analysis_data: Dict, output_dir: Path, plot: bool):
    """Generate PDF analysis report."""
    click.echo("📄 PDF generation not yet implemented")
    click.echo("Using HTML format as fallback...")
    _generate_html_report(test_results, analysis_data, output_dir, plot)


def _create_html_template(test_results: Dict, analysis_data: Dict, plot: bool) -> str:
    """Create HTML template for analysis report."""
    html = f"""<!DOCTYPE html>
<html>
<head>
    <title>BioAlgoCompare Analysis Report</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; }}
        .header {{ background-color: #f0f0f0; padding: 20px; border-radius: 5px; }}
        .section {{ margin: 20px 0; padding: 15px; border: 1px solid #ddd; border-radius: 5px; }}
        .test-result {{ margin: 10px 0; padding: 10px; background-color: #f9f9f9; }}
        table {{ border-collapse: collapse; width: 100%; }}
        th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
        th {{ background-color: #f2f2f2; }}
    </style>
</head>
<body>
    <div class="header">
        <h1>BioAlgoCompare Statistical Analysis Report</h1>
        <p>Generated on: {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
    </div>
    
    <div class="section">
        <h2>Summary</h2>
        <p>Number of algorithms: {len(analysis_data)}</p>
        <p>Algorithms: {', '.join(analysis_data.keys())}</p>
    </div>
    
    <div class="section">
        <h2>Statistical Test Results</h2>
        {_format_test_results(test_results)}
    </div>
</body>
</html>"""
    
    return html


def _format_test_results(test_results: Dict) -> str:
    """Format test results for HTML display."""
    html = ""
    
    for test_name, results in test_results.items():
        html += f"<div class='test-result'>"
        html += f"<h3>{test_name.title()} Test</h3>"
        html += f"<p>Results: {results}</p>"
        html += f"</div>"
    
    return html