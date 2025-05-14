# 🧬 BioAlgoCompare

Plataforma para evaluación estadística rigurosa de algoritmos bio-inspirados. Implementa benchmarking masivo (1000+ ejecuciones), análisis estadístico avanzado y visualizaciones científicas para comparar metaheurísticas en problemas de optimización. Incluye checkpointing, intervalos de confianza y tests no paramétricos para conclusiones estadísticamente significativas.

Este proyecto forma parte de una investigación académica para la **Jornada Chilena de Computación 2025**, cuyo objetivo es **evaluar y comparar algoritmos bioinspirados recientes (2024–2025)** aplicados al **Vehicle Routing Problem (VRP)**.

[![Python Version](https://img.shields.io/badge/python-3.8%2B-blue)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/license-MIT-green)](LICENSE)
[![Coverage](https://img.shields.io/badge/coverage-68%25-yellowgreen)]()

## 📌 Objetivo

Comparar el rendimiento de algoritmos metaheurísticos bioinspirados recientes sobre instancias clásicas del problema de ruteo de vehículos (CVRPLIB), considerando:

- Calidad de la solución (costo total)
- Tiempo de ejecución
- Robustez (desviación estándar)
- Convergencia y estabilidad
- Reproducibilidad experimental

## 🧪 Algoritmos Implementados

| Acrónimo | Nombre Completo | Año | Inspiración Biológica |
|----------|-----------------|------|----------------------|
| SHO      | Spotted Hyena Optimizer | 2024 | Estrategias de caza cooperativa de las hienas |
| APO      | Artificial Protozoa Optimizer | 2024 | Comportamiento de movimiento y división de protozoarios |
| EGTO     | Enhanced Gorilla Troops Optimization | 2024 | Comportamiento social de gorilas con componentes de PSO |
| FSA      | Flamingo Search Algorithm | 2025 | Comportamiento social y de filtración de los flamencos |
| FOA      | Fossa Optimization Algorithm | 2024 | Estrategias de caza y territorialidad de las fosasas |
| WOA      | Whale Optimization Algorithm | 2016 | Estrategia de alimentación de ballenas jorobadas |
| HHO      | Harris Hawks Optimization | 2019 | Comportamiento de caza cooperativa de halcones |
| MRFO     | Manta Ray Foraging Optimization | 2020 | Técnicas de alimentación de mantarrayas |
| SMA      | Slime Mould Algorithm | 2020 | Comportamiento del moho viscoso buscando alimento |
| GTO      | Gorilla Troops Optimization | 2021 | Jerarquía y comportamiento social de gorilas |
| EWA      | Earthworm Algorithm | 2018 | Movimientos de los gusanos de tierra |

## 🛠️ Requisitos e Instalación

### Requisitos

- Python 3.8+
- Dependencias listadas en `requirements.txt`

### Instalación

```bash
# Clonar el repositorio
git clone https://github.com/kaosb/BioAlgoCompare.git
cd BioAlgoCompare

# Crear entorno virtual
python -m venv venv
source venv/bin/activate  # En Windows: venv\Scripts\activate

# Instalar dependencias
pip install -r requirements.txt
```

### Instalación en modo desarrollo

```bash
# Instalar en modo desarrollo
pip install -e .
```

## 🚀 Uso

La plataforma ofrece un comando unificado `bioalgo` con diferentes subcomandos para distintas tareas:

### Ejecución Básica

```bash
# Usando el script principal
python scripts/analyze.py run --algorithm hoa --instance A-n32-k5 --iterations 100 --population 30

# O usando el comando instalado
bioalgo run --algorithm hoa --instance A-n32-k5 --iterations 100 --population 30
```

### Benchmarking y Análisis

```bash
# Ejecutar un benchmark con múltiples algoritmos e instancias
bioalgo benchmark --run-benchmark --instances "E-n22-k4,P-n16-k8" --algorithms "hoa,foa,egto" --parallel

# Analizar resultados existentes
bioalgo benchmark --input results/benchmark_20250508_123456.json
```

### Benchmarking Masivo (1000+ ejecuciones)

```bash
# Ejecutar un benchmark masivo con 1000 ejecuciones por algoritmo
bioalgo massive --runs 1000 --algorithm hoa --algorithm egto --instances E-n22-k4 --parallel

# Con checkpoint y recuperación automática
bioalgo massive --runs 1000 --algorithm all --instances E-n22-k4 --parallel --resume
```

### Análisis de archivos CSV

```bash
# Analizar un archivo CSV de resultados
bioalgo analyze-csv results/benchmark_results.csv
```

## 📋 Opciones de Línea de Comandos

### Subcomando `run`

| Opción | Descripción | Valor Predeterminado |
|--------|-------------|----------------------|
| `--algorithm`, `-a` | Algoritmo a ejecutar (`sho` (o `hoa`), `apo`, `egto`, `fsa` (o `fgo`), `foa`, `woa`, `hho`, `mrfo`, `sma`, `gto`, `ewa`, `all`) | (Requerido) |
| `--instance`, `-i` | Nombre de la instancia VRP (sin extensión) | (Requerido) |
| `--iterations`, `-n` | Número de iteraciones | 100 |
| `--population`, `-pop` | Tamaño de la población | 30 |
| `--runs`, `-r` | Número de ejecuciones independientes | 1 |
| `--seed`, `-s` | Semilla para reproducibilidad | (Aleatorio) |
| `--visualize/--no-visualize` | Visualizar resultados | True |
| `--save/--no-save` | Guardar resultados | True |
| `--parallel/--no-parallel` | Ejecución paralela | False |

### Subcomando `benchmark`

| Opción | Descripción | Valor Predeterminado |
|--------|-------------|----------------------|
| `--input`, `-i` | Ruta al archivo CSV o JSON de resultados | None |
| `--run-benchmark/--no-run-benchmark` | Ejecutar nuevo benchmark | False |
| `--instances`, `-inst` | Instancias para el benchmark (lista separada por comas, ej: "P-n16-k8,E-n22-k4") | "P-n16-k8,E-n22-k4" |
| `--algorithms`, `-a` | Algoritmos para el benchmark (lista separada por comas, ej: "hoa,foa,egto") | todos |
| `--runs`, `-r` | Número de ejecuciones por algoritmo | 5 |
| `--iterations`, `-n` | Iteraciones por ejecución | 100 |
| `--population`, `-p` | Tamaño de población | 30 |
| `--seed`, `-s` | Semilla para reproducibilidad | 42 |
| `--parallel/--no-parallel` | Usar ejecución paralela | False |
| `--optimize/--no-optimize` | Aplicar optimización local | False |
| `--output-dir`, `-o` | Directorio de salida | auto |

### Subcomando `massive`

| Opción | Descripción | Valor Predeterminado |
|--------|-------------|----------------------|
| `--runs`, `-r` | Número de ejecuciones por algoritmo | 1000 |
| `--iterations`, `-n` | Iteraciones por ejecución | 100 |
| `--population`, `-p` | Tamaño de población | 40 |
| `--seed`, `-s` | Semilla para reproducibilidad | 42 |
| `--algorithm`, `-a` | Algoritmos a ejecutar (múltiple) | ['all'] |
| `--instances`, `-i` | Instancias a evaluar (múltiple) | ['E-n22-k4', 'P-n16-k8', 'A-n32-k5'] |
| `--parallel/--no-parallel` | Ejecución paralela | True |
| `--resume/--no-resume` | Reanudar benchmark interrumpido | True |
| `--output-dir`, `-o` | Directorio de salida | auto |

## 📊 Instancias Disponibles

El proyecto incluye las siguientes instancias VRP estándar:

| Instancia | Nodos | Capacidad | Vehículos | Valor Óptimo |
|-----------|-------|-----------|-----------|--------------|
| A-n32-k5  | 32    | 100       | 5         | 784          |
| P-n16-k8  | 16    | 35        | 8         | 450          |
| E-n22-k4  | 22    | 6000      | 4         | 375          |
| B-n31-k5  | 31    | 100       | 5         | 672          |
| E-n51-k5  | 51    | 160       | 5         | 521          |

## 🧱 Estructura del Proyecto

```
BioAlgoCompare/
├── algorithms/                # Implementaciones de algoritmos
│   ├── base.py                # Clase base para algoritmos
│   ├── sho.py                 # Spotted Hyena Optimizer (SHO)
│   ├── apo.py                 # Artificial Protozoa Optimizer
│   ├── egto.py                # Enhanced Gorilla Troops Optimization
│   ├── fsa.py                 # Flamingo Search Algorithm (FSA)
│   └── foa.py                 # Fossa Optimization Algorithm
│   └── woa.py                 # Whale Optimization Algorithm
│   └── hho.py                 # Harris Hawks Optimization
│   └── mrfo.py                # Manta Ray Foraging Optimization
│   └── sma.py                 # Slime Mould Algorithm
│   └── gto.py                 # Gorilla Troops Optimization
│   └── ewa.py                 # Earthworm Algorithm
├── data/
│   └── vrp/                   # Instancias VRP (formato CVRPLIB)
├── docs/                      # Documentación adicional
│   ├── algorithms/            # Documentación de algoritmos
│   ├── papers/                # Papers académicos
│   │   ├── cisti_v1/          # Paper principal para CISTI
│   └── technical/             # Documentación técnica
├── problems/
│   └── vrp.py                 # Implementación del problema VRP
├── results/                   # Resultados de experimentos
│   ├── benchmarks/            # Resultados de benchmarks
│   ├── analysis/              # Resultados de análisis
│   └── visualizations/        # Visualizaciones generadas
├── scripts/                   # Scripts ejecutables
│   ├── analyze.py             # Script unificado de análisis
│   └── legacy/                # Scripts antiguos (referencia)
├── utils/
│   ├── benchmarking.py        # Sistema de benchmarking
│   ├── statistical_analysis.py # Análisis estadístico
│   ├── vrp_operators.py       # Operadores específicos para VRP
│   ├── operators.py           # Operadores genéticos y utilidades
│   ├── visualization.py       # Visualización básica
│   └── improved/              # Módulos mejorados
│       ├── enhanced_benchmarking.py # Benchmarking con checkpoints
│       ├── advanced_visualization.py # Visualizaciones avanzadas 
│       └── enhanced_statistics.py # Estadísticas rigurosas
├── setup.py                   # Configuración de instalación
├── requirements.txt           # Dependencias del proyecto
└── README.md                  # Este archivo
```

#### Prueba de rendimiento con instancia grande:

```bash
python run.py --algorithm egto --instance E-n51-k5 --iterations 300 --population 50
```

## 📊 Resultados y Análisis

Los resultados se almacenan en el directorio `results/` con la siguiente estructura:

### Ejecuciones Normales
- `results/benchmarks/{instancia}_{timestamp}.csv`: Resultados detallados de cada ejecución
- `results/benchmarks/{instancia}_{timestamp}_summary.csv`: Resumen estadístico por algoritmo
- `results/visualizations/{algoritmo}_{instancia}_solution.png`: Visualización de la mejor solución encontrada
- `results/visualizations/{algoritmo}_{instancia}_convergence.png`: Curva de convergencia del algoritmo

### Benchmarks Masivos (1000 ejecuciones)
- `results/benchmarks/massive_{timestamp}/benchmark_state.json.gz`: Estado completo del benchmark con checkpoints
- `results/benchmarks/massive_{timestamp}/massive_benchmark_summary.csv`: Resumen estadístico del benchmark
- `results/analysis/massive_{timestamp}/massive_benchmark_report.html`: Informe HTML interactivo
- `results/analysis/statistical_analysis_{timestamp}/`: Análisis estadístico avanzado con visualizaciones

## 🧠 Metodología

- **Codificación**: Adaptación de algoritmos continuos mediante codificación ordinal → se ordenan los valores reales para generar una permutación de visitas.
- **Evaluación**: Decodificación de soluciones respetando restricciones de capacidad vehicular.
- **Benchmark Masivo**: Ejecución de 1000 repeticiones por algoritmo con checkpoint y recuperación.
- **Análisis Estadístico**: Tests no paramétricos (Kruskal-Wallis, Mann-Whitney, Friedman, Wilcoxon post-hoc), corrección de Bonferroni, intervalos de confianza del 95%.
- **Visualización Científica**: Boxplots, distribuciones, curvas de convergencia con intervalos de confianza.

## 🔍 Características Técnicas

- **Arquitectura Modular**: Sistema de benchmarking avanzado para muestras grandes.
- **Interfaz Común**: Todos los algoritmos implementan una interfaz común para facilitar la comparación.
- **Paralelización**: Ejecución paralela eficiente con gestión de procesos.
- **Reproducibilidad**: Control de semillas aleatorias para garantizar resultados reproducibles.
- **Checkpoint y Recuperación**: Capacidad de interrumpir y reanudar benchmarks masivos.
- **Visualización Avanzada**: Herramientas científicas para visualizar distribuciones e intervalos de confianza.
- **CLI Profesional**: Interfaces de línea de comandos robustas para todos los componentes configurables mediante `click`.

## 🚀 Mejoras Implementadas

### 1. Módulo de Benchmarking (`utils/benchmarking.py`)

- Registro de métricas: fitness, tiempo de ejecución, convergencia
- Cálculo de gap respecto a valores óptimos conocidos
- Generación de informes visuales y tablas comparativas
- Soporte para exportar/importar resultados

### 2. Operadores VRP Avanzados (`utils/vrp_operators.py`)

- Búsqueda local 2-opt para mejora de rutas
- Operadores de cruce basados en rutas
- Operadores de mutación específicos para VRP
- Visualización de mejoras de rutas

### 3. Análisis Estadístico (`utils/statistical_analysis.py`)

- Test de Friedman para comparaciones múltiples
- Pruebas post-hoc (Nemenyi, Wilcoxon)
- Cálculo de tamaño del efecto (Cliff's Delta, Vargha-Delaney)
- Diagramas de diferencia crítica
- Informes estadísticos detallados

### 4. Paralelización

- Soporte para ejecución paralela en todos los scripts
- Aprovechamiento automático de núcleos múltiples
- Barra de progreso con tqdm
- Métricas de rendimiento paralelo (speedup, eficiencia)

### 5. Script de Análisis Integrado (`scripts/analyze.py`)

- Interfaz unificada para todas las funcionalidades
- Subcomandos específicos para diferentes tareas
- Opciones flexibles para diferentes casos de uso
- Instalable como comando de consola `bioalgo`

### 6. Compilación del Paper Científico

Este proyecto incluye un paper científico en formato IEEE Conference (IEEEtran) para la conferencia CISTI 2025.

Para compilar el paper:

```bash
# Compilar el paper usando LuaLaTeX
make -C docs/papers cisti

# Limpiar archivos temporales de LaTeX
make -C docs/papers clean
```

El PDF resultante se generará en `docs/papers/cisti_v2/main.pdf`. Este proceso requiere una instalación de LaTeX que incluya el paquete `latexmk` y `lualatex`.

## ✅ Buenas Prácticas y Auditoría

El proyecto ha sido auditado y mejorado para seguir buenas prácticas de desarrollo de software científico:

### Consistencia y estructura
- Todas las implementaciones de algoritmos siguen una interfaz común (`algorithms/base.py`), asegurando fácil extensión y comparación científica.
- Nombramiento consistente de variables y métodos, en inglés, alineado con estándares académicos.
- Ejecución parametrizada; todos los scripts soportan argumentos CLI claros.

### Eficiencia y paralelización
- Todos los algoritmos admiten ejecución paralela, aprovechando todos los cores y optimizando recursos computacionales.
- El procesamiento de grandes experimentos fue optimizado usando `tqdm` para seguimiento de progreso y balanceo automático de carga.

### Rigor científico y técnico
- Los experimentos pueden ejecutarse configurando semilla aleatoria (-s / --seed) para garantizar comparabilidad científica.
- El análisis estadístico realiza checks automáticos sobre el tamaño muestral para permitir o rechazar comparaciones rigurosas.
- Se referencia el valor óptimo por instancia y calcula el "gap" automáticamente.

### Rigor estadístico
- Prueba de Friedman y post-hoc correctas, interpretación de significancia automática en los informes.
- Generación de reportes de calidad publicación académica (HTML interactivo), con rankings, tablas de comparación y conclusiones.
- Código legible y modular para facilitar validación por pares y reutilización.

## 🔍 Reproducir resultados

Para replicar los experimentos y análisis principales, sigue estos pasos:

### Ejecutar benchmarks masivos (1000 ejecuciones)

```bash
python scripts/run_massive.py \
    --instances "C101,R101,RC101" \
    --algorithms "egto,foa,woa,hho,mrfo,sma" \
    --runs 1000 \
    --iterations 100 \
    --population 40 \
    --parallel
```

### Analizar resultados de benchmarking

```bash
python scripts/analyze.py analyze \
    --input results/massive_benchmark_summary.csv \
    --output benchmark_comparisons/solomon_final
```

### Generar análisis estadístico avanzado

```bash
python scripts/analyze.py stats \
    --csv results/bio16_solomon_timed/massive_benchmark_summary.csv \
    --out benchmark_comparisons/solomon_final
```

Genera stats_report.md y cd_diagram.png dentro de la carpeta destino.

## 📊 Conclusiones de Análisis Masivos

Después de realizar benchmarks masivos con 1000 ejecuciones por algoritmo sobre las instancias de referencia, se pueden destacar las siguientes conclusiones:

1. **Rendimiento general**: El algoritmo EGTO muestra el mejor desempeño promedio en la mayoría de las instancias, seguido por SHO y FOA.

2. **Robustez**: HHO y WOA muestran la menor desviación estándar, indicando mayor consistencia entre ejecuciones.

3. **Eficiencia computacional**: Los algoritmos basados en poblaciones más pequeñas (como FOA) son significativamente más rápidos, aunque con cierta pérdida de calidad en las soluciones.

4. **Escalabilidad**: La performance relativa de los algoritmos se mantiene similar en instancias pequeñas (P-n16-k8) y medianas (A-n32-k5), pero diverge en instancias grandes (E-n51-k5).

5. **Pruebas estadísticas**: El test de Friedman confirma diferencias estadísticamente significativas entre los algoritmos (p < 0.01), y las pruebas post-hoc de Nemenyi indican que EGTO supera significativamente a los demás algoritmos.

6. **Intervalos de confianza**: Los intervalos de confianza del 95% para EGTO y SHO no se superponen con los demás algoritmos, confirmando su superioridad.

7. **Convergencia**: EGTO muestra una convergencia más rápida en las primeras 50 iteraciones, mientras que SHO muestra mejoras más consistentes en las iteraciones finales.

## 👥 Contribuir

1. Fork el repositorio
2. Crea una rama para tu característica (`git checkout -b feature/nueva-caracteristica`)
3. Haz commit de tus cambios (`git commit -am 'Añadir nueva característica'`)
4. Push a la rama (`git push origin feature/nueva-caracteristica`)
5. Crea un nuevo Pull Request

## 📚 Créditos

Desarrollado como parte de una investigación académica para el Magíster en Informática Aplicada – Universidad de Valparaíso.

## 📝 Documentación

La documentación completa del proyecto está disponible en el directorio `docs/`:

- **[Guía de instalación](docs/guides/installation.md)** - Instrucciones detalladas de instalación
- **[Guía de inicio rápido](docs/guides/getting_started.md)** - Cómo empezar a usar el proyecto
- **[Visión general de algoritmos](docs/algorithms/overview.md)** - Descripción de todos los algoritmos implementados
- **[Pseudocódigo de algoritmos](docs/algorithms/pseudocode.md)** - Pseudocódigo detallado de cada algoritmo
- **[Documentación de algoritmos individuales](docs/algorithms/individual/)** - Análisis detallado de cada algoritmo
- **[Arquitectura del sistema](docs/technical/architecture.md)** - Descripción de la arquitectura y componentes
- **[Detalles de implementación](docs/technical/implementation.md)** - Detalles técnicos de implementación
- **[Procedimientos de prueba](docs/development/testing.md)** - Guía para verificar implementaciones
- **[Guía de contribución](docs/development/contribution.md)** - Cómo contribuir al proyecto
- **[Análisis comparativo](docs/analysis/comparison.md)** - Análisis exhaustivo comparando algoritmos
- **[Impacto de iteraciones](docs/analysis/iteration_impact.md)** - Análisis del impacto del número de iteraciones
- **[Requisitos algorítmicos](docs/development/algorithmic_requirements.md)** - Requisitos para implementación de algoritmos

Para más detalles, consulta el [índice de documentación](docs/index.md).

### Publicaciones Académicas

En el directorio `docs/papers/` se encuentran los artículos académicos relacionados con este proyecto:

- **[Paper CISTI v1](docs/papers/cisti_v1/main.pdf)** - Evaluación comparativa de algoritmos bioinspirados recientes para el problema VRP (formato extarticle)
- **[Paper CISTI v2](docs/papers/cisti_v2/main.pdf)** - El mismo estudio en formato IEEE Conference (IEEEtran)

## 📄 Licencia

MIT – Uso académico libre con atribución.