# Análisis Comparativo de Benchmarks

Esta carpeta contiene los resultados gráficos de análisis comparativos entre diferentes algoritmos para instancias Solomon VRP.

## Contenido típico

- **algoritmos_por_serie.png**: Comparación de algoritmos agrupados por serie (101/201)
- **algoritmos_por_tipo.png**: Comparación de algoritmos agrupados por tipo de instancia (C/R/RC)
- **ranking_algoritmos.png**: Ranking de algoritmos basado en rendimiento
- **tiempo_por_algoritmo.png**: Comparación de tiempos de ejecución
- **variabilidad_por_algoritmo.png**: Comparación de estabilidad (desviación estándar)
- **resumen_algoritmos.csv**: Datos de resumen en formato CSV

## Generación

Estas visualizaciones son generadas por el script `analyze_solomon_results.py` a partir de los resultados de benchmark realizados con el script `run_full_solomon_benchmark.py`.