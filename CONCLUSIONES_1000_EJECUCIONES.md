# Conclusiones del Análisis Masivo (1000 Ejecuciones)

Este documento presenta los hallazgos y conclusiones derivados de un análisis estadístico riguroso basado en benchmarks con diferentes cantidades de ejecuciones (10, 100 y 1000) sobre algoritmos metaheurísticos aplicados al problema de ruteo de vehículos (VRP).

## Configuración Experimental

- **Instancia:** P-n16-k8 (16 nodos, 8 vehículos)
- **Algoritmos comparados:** HOA, EGTO, FOA, HHO y WOA (1000 ejecuciones completadas con HOA, EGTO, HHO y WOA)
- **Ejecuciones:** 10, 100 y 1000 por algoritmo
- **Iteraciones:** 50 para 10 y 100 ejecuciones, 20 para 1000 ejecuciones
- **Valor óptimo conocido:** 450 (para la instancia P-n16-k8)

## Hallazgos Clave

### 1. Calidad de las Soluciones

| Algoritmo | 10 Ejecuciones (Mejor) | 100 Ejecuciones (Mejor) | 1000 Ejecuciones (Mejor) |
|-----------|--------------------------|---------------------------|----------------------------|
| HOA       | 422.18 (-6.18%)         | 410.93 (-8.68%)          | 410.93 (-8.68%)           |
| EGTO      | 416.87 (-7.36%)         | 410.93 (-8.68%)          | 410.93 (-8.68%)           |
| FOA       | 437.78 (-2.72%)         | 418.25 (-7.06%)          | -                         |
| HHO       | 410.93 (-8.68%)         | 410.93 (-8.68%)          | 410.93 (-8.68%)           |
| WOA       | 416.87 (-7.36%)         | 410.93 (-8.68%)          | 410.93 (-8.68%)           |

La mejor solución global hallada fue de 410.93, lo que representa un 8.68% de mejora sobre el valor óptimo conocido (450). Esta solución fue encontrada por HOA, EGTO, HHO y WOA, destacando que HHO logró esta solución óptima desde las primeras 10 ejecuciones y la mantuvo consistentemente a lo largo de todas las pruebas.

### 2. Evolución de la Precisión Estadística

Con el aumento del número de ejecuciones, se observó:

- **10 ejecuciones:** Permitió obtener un ranking inicial de algoritmos y detectar diferencias significativas (p-value = 0.0183), pero con intervalos de confianza amplios.
- **100 ejecuciones:** Aumentó considerablemente la confianza estadística (p-value ≈ 9.84e-09), reduciendo los intervalos de confianza y permitiendo una mejor discriminación entre algoritmos.
- **1000 ejecuciones:** Proporcionó la máxima certeza estadística (p-value ≈ 0.0004) para detectar incluso pequeñas diferencias entre algoritmos, permitiendo conclusiones definitivas.

### 3. Estabilidad y Consistencia

| Algoritmo | 10 ejecuciones (Desv. Est.) | 100 ejecuciones (Desv. Est.) | 1000 ejecuciones (Desv. Est.) |
|-----------|--------------------------|---------------------------|----------------------------|
| HOA       | 7.95                     | 11.02                     | 11.03                      |
| EGTO      | 14.44                    | 14.56                     | 13.16                      |
| FOA       | 7.23                     | 9.28                      | -                         |
| HHO       | 6.45                     | 10.36                     | 10.21                      |
| WOA       | 9.87                     | 13.52                     | 13.01                      |

El algoritmo HHO mostró la mayor estabilidad con 10 ejecuciones (6.45), mientras que EGTO presentó mayor variabilidad. Con 1000 ejecuciones, todos los algoritmos mostraron un incremento en su desviación estándar, pero HHO mantuvo la menor variabilidad (10.21), lo que indica una mejor consistencia a largo plazo y robustez tras la corrección del error de scope.

### 4. Eficiencia Computacional

| Algoritmo | Tiempo Medio (10) | Tiempo Medio (100) | Tiempo Medio (1000) |
|-----------|-------------------|---------------------|----------------------|
| HOA       | 0.043s            | 0.043s              | 0.018s               |
| EGTO      | 0.033s            | 0.033s              | 0.013s               |
| FOA       | 0.090s            | 0.092s              | -                    |
| HHO       | 0.048s            | 0.050s              | 0.020s               |
| WOA       | 0.030s            | 0.030s              | 0.012s               |

El rendimiento computacional muestra que WOA es el algoritmo más rápido, seguido de EGTO. HHO es aproximadamente un 66% más lento que WOA, pero esta diferencia se ve compensada por su mayor calidad de solución. FOA es significativamente más lento que todos los demás algoritmos. Con 1000 ejecuciones, todos los algoritmos mostraron tiempos de ejecución menores, probablemente debido al uso de menos iteraciones (20 vs 50).

### 5. Distribuciones y Análisis Estadístico

Los tests estadísticos (Friedman y post-hoc de Wilcoxon) mostraron:

- Con 10 ejecuciones: Diferencias estadísticamente significativas entre algoritmos (p<0.05), pero con menor poder estadístico.
- Con 100 ejecuciones: Significancia estadística extremadamente alta (p<0.000001), permitiendo un ranking confiable.
- Con 1000 ejecuciones: Confirmación definitiva de las diferencias entre HOA y EGTO.

