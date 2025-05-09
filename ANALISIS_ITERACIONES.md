# Análisis de Impacto del Número de Iteraciones en Algoritmos Metaheurísticos

Este documento presenta un análisis detallado del impacto que tiene el número de iteraciones en el rendimiento de diferentes algoritmos metaheurísticos aplicados al Problema de Ruteo de Vehículos (VRP).

## Configuración Experimental

- **Instancia de prueba:** E-n22-k4 (22 nodos, 4 vehículos)
- **Algoritmos evaluados:** 11 algoritmos bioinspirados (HHO, WOA, EWA, SMA, MRFO, GTO, EGTO, FOA, FGO, HOA, APO)
- **Parámetros de ejecución:**
  - Iteraciones: 10, 100, 1000
  - Tamaño de población: 30
  - Ejecuciones por algoritmo y configuración: 1
  - Semilla fija: 42 (para asegurar reproducibilidad)
- **Valor óptimo conocido:** 375.28 (para la instancia E-n22-k4)

## Resultados Comparativos

### Mejores Soluciones por Algoritmo y Número de Iteraciones

| Algoritmo | 10 iteraciones | 100 iteraciones | 1000 iteraciones | Mejora 10→100 | Mejora 100→1000 | Mejora Total |
|-----------|---------------|-----------------|------------------|--------------|----------------|--------------|
| GTO       | 568.87        | 522.09          | 426.29           | 8.2%         | 18.4%          | 25.1%        |
| FOA       | 650.78        | 523.21          | 437.04           | 19.6%        | 16.5%          | 32.8%        |
| HOA       | 651.43        | 471.68          | 452.58           | 27.6%        | 4.0%           | 30.5%        |
| MRFO      | 507.20        | 475.64          | 459.65           | 6.2%         | 3.4%           | 9.4%         |
| HHO       | 561.98        | 538.69          | 475.13           | 4.1%         | 11.8%          | 15.4%        |
| EGTO      | 600.11        | 520.47          | 474.30           | 13.3%        | 8.9%           | 21.0%        |
| WOA       | 525.75        | 476.21          | 476.41           | 9.4%         | -0.04%         | 9.4%         |
| EWA       | 564.47        | 507.32          | 479.12           | 10.1%        | 5.6%           | 15.1%        |
| SMA       | 537.72        | 539.99          | 489.30           | -0.4%        | 9.4%           | 9.0%         |
| FGO       | 515.55        | 496.49          | 494.98           | 3.7%         | 0.3%           | 4.0%         |
| APO       | 597.50        | 544.41          | 531.42           | 8.9%         | 2.4%           | 11.1%        |

*Nota: Los valores de mejora representan el porcentaje de reducción en el fitness (menor es mejor).

### Tiempo de Ejecución (segundos)

| Algoritmo | 10 iteraciones | 100 iteraciones | 1000 iteraciones | Factor 10→100 | Factor 100→1000 |
|-----------|---------------|-----------------|------------------|--------------|-----------------|
| EGTO      | 0.00          | 0.04            | 0.38             | ∞            | 9.5x            |
| GTO       | 0.01          | 0.06            | 0.57             | 6.0x         | 9.5x            |
| APO       | 0.01          | 0.05            | 0.54             | 5.0x         | 10.8x           |
| HHO       | 0.01          | 0.07            | 0.65             | 7.0x         | 9.3x            |
| WOA       | 0.01          | 0.07            | 0.64             | 7.0x         | 9.1x            |
| MRFO      | 0.01          | 0.06            | 0.63             | 6.0x         | 10.5x           |
| EWA       | 0.01          | 0.09            | 0.92             | 9.0x         | 10.2x           |
| HOA       | 0.01          | 0.12            | 1.16             | 12.0x        | 9.7x            |
| FOA       | 0.02          | 0.18            | 1.83             | 9.0x         | 10.2x           |
| FGO       | 0.03          | 0.26            | 2.58             | 8.7x         | 9.9x            |
| SMA       | 0.04          | 0.40            | 4.03             | 10.0x        | 10.1x           |

## Análisis por Algoritmo

### GTO (Gorilla Troops Optimization)
- **Mejora más significativa:** Mostró la mayor mejora entre 100 y 1000 iteraciones (18.4%)
- **Mejor solución:** 426.29 (13.6% sobre el óptimo)
- **Comportamiento:** Mejora continua y sustancial a medida que aumentan las iteraciones
- **Eficiencia:** Mantiene buena eficiencia incluso con 1000 iteraciones (0.57s)
- **Destaca por:** Alcanzar la segunda mejor solución global con 1000 iteraciones

### FOA (Forest Optimization Algorithm)
- **Mejora más significativa:** Mostró la mayor mejora total (32.8%) desde 10 a 1000 iteraciones
- **Mejor solución:** 437.04 (16.5% sobre el óptimo)
- **Comportamiento:** Mejora dramática con más iteraciones, especialmente entre 10 y 100
- **Eficiencia:** Tiempo moderado-alto (1.83s con 1000 iteraciones)
- **Destaca por:** Tercera mejor solución global con la mayor mejora porcentual total

