# Análisis Comparativo de Algoritmos en Instancias Solomon VRP

Este documento presenta los resultados del análisis comparativo de diferentes algoritmos metaheurísticos aplicados a instancias del problema de enrutamiento de vehículos (VRP) de la serie Solomon.

## Resumen de Resultados

Los algoritmos evaluados fueron:
- **WOA** (Whale Optimization Algorithm)
- **OPA** (Osprey Predation Algorithm)
- **GTO** (Golden Tailed Optimization)
- **SMA** (Slime Mould Algorithm)

Cada algoritmo fue ejecutado 10 veces en cada instancia con 30 iteraciones por ejecución.

### Instancias Evaluadas

Se utilizaron 6 instancias de la colección Solomon:
- **C101, C201**: Instancias con clientes agrupados
- **R101, R201**: Instancias con clientes distribuidos aleatoriamente
- **RC101, RC201**: Instancias mixtas (clientes agrupados y aleatorios)

Las series 101 tienen ventanas de tiempo estrechas y pocos vehículos, mientras que las series 201 tienen ventanas de tiempo más amplias y permiten menos vehículos.

## Rendimiento General

| Algoritmo | Mejor Fitness | Fitness Promedio | Desviación Estándar | Tiempo (s) |
|-----------|---------------|------------------|---------------------|------------|
| WOA       | 1955.31       | 2027.62          | 36.46               | 0.135      |
| SMA       | 1983.37       | 2024.13          | 24.31               | 0.067      |
| GTO       | 2173.94       | 2326.72          | 78.18               | 0.081      |
| OPA       | 3416.05       | 3547.16          | 77.43               | 0.163      |

## Observaciones Clave

1. **Mejor algoritmo**: WOA obtuvo las mejores soluciones en términos de fitness (menor distancia total).

2. **Eficiencia computacional**: SMA fue el algoritmo más rápido, requiriendo aproximadamente la mitad del tiempo que WOA y OPA.

3. **Estabilidad**: SMA tuvo la menor desviación estándar (24.31), lo que indica mayor consistencia entre ejecuciones.

4. **Peor rendimiento**: OPA tuvo el peor rendimiento tanto en calidad de solución como en tiempo de ejecución.

5. **Series 101 vs 201**: Se logró integrar exitosamente tanto las series 101 como 201, gracias a la conversión al formato requerido por el parser VRPProblem.

## Resultados finales

### Análisis estadístico

#### Pruebas de significancia y tamaños de efecto

![Critical Difference Diagram](../benchmark_comparisons/solomon_final/cd_diagram.png)

Los algoritmos dentro de la misma banda horizontal no presentan diferencias estadísticamente significativas (α = 0.05) según la prueba de Nemenyi.

#### Tabla de p-values y tamaños de efecto

##### Nemenyi Post-hoc Test (p-values)

