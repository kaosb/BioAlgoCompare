# Análisis del Algoritmo FGO

Este documento detalla las características y rendimiento del algoritmo FGO (Flamingo Optimization Algorithm) en la resolución de problemas VRP.

## Evaluación del Algoritmo FGO

**Fecha:** 8 de mayo de 2025

### Características del Algoritmo

El algoritmo FGO implementa el comportamiento de los flamencos, con dos estrategias principales de movimiento:

1. **Estrategia de forrajeo (forage)**:
   - Implementa el comportamiento de alimentación de los flamencos
   - Utiliza distribuciones normales y chi-cuadrado para modelar el movimiento
   - Incorpora factores aleatorios para la exploración
   - Se aplica a individuos de rendimiento intermedio

2. **Estrategia de migración (migrate)**:
   - Simula el comportamiento de vuelo y migración de los flamencos
   - Implementa un movimiento más directo hacia las mejores soluciones
   - Se aplica a los mejores individuos (élite) y a los peores para mejorar su posición
   - Utiliza un factor de peso ω basado en una distribución normal

3. **División de la población**:
   - La población se divide en tres grupos según su rendimiento
   - Los mejores individuos (10%) se mueven con estrategia de migración
   - Un grupo intermedio (determinado dinámicamente) usa estrategia de forrajeo
   - Los peores individuos utilizan estrategia de migración para abandonar áreas poco prometedoras

### Resultados de las Pruebas

Las pruebas realizadas con el algoritmo FGO muestran:

1. **Rendimiento**:
   - Mejor fitness encontrado: 447.10 (mejora del 0.64% sobre el valor óptimo conocido)
   - Fitness promedio en 5 ejecuciones: 451.19
   - Desviación estándar: 3.22 (muy baja, indicando alta estabilidad)

2. **Eficiencia**:
   - Tiempo promedio de ejecución: 0.194s
   - Desviación estándar del tiempo: 0.002s

3. **Estabilidad**:
   - El algoritmo muestra un comportamiento muy estable
   - La segunda menor desviación estándar entre todos los algoritmos, solo superado por FOA
   - Alta consistencia en los resultados

### Análisis Comparativo

Comparado con otros algoritmos:

1. FGO tiene la segunda menor desviación estándar (3.22), solo superado por FOA (4.83)
2. La calidad de solución es moderada, no alcanzando los niveles de HHO, WOA o GTO mejorado
3. El tiempo de ejecución (0.194s) es relativamente alto, más lento que MRFO, GTO y EGTO
4. No logra encontrar la solución óptima (410.93) que alcanzan otros algoritmos

## Conclusión

El algoritmo FGO destaca principalmente por su estabilidad, ofreciendo resultados consistentes entre diferentes ejecuciones. Sus características principales son:

1. Excelente estabilidad, con muy baja variabilidad entre ejecuciones
2. Implementación efectiva del comportamiento social de los flamencos
3. División dinámica de la población según rendimiento
4. Balance adecuado entre exploración y explotación

A pesar de que FGO no alcanza las soluciones óptimas que logran otros algoritmos, su alta estabilidad lo hace valioso para aplicaciones donde se requiere predictibilidad. El algoritmo representa una buena opción para problemas donde la consistencia en los resultados es más importante que encontrar la solución absolutamente óptima.

FGO se posiciona como un algoritmo con implementación robusta y comportamiento predecible, aunque con limitaciones en términos de capacidad para encontrar soluciones óptimas globales en problemas VRP complejos.