### HOA (Hyena Optimization Algorithm)
- **Mejora más significativa:** Mayor mejora entre 10 y 100 iteraciones (27.6%)
- **Mejor solución:** 452.58 (20.6% sobre el óptimo)
- **Comportamiento:** Rápida convergencia inicial, con menor mejora en iteraciones posteriores
- **Eficiencia:** Tiempo moderado-alto (1.16s con 1000 iteraciones)
- **Destaca por:** Mejora más pronunciada en las primeras 100 iteraciones

### MRFO (Manta Ray Foraging Optimization)
- **Mejora más significativa:** Mejora constante pero moderada (9.4% total)
- **Mejor solución:** 459.65 (22.5% sobre el óptimo)
- **Comportamiento:** Mejora gradual y estable con más iteraciones
- **Eficiencia:** Buena eficiencia (0.63s con 1000 iteraciones)
- **Destaca por:** Consistencia y buen balance entre calidad y tiempo

### EGTO (Enhanced Gorilla Troops Optimization)
- **Mejora más significativa:** Buena mejora entre 10 y 100 iteraciones (13.3%)
- **Mejor solución:** 474.30 (26.4% sobre el óptimo)
- **Comportamiento:** Mejora notable con iteraciones adicionales
- **Eficiencia:** El algoritmo más rápido (0.38s con 1000 iteraciones)
- **Destaca por:** Excelente balance eficiencia-calidad

### WOA (Whale Optimization Algorithm)
- **Mejora más significativa:** Mejora notable entre 10 y 100 iteraciones (9.4%)
- **Mejor solución:** 476.21 (26.9% sobre el óptimo)
- **Comportamiento:** Converge rápidamente, con poco o ningún beneficio después de 100 iteraciones
- **Eficiencia:** Buena eficiencia (0.64s con 1000 iteraciones)
- **Destaca por:** Rápida convergencia; más iteraciones no mejoran significativamente la solución

### HHO (Harris Hawks Optimization)
- **Mejora más significativa:** Mejora importante entre 100 y 1000 iteraciones (11.8%)
- **Mejor solución:** 475.13 (26.6% sobre el óptimo)
- **Comportamiento:** Mejora más notable en fase tardía (100-1000 iteraciones)
- **Eficiencia:** Buena eficiencia (0.65s con 1000 iteraciones)
- **Destaca por:** Patrón de mejora inverso al de HOA, con mejores resultados en etapas tardías

### EWA (Earthworm Algorithm)
- **Mejora más significativa:** Mejora constante que se mantiene incluso con iteraciones extendidas (ver análisis extendido)
- **Mejor solución:** 479.12 (27.7% sobre el óptimo) con 1000 iteraciones; 447.05 (19.2%) con 10000 iteraciones
- **Comportamiento:** Mejora gradual en todas las fases sin signos de estancamiento
- **Eficiencia:** Tiempo moderado (0.92s con 1000 iteraciones); 8.05s con 10000 iteraciones
- **Destaca por:** Comportamiento equilibrado y mejora consistente incluso en ejecuciones muy largas
- **Nota:** Análisis extendido muestra que alcanza 436.56 (16.4% sobre el óptimo) con 10000 iteraciones y población 50

### SMA (Slime Mould Algorithm)
- **Mejora más significativa:** Mejora solo en fase tardía (9.4% entre 100-1000 iteraciones)
- **Mejor solución:** 489.30 (30.4% sobre el óptimo)
- **Comportamiento:** Inicialmente empeora ligeramente, luego mejora significativamente
- **Eficiencia:** El algoritmo más lento (4.03s con 1000 iteraciones)
- **Destaca por:** Comportamiento atípico (empeora antes de mejorar)

### FGO (Flamingo Optimization)
- **Mejora más significativa:** Mejora mínima (4.0% total)
- **Mejor solución:** 494.98 (31.9% sobre el óptimo)
- **Comportamiento:** Converge muy rápidamente, con mínima mejora después de 100 iteraciones
- **Eficiencia:** Tiempo alto (2.58s con 1000 iteraciones)
- **Destaca por:** Rápida convergencia inicial pero estancamiento posterior

### APO (Artificial Protozoa Optimizer)
- **Mejora más significativa:** Mejora moderada (11.1% total)
- **Mejor solución:** 531.42 (41.6% sobre el óptimo)
- **Comportamiento:** Mejora gradual pero limitada
- **Eficiencia:** Buena eficiencia (0.54s con 1000 iteraciones)
- **Destaca por:** Rendimiento inferior a otros algoritmos incluso con 1000 iteraciones

## Patrones Observados

### Patrones de Convergencia

Identificamos cuatro patrones principales de convergencia:

