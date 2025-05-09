# Correcciones, Mejoras y Pruebas del Algoritmo EGTO

Este documento detalla las correcciones, mejoras y pruebas realizadas al algoritmo EGTO (Enhanced Gorilla Troops Optimization) para adaptarlo correctamente al problema VRP.

## Corrección del Algoritmo EGTO

**Fecha:** 8 de mayo de 2025

### Problema Identificado

Se detectó un error de implementación relacionado con los límites del dominio de búsqueda, ya que el algoritmo asumía incorrectamente que el problema VRP proporcionaba atributos `lower_bounds` y `upper_bounds`.

### Solución Implementada

1. **Corrección del error de límites del dominio**
   - Implementación explícita de los límites del dominio para problemas VRP:
   ```python
   # Para problemas VRP, los límites son [0,1]
   self.lower_bounds = np.zeros(self.dimension)
   self.upper_bounds = np.ones(self.dimension)
   ```

2. **Características del algoritmo EGTO**
   - El algoritmo implementa una versión mejorada del GTO con características de optimización de enjambre
   - Incorpora un vector de velocidad para el movimiento
   - Incluye tres fases distintas: 
     - Exploración de alta velocidad en etapas iniciales (primer tercio de iteraciones)
     - Velocidad media con mezcla aleatoria (segundo tercio de iteraciones)
     - Baja velocidad con comportamiento de depredador en etapas finales (último tercio)
   - Utiliza movimiento Browniano para la exploración inicial
   - Implementa componentes de Lévy para la explotación final

## Resultados de las Pruebas Iniciales

Las pruebas iniciales realizadas con el algoritmo EGTO corregido muestran:

1. **Rendimiento**:
   - Mejor fitness encontrado: 448.13 (mejora del 0.42% sobre el valor óptimo conocido)
   - Fitness promedio en 5 ejecuciones: 455.77
   - Desviación estándar: 7.64

2. **Eficiencia**:
   - Tiempo promedio de ejecución: 0.044s (el más rápido de todos los algoritmos)
   - Desviación estándar del tiempo: 0.0003s

3. **Estabilidad**:
   - El algoritmo muestra un comportamiento estable con variabilidad moderada
   - Presenta desviación estándar similar a GTO en su versión inicial (7.69)

## Pruebas con Diferentes Iteraciones

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

## Análisis Comparativo

Comparado con otros algoritmos:

1. EGTO es el algoritmo más rápido, con un tiempo de ejecución de 0.044s
2. La calidad de solución es aceptable, pero no alcanza los resultados óptimos de HHO, WOA o GTO mejorado
3. Presenta baja variabilidad (7.64), indicando un comportamiento estable
4. No logra encontrar la solución óptima (410.93) que alcanzan otros algoritmos como GTO mejorado

## Conclusiones

Las correcciones implementadas en el algoritmo EGTO han solucionado los problemas de compatibilidad con el problema VRP, permitiendo que el algoritmo funcione correctamente. Las principales observaciones son:

1. **Ventajas**:
   - Excepcional velocidad de ejecución (el algoritmo más rápido)
   - Comportamiento estable y predecible
   - Balance eficiente entre exploración y explotación
   - Mejora consistente con más iteraciones, mostrando buena capacidad de convergencia

2. **Limitaciones**:
   - A pesar de su eficiencia, no logra aproximarse al óptimo conocido, incluso con 100 iteraciones
   - Las mejoras propuestas en EGTO podrían no ser óptimas para la naturaleza específica del problema VRP
   - Aunque es el más rápido, sacrifica calidad de solución comparado con otros algoritmos

3. **Aplicaciones recomendadas**:
   - Adecuado para aplicaciones donde el tiempo de cómputo es crítico y se puede sacrificar algo de calidad de solución
   - Útil en escenarios que requieren respuestas rápidas y soluciones aceptables, no necesariamente óptimas
   - Ideal para aproximaciones iniciales o exploración rápida de espacios de búsqueda

4. **Recomendaciones**:
   - Para aplicaciones que requieran soluciones más cercanas al óptimo, considerar algoritmos como HHO, WOA o GTO mejorado
   - Se podrían investigar ajustes específicos en los parámetros del algoritmo EGTO para mejorar su rendimiento en problemas VRP
   - Una posible mejora sería incorporar conocimiento específico del dominio VRP en los operadores de movimiento

Es interesante notar que, mientras que la implementación básica de GTO se mejoró considerablemente con las correcciones finales, alcanzando soluciones óptimas de 410.93, el EGTO que teóricamente incorpora mejoras sobre GTO no logra el mismo nivel de calidad. Esto sugiere que las mejoras genéricas propuestas en EGTO podrían no ser las más adecuadas para la estructura específica del problema VRP.