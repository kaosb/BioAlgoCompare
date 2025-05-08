# 🧬 BioAlgoCompare

Plataforma para evaluación estadística rigurosa de algoritmos bio-inspirados. Implementa benchmarking masivo (1000+ ejecuciones), análisis estadístico avanzado y visualizaciones científicas para comparar metaheurísticas en problemas de optimización. Incluye checkpointing, intervalos de confianza y tests no paramétricos para conclusiones estadísticamente significativas.

[![Python Version](https://img.shields.io/badge/python-3.8%2B-blue)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/license-MIT-green)](LICENSE)

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
| HOA      | Hyena Optimization Algorithm | 2024 | Estrategias de caza cooperativa de las hienas |
| APO      | Artificial Piranha Optimization | 2024 | Comportamiento de caza en grupo de las pirañas |
| EGTO     | Enhanced Gorilla Troops Optimization | 2024 | Comportamiento social de gorilas con componentes de PSO |
| FGO      | Flamingo Optimization | 2025 | Comportamiento social y de filtración de los flamencos |
| FOA      | Fox Optimization Algorithm | 2024 | Estrategias de caza y territorialidad de los zorros |

## 🧱 Estructura del Proyecto

```
BioAlgoCompare/
├── algorithms/                # Implementaciones de algoritmos
│   ├── base.py                # Clase base para algoritmos
│   ├── hoa.py                 # Hyena Optimization Algorithm
│   ├── apo.py                 # Artificial Piranha Optimization
│   ├── egto.py                # Enhanced Gorilla Troops Optimization
│   ├── fgo.py                 # Flamingo Optimization
│   └── foa.py                 # Fox Optimization Algorithm
├── data/
│   └── vrp/                   # Instancias VRP (formato CVRPLIB)
├── problems/
│   └── vrp.py                 # Implementación del problema VRP
├── utils/
│   ├── benchmarking.py        # Sistema base de benchmarking
│   ├── statistical_analysis.py # Análisis estadístico
│   ├── vrp_operators.py       # Operadores específicos para VRP
│   ├── operators.py           # Operadores genéticos y utilidades
│   ├── visualization.py       # Visualización básica
│   ├── improved/              # Componentes avanzados
│   │   ├── enhanced_benchmarking.py # Benchmarking con checkpoints
│   │   ├── advanced_visualization.py # Visualizaciones avanzadas 
│   │   └── enhanced_statistics.py # Estadísticas rigurosas
├── results/                   # Resultados de experimentos
├── run.py                     # Ejecución de algoritmos individuales
├── run_massive.py             # Ejecución de benchmarks masivos
├── analyze_results.py         # Análisis de resultados
├── analyze_1000runs.py        # Análisis estadístico para 1000 ejecuciones
├── requirements.txt           # Dependencias del proyecto
└── README.md                  # Este archivo
```

## 📋 Instancias Disponibles

El proyecto incluye las siguientes instancias VRP estándar:

| Instancia | Nodos | Capacidad | Vehículos | Valor Óptimo |
|-----------|-------|-----------|-----------|--------------|
| A-n32-k5  | 32    | 100       | 5         | 784          |
| P-n16-k8  | 16    | 35        | 8         | 450          |
| E-n22-k4  | 22    | 6000      | 4         | 375          |
| B-n31-k5  | 31    | 100       | 5         | 672          |
| E-n51-k5  | 51    | 160       | 5         | 521          |

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

## 🚀 Uso

### Ejecución Básica

Para ejecutar un algoritmo específico en una instancia VRP:

```bash
python run.py --algorithm hoa --instance A-n32-k5 --iterations 100 --population 30
```

### Opciones de Ejecución Normal

| Opción | Descripción | Valor Predeterminado |
|--------|-------------|----------------------|
| `--algorithm`, `-a` | Algoritmo a ejecutar (`hoa`, `apo`, `egto`, `fgo`, `foa`, `all`) | (Requerido) |
| `--instance`, `-i` | Nombre de la instancia VRP (sin extensión) | (Requerido) |
| `--iterations`, `-n` | Número de iteraciones | 100 |
| `--population`, `-p` | Tamaño de la población | 30 |
| `--runs`, `-r` | Número de ejecuciones independientes | 1 |
| `--seed`, `-s` | Semilla para reproducibilidad | (Aleatorio) |
| `--visualize/--no-visualize` | Visualizar resultados | True |
| `--save/--no-save` | Guardar resultados | True |
| `--parallel/--no-parallel` | Ejecución paralela | False |

### Opciones de Benchmarking Masivo (1000 ejecuciones)

| Opción | Descripción | Valor Predeterminado |
|--------|-------------|----------------------|
| `--runs`, `-r` | Número de ejecuciones por algoritmo | 1000 |
| `--algorithm`, `-a` | Algoritmos a ejecutar | all |
| `--instances`, `-i` | Instancias a evaluar | E-n22-k4 |
| `--parallel/--no-parallel` | Ejecución paralela | True |
| `--resume/--no-resume` | Reanudar benchmark interrumpido | True |
| `--output-dir`, `-o` | Directorio de salida | auto |

### Ejemplos de Uso

#### Ejecutar todos los algoritmos en una instancia:

```bash
python run.py --algorithm all --instance A-n32-k5 --runs 5 --parallel
```

#### Ejecutar un algoritmo específico con parámetros personalizados:

```bash
python run.py --algorithm foa --instance P-n16-k8 --iterations 200 --population 50 --seed 42
```

#### Ejecutar un benchmark masivo con 1000 ejecuciones por algoritmo:

```bash
python run_massive.py --runs 1000 --algorithm hoa --algorithm egto --instances E-n22-k4 --parallel
```

#### Analizar resultados de un benchmark masivo:

```bash
python analyze_1000runs.py
```

## 📊 Resultados y Análisis

Los resultados se almacenan en el directorio `results/` con la siguiente estructura:

### Ejecuciones Normales
- `{instancia}_{timestamp}.csv`: Resultados detallados de cada ejecución
- `{instancia}_{timestamp}_summary.csv`: Resumen estadístico por algoritmo
- `{algoritmo}_{instancia}_solution.png`: Visualización de la mejor solución encontrada
- `{algoritmo}_{instancia}_convergence.png`: Curva de convergencia del algoritmo

### Benchmarks Masivos (1000 ejecuciones)
- `massive_{timestamp}/benchmark_state.json.gz`: Estado completo del benchmark con checkpoints
- `massive_{timestamp}/massive_benchmark_summary.csv`: Resumen estadístico del benchmark
- `massive_{timestamp}/massive_benchmark_report.html`: Informe HTML interactivo
- `statistical_analysis_{timestamp}/`: Análisis estadístico avanzado con visualizaciones

## 🧠 Metodología

- **Codificación**: Adaptación de algoritmos continuos mediante codificación ordinal → se ordenan los valores reales para generar una permutación de visitas.
- **Evaluación**: Decodificación de soluciones respetando restricciones de capacidad vehicular.
- **Benchmark Masivo**: Ejecución de 1000 repeticiones por algoritmo con checkpoint y recuperación.
- **Análisis Estadístico**: Tests no paramétricos (Kruskal-Wallis, Mann-Whitney), corrección de Bonferroni, intervalos de confianza del 95%.
- **Visualización Científica**: Boxplots, distribuciones, curvas de convergencia con intervalos de confianza.

## 🔍 Características Técnicas

- **Arquitectura Modular**: Sistema de benchmarking avanzado para muestras grandes.
- **Paralelización**: Ejecución paralela eficiente con gestión de procesos.
- **Reproducibilidad**: Control de semillas aleatorias para garantizar resultados reproducibles.
- **Checkpoint y Recuperación**: Capacidad de interrumpir y reanudar benchmarks masivos.
- **Visualización Avanzada**: Herramientas científicas para visualizar distribuciones e intervalos de confianza.
- **CLI Profesional**: Interfaces de línea de comandos robustas para todos los componentes.

## 👥 Contribuir

1. Fork el repositorio
2. Crea una rama para tu característica (`git checkout -b feature/nueva-caracteristica`)
3. Haz commit de tus cambios (`git commit -am 'Añadir nueva característica'`)
4. Push a la rama (`git push origin feature/nueva-caracteristica`)
5. Crea un nuevo Pull Request

## 📚 Créditos

Desarrollado como parte de una investigación académica para el Magíster en Informática Aplicada – Universidad de Valparaíso.

## 📄 Licencia

MIT – Uso académico libre con atribución.
