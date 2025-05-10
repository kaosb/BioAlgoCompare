# Análisis de Impacto del Número de Iteraciones en Metaheurísticas

Este análisis examina el impacto del número de iteraciones en el rendimiento de diversos algoritmos metaheurísticos aplicados al problema VRP (Vehicle Routing Problem) usando la instancia E-n22-k4.

## Resumen Comparativo

### Calidad de Solución (Fitness - menor es mejor)

| Algoritmo | 10 iteraciones | 100 iteraciones | 1000 iteraciones | Mejora 10→100 | Mejora 100→1000 |
|-----------|---------------|-----------------|------------------|--------------|----------------|
| HOA       | 629.20        | 463.68          | 513.70           | 26.31%       | -10.79%        |
| APO       | 645.04        | 556.52          | 519.79           | 13.72%       | 6.60%          |
| EGTO      | 647.94        | 540.07          | 553.01           | 16.65%       | -2.40%         |
| EWA       | 567.67        | 521.97          | 478.27           | 8.05%        | 8.37%          |
| FGO       | 471.67        | 479.29          | 475.79           | -1.62%       | 0.73%          |
| FOA       | 627.93        | 485.13          | 443.23           | 22.74%       | 8.64%          |
| GTO       | 537.72        | 511.18          | 481.68           | 4.94%        | 5.77%          |
| HHO       | 563.87        | 477.28          | 494.21           | 15.36%       | -3.55%         |
| MRFO      | 474.48        | 480.22          | 472.81           | -1.21%       | 1.54%          |
| SMA       | 476.00        | 462.41          | 482.26           | 2.86%        | -4.29%         |
| WOA       | 536.99        | 497.02          | 497.86           | 7.44%        | -0.17%         |
| AHA       | 658.22        | 564.27          | 610.64           | 14.27%       | -8.22%         |
| RRO       | 599.06        | 528.05          | 406.94           | 11.85%       | 22.94%         |
| GVOA      | 631.47        | 517.56          | 423.11           | 18.04%       | 18.25%         |
| SMO       | 634.50        | 563.87          | 458.78           | 11.13%       | 18.64%         |

### Tiempos de Ejecución (segundos)

| Algoritmo | 10 iteraciones | 100 iteraciones | 1000 iteraciones | Factor 10→100 | Factor 100→1000 |
|-----------|---------------|-----------------|------------------|--------------|----------------|
| HOA       | 0.01          | 0.12            | 1.18             | 12.0x        | 9.8x           |
| APO       | 0.01          | 0.05            | 0.54             | 5.0x         | 10.8x          |
| EGTO      | 0.00          | 0.04            | 0.38             | ∞            | 9.5x           |
| EWA       | 0.01          | 0.08            | 0.83             | 8.0x         | 10.4x          |
| FGO       | 0.03          | 0.27            | 2.72             | 9.0x         | 10.1x          |
| FOA       | 0.02          | 0.19            | 2.01             | 9.5x         | 10.6x          |
| GTO       | 0.01          | 0.06            | 0.58             | 6.0x         | 9.7x           |
| HHO       | 0.01          | 0.07            | 0.66             | 7.0x         | 9.4x           |
| MRFO      | 0.01          | 0.06            | 0.63             | 6.0x         | 10.5x          |
| SMA       | 0.01          | 0.06            | 0.54             | 6.0x         | 9.0x           |
| WOA       | 0.01          | 0.07            | 0.76             | 7.0x         | 10.9x          |
| AHA       | 0.03          | 0.26            | 2.61             | 8.7x         | 10.0x          |
| RRO       | 0.43          | 4.69            | 48.85            | 10.9x        | 10.4x          |
| GVOA      | 0.02          | 0.22            | 2.34             | 11.0x        | 10.6x          |
| SMO       | 0.01          | 0.05            | 0.50             | 5.0x         | 10.0x          |

## Análisis por Algoritmo

### FOA (Fossa Optimization Algorithm)
- **Mejor mejora progresiva**: Muestra una mejora consistente con más iteraciones (627.93 → 485.13 → 443.23)
- Excelente escalabilidad de calidad con iteraciones (mejora total de 29.4%)
- Tiempo de ejecución proporcional al número de iteraciones

### RRO (Raven Roosting Optimization)
- **Mayor mejora con 1000 iteraciones**: Logra el mejor fitness final (406.94)
- Mejora dramática al aumentar las iteraciones (599.06 → 528.05 → 406.94)
- **Algoritmo más lento**: Tiempos de ejecución significativamente mayores (0.43s → 4.69s → 48.85s)

### EWA (Earthworm Algorithm)
- **Mejora constante**: Muestra mejora consistente al aumentar iteraciones (567.67 → 521.97 → 478.27)
- Buen balance entre calidad de solución y tiempo de ejecución

