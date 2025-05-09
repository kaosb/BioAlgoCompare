# Comparativa Global de Algoritmos Metaheurísticos

## Resumen Ejecutivo

Este análisis comparativo evalúa el rendimiento de once algoritmos metaheurísticos bioinspirados aplicados al problema de ruteo de vehículos (VRP). Los resultados muestran que SHO (Spotted Hyena Optimizer), WOA (Whale Optimization Algorithm) y FSA (Flamingo Search Algorithm) ofrecen las mejores soluciones, con ventajas específicas en diferentes contextos de aplicación.

## Resultados Clave

### Ranking de Rendimiento (Mejor Fitness)

1. **SHO (Spotted Hyena Optimizer)**: 410.23 (Gap: 9.39%)
2. **WOA (Whale Optimization Algorithm)**: 421.77 (Gap: 12.47%)
3. **FSA (Flamingo Search Algorithm)**: 423.12 (Gap: 12.83%)
4. **SMA (Slime Mould Algorithm)**: 452.50 (Gap: 20.67%)
5. **MRFO (Manta Ray Foraging Optimization)**: 454.07 (Gap: 21.09%)

### Eficiencia Computacional (Tiempo Promedio)

1. **EGTO**: 0.04s
2. **APO**: 0.05s
3. **GTO/MRFO**: 0.06s
4. **WOA/HHO**: 0.07s
5. **EWA**: 0.09s

### Balance Calidad-Eficiencia

1. **WOA**: Excelente balance (2° mejor solución, 5° más rápido)
2. **MRFO**: Buen balance (5° mejor solución, 3° más rápido)
3. **SHO**: Orientado a calidad (1° mejor solución, 8° más rápido)

## Análisis Estadístico

Las pruebas estadísticas (Friedman, p<0.001) confirman diferencias significativas entre los algoritmos en términos de fitness promedio, tiempo y gap al óptimo. Sin embargo, entre los tres mejores algoritmos (SHO, WOA, FSA), las diferencias en mejor fitness no son estadísticamente significativas (p=0.2952).

## Conclusiones Principales

1. **SHO** ofrece el mejor rendimiento global para el VRP, con soluciones de alta calidad y buena robustez.

2. **WOA** presenta el mejor equilibrio entre calidad de solución y eficiencia computacional.

3. **FSA** logra resultados competitivos pero con mayor costo computacional.

4. Los algoritmos más recientes (SHO, FSA) superan a algoritmos clásicos como GTO y HHO.

5. El balance entre exploración global y explotación local es un factor determinante para el rendimiento en el problema VRP.

## Recomendaciones

- **Para aplicaciones con prioridad en calidad**: Utilizar SHO
- **Para aplicaciones con restricciones de tiempo**: Utilizar WOA
- **Para mejores resultados en instancias complejas**: Considerar una hibridación SHO+WOA

---

*Un análisis detallado con metodología, estadísticas completas y recomendaciones específicas está disponible en el directorio results/analysis/*
EOF < /dev/null