

# Griffon Vultures Optimization Algorithm (GVOA)

## Descripción General

El Griffon Vultures Optimization Algorithm (GVOA) es un algoritmo bioinspirado propuesto por Hasan, Mohammed y Abdul en 2025 en *Expert Systems with Applications*. Se inspira en el comportamiento de vuelo termal de los buitres leonados (*Gyps fulvus*), alternando fases de **soaring** (exploración mediante corrientes térmicas ascendentes) y **carcass feeding** (explotación intensiva alrededor de las ubicaciones descubiertas con alta aptitud). Introduce un mecanismo de **memoria de carcasa** para reforzar regiones prometedoras y evitar revisitas redundantes.

## Implementación y Mejoras

- Implementado en Python adaptado al problema de VRP.
- Se modelan las fases de forrajeo:
  - **Soaring**: búsqueda global aprovechando vectores de viento térmico.
  - **Carcass Feeding**: búsqueda local intensiva alrededor del líder/global best.
- Memoria de carcasa que graba las mejores soluciones previas.
- Parámetros principales:
  - `Rpcpt = 3.6 * R * sqrt(D)`
  - `Rleader = Rpcpt`
  - `Npcpt = 10`, `Nsteps = 10`
  - `Percfollow = 0.2`, `Pstop = 0.1`

## Pseudocódigo

```text
Inicializar población de buitres con soluciones VRP aleatorias
Para cada buitre: personal_best = posición inicial

Para t = 1 hasta T:
  leader = mejor solución global
  informed = top 50% de la población por fitness
  Para cada buitre v:
    Si random() < Percfollow:
      target = leader.position, radio = Rleader
    Sino:
      target = v.personal_best_position, radio = Rpcpt
    Ejecutar v.move(target, radio, Npcpt, Nsteps, Pstop, t, T)
  Actualizar leader global y registrar fitness en convergence_curve

Retornar leader
```

## Análisis de Rendimiento

| Iteraciones | Fitness mínimo | Fitness medio | Std. | Tiempo medio |
|-------------|----------------|---------------|------|--------------|
| 100         | [valor]        | [valor]       | [n]  | [t] s        |
| 1 000       | [valor]        | [valor]       | [n]  | [t] s        |
| 10 000      | [valor]        | [valor]       | [n]  | [t] s        |

## Características de Convergencia

- Fuerte exploración en fases tempranas gracias al soaring.
- Explotación localizada efectiva alrededor del líder.
- Memoria de carcasa reduce ciclos de búsqueda redundantes.

## Fortalezas y Limitaciones

**Fortalezas**
- Balance dinámico entre exploración y explotación.
- Memoria explícita para evitar re-visitas.
- Estructura modular fácil de extender.

**Limitaciones**
- Sensible a la exactitud de `R` y tamaño de población.
- Coste computacional mayor por gestión de memoria.

## Recomendaciones de Uso

- Usar `population_size ≥ 30` y `T ≥ 500` para entornos VRP medianos.
- Ajustar `Pstop` para problemas ruidosos.
- Combinar con otras metaheurísticas en enfoque híbrido.

## Ejemplo de Uso

```python
from algorithms.gvoa import GVOA

algo = GVOA(problem, population_size=30, max_iterations=1000, seed=42)
best = algo.execute()
print("Mejor fitness GVOA:", best.fitness())
```

## Referencias

- Hasan, D. O., Mohammed, H. M., & Abdul, Z. Kh. (2025). Griffon vultures optimization algorithm for solving optimization problems. *Expert Systems with Applications, 276*, 127206. https://doi.org/10.1016/j.eswa.2025.127206
- [Análisis comparativo de todos los algoritmos](../../COMPARATIVA_GLOBAL.md)
