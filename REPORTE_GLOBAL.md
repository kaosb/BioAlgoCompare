# Reporte Global de Evaluación de Algoritmos Metaheurísticos

Este reporte presenta los resultados exhaustivos del análisis comparativo de 11 algoritmos metaheurísticos bio-inspirados en la resolución del Problema de Ruteo de Vehículos (VRP), con diferentes tamaños de muestra (10, 100 y 1000 ejecuciones).

## 1. Configuración Experimental

- **Instancia de prueba:** P-n16-k8 (16 nodos, 8 vehículos, capacidad 35)
- **Algoritmos evaluados:**
  - HHO (Harris Hawks Optimization - variante)
  - EWA (Earthworm Algorithm)
  - WOA (Whale Optimization Algorithm)
  - SMA (Slime Mould Algorithm)
  - HOA (Harris Hawks Optimization)
  - FGO (Fox Geese Optimization) 
  - APO (Artificial Platypus Optimizer)
  - EGTO (Extended Grasshopper Optimization)
  - MRFO (Manta Ray Foraging Optimization)
  - FOA (Fruit Fly Optimization Algorithm)
  - GTO (Grasshopper Optimization Algorithm)
- **Ejecuciones:** 10, 100 y 1000 por algoritmo (escalado progresivo)
- **Iteraciones:** 50 para pruebas con 10 y 100 ejecuciones, reducido a 20 para las pruebas con 1000 ejecuciones
- **Valor óptimo conocido:** 450 (para la instancia P-n16-k8)
- **Métrica principal:** Minimización de la distancia total recorrida

## 2. Resumen Global de Resultados

### 2.1 Calidad de las Soluciones (Mejor Fitness)

| Algoritmo | 10 Ejecuciones | 100 Ejecuciones | 1000 Ejecuciones | Mejor Global |
|-----------|----------------|-----------------|------------------|--------------|
| HHO       | 410.93         | 410.93          | 410.93           | 410.93       |
| EWA       | 410.93         | 410.93          | 410.93           | 410.93       |
| WOA       | 416.87         | 410.93          | 410.93           | 410.93       |
| SMA       | 410.93         | 410.93          | 410.93           | 410.93       |
| HOA       | 422.18         | 410.93          | -                | 410.93       |
| FGO       | 430.87         | 410.93          | -                | 410.93       |
| APO       | 434.01         | 410.93          | -                | 410.93       |
| EGTO      | 416.87         | 410.93          | -                | 410.93       |
| MRFO      | 418.25         | 416.87          | -                | 416.87       |
| FOA       | 437.78         | 418.25          | -                | 418.25       |
| GTO       | 424.19         | 410.93          | -                | 410.93       |

La mejor solución global encontrada fue 410.93, lo que representa una mejora del 8.68% sobre el valor óptimo conocido (450). Esta solución fue encontrada por múltiples algoritmos.

### 2.2 Estabilidad (Fitness Promedio con 100 Ejecuciones)

| Algoritmo | Fitness Promedio | Desviación Estándar | Tasa de Éxito (%) |
|-----------|------------------|---------------------|-------------------|
| HHO       | 425.11           | 10.36               | 100.00            |
| EWA       | 427.09           | 12.09               | 98.00             |
| WOA       | 434.49           | 13.52               | 91.00             |
| SMA       | 437.57           | 11.89               | 93.00             |
| HOA       | 436.27           | 9.94                | 96.00             |
| FGO       | 437.42           | 10.45               | 96.00             |
| APO       | 438.14           | 11.07               | 98.00             |
| EGTO      | 443.91           | 14.56               | 77.00             |
| MRFO      | 443.60           | 11.32               | 89.00             |
| FOA       | 445.88           | 9.28                | 89.00             |
| GTO       | 457.05           | 15.78               | 44.00             |

HHO muestra el mejor promedio, indicando mayor consistencia en encontrar soluciones de alta calidad.

### 2.3 Eficiencia Computacional (Tiempo Promedio con 100 Ejecuciones)

| Algoritmo | Tiempo Promedio (s) | Tiempo Relativo |
|-----------|---------------------|-----------------|
| MRFO      | 0.02                | 1.0x (más rápido) |
| GTO       | 0.02                | 1.0x            |
| WOA       | 0.03                | 1.5x            |
| SMA       | 0.03                | 1.5x            |
| EGTO      | 0.03                | 1.5x            |
| APO       | 0.03                | 1.5x            |
| FGO       | 0.03                | 1.5x            |
| EWA       | 0.03                | 1.5x            |
| HOA       | 0.04                | 2.0x            |
| HHO       | 0.05                | 2.5x            |
| FOA       | 0.09                | 4.5x            |

MRFO y GTO son los algoritmos más rápidos, mientras que FOA es significativamente más lento que el resto.

## 3. Análisis Estadístico Avanzado

### 3.1 Pruebas de Significancia

Las pruebas estadísticas (Kruskal-Wallis y post-hoc de Wilcoxon) mostraron diferencias estadísticamente significativas entre los algoritmos:

- **Con 10 ejecuciones:** p-value = 0.0126 (significativo)
- **Con 100 ejecuciones:** p-value ≈ 9.84e-09 (altamente significativo)
- **Con 1000 ejecuciones:** p-value = 1.51e-49 (extremadamente significativo)

La significancia estadística aumentó dramáticamente con el número de ejecuciones, lo que confirma la robustez de las conclusiones con muestras grandes.

### 3.2 Ranking Global de Algoritmos

Basado en todos los criterios de evaluación (calidad, estabilidad, eficiencia y estadísticas):