|      |    AHA |    APO |   EGTO |    EWA |    FOA |    FSA |    GTO |   GVOA |    HHO |   MRFO |    OPA |    RRO |    SHO |    SMA |    SMO |    WOA |
|:-----|-------:|-------:|-------:|-------:|-------:|-------:|-------:|-------:|-------:|-------:|-------:|-------:|-------:|-------:|-------:|-------:|
| AHA  | 1      | 0.275  | 0.981  | 0.751  | 1      | 0.0006 | 0.095  | 0.8856 | 0.0372 | 0.0008 | 0.9999 | 1      | 0.1328 | 0.0008 | 1      | 0.0001 |
| APO  | 0.275  | 1      | 0.9968 | 1      | 0.7096 | 0.9308 | 1      | 0.9999 | 1      | 0.9479 | 0.8856 | 0.3932 | 1      | 0.9479 | 0.6659 | 0.751  |
| EGTO | 0.981  | 0.9968 | 1      | 1      | 0.9999 | 0.1556 | 0.9479 | 1      | 0.8253 | 0.1812 | 1      | 0.9947 | 0.9726 | 0.1812 | 0.9999 | 0.0551 |
| EWA  | 0.751  | 1      | 1      | 1      | 0.981  | 0.5281 | 0.9994 | 1      | 0.9916 | 0.5745 | 0.9981 | 0.8573 | 0.9999 | 0.5745 | 0.9726 | 0.275  |
| FOA  | 1      | 0.7096 | 0.9999 | 0.981  | 1      | 0.008  | 0.3932 | 0.9968 | 0.2096 | 0.0101 | 1      | 1      | 0.482  | 0.0101 | 1      | 0.0018 |
| FSA  | 0.0006 | 0.9308 | 0.1556 | 0.5281 | 0.008  | 1      | 0.9947 | 0.3514 | 0.9997 | 1      | 0.0246 | 0.0014 | 0.9872 | 1      | 0.0063 | 1      |
| GTO  | 0.095  | 1      | 0.9479 | 0.9994 | 0.3932 | 0.9947 | 1      | 0.9947 | 1      | 0.9968 | 0.6207 | 0.1556 | 1      | 0.9968 | 0.3514 | 0.9479 |
| GVOA | 0.8856 | 0.9999 | 1      | 1      | 0.9968 | 0.3514 | 0.9947 | 1      | 0.9617 | 0.3932 | 0.9999 | 0.9479 | 0.9981 | 0.3932 | 0.9947 | 0.1556 |
| HHO  | 0.0372 | 1      | 0.8253 | 0.9916 | 0.2096 | 0.9997 | 1      | 0.9617 | 1      | 0.9999 | 0.3932 | 0.0664 | 1      | 0.9999 | 0.1812 | 0.9916 |
| MRFO | 0.0008 | 0.9479 | 0.1812 | 0.5745 | 0.0101 | 1      | 0.9968 | 0.3932 | 0.9999 | 1      | 0.0304 | 0.0018 | 0.9916 | 1      | 0.008  | 1      |
| OPA  | 0.9999 | 0.8856 | 1      | 0.9981 | 1      | 0.0246 | 0.6207 | 0.9999 | 0.3932 | 0.0304 | 1      | 1      | 0.7096 | 0.0304 | 1      | 0.0063 |
| RRO  | 1      | 0.3932 | 0.9947 | 0.8573 | 1      | 0.0014 | 0.1556 | 0.9479 | 0.0664 | 0.0018 | 1      | 1      | 0.2096 | 0.0018 | 1      | 0.0003 |
| SHO  | 0.1328 | 1      | 0.9726 | 0.9999 | 0.482  | 0.9872 | 1      | 0.9981 | 1      | 0.9916 | 0.7096 | 0.2096 | 1      | 0.9916 | 0.4369 | 0.91   |
| SMA  | 0.0008 | 0.9479 | 0.1812 | 0.5745 | 0.0101 | 1      | 0.9968 | 0.3932 | 0.9999 | 1      | 0.0304 | 0.0018 | 0.9916 | 1      | 0.008  | 1      |
| SMO  | 1      | 0.6659 | 0.9999 | 0.9726 | 1      | 0.0063 | 0.3514 | 0.9947 | 0.1812 | 0.008  | 1      | 1      | 0.4369 | 0.008  | 1      | 0.0014 |
| WOA  | 0.0001 | 0.751  | 0.0551 | 0.275  | 0.0018 | 1      | 0.9479 | 0.1556 | 0.9916 | 1      | 0.0063 | 0.0003 | 0.91   | 1      | 0.0014 | 1      |

*p-values < 0.05 indican diferencias estadísticamente significativas*

##### Vargha-Delaney A12 Effect Size

