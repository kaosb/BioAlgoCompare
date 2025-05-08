# Optimización Metaheurística para VRP

Este repositorio contiene implementaciones de algoritmos metaheurísticos modernos para resolver problemas de optimización, específicamente el Problema de Ruteo de Vehículos (VRP).

## Algoritmos Implementados

- **HOA (Hyena Optimization Algorithm)**: Algoritmo inspirado en el comportamiento de caza de las hienas.
- **APO (Artificial Piranha Optimization)**: Algoritmo basado en el comportamiento de caza de las pirañas.
- **EGTO (Enhanced Gorilla Troops Optimization)**: Versión mejorada del algoritmo GTO con componentes de PSO.
- **FGO (Flamingo Optimization)**: Algoritmo inspirado en el comportamiento social de los flamencos.
- **FOA (Fox Optimization Algorithm)**: Algoritmo basado en las estrategias de caza de los zorros.

## Estructura del Proyecto

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
│   └── vrp/                   # Instancias VRP
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

## Requisitos

- Python 3.8+
- Dependencias listadas en `requirements.txt`

## Instalación

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

## Uso

Para ejecutar un algoritmo específico en una instancia VRP:

```bash
python run.py --algorithm hoa --instance A-n32-k5 --iterations 100 --population 30
```

Opciones disponibles:

- `--algorithm`, `-a`: Algoritmo a ejecutar (`hoa`, `apo`, `egto`, `fgo`, `foa`, `all`)
- `--instance`, `-i`: Nombre de la instancia VRP (sin extensión)
- `--iterations`, `-n`: Número de iteraciones (default: 100)
- `--population`, `-p`: Tamaño de la población (default: 30)
- `--runs`, `-r`: Número de ejecuciones independientes (default: 1)
- `--seed`, `-s`: Semilla para reproducibilidad
- `--visualize/--no-visualize`: Visualizar resultados (default: True)
- `--save/--no-save`: Guardar resultados (default: True)

## Ejemplos

Ejecutar todos los algoritmos en una instancia:

```bash
python run.py --algorithm all --instance A-n32-k5 --runs 5
```

Ejecutar un algoritmo específico con parámetros personalizados:

```bash
python run.py --algorithm foa --instance P-n16-k8 --iterations 200 --population 50 --seed 42
```

## Contribuir

1. Fork el repositorio
2. Crea una rama para tu característica (`git checkout -b feature/nueva-caracteristica`)
3. Haz commit de tus cambios (`git commit -am 'Añadir nueva característica'`)
4. Push a la rama (`git push origin feature/nueva-caracteristica`)
5. Crea un nuevo Pull Request
