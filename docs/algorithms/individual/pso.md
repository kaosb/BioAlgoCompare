# Particle Swarm Optimization (PSO)

## Descripción General

Particle Swarm Optimization (PSO) es una metaheurística de computación evolutiva basada en poblaciones, propuesta originalmente por James Kennedy y Russell Eberhart en 1995. El algoritmo se inspira en el comportamiento social de las bandadas de aves o los bancos de peces. En PSO, un conjunto de soluciones candidatas, denominadas "partículas", se mueven a través del espacio de búsqueda para encontrar la solución óptima.

### Inspiración Social

El movimiento de cada partícula está influenciado por dos componentes principales:
- **Experiencia Cognitiva**: La tendencia de una partícula a volver a la mejor posición que ha encontrado hasta ahora (`pbest`).
- **Experiencia Social**: La tendencia de una partícula a moverse hacia la mejor posición encontrada por cualquier partícula en toda la bandada (`gbest`).
- **Inercia**: La tendencia de una partícula a continuar en su dirección de movimiento actual.

## Implementación y Mejoras

**Fecha de última actualización:** 14 de julio de 2025

### Cambios Implementados

Esta es una implementación canónica de PSO, a menudo utilizando un factor de constricción para asegurar la convergencia.

1.  **Representación de Partículas**:
    -   Cada `Particle` tiene una `position` (solución candidata), una `velocity` que dirige su movimiento, y una `pbest_position` que almacena su mejor posición histórica.
    -   La representación de la posición es un vector continuo en [0, 1], adecuado para decodificación en problemas como el VRP.

2.  **Ecuaciones de Movimiento**:
    -   La velocidad se actualiza combinando la inercia actual, el componente cognitivo (atracción hacia `pbest`) y el componente social (atracción hacia `gbest`).
    -   Se utiliza un **factor de inercia** (`w`) para equilibrar la exploración global y la explotación local. En esta implementación, puede ser adaptativo.
    -   La posición se actualiza sumando la nueva velocidad a la posición actual.

3.  **Control de Parámetros**:
    -   **Sujeción de Velocidad (Velocity Clamping)**: La velocidad de cada partícula se limita a un rango `[-v_max, v_max]` para evitar que las partículas se alejen demasiado del espacio de búsqueda y el algoritmo diverja.
    -   **Límites de Posición**: Las posiciones se mantienen dentro de los límites del espacio de búsqueda (ej. [0, 1]) después de cada actualización.

## Pseudocódigo

```
Inicializar población de N partículas con posiciones y velocidades aleatorias
Para cada partícula: pbest = posición inicial
gbest = la mejor posición en toda la población

Para t = 1 hasta T (iteraciones):
  Para cada partícula i:
    # Actualizar velocidad
    r1, r2 = números aleatorios en [0, 1]
    velocidad_cognitiva = c1 * r1 * (pbest_i - posicion_i)
    velocidad_social = c2 * r2 * (gbest - posicion_i)
    velocidad_i = w * velocidad_i + velocidad_cognitiva + velocidad_social

    # Sujetar velocidad a [-v_max, v_max]

    # Actualizar posición
    posicion_i = posicion_i + velocidad_i

    # Sujetar posición a los límites del dominio

    # Evaluar fitness y actualizar mejores posiciones
    Evaluar fitness(posicion_i)
    Si fitness(posicion_i) es mejor que fitness(pbest_i):
      pbest_i = posicion_i
    Si fitness(pbest_i) es mejor que fitness(gbest):
      gbest = pbest_i

Retornar gbest
```

## Fortalezas y Limitaciones

### Fortalezas
-   Conceptualmente simple y fácil de implementar.
-   Pocos parámetros que ajustar en su versión básica.
-   Computacionalmente muy eficiente.
-   Buena capacidad de convergencia rápida en las primeras etapas.

### Limitaciones
-   Puede converger prematuramente a óptimos locales, especialmente en problemas multimodales complejos.
-   El rendimiento puede degradarse en problemas de muy alta dimensionalidad.
-   La versión básica no tiene un mecanismo garantizado para escapar de óptimos locales una vez que la bandada ha convergido.

## Recomendaciones de Uso
-   **Parámetros**: Los valores `w=0.729`, `c1=1.49445`, `c2=1.49445` (usando el enfoque del factor de constricción) son un buen punto de partida y a menudo no requieren ajuste.
-   **Topologías**: Para problemas más complejos, se pueden explorar diferentes topologías de vecindario (como anillo o estrella) en lugar de usar un `gbest` global para ralentizar la convergencia y mejorar la exploración.
-   **Hibridación**: Al igual que los GAs, PSO se beneficia de la hibridación con búsquedas locales para mejorar el ajuste fino de las soluciones.

## Ejemplo de Uso

```python
from algorithms.pso import PSO
from problems.vrp import VRPProblem

# Cargar problema
problem = VRPProblem("data/vrp/P-n16-k8.vrp")

# Inicializar algoritmo
pso = PSO(
    problem=problem,
    population_size=30,
    max_iterations=1000,
    seed=42
)

# Ejecutar optimización
best_solution, best_fitness, convergence = pso.execute()

# Obtener fitness y convergencia
print("Mejor fitness PSO:", best_fitness)
```

## Referencias

- Kennedy, J., & Eberhart, R. (1995). Particle Swarm Optimization. In *Proceedings of ICNN'95 - International Conference on Neural Networks* (Vol. 4, pp. 1942-1948). doi: 10.1109/ICNN.1995.488968

- Para análisis comparativo con otros algoritmos, consulte: [Análisis Comparativo Exhaustivo](../../analysis/comparison.md)

---

*Última actualización: 14 de julio de 2025*
