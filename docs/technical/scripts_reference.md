# Referencia de Scripts

Este documento proporciona una referencia detallada de los scripts ejecutables del proyecto, con enfoque en rigor científico, reproducibilidad, transparencia y explicabilidad.

## Estructura General

Los scripts principales del proyecto se encuentran en el directorio `scripts/`:

```
scripts/
├── analyze.py            # Script unificado de análisis (CLI principal)
├── run.py                # Ejecución de algoritmos individuales
├── run_massive.py        # Ejecución masiva (1000+ repeticiones)
└── legacy/               # Scripts antiguos (compatibilidad)
    ├── analyze_results.py    # Versión anterior de análisis
    └── analyze_1000runs.py   # Versión anterior para 1000 ejecuciones
```

## Scripts Principales

### 1. `scripts/run.py`

**Propósito**: Ejecuta algoritmos metaheurísticos individuales o comparaciones sobre instancias del problema VRP.

**Características científicas**:
- Control de semilla aleatoria para reproducibilidad
- Métricas de rendimiento detalladas (tiempo, fitness, convergencia)
- Visualización de soluciones y curvas de convergencia
- Soporte para ejecución paralela
- Registro de parámetros completos

**Sintaxis**:
```bash
python scripts/run.py --algorithm ALGORITMO --instance INSTANCIA [opciones adicionales]
```

**Parámetros**:
| Parámetro | Descripción | Valor Predeterminado |
|-----------|-------------|----------------------|
| `--algorithm`, `-a` | Algoritmo a ejecutar (`hoa`, `apo`, `egto`, `fgo`, `foa`, `woa`, `hho`, `mrfo`, `sma`, `gto`, `ewa`, `all`) | (Requerido) |
| `--instance`, `-i` | Nombre de la instancia VRP | (Requerido) |
| `--iterations`, `-n` | Número de iteraciones | 100 |
| `--population`, `-p` | Tamaño de la población | 30 |
| `--runs`, `-r` | Número de ejecuciones independientes | 1 |
| `--seed`, `-s` | Semilla para reproducibilidad | (Aleatorio) |
| `--visualize/--no-visualize` | Visualizar resultados | True |
| `--save/--no-save` | Guardar resultados | True |
| `--parallel/--no-parallel` | Ejecución paralela | False |

**Salidas**:
- **Resultados en terminal**: Progreso, métricas y resumen
- **Archivos CSV**: Resultados detallados y resumen estadístico
- **Visualizaciones**: Soluciones de rutas y curvas de convergencia
- **Metadatos de ejecución**: Información de paralelización y parámetros

**Ejemplo de uso científico**:
```bash
# Ejecución rigurosa para análisis estadístico
python scripts/run.py --algorithm all --instance E-n22-k4 --runs 30 --seed 42 --parallel

# Estudio de parámetros (efecto del tamaño de población)
python scripts/run.py --algorithm egto --instance P-n16-k8 --population 20 --runs 10 --seed 42
python scripts/run.py --algorithm egto --instance P-n16-k8 --population 50 --runs 10 --seed 42
python scripts/run.py --algorithm egto --instance P-n16-k8 --population 100 --runs 10 --seed 42
```

**Notas metodológicas**:
- Para análisis estadísticamente significativos, se recomienda un mínimo de 30 ejecuciones independientes
- La semilla determina la inicialización de los generadores de números aleatorios
- Los resultados guardados contienen toda la información necesaria para reproducir el experimento

---

### 2. `scripts/analyze.py`

**Propósito**: Script unificado para análisis riguroso de metaheurísticas, que combina las funcionalidades de múltiples herramientas de análisis anteriores.

**Características científicas**:
- Tests estadísticos no paramétricos (Friedman, Wilcoxon, etc.)
- Corrección para comparaciones múltiples (Bonferroni, Holm, etc.)
- Intervalos de confianza y tamaño del efecto
- Visualizaciones científicas avanzadas
- Generación automática de informes

