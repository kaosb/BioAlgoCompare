

# Artificial Hummingbird Algorithm (AHA)

## Descripción General

El Artificial Hummingbird Algorithm (AHA) es un algoritmo bioinspirado propuesto por Zhao, Wang y Mirjalili en 2022. Simula las habilidades únicas de vuelo y comportamiento de búsqueda de alimento del colibrí (hummingbird), incorporando tres tipos de vuelo (axial, diagonal y omnidireccional) y tres estrategias de forrajeo (guiado, territorial y migratorio), así como una tabla de memoria que evita el re-visitado de soluciones.

## Implementación y Mejoras

- Implementado en Python siguiendo fielmente el pseudocódigo del paper original.
- Se modelan todos los tipos de vuelo y estrategias de forrajeo.
- Se incluye una tabla de memoria (con discretización) para registrar las regiones ya exploradas.
- Posición actual y fitness se actualizan condicionalmente según mejora.
- El tipo de vuelo y la estrategia de forrajeo se seleccionan de forma estocástica.

## Pseudocódigo

```text
Inicializar población de colibríes aleatoriamente
Crear tabla de memoria vacía

Para t = 1 hasta T:
  Para cada colibrí:
    Seleccionar tipo de vuelo (axial, diagonal u omnidireccional)
    Seleccionar modo de forrajeo:
      - Guiado: moverse hacia el mejor
      - Territorial: perturbación local
      - Migratorio: hacia una posición aleatoria
    Calcular nueva posición y evaluar fitness
    Si nueva posición no está en memoria y mejora:
      Aceptar nuevo estado
      Registrar en memoria
Actualizar el mejor individuo global
```

## Análisis de Rendimiento

| Iteraciones | Fitness mínimo | Fitness medio | Std. | Tiempo medio |
|-------------|----------------|----------------|------|---------------|
| 100         | [valor]        | [valor]        | [n]  | [t] s         |
| 1 000       | [valor]        | [valor]        | [n]  | [t] s         |
| 10 000      | [valor]        | [valor]        | [n]  | [t] s         |

## Características de Convergencia

- Mejora progresiva con estabilidad desde 1 000 iteraciones.
- En entornos ruidosos, el uso de memoria evita ciclos prematuros.
- Muestra capacidad para escapar de óptimos locales mediante migración.

## Fortalezas y Limitaciones

**Fortalezas**
- Balance adecuado entre exploración y explotación.
- Evita la reexploración mediante memoria explícita.
- Comportamiento biológicamente plausible y diverso.

**Limitaciones**
- Tiempo ligeramente mayor que algoritmos más simples.
- Efectividad sensible al tamaño de la memoria y paso.

## Recomendaciones de Uso

- Usar con ≥1 000 iteraciones para observar convergencia estable.
- Ajustar discretización si se aplica a problemas continuos con mucha precisión.
- Recomendado cuando se desea diversidad de búsqueda con baja redundancia.

## Ejemplo de Uso

```python
from algorithms.aha import AHA

algo = AHA(problem, population_size=30, max_iterations=1000, seed=42)
best = algo.execute()
print("Best fitness:", best.fitness())
```

## Referencias

- Zhao, W., Wang, L., & Mirjalili, S. (2022). Artificial hummingbird algorithm: A new bio-inspired optimizer with its engineering applications. *Computer Methods in Applied Mechanics and Engineering, 388*, 114194. https://doi.org/10.1016/j.cma.2021.114194

- [Análisis comparativo de todos los algoritmos](../../COMPARATIVA_GLOBAL.md)