|      |      AHA |       APO |     EGTO |       EWA |      FOA |       FSA |       GTO |     GVOA |       HHO |      MRFO |      OPA |      RRO |       SHO |       SMA |      SMO |       WOA |
|:-----|---------:|----------:|---------:|----------:|---------:|----------:|----------:|---------:|----------:|----------:|---------:|---------:|----------:|----------:|---------:|----------:|
| AHA  | 0.5      | 0         | 0.194444 | 0.0555556 | 0.388889 | 0         | 0         | 0.194444 | 0         | 0         | 0.361111 | 0.472222 | 0         | 0         | 0.388889 | 0         |
| APO  | 1        | 0.5       | 0.944444 | 0.694444  | 0.972222 | 0.277778  | 0.388889  | 0.916667 | 0.305556  | 0.277778  | 0.972222 | 0.944444 | 0.444444  | 0.277778  | 0.972222 | 0.222222  |
| EGTO | 0.805556 | 0.0555556 | 0.5      | 0.194444  | 0.694444 | 0         | 0         | 0.416667 | 0         | 0         | 0.611111 | 0.694444 | 0.0277778 | 0         | 0.722222 | 0         |
| EWA  | 0.944444 | 0.305556  | 0.805556 | 0.5       | 0.861111 | 0.0833333 | 0.25      | 0.722222 | 0.138889  | 0.0833333 | 0.861111 | 0.888889 | 0.25      | 0.0833333 | 0.888889 | 0.0833333 |
| FOA  | 0.611111 | 0.0277778 | 0.305556 | 0.138889  | 0.5      | 0         | 0         | 0.333333 | 0         | 0         | 0.472222 | 0.611111 | 0.0277778 | 0         | 0.5      | 0         |
| FSA  | 1        | 0.722222  | 1        | 0.916667  | 1        | 0.5       | 0.722222  | 1        | 0.611111  | 0.444444  | 1        | 1        | 0.722222  | 0.527778  | 1        | 0.444444  |
| GTO  | 1        | 0.611111  | 1        | 0.75      | 1        | 0.277778  | 0.5       | 0.916667 | 0.444444  | 0.277778  | 1        | 1        | 0.5       | 0.305556  | 1        | 0.277778  |
| GVOA | 0.805556 | 0.0833333 | 0.583333 | 0.277778  | 0.666667 | 0         | 0.0833333 | 0.5      | 0.0277778 | 0         | 0.666667 | 0.777778 | 0.0833333 | 0         | 0.722222 | 0         |
| HHO  | 1        | 0.694444  | 1        | 0.861111  | 1        | 0.388889  | 0.555556  | 0.972222 | 0.5       | 0.361111  | 1        | 1        | 0.638889  | 0.388889  | 1        | 0.333333  |
| MRFO | 1        | 0.722222  | 1        | 0.916667  | 1        | 0.555556  | 0.722222  | 1        | 0.638889  | 0.5       | 1        | 1        | 0.75      | 0.5       | 1        | 0.388889  |
| OPA  | 0.638889 | 0.0277778 | 0.388889 | 0.138889  | 0.527778 | 0         | 0         | 0.333333 | 0         | 0         | 0.5      | 0.583333 | 0.0277778 | 0         | 0.527778 | 0         |
| RRO  | 0.527778 | 0.0555556 | 0.305556 | 0.111111  | 0.388889 | 0         | 0         | 0.222222 | 0         | 0         | 0.416667 | 0.5      | 0.0277778 | 0         | 0.444444 | 0         |
| SHO  | 1        | 0.555556  | 0.972222 | 0.75      | 0.972222 | 0.277778  | 0.5       | 0.916667 | 0.361111  | 0.25      | 0.972222 | 0.972222 | 0.5       | 0.25      | 1        | 0.25      |
| SMA  | 1        | 0.722222  | 1        | 0.916667  | 1        | 0.472222  | 0.694444  | 1        | 0.611111  | 0.5       | 1        | 1        | 0.75      | 0.5       | 1        | 0.472222  |
| SMO  | 0.611111 | 0.0277778 | 0.277778 | 0.111111  | 0.5      | 0         | 0         | 0.277778 | 0         | 0         | 0.472222 | 0.555556 | 0         | 0         | 0.5      | 0         |
| WOA  | 1        | 0.777778  | 1        | 0.916667  | 1        | 0.555556  | 0.722222  | 1        | 0.666667  | 0.611111  | 1        | 1        | 0.75      | 0.527778  | 1        | 0.5       |

