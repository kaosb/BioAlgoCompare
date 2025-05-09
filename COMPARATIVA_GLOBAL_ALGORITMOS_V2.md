# Comparativa Global de Algoritmos Metaheurísticos para VRP

Este documento presenta un análisis comparativo integral de todos los algoritmos metaheurísticos implementados para la resolución del Problema de Ruteo de Vehículos (VRP), basado en múltiples ejecuciones, análisis de iteraciones y evaluación sistemática de resultados.

## Configuración Experimental

- **Instancia de prueba:** E-n22-k4 (22 nodos, 4 vehículos)
- **Algoritmos evaluados:** 11 algoritmos bioinspirados (HHO, WOA, EWA, SMA, MRFO, GTO, EGTO, FOA, FGO, HOA, APO)
- **Parámetros de ejecución:**
  - Iteraciones: 10, 100, 1000
  - Tamaño de población: 30
  - Ejecuciones por algoritmo y configuración: 1-5
  - Semilla fija: 42 (para asegurar reproducibilidad)
- **Valor óptimo conocido:** 375.28 (para la instancia E-n22-k4)

## Resultados Comparativos

### Mejores Soluciones Globales (1000 iteraciones)

| Ranking | Algoritmo | Mejor Fitness | % sobre óptimo | Tiempo (s) |
|---------|-----------|---------------|----------------|------------|
| 1       | GTO       | 426.29        | 13.6%          | 0.57       |
| 2       | FOA       | 437.04        | 16.5%          | 1.83       |
| 3       | HOA       | 452.58        | 20.6%          | 1.16       |
| 4       | MRFO      | 459.65        | 22.5%          | 0.63       |
| 5       | EGTO      | 474.30        | 26.4%          | 0.38       |
| 6       | HHO       | 475.13        | 26.6%          | 0.65       |
| 7       | WOA       | 476.41        | 26.9%          | 0.64       |
| 8       | EWA       | 479.12        | 27.7%          | 0.92       |
| 9       | SMA       | 489.30        | 30.4%          | 4.03       |
| 10      | FGO       | 494.98        | 31.9%          | 2.58       |
| 11      | APO       | 531.42        | 41.6%          | 0.54       |

### Patrones de Convergencia por Iteraciones

| Algoritmo | 10 iteraciones | 100 iteraciones | 1000 iteraciones | Mejora Total | Patrón de Convergencia |
|-----------|---------------|-----------------|------------------|--------------|------------------------|
| GTO       | 568.87        | 522.09          | 426.29           | 25.1%        | Mejora Constante       |
| FOA       | 650.78        | 523.21          | 437.04           | 32.8%        | Mejora Constante       |
| HOA       | 651.43        | 471.68          | 452.58           | 30.5%        | Convergencia Temprana  |
| MRFO      | 507.20        | 475.64          | 459.65           | 9.4%         | Mejora Gradual Limitada|
| EGTO      | 600.11        | 520.47          | 474.30           | 21.0%        | Mejora Constante       |
| HHO       | 561.98        | 538.69          | 475.13           | 15.4%        | Convergencia Tardía    |
| WOA       | 525.75        | 476.21          | 476.41           | 9.4%         | Convergencia Temprana  |
| EWA       | 564.47        | 507.32          | 479.12           | 15.1%        | Mejora Constante       |
| SMA       | 537.72        | 539.99          | 489.30           | 9.0%         | Convergencia Tardía    |
| FGO       | 515.55        | 496.49          | 494.98           | 4.0%         | Convergencia Temprana  |
| APO       | 597.50        | 544.41          | 531.42           | 11.1%        | Mejora Gradual Limitada|

### Eficiencia Computacional (Tiempo en segundos)

| Algoritmo | 10 iteraciones | 100 iteraciones | 1000 iteraciones | Factor 10→1000 |
|-----------|---------------|-----------------|------------------|---------------|
| EGTO      | 0.00          | 0.04            | 0.38             | ≈380x         |
| APO       | 0.01          | 0.05            | 0.54             | 54x           |
| GTO       | 0.01          | 0.06            | 0.57             | 57x           |
| MRFO      | 0.01          | 0.06            | 0.63             | 63x           |
| WOA       | 0.01          | 0.07            | 0.64             | 64x           |
| HHO       | 0.01          | 0.07            | 0.65             | 65x           |
| EWA       | 0.01          | 0.09            | 0.92             | 92x           |
| HOA       | 0.01          | 0.12            | 1.16             | 116x          |
| FOA       | 0.02          | 0.18            | 1.83             | 91.5x         |
| FGO       | 0.03          | 0.26            | 2.58             | 86x           |
| SMA       | 0.04          | 0.40            | 4.03             | 100.8x        |

