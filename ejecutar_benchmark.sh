#!/bin/bash

# ==========================================
# Configuración de variables
# ==========================================
RESULTS_DIR="results"
FECHA="20250515"

# ==========================================
# Limpieza de resultados anteriores
# ==========================================
echo "Limpiando resultados anteriores..."
rm -rf results/massive_benchmark_${FECHA}*

# ==========================================
# Ejecución de pruebas de benchmarking
# ==========================================
echo "Iniciando pruebas de benchmarking..."

# Lista de algoritmos a probar
ALGORITHMS=("hoa" "sho" "apo" "egto" "fgo" "fsa" "foa" "woa" "hho" "mrfo" "sma" "gto" "ewa")

# Ejecutar pruebas para cada algoritmo
for algo in "${ALGORITHMS[@]}"; do
    echo "Ejecutando pruebas para algoritmo: $algo"
    PYTHONPATH=./ python scripts/run_massive.py \
        --instances "E-n22-k4" \
        --algorithm "$algo" \
        --runs 100 \
        --iterations 1000 \
        --population 100 \
        --parallel \
        --seed $(shuf -i 1-10000 -n 1)
done

# ==========================================
# Visualización de reportes
# ==========================================
echo "Abriendo reportes generados..."

# Buscar y abrir cada archivo HTML generado
find "$RESULTS_DIR" -type f -path "*massive_benchmark_${FECHA}_*/massive_benchmark_report.html" | while read -r report; do
    echo "Abriendo reporte: $report"
    open "$report"
done

echo "Proceso completado."
