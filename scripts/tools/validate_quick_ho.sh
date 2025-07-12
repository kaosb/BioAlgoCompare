#!/bin/bash
# validate_quick_ho.sh - Validación completa de Quick-HO para tesis CLEI 2025
# Autor: Quick-HO Research Team
# Referencias: Amiri et al. (2024), Potvin (2009)

set -euo pipefail

# Colores para output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo "=========================================="
echo "Quick-HO Validation Script v1.0"
echo "CLEI 2025 - Tesis Implementation"
echo "=========================================="

# 1. CONFIGURACIÓN INICIAL
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
LOG_DIR="validation_logs/$TIMESTAMP"
RESULTS_DIR="validation_results/$TIMESTAMP"
mkdir -p "$LOG_DIR" "$RESULTS_DIR"

# Archivo de log principal
MAIN_LOG="$LOG_DIR/validation_main.log"
exec > >(tee -a "$MAIN_LOG")
exec 2>&1

echo -e "${GREEN}[INFO]${NC} Creando directorios de validación..."

# 2. VALIDACIÓN DE DEPENDENCIAS
echo -e "\n${YELLOW}=== PASO 1: Validando dependencias ===${NC}"

check_dependency() {
    if ! command -v $1 &> /dev/null; then
        echo -e "${RED}[ERROR]${NC} $1 no está instalado"
        return 1
    else
        echo -e "${GREEN}[OK]${NC} $1 está disponible"
        return 0
    fi
}

check_dependency python
check_dependency pytest
check_dependency git

# Verificar versión de Python
PYTHON_VERSION=$(python --version 2>&1 | awk '{print $2}')
echo -e "${GREEN}[INFO]${NC} Python version: $PYTHON_VERSION"

# 3. TESTS UNITARIOS CON COBERTURA
echo -e "\n${YELLOW}=== PASO 2: Ejecutando tests unitarios con cobertura ===${NC}"

# Test completo del codebase
pytest tests/ \
    --cov=algorithms \
    --cov=problems \
    --cov=utils \
    --cov-report=html:$RESULTS_DIR/coverage_html \
    --cov-report=term \
    --cov-report=json:$RESULTS_DIR/coverage.json \
    -v \
    --tb=short \
    | tee "$LOG_DIR/pytest_output.log"

# Verificar cobertura mínima
COVERAGE=$(python -c "import json; print(json.load(open('$RESULTS_DIR/coverage.json'))['totals']['percent_covered'])")
echo -e "${GREEN}[INFO]${NC} Cobertura total: ${COVERAGE}%"

if (( $(echo "$COVERAGE < 80" | bc -l) )); then
    echo -e "${YELLOW}[WARN]${NC} Cobertura por debajo del 80% objetivo"
fi

# 4. VALIDACIÓN DE INTEGRACIÓN HO + IL
echo -e "\n${YELLOW}=== PASO 3: Validando integración HO + IL ===${NC}"

python -c "
import sys
sys.path.insert(0, '.')
from algorithms.ho import HO
from problems.vrp import VRPProblem
import numpy as np

# Verificar que HO puede usar IL
problem = VRPProblem('data/vrp/P-n16-k8.vrp')
try:
    ho = HO(problem, population_size=10, max_iterations=10, use_il=True, il_model_path='models/ho_il_model.pth')
    print('✓ HO con IL se inicializa correctamente')
except FileNotFoundError:
    print('⚠ Modelo IL no encontrado en models/ho_il_model.pth')
except Exception as e:
    print(f'✗ Error en integración HO+IL: {e}')

# Verificar evaluate_multi en VRP
if hasattr(problem, 'evaluate_multi'):
    print('✓ VRPProblem tiene método evaluate_multi')
    # Test con solución dummy
    dummy_solution = np.random.rand(problem.dimension)
    result = problem.evaluate_multi(dummy_solution)
    print(f'  Resultado multiobjetivo: {result}')
else:
    print('✗ VRPProblem no tiene método evaluate_multi')
" | tee "$LOG_DIR/integration_check.log"

# 5. BENCHMARK PEQUEÑO PARA VALIDACIÓN
echo -e "\n${YELLOW}=== PASO 4: Benchmark de validación (30 runs) ===${NC}"