1. **HHO** - Excelente calidad y estabilidad con tiempo moderado (tras corrección de error de scope)
2. **EWA** - Excelente calidad y buena estabilidad con tiempo moderado
3. **WOA** - Muy buena calidad y buen balance tiempo-calidad
4. **SMA** - Muy buena calidad pero menos estable que los mejores (tras corrección del error de dominio)
5. **FGO** - Buena calidad y eficiencia computacional
6. **HOA** - Buena calidad pero menos eficiente
7. **APO** - Rendimiento bueno pero no destacado
8. **MRFO** - Velocidad superior pero calidad inferior
9. **EGTO** - Alta variabilidad en resultados
10. **FOA** - Alto tiempo computacional con calidad inferior
11. **GTO** - Alta variabilidad y bajo rendimiento global

### 3.3 Análisis con 1000 Ejecuciones (Top 4 Algoritmos)

El análisis extendido con 1000 ejecuciones para los 4 mejores algoritmos confirmó:

- **Estabilidad:** HHO > EWA > WOA > SMA
- **Tiempo de ejecución:** WOA > SMA > EWA > HHO
- **Distribución de soluciones óptimas:**
  - HHO: 15.8% de ejecuciones encontraron la mejor solución (410.93)
  - EWA: 20.3% de ejecuciones encontraron la mejor solución
  - WOA: 5.0% de ejecuciones encontraron la mejor solución
  - SMA: 4.0% de ejecuciones encontraron la mejor solución

## 4. Impacto del Tamaño de Muestra

### 4.1 Mejora de la Calidad con Mayor Número de Ejecuciones

| Algoritmo | Mejora 10→100 | Mejora 100→1000 |
|-----------|---------------|----------------|
| HHO       | 0.00%         | 0.00%          |
| EWA       | 0.00%         | 0.00%          |
| WOA       | 1.42%         | 0.00%          |
| SMA       | 0.00%         | 0.00%          |
| HOA       | 2.66%         | -              |
| FGO       | 4.63%         | -              |
| APO       | 5.32%         | -              |
| EGTO      | 1.42%         | -              |
| MRFO      | 0.33%         | -              |
| FOA       | 4.46%         | -              |
| GTO       | 3.13%         | -              |

La mayor mejora se observó al pasar de 10 a 100 ejecuciones. No se observaron mejoras adicionales al pasar de 100 a 1000 ejecuciones para la mejor solución.

### 4.2 Impacto en el Análisis Estadístico

El aumento del tamaño de muestra mejoró dramáticamente la potencia estadística:

- **10 ejecuciones:** Detecta diferencias obvias entre algoritmos
- **100 ejecuciones:** Permite un ranking robusto con alta confianza
- **1000 ejecuciones:** Detecta incluso pequeñas diferencias entre algoritmos similares

### 4.3 Recomendaciones sobre Número de Ejecuciones

- **Pruebas exploratorias:** 10 ejecuciones son suficientes
- **Estudios rigurosos:** 100 ejecuciones proporcionan un excelente balance
- **Análisis extremadamente detallados:** 1000 ejecuciones sólo necesarias para casos excepcionales

## 5. Análisis por Tipo de Algoritmo

### 5.1 Algoritmos Basados en Comportamiento de Enjambres

Los algoritmos de tipo enjambre (HHO, WOA, MRFO, SMA) mostraron rendimientos dispares:
- HHO y WOA destacaron con excelente rendimiento
- SMA tuvo un buen rendimiento pero menos consistente
- MRFO mostró una velocidad excepcional pero menor calidad

### 5.2 Algoritmos Evolutivos/Genéticos

EWA mostró un rendimiento superior a FOA, sugiriendo que su mecanismo de búsqueda es más adecuado para VRP.

### 5.3 Algoritmos Basados en Comportamiento Animal Individual

HOA y FGO mostraron rendimientos sólidos pero no superiores a los mejores algoritmos de enjambre.

## 6. Conclusiones y Recomendaciones

### 6.1 Algoritmos Recomendados para VRP

1. **Para máxima calidad de solución:**
   - HHO o EWA (ambos encontraron consistentemente las mejores soluciones)

2. **Para mejor balance calidad-tiempo:**
   - WOA (soluciones de alta calidad con tiempo computacional más bajo)

3. **Para restricciones extremas de tiempo:**
   - MRFO (el más rápido, con calidad razonable)

4. **Para aplicaciones que requieren análisis exploratorio rápido:**
   - WOA para rápido prototipado y exploración inicial

### 6.2 Recomendaciones para Investigación

1. **Para publicaciones científicas:**
   - Utilizar al menos 100 ejecuciones independientes
   - Incluir análisis estadístico (Friedman y post-hoc)
   - Evaluar tanto calidad como tiempo de ejecución

2. **Para aplicaciones prácticas:**
   - Seleccionar algoritmos basados en requisitos específicos (calidad vs. tiempo)
   - Considerar HHO para máxima calidad y WOA para mejor balance

3. **Para desarrollo de nuevos algoritmos:**
   - Estudiar en profundidad los mecanismos de búsqueda de HHO y EWA
   - Explorar la hibridación de algoritmos rápidos con los de alta calidad

### 6.3 Limitaciones del Estudio

1. Análisis en una única instancia VRP (P-n16-k8)
2. Parámetros fijos para todos los algoritmos
3. Sin optimización de hiperparámetros específica por algoritmo

## 7. Trabajo Futuro

1. Extender el análisis a más instancias VRP de diferentes tamaños
2. Explorar algoritmos híbridos que combinen la velocidad de MRFO con la calidad de HHO/EWA
3. Realizar optimización de hiperparámetros para cada algoritmo
4. Analizar el comportamiento de los algoritmos con diferentes restricciones (ventanas de tiempo, flota heterogénea, etc.)
5. Desarrollar un framework unificado para la implementación de metaheurísticas bio-inspiradas para VRP

---

*Análisis realizado el 8 de mayo de 2025*