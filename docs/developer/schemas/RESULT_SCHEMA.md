# Esquema Estandarizado de Resultados

## Introducción

El esquema estandarizado de resultados de BioAlgoCompare proporciona una estructura consistente, completa y profesional para todos los resultados experimentales. Este esquema facilita el análisis, la publicación y el intercambio de resultados entre investigadores.

## Características Principales

### 1. Estructura Unificada
- Formato consistente para todos los experimentos
- Información completa del problema, algoritmo y ejecución
- Estadísticas calculadas automáticamente
- Metadatos extensivos para reproducibilidad

### 2. Múltiples Formatos de Exportación
- **JSON**: Datos completos estructurados
- **CSV**: Tablas para análisis en hojas de cálculo
- **LaTeX**: Tablas formateadas para publicaciones
- **HTML**: Reportes interactivos con visualizaciones

### 3. Compatibilidad Bidireccional
- Integración transparente con el sistema de tracking existente
- Conversión automática entre formatos
- Migración de resultados legacy

## Estructura del Esquema

### StandardResult
```python
@dataclass
class StandardResult:
    result_id: str                    # Identificador único
    result_type: ResultType           # SINGLE_RUN, MULTI_RUN, etc.
    timestamp: datetime               # Marca de tiempo
    problem_info: ProblemInfo         # Información del problema
    algorithm_info: AlgorithmInfo     # Información del algoritmo
    execution_info: ExecutionInfo     # Información de ejecución
    runs: List[SingleRunResult]       # Resultados individuales
    statistics: MultiRunStatistics    # Estadísticas consolidadas
    metadata: Dict[str, Any]          # Metadatos adicionales
```

### ProblemInfo
```python
@dataclass
class ProblemInfo:
    name: str                         # Nombre de la instancia
    type: str = "VRP"                # Tipo de problema
    dimension: int                    # Tamaño del problema
    optimal_value: Optional[float]    # Valor óptimo conocido
    instance_file: Optional[str]      # Archivo de instancia
    constraints: Dict[str, Any]       # Restricciones
    metadata: Dict[str, Any]          # Metadatos adicionales
```

### AlgorithmInfo
```python
@dataclass
class AlgorithmInfo:
    name: str                         # Nombre del algoritmo
    version: str = "v2"              # Versión
    population_size: int              # Tamaño de población
    max_iterations: int               # Iteraciones máximas
    parameters: Dict[str, Any]        # Parámetros específicos
    seed: Optional[int]               # Semilla aleatoria
```

### ExecutionInfo
```python
@dataclass
class ExecutionInfo:
    start_time: datetime              # Tiempo de inicio
    end_time: datetime                # Tiempo de fin
    duration_seconds: float           # Duración total
    platform: str                     # Sistema operativo
    python_version: str               # Versión de Python
    cpu_count: int                    # Número de CPUs
    memory_gb: float                  # Memoria RAM
    parallel: bool = False            # Ejecución paralela
    n_workers: Optional[int]          # Número de workers
```

### SingleRunResult
```python
@dataclass
class SingleRunResult:
    run_id: int                       # ID de la ejecución
    seed: int                         # Semilla utilizada
    best_fitness: float               # Mejor fitness
    best_solution: Any                # Mejor solución
    convergence_curve: List[float]    # Curva de convergencia
    execution_time: float             # Tiempo de ejecución
    iterations_completed: int         # Iteraciones completadas
    evaluations: int                  # Evaluaciones realizadas
    final_population_fitness: Optional[List[float]]  # Fitness final
    diversity_metrics: Optional[Dict[str, float]]    # Métricas de diversidad
    custom_metrics: Dict[str, Any]    # Métricas personalizadas
```

### MultiRunStatistics
```python
@dataclass
class MultiRunStatistics:
    n_runs: int                       # Número de ejecuciones
    best_fitness: float               # Mejor fitness
    worst_fitness: float              # Peor fitness
    mean_fitness: float               # Media
    std_fitness: float                # Desviación estándar
    median_fitness: float             # Mediana
    q1_fitness: float                 # Primer cuartil
    q3_fitness: float                 # Tercer cuartil
    iqr_fitness: float                # Rango intercuartílico
    cv_fitness: float                 # Coeficiente de variación
    success_rate: float               # Tasa de éxito
    mean_convergence_rate: float      # Tasa de convergencia media
    mean_execution_time: float        # Tiempo medio
    total_execution_time: float       # Tiempo total
    confidence_interval_95: Tuple[float, float]  # IC 95%
```

## Uso Básico

