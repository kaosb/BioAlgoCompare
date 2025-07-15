# Raven Roosting Optimization (RRO)

## Descripción General

El Raven Roosting Optimization (RRO) es un algoritmo bioinspirado propuesto por Brabazon, Cui y O’Neill en 2016. Se basa en el comportamiento de agrupamiento y dormidero de los cuervos (*Corvus corax*), donde las aves se reúnen en sitios fijos (roosts) para intercambiar información sobre fuentes de alimento. El algoritmo simula:

- **Roosting site**: Punto de encuentro (solución líder) donde se congregan las mejores aves.
- **Percepción individual**: Cada cuervo explora su entorno local para detectar mejores soluciones.
- **Reclutamiento**: Algunos cuervos siguen al líder dentro de un radio definido, mientras otros exploran basados en su experiencia personal.

## Implementación y Mejoras

- Implementado en Python siguiendo el pseudocódigo de la versión RRO0 del artículo.
- Parámetros predeterminados (RRO0):
  - `Rpcpt = 3.6 * R * sqrt(D)`
  - `Npcpt = 10`, `Nsteps = 10`
  - `Percfollow = 0.2`, `Pstop = 0.1`
- Cada cuervo gestiona su `personal_best_position` y sigue al **LEADER** con probabilidad `Percfollow`.
- Percepción local (`Npcpt`) y detención anticipada (`Pstop`) para mejorar eficiencia.

## Pseudocódigo

```text
Inicializar población de cuervos con posiciones aleatorias
Para cada cuervo: personal_best = posición inicial

Para t = 1 hasta T:
  Calcular LEADER = cuervo con mejor fitness
  Para cada cuervo r_i en la población:
    Si random() < Percfollow:
      target = LEADER.position
      radio = Rleader
    Sino:
      target = r_i.personal_best_position
      radio = Rpcpt
    Llamar a r_i.move(target, radio, Npcpt, Nsteps, Pstop)
  Actualizar LEADER global
  Registrar fitness de LEADER en convergence_curve

Retornar LEADER
```

## Análisis de Rendimiento

| Iteraciones | Fitness mínimo | Fitness medio | Std. | Tiempo medio |
|-------------|----------------|---------------|------|--------------|
| 100         | [valor]        | [valor]       | [n]  | [t] s        |
| 1 000       | [valor]        | [valor]       | [n]  | [t] s        |
| 10 000      | [valor]        | [valor]       | [n]  | [t] s        |

## Características de Convergencia

- Convergencia rápida en las primeras iteraciones gracias al seguimiento al líder.
- La percepción local evita ciclos de búsqueda repetitiva.
- Buen balance entre exploración global (exploradores) y explotación (seguidores del líder).

## Fortalezas y Limitaciones

**Fortalezas**
- Modelo claro de comunicación líder-seguidor.
- Evita estancamientos con detención anticipada.
- Fácil de parametrizar y extender.

**Limitaciones**
- Sensible al radio de percepción (`Rpcpt`).
- Pocas estrategias de diversificación fuera del radio local.

## Recomendaciones de Uso

- Usar `Percfollow` = 0.2–0.3 y `Pstop` = 0.1 para problemas continuos.
- Ajustar `Npcpt` (5–15) según dimensionalidad.
- Para soluciones de alta calidad, ejecutar ≥ 1 000 iteraciones.

## Ejemplo de Uso

```python
from algorithms.rro import RRO

algo = RRO(problem, population_size=30, max_iterations=1000, seed=42)
best = algo.execute()
print("Mejor fitness RRO:", best.fitness())
```

## Referencias

- Brabazon, A., Cui, W., & O’Neill, M. (2016). The Raven Roosting Optimisation Algorithm. *Soft Computing*, 20(2), 525–545. https://doi.org/10.1007/s00500-014-1520-5
- [Análisis comparativo de todos los algoritmos](../../COMPARATIVA_GLOBAL.md)
