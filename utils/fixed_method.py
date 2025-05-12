#!/usr/bin/env python3
"""
Versión corregida del método generate_statistical_analysis_report
"""

import os
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime
import base64
from io import BytesIO


def generate_html_report(
    data_df,
    metric,
    friedman_result,
    test_info,
    posthoc_matrix,
    cliff_delta,
    alpha,
    cd_img,
    rank_img,
    posthoc_img,
    effect_img,
    vd_img,
):
    """
    Genera contenido HTML para un informe estadístico.
    Este enfoque evita los problemas de formato con f-strings.
    """
    # Convertir la métrica a string seguro para prevenir errores de formato
    metric_str = str(metric).capitalize() if metric else "Desconocida"

    # Definir elementos HTML
    html_parts = []

    # Cabecera y estilo
    html_parts.append("<!DOCTYPE html>")
    html_parts.append("<html>")
    html_parts.append("<head>")
    html_parts.append(f"<title>Análisis Estadístico - {metric_str}</title>")
    html_parts.append("<style>")
    html_parts.append(
        'body { font-family: "Arial", sans-serif; margin: 20px; line-height: 1.6; }'
    )
    html_parts.append("h1, h2, h3 { color: #2c3e50; }")
    html_parts.append(
        "table { border-collapse: collapse; width: 100%; margin-bottom: 20px; }"
    )
    html_parts.append(
        "th, td { text-align: left; padding: 8px; border: 1px solid #ddd; }"
    )
    html_parts.append("th { background-color: #f2f2f2; }")
    html_parts.append("tr:nth-child(even) { background-color: #f9f9f9; }")
    html_parts.append(".section { margin-bottom: 30px; }")
    html_parts.append(".figure { margin: 20px 0; text-align: center; }")
    html_parts.append(".figure img { max-width: 100%; height: auto; }")
    html_parts.append(".caption { margin-top: 10px; font-style: italic; color: #666; }")
    html_parts.append(".mejor { color: green; font-weight: bold; }")
    html_parts.append(".peor { color: red; font-weight: bold; }")
    html_parts.append(".equal { color: gray; }")
    html_parts.append("</style>")
    html_parts.append("</head>")
    html_parts.append("<body>")

    # Contenido
    html_parts.append(f"<h1>Análisis Estadístico - {metric_str}</h1>")
    html_parts.append(
        f'<p>Generado: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}</p>'
    )

    # Resultados de la prueba
    html_parts.append('<div class="section">')
    html_parts.append(f'<h2>Resultados de la Prueba {test_info["Prueba"]}</h2>')
    html_parts.append("<table>")
    html_parts.append("<tr>")
    html_parts.append("<th>Estadístico</th>")
    html_parts.append("<th>p-value</th>")
    html_parts.append("<th>Diferencia Significativa</th>")
    html_parts.append("<th>Distancia Crítica</th>")
    html_parts.append("</tr>")
    html_parts.append("<tr>")
    html_parts.append(f'<td>{test_info["Estadístico"]:.4f}</td>')
    html_parts.append(f'<td>{test_info["p-value"]:.4f}</td>')
    html_parts.append(f'<td>{test_info["Diferencia significativa"]}</td>')
    html_parts.append(f'<td>{test_info["Distancia crítica"]}</td>')
    html_parts.append("</tr>")
    html_parts.append("</table>")

    # Interpretación
    html_parts.append("<p><strong>Interpretación:</strong> ")
    if test_info["Diferencia significativa"] == "Sí":
        html_parts.append(
            f'La prueba {test_info["Prueba"]} indica que hay diferencias estadísticamente significativas entre los algoritmos comparados (p-value < {alpha}).'
        )
    else:
        html_parts.append(
            f'La prueba {test_info["Prueba"]} NO indica diferencias estadísticamente significativas entre los algoritmos comparados (p-value >= {alpha}).'
        )
    html_parts.append("</p>")
    html_parts.append("</div>")

    # Ranking de algoritmos
    html_parts.append('<div class="section">')
    html_parts.append("<h2>Ranking de Algoritmos</h2>")
    html_parts.append("<table>")
    html_parts.append("<tr>")
    html_parts.append("<th>Posición</th>")
    html_parts.append("<th>Algoritmo</th>")
    html_parts.append("<th>Rango Promedio</th>")
    html_parts.append("</tr>")

    # Añadir filas para cada algoritmo (ordenados por rango)
    algo_ranks = []
    if "error" not in friedman_result:
        algo_ranks = [
            (algo, friedman_result["rank_dict"][algo])
            for algo in friedman_result["algorithms"]
        ]
        algo_ranks.sort(key=lambda x: x[1])

        for i, (algo, rank) in enumerate(algo_ranks):
            html_parts.append("<tr>")
            html_parts.append(f"<td>{i+1}</td>")
            html_parts.append(f"<td>{algo}</td>")
            html_parts.append(f"<td>{rank:.2f}</td>")
            html_parts.append("</tr>")

    html_parts.append("</table>")
    html_parts.append("</div>")

    # Comparaciones entre algoritmos
    if "error" not in friedman_result and algo_ranks:
        html_parts.append('<div class="section">')
        html_parts.append("<h2>Comparaciones entre Algoritmos</h2>")
        html_parts.append(
            "<p>Simbología: + (mejor), - (peor), = (no hay diferencia significativa)</p>"
        )
        html_parts.append("<table>")
        html_parts.append("<tr>")
        html_parts.append("<th>Algoritmo</th>")
        html_parts.append("<th>Rango</th>")

        # Añadir columnas para cada algoritmo
        for algo, _ in algo_ranks:
            html_parts.append(f"<th>{algo}</th>")

        html_parts.append("</tr>")

        # Añadir filas para cada algoritmo
        for i, (algo_i, rank_i) in enumerate(algo_ranks):
            html_parts.append("<tr>")
            html_parts.append(f"<td>{algo_i}</td>")
            html_parts.append(f"<td>{rank_i:.2f}</td>")

            for j, (algo_j, _) in enumerate(algo_ranks):
                if i == j:
                    html_parts.append("<td>-</td>")
                else:
                    try:
                        p_value = float(posthoc_matrix.loc[algo_i, algo_j])
                        effect = float(cliff_delta.loc[algo_i, algo_j])

                        symbol = '<span class="equal">=</span>'  # Por defecto, no diferencia significativa
                        if p_value < alpha:
                            if float(rank_i) < float(
                                friedman_result["rank_dict"][algo_j]
                            ):
                                symbol = '<span class="mejor">+</span>'  # Mejor
                            else:
                                symbol = '<span class="peor">-</span>'  # Peor

                        html_parts.append(
                            f"<td>{symbol} (p={p_value:.3f}, d={effect:.3f})</td>"
                        )
                    except Exception:
                        html_parts.append("<td>Error</td>")

            html_parts.append("</tr>")

        html_parts.append("</table>")
        html_parts.append("</div>")

    # Visualizaciones
    html_parts.append('<div class="section">')
    html_parts.append("<h2>Visualizaciones</h2>")

    html_parts.append('<div class="figure">')
    html_parts.append(
        f'<img src="data:image/png;base64,{cd_img}" alt="Critical Difference Diagram">'
    )
    html_parts.append(
        '<div class="caption">Figura 1: Diagrama de diferencia crítica</div>'
    )
    html_parts.append("</div>")

    html_parts.append('<div class="figure">')
    html_parts.append(
        f'<img src="data:image/png;base64,{rank_img}" alt="Rank Distribution">'
    )
    html_parts.append(
        '<div class="caption">Figura 2: Distribución de rangos por algoritmo</div>'
    )
    html_parts.append("</div>")

    html_parts.append('<div class="figure">')
    html_parts.append(
        f'<img src="data:image/png;base64,{posthoc_img}" alt="Post-hoc Test p-values">'
    )
    html_parts.append(
        '<div class="caption">Figura 3: Matriz de p-values de prueba post-hoc</div>'
    )
    html_parts.append("</div>")

    html_parts.append('<div class="figure">')
    html_parts.append(
        f'<img src="data:image/png;base64,{effect_img}" alt="Effect Size - Cliff\'s Delta">'
    )
    html_parts.append(
        '<div class="caption">Figura 4: Tamaño del efecto (Cliff\'s Delta)</div>'
    )
    html_parts.append("</div>")

    html_parts.append('<div class="figure">')
    html_parts.append(
        f'<img src="data:image/png;base64,{vd_img}" alt="Effect Size - Vargha-Delaney A">'
    )
    html_parts.append(
        '<div class="caption">Figura 5: Tamaño del efecto (Vargha-Delaney A)</div>'
    )
    html_parts.append("</div>")

    html_parts.append("</div>")

    # Interpretación de resultados
    html_parts.append('<div class="section">')
    html_parts.append("<h2>Interpretación de los Resultados</h2>")
    html_parts.append(
        f"<p>Este análisis estadístico para la métrica <strong>{metric_str}</strong> "
    )

    if test_info["Diferencia significativa"] == "Sí":
        html_parts.append(
            "muestra diferencias estadísticamente significativas entre los algoritmos."
        )
    else:
        html_parts.append(
            "no muestra diferencias estadísticamente significativas entre los algoritmos."
        )

    html_parts.append("</p>")

    html_parts.append("<p><strong>Principales conclusiones:</strong></p>")
    html_parts.append("<ul>")

    # Añadir conclusiones basadas en los resultados
    if (
        "error" not in friedman_result
        and test_info["Diferencia significativa"] == "Sí"
        and algo_ranks
    ):
        best_algo = algo_ranks[0][0]
        worst_algo = algo_ranks[-1][0]

        html_parts.append(
            f"<li>El algoritmo <strong>{best_algo}</strong> obtuvo el mejor ranking promedio ({algo_ranks[0][1]:.2f}).</li>"
        )
        html_parts.append(
            f"<li>El algoritmo <strong>{worst_algo}</strong> obtuvo el peor ranking promedio ({algo_ranks[-1][1]:.2f}).</li>"
        )

        # Buscar algoritmos que no sean significativamente diferentes del mejor
        not_diff_from_best = []
        for algo_j, _ in algo_ranks[1:]:
            try:
                if posthoc_matrix.loc[best_algo, algo_j] >= alpha:
                    not_diff_from_best.append(algo_j)
            except:
                continue

        if not_diff_from_best:
            html_parts.append(
                f'<li>Los algoritmos {", ".join(not_diff_from_best)} no son significativamente diferentes del mejor algoritmo ({best_algo}).</li>'
            )
    else:
        html_parts.append(
            "<li>No se encontraron diferencias estadísticamente significativas entre los algoritmos comparados.</li>"
        )

    html_parts.append("</ul>")
    html_parts.append("</div>")

    html_parts.append("</body>")
    html_parts.append("</html>")

    # Unir las partes HTML
    return "\n".join(html_parts)


