# Reporte de Inventario del Repositorio

## Análisis completo de archivos, dependencias y cobertura

## Tiempos de iteración

El benchmarking ahora incluye medición automática de tiempos por iteración para cada algoritmo:

- La columna `avg_iter_time` en `massive_benchmark_summary.csv` contiene el tiempo promedio por iteración
- Los tiempos se miden y propagan automáticamente durante las ejecuciones
- Permite comparación precisa del rendimiento computacional de los algoritmos

## Resumen General

- **Total de archivos:** 123
- **Archivos Python:** 61
- **Líneas de código Python:** 16358
- **Módulos:** 62

## Módulos y quién los importa

| Módulo | Importado por | Número de referencias |
|--------|--------------|------------------------|
| problems/vrp.py | tests/test_algorithms_regression.py, tests/test_vrp_operators_split.py, tests/test_vrp_penalties.py, tests/test_vrp_parser.py, tests/test_algorithms_convergence.py y 6 más | 11 |
| algorithms/base.py | algorithms/gvoa.py, algorithms/opa.py, algorithms/smo.py, algorithms/aha.py, tests/test_hoa.py y 1 más | 6 |
| algorithms/opa.py | tests/test_cli_run.py, scripts/run_massive.py, scripts/run.py, scripts/run_opa_experiment.py, scripts/analyze.py | 5 |
| algorithms/sho.py | tests/test_cli_run.py, utils/benchmarking.py, scripts/run_massive.py, scripts/run.py, scripts/analyze.py | 5 |
| utils/__init__.py | tests/test_vrp_operators_split.py, tests/test_utils_operators.py, tests/test_operators_complete.py, utils/improved/iteration_timer.py | 4 |
| algorithms/foa.py | utils/benchmarking.py, scripts/run_massive.py, scripts/run.py, scripts/analyze.py | 4 |
| utils/improved/timing.py | tests/test_timing.py, utils/improved/enhanced_benchmarking.py, scripts/run_massive.py | 3 |
| utils/vrp_operators.py | tests/test_vrp_operators_split.py, tests/test_vrp_operators.py, scripts/analyze.py | 3 |
| scripts/run.py | tests/test_cli_run.py, tests/test_cli.py, scripts/analyze.py | 3 |
| utils/improved/enhanced_benchmarking.py | utils/improved/iteration_timer.py, scripts/run_massive.py, scripts/analyze.py | 3 |
| algorithms/aha.py | scripts/run_massive.py, scripts/run.py, scripts/analyze.py | 3 |
| algorithms/apo.py | scripts/run_massive.py, scripts/run.py, scripts/analyze.py | 3 |
| algorithms/egto.py | scripts/run_massive.py, scripts/run.py, scripts/analyze.py | 3 |
| algorithms/ewa.py | scripts/run_massive.py, scripts/run.py, scripts/analyze.py | 3 |
| algorithms/fsa.py | scripts/run_massive.py, scripts/run.py, scripts/analyze.py | 3 |
| algorithms/gto.py | scripts/run_massive.py, scripts/run.py, scripts/analyze.py | 3 |
| algorithms/gvoa.py | scripts/run_massive.py, scripts/run.py, scripts/analyze.py | 3 |
| algorithms/hho.py | scripts/run_massive.py, scripts/run.py, scripts/analyze.py | 3 |
| algorithms/mrfo.py | scripts/run_massive.py, scripts/run.py, scripts/analyze.py | 3 |
| algorithms/rro.py | scripts/run_massive.py, scripts/run.py, scripts/analyze.py | 3 |
| algorithms/sma.py | scripts/run_massive.py, scripts/run.py, scripts/analyze.py | 3 |
| algorithms/smo.py | scripts/run_massive.py, scripts/run.py, scripts/analyze.py | 3 |
| algorithms/woa.py | scripts/run_massive.py, scripts/run.py, scripts/analyze.py | 3 |
| utils/visualization.py | tests/test_visualization.py, scripts/run.py | 2 |
| utils/operators.py | tests/test_utils_operators.py, tests/test_operators_complete.py | 2 |
| utils/statistical_analysis.py | utils/modify_statistical_analysis.py, scripts/analyze.py | 2 |
| utils/improved/advanced_visualization.py | utils/improved/enhanced_statistics.py, scripts/analyze.py | 2 |
| utils/benchmarking.py | utils/improved/enhanced_benchmarking.py, scripts/analyze.py | 2 |
| algorithms/hoa.py | tests/test_hoa.py | 1 |
| algorithms/fgo.py | tests/test_fgo.py | 1 |
| utils/fixed_method.py | utils/modify_statistical_analysis.py | 1 |
| scripts/run_massive.py | scripts/analyze.py | 1 |
| utils/improved/enhanced_statistics.py | scripts/analyze.py | 1 |

## Archivos huérfanos (no referenciados)

| Archivo | Tamaño (bytes) | Líneas |
|---------|----------------|--------|
| utils/statistical_analysis.py | 68697 | 1822 |
| utils/improved/advanced_visualization.py | 26538 | 837 |
| utils/fixed_method.py | 20130 | 540 |
| scripts/inventory.py | 14864 | 395 |
| utils/html_generator.py | 9163 | 262 |
| utils/improved/timing.py | 6230 | 206 |
| utils/vrp_operators.py | 5408 | 173 |
| utils/operators.py | 3478 | 108 |
| utils/visualization.py | 2964 | 108 |
| setup.py | 1209 | 39 |
| utils/improved/__init__.py | 212 | 5 |
| problems/__init__.py | 18 | 1 |
| utils/__init__.py | 15 | 1 |

## Archivos de datos y su uso

| Archivo de datos | Usado por | Número de usos |
|------------------|-----------|----------------|
| data/vrp/P-n16-k8.vrp | tests/test_algorithms_regression.py, tests/test_vrp_penalties.py, tests/test_vrp_parser.py, tests/test_vrp_operators.py, tests/test_cli.py | 5 |
| data/vrp/E-n22-k4.vrp | tests/test_algorithms_regression.py, tests/test_vrp_parser.py | 2 |
| data/vrp/E-n51-k5.vrp | tests/test_algorithms_regression.py, tests/test_vrp_parser.py | 2 |
| data/vrp/A-n32-k5.vrp | tests/test_algorithms_regression.py | 1 |
| data/vrp/B-n31-k5.vrp | tests/test_algorithms_regression.py | 1 |
| data/vrp/Solomon/R101.vrp | tests/test_algorithms_convergence.py | 1 |
| data/vrp/Solomon/RC101.vrp | tests/test_algorithms_convergence.py | 1 |
| data/vrp/Solomon/C101.vrp | tests/test_algorithms_convergence.py | 1 |