### 1. Crear un Resultado Simple

```python
from utils.result_schema import ResultBuilder

# Después de ejecutar un algoritmo
result = ResultBuilder.create_single_run(
    algorithm_name="woa",
    problem_name="P-n16-k8",
    run_result=best_individual,
    execution_time=5.67,
    dimension=15,
    optimal_value=450.0,
    population_size=30,
    max_iterations=100,
    convergence_curve=convergence_history,
    seed=42
)

# Guardar
result.to_json("results/woa_experiment.json")
```

### 2. Crear un Resultado Multi-Run

```python
# Recopilar resultados de múltiples ejecuciones
run_results = []
for i in range(30):
    # Ejecutar algoritmo...
    run_results.append({
        'best_fitness': best.fitness(),
        'best_solution': best.position,
        'convergence_curve': convergence,
        'execution_time': elapsed_time,
        'seed': 42 + i
    })

# Crear resultado consolidado
multi_result = ResultBuilder.create_multi_run(
    algorithm_name="sma",
    problem_name="E-n22-k4",
    run_results=run_results,
    dimension=21,
    optimal_value=375.0,
    population_size=50,
    max_iterations=200,
    parallel=True,
    n_workers=4
)
```

### 3. Exportar en Diferentes Formatos

```python
# JSON completo
result.to_json("result.json")

# CSV para análisis
df = result.to_dataframe()
df.to_csv("result_summary.csv")

# Curvas de convergencia
result.export_convergence_curves("convergence.csv")

# HTML con visualizaciones (requiere integración con tracker)
tracker.export_experiment(result.result_id, 'html')
```

## Integración con Sistema de Tracking

### 1. Conversión Automática

```python
from utils.result_integration import ResultIntegration

# De ExperimentRecord a StandardResult
standard_result = ResultIntegration.experiment_to_standard(experiment_record)

# De StandardResult a ExperimentRecord
experiment_record = ResultIntegration.standard_to_experiment(standard_result)
```

### 2. Decorador para Trackers

```python
from utils.result_integration import integrate_with_tracker

@integrate_with_tracker
class MyTracker(ExperimentTracker):
    pass

# El tracker ahora guarda automáticamente en ambos formatos
tracker = MyTracker()
```

### 3. Migración de Resultados Legacy

```python
from utils.result_integration import ResultIntegration

# Migrar archivos legacy
migrated_ids = ResultIntegration.migrate_legacy_results(
    legacy_path="old_results/",
    output_dir="migrated_results/"
)

print(f"Migrados {len(migrated_ids)} resultados")
```

## Scripts con Esquema Estandarizado

### Script run_with_schema.py

```bash
# Ejecutar con esquema estándar
python scripts/core/run_with_schema.py \
    -a woa -i P-n16-k8 \
    --standard \
    --export-formats json csv html latex

# Múltiples runs con exportación completa
python scripts/core/run_with_schema.py \
    -a sma -i E-n22-k4 \
    -r 30 \
    --parallel \
    --export-formats all
```

## Validación de Resultados

```python
from utils.result_schema import validate_result

# Validar un resultado
errors = validate_result(result)
if errors:
    print("Errores encontrados:")
    for error in errors:
        print(f"  - {error}")
else:
    print("Resultado válido")
```

## Comparación de Resultados

```python
from utils.result_schema import ComparisonResult

# Crear comparación entre algoritmos
comparison = ComparisonResult(
    comparison_id="algorithm_comparison",
    timestamp=datetime.now(),
    problem_info=problem_info,
    algorithms=[woa_info, sma_info, gto_info],
    results=[woa_result, sma_result, gto_result],
    statistical_tests={
        "kruskal_wallis": {"statistic": 12.5, "p_value": 0.002}
    }
)

# Obtener tabla resumen
summary = comparison.get_summary_table()
print(summary)
```

## Análisis de Resultados

### 1. Cargar y Analizar

```python
# Cargar resultado
result = StandardResult.from_json("results/experiment.json")

# Información básica
print(f"Algoritmo: {result.algorithm_info.name}")
print(f"Mejor fitness: {result.statistics.best_fitness}")
print(f"Media ± std: {result.statistics.mean_fitness} ± {result.statistics.std_fitness}")

# Gap al óptimo
gap = result.get_gap_to_optimal()
if gap is not None:
    print(f"Gap al óptimo: {gap:.2f}%")
```

### 2. Análisis Estadístico

