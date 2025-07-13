# 🧬 BioAlgoCompare

[![Python Version](https://img.shields.io/badge/python-3.8%2B-blue)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/license-MIT-green)](LICENSE)
[![Algorithms](https://img.shields.io/badge/algorithms-17-orange)](algorithms/)
[![Coverage](https://img.shields.io/badge/coverage-92%25-brightgreen)](tests/)
[![Tests](https://img.shields.io/badge/tests-759%20passed-brightgreen)](tests/)

Plataforma de evaluación estadística rigurosa para algoritmos metaheurísticos bioinspirados aplicados al Vehicle Routing Problem (VRP). Implementa benchmarking masivo con análisis estadístico avanzado siguiendo las mejores prácticas de investigación reproducible.

## 🎯 Enfoque de Investigación

Esta plataforma se centra en la evaluación rigurosa de algoritmos bioinspirados para el Vehicle Routing Problem (VRP) estándar, con énfasis en análisis estadístico reproducible y benchmarking masivo.

## 🚀 Inicio Rápido

```bash
# 1. Clonar e instalar
git clone https://github.com/kaosb/BioAlgoCompare.git
cd BioAlgoCompare
pip install -r requirements.txt

# 2. Ejecutar un algoritmo
python scripts/analyze.py run --algorithm sho --instance A-n32-k5

# 3. Benchmark comparativo
python scripts/analyze.py benchmark --run-benchmark --algorithms "sho,foa,egto" --instances "E-n22-k4,P-n16-k8"
```

## 📋 Tabla de Contenidos

- [Características](#-características)
- [Instalación](#-instalación)
- [Uso Completo](#-uso-completo)
  - [Ejecución Básica](#ejecución-básica)
  - [Benchmarking Comparativo](#benchmarking-comparativo)
  - [Benchmarking Masivo](#benchmarking-masivo)
  - [Análisis Estadístico](#análisis-estadístico-de-resultados)
- [Flujo de Reproducibilidad](#-flujo-de-reproducibilidad-datos--paper)
- [Generación de Papers](#-generación-de-papers-y-reportes)
- [Algoritmos Implementados](#-algoritmos-implementados)
- [Características Avanzadas](#-características-avanzadas)
- [Herramientas Solomon](#-herramientas-solomon)
- [Arquitectura](#-arquitectura)
- [Tests y Cobertura](#-tests-y-cobertura)
- [Documentación](#-documentación)
- [Referencias](#-referencias)
- [Contribuir](#-contribuir)
- [Licencia](#-licencia)

## ✨ Características

### Capacidades Principales
- **17 algoritmos bioinspirados** únicos (2016-2025)
- **Benchmarking masivo** con soporte para 1000+ ejecuciones
- **Análisis estadístico completo**: Friedman, Nemenyi (CD corregido), Wilcoxon, tamaños de efecto
- **Ejecución paralela** para máximo rendimiento
- **Checkpointing automático** para experimentos largos
- **Visualizaciones científicas** de calidad publicación
- **CLI unificado** con interfaz intuitiva
- **100% reproducible** con control de semillas

### Capacidades Adicionales
- **Optimización local**: Operadores 2-opt, Or-opt, Relocate, Exchange
- **Métricas avanzadas**: Gap to optimal, success rate
- **Instancias Solomon**: Soporte completo para benchmarks Solomon
- **Análisis de sensibilidad**: Herramientas para análisis paramétrico

## 🛠️ Instalación

### Requisitos

- Python 3.8 o superior
- pip o conda para gestión de paquetes

### Instalación Estándar

```bash
# Clonar el repositorio
git clone https://github.com/kaosb/BioAlgoCompare.git
cd BioAlgoCompare

# Crear entorno virtual (recomendado)
python -m venv venv
source venv/bin/activate  # En Windows: venv\Scripts\activate

# Instalar dependencias
pip install -r requirements.txt
```

### Instalación para Desarrollo

```bash
# Instalar en modo desarrollo
pip install -e .

# Instalar dependencias opcionales
pip install torch torchvision  # Para Imitation Learning
pip install cec2017           # Para validación CEC2017

# Esto habilita el comando 'bioalgo' globalmente
bioalgo run --algorithm sho --instance A-n32-k5
```

## 📖 Uso Completo

### Ejecución Básica

Ejecutar un algoritmo individual:

```bash
python scripts/analyze.py run --algorithm sho --instance A-n32-k5 --iterations 100 --population 30
```

Con múltiples ejecuciones y semilla fija:

```bash
python scripts/analyze.py run --algorithm egto --instance E-n51-k5 --runs 10 --seed 42
```

Ejecutar todos los algoritmos en paralelo:

```bash
python scripts/analyze.py run --algorithm all --instance P-n16-k8 --parallel
```

### Benchmarking Comparativo

Comparar múltiples algoritmos (30+ runs recomendado):

```bash
python scripts/analyze.py benchmark \
    --run-benchmark \
    --algorithms "ho,sho,foa,egto,woa" \
    --instances "E-n22-k4,P-n16-k8,A-n32-k5" \
    --runs 30 \
    --iterations 100 \
    --population 40 \
    --parallel \
    --seed 42
```

Con optimización local:

```bash
python scripts/analyze.py benchmark \
    --run-benchmark \
    --optimize \
    --output-dir results/optimized_benchmark
```

### Benchmarking Masivo

Para experimentos de gran escala con 1000+ ejecuciones:

```bash
python scripts/analyze.py massive \
    --runs 1000 \
    --algorithm all \
    --instances E-n22-k4 P-n16-k8 A-n32-k5 \
    --parallel \
    --resume \
    --iterations 300 \
    --population 50
```

Reanudar experimento interrumpido:

```bash
python scripts/analyze.py massive \
    --resume \
    --checkpoint results/massive_20250111_123456/checkpoint.pkl
```

### Análisis de Instancias Solomon

Benchmark con instancias Solomon para VRP:

```bash
python scripts/analyze.py benchmark \
    --run-benchmark \
    --instances "RC101,RC102,RC103" \
    --algorithms "ho,sho,foa" \
    --runs 100 \
    --seed 42
```

### Análisis Estadístico de Resultados

Analizar resultados existentes:

```bash
# Convertir resultados JSON a CSV
python scripts/analyze.py convert \
    --json results/benchmark_results.json \
    --csv results/results.csv

# Análisis estadístico completo
python scripts/analyze.py stats \
    --csv results/results.csv \
    --out results/statistical_analysis
```

El análisis incluye:
- Tests de Friedman y Quade
- Test post-hoc de Nemenyi con CD corregido: `q_α/√2 * sqrt(k(k+1)/(6n))`
- Test de Wilcoxon signed-rank para comparación pareada
- Tamaños de efecto (Vargha-Delaney A12, Cliff's delta)
- Diagramas de diferencias críticas
- Heatmaps de significancia
- Reportes detallados en Markdown/HTML
- Exportación a LaTeX con booktabs/siunitx

### Ejemplo de Flujo Completo

```bash
# 1. Definir experimento
EXPERIMENT="vrp_bioinspirados_2025"
OUTPUT="results/${EXPERIMENT}"

# 2. Ejecutar benchmark
python scripts/analyze.py benchmark \
    --run-benchmark \
    --algorithms "sho,apo,egto,fsa,foa,woa,hho,mrfo,sma,gto,ewa" \
    --instances "E-n22-k4,P-n16-k8,A-n32-k5,B-n31-k5,E-n51-k5" \
    --runs 100 \
    --iterations 200 \
    --population 40 \
    --parallel \
    --output-dir "${OUTPUT}"

# 3. Convertir a CSV
python scripts/analyze.py convert \
    --json "${OUTPUT}/benchmark_results.json" \
    --csv "${OUTPUT}/results.csv"

# 4. Análisis estadístico
python scripts/analyze.py stats \
    --csv "${OUTPUT}/results.csv" \
    --out "${OUTPUT}/analysis"
```

## 🔬 Flujo de Reproducibilidad: Datos → Paper

### Paso 1: Ejecutar Experimentos Comprehensivos

```bash
# 1.1 Benchmark masivo (resultados principales)
python scripts/analyze.py massive \
    --runs 1000 \
    --algorithm ho sho foa egto woa \
    --instances "E-n22-k4,P-n16-k8,A-n32-k5" \
    --parallel \
    --seed 42

# 1.2 Experimentos con instancias Solomon
python scripts/analyze.py benchmark \
    --run-benchmark \
    --instances "RC101,RC102,RC103" \
    --algorithms "ho,sho,foa" \
    --runs 100 \
    --seed 42
```

### Paso 2: Análisis Estadístico

```bash
# 2.1 Convertir resultados
python scripts/analyze.py convert \
    --json results/massive_*/benchmark_results.json \
    --csv results/all_results.csv

# 2.2 Análisis estadístico completo
python scripts/analyze.py stats \
    --csv results/all_results.csv \
    --out results/statistical_analysis
```

### Paso 3: Análisis de Sensibilidad de Parámetros

```bash
# 3.1 Análisis de sensibilidad HO
python scripts/tools/sensitivity_analysis_ho.py \
    --instance data/vrp/P-n16-k8.vrp \
    --runs 30 \
    --output results/sensitivity

# Analiza: α ∈ [0.1, 0.9], β ∈ [0.2, 0.8], γ ∈ [0.3, 1.0]
```

### Paso 4: Generar Materiales del Paper

```bash
# 4.1 Generar reporte comprehensivo
python scripts/tools/generate_paper_report.py \
    --input results/massive_*/benchmark_results.json \
    --out paper_submission \
    --seed 42

# 4.2 Generar reporte de validación
python scripts/tools/generate_validation_report.py \
    --results-path results/all_results.csv \
    --output-path paper_submission/validation_report.tex
```

### Paso 5: Paquete de Sumisión Completo

```bash
# 5.1 Generar sumisión CLEI 2025
./scripts/tools/generate_clei_submission.sh

# Genera:
# - paper_clei2025.pdf (LaTeX compilado)
# - Todas las tablas en formato booktabs/siunitx
# - Figuras en calidad publicación (300 DPI)
# - Metadatos completos
# - Archivo ZIP para sumisión
```

## 📝 Generación de Papers y Reportes

### Scripts de Generación Disponibles

#### 1. **generate_paper_report.py** - Generador de Informes Científicos

```bash
python scripts/tools/generate_paper_report.py \
    --input results/benchmark_results.json \
    --out clei_submission \
    --format ieee \
    --include-sensitivity \
    --include-convergence
```

Genera:
- `paper_clei2025.tex`: Paper completo en LaTeX
- `tables/`: Tablas con formato booktabs/siunitx
- `figures/`: Visualizaciones de convergencia y frentes de Pareto
- `informe_tecnico.md`: Informe técnico detallado

#### 2. **generate_validation_report.py** - Reporte de Validación

```bash
python scripts/tools/generate_validation_report.py \
    --results-path results/validation_results.json \
    --output-path validation_report.tex
```

#### 3. **sensitivity_analysis_ho.py** - Análisis de Sensibilidad

```bash
python scripts/tools/sensitivity_analysis_ho.py \
    --instance data/vrp/P-n16-k8.vrp \
    --runs 10 \
    --output sensitivity_results
```

Genera:
- Mapas de calor de interacción de parámetros
- Gráficos de efectos principales
- Configuración óptima: α=0.10, β=0.50, γ=0.65

### Scripts de Validación

#### **validate_quick_ho.sh** - Validación Completa

```bash
./scripts/tools/validate_quick_ho.sh
```

Ejecuta:
- Tests unitarios con cobertura (objetivo: 80%+)
- Validación HO+IL integración
- Benchmark pequeño (30 runs)
- Análisis estadístico
- Validación de factibilidad de rutas y restricciones de capacidad
- Comando para benchmark masivo (1000 runs)

#### **compare_cec_benchmarks.py** - Comparación CEC2017

```bash
python scripts/tools/compare_cec_benchmarks.py
```

- Compara en funciones unimodales (F1, F3) y multimodales (F7, F10)
- Analiza fases HO (Position, Defense, Evasion)
- Valida métricas QC en instancias Solomon

## 🧪 Algoritmos Implementados

El proyecto implementa **17 algoritmos metaheurísticos bioinspirados únicos**:

| Algoritmo | Nombre Completo | Año | Inspiración |
|-----------|-----------------|-----|-------------|
| **sho** | Spotted Hyena Optimizer | 2017 | Caza cooperativa de hienas |
| **apo** | Artificial Protozoa Optimizer | 2024 | División de protozoarios |
| **egto** | Enhanced Gorilla Troops Optimization | 2024 | Comportamiento social mejorado |
| **fsa** | Flamingo Search Algorithm | 2021 | Búsqueda de alimento |
| **foa** | Fossa Optimization Algorithm | 2024 | Estrategias de caza |
| **woa** | Whale Optimization Algorithm | 2016 | Alimentación de ballenas |
| **hho** | Harris Hawks Optimization | 2019 | Caza cooperativa |
| **mrfo** | Manta Ray Foraging Optimization | 2020 | Alimentación de mantarrayas |
| **sma** | Slime Mould Algorithm | 2020 | Comportamiento del moho |
| **gto** | Gorilla Troops Optimization | 2021 | Jerarquía social |
| **ewa** | Earthworm Algorithm | 2018 | Movimientos de lombrices |
| **aha** | Artificial Hummingbird Algorithm | 2022 | Vuelo de colibríes |
| **opa** | Orca Predator Algorithm | 2021 | Caza de orcas |
| **rro** | Raven Roosting Optimization | 2016 | Dormideros de cuervos |
| **smo** | Starling Murmuration Optimizer | 2022 | Bandadas de estorninos |
| **gvoa** | Griffon Vultures Optimization | 2025 | Vuelo termal de buitres |
| **ho** | Hippopotamus Optimizer | 2024 | Comportamiento territorial |

**Nota**: Los alias `hoa` (→ `sho`) y `fgo` (→ `fsa`) están disponibles para compatibilidad.

### Detalles de Implementación HO

El Hippopotamus Optimizer implementa tres fases comportamentales:

1. **Fase de Posición**: Exploración del espacio de búsqueda
2. **Fase de Defensa**: Intensificación territorial con parámetro α
3. **Fase de Evasión**: Escape de óptimos locales con parámetro γ

Parámetros: α ∈ [0.1, 0.9], β ∈ [0.2, 0.8], γ ∈ [0.3, 1.0]

## 🚀 Características Avanzadas

### 1. Imitation Learning (IL) Integration

```bash
# Generar demostraciones
python utils/generate_demos.py \
    --algorithm ho \
    --instances "E-n22-k4,P-n16-k8" \
    --runs 100 \
    --output demos/ho_demos.csv

# Entrenar modelo IL
python utils/train_il.py \
    --dataset demos/ho_demos.csv \
    --epochs 100 \
    --batch-size 32 \
    --learning-rate 0.001 \
    --output models/ho_il_model.pth

# Evaluar con IL
python utils/evaluate_il.py \
    --model models/ho_il_model.pth \
    --test-instances "A-n32-k5,E-n51-k5" \
    --runs 50
```

### 2. Operadores de Optimización Local VRP

- **2-opt**: Intercambio de arcos
- **Or-opt**: Reubicación de secuencias
- **Relocate**: Mover clientes entre rutas
- **Exchange**: Intercambiar clientes

### 3. Métricas Multi-objetivo

```python
# Las métricas multi-objetivo están disponibles para futuras extensiones
# en utils/multiobjective_metrics.py
```

## 🛠️ Herramientas Solomon

### Benchmark Completo Solomon

```bash
# Ejecutar todas las instancias Solomon
python tools/solomon/run_full_solomon_benchmark.py \
    --algorithms ho sho foa woa \
    --runs 100 \
    --parallel
```

### Benchmark Extendido Solomon

```bash
# Series específicas RC (clientes agrupados)
python tools/solomon/run_extended_solomon_benchmark.py \
    --series RC \
    --subset 101 102 103 104 \
    --time-limit 3600
```

### Análisis de Resultados Solomon

```bash
# Analizar resultados
python tools/solomon/analyze_solomon_results.py \
    --results results/solomon_benchmark \
    --output solomon_analysis
```

### Conversión de Formato

```bash
# Convertir instancias Solomon a formato VRP estándar
python tools/solomon/convert_solomon_format.py \
    --input solomon_instances \
    --output data/vrp/Solomon
```

## 🏗️ Arquitectura

### Estructura del Proyecto

```
BioAlgoCompare/
├── algorithms/          # Implementaciones de algoritmos
│   ├── base.py         # Clases base abstractas
│   └── *.py            # 16 algoritmos bioinspirados
├── data/
│   └── vrp/            # Instancias CVRPLIB
├── docs/               # Documentación completa
│   ├── algorithms/     # Docs de cada algoritmo
│   ├── papers/         # Artículos académicos
│   └── technical/      # Documentación técnica
├── problems/
│   └── vrp.py          # Implementación del VRP
├── results/            # Resultados experimentales
├── scripts/
│   └── analyze.py      # CLI principal unificado
├── tests/              # Suite de pruebas
├── utils/              # Utilidades del sistema
│   ├── algorithm_factory.py      # Factory de algoritmos
│   ├── benchmarking.py          # Sistema de benchmarking
│   ├── statistical_analysis.py  # Análisis estadístico
│   └── visualization.py         # Visualizaciones
├── LICENSE             # Licencia MIT
├── README.md           # Este archivo
├── requirements.txt    # Dependencias Python
└── setup.py           # Configuración de instalación
```

### Diseño Modular

```
┌─────────────────┐     ┌──────────────────┐     ┌─────────────────┐
│   CLI (Click)   │────▶│ Algorithm Factory │────▶│   Algorithms    │
└─────────────────┘     └──────────────────┘     └─────────────────┘
         │                       │                         │
         ▼                       ▼                         ▼
┌─────────────────┐     ┌──────────────────┐     ┌─────────────────┐
│  Benchmarking   │────▶│   VRP Problem    │────▶│   Operators     │
└─────────────────┘     └──────────────────┘     └─────────────────┘
         │
         ▼
┌─────────────────┐     ┌──────────────────┐
│   Statistics    │────▶│  Visualization   │
└─────────────────┘     └──────────────────┘
```

## 🧪 Tests y Cobertura

### Ejecutar Tests

```bash
# Ejecutar todos los tests con cobertura
pytest --cov=algorithms --cov=problems --cov=utils --cov=scripts

# Tests específicos por categoría
pytest tests/unit/algorithms/
pytest tests/integration/

# Tests con marcadores
pytest -m "not slow"

# Generar reporte de cobertura HTML
pytest --cov-report=html --cov-report=term-missing
```

### Estado Actual de Cobertura: **92%**

#### Gaps de Cobertura a Resolver

1. `utils/algorithm_factory.py` (0%)
2. `utils/evaluate_il.py` (0%)
3. `utils/generate_demos.py` (0%)
4. `utils/train_il.py` (0%)
5. `problems/vrp.py` (92% - casos edge faltantes)

## 📊 Opciones de Línea de Comandos

### Comando `run`

| Opción | Descripción | Default |
|--------|-------------|---------|
| `--algorithm`, `-a` | Algoritmo a ejecutar | (requerido) |
| `--instance`, `-i` | Instancia VRP | (requerido) |
| `--iterations`, `-n` | Número de iteraciones | 100 |
| `--population`, `-pop` | Tamaño de población | 30 |
| `--runs`, `-r` | Ejecuciones independientes | 1 |
| `--seed`, `-s` | Semilla aleatoria | None |
| `--parallel`, `-p` | Ejecución paralela | False |

### Comando `benchmark`

| Opción | Descripción | Default |
|--------|-------------|---------|
| `--run-benchmark` | Ejecutar nuevo benchmark | False |
| `--algorithms`, `-a` | Lista de algoritmos | todos |
| `--instances`, `-inst` | Lista de instancias | P-n16-k8,E-n22-k4 |
| `--runs`, `-r` | Ejecuciones por algoritmo | 5 |
| `--output-dir`, `-o` | Directorio de salida | auto |

### Comando `massive`

| Opción | Descripción | Default |
|--------|-------------|---------|
| `--runs`, `-r` | Ejecuciones por algoritmo | 1000 |
| `--algorithm`, `-a` | Algoritmos (múltiple) | all |
| `--instances`, `-i` | Instancias VRP | E-n22-k4,P-n16-k8,A-n32-k5 |
| `--resume` | Reanudar si se interrumpe | True |

### Comando `stats`

| Opción | Descripción | Default |
|--------|-------------|---------|
| `--csv` | Archivo CSV de entrada | (requerido) |
| `--out` | Directorio de salida | mismo que CSV |

## 📚 Documentación

### Documentación Principal

- [Guía de Instalación](docs/guides/installation.md)
- [Referencia de Comandos](docs/COMMAND_REFERENCE.md)
- [Metodología Estadística](docs/STATISTICS.md)
- [Arquitectura del Sistema](docs/technical/architecture.md)

### Documentación de Algoritmos

- [Visión General](docs/algorithms/overview.md)
- [Pseudocódigo](docs/algorithms/pseudocode.md)
- [Documentación Individual](docs/algorithms/individual/)

### Análisis y Resultados

- [Comparación de Algoritmos](docs/analysis/comparison.md)
- [Impacto de Iteraciones](docs/analysis/iteration_impact.md)
- [Conclusiones](docs/analysis/conclusions.md)

### Desarrollo

- [Guía de Contribución](docs/development/contribution.md)
- [Procedimientos de Prueba](docs/development/testing.md)
- [Requisitos Algorítmicos](docs/development/algorithmic_requirements.md)

## 🤝 Contribuir

Las contribuciones son bienvenidas. Por favor:

1. Fork el repositorio
2. Crea una rama (`git checkout -b feature/nueva-caracteristica`)
3. Commit cambios (`git commit -am 'Añade nueva característica'`)
4. Push a la rama (`git push origin feature/nueva-caracteristica`)
5. Crea un Pull Request

Ver [Guía de Contribución](docs/development/contribution.md) para más detalles.

## 📈 Estado del Proyecto

- ✅ 16 algoritmos implementados y probados
- ✅ Sistema de benchmarking completo
- ✅ Análisis estadístico riguroso
- ✅ Documentación exhaustiva
- 🚧 Integración con más problemas de optimización
- 🚧 Interfaz web para visualización

## 📝 Documentación de Investigación

- [Paper IEEE Format](docs/papers/paper_ieee/) - Formato IEEE estándar
- [Paper Extended](docs/papers/paper_extended/) - Versión extendida del análisis
- [Paper Current](docs/papers/paper_current/) - Versión actual en desarrollo
- [CLEI 2025 Submission](clei_submission_20250711_214745/) - Materiales para CLEI 2025

## 📚 Referencias

### Referencias Principales

1. **Amiri, M. H., et al. (2024)**. "Hippopotamus optimization algorithm: a novel nature-inspired optimization algorithm". *Scientific Reports* 14, 5032.
   - Algoritmo HO base implementado verbatim
   - Tres fases comportamentales modeladas
   - Rangos de parámetros respetados

2. **Potvin, J. Y. (2009)**. "State-of-the-art review—evolutionary algorithms for vehicle routing". *INFORMS Journal on Computing*, 21(4), 518-548.
   - Comparación con baselines establecidos
   - Métricas VRP estándar utilizadas

3. **Barros, T. D., & Everett, J. W. (2023)**. "Imitation Learning for Metaheuristic Optimization". *arXiv preprint*.
   - Base para integración IL con HO
   - Arquitectura de red neuronal

### Citar Este Trabajo

Si utilizas BioAlgoCompare en tu investigación:

```bibtex
@inproceedings{bioalgocompare2025,
  title={A Comprehensive Evaluation of Bio-inspired Algorithms for Vehicle Routing Problems},
  author={[Tu Nombre]},
  booktitle={Proceedings of CLEI 2025},
  year={2025},
  organization={CLEI}
}

@software{bioalgocompare2025,
  title={BioAlgoCompare: A Comprehensive Platform for Bio-inspired Algorithm Evaluation},
  author={[Tu Nombre]},
  year={2025},
  url={https://github.com/username/BioAlgoCompare}
}
```

## 📄 Licencia

MIT License - ver [LICENSE](LICENSE) para detalles.

---

<div align="center">
  <sub>Construido con ❤️ para la comunidad de optimización</sub>
</div>