1. **Mejora Constante:** Algoritmos que muestran mejora significativa tanto en etapas tempranas como tardías (GTO, FOA, EGTO, EWA).
   - Nota: El análisis extendido de EWA hasta 10000 iteraciones confirmó que este patrón se mantiene incluso en ejecuciones extremadamente largas, sin signos claros de estancamiento.

2. **Convergencia Temprana:** Algoritmos que convergen rápidamente y muestran poca mejora después de 100 iteraciones (WOA, FGO, HOA).

3. **Convergencia Tardía:** Algoritmos que mejoran más significativamente en etapas avanzadas (HHO, SMA).

4. **Mejora Gradual Limitada:** Algoritmos que mejoran de forma constante pero moderada (MRFO, APO).

### Eficiencia Computacional vs. Número de Iteraciones

- La relación entre tiempo de ejecución e iteraciones es aproximadamente lineal para la mayoría de los algoritmos
- El factor de aumento de tiempo entre 10→100 y 100→1000 iteraciones es similar (aproximadamente 10x)
- Algunos algoritmos muestran ligeras desviaciones, posiblemente debido a operaciones de inicialización o complejidades específicas del algoritmo

### Balance Calidad-Eficiencia

Considerando tanto la calidad de la solución como el tiempo de ejecución con 1000 iteraciones:

1. **Mejor Balance:** GTO, EGTO, MRFO y HOA ofrecen el mejor equilibrio entre calidad de solución y eficiencia
2. **Alta Calidad / Alto Costo:** FOA ofrece excelente calidad pero con tiempo computacional significativo
3. **Baja Calidad / Bajo Costo:** APO es eficiente pero ofrece soluciones de menor calidad
4. **Peor Balance:** SMA combina tiempo alto con calidad moderada

## Conclusiones Generales

1. **Número óptimo de iteraciones:**
   - Para la mayoría de los algoritmos, 100 iteraciones ofrecen un buen balance entre calidad y costo computacional
   - GTO, FOA y HHO se benefician significativamente de 1000 iteraciones
   - EWA muestra mejora continua incluso hasta 10000 iteraciones (ver análisis extendido)
   - WOA y FGO alcanzan convergencia efectiva con solo 100 iteraciones

2. **Mejor algoritmo según iteraciones:**
   - Con 10 iteraciones: FGO ofrece el mejor resultado inicial (515.55)
   - Con 100 iteraciones: HOA proporciona el mejor resultado (471.68)
   - Con 1000 iteraciones: GTO alcanza la mejor solución global (426.29)
   - Con 10000 iteraciones: EWA alcanza 447.05 (19.2% sobre el óptimo), mejorando a 436.56 (16.4%) con población 50

3. **Recomendaciones prácticas:**
   - Para resultados rápidos: WOA con 100 iteraciones ofrece buen balance
   - Para máxima calidad: GTO con 1000 iteraciones proporciona los mejores resultados en tiempo razonable
   - Para aplicaciones donde el tiempo no es crítico: EWA con 10000 iteraciones y población 50
   - Para máxima eficiencia: EGTO con 100 iteraciones ofrece resultados aceptables en tiempo mínimo

4. **Diferencias de comportamiento:**
   - El comportamiento varía significativamente entre algoritmos, lo que indica diferentes mecanismos de exploración/explotación
   - Las mejoras con más iteraciones no son uniformes, algunos algoritmos tienen puntos de inflexión donde la mejora se acelera o desacelera

## Implicaciones para Investigación y Aplicaciones

1. **Investigación:**
   - Los resultados destacan la importancia de evaluar algoritmos con diferentes números de iteraciones
   - La comparación de algoritmos debe considerar tanto resultados como patrones de convergencia

2. **Aplicaciones prácticas:**
   - Para aplicaciones en tiempo real, algoritmos con convergencia temprana como WOA serían preferibles
   - Para planificación offline donde la calidad es prioritaria, GTO con alto número de iteraciones es recomendable
   - Para sistemas híbridos, combinar la exploración inicial de HOA con la explotación tardía de HHO podría ser beneficioso

3. **Trabajo futuro:**
   - Desarrollar criterios de parada adaptativos basados en los patrones de convergencia identificados
   - Investigar hibridaciones que combinen la rápida convergencia inicial de algoritmos como HOA con la capacidad de refinamiento tardío de GTO
   - Analizar el impacto del tamaño de población en relación con el número de iteraciones

---

**Nota:** Se ha realizado un análisis extendido del algoritmo EWA con mayor número de iteraciones (hasta 10000) y variación en el tamaño de población. Los resultados completos de este estudio se encuentran en el documento [ANALISIS_ITERACIONES_EXTENDIDO.md](/docs/ANALISIS_ITERACIONES_EXTENDIDO.md).

---

*Análisis inicial realizado el 8 de mayo de 2025*
*Actualizado el 9 de mayo de 2025 con análisis extendido de EWA*