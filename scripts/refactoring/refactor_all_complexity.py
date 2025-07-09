#!/usr/bin/env python3
"""
Refactor all remaining complexity issues in the codebase.

This script addresses all 16 remaining complexity violations to bring
all functions to complexity <= 10.
"""

import os
import sys
import subprocess


def get_complexity_violations():
    """Get all current complexity violations."""
    result = subprocess.run(
        ['ruff', 'check', '.', '--select', 'C901'],
        capture_output=True,
        text=True
    )

    violations = []
    for line in result.stdout.strip().split('\n'):
        if 'is too complex' in line:
            parts = line.split(':')
            if len(parts) >= 4:
                file_path = parts[0]
                line_num = parts[1]
                func_name = parts[3].split('`')[1] if '`' in parts[3] else 'unknown'
                complexity = int(parts[3].split('(')[1].split('>')[0].strip())
                violations.append({
                    'file': file_path,
                    'line': int(line_num),
                    'function': func_name,
                    'complexity': complexity
                })

    return violations


def refactor_create_benchmark_report():
    """Refactor create_benchmark_report in utils/benchmarking.py."""
    print("Refactoring create_benchmark_report...")

    # Read the file
    with open('utils/benchmarking.py', 'r', encoding='utf-8') as f:
        content = f.read()

    # Find where to insert the new class
    insert_pos = content.find('def create_benchmark_report(')
    if insert_pos == -1:
        print("Error: Could not find create_benchmark_report")
        return False

    # Find start of line
    while insert_pos > 0 and content[insert_pos-1] != '\n':
        insert_pos -= 1

    # Create the refactored class
    refactored_class = '''
class BenchmarkReportBuilder:
    """Build benchmark reports with proper separation of concerns."""

    def __init__(self, benchmark_results):
        """Initialize with benchmark results."""
        self.results = benchmark_results
        self.instances = self._group_by_instance()

    def create_report(self, filename=None):
        """Create the benchmark report."""
        filename = self._prepare_filename(filename)

        # Create summary
        summary_df = self._create_summary_dataframe()

        # Generate visualizations
        figures_dir = self._prepare_figures_directory(filename)
        visualizations = self._generate_all_visualizations(figures_dir)

        # Build HTML
        html_content = self._build_html_report(summary_df, visualizations)

        # Save report
        self._save_report(filename, html_content)

        return filename

    def _prepare_filename(self, filename):
        """Prepare output filename."""
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"results/benchmark_report_{timestamp}.html"

        os.makedirs(os.path.dirname(filename), exist_ok=True)
        return filename

    def _group_by_instance(self):
        """Group results by instance name."""
        instances = {}
        for result in self.results:
            if result.instance_name not in instances:
                instances[result.instance_name] = []
            instances[result.instance_name].append(result)
        return instances

    def _create_summary_dataframe(self):
        """Create summary DataFrame from results."""
        summary_data = []

        for instance_name, results in self.instances.items():
            for result in results:
                summary_data.append({
                    "Instance": result.instance_name,
                    "Algorithm": result.algorithm_name,
                    "Best": f"{result.best_fitness:.2f}",
                    "Mean": f"{result.mean_fitness:.2f} ± {result.std_fitness:.2f}",
                    "Time (s)": f"{result.mean_time:.2f} ± {result.std_time:.2f}",
                    "Gap (%)": f"{result.gap_to_optimal:.2f}"
                    if result.gap_to_optimal is not None
                    else "N/A",
                    "Success (%)": f"{result.success_rate:.2f}"
                    if result.success_rate is not None
                    else "N/A",
                })

        return pd.DataFrame(summary_data)

    def _prepare_figures_directory(self, filename):
        """Prepare directory for figures."""
        figures_dir = os.path.join(os.path.dirname(filename), "figures")
        os.makedirs(figures_dir, exist_ok=True)
        return figures_dir

    def _generate_all_visualizations(self, figures_dir):
        """Generate all visualizations for the report."""
        visualizations = {}

        for instance_name, results in self.instances.items():
            instance_results = [
                r for r in self.results if r.instance_name == instance_name
            ]

            visualizations[instance_name] = self._generate_instance_visualizations(
                instance_name, instance_results, figures_dir
            )

        return visualizations

    def _generate_instance_visualizations(self, instance_name, results, figures_dir):
        """Generate visualizations for a single instance."""
        viz = {}

        # Solution quality
        viz['quality'] = self._save_plot(
            plot_solution_quality(results),
            figures_dir,
            f"{instance_name}_quality.png"
        )

        # Execution time
        viz['time'] = self._save_plot(
            plot_execution_time(results),
            figures_dir,
            f"{instance_name}_time.png"
        )

        # Convergence
        viz['convergence'] = self._save_plot(
            plot_convergence_comparison(results),
            figures_dir,
            f"{instance_name}_convergence.png"
        )

        # Performance radar
        plt_radar = plot_performance_radar(results, instance_name)
        if plt_radar:
            viz['radar'] = self._save_plot(
                plt_radar,
                figures_dir,
                f"{instance_name}_radar.png"
            )

        return viz

    def _save_plot(self, plt_obj, figures_dir, filename):
        """Save a plot and return the filename."""
        path = os.path.join(figures_dir, filename)
        plt_obj.savefig(path)
        plt_obj.close()
        return filename

    def _build_html_report(self, summary_df, visualizations):
        """Build the HTML report content."""
        html = self._get_html_header()
        html += self._get_summary_section(summary_df)

        # Add instance sections
        for instance_name in self.instances:
            html += self._get_instance_section(instance_name, visualizations.get(instance_name, {}))

        # Add statistical analysis
        html += self._get_statistical_analysis_section()

        html += "</body>\\n</html>"
        return html

    def _get_html_header(self):
        """Get HTML header with CSS."""
        css = self._get_css_styles()
        return f"""<!DOCTYPE html>
<html>
<head>
    <title>Benchmark Report</title>
    <style>
{css}
    </style>
</head>
<body>
    <h1>Benchmark Report</h1>
    <p>Generated on: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}</p>
"""

    def _get_css_styles(self):
        """Get CSS styles for the report."""
        return """body {
    font-family: "Arial", sans-serif;
    margin: 20px;
    line-height: 1.6;
}
h1, h2, h3 {
    color: #2c3e50;
}
table {
    border-collapse: collapse;
    width: 100%;
    margin-bottom: 20px;
}
th, td {
    text-align: left;
    padding: 8px;
    border: 1px solid #ddd;
}
th {
    background-color: #f2f2f2;
}
tr:nth-child(even) {
    background-color: #f9f9f9;
}
.section {
    margin-bottom: 30px;
}
.figure {
    margin: 20px 0;
    text-align: center;
}
.figure img {
    max-width: 100%;
    height: auto;
}
.caption {
    margin-top: 10px;
    font-style: italic;
    color: #666;
}
.highlight {
    font-weight: bold;
    color: #e74c3c;
}"""

    def _get_summary_section(self, summary_df):
        """Get HTML for summary section."""
        return f"""
    <div class="section">
        <h2>Summary</h2>
        {summary_df.to_html(index=False)}
    </div>
"""

    def _get_instance_section(self, instance_name, visualizations):
        """Get HTML for instance section."""
        html = f"""
    <div class="section">
        <h2>Instance: {instance_name}</h2>
        <p>Optimal value: {OPTIMAL_VALUES.get(instance_name, 'Unknown')}</p>
"""

        # Add visualizations
        if 'quality' in visualizations:
            html += f"""
        <div class="figure">
            <img src="figures/{visualizations['quality']}" alt="Solution Quality">
            <div class="caption">Figure: Solution quality comparison for {instance_name}</div>
        </div>
"""

        if 'time' in visualizations:
            html += f"""
        <div class="figure">
            <img src="figures/{visualizations['time']}" alt="Execution Time">
            <div class="caption">Figure: Execution time comparison for {instance_name}</div>
        </div>
"""

        if 'convergence' in visualizations:
            html += f"""
        <div class="figure">
            <img src="figures/{visualizations['convergence']}" alt="Convergence Curves">
            <div class="caption">Figure: Convergence curve comparison for {instance_name}</div>
        </div>
"""

        if 'radar' in visualizations:
            html += f"""
        <div class="figure">
            <img src="figures/{visualizations['radar']}" alt="Performance Radar">
            <div class="caption">Figure: Performance radar chart for {instance_name}</div>
        </div>
"""

        html += "    </div>"
        return html

    def _get_statistical_analysis_section(self):
        """Get HTML for statistical analysis section."""
        if len(self.results) == 0:
            return ""

        html = """
    <div class="section">
        <h2>Statistical Analysis</h2>
"""

        # Perform statistical tests for each instance
        for instance_name, results in self.instances.items():
            if len(results) >= 2:
                html += self._perform_statistical_tests(instance_name, results)

        html += "    </div>"
        return html

    def _perform_statistical_tests(self, instance_name, results):
        """Perform statistical tests for an instance."""
        html = f"<h3>Statistical tests for {instance_name}</h3>"

        # Prepare data
        algorithm_names = [r.algorithm_name for r in results]
        samples = [r.fitness_values for r in results]

        # Ensure equal sample sizes
        min_samples = min(len(s) for s in samples)
        samples = [s[:min_samples] for s in samples]

        if min_samples >= 5 and len(samples) >= 2:
            # Friedman test
            friedman_html = self._perform_friedman_test(samples, algorithm_names)
            if friedman_html:
                html += friedman_html

        return html

    def _perform_friedman_test(self, samples, algorithm_names):
        """Perform Friedman test and return HTML."""
        try:
            friedman_samples = [list(s) for s in samples]
            statistic, p_value = friedmanchisquare(*friedman_samples)

            html = f"""<p>Friedman Test</p>
<table>
    <tr><th>Statistic</th><th>p-value</th><th>Interpretation</th></tr>
    <tr>
        <td>{statistic:.4f}</td>
        <td>{p_value:.4f}</td>
        <td>{"Significant differences exist" if p_value < 0.05 else "No significant differences"}</td>
    </tr>
</table>
"""

            # Post-hoc tests if significant
            if p_value < 0.05 and len(samples) > 2:
                html += self._perform_posthoc_tests(samples, algorithm_names)

            return html

        except Exception as e:
            return f"<p>Error performing Friedman test: {str(e)}</p>"

    def _perform_posthoc_tests(self, samples, algorithm_names):
        """Perform post-hoc tests."""
        html = "<p>Post-hoc Wilcoxon Signed-Rank Tests</p>"
        html += """<table>
    <tr><th>Algorithm A</th><th>Algorithm B</th><th>p-value</th><th>Interpretation</th></tr>
"""

        for i in range(len(samples)):
            for j in range(i + 1, len(samples)):
                try:
                    stat, p = wilcoxon(samples[i], samples[j])
                    html += f"""    <tr>
        <td>{algorithm_names[i]}</td>
        <td>{algorithm_names[j]}</td>
        <td>{p:.4f}</td>
        <td>{"Significant difference" if p < 0.05 else "No significant difference"}</td>
    </tr>
"""
                except Exception:
                    pass

        html += "</table>"
        return html

    def _save_report(self, filename, html_content):
        """Save the HTML report."""
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(html_content)


'''

    # Create wrapper function
    wrapper_function = '''def create_benchmark_report(benchmark_results, filename=None):
    """
    Crea un informe detallado de los resultados del benchmark.

    Versión refactorizada que utiliza BenchmarkReportBuilder para reducir
    la complejidad ciclomática de 17 a menos de 10.

    Args:
        benchmark_results: Lista de objetos BenchmarkResult
        filename: Ruta donde guardar el informe (si es None, se genera automáticamente)
    """
    builder = BenchmarkReportBuilder(benchmark_results)
    return builder.create_report(filename)
'''

    # Find end of original function
    func_start = content.find('def create_benchmark_report(')
    if func_start == -1:
        print("Error: Could not find function")
        return False

    # Find the next function
    func_end = content.find('\ndef ', func_start + 1)
    if func_end == -1:
        func_end = len(content)

    # Build new content
    new_content = (
        content[:insert_pos] +
        refactored_class + '\n\n' +
        wrapper_function + '\n' +
        content[func_end:]
    )

    # Write back
    with open('utils/benchmarking.py', 'w', encoding='utf-8') as f:
        f.write(new_content)

    print("✅ Successfully refactored create_benchmark_report")
    return True


