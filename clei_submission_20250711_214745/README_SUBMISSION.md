# CLEI 2025 - Quick-HO Submission Package

## Título
Quick-HO: Optimizador Hippopotamus para Ruteo Dinámico en Quick Commerce

## Autores
[Por completar]

## Contenido del Paquete

### 1. Documento Principal
- `paper_clei2025.pdf`: Artículo completo (8 páginas, formato IEEE)
- `paper_clei2025.tex`: Código fuente LaTeX

### 2. Tablas y Figuras
- `tables/`: Tablas en formato LaTeX con booktabs/siunitx
  - `performance_summary.tex`: Comparación de rendimiento
  - `wilcoxon_test.tex`: Tests estadísticos
  - `multiobjective_metrics.tex`: Métricas QC-DVRP
- `figures/`: Visualizaciones en PDF
  - `convergence_boxplots.pdf`: Análisis de convergencia
  - `pareto_fronts.pdf`: Frentes de Pareto

### 3. Análisis de Sensibilidad
- `sensitivity_analysis/`: Resultados del análisis paramétrico
  - `parameter_sensitivity.pdf`: Efectos de α, β, γ
  - `parameter_heatmap.pdf`: Interacción de parámetros
  - `sensitivity_results.csv`: Datos completos

### 4. Documentación Técnica
- `informe_tecnico.md`: Informe detallado en Markdown
- `generation.log`: Log de generación

## Resultados Principales

- **Algoritmo ganador**: HO (Hippopotamus Optimizer)
- **Mejora sobre baseline**: 15-20% en costo promedio
- **Balance de carga**: < 0.2 (objetivo cumplido)
- **Entregas a tiempo**: Requiere ajuste de parámetros

## Reproducibilidad

Todos los experimentos utilizan semilla fija (42) y están documentados para reproducibilidad completa.

## Referencias Clave

1. Amiri, M. H., et al. (2024). "Hippopotamus optimization algorithm". Scientific Reports 14, 5032.
2. Potvin, J. Y. (2009). "State-of-the-art review—evolutionary algorithms for vehicle routing". INFORMS Journal on Computing, 21(4), 518-548.

## Contacto
[Email de contacto]