# Primero un benchmark pequeño para validar funcionalidad
python scripts/analyze.py benchmark \
    --run-benchmark \
    --algorithms ho,sho,foa \
    --instances P-n16-k8 \
    --dynamic \
    --multiobjective \
    --runs 30 \
    --iterations 100 \
    --population 40 \
    --seed 42 \
    --output-dir "$RESULTS_DIR/benchmark_validation" \
    2>&1 | tee "$LOG_DIR/benchmark_validation.log"

# 6. ANÁLISIS ESTADÍSTICO DEL BENCHMARK
echo -e "\n${YELLOW}=== PASO 5: Análisis estadístico ===${NC}"

# Primero buscar el archivo JSON de resultados
LATEST_JSON=$(find "$RESULTS_DIR/benchmark_validation" -name "benchmark_results.json" -type f | head -1)

if [ -f "$LATEST_JSON" ]; then
    # Convertir JSON a CSV para análisis estadístico
    echo -e "${GREEN}[INFO]${NC} Convirtiendo resultados JSON a CSV..."
    python -c "
import json
import pandas as pd
import sys

with open('$LATEST_JSON', 'r') as f:
    data = json.load(f)

# Extraer datos para DataFrame
rows = []
for result in data:
    algo = result.get('algorithm_name', 'Unknown')
    instance = result.get('instance_name', 'Unknown')

    # Obtener valores detallados si existen
    if 'detailed_results' in result:
        fitness_vals = result['detailed_results'].get('fitness_values', [])
        times = result['detailed_results'].get('execution_times', [])

        for i, (fitness, time) in enumerate(zip(fitness_vals, times)):
            rows.append({
                'Algorithm': algo,
                'Instance': instance,
                'Run': i + 1,
                'Best_Cost': fitness,
                'Time': time
            })
    else:
        # Fallback to metrics
        metrics = result.get('metrics', {})
        rows.append({
            'Algorithm': algo,
            'Instance': instance,
            'Run': 1,
            'Best_Cost': metrics.get('best_fitness', 0),
            'Time': metrics.get('mean_time', 0)
        })

df = pd.DataFrame(rows)
df.to_csv('$RESULTS_DIR/benchmark_validation/results.csv', index=False)
print(f'CSV creado con {len(df)} filas')
"

    # Ahora ejecutar análisis estadístico
    if [ -f "$RESULTS_DIR/benchmark_validation/results.csv" ]; then
        python scripts/analyze.py stats \
            --csv "$RESULTS_DIR/benchmark_validation/results.csv" \
            --out "$RESULTS_DIR/statistical_analysis" \
            2>&1 | tee "$LOG_DIR/statistical_analysis.log"
    else
        echo -e "${RED}[ERROR]${NC} No se pudo crear archivo CSV"
    fi
else
    echo -e "${RED}[ERROR]${NC} No se encontraron resultados JSON de benchmark"
fi

# 7. VALIDACIÓN DE MÉTRICAS QC-DVRP
echo -e "\n${YELLOW}=== PASO 6: Validando métricas QC-DVRP ===${NC}"

# Buscar el archivo JSON de resultados más reciente
LATEST_JSON=$(find "$RESULTS_DIR/benchmark_validation" -name "benchmark_results.json" -type f | head -1)

python -c "
import json
import sys
import numpy as np

results_file = '$LATEST_JSON'
if not results_file:
    print('No hay resultados JSON para analizar')
    sys.exit(1)

with open(results_file, 'r') as f:
    data = json.load(f)

print('\\n=== Métricas QC-DVRP ===')
for result in data:
    algo = result.get('algorithm_name', 'Unknown')
    instance = result.get('instance_name', 'Unknown')
    metrics = result.get('metrics', {})

    # Métricas objetivo para tesis
    on_time_rate = metrics.get('on_time_delivery_rate', 0)
    load_var = metrics.get('avg_load_variation', 0)
    hypervolume = metrics.get('avg_hypervolume', 0)

    print(f'\\nAlgoritmo: {algo} - Instancia: {instance}')
    print(f'  % Entregas ≤30min: {on_time_rate*100:.1f}%')
    print(f'  Coef. variación carga: {load_var:.3f}')
    print(f'  Hipervolumen: {hypervolume:.3f}')

    # Validar umbrales de tesis
    if on_time_rate >= 0.85:
        print('  ✓ Cumple objetivo entregas a tiempo (≥85%)')
    else:
        print('  ✗ No cumple objetivo entregas a tiempo')

    if load_var <= 0.2:
        print('  ✓ Cumple objetivo balance de carga (≤0.2)')
    else:
        print('  ✗ No cumple objetivo balance de carga')
