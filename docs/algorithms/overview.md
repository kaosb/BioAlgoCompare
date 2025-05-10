# Visión General de Algoritmos Metaheurísticos Implementados

Este documento proporciona una visión general de todos los algoritmos metaheurísticos bioinspirados implementados en BioAlgoCompare, junto con sus características principales y rendimiento comparativo.

## Algoritmos Disponibles

| Acrónimo | Nombre Completo | Año | Inspiración Biológica |
|----------|-----------------|------|----------------------|
| SHO      | Spotted Hyena Optimizer | 2017 | Estrategias de caza cooperativa de las hienas |
| APO      | Artificial Protozoa Optimizer | 2024 | Comportamiento de movimiento y división de protozoarios |
| EGTO     | Enhanced Gorilla Troops Optimization | 2024 | Comportamiento social de gorilas con componentes de PSO |
| FSA      | Flamingo Search Algorithm | 2021 | Comportamiento social y de filtración de los flamencos |
| FOA      | Fossa Optimization Algorithm | 2024 | Estrategias de caza y territorialidad de las fosasas |
| WOA      | Whale Optimization Algorithm | 2016 | Estrategia de alimentación de ballenas jorobadas |
| HHO      | Harris Hawks Optimization | 2019 | Comportamiento de caza cooperativa de halcones |
| MRFO     | Manta Ray Foraging Optimization | 2020 | Técnicas de alimentación de mantarrayas |
| SMA      | Slime Mould Algorithm | 2020 | Comportamiento del moho viscoso buscando alimento |
| GTO      | Gorilla Troops Optimization | 2021 | Jerarquía y comportamiento social de gorilas |
| EWA      | Earthworm Algorithm | 2018 | Movimientos de los gusanos de tierra |
| AHA      | Artificial Hummingbird Algorithm | 2022 | Comportamiento de vuelo y forrajeo de colibríes |
| RRO      | Raven Roosting Optimization | 2016 | Comportamiento de dormidero de los cuervos |
| GVOA     | Griffon Vultures Optimization Algorithm | 2025 | Comportamiento de vuelo termal de buitres leonados |
| SMO      | Starling Murmuration Optimizer | 2022 | Murmullos y comportamiento emergente de estorninos |

## Rendimiento Comparativo

Basado en análisis exhaustivos, presentamos un resumen comparativo del rendimiento de los algoritmos:

### Mejor Fitness Obtenido (Instancia E-n22-k4)

| Ranking | Algoritmo | Mejor Fitness | Gap al Óptimo | Iteraciones | Tiempo (s) |
|---------|-----------|---------------|---------------|-------------|------------|
| 1       | FOA       | 396.00        | 5.5%          | 10000       | 16.72      |
| 2       | WOA       | 411.32        | 9.6%          | 10000       | 6.58       |
| 3       | GTO       | 420.32        | 12.0%         | 10000       | 5.24       |
| 4       | EWA       | 448.86        | 19.6%         | 10000       | 8.16       |
| 5       | SMA       | 453.17        | 20.8%         | 1000        | 3.98       |
| 6       | EGTO      | 459.08        | 22.3%         | 1000        | 0.37       |
| 7       | HOA       | 466.02        | 24.2%         | 1000        | 1.14       |
| 8       | APO       | 469.69        | 25.2%         | 1000        | 0.53       |
| 9       | MRFO      | 470.19        | 25.3%         | 1000        | 0.63       |
| 10      | FGO       | 478.50        | 27.5%         | 1000        | 2.66       |
| 11      | HHO       | 491.71        | 31.0%         | 1000        | 0.59       |

*Nota: El óptimo conocido para E-n22-k4 es 375.28*

### Clasificación por Patrones de Convergencia

Basado en el comportamiento observado, los algoritmos se pueden categorizar en 4 patrones distintos:

#### Patrón 1: Mejora Continua Sostenida
**Algoritmos**: FOA, GTO, EWA
- Muestran mejora constante en cada orden de magnitud de iteraciones
- FOA destaca con una mejora dramática entre 100-1000 iteraciones
- GTO mantiene tasa de mejora relativamente constante
- EWA progresa constantemente, con mejora acentuada entre 100-1000 iteraciones

#### Patrón 2: Convergencia No Monótona
**Algoritmos**: WOA, HOA, FGO
- WOA muestra mejora significativa inicial pero estancamiento intermedio
- HOA tiene mejora espectacular en etapa temprana pero luego deterioro leve
- FGO mejora rápidamente al inicio, pero luego la calidad se deteriora

#### Patrón 3: Inicio Lento, Mejora Tardía
**Algoritmos**: SMA, APO 
- SMA muestra mejora modesta inicial pero aceleración notable en etapas avanzadas
- APO sigue patrón similar, con la mayor parte de mejora en etapas tardías

#### Patrón 4: Mejora Modesta y Gradual
**Algoritmos**: MRFO, HHO
- Muestran mejoras moderadas pero consistentes
- Sin fases de aceleración o desaceleración dramáticas
- Mejora total más limitada que otros grupos

### Eficiencia Computacional

Ranking de algoritmos por relación calidad/tiempo (con 10000 iteraciones):

1. **GTO**: Mejor balance calidad-tiempo
2. **WOA**: Excelente rendimiento con tiempo moderado
3. **EWA**: Buen rendimiento con tiempo moderado
4. **FOA**: Mejor calidad pero tiempo computacional elevado

## Recomendaciones de Uso

### Por Tiempo Disponible:
- **Tiempo limitado (<0.1s)**: EGTO con 100 iteraciones
- **Tiempo moderado (~1s)**: WOA o GTO con 1000 iteraciones
- **Sin restricción de tiempo (~15s)**: FOA con 10000 iteraciones

### Por Tipo de Aplicación:
- **Aplicaciones en tiempo real**: WOA con 100-1000 iteraciones
- **Planificación offline con énfasis en calidad**: FOA con 10000 iteraciones
- **Balance calidad/variabilidad**: EWA o GTO con 10000 iteraciones

## Implementación en el Sistema

Todos los algoritmos implementan la interfaz base definida en `algorithms/base.py`, asegurando una API consistente:

```python
# Ejemplo de uso de los algoritmos
from algorithms.foa import FOA
from problems.vrp import VRPProblem

# Cargar problema
problem = VRPProblem("data/vrp/E-n22-k4.vrp")

# Inicializar algoritmo (ejemplo con FOA)
algorithm = FOA(
    problem=problem,
    population_size=30,
    max_iterations=1000,
    seed=42
)

# Ejecutar optimización
best_solution = algorithm.execute()

# Obtener fitness y convergencia
fitness = best_solution.fitness()
convergence_curve = algorithm.get_convergence_curve()
```

## Referencias

Para ver el pseudocódigo detallado de cada algoritmo, consulte el documento [Pseudocódigo de Algoritmos](pseudocode.md).

Para análisis detallados del rendimiento de cada algoritmo, consulte:
- [Análisis del Impacto de Iteraciones](../analysis/iteration_impact.md)
- [Análisis Comparativo Exhaustivo](../analysis/comparison.md)
- Documentación individual de cada algoritmo en la carpeta [individual](individual/)