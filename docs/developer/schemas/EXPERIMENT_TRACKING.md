# Sistema de Registro de Experimentos

## Introducción

El sistema de registro de experimentos de BioAlgoCompare proporciona trazabilidad completa y reproducibilidad científica para todos los experimentos ejecutados. Este sistema es fundamental para mantener el rigor científico y facilitar la publicación de resultados.

## Características Principales

### 1. Registro Automático
- Captura automática de configuración, sistema y repositorio Git
- Registro de cada ejecución con semilla y resultados
- Tracking de curvas de convergencia completas
- Metadatos extensivos para reproducibilidad

### 2. Almacenamiento Estructurado
```
experiments/
├── records/          # Registros JSON completos
├── metadata/         # Metadatos de configuración
├── summaries/        # Resúmenes CSV consolidados
└── exports/          # Exportaciones en varios formatos
```

### 3. Formatos de Exportación
- **JSON**: Datos completos estructurados
- **CSV**: Tablas de resultados y convergencia
- **LaTeX**: Tablas formateadas para publicaciones
- **HTML**: Reportes interactivos con visualizaciones

## Uso Básico

### 1. Inicialización del Tracker

```python
from utils.experiment_tracker import ExperimentTracker, ExperimentConfig

# Crear tracker
tracker = ExperimentTracker(base_dir="experiments", auto_save=True)
```

### 2. Configurar y Comenzar Experimento

```python
# Configurar experimento
config = ExperimentConfig(
    algorithm="woa",
    problem_instance="P-n16-k8.vrp",
    population_size=30,
    max_iterations=100,
    algorithm_params={"a": 2.0, "b": 1.0},
    seed=42
)

# Iniciar experimento
exp_id = tracker.start_experiment(config, metadata={
    "experiment_type": "parameter_tuning",
    "objective": "minimize_fitness"
})
```

### 3. Registrar Resultados

```python
from utils.experiment_tracker import ExperimentResult

# Para cada ejecución
result = ExperimentResult(
    run_id=1,
    seed=42,
    best_fitness=123.45,
    convergence_curve=[200.0, 180.0, 160.0, 140.0, 123.45],
    execution_time=5.67,
    final_solution=best_solution,
    iterations_completed=100
)

tracker.log_result(result)
```

### 4. Exportar Resultados

```python
# Exportar en diferentes formatos
tracker.export_experiment(exp_id, format='json')    # Datos completos
tracker.export_experiment(exp_id, format='csv')     # Tablas
tracker.export_experiment(exp_id, format='latex')   # Para papers
tracker.export_experiment(exp_id, format='html')    # Reporte web
```

## Integración con Scripts

### Usando el Script con Tracker

```bash
# Ejecutar con tracking automático
python scripts/core/run_with_tracker.py -a woa -i P-n16-k8.vrp --mode standard

# Desactivar tracking
python scripts/core/run_with_tracker.py -a woa -i P-n16-k8.vrp --no-track

# Especificar directorio de experimentos
python scripts/core/run_with_tracker.py -a woa -i P-n16-k8.vrp --experiment-dir my_experiments
```

### Usando el Decorador

```python
from utils.experiment_tracker import track_experiment

@track_experiment(tracker)
def run_algorithm_experiment(config: ExperimentConfig):
    # Tu código aquí
    algorithm = WOA(...)
    best = algorithm.execute()
    
    # Retornar ExperimentResult
    return create_experiment_result(
        run_id=1,
        seed=config.seed,
        algorithm_result=best,
        execution_time=elapsed_time
    )
```

## Consulta y Análisis

### Listar Experimentos

```python
# Listar todos los experimentos
df = tracker.list_experiments()

# Filtrar por criterios
df = tracker.list_experiments(filter_criteria={
    'algorithm': 'woa',
    'instance': 'P-n16-k8.vrp'
})
```

### Comparar Experimentos

```python
# Comparar múltiples experimentos
comparison = tracker.compare_experiments([
    'woa_P-n16-k8_20240315_120000_abc123',
    'sma_P-n16-k8_20240315_130000_def456'
])
```

### Cargar Experimento Anterior

```python
# Cargar experimento guardado
record = tracker.load_experiment(experiment_id)

# Acceder a resultados
for result in record.results:
    print(f"Run {result.run_id}: {result.best_fitness}")
```

## Estructura de Datos

### ExperimentConfig
```python
@dataclass
class ExperimentConfig:
    algorithm: str              # Nombre del algoritmo
    problem_instance: str       # Instancia del problema
    population_size: int        # Tamaño de población
    max_iterations: int         # Iteraciones máximas
    algorithm_params: Dict      # Parámetros específicos
    seed: Optional[int]         # Semilla (opcional)
```

### ExperimentResult
```python
@dataclass
class ExperimentResult:
    run_id: int                 # ID de la ejecución
    seed: int                   # Semilla utilizada
    best_fitness: float         # Mejor fitness obtenido
    convergence_curve: List     # Curva de convergencia
    execution_time: float       # Tiempo de ejecución
    final_solution: Any         # Solución final
    iterations_completed: int   # Iteraciones completadas
    metadata: Dict             # Metadatos adicionales
```

### ExperimentRecord
```python
@dataclass
class ExperimentRecord:
    experiment_id: str          # ID único del experimento
    timestamp: str              # Marca de tiempo ISO
    config: ExperimentConfig    # Configuración
    system_info: SystemInfo     # Info del sistema
    git_info: GitInfo          # Info del repositorio
    results: List[Result]       # Lista de resultados
    summary_stats: Dict         # Estadísticas resumen
    metadata: Dict             # Metadatos adicionales
```