## Análisis Multidimensional

### Balance Calidad-Eficiencia (1000 iteraciones)

Para evaluar el balance entre calidad de solución y eficiencia computacional, utilizamos un índice compuesto que considera ambos factores:

1. **Excelente Balance:** 
   - **GTO**: Mejor solución (426.29) con tiempo moderado (0.57s)
   - **MRFO**: Buena solución (459.65) con tiempo moderado (0.63s)
   - **EGTO**: Solución moderada (474.30) con el mejor tiempo (0.38s)

2. **Buena Calidad / Tiempo Moderado:**
   - **FOA**: Segunda mejor solución (437.04) pero tiempo alto (1.83s)
   - **HOA**: Tercera mejor solución (452.58) con tiempo moderado-alto (1.16s)

3. **Calidad Moderada / Buena Eficiencia:**
   - **HHO**: Solución moderada (475.13) con buena eficiencia (0.65s)
   - **WOA**: Solución moderada (476.41) con buena eficiencia (0.64s)

4. **Balance Inferior:**
   - **EWA**: Solución moderada (479.12) con tiempo moderado (0.92s)
   - **APO**: Peor solución (531.42) a pesar de buena eficiencia (0.54s)
   - **FGO**: Solución baja (494.98) con tiempo alto (2.58s)
   - **SMA**: Solución baja (489.30) con el peor tiempo (4.03s)

### Patrones de Convergencia y Comportamiento Algorítmico

Identificamos cuatro patrones principales de convergencia:

1. **Mejora Constante (GTO, FOA, EGTO, EWA)**: 
   - Muestran mejora significativa tanto en etapas tempranas como tardías
   - Alta capacidad de exploración y explotación balanceadas
   - Mejor diseño para problemas complejos que requieren refinamiento continuo

2. **Convergencia Temprana (WOA, FGO, HOA)**:
   - Convergen rápidamente con poca mejora después de 100 iteraciones
   - Alta eficiencia con presupuesto computacional limitado
   - Posible tendencia a quedar atrapados en óptimos locales

3. **Convergencia Tardía (HHO, SMA)**:
   - Mejoran más significativamente en etapas avanzadas (>100 iteraciones)
   - Fase exploratoria extendida antes de la explotación efectiva
   - Requieren mayor presupuesto computacional para mostrar su potencial

4. **Mejora Gradual Limitada (MRFO, APO)**:
   - Mejoran de forma constante pero modesta
   - Capacidad limitada para escapar de óptimos locales
   - Menor sensibilidad al número de iteraciones

### Sensibilidad al Número de Iteraciones

La sensibilidad de cada algoritmo al número de iteraciones revela aspectos importantes de su comportamiento:

1. **Alta Sensibilidad (>25% mejora)**: GTO (25.1%), FOA (32.8%), HOA (30.5%)
   - Estos algoritmos se benefician enormemente de un mayor presupuesto computacional
   - Implementan mecanismos efectivos para continuar mejorando a largo plazo
   - Óptimos para situaciones donde la calidad de solución es prioritaria

2. **Sensibilidad Media (15-25% mejora)**: EGTO (21.0%), HHO (15.4%), EWA (15.1%)
   - Balance entre mejora rápida inicial y capacidad de refinamiento posterior
   - Buen comportamiento general para la mayoría de aplicaciones

3. **Baja Sensibilidad (<15% mejora)**: MRFO (9.4%), WOA (9.4%), SMA (9.0%), APO (11.1%), FGO (4.0%)
   - Convergen rápidamente a una solución de calidad moderada
   - Aumentar iteraciones ofrece retornos marginales decrecientes
   - Ideales para aplicaciones con restricciones de tiempo

## Comparación con Instancias Previas (P-n16-k8)

Comparando con resultados obtenidos previamente para la instancia P-n16-k8:

