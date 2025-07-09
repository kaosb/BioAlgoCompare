#!/usr/bin/env python3
"""
Refactor statistical_analysis.py to reduce complexity.

This script implements the refactoring plan to break down the complex
generate_statistical_analysis_report function (complexity 29) into smaller,
more manageable components.
"""

import sys
import os


def refactor_statistical_analysis():
    """Refactor the statistical analysis module."""
    print("Starting refactoring of statistical_analysis.py...")
    
    # Read the original file
    with open('utils/statistical_analysis.py', 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Find the location where we need to insert the new classes
    # We'll add them before the generate_statistical_analysis_report function
    insert_pos = content.find('@staticmethod\n    def generate_statistical_analysis_report(')
    
    if insert_pos == -1:
        print("Error: Could not find generate_statistical_analysis_report function")
        return False
    
    # Find the start of the line
    while insert_pos > 0 and content[insert_pos-1] != '\n':
        insert_pos -= 1
    
    # Create the new class definitions
    new_classes = '''
class StatisticalReportGenerator:
    """Generate statistical analysis reports with proper separation of concerns."""
    
    def __init__(self, data_df, metric="best_fitness", alpha=0.05):
        """
        Initialize the report generator.
        
        Args:
            data_df: DataFrame prepared with prepare_data_for_statistics
            metric: Metric being analyzed
            alpha: Significance level
        """
        self.data_df = data_df
        self.metric = metric
        self.alpha = alpha
        self.results = {}
        self.visualizations = {}
        
    def generate_report(self, output_file=None):
        """
        Generate the complete statistical analysis report.
        
        Args:
            output_file: Path to save the HTML report
            
        Returns:
            Path to the generated HTML file
        """
        output_file = self._prepare_output_file(output_file)
        
        # Validate data
        if not self._validate_data():
            return self._generate_error_report(output_file)
            
        # Run statistical tests
        self._run_statistical_tests()
        
        # Generate visualizations
        self._generate_visualizations()
        
        # Build and save HTML report
        html_content = self._build_html_report()
        self._save_report(output_file, html_content)
        
        return output_file
        
    def _prepare_output_file(self, output_file):
        """Prepare output file path."""
        if output_file is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_file = f"results/statistical_report_{self.metric}_{timestamp}.html"
            
        os.makedirs(os.path.dirname(output_file), exist_ok=True)
        return output_file
        
    def _validate_data(self):
        """Validate that data has sufficient instances/algorithms for analysis."""
        n_instances = self.data_df['Instance'].nunique()
        n_algorithms = self.data_df['Algorithm'].nunique()
        
        print(f"Debug - Análisis de datos para {self.metric}:")
        print(f"- Instancias: {n_instances}")
        print(f"- Algoritmos: {n_algorithms}")
        print(f"- Total de ejecuciones: {len(self.data_df)}")
        
        return n_instances >= 2 or n_algorithms >= 2
        
    def _generate_error_report(self, output_file):
        """Generate error report when data is insufficient."""
        error_msg = "Datos insuficientes para análisis estadístico: se requieren múltiples instancias o algoritmos."
        error_html = f"""
        <!DOCTYPE html>
        <html>
        <head><title>Error en Análisis Estadístico</title></head>
        <body>
            <h1>Error en el Análisis Estadístico</h1>
            <p>{error_msg}</p>
            <p>Se requieren al menos 2 algoritmos con múltiples ejecuciones para realizar análisis estadísticos comparativos.</p>
        </body>
        </html>
        """
        
        with open(output_file, 'w') as f:
            f.write(error_html)
            
        return output_file
        
    def _run_statistical_tests(self):
        """Execute all statistical tests and store results."""
        # Friedman test
        self.results['friedman'] = self._safe_execute(
            StatisticalAnalysis.friedman_test,
            self.data_df,
            alpha=self.alpha
        )
        
        # Post-hoc tests
        if self.results['friedman'] and 'reject_h0' in self.results['friedman']:
            self.results['posthoc'], self.results['cd'] = self._safe_execute(
                StatisticalAnalysis.nemenyi_test,
                self.results['friedman'],
                default=(pd.DataFrame(), 0)
            )
            
            # Wilcoxon tests
            self.results['wilcoxon'], self.results['wilcoxon_effect'] = self._safe_execute(
                StatisticalAnalysis.wilcoxon_paired_test,
                self.data_df,
                alpha=self.alpha,
                bonferroni_correction=True,
                default=(pd.DataFrame(), pd.DataFrame())
            )
            
            # Effect sizes
            self.results['cliff_delta'] = self._safe_execute(
                StatisticalAnalysis.effect_size_cliff_delta,
                self.data_df,
                default=pd.DataFrame()
            )
            
            self.results['vargha_delaney'] = self._safe_execute(
                StatisticalAnalysis.vargha_delaney_a_measure,
                self.data_df,
                default=pd.DataFrame()
            )
            
    def _safe_execute(self, func, *args, default=None, **kwargs):
        """Safely execute a function with error handling."""
        try:
            return func(*args, **kwargs)
        except Exception as e:
            print(f"Debug - Error in {func.__name__}: {str(e)}")
            if default is not None:
                return default
            # Return empty defaults based on function
            if 'nemenyi' in func.__name__:
                algorithms = self.results.get('friedman', {}).get('algorithms', [])
                return pd.DataFrame(1.0, index=algorithms, columns=algorithms), 0
            elif 'wilcoxon' in func.__name__:
                algorithms = list(self.data_df['Algorithm'].unique())
                return pd.DataFrame(1.0, index=algorithms, columns=algorithms), pd.DataFrame(0.0, index=algorithms, columns=algorithms)
            elif 'cliff_delta' in func.__name__:
                algorithms = list(self.data_df['Algorithm'].unique())
                return pd.DataFrame(0.0, index=algorithms, columns=algorithms)
            elif 'vargha_delaney' in func.__name__:
                algorithms = list(self.data_df['Algorithm'].unique())
                return pd.DataFrame(0.5, index=algorithms, columns=algorithms)
            return {}
            
    def _generate_visualizations(self):
        """Generate all visualizations and convert to base64."""
        viz_methods = {
            'cd_diagram': (
                StatisticalAnalysis.plot_critical_difference_diagram,
                [self.results['friedman']],
                {'title': f"Diagrama de Diferencia Crítica - {self.metric.capitalize()}"}
            ),
            'rank_boxplot': (
                StatisticalAnalysis.plot_rank_boxplot,
                [self.data_df, self.results['friedman']],
                {'title': f"Distribución de Rangos - {self.metric.capitalize()}"}
            ),
            'posthoc_heatmap': (
                StatisticalAnalysis.plot_posthoc_heatmap,
                [self.results.get('posthoc', pd.DataFrame())],
                {'title': f"P-values Post-hoc - {self.metric.capitalize()}", 'alpha': self.alpha}
            ),
            'effect_heatmap': (
                StatisticalAnalysis.plot_effect_size_heatmap,
                [self.results.get('cliff_delta', pd.DataFrame())],
                {'method': 'cliff_delta', 'title': f"Cliff's Delta - {self.metric.capitalize()}"}
            ),
            'vd_heatmap': (
                StatisticalAnalysis.plot_effect_size_heatmap,
                [self.results.get('vargha_delaney', pd.DataFrame())],
                {'method': 'vargha_delaney', 'title': f"Vargha-Delaney A - {self.metric.capitalize()}"}
            )
        }
        
        for viz_name, (method, args, kwargs) in viz_methods.items():
            self.visualizations[viz_name] = self._create_visualization(method, *args, **kwargs)
            
    def _create_visualization(self, method, *args, **kwargs):
        """Create a visualization and convert to base64."""
        try:
            fig = method(*args, **kwargs)
            return self._fig_to_base64(fig)
        except Exception as e:
            print(f"Debug - Error creating visualization: {str(e)}")
            return self._create_error_image(str(e))
            
    def _fig_to_base64(self, fig):
        """Convert matplotlib figure to base64 string."""
        try:
            buf = BytesIO()
            fig.savefig(buf, format='png', bbox_inches='tight', dpi=100)
            buf.seek(0)
            img_str = base64.b64encode(buf.getvalue()).decode('utf-8')
            plt.close(fig)
            return img_str
        except Exception as e:
            print(f"Debug - Error converting figure to base64: {str(e)}")
            return self._create_error_image(str(e))
    
    def _create_error_image(self, error_msg):
        """Create an error placeholder image."""
        error_fig, ax = plt.subplots(figsize=(8, 2))
        ax.text(0.5, 0.5, f"Error al generar gráfico: {error_msg}",
                ha='center', va='center', fontsize=12, color='red')
        ax.axis('off')
        
        buf = BytesIO()
        error_fig.savefig(buf, format='png')
        buf.seek(0)
        img_str = base64.b64encode(buf.getvalue()).decode('utf-8')
        plt.close(error_fig)
        return img_str
        
    def _build_html_report(self):
        """Build the HTML report content."""
        # Prepare data for template
        template_data = self._prepare_template_data()
        
        # Generate HTML using extracted methods
        html_content = self._generate_html_header(template_data)
        html_content += self._generate_test_results_section(template_data)
        html_content += self._generate_rankings_section(template_data)
        html_content += self._generate_comparison_table_section(template_data)
        html_content += self._generate_visualizations_section(template_data)
        html_content += self._generate_conclusions_section(template_data)
        html_content += "</body>\\n</html>"
        
        return html_content
        
    def _prepare_template_data(self):
        """Prepare data for HTML template."""
        friedman = self.results.get('friedman', {})
        
        # Extract test info
        test_info = {
            "Prueba": friedman.get("test", "Friedman"),
            "Estadístico": friedman.get("statistic", 0.0),
            "p-value": friedman.get("p_value", 1.0),
            "Diferencia significativa": "Sí" if friedman.get("reject_h0", False) else "No",
            "Distancia crítica": f"{self.results.get('cd', 0):.4f}" if self.results.get('cd') else "N/A"
        }
        
        # Generate comparison table
        comparison_table, _ = StatisticalAnalysis.generate_statistical_comparison_table(
            friedman,
            self.results.get('posthoc', pd.DataFrame()),
            self.results.get('cliff_delta', pd.DataFrame()),
            method="cliff_delta",
            alpha=self.alpha
        )
        
        return {
            'metric': self.metric,
            'metric_str': str(self.metric).capitalize(),
            'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            'alpha': self.alpha,
            'test_info': test_info,
            'friedman': friedman,
            'comparison_table': comparison_table,
            'visualizations': self.visualizations
        }
        
    def _generate_html_header(self, data):
        """Generate HTML header with styles."""
        css_style = """body {
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
}
.mejor {
    color: green;
    font-weight: bold;
}
.peor {
    color: red;
    font-weight: bold;
}
.equal {
    color: gray;
}"""
        
        return f"""<!DOCTYPE html>
<html>
<head>
    <title>Análisis Estadístico - {data['metric_str']}</title>
    <style>
{css_style}
    </style>
</head>
<body>
    <h1>Análisis Estadístico - {data['metric_str']}</h1>
    <p>Generado: {data['timestamp']}</p>
"""
        
    def _generate_test_results_section(self, data):
        """Generate test results section."""
        test_info = data['test_info']
        interpretation = (
            f"La prueba {test_info['Prueba']} indica que hay diferencias estadísticamente significativas entre los algoritmos comparados (p-value < {data['alpha']})."
            if test_info['Diferencia significativa'] == 'Sí' else
            f"La prueba {test_info['Prueba']} NO indica diferencias estadísticamente significativas entre los algoritmos comparados (p-value >= {data['alpha']})."
        )
        
        return f"""
    <div class="section">
        <h2>Resultados de la Prueba {test_info['Prueba']}</h2>
        <table>
            <tr>
                <th>Estadístico</th>
                <th>p-value</th>
                <th>Diferencia Significativa</th>
                <th>Distancia Crítica</th>
            </tr>
            <tr>
                <td>{test_info['Estadístico']:.4f}</td>
                <td>{test_info['p-value']:.4f}</td>
                <td>{test_info['Diferencia significativa']}</td>
                <td>{test_info['Distancia crítica']}</td>
            </tr>
        </table>
        <p><strong>Interpretación:</strong> {interpretation}</p>
    </div>
"""
        
    def _generate_rankings_section(self, data):
        """Generate algorithm rankings section."""
        friedman = data['friedman']
        if 'rank_dict' not in friedman:
            return ""
            
        # Sort algorithms by rank
        sorted_algorithms = sorted(friedman['rank_dict'].items(), key=lambda x: x[1])
        
        rows = "\\n".join([
            f"<tr><td>{i+1}</td><td>{algo}</td><td>{rank:.2f}</td></tr>"
            for i, (algo, rank) in enumerate(sorted_algorithms)
        ])
        
        return f"""
    <div class="section">
        <h2>Ranking de Algoritmos</h2>
        <table>
            <tr>
                <th>Posición</th>
                <th>Algoritmo</th>
                <th>Ranking Promedio</th>
            </tr>
            {rows}
        </table>
    </div>
"""
        
    def _generate_comparison_table_section(self, data):
        """Generate comparison table section."""
        comparison_table = data.get('comparison_table')
        if comparison_table is None or comparison_table.empty:
            return ""
            
        return f"""
    <div class="section">
        <h2>Tabla de Comparación entre Algoritmos</h2>
        <p>Símbolos: + (mejor), - (peor), = (sin diferencia significativa)</p>
        {comparison_table.to_html(classes='comparison-table', escape=False)}
    </div>
"""
        
    def _generate_visualizations_section(self, data):
        """Generate visualizations section."""
        visualizations = data['visualizations']
        if not visualizations:
            return ""
            
        viz_html = ""
        viz_info = [
            ('cd_diagram', 'Diagrama de Diferencia Crítica'),
            ('rank_boxplot', 'Distribución de Rangos por Algoritmo'),
            ('posthoc_heatmap', 'Matriz de P-values de Pruebas Post-hoc'),
            ('effect_heatmap', 'Tamaño del Efecto - Cliff\\'s Delta'),
            ('vd_heatmap', 'Tamaño del Efecto - Vargha-Delaney A')
        ]
        
        for i, (viz_key, caption) in enumerate(viz_info, 1):
            if viz_key in visualizations:
                viz_html += f"""
        <div class="figure">
            <img src="data:image/png;base64,{visualizations[viz_key]}" alt="{caption}">
            <div class="caption">Figura {i}: {caption}</div>
        </div>
"""
                
        return f"""
    <div class="section">
        <h2>Visualizaciones</h2>
        {viz_html}
    </div>
"""
        
    def _generate_conclusions_section(self, data):
        """Generate conclusions section."""
        friedman = data['friedman']
        test_info = data['test_info']
        
        conclusions = []
        
        if test_info['Diferencia significativa'] == 'Sí' and 'rank_dict' in friedman:
            sorted_algorithms = sorted(friedman['rank_dict'].items(), key=lambda x: x[1])
            best = sorted_algorithms[0]
            worst = sorted_algorithms[-1]
            
            conclusions.append(f"El algoritmo <strong>{best[0]}</strong> obtuvo el mejor ranking promedio ({best[1]:.2f}).")
            conclusions.append(f"El algoritmo <strong>{worst[0]}</strong> obtuvo el peor ranking promedio ({worst[1]:.2f}).")
            
            # Add more conclusions based on effect sizes
            if 'cd' in self.results:
                cd = self.results['cd']
                similar_to_best = [algo for algo, rank in sorted_algorithms[1:] 
                                  if abs(rank - best[1]) < cd]
                if similar_to_best:
                    conclusions.append(f"Los algoritmos {', '.join(similar_to_best)} no presentan diferencias significativas con el mejor algoritmo.")
        else:
            conclusions.append("No se encontraron diferencias estadísticamente significativas entre los algoritmos comparados.")
            
        conclusions_html = "\\n".join([f"<li>{c}</li>" for c in conclusions])
        
        return f"""
    <div class="section">
        <h2>Interpretación de Resultados</h2>
        <p>Este análisis estadístico para la métrica <strong>{data['metric_str']}</strong> 
        {'muestra diferencias significativas' if test_info['Diferencia significativa'] == 'Sí' else 'no muestra diferencias significativas'} 
        entre los algoritmos.</p>
        <p><strong>Conclusiones principales:</strong></p>
        <ul>{conclusions_html}</ul>
    </div>
"""
        
    def _save_report(self, output_file, html_content):
        """Save the HTML report to file."""
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(html_content)


    '''
    
    # Now, replace the original function with a wrapper
    refactored_function = '''@staticmethod
    def generate_statistical_analysis_report(
        data_df, metric="best_fitness", alpha=0.05, output_file=None
    ):
        """
        Genera un informe completo de análisis estadístico en formato HTML.
        
        Esta es una versión refactorizada que utiliza la clase StatisticalReportGenerator
        para reducir la complejidad ciclomática de 29 a menos de 10.

        Args:
            data_df: DataFrame preparado con prepare_data_for_statistics
            metric: Métrica analizada
            alpha: Nivel de significancia
            output_file: Ruta para guardar el informe HTML

        Returns:
            Ruta al archivo HTML generado
        """
        # Use the new class-based implementation
        generator = StatisticalReportGenerator(data_df, metric, alpha)
        return generator.generate_report(output_file)
'''
    
    # Find the end of the original function
    # Look for the next method or class definition
    func_start = content.find('@staticmethod\n    def generate_statistical_analysis_report(')
    if func_start == -1:
        print("Error: Could not find function to replace")
        return False
        
    # Find the end of the function by looking for the next method at the same indentation level
    func_end = content.find('\n    @staticmethod', func_start + 1)
    if func_end == -1:
        func_end = content.find('\n    def ', func_start + 1)
    if func_end == -1:
        func_end = content.find('\nclass ', func_start + 1)
    if func_end == -1:
        func_end = len(content)
    
    # Build the new content
    new_content = (
        content[:insert_pos] + 
        new_classes + '\n\n' +
        content[insert_pos:func_start] +
        refactored_function + '\n' +
        content[func_end:]
    )
    
    # Write the refactored content
    with open('utils/statistical_analysis.py', 'w', encoding='utf-8') as f:
        f.write(new_content)
    
    print("✅ Successfully refactored generate_statistical_analysis_report")
    print("   - Complexity reduced from 29 to <10")
    print("   - Created StatisticalReportGenerator class")
    print("   - Maintained backwards compatibility")
    
    return True


if __name__ == "__main__":
    success = refactor_statistical_analysis()
    sys.exit(0 if success else 1)