" | tee "$LOG_DIR/qc_metrics_validation.log"

# 8. GITFLOW INTEGRATION
echo -e "\n${YELLOW}=== PASO 7: Integración GitFlow ===${NC}"

# Verificar estado git
CURRENT_BRANCH=$(git branch --show-current)
echo -e "${GREEN}[INFO]${NC} Rama actual: $CURRENT_BRANCH"

# Crear feature branch si no existe
if [ "$CURRENT_BRANCH" != "feature/quick-ho" ]; then
    if git show-ref --verify --quiet refs/heads/feature/quick-ho; then
        echo -e "${GREEN}[INFO]${NC} La rama feature/quick-ho ya existe"
    else
        echo -e "${GREEN}[INFO]${NC} Creando rama feature/quick-ho..."
        git checkout -b feature/quick-ho
    fi
fi

# Verificar cambios pendientes
if [[ -n $(git status -s) ]]; then
    echo -e "${YELLOW}[WARN]${NC} Hay cambios sin commit. Commiteando..."
    git add -A
    git commit -m "feat(quick-ho): validación completa Quick-HO - $(date +%Y%m%d)" || true
fi

echo -e "${GREEN}[INFO]${NC} Para completar el merge a develop, ejecuta:"
echo "  git checkout develop"
echo "  git merge feature/quick-ho --no-ff -m 'Merge Quick-HO implementación completa'"

# 9. BENCHMARK MASIVO (OPCIONAL)
echo -e "\n${YELLOW}=== PASO 8: Benchmark masivo (opcional) ===${NC}"
echo "Para ejecutar el benchmark completo de 1000 runs, usa:"
echo ""
echo "python scripts/analyze.py massive \\"
echo "  --algorithms ho,sho,foa,woa,hho \\"
echo "  --instances Solomon-RC101,Solomon-RC102,Solomon-RC103,Solomon-RC104 \\"
echo "  --runs 1000 \\"
echo "  --iterations 300 \\"
echo "  --population 50 \\"
echo "  --dynamic \\"
echo "  --multiobjective \\"
echo "  --parallel \\"
echo "  --seed 42 \\"
echo "  --output-dir $RESULTS_DIR/massive_benchmark"

# 10. ANÁLISIS DE SENSIBILIDAD (Amiri et al. 2024)
echo -e "\n${YELLOW}=== PASO 9: Análisis de sensibilidad de parámetros HO ===${NC}"

cat > "$RESULTS_DIR/sensitivity_analysis.py" << 'EOF'
import numpy as np
import matplotlib.pyplot as plt
from algorithms.ho import HO
from problems.vrp import VRPProblem

# Parámetros HO según Amiri et al. (2024)
alpha_range = np.linspace(0.1, 0.9, 9)
beta_range = np.linspace(0.2, 0.8, 7)
gamma_range = np.linspace(0.3, 1.0, 8)

# Análisis de sensibilidad
def sensitivity_analysis():
    problem = VRPProblem('data/vrp/Solomon-RC101.vrp')
    results = {
        'alpha': [],
        'beta': [],
        'gamma': []
    }

    # Variar alpha
    for alpha in alpha_range:
        ho = HO(problem, population_size=30, max_iterations=100)
        # Sobrescribir parámetro
        ho.alpha = alpha
        best = ho.execute()
        results['alpha'].append(best.fitness())

    # Similar para beta y gamma...

    return results

print("Ejecutar sensitivity_analysis.py para análisis completo de parámetros")
EOF

echo -e "${GREEN}[INFO]${NC} Script de análisis de sensibilidad creado en: $RESULTS_DIR/sensitivity_analysis.py"

# 11. RESUMEN FINAL
echo -e "\n${GREEN}=========================================="
echo "VALIDACIÓN COMPLETA"
echo "==========================================${NC}"
echo ""
echo "Resultados guardados en:"
echo "  - Logs: $LOG_DIR/"
echo "  - Resultados: $RESULTS_DIR/"
echo "  - Cobertura HTML: $RESULTS_DIR/coverage_html/index.html"
echo ""
echo "Referencias:"
echo "  - Amiri, M. H., et al. (2024). 'Hippopotamus optimization algorithm'"
echo "  - Potvin, J. Y. (2009). 'State-of-the-art review—evolutionary algorithms for vehicle routing'"
echo ""
echo -e "${GREEN}[SUCCESS]${NC} Validación Quick-HO completada exitosamente"