```python
# Intervalo de confianza
ci_lower, ci_upper = result.statistics.confidence_interval_95
print(f"IC 95%: [{ci_lower:.2f}, {ci_upper:.2f}]")

# Coeficiente de variación
print(f"CV: {result.statistics.cv_fitness:.3f}")

# Tasa de convergencia media
print(f"Convergencia: {result.statistics.mean_convergence_rate:.3f}")
```

### 3. Visualización

```python
import matplotlib.pyplot as plt
import pandas as pd

# Cargar curvas de convergencia
curves_df = pd.read_csv("convergence.csv", index_col=0)

# Graficar
plt.figure(figsize=(10, 6))
for col in curves_df.columns:
    plt.plot(curves_df.index, curves_df[col], alpha=0.5)
plt.xlabel("Iteración")
plt.ylabel("Fitness")
plt.title("Curvas de Convergencia")
plt.show()
```

## Mejores Prácticas

### 1. Siempre Incluir Información Completa
```python
# ✅ Bueno
result = ResultBuilder.create_single_run(
    algorithm_name="woa",
    problem_name="P-n16-k8",
    run_result=best,
    execution_time=5.67,
    dimension=15,
    optimal_value=450.0,  # Incluir si se conoce
    convergence_curve=history,  # Incluir siempre
    seed=42  # Para reproducibilidad
)

# ❌ Evitar
result = ResultBuilder.create_single_run(
    algorithm_name="woa",
    problem_name="P-n16-k8",
    run_result=best,
    execution_time=5.67
    # Faltan datos importantes
)
```

### 2. Usar Métricas Personalizadas para VRP
```python
# Añadir métricas específicas de VRP
result.runs[0].custom_metrics = {
    'n_vehicles': len(routes),
    'avg_route_length': np.mean([len(r) for r in routes]),
    'route_balance': np.std([len(r) for r in routes]),
    'capacity_utilization': total_demand / (n_vehicles * capacity)
}
```

### 3. Documentar Metadatos
```python
# Incluir contexto experimental
result.metadata.update({
    'experiment_purpose': 'Parameter tuning for population size',
    'hardware': 'GPU Tesla V100',
    'notes': 'Run with modified selection operator'
})
```

## Ejemplos Completos

### Experimento de Comparación de Algoritmos

```python
from utils.result_schema import ResultBuilder, StandardResult
import numpy as np

# Ejecutar múltiples algoritmos
algorithms = ['woa', 'sma', 'gto']
all_results = []

for algo in algorithms:
    # 30 runs por algoritmo
    run_results = []
    
    for seed in range(30):
        # Ejecutar algoritmo...
        # ...
        
        run_results.append({
            'best_fitness': fitness,
            'best_solution': solution,
            'convergence_curve': convergence,
            'execution_time': time,
            'seed': seed
        })
    
    # Crear resultado del algoritmo
    result = ResultBuilder.create_multi_run(
        algorithm_name=algo,
        problem_name="P-n16-k8",
        run_results=run_results,
        dimension=15,
        optimal_value=450.0
    )
    
    all_results.append(result)
    
    # Guardar resultado individual
    result.to_json(f"results/{algo}_P-n16-k8.json")

# Análisis comparativo
print("\nComparación de Algoritmos:")
print("-" * 60)
for result in all_results:
    stats = result.statistics
    gap = result.get_gap_to_optimal()
    print(f"{result.algorithm_info.name:10s}: "
          f"Best={stats.best_fitness:7.2f}, "
          f"Mean={stats.mean_fitness:7.2f}±{stats.std_fitness:5.2f}, "
          f"Gap={gap:5.2f}%")
```

## Resolución de Problemas

### Error: "Debe haber al menos un run"
```python
# Solución: Asegurarse de incluir resultados
runs = []  # ❌ Vacío
runs = [SingleRunResult(...)]  # ✅ Al menos uno
```

### Error: "Inconsistencia en estadísticas"
```python
# Las estadísticas se recalculan automáticamente
result.statistics = MultiRunStatistics.from_runs(result.runs)
```

### Migración falla
```python
# Verificar formato del archivo
with open('legacy.json', 'r') as f:
    data = json.load(f)
    print(data.keys())  # Ver estructura
```

## Conclusión

El esquema estandarizado de resultados proporciona:
- **Consistencia**: Todos los resultados siguen el mismo formato
- **Completitud**: Toda la información necesaria en un solo lugar
- **Profesionalismo**: Exportación directa para publicaciones
- **Interoperabilidad**: Fácil intercambio entre investigadores
- **Trazabilidad**: Registro completo para reproducibilidad

Úsalo en todos tus experimentos para mantener estándares profesionales y facilitar el análisis y publicación de resultados.