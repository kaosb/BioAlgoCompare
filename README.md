# 🧬 Optimización Metaheurística Bioinspirada para VRP

Este proyecto forma parte de una investigación académica para la **Jornada Chilena de Computación 2025**, cuyo objetivo es **evaluar y comparar algoritmos bioinspirados recientes (2024–2025)** aplicados al **Vehicle Routing Problem (VRP)**.

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
bio-vrp-paper/
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
│   ├── operators.py           # Operadores genéticos y utilidades
│   └── visualization.py       # Visualización de soluciones
├── results/                   # Resultados de experimentos
├── run.py                     # Script principal de ejecución
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
git clone https://github.com/usuario/bio-vrp-paper.git
cd bio-vrp-paper

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

### Opciones Disponibles

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

### Ejemplos de Uso

#### Ejecutar todos los algoritmos en una instancia:

```bash
python run.py --algorithm all --instance A-n32-k5 --runs 5
```

#### Ejecutar un algoritmo específico con parámetros personalizados:

```bash
python run.py --algorithm foa --instance P-n16-k8 --iterations 200 --population 50 --seed 42
```

#### Prueba de rendimiento con instancia grande:

```bash
python run.py --algorithm egto --instance E-n51-k5 --iterations 300 --population 50
```

## 📊 Resultados y Análisis

Los resultados se almacenan en el directorio `results/` con la siguiente estructura:

- `{instancia}_{timestamp}.csv`: Resultados detallados de cada ejecución
- `{instancia}_{timestamp}_summary.csv`: Resumen estadístico por algoritmo
- `{algoritmo}_{instancia}_solution.png`: Visualización de la mejor solución encontrada
- `{algoritmo}_{instancia}_convergence.png`: Curva de convergencia del algoritmo

## 🧠 Metodología

- **Codificación**: Adaptación de algoritmos continuos mediante codificación ordinal → se ordenan los valores reales para generar una permutación de visitas.
- **Evaluación**: Decodificación de soluciones respetando restricciones de capacidad vehicular.
- **Análisis**: Comparación estadística mediante pruebas de Friedman, Wilcoxon post-hoc, boxplots y curvas de convergencia.

## 🔍 Características Técnicas

- **Interfaz Común**: Todos los algoritmos implementan una interfaz común para facilitar la comparación.
- **Reproducibilidad**: Control de semillas aleatorias para garantizar resultados reproducibles.
- **Visualización**: Herramientas para visualizar soluciones y analizar convergencia.
- **CLI Profesional**: Interfaz de línea de comandos con opciones configurables mediante `click`.

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