def perform_statistical_analysis_report(
    data_df,
    metric="best_fitness",
    alpha=0.05,
    output_file=None,
    StatisticalAnalysis=None,
):
    """
    Genera un informe completo de análisis estadístico en formato HTML.
    """
    try:
        # Si no se especifica archivo de salida, generar nombre automático
        if output_file is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_file = f"results/statistical_report_{metric}_{timestamp}.html"

        # Crear directorio si no existe
        os.makedirs(os.path.dirname(output_file), exist_ok=True)

        # Realizar prueba de Friedman y análisis estadístico
        from io import BytesIO
        import base64
        import matplotlib.pyplot as plt

        # Validar los datos de entrada
        print(f"Debug - Análisis de datos para {metric}:")
        print(f"- Instancias: {data_df['Instance'].nunique()}")
        print(f"- Algoritmos: {data_df['Algorithm'].nunique()}")
        print(f"- Total de ejecuciones: {len(data_df)}")

        # Verificar si hay suficientes datos para un análisis estadístico
        if data_df["Instance"].nunique() < 2 and data_df["Algorithm"].nunique() < 2:
            error_msg = "Datos insuficientes para análisis estadístico: se requieren múltiples instancias o algoritmos."
            with open(output_file, "w") as f:
                f.write(
                    f"""
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
                )
            return output_file

        # Realizar prueba de Friedman
        friedman_result = StatisticalAnalysis.friedman_test(data_df, alpha=alpha)

        # Información sobre el resultado Friedman
        print("Debug - Resultado de Friedman:")
        for key, value in friedman_result.items():
            if key not in ["avg_ranks", "algorithms"]:
                print(f"- {key}: {value}")

        # Realizar pruebas post-hoc
        try:
            posthoc_matrix, cd = StatisticalAnalysis.nemenyi_test(friedman_result)
            print(f"Debug - Post-hoc completado con éxito. CD = {cd}")
        except Exception as e:
            print(f"Debug - Error en post-hoc: {str(e)}")
            # Crear matrices vacías si falla
            algorithms = friedman_result.get("algorithms", [])
            posthoc_matrix = pd.DataFrame(1.0, index=algorithms, columns=algorithms)
            cd = 0

        # Realizar pruebas por pares con Wilcoxon
        try:
            wilcoxon_matrix, wilcoxon_effect = StatisticalAnalysis.wilcoxon_paired_test(
                data_df, alpha=alpha, bonferroni_correction=True
            )
            print("Debug - Wilcoxon completado con éxito.")
        except Exception as e:
            print(f"Debug - Error en Wilcoxon: {str(e)}")
            # Crear matrices vacías si falla
            algorithms = friedman_result.get("algorithms", [])
            wilcoxon_matrix = pd.DataFrame(1.0, index=algorithms, columns=algorithms)
            wilcoxon_effect = pd.DataFrame(0.0, index=algorithms, columns=algorithms)

        # Calcular diferentes medidas de efecto tamaño
        try:
            cliff_delta = StatisticalAnalysis.effect_size_cliff_delta(data_df)
            vargha_delaney = StatisticalAnalysis.vargha_delaney_a_measure(data_df)
            print("Debug - Cálculo de efecto tamaño completado con éxito.")
        except Exception as e:
            print(f"Debug - Error en cálculo de efecto tamaño: {str(e)}")
            # Crear matrices vacías si falla
            algorithms = friedman_result.get("algorithms", [])
            cliff_delta = pd.DataFrame(0.0, index=algorithms, columns=algorithms)
            vargha_delaney = pd.DataFrame(0.5, index=algorithms, columns=algorithms)

        # Generar tabla de comparación
        (
            comparison_table,
            test_info,
        ) = StatisticalAnalysis.generate_statistical_comparison_table(
            friedman_result,
            posthoc_matrix,
            cliff_delta,
            method="cliff_delta",
            alpha=alpha,
        )

        # Generar visualizaciones
        figures_dir = os.path.join(os.path.dirname(output_file), "figures")
        os.makedirs(figures_dir, exist_ok=True)

        # Función para convertir figura a string base64 de forma segura
        def fig_to_base64(fig):
            try:
                buf = BytesIO()
                fig.savefig(buf, format="png")
                buf.seek(0)
                img_str = base64.b64encode(buf.getvalue()).decode("utf-8")
                plt.close(fig)
                return img_str
            except Exception as e:
                print(f"Debug - Error al convertir figura a base64: {str(e)}")
                # Generar una imagen de error alternativa
                error_fig, ax = plt.subplots(figsize=(8, 2))
                ax.text(
                    0.5,
                    0.5,
                    f"Error al generar gráfico: {str(e)}",
                    ha="center",
                    va="center",
                    fontsize=12,
                    color="red",
                )
                ax.axis("off")

                buf = BytesIO()
                error_fig.savefig(buf, format="png")
                buf.seek(0)
                img_str = base64.b64encode(buf.getvalue()).decode("utf-8")
                plt.close(error_fig)
                return img_str

        # Generar visualizaciones dentro de bloques try/except para manejar errores
        metric_str = str(metric).capitalize() if metric else "Desconocida"

        try:
            cd_diagram = StatisticalAnalysis.plot_critical_difference_diagram(
                friedman_result, title=f"Diagrama de Diferencia Crítica - {metric_str}"
            )
            cd_img = fig_to_base64(cd_diagram)
        except Exception as e:
            print(f"Debug - Error al generar diagrama CD: {str(e)}")
            cd_img = fig_to_base64(plt.figure(figsize=(8, 2)))

        try:
            posthoc_heatmap = StatisticalAnalysis.plot_posthoc_heatmap(
                posthoc_matrix, title=f"P-values Post-hoc - {metric_str}", alpha=alpha
            )
            posthoc_img = fig_to_base64(posthoc_heatmap)
        except Exception as e:
            print(f"Debug - Error al generar mapa de calor post-hoc: {str(e)}")
            posthoc_img = fig_to_base64(plt.figure(figsize=(8, 2)))

        try:
            effect_heatmap = StatisticalAnalysis.plot_effect_size_heatmap(
                cliff_delta, method="cliff_delta", title=f"Cliff's Delta - {metric_str}"
            )
            effect_img = fig_to_base64(effect_heatmap)
        except Exception as e:
            print(f"Debug - Error al generar mapa de efecto tamaño: {str(e)}")
            effect_img = fig_to_base64(plt.figure(figsize=(8, 2)))

        try:
            vd_heatmap = StatisticalAnalysis.plot_effect_size_heatmap(
                vargha_delaney,
                method="vargha_delaney",
                title=f"Vargha-Delaney A - {metric_str}",
            )
            vd_img = fig_to_base64(vd_heatmap)
        except Exception as e:
            print(f"Debug - Error al generar mapa Vargha-Delaney: {str(e)}")
            vd_img = fig_to_base64(plt.figure(figsize=(8, 2)))

        try:
            rank_boxplot = StatisticalAnalysis.plot_rank_boxplot(
                data_df, friedman_result, title=f"Distribución de Rangos - {metric_str}"
            )
            rank_img = fig_to_base64(rank_boxplot)
        except Exception as e:
            print(f"Debug - Error al generar boxplot de rangos: {str(e)}")
            rank_img = fig_to_base64(plt.figure(figsize=(8, 2)))

        # Generar HTML utilizando una función externa para evitar problemas de formato
        html_content = generate_html_report(
            data_df,
            metric,
            friedman_result,
            test_info,
            posthoc_matrix,
            cliff_delta,
            alpha,
            cd_img,
            rank_img,
            posthoc_img,
            effect_img,
            vd_img,
        )

        # Guardar el informe
        with open(output_file, "w") as f:
            f.write(html_content)

        print(f"✅ Informe generado para {metric}")
        return output_file

    except Exception as e:
        # Si hay un error crítico, crear un informe de error simple
        print(f"⚠️ Error durante el análisis estadístico: {str(e)}")
        error_file = (
            output_file
            or f"results/error_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html"
        )
        os.makedirs(os.path.dirname(error_file), exist_ok=True)

        with open(error_file, "w") as f:
            f.write(
                f"""
<!DOCTYPE html>
<html>
<head><title>Error en Análisis Estadístico</title></head>
<body>
<h1>Error en el Análisis Estadístico</h1>
<p>Ocurrió un error al generar el informe estadístico:</p>
<pre>{str(e)}</pre>
</body>
</html>
            """
            )
        return error_file
