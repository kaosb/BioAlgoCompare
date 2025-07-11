# 🧬 BioAlgoCompare

[![Python Version](https://img.shields.io/badge/python-3.8%2B-blue)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/license-MIT-green)](LICENSE)
[![Algorithms](https://img.shields.io/badge/algorithms-16-orange)](algorithms/)
[![Conference](https://img.shields.io/badge/CISTI-2025-red)](docs/papers/)

Plataforma de evaluación estadística rigurosa para algoritmos metaheurísticos bioinspirados aplicados al Vehicle Routing Problem (VRP). Implementa benchmarking masivo con análisis estadístico avanzado siguiendo las mejores prácticas de investigación reproducible.

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
- [Uso](#-uso)
  - [Ejecución Básica](#ejecución-básica)
  - [Benchmarking](#benchmarking-y-análisis)
  - [Análisis Estadístico](#análisis-estadístico-de-resultados)
- [Algoritmos Implementados](#-algoritmos-implementados)
- [Arquitectura](#-arquitectura)
- [Documentación](#-documentación)
- [Contribuir](#-contribuir)
- [Licencia](#-licencia)

## ✨ Características

- **16 algoritmos bioinspirados** modernos (2016-2025)
- **Benchmarking masivo** con soporte para 1000+ ejecuciones
- **Análisis estadístico completo**: Friedman, Nemenyi, Wilcoxon, tamaños de efecto
- **Ejecución paralela** para máximo rendimiento
- **Checkpointing** para experimentos largos
- **Visualizaciones científicas** de calidad publicación
- **CLI unificado** con interfaz intuitiva
- **100% reproducible** con control de semillas

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

# Esto habilita el comando 'bioalgo' globalmente
bioalgo run --algorithm sho --instance A-n32-k5
```

## 📖 Uso

### Ejecución Básica

Ejecutar un algoritmo individual:

```bash
python scripts/analyze.py run --algorithm sho --instance A-n32-k5 --iterations 100 --population 30
```

Con múltiples ejecuciones y semilla fija:

```bash
python scripts/analyze.py run --algorithm egto --instance E-n51-k5 --runs 10 --seed 42
```

### Benchmarking y Análisis

Comparar múltiples algoritmos:

```bash
python scripts/analyze.py benchmark \
    --run-benchmark \
    --algorithms "sho,foa,egto,ewa,hho" \
    --instances "E-n22-k4,P-n16-k8,A-n32-k5" \
    --runs 30 \
    --parallel
```

### Benchmarking Masivo

Para experimentos de gran escala con 1000+ ejecuciones:

```bash
python scripts/analyze.py massive \
    --runs 1000 \
    --algorithm sho --algorithm egto --algorithm foa \
    --instances E-n22-k4 P-n16-k8 \
    --parallel \
    --resume \
    --output-dir results/exp_massive_jan2025
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
- Test post-hoc de Nemenyi con CD corregido
- Tamaños de efecto (A12, Cliff's delta)
- Diagramas de diferencias críticas
- Reportes detallados en Markdown

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

## 🧪 Algoritmos Implementados

El proyecto implementa **16 algoritmos metaheurísticos bioinspirados únicos**:

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

**Nota**: Los alias `hoa` (→ `sho`) y `fgo` (→ `fsa`) están disponibles para compatibilidad.

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

## 🎓 Contexto Académico

Este proyecto es parte de una investigación para la **Jornada Chilena de Computación 2025** (CISTI 2025), evaluando algoritmos bioinspirados recientes aplicados al VRP.

**Institución**: Universidad de Valparaíso
**Programa**: Magíster en Informática Aplicada

## 📝 Publicaciones

- [Paper CISTI v1](docs/papers/cisti_v1/) - Formato IEEE Conference
- [Paper CISTI v2](docs/papers/cisti_v2/) - Versión extendida

## 📄 Licencia

MIT License - ver [LICENSE](LICENSE) para detalles.

---

<div align="center">
  <sub>Construido con ❤️ para la comunidad de optimización</sub>
</div>