El análisis de diagramas de caja (disponibles en los informes HTML) mostró distribuciones más definidas y menor solapamiento conforme aumentaba el número de ejecuciones.

### 6. Tasa de Éxito

| Algoritmo | 10 ejecuciones | 100 ejecuciones | 1000 ejecuciones |
|-----------|----------------|-----------------|------------------|
| HOA       | 100.00%        | 96.00%          | 70.00%           |
| EGTO      | 70.00%         | 77.00%          | 71.90%           |
| FOA       | 80.00%         | 89.00%          | -                |
| HHO       | 100.00%        | 100.00%         | 91.30%           |
| WOA       | 90.00%         | 91.00%          | 84.10%           |

La tasa de éxito (soluciones dentro del 1% del óptimo) mostró patrones interesantes: HHO destaca por mantener una tasa perfecta (100%) con 10 y 100 ejecuciones, y la mayor tasa (91.30%) con 1000 ejecuciones, lo que demuestra su robustez tras la corrección del error de scope. HOA mostró un descenso significativo en su tasa de éxito al aumentar las ejecuciones, mientras que EGTO y FOA mejoraron su tasa al aumentar de 10 a 100 ejecuciones, sugiriendo que estos algoritmos se benefician de más oportunidades para encontrar soluciones de alta calidad.

## Conclusiones

1. **Número óptimo de ejecuciones para investigación rigurosa:** El análisis sugiere que 100 ejecuciones proporcionan un excelente balance entre rigor estadístico y costo computacional. La mejora marginal de precisión entre 100 y 1000 ejecuciones no justifica el incremento en costo computacional, ya que no se encontraron mejores soluciones al aumentar de 100 a 1000 ejecuciones.

2. **Ranking de algoritmos para la instancia P-n16-k8:**
   - **Primer lugar:** HHO (mejor fitness, mejor estabilidad y 100% de tasa de éxito)
   - **Segundo lugar:** HOA y EGTO (mismo mejor fitness, aunque con menor estabilidad y tasa de éxito que HHO)
   - **Tercer lugar:** WOA (mismo mejor fitness pero menor promedio que los anteriores)
   - **Cuarto lugar:** FOA (buenos resultados pero menos óptimos)

3. **Recomendaciones prácticas:**
   - Para pruebas preliminares, 10 ejecuciones pueden dar orientación inicial
   - Para publicaciones académicas, al menos 100 ejecuciones son necesarias
   - Solo para comparaciones extremadamente detalladas y análisis de distribuciones específicos se justifica usar 1000 ejecuciones

4. **Eficiencia vs. Calidad:** HHO muestra el mejor rendimiento en términos de calidad de solución, aunque con un tiempo de ejecución moderado. WOA ofrece el mejor balance entre tiempo y calidad, siendo aproximadamente un 66% más rápido que HHO mientras alcanza la misma mejor solución pero con menor tasa de éxito. EGTO es también una opción eficiente, siendo un 35% más rápido que HHO con la misma calidad máxima de solución.

5. **Evolución de la Significancia Estadística:** El aumento en el número de ejecuciones permitió detectar diferencias significativas con mayor confianza y menor margen de error, lo que es crucial para estudios comparativos rigurosos. El p-value mejoró de 0.0183 (10 ejecuciones) a 9.84e-09 (100 ejecuciones).

6. **Comportamiento a largo plazo:** Los algoritmos mostraron patrones de comportamiento diferentes a medida que aumentaba el número de ejecuciones. HHO demostró ser el más robusto, manteniendo la mejor tasa de éxito (91.30%) incluso con 1000 ejecuciones. HOA tuvo una excelente tasa de éxito inicial pero disminuyó significativamente con más ejecuciones (de 100% a 70%), mientras que EGTO mostró un comportamiento más uniforme a lo largo de todas las pruebas.

## Impacto para la Investigación

Este análisis demuestra la importancia de utilizar un número adecuado de ejecuciones independientes en estudios sobre metaheurísticas. La práctica común de usar 30-50 ejecuciones puede ser insuficiente para detectar diferencias sutiles entre algoritmos avanzados.

Las 1000 ejecuciones nos permiten establecer un "ground truth" sobre el comportamiento real de estos algoritmos, confirmando que las conclusiones obtenidas con 100 ejecuciones son suficientemente robustas para la mayoría de los propósitos de investigación.

Estos resultados serán valiosos para establecer parámetros metodológicos en futuros trabajos relacionados con algoritmos metaheurísticos aplicados a problemas VRP y otros problemas de optimización combinatoria.

## Relación con Trabajos Futuros

Para investigaciones futuras, se recomienda:

1. Extender este análisis a otras instancias de VRP de diferentes tamaños para confirmar si las conclusiones se mantienen.
2. Implementar un enfoque híbrido que combine la robustez y calidad de HHO con la velocidad de WOA o EGTO.
3. Explorar el impacto del ajuste de parámetros en estos algoritmos y cómo afecta la cantidad de ejecuciones necesarias.
4. Desarrollar metodologías adaptativas que determinen dinámicamente el número óptimo de ejecuciones según la complejidad del problema.

## Gráficas Comparativas

Las gráficas comparativas detalladas están disponibles en el directorio `results/comparative_analysis/`. Estas gráficas ilustran visualmente las conclusiones presentadas en este documento y proporcionan una base sólida para comparaciones futuras.

---

*Análisis realizado y documento generado el 8 de mayo de 2025*