**Sintaxis**:
```bash
python scripts/analyze.py COMANDO [opciones]
```

**Comandos disponibles**:
- `run`: Ejecuta algoritmos (similar a `run.py`)
- `benchmark`: Realiza benchmarking comparativo
- `massive`: Ejecuta benchmarks masivos (1000+ repeticiones)
- `analyze-csv`: Analiza archivos CSV de resultados existentes

**Parámetros para `benchmark`**:
| Parámetro | Descripción | Valor Predeterminado |
|-----------|-------------|----------------------|
| `--input`, `-i` | Archivo CSV/JSON de resultados | None |
| `--run-benchmark/--no-run-benchmark` | Ejecutar nuevo benchmark | False |
| `--instances`, `-inst` | Instancias para benchmark | ['P-n16-k8', 'E-n22-k4'] |
| `--algorithms`, `-a` | Algoritmos para benchmark | [todos] |
| `--runs`, `-r` | Ejecuciones por algoritmo | 5 |
| `--iterations`, `-n` | Iteraciones por ejecución | 100 |
| `--population`, `-p` | Tamaño de población | 30 |
| `--seed`, `-s` | Semilla para reproducibilidad | 42 |
| `--parallel/--no-parallel` | Ejecución paralela | False |
| `--optimize/--no-optimize` | Aplicar optimización local | False |
| `--output-dir`, `-o` | Directorio de salida | auto |

**Parámetros para `massive`**:
| Parámetro | Descripción | Valor Predeterminado |
|-----------|-------------|----------------------|
| `--runs`, `-r` | Ejecuciones por algoritmo | 1000 |
| `--iterations`, `-n` | Iteraciones por ejecución | 100 |
| `--population`, `-p` | Tamaño de población | 40 |
| `--seed`, `-s` | Semilla para reproducibilidad | 42 |
| `--algorithm`, `-a` | Algoritmos a ejecutar | ['all'] |
| `--instances`, `-i` | Instancias a evaluar | ['E-n22-k4', 'P-n16-k8', 'A-n32-k5'] |
| `--parallel/--no-parallel` | Ejecución paralela | True |
| `--resume/--no-resume` | Reanudar benchmark interrumpido | True |
| `--output-dir`, `-o` | Directorio de salida | auto |

**Salidas**:
- **Resultados en terminal**: Progreso, métricas y resumen estadístico
- **Archivos CSV/JSON**: Resultados detallados y resumen estadístico
- **Informes HTML**: Análisis completo con visualizaciones interactivas
- **Archivos de checkpoint**: Para benchmarks masivos con recuperación

**Ejemplo de uso científico**:
```bash
# Benchmark completo para publicación científica
python scripts/analyze.py benchmark --run-benchmark --optimize --parallel \
    --instances E-n22-k4 P-n16-k8 A-n32-k5 \
    --algorithms hoa foa egto gto ewa \
    --runs 30 --seed 42

# Benchmark masivo con 1000 ejecuciones y checkpointing
python scripts/analyze.py massive --runs 1000 --algorithm all --instances E-n22-k4 --parallel --resume

# Análisis estadístico de resultados existentes
python scripts/analyze.py analyze-csv results/benchmark_20250508_123456.csv
```

**Notas metodológicas**:
- Los informes incluyen tests de normalidad automáticos para seleccionar pruebas paramétricas/no paramétricas
- El sistema de checkpointing permite recuperar ejecuciones interrumpidas sin pérdida de datos
- Para publicaciones científicas, se recomienda usar el modo `--optimize` que aplica búsqueda local

---

### 3. `scripts/run_massive.py`

**Propósito**: Ejecuta benchmarks masivos con 1000 o más repeticiones, con soporte de checkpointing y recuperación.

**Características científicas**:
- Muestreo estadístico de gran escala
- Intervalos de confianza precisos
- Sistema de recuperación para ejecuciones interrumpidas
- Análisis automático de convergencia