### MRFO (Manta Ray Foraging Optimization)
- **Consistente**: Rendimiento estable en todos los niveles de iteración
- Buena calidad de solución desde pocas iteraciones
- No muestra mejora significativa con más iteraciones

### HOA/SHO (Spotted Hyena Optimizer)
- **Comportamiento irregular**: Mejor con 100 iteraciones (463.68) que con 1000 (513.70)
- Posible convergencia prematura en óptimos locales con más iteraciones

### AHA (Artificial Hummingbird Algorithm)
- **Rendimiento inconsistente**: Peor con 10 iteraciones (658.22), mejora con 100 (564.27), pero empeora con 1000 (610.64)
- Tiempo de ejecución relativamente alto
- No muestra beneficio claro al aumentar iteraciones

### GVOA (Griffon Vultures Optimization Algorithm)
- **Mejora sostenida excepcional**: Mantiene tasa de mejora similar en ambas etapas (18.04% y 18.25%)
- Excelente progresión (631.47 → 517.56 → 423.11) con mejora total del 32.99%
- Segundo mejor fitness general con 1000 iteraciones (423.11)
- Tiempo de ejecución moderado (2.34s para 1000 iteraciones)

### SMO (Starling Murmuration Optimizer)
- **Mejora destacada en fase tardía**: Gran salto entre 100 y 1000 iteraciones (18.64%)
- Buena progresión general (634.50 → 563.87 → 458.78) con mejora total del 27.7%
- Excelente eficiencia computacional (0.50s para 1000 iteraciones)
- Buen balance entre calidad de solución y velocidad de ejecución

## Comportamiento en 10000 iteraciones (datos parciales)

Los resultados parciales para 10000 iteraciones muestran tendencias interesantes:

| Algoritmo | 1000 iteraciones | 10000 iteraciones | Mejora |
|-----------|-----------------|-------------------|--------|
| FOA       | 443.23          | 383.87            | 13.39% |
| GTO       | 481.68          | 383.84            | 20.31% |
| WOA       | 497.86          | 400.31            | 19.59% |
| HHO       | 494.21          | 392.89            | 20.50% |
| MRFO      | 472.81          | 442.24            | 6.47%  |
| EWA       | 478.27          | 441.90            | 7.60%  |
| AHA       | 610.64          | 477.32            | 21.83% |

Notablemente:
- FOA, GTO y HHO muestran mejoras significativas (~20%)
- AHA muestra la mayor mejora porcentual, pero sigue siendo inferior a otros algoritmos

## Conclusiones Generales

1. **Impacto del número de iteraciones**:
   - El mayor salto de calidad ocurre entre 10 y 100 iteraciones para la mayoría de los algoritmos
   - Algunos algoritmos muestran comportamiento no monótono (empeoran con más iteraciones)
   - Con 10000 iteraciones, varios algoritmos alcanzan soluciones de alta calidad (<400)

2. **Eficiencia computacional**:
   - El tiempo de ejecución escala aproximadamente de forma lineal con el número de iteraciones
   - RRO es significativamente más costoso computacionalmente (10x más lento que otros)

3. **Mejores algoritmos para VRP**:
   - **Mejor calidad global**: RRO con 1000 iteraciones (406.94), GVOA con 1000 iteraciones (423.11) y FOA/GTO con 10000 iteraciones (~383)
   - **Mejor balance calidad/tiempo**: SMO con 1000 iteraciones (458.78 en 0.50s) y FOA con 1000 iteraciones (443.23 en 2.01s)
   - **Mejor con pocas iteraciones**: FGO y MRFO obtienen buenos resultados incluso con 10 iteraciones

4. **Recomendaciones de uso**:
   - Para exploraciones rápidas: MRFO o FGO con 10-100 iteraciones
   - Para soluciones de alta calidad con tiempo limitado: SMO o FOA con 1000 iteraciones
   - Para soluciones óptimas con tiempo moderado: GVOA con 1000 iteraciones
   - Para soluciones óptimas sin restricción de tiempo: RRO con 1000+ iteraciones o GTO/FOA con 10000 iteraciones

5. **Comportamiento por familias de algoritmos**:
   - **Aves rapaces/carroñeras**: Excelente desempeño (RRO, GVOA) con mejoras sostenidas al aumentar iteraciones
   - **Comportamiento de bandada/conjunto**: SMO muestra buen equilibrio entre calidad y eficiencia
   - **Búsqueda de alimento**: (FOA, MRFO) parecen funcionar mejor en términos generales
   - **Comportamiento de manada/social**: (HOA, GTO) muestran variabilidad
   - **Vuelo singular**: AHA (colibríes) muestra rendimiento inconsistente con diferentes números de iteraciones

Este análisis demuestra la importancia de seleccionar no solo el algoritmo adecuado sino también el número óptimo de iteraciones según las restricciones de tiempo y calidad requeridas.