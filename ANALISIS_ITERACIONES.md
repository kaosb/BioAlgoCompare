# Análisis del Impacto del Número de Iteraciones en Algoritmos Metaheurísticos

Este documento presenta un análisis detallado del efecto que tiene el número de iteraciones en el rendimiento de diferentes algoritmos metaheurísticos bioinspirados para resolver el problema de enrutamiento de vehículos (VRP).

## Metodología

Se ejecutaron pruebas sistemáticas con los siguientes parámetros:
- **Algoritmos evaluados**: APO, EGTO, HOA, SMA, WOA
- **Números de iteraciones**: 10, 100, 1000, 10000
- **Problema**: E-n22-k4 (VRP con 22 nodos y 4 vehículos)
- **Métricas**: Fitness, tiempo de ejecución, gap al óptimo conocido, eficiencia (relación calidad/tiempo)
- **Ejecuciones por configuración**: 5-10 con diferentes semillas aleatorias para obtener significancia estadística

## Resultados Principales

### 1. Calidad de la Solución vs. Iteraciones

A medida que aumenta el número de iteraciones, todos los algoritmos mejoran la calidad de sus soluciones, pero con rendimientos decrecientes:

- **Mejora más significativa**: Entre 10 y 100 iteraciones (reducción promedio del 20-30% en el gap al óptimo)
- **Mejora moderada**: Entre 100 y 1000 iteraciones (reducción adicional del 10-15%)
- **Mejora menor**: Entre 1000 y 10000 iteraciones (reducción adicional del 5-10%)

### 2. Ranking de Algoritmos según Calidad de Solución (10000 iteraciones)

| Posición | Algoritmo | Fitness Promedio | Gap al Óptimo (%) |
|----------|-----------|-----------------|-------------------|
| 1        | WOA       | 407.32          | 8.62%             |
| 2        | SMA       | 414.58          | 10.55%            |
| 3        | HOA       | 425.71          | 13.52%            |
| 4        | APO       | 456.29          | 21.68%            |
| 5        | EGTO      | 467.83          | 24.75%            |

### 3. Tiempo de Ejecución vs. Iteraciones

El tiempo de ejecución crece de manera aproximadamente lineal con el número de iteraciones para todos los algoritmos, pero con tasas de crecimiento diferentes:

- **Algoritmos más rápidos**: EGTO, APO, WOA
- **Algoritmos más lentos**: SMA, HOA

### 4. Eficiencia (Calidad/Tiempo)

La métrica de eficiencia combina la calidad de la solución y el tiempo de ejecución, permitiendo identificar los algoritmos con mejor balance:

| Posición | Algoritmo | Eficiencia (10000 iteraciones) |
|----------|-----------|--------------------------------|
| 1        | WOA       | 0.8124                         |
| 2        | EGTO      | 0.6753                         |
| 3        | APO       | 0.5981                         |
| 4        | SMA       | 0.0985                         |
| 5        | HOA       | 0.0721                         |

## Análisis por Algoritmo

### APO (Artificial Protozoa Optimizer)
- **Comportamiento**: Mejora constante pero lenta con más iteraciones
- **Fortalezas**: Tiempo de ejecución rápido, mejora continua
- **Debilidades**: No alcanza soluciones tan buenas como WOA o SMA
- **Recomendado para**: Problemas con restricciones moderadas de tiempo que necesitan buenas soluciones

### EGTO (Exemplar Grasshopper Optimization)
- **Comportamiento**: Mejora rápidamente al inicio pero se estanca
- **Fortalezas**: Extremadamente rápido (el más rápido)
- **Debilidades**: Calidad de solución inferior en el largo plazo
- **Recomendado para**: Problemas donde el tiempo es crítico y se necesitan soluciones rápidas aunque no óptimas

### HOA (Hyena Optimization Algorithm)
- **Comportamiento**: Mejora constante con más iteraciones
- **Fortalezas**: Buena calidad de solución, especialmente con más iteraciones
- **Debilidades**: Tiempo de ejecución lento
- **Recomendado para**: Problemas donde la calidad es más importante que el tiempo

### SMA (Slime Mould Algorithm)
- **Comportamiento**: Converge rápidamente a buenas soluciones
- **Fortalezas**: Excelente calidad de solución
- **Debilidades**: Tiempo de ejecución muy alto
- **Recomendado para**: Problemas donde la calidad es crítica y el tiempo no es limitante

### WOA (Whale Optimization Algorithm)
- **Comportamiento**: Mejora significativa con más iteraciones, buena convergencia
- **Fortalezas**: Mejor balance calidad/tiempo, mejores soluciones
- **Debilidades**: Variabilidad entre ejecuciones
- **Recomendado para**: Uso general, mejor algoritmo en el conjunto evaluado

## Conclusiones y Recomendaciones

1. **Para ejecuciones rápidas (menos de 1 segundo)**: 
   - Utilizar WOA o EGTO con 100-1000 iteraciones

2. **Para soluciones de alta calidad**:
   - Utilizar WOA o SMA con 10000+ iteraciones

3. **Para mejor balance calidad/tiempo**:
   - WOA con 1000-10000 iteraciones ofrece el mejor compromiso

4. **Recomendaciones de iteraciones**:
   - **10-100**: Exploraciones iniciales o pruebas rápidas
   - **100-1000**: Uso práctico estándar con buen balance
   - **1000-10000**: Cuando se requiere alta calidad
   - **10000+**: Para benchmarks o soluciones críticas

5. **Paralelización**:
   - La ejecución en paralelo es crucial para iteraciones altas
   - A partir de 1000 iteraciones, el beneficio de la paralelización es significativo

Este análisis demuestra la importancia de seleccionar adecuadamente tanto el algoritmo como el número de iteraciones según los requisitos específicos del problema, equilibrando la calidad de la solución y el tiempo de ejecución disponible.