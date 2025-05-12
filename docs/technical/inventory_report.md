# Reporte de Inventario del Repositorio

## Análisis completo de archivos, dependencias y cobertura

## Resumen General

- **Total de archivos:** 100
- **Archivos Python:** 45
- **Líneas de código Python:** 18000
- **Módulos:** 45

## Módulos y quién los importa

| Módulo | Importado por | Número de referencias |
|--------|--------------|------------------------|
| problems/vrp.py | debug_opa.py, test_opa.py, tests/test_algorithms_regression.py, tests/test_vrp_parser.py, tests/test_vrp_operators.py y 7 más | 12 |
| algorithms/opa.py | debug_opa.py, test_opa.py, scripts/run_massive.py, scripts/run.py, scripts/run_opa_experiment.py y 1 más | 6 |
| algorithms/foa.py | utils/benchmarking.py, scripts/run_massive.py, scripts/run.py, scripts/analyze.py | 4 |
| algorithms/sho.py | utils/benchmarking.py, scripts/run_massive.py, scripts/run.py, scripts/analyze.py | 4 |
| algorithms/base.py | algorithms/gvoa.py, algorithms/opa.py, algorithms/smo.py, algorithms/aha.py | 4 |
| utils/statistical_analysis.py | utils/modify_statistical_analysis.py, scripts/analyze.py | 2 |
| utils/improved/advanced_visualization.py | utils/improved/enhanced_statistics.py, scripts/analyze.py | 2 |
| utils/benchmarking.py | utils/improved/enhanced_benchmarking.py, scripts/analyze.py | 2 |
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
| utils/vrp_operators.py | tests/test_vrp_operators.py, scripts/analyze.py | 2 |
| scripts/run.py | tests/test_cli.py, scripts/analyze.py | 2 |
| utils/fixed_method.py | utils/modify_statistical_analysis.py | 1 |
| utils/improved/enhanced_benchmarking.py | scripts/run_massive.py, scripts/analyze.py | 2 |
| utils/visualization.py | scripts/run.py | 1 |
| scripts/run_massive.py | scripts/analyze.py | 1 |
| utils/improved/enhanced_statistics.py | scripts/analyze.py | 1 |

## Archivos huérfanos (no referenciados)

| Archivo | Tamaño (bytes) | Líneas |
|---------|----------------|--------|
| utils/statistical_analysis.py | 69062 | 1830 |
| utils/vrp_operators.py | 54795 | 1560 |
| utils/improved/advanced_visualization.py | 26564 | 837 |
| utils/fixed_method.py | 20166 | 540 |
| scripts/inventory.py | 14856 | 348 |
| utils/html_generator.py | 9163 | 262 |
| utils/visualization.py | 2964 | 108 |
| utils/operators.py | 2698 | 98 |
| setup.py | 1209 | 39 |

## Archivos de datos y su uso

| Archivo de datos | Usado por | Número de usos |
|------------------|-----------|----------------|
| data/vrp/P-n16-k8.vrp | debug_opa.py, tests/test_algorithms_regression.py, tests/test_vrp_parser.py, tests/test_vrp_operators.py, tests/test_cli.py | 5 |
| data/vrp/E-n22-k4.vrp | test_opa.py, tests/test_algorithms_regression.py, tests/test_vrp_parser.py | 3 |
| data/vrp/E-n51-k5.vrp | tests/test_algorithms_regression.py, tests/test_vrp_parser.py | 2 |
| data/vrp/A-n32-k5.vrp | tests/test_algorithms_regression.py | 1 |
| data/vrp/B-n31-k5.vrp | tests/test_algorithms_regression.py | 1 |