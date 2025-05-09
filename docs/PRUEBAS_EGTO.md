# Pruebas de Rendimiento del Algoritmo EGTO

Este documento detalla los resultados de las pruebas realizadas con el algoritmo EGTO (Enhanced Gorilla Troops Optimization) con diferentes parámetros.

## Pruebas con Diferentes Iteraciones

**Fecha:** 8 de mayo de 2025

### Configuración de Pruebas

- **Instancia VRP**: E-n22-k4
- **Tamaño de población**: 30
- **Iteraciones**: 1, 5, 10, 100
- **Ejecuciones por configuración**: 1

### Resultados Obtenidos

| Iteraciones | Mejor fitness | Tiempo (s) |
|-------------|---------------|------------|
| 1           | 675.58        | 0.00       |
| 5           | 660.67        | 0.00       |
| 10          | 613.16        | 0.00       |
| 100         | 565.84        | 0.04       |

### Análisis de Resultados

1. **Progresión del fitness**:
   - Se observa una mejora significativa del fitness a medida que aumenta el número de iteraciones
   - La reducción del fitness entre 1 y 100 iteraciones es de 109.74 unidades (16.2%)
   - La mayor mejora proporcional se produce entre 5 y 10 iteraciones (7.2%)

2. **Eficiencia computacional**:
   - El algoritmo EGTO es extremadamente eficiente, con tiempos de ejecución muy bajos
   - Incluso con 100 iteraciones, el tiempo de ejecución es solo de 0.04 segundos
   - Las ejecuciones con menos de 10 iteraciones son prácticamente instantáneas

3. **Rendimiento general**:
   - El algoritmo muestra una clara convergencia hacia mejores soluciones con más iteraciones
   - Sin embargo, incluso con 100 iteraciones, no alcanza el valor óptimo conocido para esta instancia (375.28)
   - El mejor resultado obtenido (565.84) está a un 50.8% del óptimo

## Conclusiones

El algoritmo EGTO muestra un excelente rendimiento en términos de velocidad de ejecución, siendo extremadamente eficiente incluso con un número elevado de iteraciones. Sin embargo, en términos de calidad de solución, se observa que:

1. EGTO mejora consistentemente con más iteraciones, mostrando una buena capacidad de convergencia
2. La velocidad de convergencia es alta en las primeras iteraciones y luego se ralentiza
3. A pesar de su eficiencia, no logra aproximarse al óptimo conocido con 100 iteraciones

Estas pruebas confirman las observaciones documentadas en el análisis previo de EGTO: su principal fortaleza es la velocidad de ejecución, lo que lo hace adecuado para aplicaciones donde el tiempo de cómputo es crítico y se puede sacrificar algo de calidad de solución.

Recomendación: para aplicaciones que requieran soluciones más cercanas al óptimo, considerar algoritmos como HHO, WOA o GTO mejorado, que han demostrado mejores resultados en términos de calidad de solución para problemas VRP.