**Sintaxis**:
```bash
python scripts/run_massive.py [opciones]
```

**Parámetros**:
| Parámetro | Descripción | Valor Predeterminado |
|-----------|-------------|----------------------|
| `--runs`, `-r` | Número de ejecuciones | 1000 |
| `--algorithm`, `-a` | Algoritmos a ejecutar | ['all'] |
| `--instance`, `-i` | Instancias VRP | ['E-n22-k4'] |
| `--iterations`, `-n` | Iteraciones por ejecución | 100 |
| `--population`, `-p` | Tamaño de población | 30 |
| `--seed`, `-s` | Semilla base | 42 |
| `--resume/--no-resume` | Reanudar ejecución | True |
| `--checkpoint-interval`, `-c` | Intervalo de checkpoint | 10 |

**Salidas**:
- **Archivos de checkpoint**: Estado completo en formato JSON comprimido
- **Resumen estadístico**: Estadísticas detalladas en CSV
- **Informe HTML**: Análisis completo con visualizaciones

**Ejemplo de uso científico**:
```bash
# Benchmark masivo para un solo algoritmo
python scripts/run_massive.py --algorithm egto --runs 1000 --instance E-n22-k4,P-n16-k8

# Comparación exhaustiva de todos los algoritmos
python scripts/run_massive.py --algorithm all --runs 1000 --instance E-n22-k4 --parallel
```

**Notas metodológicas**:
- Las muestras de 1000+ ejecuciones permiten una caracterización estadística robusta
- Se generan automáticamente intervalos de confianza del 95%
- El método utiliza la variación sistemática de la semilla base para garantizar independencia estadística

## Acerca de la Reproducibilidad

Todos los scripts están diseñados siguiendo principios de reproducibilidad científica:

1. **Control de semilla**: Todos aceptan un parámetro de semilla `--seed` para garantizar resultados deterministas
2. **Registro de configuración**: Los resultados almacenan todos los parámetros utilizados
3. **Almacenamiento de metadatos**: Información sobre versión, tiempo de ejecución y entorno
4. **Checkpointing**: Para experimentos largos, permiten guardar y recuperar el estado
5. **Informes completos**: Los informes generados incluyen toda la información metodológica

## Ejemplo de Flujo de Trabajo Científico

Para un estudio científico completo, se recomienda el siguiente flujo de trabajo:

1. **Exploración inicial**:
   ```bash
   python scripts/run.py --algorithm all --instance P-n16-k8 --runs 5 --parallel
   ```

2. **Ajuste de parámetros**:
   ```bash
   python scripts/analyze.py benchmark --run-benchmark --instances P-n16-k8 \
       --algorithms egto --population 20,30,50,100 --runs 10
   ```

3. **Benchmark riguroso**:
   ```bash
   python scripts/analyze.py benchmark --run-benchmark --optimize --parallel \
       --instances E-n22-k4,P-n16-k8,A-n32-k5 \
       --algorithms egto,foa,hoa,gto,ewa \
       --runs 30 --seed 42
   ```

4. **Validación masiva**:
   ```bash
   python scripts/analyze.py massive --runs 1000 --algorithm egto,foa,hoa \
       --instances E-n22-k4 --parallel --resume
   ```

5. **Análisis estadístico**:
   ```bash
   python scripts/analyze.py analyze-csv results/benchmark_final.csv \
       --output-dir results/analysis_final
   ```

Este flujo garantiza resultados científicamente rigurosos, reproducibles y estadísticamente significativos.

## Legado y Compatibilidad

Los scripts en `scripts/legacy/` se mantienen por compatibilidad con trabajos anteriores:

- `analyze_results.py`: Versión previa del sistema de análisis
- `analyze_1000runs.py`: Versión previa para ejecuciones masivas

Aunque funcionales, se recomienda usar los scripts principales actualizados para nuevos experimentos.