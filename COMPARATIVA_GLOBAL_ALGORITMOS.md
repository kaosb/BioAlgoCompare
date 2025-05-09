# Comparativa Global de Algoritmos Metaheurísticos para VRP

Este documento presenta un análisis comparativo de todos los algoritmos metaheurísticos implementados para la resolución del Problema de Ruteo de Vehículos (VRP), basado en ejecuciones sistemáticas y análisis de resultados.

## Configuración Experimental

- **Instancia de prueba:** E-n22-k4 (22 nodos, 4 vehículos)
- **Algoritmos evaluados:** 11 algoritmos bioinspirados (HOA, APO, EGTO, FGO, FOA, WOA, HHO, MRFO, SMA, GTO, EWA)
- **Parámetros de ejecución:**
  - Iteraciones: 100
  - Tamaño de población: 30
  - Ejecuciones por algoritmo: 5
  - Semilla fija: 42 (para asegurar reproducibilidad)
- **Valor óptimo conocido:** 375.28 (para la instancia E-n22-k4)

## Resultados Comparativos

### Calidad de Solución (Fitness)

| Algoritmo | Mejor Fitness | Fitness Promedio | Desviación Estándar | % sobre óptimo |
|-----------|---------------|------------------|---------------------|----------------|
| WOA       | 448.75        | 464.88           | 11.91               | 19.58%         |
| HOA       | 460.62        | 483.60           | 21.94               | 22.74%         |
| FGO       | 461.55        | 475.18           | 14.54               | 23.01%         |
| MRFO      | 468.08        | 488.22           | 19.87               | 24.73%         |
| HHO       | 505.13        | 539.44           | 20.34               | 34.60%         |
| GTO       | 488.49        | 508.92           | 22.39               | 30.17%         |
| EWA       | 501.87        | 510.29           | 9.84                | 33.73%         |
| APO       | 496.38        | 553.38           | 36.66               | 32.27%         |
| SMA       | 504.41        | 525.93           | 28.90               | 34.41%         |
| FOA       | 502.71        | 533.90           | 23.17               | 33.96%         |
| EGTO      | 520.07        | 545.96           | 26.50               | 38.58%         |

### Eficiencia Computacional (Tiempo)

| Algoritmo | Tiempo Promedio (s) | Desviación Estándar |
|-----------|---------------------|---------------------|
| EGTO      | 0.0375              | 0.0002              |
| APO       | 0.0532              | 0.0008              |
| GTO       | 0.0572              | 0.0005              |
| MRFO      | 0.0626              | 0.0005              |
| WOA       | 0.0641              | 0.0003              |
| HHO       | 0.0651              | 0.0009              |
| EWA       | 0.0945              | 0.0014              |
| HOA       | 0.1148              | 0.0018              |
| FOA       | 0.1829              | 0.0017              |
| FGO       | 0.2637              | 0.0046              |
| SMA       | 0.3979              | 0.0040              |

### Balance Rendimiento-Eficiencia

Ordenando los algoritmos por un índice de rendimiento que combina calidad de solución (mejores valores tienen mayor peso) y eficiencia computacional, obtenemos:

1. **WOA** - Mejor balance general: excelente calidad de solución (mejor fitness: 448.75) con eficiencia computacional competitiva (0.064s).
2. **HOA** - Segunda mejor solución (460.62) pero tiempo moderado (0.115s).
3. **FGO** - Buena calidad de solución (461.55) pero tiempo alto (0.264s).
4. **MRFO** - Buena calidad de solución (468.08) con eficiencia competitiva (0.063s).
5. **GTO** - Calidad moderada (488.49) con buena eficiencia (0.057s).
6. **EGTO** - Calidad inferior (520.07) pero tiempo excepcional (0.038s, el más rápido).
7. **EWA** - Calidad moderada (501.87) con tiempo moderado (0.095s).
8. **HHO** - Calidad moderada en esta prueba (505.13) con tiempo moderado (0.065s).
9. **APO** - Calidad moderada (496.38) con buena eficiencia (0.053s).
10. **FOA** - Calidad inferior (502.71) con tiempo alto (0.183s).
11. **SMA** - Calidad inferior (504.41) con el tiempo más alto (0.398s).

## Análisis de Estabilidad

La estabilidad de un algoritmo, medida por su desviación estándar, indica su consistencia para encontrar soluciones de calidad similar en diferentes ejecuciones:

1. **EWA** - Mayor estabilidad (9.84)
2. **WOA** - Excelente estabilidad (11.91)
3. **FGO** - Buena estabilidad (14.54)
4. **MRFO** - Estabilidad moderada (19.87)
5. **HHO** - Estabilidad moderada (20.34)
6. **HOA** - Estabilidad moderada (21.94)
7. **GTO** - Estabilidad moderada (22.39)
8. **FOA** - Estabilidad moderada (23.17)
9. **EGTO** - Alta variabilidad (26.50)
10. **SMA** - Alta variabilidad (28.90)
11. **APO** - La mayor variabilidad (36.66)

## Comparación con Análisis Previos

Estos resultados muestran algunas diferencias con respecto a análisis previos realizados con otras instancias y configuraciones:

1. **Comportamiento del algoritmo HHO**: En análisis con 1000 ejecuciones sobre la instancia P-n16-k8, HHO alcanzó el mejor rendimiento (410.93, equivalente al 8.68% de mejora). Sin embargo, en la presente prueba con E-n22-k4, su rendimiento fue menos destacado (505.13, 34.60% sobre el óptimo). Esto sugiere que HHO puede ser sensible a las características específicas de la instancia y podría requerir ajustes para cada tipo de problema.

2. **Consistencia de WOA**: En ambos análisis, WOA ha mostrado un rendimiento destacado, lo que sugiere que es un algoritmo altamente versátil y robusto para diferentes instancias VRP.

3. **Rendimiento de GTO**: Mientras que en análisis previos con la implementación final de GTO se alcanzó el óptimo (410.93), en la presente prueba su rendimiento fue moderado (488.49). Esto podría requerir una revisión adicional de la implementación para garantizar consistencia.

4. **EGTO vs GTO**: Contrario a lo esperado, EGTO (versión mejorada de GTO) muestra un peor rendimiento que GTO en términos de calidad de solución, aunque es significativamente más rápido. Esto confirma lo observado en análisis previos y sugiere que las mejoras teóricas en EGTO podrían no estar optimizadas para problemas VRP.

## Conclusiones Generales

1. **Algoritmo más eficaz para VRP**: WOA (Whale Optimization Algorithm) demuestra el mejor balance entre calidad de solución y eficiencia computacional en esta instancia, seguido por HOA (Hyena Optimization Algorithm) y FGO (Flamingo Optimization Algorithm).

2. **Algoritmo más rápido**: EGTO (Enhanced Gorilla Troops Optimization) es el algoritmo más rápido, pero con una calidad de solución inferior.

3. **Algoritmo más estable**: EWA (Earthworm Algorithm) y WOA muestran la mayor estabilidad, lo que los hace recomendables para aplicaciones donde se requiere consistencia en los resultados.

4. **Mayor variabilidad**: APO (Artificial Protozoa Optimizer) muestra la mayor variabilidad, lo que podría indicar un potencial para encontrar diversas soluciones, pero también menor confiabilidad.

5. **Algoritmo con peor balance eficacia-eficiencia**: SMA (Slime Mould Algorithm) combina una calidad de solución inferior con el tiempo de ejecución más alto, resultando en el peor balance eficacia-eficiencia.

## Recomendaciones Prácticas

1. **Para aplicaciones generales de VRP**: Utilizar WOA como primera opción, ofreciendo el mejor balance general.

2. **Para aplicaciones con restricciones de tiempo críticas**: Considerar EGTO, que sacrifica calidad de solución pero ofrece tiempos de ejecución excepcionalmente rápidos.

3. **Para exploración de espacios de solución diversos**: APO podría ser útil debido a su alta variabilidad, complementando otros enfoques.

4. **Para aplicaciones que requieren alta consistencia**: EWA y WOA son las opciones más estables.

5. **Para entornos híbridos**: Combinar WOA o HOA (calidad) con EGTO (velocidad) podría resultar en enfoques híbridos prometedores.

## Trabajo Futuro

1. **Análisis con más instancias**: Extender este análisis a un conjunto más amplio de instancias VRP para verificar la consistencia de estos hallazgos.

2. **Optimización de parámetros**: Analizar el impacto de diferentes configuraciones de parámetros específicos para cada algoritmo.

3. **Algoritmos híbridos**: Desarrollar y evaluar algoritmos híbridos que combinen las fortalezas de WOA/HOA (calidad) con EGTO (velocidad).

4. **Análisis de escalabilidad**: Evaluar el comportamiento de estos algoritmos en instancias VRP de mayor tamaño para determinar su escalabilidad.

---

*Análisis realizado el 8 de mayo de 2025*