1. **Consistencia de GTO**: Mantiene excelente desempeño en ambas instancias, confirmando su robustez
2. **Variación en HHO**: Excelente en P-n16-k8 (mejor solución) pero rendimiento moderado en E-n22-k4
3. **Estabilidad de MRFO**: Mantiene desempeño similar en ambas instancias (bueno pero no óptimo)
4. **Mejora de FOA**: Mayor efectividad en E-n22-k4 que en P-n16-k8, posible afinidad con esta estructura de problema

Estas diferencias sugieren sensibilidad a las características específicas de cada instancia:
- E-n22-k4: Mayor dimensionalidad (22 vs 16 nodos) pero menor flota (4 vs 8 vehículos)
- Algunos algoritmos responden mejor a problemas con muchos vehículos (HHO), mientras que otros a problemas con rutas más extensas (FOA)

## Recomendaciones Específicas por Escenario

### Por Restricción de Tiempo

1. **Restricción severa (<0.1s)**: 
   - Usar EGTO, APO o GTO con 10 iteraciones
   - Priorizar algoritmos con convergencia temprana (FGO, WOA)

2. **Restricción moderada (0.1-1.0s)**:
   - Usar EGTO o GTO con 100 iteraciones
   - Alternativa: MRFO, HHO o WOA con 100 iteraciones

3. **Sin restricción significativa (>1.0s)**:
   - Usar GTO o FOA con 1000 iteraciones
   - Alternativa: HOA con 1000 iteraciones

### Por Prioridad de Calidad

1. **Calidad crítica**:
   - GTO con 1000 iteraciones (mejor solución global)
   - FOA con 1000 iteraciones (segunda mejor)

2. **Balance calidad/tiempo**:
   - GTO con 100 iteraciones
   - HOA con 100 iteraciones
   - MRFO con 100-1000 iteraciones

3. **Exploración preliminar**:
   - FGO con 10 iteraciones (mejor resultado inicial)
   - WOA con 10 iteraciones (segundo mejor resultado inicial)

### Por Tipo de Problema VRP

1. **Problemas con más vehículos y menos nodos**:
   - Preferir HHO, WOA (mejores en P-n16-k8)

2. **Problemas con menos vehículos y más nodos**:
   - Preferir GTO, FOA (mejores en E-n22-k4)

3. **Soluciones iniciales rápidas**:
   - FGO, WOA (mejores resultados con pocas iteraciones)

4. **Refinamiento de soluciones existentes**:
   - GTO, HHO (mejora significativa en fases tardías)

## Conclusiones Generales

1. **Algoritmo más versátil**: GTO demuestra el mejor balance general entre calidad de solución, eficiencia y capacidad de mejora con más iteraciones, posicionándose como la opción más recomendable para la mayoría de escenarios VRP.

2. **Mejor comportamiento a largo plazo**: FOA y GTO presentan la mayor capacidad de mejora continua, indicando mecanismos efectivos de búsqueda que evitan estancamiento.

3. **Mayor eficiencia computacional**: EGTO mantiene su posición como el algoritmo más rápido, aunque con soluciones de calidad intermedia.

4. **Importancia del número de iteraciones**: El análisis demuestra que el comportamiento de los algoritmos varía significativamente según el número de iteraciones, y esta variación no es uniforme entre algoritmos.

5. **Comportamientos complementarios**: Se identifican algoritmos con fortalezas complementarias (rápida convergencia inicial vs. refinamiento tardío), sugiriendo potencial para enfoques híbridos.

## Trabajo Futuro

1. **Algoritmos híbridos adaptables**: Desarrollar algoritmos que combinen las estrategias de exploración temprana de HOA/FGO con las capacidades de refinamiento tardío de GTO/FOA.

2. **Estrategias de parametrización dinámica**: Implementar ajuste dinámico de parámetros basado en la fase de convergencia para optimizar el balance exploración/explotación.

3. **Especialización por tipo de instancia**: Investigar la relación entre características de instancias VRP y rendimiento algorítmico para desarrollar heurísticas de selección de algoritmos.

4. **Criterios de parada adaptables**: Crear mecanismos inteligentes de terminación basados en patrones de convergencia para optimizar el uso de recursos computacionales.

5. **Benchmark extendido**: Ampliar el estudio a un conjunto más diverso de instancias VRP, incluyendo variantes con restricciones adicionales (ventanas de tiempo, múltiples depósitos, etc.).

---

*Análisis realizado el 8 de mayo de 2025*