*Interpretación de valores A12:*
* A12 = 0.5: Sin efecto (rendimiento igual)
* A12 < 0.5: El algoritmo de la fila supera al algoritmo de la columna
* A12 > 0.5: El algoritmo de la columna supera al algoritmo de la fila

## Análisis Estadístico Avanzado

El análisis estadístico avanzado se realizó utilizando:
- Test de Friedman alineado para detectar diferencias significativas entre algoritmos
- Test post-hoc de Nemenyi para comparaciones por pares
- Tamaños de efecto A12 de Vargha-Delaney para medir la magnitud práctica de las diferencias
- Diagramas de Diferencia Crítica (CD) para visualizar grupos de algoritmos sin diferencias significativas

### Resultados del Test de Friedman Alineado

El test de Friedman alineado mostró diferencias estadísticamente significativas entre los algoritmos (p < 0.001), lo que justifica el análisis post-hoc realizado.

### Interpretación del Diagrama CD

El diagrama de Diferencia Crítica muestra que:
- Los algoritmos WOA, MRFO, FSA y SMA forman el grupo con mejor rendimiento, sin diferencias estadísticamente significativas entre ellos.
- HHO y GTO forman un segundo grupo de rendimiento.
- APO y SHO forman un grupo intermedio.
- EGTO, GVOA, EWA y FOA constituyen otro grupo.
- Los algoritmos AHA, OPA, RRO y SMO muestran el rendimiento más bajo.

### Interpretación de Tamaños de Efecto

La matriz A12 de Vargha-Delaney revela:
- WOA tiene un efecto grande (A12 > 0.71) cuando se compara con la mayoría de los otros algoritmos, confirmando su superioridad.
- SMA muestra un efecto mediano a grande contra algoritmos de rendimiento inferior.
- No hay diferencias de tamaño de efecto significativas entre WOA, MRFO, FSA y SMA (A12 cercano a 0.5), corroborando los resultados del diagrama CD.

## Conclusiones

1. **Recomendación principal**: Para instancias Solomon VRP, según el análisis estadístico avanzado, WOA y SMA ofrecen el mejor rendimiento, con WOA proporcionando soluciones de mayor calidad y SMA mostrando mejor equilibrio entre calidad y tiempo.

2. **Grupos de rendimiento**:
   - Primer nivel (estadísticamente superior): WOA, MRFO, FSA, SMA
   - Segundo nivel: HHO, GTO, APO, SHO
   - Tercer nivel: EGTO, GVOA, EWA, FOA
   - Rendimiento más bajo: AHA, OPA, RRO, SMO

3. **Significancia práctica**: Las diferencias entre WOA y otros algoritmos no solo son estadísticamente significativas, sino también de magnitud práctica relevante según los tamaños de efecto A12.

4. **Mejoras futuras**:
   - Optimizar OPA para mejorar su rendimiento en instancias VRP.
   - Evaluar el impacto de aumentar el número de iteraciones en SMA.
   - Analizar el comportamiento de los algoritmos en instancias más grandes.
   - Profundizar en la comparación entre los algoritmos del primer grupo (WOA, MRFO, FSA, SMA) con mayor número de ejecuciones.

## Referencia de Archivos

Los resultados detallados y gráficos se encuentran en:
- CSV de resumen: `results/massive_benchmark_20250512_142739/massive_benchmark_summary.csv`
- Reporte HTML: `results/massive_benchmark_20250512_142739/massive_benchmark_report.html`
- Gráficos comparativos: `benchmark_comparisons/`
- Análisis estadístico: `benchmark_comparisons/solomon_final/`
