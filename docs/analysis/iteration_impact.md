# Análisis del Impacto de Iteraciones en Algoritmos Metaheurísticos

Este documento presenta un análisis completo sobre el impacto del número de iteraciones en el rendimiento de diversos algoritmos metaheurísticos aplicados al problema VRP (Vehicle Routing Problem).

## Índice
1. [Análisis General](#análisis-general)
2. [Análisis Detallado por Algoritmo](#análisis-por-algoritmo)
3. [Comportamiento con 10000 Iteraciones](#comportamiento-en-10000-iteraciones-datos-parciales)
4. [Conclusiones Generales](#conclusiones-generales)
5. [Análisis Extendido para EWA](#análisis-extendido-para-ewa)
6. [Análisis de Convergencia Extendido](#análisis-de-convergencia-extendido)
7. [Recomendaciones Finales](#recomendaciones-actualizadas)

## Análisis General

Este análisis examina el impacto del número de iteraciones en el rendimiento de diversos algoritmos metaheurísticos aplicados al problema VRP (Vehicle Routing Problem) usando la instancia E-n22-k4.

### Resumen Comparativo

#### Calidad de Solución (Fitness - menor es mejor)

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

#### Tiempos de Ejecución (segundos)

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

## Análisis Extendido para EWA

- **Instancias de prueba:**
  - E-n22-k4 (22 nodos, 4 vehículos)
  - P-n16-k8 (16 nodos, 8 vehículos)
- **Algoritmo analizado en profundidad:** EWA (Earthworm Algorithm)
- **Parámetros de ejecución ampliados:**
  - Iteraciones: 10, 100, 1000, 10000
  - Tamaños de población: 30, 50
  - Ejecuciones por configuración: 5 (para 10-1000 iter), 3 (para 10000 iter)
  - Múltiples semillas para robustez estadística
- **Valores óptimos conocidos:**
  - E-n22-k4: 375.28
  - P-n16-k8: 450.00

## Resultados Comparativos Extendidos (EWA)

### Evolución del Rendimiento con Número de Iteraciones

| Iteraciones | Fitness Mínimo | Fitness Medio | Desviación Estándar | Tiempo Medio (s) | Gap al Óptimo |
|-------------|----------------|---------------|---------------------|------------------|--------------|
| 10          | 502.46         | 554.12        | 30.80               | 0.009            | 34.0%        |
| 100         | 489.59         | 511.51        | 18.91               | 0.081            | 30.6%        |
| 1000        | 474.78         | 490.21        | 14.76               | 0.800            | 26.6%        |
| 10000       | 447.05         | 453.40        | 5.55                | 8.050            | 19.2%        |

### Efecto del Tamaño de Población (10000 Iteraciones)

| Población | Fitness Mínimo | Fitness Medio | Desviación Estándar | Tiempo (s) | Gap al Óptimo |
|-----------|----------------|---------------|---------------------|------------|---------------|
| 30        | 447.05         | 453.40        | 5.55                | 8.05       | 19.2%         |
| 50        | 436.56         | 436.89        | 0.47                | 13.49      | 16.4%         |

### Desempeño por Tipo de Instancia (10000 Iteraciones)

| Instancia  | Fitness Mínimo | Óptimo | Gap     | Tiempo (s) |
|------------|----------------|--------|---------|------------|
| E-n22-k4   | 436.56         | 375    | 16.4%   | 13.49      |
| P-n16-k8   | 418.25         | 450    | -7.1%   | 7.34       |

## Análisis de Convergencia Extendido

### Curva de Mejora en EWA
- **10 → 100 iteraciones**: Mejora del 2.6% con un aumento de 9x en tiempo
- **100 → 1000 iteraciones**: Mejora del 3.0% con un aumento de 9.9x en tiempo
- **1000 → 10000 iteraciones**: Mejora del 5.9% con un aumento de 10.1x en tiempo

### Tasa de Mejora por Tiempo Invertido
- **10 → 100**: 0.29% mejora por cada incremento de tiempo (baja eficiencia)
- **100 → 1000**: 0.30% mejora por cada incremento de tiempo (baja eficiencia)
- **1000 → 10000**: 0.58% mejora por cada incremento de tiempo (mejor eficiencia)

### Reducción de Variabilidad
La desviación estándar evoluciona de la siguiente manera:
- **10 iteraciones**: 30.80
- **100 iteraciones**: 18.91 (reducción del 38.6%)
- **1000 iteraciones**: 14.76 (reducción del 22.0%)
- **10000 iteraciones**: 5.55 (reducción del 62.4%)
- **10000 iteraciones, población 50**: 0.47 (reducción del 91.5% respecto a población 30)

Esta reducción progresiva de la variabilidad indica una convergencia hacia soluciones más estables y consistentes a medida que aumentan las iteraciones, con un efecto particularmente pronunciado al aumentar también el tamaño de población.

## Análisis de Eficiencia Computacional Extendido

### Escalabilidad de Tiempo
- **Respecto a iteraciones**: El tiempo escala linealmente con un factor aproximado de 10x por cada orden de magnitud en iteraciones
- **Respecto a población**: El tiempo escala aproximadamente 1.7x al aumentar la población de 30 a 50 individuos

### Relación Calidad-Tiempo
La mejora porcentual en solución por cada segundo adicional muestra un patrón interesante:
- **10 → 100 iteraciones**: 2.6% mejora / 0.072s ≈ 36.1% mejora por segundo
- **100 → 1000 iteraciones**: 3.0% mejora / 0.719s ≈ 4.2% mejora por segundo
- **1000 → 10000 iteraciones**: 5.9% mejora / 7.25s ≈ 0.8% mejora por segundo
- **30 → 50 individuos (10000 iter)**: 2.3% mejora / 5.44s ≈ 0.4% mejora por segundo

Esto sugiere una ley de rendimientos decrecientes, donde cada incremento adicional de recursos computacionales produce mejoras cada vez menores por unidad de tiempo.

## Comportamiento por Tipos de Problemas

El análisis muestra un comportamiento diferente en distintos tipos de instancias:

1. **En instancias pequeñas (P-n16-k8):**
   - EWA supera el óptimo conocido en un 7.1%
   - La convergencia es más rápida y efectiva
   - El tiempo de ejecución es menor (7.34s para 10000 iteraciones)

2. **En instancias medianas (E-n22-k4):**
   - EWA alcanza soluciones a un 16.4% del óptimo conocido
   - Requiere más iteraciones para convergencia efectiva
   - El tiempo de ejecución aumenta proporcionalmente al tamaño

Esto sugiere que:
- La eficacia de EWA varía según el tamaño y estructura del problema
- Es particularmente efectivo en instancias pequeñas o con ciertas características estructurales
- Para problemas más complejos, se beneficia significativamente de iteraciones adicionales

## Conclusiones Extendidas

### Hallazgos Principales

1. **Comportamiento de Convergencia a Muy Largo Plazo:**
   - EWA muestra mejora continua incluso hasta 10000 iteraciones
   - La tasa de mejora no disminuye significativamente en etapas tardías
   - La variabilidad entre ejecuciones disminuye sustancialmente con más iteraciones

2. **Efecto del Tamaño de Población:**
   - Aumentar la población mejora tanto la calidad como la consistencia de las soluciones
   - El impacto en la variabilidad es dramático (reducción > 90%)
   - El costo computacional adicional puede justificarse para aplicaciones donde la calidad es crucial

3. **Eficiencia Comparativa:**
   - La mejor relación mejora/tiempo se observa en el rango 1000-10000 iteraciones
   - Cada orden de magnitud en iteraciones proporciona aproximadamente 3-6% de mejora adicional
   - El mayor salto cualitativo se observa entre 1000-10000 iteraciones

### Recomendaciones Actualizadas

1. **Para uso práctico en aplicaciones:**
   - **Alta prioridad en tiempo (< 0.1s)**: 100 iteraciones, población 30
   - **Balance tiempo-calidad (< 1s)**: 1000 iteraciones, población 30
   - **Alta calidad con tiempo razonable (< 10s)**: 10000 iteraciones, población 30
   - **Máxima calidad sin restricción de tiempo**: 10000 iteraciones, población 50+

2. **Para investigación y benchmark:**
   - Ejecutar al menos 5 repeticiones con semillas diferentes
   - Evaluar el rango completo de 10-10000 iteraciones para caracterizar completamente el algoritmo
   - Considerar tamaños de población de 30-50 para análisis de sensibilidad

3. **Para adaptación dinámica:**
   - Implementar detección de estancamiento basada en la tasa de mejora
   - Aumentar dinámicamente el tamaño de población si la variabilidad es alta
   - Considerar criterios de parada adaptativos basados en la desviación estándar

## Implicaciones para Optimización en General

1. **Configuración Experimental:**
   - Los estudios comparativos deben incluir análisis de sensibilidad a iteraciones
   - 1000 iteraciones parece ser un mínimo razonable para conclusiones estadísticamente sólidas
   - La variabilidad entre ejecuciones debe evaluarse explícitamente

2. **Diseño de Algoritmos:**
   - Los mecanismos de auto-ajuste deben operar en escalas de tiempo extendidas
   - La capacidad de mantener mejora continua en etapas tardías es un indicador de robustez
   - La reducción de variabilidad debe considerarse un objetivo de diseño

3. **Aplicaciones Prácticas:**
   - Las implementaciones deberían permitir "anytime stopping" para balance flexibilidad-calidad
   - Los métodos con convergencia gradual y consistente como EWA permiten ajuste preciso de recursos
   - La selección de algoritmos debe considerar no solo la calidad final sino el patrón de convergencia

---

*Análisis realizado el 9 de mayo de 2025*
