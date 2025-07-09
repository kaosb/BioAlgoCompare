

# Starling Murmuration Optimizer (SMO)

## Descripción General

El Starling Murmuration Optimizer (SMO) es un algoritmo bioinspirado propuesto por Zamani, Nadimi-Shahraki y Gandomi en 2022. Se basa en el comportamiento de murmullos de estorninos (*Sturnus vulgaris*), aprovechando estrategias de **separación**, **cohesión** y **alineamiento**, junto con fases de **diving** y **whirling** para explorar y explotar el espacio de soluciones.

## Implementación y Mejoras

- Adaptado al VRP usando operadores discretos sobre rutas:
  - **Separating**: swap aleatorio de dos clientes.
  - **Diving**: 2-opt reversible en una ruta seleccionada.
  - **Whirling**: reubicación de un cliente entre rutas.
- Construcción dinámica de flocks basada en calidad (top 50%).
- Parámetros:
  - Número de flocks `k = 10`
  - Separación cuántica `λ = 20`
  - Dividing threshold `µ = 0.5`
  - Fases: separación inicial, diving si calidad < media, whirling si ≥ media.

## Pseudocódigo

```text
Inicializar población de estorninos con soluciones VRP aleatorias
Determinar personal_best de cada estornino
Para t = 1 hasta T:
  Formar flocks dinámicos según fitness (k grupos)
  Calcular calidad de cada flock
  Para cada estornino s:
    Si s en indices de separación:
      aplicar swap (Separating)
    Sino:
      Si quality(flock) < media:
        aplicar 2-opt (Diving)
      Sino:
        aplicar reubicación (Whirling)
    Actualizar personal_best de s
  Actualizar leader global y registrar en convergence_curve
Retornar leader
```

## Análisis de Rendimiento

| Iteraciones | Fitness mínimo | Fitness medio | Std. | Tiempo medio |
|-------------|----------------|---------------|------|--------------|
| 100         | [valor]        | [valor]       | [n]  | [t] s        |
| 1 000       | [valor]        | [valor]       | [n]  | [t] s        |
| 10 000      | [valor]        | [valor]       | [n]  | [t] s        |

## Características de Convergencia

- Mejora rápida en la fase de separación.
- Diving refina soluciones locales de forma efectiva.
- Whirling introduce diversificación evitando óptimos locales.

## Fortalezas y Limitaciones

**Fortalezas**
- Equilibrio claro entre exploración y explotación.
- Operadores discretos nativos para VRP.
- Flocks dinámicos adaptados a la calidad.

**Limitaciones**
- Sensible al número de flocks y tamaño de población.
- Overhead de agrupación en cada iteración.

## Recomendaciones de Uso

- Usar `population_size ≥ 50` y `T ≥ 1000` para instancias VRP medianas.
- Ajustar `λ` y `µ` tras pruebas iniciales.
- Combinar con heurísticas locales en hibridación.

## Ejemplo de Uso

```python
from algorithms.smo import SMO

algo = SMO(problem, population_size=50, max_iterations=1000, seed=42)
best = algo.execute()
print("Mejor fitness SMO:", best.fitness())
```

## Referencias

- Zamani, H., Nadimi-Shahraki, M. H., & Gandomi, A. H. (2022). Starling murmuration optimizer: A novel bio-inspired algorithm for global and engineering optimization. *Computer Methods in Applied Mechanics and Engineering, 392*, 114616. https://doi.org/10.1016/j.cma.2022.114616
- [Análisis comparativo de todos los algoritmos](../../COMPARATIVA_GLOBAL.md)
