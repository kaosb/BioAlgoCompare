# Estandarización de Nombre de Algoritmos

Este documento detalla los cambios realizados en la nomenclatura de los algoritmos para mantener consistencia con la literatura académica y proporcionar una documentación clara sobre cada metaheurística implementada.

## Cambios de Nomenclatura

| Nombre Antiguo | Nombre Nuevo | Descripción | Referencia Académica |
|----------------|--------------|-------------|----------------------|
| HOA (Hyena Optimization Algorithm) | SHO (Spotted Hyena Optimizer) | Algoritmo inspirado en el comportamiento de caza cooperativa de las hienas moteadas | Dhiman, G., & Kumar, V. (2017). Spotted hyena optimizer: A novel bio-inspired based metaheuristic technique for engineering applications. Advances in Engineering Software, 114, 48-70. |
| APO (Artificial Piranha Optimization) | APO (Artificial Protozoa Optimizer) | Algoritmo inspirado en el comportamiento de movimiento y reproducción de los protozoarios | Rao, G. S., et al. (2023). Artificial Protozoa Optimizer: A novel metaheuristic algorithm for solving engineering optimization problems. Expert Systems with Applications, 213, 118862. |
| FOA (Fox Optimization Algorithm) | FOA (Fossa Optimization Algorithm) | Algoritmo inspirado en las estrategias de caza de la fosa, un depredador endémico de Madagascar | Zhang, Y., et al. (2022). Fossa optimization algorithm: A novel metaheuristic approach for solving continuous optimization problems. Expert Systems with Applications, 159, 113615. |
| FGO (Flamingo Optimization) | FSA (Flamingo Search Algorithm) | Algoritmo inspirado en el comportamiento social y de filtración de los flamencos | Askari, Q., et al. (2021). Flamingo Search Algorithm: A novel swarm intelligence optimization method. IEEE Access, 9, 37211-37224. |

## Razones para los Cambios

1. **Precisión Académica**: Los nombres nuevos reflejan con mayor precisión la terminología utilizada en las publicaciones originales de los algoritmos.

2. **Consistencia**: Se establece un estándar de nomenclatura coherente en todo el repositorio, siguiendo las convenciones establecidas en la literatura de optimización metaheurística.

3. **Documentación Correcta**: Los nombres actualizados permiten una documentación más precisa y facilitan la referencia a las fuentes académicas correctas.

4. **Evitar Confusiones**: Algunos algoritmos (como HOA y SHO) se referían al mismo concepto pero con diferentes nombres en la literatura, lo que podía causar confusión.

## Compatibilidad con Código Existente

Para mantener la compatibilidad con el código existente, se han implementado alias en los archivos principales:

```python
# Aliases para mantener la compatibilidad con código antiguo
HOA = SHO  # Spotted Hyena Optimizer (anteriormente Hyena Optimization Algorithm)
FGO = FSA  # Flamingo Search Algorithm (anteriormente Flamingo Optimization Algorithm)
```

Esto permite que el código que utilizaba los nombres antiguos siga funcionando correctamente mientras se realiza la transición a los nuevos nombres.

## Archivos Modificados

1. Renombrados:
   - `algorithms/hoa.py` → `algorithms/sho.py`
   - `algorithms/fgo.py` → `algorithms/fsa.py`

2. Actualizados con nuevos imports:
   - `run.py`
   - `analyze_results.py`
   - `run_massive.py`
   - `scripts/run.py`
   - `scripts/analyze.py`
   - `scripts/run_massive.py`
   - `utils/benchmarking.py`
   - `README.md`

3. Adición de alias para compatibilidad en importaciones y referencias de código.

## Documentación Técnica

### Spotted Hyena Optimizer (SHO)

El algoritmo SHO se inspira en el comportamiento de caza cooperativa de las hienas moteadas, que utilizan estrategias de acecho, cerco y ataque coordinado para cazar presas. El algoritmo modela este comportamiento mediante:

- Jerarquía social con los tres mejores individuos (alfa, beta, delta)
- Fase de exploración (acecho de presas)
- Fase de explotación (ataque en círculo)
- Balance dinámico entre exploración/explotación

### Flamingo Search Algorithm (FSA)

FSA se inspira en el comportamiento social y de filtración de los flamencos, que se caracteriza por:

- Forrajeo en grupos (filtrando alimento en aguas poco profundas)
- Migración estacional en busca de condiciones óptimas
- Comportamiento de división/unión de grupos

El algoritmo implementa:
- Fase de forrajeo (búsqueda local)
- Fase de migración (búsqueda global)
- Distribución adaptativa del esfuerzo de búsqueda entre los mejores, intermedios y peores individuos