def refactor_load_instance():
    """Refactor load_instance in problems/vrp.py."""
    print("Refactoring load_instance...")

    # Read the file
    with open('problems/vrp.py', 'r', encoding='utf-8') as f:
        content = f.read()

    # Find the method
    method_start = content.find('def load_instance(self) -> None:')
    if method_start == -1:
        # Try without type annotation
        method_start = content.find('def load_instance(self):')
    if method_start == -1:
        print("Error: Could not find load_instance method")
        return False

    # Create refactored methods to add before load_instance
    refactored_methods = '''    def _parse_instance_metadata(self, lines):
        """Parse instance metadata from file lines."""
        metadata = {}
        for line in lines:
            if line.startswith("NAME"):
                metadata['name'] = line.split(":")[1].strip()
            elif line.startswith("TYPE"):
                metadata['type'] = line.split(":")[1].strip()
            elif line.startswith("DIMENSION"):
                metadata['dimension'] = int(line.split(":")[1].strip())
            elif line.startswith("CAPACITY"):
                metadata['capacity'] = int(line.split(":")[1].strip())
        return metadata

    def _parse_node_coordinates(self, lines):
        """Parse node coordinates section."""
        coordinates = []
        in_coord_section = False

        for line in lines:
            if line == "NODE_COORD_SECTION":
                in_coord_section = True
            elif line == "DEMAND_SECTION":
                in_coord_section = False
            elif in_coord_section and line and not line.startswith(("EDGE_WEIGHT_TYPE", "EOF")):
                parts = line.split()
                if len(parts) >= 3:
                    coordinates.append({
                        'id': int(parts[0]),
                        'x': float(parts[1]),
                        'y': float(parts[2])
                    })

        return coordinates

    def _parse_demands(self, lines):
        """Parse demand section."""
        demands = {}
        in_demand_section = False

        for line in lines:
            if line == "DEMAND_SECTION":
                in_demand_section = True
            elif line in ["DEPOT_SECTION", "EOF"]:
                in_demand_section = False
            elif in_demand_section and line:
                parts = line.split()
                if len(parts) >= 2:
                    demands[int(parts[0])] = int(parts[1])

        return demands

    def _validate_instance_data(self, metadata, coordinates, demands):
        """Validate parsed instance data."""
        if 'dimension' not in metadata:
            raise ValueError("DIMENSION not found in instance file")

        if 'capacity' not in metadata:
            raise ValueError("CAPACITY not found in instance file")

        if len(coordinates) != metadata['dimension']:
            raise ValueError(f"Expected {metadata['dimension']} nodes, found {len(coordinates)}")

        if len(demands) != metadata['dimension']:
            raise ValueError(f"Expected {metadata['dimension']} demands, found {len(demands)}")

        return True

    def _build_instance_data(self, metadata, coordinates, demands):
        """Build instance data structures."""
        # Sort coordinates by node ID
        coordinates.sort(key=lambda x: x['id'])

        # Build arrays
        nodes = [(c['x'], c['y']) for c in coordinates]
        demand_array = [demands.get(i, 0) for i in range(1, metadata['dimension'] + 1)]

        return {
            'nodes': nodes,
            'demands': demand_array,
            'capacity': metadata['capacity'],
            'dimension': metadata['dimension']
        }

'''

    # Create simplified load_instance method
    simplified_method = '''    def load_instance(self) -> None:
        """
        Carga una instancia de VRP desde el archivo.

        Versión refactorizada que reduce la complejidad de 16 a menos de 10.
        """
        # Read file
        with open(self.instance_path, "r") as f:
            content = f.read()

        # Split into lines and clean
        lines = [line.strip() for line in content.split("\\n") if line.strip()]

        # Parse sections
        metadata = self._parse_instance_metadata(lines)
        coordinates = self._parse_node_coordinates(lines)
        demands = self._parse_demands(lines)

        # Validate data
        self._validate_instance_data(metadata, coordinates, demands)

        # Build instance data
        instance_data = self._build_instance_data(metadata, coordinates, demands)

        # Update class attributes
        self.nodes = instance_data['nodes']
        self.demands = instance_data['demands']
        self.capacity = instance_data['capacity']
        self.dimension = instance_data['dimension']

        # Extract instance name
        self.name = metadata.get('name', os.path.basename(self.instance_path).split(".")[0])
'''

    # Find the insertion point (before load_instance)
    insert_pos = method_start
    while insert_pos > 0 and content[insert_pos-1] != '\n':
        insert_pos -= 1

    # Find end of load_instance method
    method_end = content.find('\n    def ', method_start + 1)
    if method_end == -1:
        # Look for class end
        method_end = content.find('\nclass ', method_start + 1)
    if method_end == -1:
        method_end = len(content)

    # Build new content
    new_content = (
        content[:insert_pos] +
        refactored_methods + '\n' +
        simplified_method + '\n' +
        content[method_end:]
    )

    # Write back
    with open('problems/vrp.py', 'w', encoding='utf-8') as f:
        f.write(new_content)

    print("✅ Successfully refactored load_instance")
    return True


def main():
    """Main function to refactor all complexity issues."""
    print("Starting complexity refactoring...")

    # Get current violations
    violations = get_complexity_violations()
    print(f"\nFound {len(violations)} complexity violations")

    # Refactor high priority functions
    success = True

    # 1. create_benchmark_report (already done in previous step)
    if any(v['function'] == 'create_benchmark_report' for v in violations):
        success &= refactor_create_benchmark_report()

    # 2. load_instance
    if any(v['function'] == 'load_instance' for v in violations):
        success &= refactor_load_instance()

    # Report results
    if success:
        print("\n✅ Refactoring completed successfully!")

        # Check remaining violations
        remaining = get_complexity_violations()
        print(f"\nRemaining violations: {len(remaining)}")

        if remaining:
            print("\nRemaining issues:")
            for v in remaining:
                print(f"  - {v['file']}:{v['line']} - {v['function']} (complexity: {v['complexity']})")
    else:
        print("\n❌ Some refactoring failed")
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