## Información Capturada

### Sistema
- Plataforma y versión
- Versión de Python
- CPU (modelo y núcleos)
- Memoria RAM total
- Hostname

### Git
- Hash del commit
- Rama actual
- Estado (limpio/modificado)
- Mensaje del commit
- Fecha del commit

### Estadísticas
- Mejor/peor fitness
- Media y desviación estándar
- Mediana y cuartiles
- Tiempos de ejecución
- Tasa de convergencia

## Mejores Prácticas

### 1. Siempre Usar Tracking en Experimentos Importantes
```python
# ✅ Bueno
tracker = ExperimentTracker()
exp_id = tracker.start_experiment(config)
# ... ejecutar experimento ...
tracker.save_current()

# ❌ Evitar
# Ejecutar sin tracking
```

### 2. Incluir Metadatos Relevantes
```python
# ✅ Bueno
tracker.start_experiment(config, metadata={
    'hypothesis': 'Population size affects convergence',
    'hardware': 'GPU Tesla V100',
    'dataset_version': 'v2.1'
})

# ❌ Evitar
tracker.start_experiment(config)  # Sin contexto
```

### 3. Usar Semillas para Reproducibilidad
```python
# ✅ Bueno
config = ExperimentConfig(..., seed=42)

# ❌ Evitar
config = ExperimentConfig(..., seed=None)
```

### 4. Exportar en Múltiples Formatos
```python
# ✅ Bueno - Exportar para diferentes usos
tracker.export_experiment(exp_id, 'json')   # Archivo
tracker.export_experiment(exp_id, 'latex')  # Paper
tracker.export_experiment(exp_id, 'html')   # Compartir

# ❌ Evitar - Solo un formato
tracker.export_experiment(exp_id, 'json')
```

## Ejemplos de Uso Avanzado

### Experimento de Tuning de Parámetros

```python
# Configurar tracker
tracker = ExperimentTracker("experiments/parameter_tuning")

# Probar diferentes configuraciones
for pop_size in [20, 30, 50]:
    for max_iter in [50, 100, 200]:
        config = ExperimentConfig(
            algorithm="woa",
            problem_instance="P-n16-k8.vrp",
            population_size=pop_size,
            max_iterations=max_iter
        )
        
        exp_id = tracker.start_experiment(config, metadata={
            'tuning_param': ['population_size', 'max_iterations']
        })
        
        # Ejecutar múltiples runs
        for seed in range(30):
            result = run_algorithm(config, seed)
            tracker.log_result(result)
        
        tracker.save_current()

# Analizar resultados
all_experiments = tracker.list_experiments()
best_config = all_experiments.loc[all_experiments['best_fitness'].idxmin()]
print(f"Mejor configuración: {best_config}")
```

### Comparación de Algoritmos

```python
algorithms = ['woa', 'sma', 'gto', 'opa']
instance = "P-n16-k8.vrp"

experiment_ids = []

for algo in algorithms:
    config = ExperimentConfig(
        algorithm=algo,
        problem_instance=instance,
        population_size=30,
        max_iterations=100
    )
    
    exp_id = tracker.start_experiment(config)
    experiment_ids.append(exp_id)
    
    # Ejecutar 30 runs
    for i in range(30):
        result = run_algorithm(algo, instance, seed=42+i)
        tracker.log_result(result)
    
    tracker.save_current()

# Comparar todos los algoritmos
comparison = tracker.compare_experiments(experiment_ids)
print(comparison.sort_values('mean_fitness'))

# Exportar tabla LaTeX para paper
for exp_id in experiment_ids:
    tracker.export_experiment(exp_id, 'latex')
```

## Resolución de Problemas

### Error: "No hay experimento activo"
```python
# Solución: Iniciar experimento primero
tracker.start_experiment(config)
```

### Error: "Experimento no encontrado"
```python
# Verificar ID correcto
available = tracker.list_experiments()
print(available['experiment_id'].tolist())
```

### Recuperar de Fallo
```python
# El tracker guarda automáticamente con auto_save=True
tracker = ExperimentTracker(auto_save=True)

# O guardar manualmente después de cada resultado importante
tracker.log_result(result)
tracker.save_current()
```

## Integración con CI/CD

### GitHub Actions
```yaml
- name: Run experiments
  run: |
    python scripts/core/run_with_tracker.py \
      -a woa -i P-n16-k8.vrp \
      --experiment-dir artifacts/experiments

- name: Upload experiment results
  uses: actions/upload-artifact@v3
  with:
    name: experiment-results
    path: artifacts/experiments/
```

### Análisis Automatizado
```python
# Script para CI
tracker = ExperimentTracker("experiments")
recent = tracker.list_experiments(filter_criteria={
    'timestamp': {'$gte': datetime.now() - timedelta(days=1)}
})

if recent['mean_fitness'].min() > BASELINE:
    raise ValueError("Performance regression detected!")
```

## Conclusión

El sistema de tracking de experimentos es esencial para:
- **Reproducibilidad**: Cada experimento puede ser replicado exactamente
- **Trazabilidad**: Historial completo de todos los experimentos
- **Publicación**: Exportación directa a formatos de publicación
- **Análisis**: Comparación sistemática de resultados
- **Colaboración**: Compartir experimentos con el equipo

Úsalo consistentemente para mantener el rigor científico en tu investigación.