#!/usr/bin/env python3
"""
Módulo auxiliar para generar HTML para informes estadísticos.
"""


def generate_html_report(
    metric_str,
    test_info,
    algo_ranks,
    friedman_result,
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
    from datetime import datetime

    # Generar el HTML directamente, sin usar f-strings para bloques grandes
    html = []
    html.append("<!DOCTYPE html>")
    html.append("<html>")
    html.append("<head>")
    html.append(f"<title>Análisis Estadístico - {metric_str}</title>")
    html.append("<style>")
    html.append(
        'body { font-family: "Arial", sans-serif; margin: 20px; line-height: 1.6; }'
    )
    html.append("h1, h2, h3 { color: #2c3e50; }")
    html.append(
        "table { border-collapse: collapse; width: 100%; margin-bottom: 20px; }"
    )
    html.append("th, td { text-align: left; padding: 8px; border: 1px solid #ddd; }")
    html.append("th { background-color: #f2f2f2; }")
    html.append("tr:nth-child(even) { background-color: #f9f9f9; }")
    html.append(".section { margin-bottom: 30px; }")
    html.append(".figure { margin: 20px 0; text-align: center; }")
    html.append(".figure img { max-width: 100%; height: auto; }")
    html.append(".caption { margin-top: 10px; font-style: italic; color: #666; }")
    html.append(".highlight { font-weight: bold; color: #e74c3c; }")
    html.append(".mejor { color: green; font-weight: bold; }")
    html.append(".peor { color: red; font-weight: bold; }")
    html.append(".equal { color: gray; }")
    html.append("</style>")
    html.append("</head>")
    html.append("<body>")

    # Título y generación
    html.append(f"<h1>Análisis Estadístico - {metric_str}</h1>")
    html.append(f'<p>Generado: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}</p>')

    # Resultados de la prueba
    html.append('<div class="section">')
    html.append(f'<h2>Resultados de la Prueba {test_info["Prueba"]}</h2>')
    html.append("<table>")
    html.append("<tr>")
    html.append("<th>Estadístico</th>")
    html.append("<th>p-value</th>")
    html.append("<th>Diferencia Significativa</th>")
    html.append("<th>Distancia Crítica</th>")
    html.append("</tr>")
    html.append("<tr>")
    html.append(f'<td>{test_info["Estadístico"]:.4f}</td>')
    html.append(f'<td>{test_info["p-value"]:.4f}</td>')
    html.append(f'<td>{test_info["Diferencia significativa"]}</td>')
    html.append(f'<td>{test_info["Distancia crítica"]}</td>')
    html.append("</tr>")
    html.append("</table>")

    # Interpretación
    html.append("<p><strong>Interpretación:</strong> ")
    if test_info["Diferencia significativa"] == "Sí":
        html.append(
            f'La prueba {test_info["Prueba"]} indica que hay diferencias estadísticamente significativas entre los algoritmos comparados (p-value < {alpha}).'
        )
    else:
        html.append(
            f'La prueba {test_info["Prueba"]} NO indica diferencias estadísticamente significativas entre los algoritmos comparados (p-value >= {alpha}).'
        )
    html.append("</p>")
    html.append("</div>")

    # Ranking de algoritmos
    html.append('<div class="section">')
    html.append("<h2>Ranking de Algoritmos</h2>")
    html.append("<table>")
    html.append("<tr>")
    html.append("<th>Posición</th>")
    html.append("<th>Algoritmo</th>")
    html.append("<th>Rango Promedio</th>")
    html.append("</tr>")

    for i, (algo, rank) in enumerate(algo_ranks):
        html.append("<tr>")
        html.append(f"<td>{i+1}</td>")
        html.append(f"<td>{algo}</td>")
        html.append(f"<td>{rank:.2f}</td>")
        html.append("</tr>")

    html.append("</table>")
    html.append("</div>")

    # Comparaciones entre algoritmos
    html.append('<div class="section">')
    html.append("<h2>Comparaciones entre Algoritmos</h2>")
    html.append(
        "<p>Simbología: + (mejor), - (peor), = (no hay diferencia significativa)</p>"
    )
    html.append("<table>")
    html.append("<tr>")
    html.append("<th>Algoritmo</th>")
    html.append("<th>Rango</th>")

    # Añadir columnas para cada algoritmo
    for algo, _ in algo_ranks:
        html.append(f"<th>{algo}</th>")

    html.append("</tr>")

    # Añadir filas para cada algoritmo
    for i, (algo_i, rank_i) in enumerate(algo_ranks):
        html.append("<tr>")
        html.append(f"<td>{algo_i}</td>")
        html.append(f"<td>{rank_i:.2f}</td>")

        for j, (algo_j, _) in enumerate(algo_ranks):
            if i == j:
                html.append("<td>-</td>")
            else:
                try:
                    p_value = float(posthoc_matrix.loc[algo_i, algo_j])
                    effect = float(cliff_delta.loc[algo_i, algo_j])

                    symbol = '<span class="equal">=</span>'  # Por defecto, no diferencia significativa
                    if p_value < alpha:
                        if float(rank_i) < float(friedman_result["rank_dict"][algo_j]):
                            symbol = '<span class="mejor">+</span>'  # Mejor
                        else:
                            symbol = '<span class="peor">-</span>'  # Peor

                    html.append(f"<td>{symbol} (p={p_value:.3f}, d={effect:.3f})</td>")
                except Exception:
                    html.append("<td>Error</td>")

        html.append("</tr>")

    html.append("</table>")
    html.append("</div>")

    # Visualizaciones
    html.append('<div class="section">')
    html.append("<h2>Visualizaciones</h2>")

    html.append('<div class="figure">')
    html.append(
        f'<img src="data:image/png;base64,{cd_img}" alt="Critical Difference Diagram">'
    )
    html.append('<div class="caption">Figura 1: Diagrama de diferencia crítica</div>')
    html.append("</div>")

    html.append('<div class="figure">')
    html.append(f'<img src="data:image/png;base64,{rank_img}" alt="Rank Distribution">')
    html.append(
        '<div class="caption">Figura 2: Distribución de rangos por algoritmo</div>'
    )
    html.append("</div>")

    html.append('<div class="figure">')
    html.append(
        f'<img src="data:image/png;base64,{posthoc_img}" alt="Post-hoc Test p-values">'
    )
    html.append(
        '<div class="caption">Figura 3: Matriz de p-values de prueba post-hoc</div>'
    )
    html.append("</div>")

    html.append('<div class="figure">')
    html.append(
        f'<img src="data:image/png;base64,{effect_img}" alt="Effect Size - Cliff\'s Delta">'
    )
    html.append(
        '<div class="caption">Figura 4: Tamaño del efecto (Cliff\'s Delta)</div>'
    )
    html.append("</div>")

    html.append('<div class="figure">')
    html.append(
        f'<img src="data:image/png;base64,{vd_img}" alt="Effect Size - Vargha-Delaney A">'
    )
    html.append(
        '<div class="caption">Figura 5: Tamaño del efecto (Vargha-Delaney A)</div>'
    )
    html.append("</div>")

    html.append("</div>")

    # Interpretación de resultados
    html.append('<div class="section">')
    html.append("<h2>Interpretación de los Resultados</h2>")
    html.append(
        f"<p>Este análisis estadístico para la métrica <strong>{metric_str}</strong> "
    )

    if test_info["Diferencia significativa"] == "Sí":
        html.append(
            "muestra diferencias estadísticamente significativas entre los algoritmos."
        )
    else:
        html.append(
            "no muestra diferencias estadísticamente significativas entre los algoritmos."
        )

    html.append("</p>")

    html.append("<p><strong>Principales conclusiones:</strong></p>")
    html.append("<ul>")

    # Añadir conclusiones basadas en los resultados
    if test_info["Diferencia significativa"] == "Sí" and algo_ranks:
        best_algo = algo_ranks[0][0]
        worst_algo = algo_ranks[-1][0]

        html.append(
            f"<li>El algoritmo <strong>{best_algo}</strong> obtuvo el mejor ranking promedio ({algo_ranks[0][1]:.2f}).</li>"
        )
        html.append(
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
            html.append(
                f'<li>Los algoritmos {", ".join(not_diff_from_best)} no son significativamente diferentes del mejor algoritmo ({best_algo}).</li>'
            )
    else:
        html.append(
            "<li>No se encontraron diferencias estadísticamente significativas entre los algoritmos comparados.</li>"
        )

    html.append("</ul>")
    html.append("</div>")

    html.append("</body>")
    html.append("</html>")

    return "\n".join(html)
