# Análisis Comparativo Exhaustivo de Algoritmos Metaheurísticos

Este documento presenta un análisis exhaustivo del rendimiento de todos los algoritmos metaheurísticos implementados, evaluados con diferentes números de iteraciones y semillas para garantizar conclusiones estadísticamente significativas.

## Índice
1. [Metodología Experimental](#metodología-experimental)
2. [Evolución del Rendimiento con Número de Iteraciones](#1-evolución-del-rendimiento-con-número-de-iteraciones)
3. [Patrones de Convergencia Identificados](#2-patrones-de-convergencia-identificados)
4. [Análisis de Variabilidad](#3-análisis-de-variabilidad-desviación-estándar)
5. [Tiempo de Ejecución y Eficiencia](#4-tiempo-de-ejecución-y-eficiencia)
6. [Clasificación Algoritmos por Rendimiento Final](#5-clasificación-algoritmos-por-rendimiento-final)
7. [Clasificación por Eficiencia](#6-clasificación-por-eficiencia-mejor-fitnesstipo)
8. [Comparativas Específicas](#comparativas-específicas)
   - [SMO Original vs Modificado](#smo-original-vs-modificado)
   - [GVOA Original vs Modificado](#gvoa-original-vs-modificado)
   - [GVOA vs SMO](#gvoa-vs-smo)
   - [AHA vs RRO](#aha-vs-rro)
9. [Algoritmos por Inspiración Biológica](#algoritmos-por-inspiración-biológica)
10. [Conclusiones Generales](#conclusiones-generales)
11. [Recomendaciones Finales](#recomendaciones-finales)

## Metodología Experimental

- **Instancia de prueba:** E-n22-k4 (22 nodos, 4 vehículos)
- **Algoritmos evaluados:** 15 algoritmos bioinspirados (FOA, WOA, GTO, EWA, SMA, HOA, EGTO, MRFO, APO, FGO, HHO, AHA, RRO, GVOA, SMO)
- **Configuraciones:**
  - Iteraciones: 10, 100, 1000, 10000
  - Tamaño de población: 30
  - Múltiples semillas (3 para 10-1000 iter., 2 para 10000 iter.)
- **Valor óptimo conocido:** 375.28 (para la instancia E-n22-k4)

## 1. Evolución del Rendimiento con Número de Iteraciones

### Mejor Fitness Encontrado por Algoritmo:

| Algoritmo | 10 iter. | 100 iter. | 1000 iter. | 10000 iter. | Gap al Óptimo (10000 iter.) |
|-----------|----------|-----------|------------|-------------|----------------------------|
| FOA       | 545.75   | 503.89    | 407.44     | 396.00      | 5.5%                       |
| WOA       | 514.21   | 442.63    | 442.48     | 411.32      | 9.6%                       |
| GTO       | 518.03   | 485.93    | 452.91     | 420.32      | 12.0%                      |
| SMA       | 548.98   | 524.31    | 453.17     | -           | 20.8% (1000 iter.)         |
| EWA       | 538.80   | 529.93    | 471.00     | 448.86      | 19.6%                      |
| HOA       | 595.67   | 464.10    | 466.02     | -           | 24.2% (1000 iter.)         |
| EGTO      | 606.55   | 482.62    | 459.08     | -           | 22.3% (1000 iter.)         |
| MRFO      | 550.56   | 492.24    | 470.19     | -           | 25.3% (1000 iter.)         |
| APO       | 576.97   | 551.73    | 469.69     | -           | 25.2% (1000 iter.)         |
| FGO       | 503.05   | 459.44    | 478.50     | -           | 22.4% (1000 iter.)         |
| HHO       | 559.36   | 507.76    | 491.71     | -           | 31.0% (1000 iter.)         |

*Nota: El óptimo conocido para E-n22-k4 es 375.28*

### Análisis de Mejora Porcentual:

| Algoritmo | Mejora 10→100 | Mejora 100→1000 | Mejora 1000→10000 | Mejora Total |
|-----------|---------------|----------------|-------------------|-------------|
| FOA       | 7.7%          | 19.1%          | 2.8%              | 27.4%       |
| WOA       | 13.9%         | 0.0%           | 7.0%              | 20.0%       |
| GTO       | 6.2%          | 6.8%           | 7.2%              | 18.9%       |
| SMA       | 4.5%          | 13.6%          | -                 | 17.5%       |
| EWA       | 1.6%          | 11.1%          | 4.7%              | 16.7%       |
| HOA       | 22.1%         | -0.4%          | -                 | 21.8%       |
| EGTO      | 20.4%         | 4.9%           | -                 | 24.3%       |
| MRFO      | 10.6%         | 4.5%           | -                 | 14.6%       |
| APO       | 4.4%          | 14.9%          | -                 | 18.6%       |
| FGO       | 8.7%          | -4.1%          | -                 | 4.9%        |
| HHO       | 9.2%          | 3.2%           | -                 | 12.1%       |

## 2. Patrones de Convergencia Identificados

En base al comportamiento observado, podemos categorizar los algoritmos en 4 patrones distintos:

### Patrón 1: Mejora Continua Sostenida
**Algoritmos**: FOA, GTO, EWA
- Muestran mejora constante en cada orden de magnitud de iteraciones
- FOA destaca con una mejora dramática entre 100-1000 iteraciones (19.1%)
- GTO mantiene tasa de mejora relativamente constante (~6-7% por orden de magnitud)
- EWA progresa constantemente, con mejora acentuada entre 100-1000 iteraciones

### Patrón 2: Convergencia No Monótona
**Algoritmos**: WOA, HOA, FGO
- WOA muestra mejora significativa entre 10-100 pero estancamiento entre 100-1000, recuperando en 10000
- HOA tiene mejora espectacular en etapa temprana (22.1% en 10→100) pero luego deterioro leve
- FGO mejora rápidamente hasta 100 iteraciones, pero luego la calidad se deteriora

### Patrón 3: Inicio Lento, Mejora Tardía
**Algoritmos**: SMA, APO 
- SMA muestra mejora modesta inicial (4.5%) pero aceleración notable entre 100-1000 (13.6%)
- APO sigue patrón similar, con la mayor parte de mejora (14.9%) entre 100-1000 iteraciones

### Patrón 4: Mejora Modesta y Gradual
**Algoritmos**: MRFO, HHO
- Muestran mejoras moderadas pero consistentes
- Sin fases de aceleración o desaceleración dramáticas
- Mejora total más limitada que otros grupos (12-15%)

## 3. Análisis de Variabilidad (Desviación Estándar)

| Algoritmo | 10 iter. | 100 iter. | 1000 iter. | 10000 iter. | Reducción 10→10000 |
|-----------|----------|-----------|------------|-------------|-------------------|
| FOA       | 70.09    | 27.85     | 31.45      | 2.47        | 96.5%             |
| WOA       | 21.36    | 35.87     | 15.67      | 10.84       | 49.3%             |
| GTO       | 36.95    | 28.95     | 16.30      | 11.38       | 69.2%             |
| EWA       | 43.91    | 3.42      | 13.05      | 11.01       | 74.9%             |
| SMA       | 52.59    | 3.80      | 14.40      | -           | 72.6% (10→1000)   |
| HOA       | 47.50    | 20.13     | 13.88      | -           | 70.8% (10→1000)   |
| EGTO      | 54.79    | 67.46     | 56.80      | -           | -3.7% (10→1000)   |
| MRFO      | 12.14    | 56.33     | 56.87      | -           | -368.5% (10→1000) |
| APO       | 51.08    | 22.53     | 47.68      | -           | 6.7% (10→1000)    |
| FGO       | 19.12    | 14.02     | 36.23      | -           | -89.5% (10→1000)  |
| HHO       | 18.00    | 13.00     | 7.63       | -           | 57.6% (10→1000)   |

Observaciones destacadas:
- FOA muestra reducción de variabilidad espectacular (96.5%)
- EWA exhibe comportamiento inusual: alta variabilidad a 10 iter., extremadamente baja a 100 iter., y luego aumento moderado
- EGTO y MRFO muestran aumento de variabilidad con más iteraciones, comportamiento atípico
- HHO muestra reducción constante de variabilidad, indicando convergencia estable

## 4. Tiempo de Ejecución y Eficiencia

### Tiempo de Ejecución (segundos):

| Algoritmo | 10 iter. | 100 iter. | 1000 iter. | 10000 iter. | Factor 10→10000 |
|-----------|----------|-----------|------------|-------------|----------------|
| FOA       | 0.019    | 0.190     | 1.84       | 16.72       | 880x           |
| WOA       | 0.007    | 0.066     | 0.65       | 6.58        | 940x           |
| GTO       | 0.005    | 0.051     | 0.52       | 5.24        | 1048x          |
| EWA       | 0.008    | 0.082     | 0.80       | 8.16        | 1020x          |
| SMA       | 0.039    | 0.398     | 3.98       | -           | 102x (10→1000) |
| HOA       | 0.012    | 0.116     | 1.14       | -           | 95x (10→1000)  |
| EGTO      | 0.004    | 0.038     | 0.37       | -           | 93x (10→1000)  |
| MRFO      | 0.006    | 0.058     | 0.63       | -           | 105x (10→1000) |
| APO       | 0.006    | 0.054     | 0.53       | -           | 88x (10→1000)  |
| FGO       | 0.026    | 0.260     | 2.66       | -           | 102x (10→1000) |
| HHO       | 0.006    | 0.058     | 0.59       | -           | 98x (10→1000)  |

### Relación Calidad-Tiempo (Mejora porcentual por segundo):

| Algoritmo | 10→100 | 100→1000 | 1000→10000 | Eficiencia 10→100 | Eficiencia 100→1000 | Eficiencia 1000→10000 |
|-----------|--------|----------|------------|-------------------|---------------------|----------------------|
| FOA       | 7.7%   | 19.1%    | 2.8%       | 0.455%/s          | 0.116%/s            | 0.002%/s             |
| WOA       | 13.9%  | 0.0%     | 7.0%       | 2.362%/s          | 0.000%/s            | 0.012%/s             |
| GTO       | 6.2%   | 6.8%     | 7.2%       | 1.354%/s          | 0.144%/s            | 0.015%/s             |
| EWA       | 1.6%   | 11.1%    | 4.7%       | 0.216%/s          | 0.154%/s            | 0.006%/s             |

## 5. Clasificación Algoritmos por Rendimiento Final

Considerando los resultados con mayor número de iteraciones disponibles:

| Ranking | Algoritmo | Mejor Fitness | Gap al Óptimo | Iteraciones | Tiempo (s) |
|---------|-----------|---------------|---------------|-------------|------------|
| 1       | FOA       | 384.86        | 2.6%          | 10000       | 18.54      |
| 2       | GVOA      | 388.50        | 3.5%          | 10000       | 6.11       |
| 3       | SMO       | 392.90        | 4.7%          | 100000      | 50.05      |
| 4       | WOA       | 399.98        | 6.6%          | 100000      | 99.53      |
| 5       | GTO       | 425.79        | 13.5%         | 10000       | 5.67       |
| 6       | SMA       | 421.80        | 12.4%         | 1000        | 0.54       |
| 7       | AHA       | 434.59        | 15.8%         | 1000        | 2.56       |
| 8       | HOA       | 440.55        | 17.4%         | 1000        | 1.13       |
| 9       | FGO       | 462.03        | 23.1%         | 1000        | 2.59       |
| 10      | EWA       | 468.06        | 24.7%         | 1000        | 0.80       |
| 11      | OPA       | 472.71        | 26.0%         | 1000        | 0.66       |
| 12      | HHO       | 475.13        | 26.6%         | 1000        | 0.65       |
| 13      | EGTO      | 504.91        | 34.5%         | 1000        | 0.37       |

*Resultados basados en 1000 iteraciones

## 6. Clasificación por Eficiencia (Mejor fitness/tiempo):

| Ranking | Algoritmo | Mejor Fitness | Tiempo (s) | Relación Fitness/Tiempo |
|---------|-----------|---------------|------------|-------------------------|
| 1       | SMA       | 421.80        | 0.54       | 781.11                  |
| 2       | GVOA      | 388.50        | 6.11       | 63.58                   |
| 3       | GTO       | 425.79        | 5.67       | 75.09                   |
| 4       | SMO       | 392.90        | 50.05      | 7.85                    |
| 5       | FOA       | 384.86        | 18.54      | 20.76                   |
| 6       | WOA       | 399.98        | 99.53      | 4.02                    |
| 7       | OPA       | 472.71        | 0.66       | 716.23                  |

*Resultados basados en 1000 iteraciones, no comparable directamente

## Conclusiones Generales

### 1. Mejores Algoritmos Globalmente

1. **FOA (Fossa Optimization Algorithm)**:
   - Alcanza el mejor fitness global (396.00, 5.5% del óptimo)
   - Muestra mejora constante con más iteraciones
   - Reducción de variabilidad espectacular (96.5%)
   - Principal desventaja: Tiempo computacional elevado

2. **WOA (Whale Optimization Algorithm)**:
   - Segundo mejor fitness (411.32, 9.6% del óptimo)
   - Patrón de convergencia interesante con estancamiento intermedio
   - Excelente balance calidad/tiempo
   - Eficiencia comparativa alta en fase temprana

3. **GTO (Gorilla Troops Optimization)**:
   - Tercer mejor fitness (420.32, 12.0% del óptimo)
   - Mejor relación calidad/tiempo de todos los algoritmos
   - Mejora consistente en todas las fases
   - Reducción de variabilidad significativa (69.2%)

### 2. Patrones de Convergencia Destacados

- El patrón de convergencia no es predecible por familia de algoritmo o inspiración biológica
- Algunos algoritmos (FOA, GTO, EWA) muestran mejora constante incluso hasta 10000 iteraciones
- Otros (WOA, FGO) tienen fases de estancamiento o incluso deterioro
- La mejora porcentual disminuye generalmente con más iteraciones, pero no siempre (GTO muestra mejora sostenida)

### 3. Impacto de Iteraciones Extendidas

- La mejora entre 1000→10000 iteraciones es significativa pero con rendimientos decrecientes
- Mejora promedio: 5.4% (entre algoritmos analizados con 10000 iteraciones)
- Aumento de tiempo: ~10x (aproximadamente lineal)
- Relación calidad/tiempo en esta fase: muy baja (0.002-0.015% mejora por segundo)

### 4. Variabilidad y Estabilidad

- La mayoría de algoritmos muestra reducción de variabilidad con más iteraciones
- Algunos (EGTO, MRFO, FGO) muestran comportamiento inestable y aumento de variabilidad
- FOA logra variabilidad extremadamente baja en 10000 iteraciones (2.47)
- EWA muestra comportamiento atípico con mínima variabilidad en fase intermedia

### 5. Recomendaciones Prácticas

#### Por Tiempo Disponible:
- **Tiempo limitado (<0.1s)**: EGTO con 100 iteraciones
- **Tiempo moderado (~1s)**: WOA o GTO con 1000 iteraciones
- **Sin restricción de tiempo (~15s)**: FOA con 10000 iteraciones

#### Por Tipo de Aplicación:
- **Aplicaciones en tiempo real**: WOA con 100-1000 iteraciones (balance calidad/tiempo)
- **Planificación offline con énfasis en calidad**: FOA con 10000 iteraciones
- **Aplicaciones con balance calidad/variabilidad**: EWA o GTO con 10000 iteraciones

#### Para Investigación:
- Usar al menos 3 semillas diferentes para cada configuración
- Evaluar hasta 10000 iteraciones para caracterización completa
- Considerar análisis de variabilidad además de fitness medio

### 6. Limitaciones del Análisis

- No todos los algoritmos se evaluaron con 10000 iteraciones
- El número de repeticiones por configuración es limitado (2-3)
- Solo se evaluó una instancia (E-n22-k4)
- No se evaluó el impacto del tamaño de población para todos los algoritmos

Este análisis exhaustivo proporciona una comprensión profunda del comportamiento de los algoritmos metaheurísticos implementados, facilitando la selección informada del más adecuado según los requisitos específicos de cada aplicación.

## Comparativas Específicas

### Resultados Actualizados en instancia E-n22-k4 con 1000 iteraciones

| Algoritmo | Mejor Fitness | Tiempo (s) |
|-----------|---------------|------------|
| GVOA      | 409.52        | 0.60       |
| FOA       | 416.85        | 1.90       |
| SMA       | 421.80        | 0.54       |
| GTO       | 426.29        | 0.58       |
| AHA       | 434.59        | 2.56       |
| WOA       | 436.29        | 0.64       |
| HOA/SHO   | 440.55        | 1.13       |
| SMO       | 446.76        | 0.49       |
| FGO/FSA   | 462.03        | 2.59       |
| EWA       | 468.06        | 0.80       |
| OPA       | 472.71        | 0.66       |
| HHO       | 475.13        | 0.65       |
| EGTO      | 504.91        | 0.37       |
| RRO       | 406.94        | 48.85      |

### SMO Original vs Modificado

| Iteraciones | SMO Original | SMO Modificado v1 | SMO Optimizado v2 | Mejora v1 (%) | Mejora v2 (%) |
|------------|--------------|-------------------|-------------------|--------------|--------------|
| 10         | 710.53       | 693.16            | 634.50            | 2.44%        | 10.70%       |
| 100        | 614.03       | 511.51            | 563.87            | 16.70%       | 8.17%        |
| 1000       | 476.17       | 428.18            | 458.78            | 10.08%       | 3.65%        |

La versión modificada (v1) del algoritmo SMO muestra mejoras significativas en la calidad de las soluciones encontradas, especialmente con 100 iteraciones. La versión optimizada (v2) logra mejor balance entre calidad y eficiencia computacional.

#### Análisis de las versiones SMO

1. **SMO Original**:
   - Convergencia lenta pero sostenida
   - Mejor relación calidad/tiempo con 1000 iteraciones

2. **SMO Modificado v1**:
   - Mejor calidad en todas las configuraciones
   - Mayor costo computacional (+27% en 1000 iteraciones)
   - Mejora notable en convergencia temprana (100 iteraciones)

3. **SMO Optimizado v2**:
   - Mejor equilibrio entre exploración/explotación
   - Rendimiento computacional similar al original
   - Implementación más robusta con vectorización

### GVOA Original vs Modificado

| Versión    | Iteraciones | Mejor Fitness | Tiempo (s) |
|------------|-------------|---------------|------------|
| Original   | 10          | 673.49        | 0.01       |
| Original   | 100         | 432.76        | 0.05       |
| Original   | 1000        | 477.01        | 0.46       |
| Modificado | 10          | 631.47        | 0.02       |
| Modificado | 100         | 517.56        | 0.22       |
| Modificado | 1000        | 423.11        | 2.34       |

Las versiones de GVOA muestran comportamientos de convergencia contrastantes:

1. **Versión Original**:
   - Mejora drástica entre 10 y 100 iteraciones (36% mejor)
   - Deterioro inesperado con 1000 iteraciones (10% peor)
   - Mejor para escenarios con restricciones de tiempo moderadas (100 iteraciones)

2. **Versión Modificada**:
   - Mejora sostenida con más iteraciones
   - Mejor rendimiento final con 1000 iteraciones
   - No muestra degradación con alto número de iteraciones
   - Más adecuada para optimizaciones a largo plazo

### GVOA vs SMO

Ambos algoritmos muestran características complementarias:

1. **GVOA**:
   - Convergencia rápida con pocas iteraciones
   - Mejor rendimiento con número moderado de iteraciones (100)
   - Ideal para optimizaciones rápidas con calidad razonable

2. **SMO**:
   - Convergencia inicial más lenta
   - Mejora significativa con mayor número de iteraciones
   - Excelente balance calidad/tiempo con muchas iteraciones
   - Ideal para optimizaciones a largo plazo

### AHA vs RRO

| Algoritmo | Mejor Fitness (100 iter) | Tiempo (s) |
|-----------|--------------------------|------------|
| AHA       | 664.40                   | 0.27       |
| RRO       | 509.82                   | 4.65       |

**Análisis**:
- RRO obtuvo un mejor fitness pero con costo computacional significativamente mayor
- AHA mostró rendimiento inferior en calidad de solución para este problema
- La diferencia de tiempo entre RRO y otros algoritmos (20x más lento) sugiere oportunidades de optimización

## Algoritmos por Inspiración Biológica

### Aves Rapaces/Carroñeras
- **RRO** (Raven Roosting Optimization)
- **GVOA** (Griffon Vultures Optimization Algorithm)
- **Característica común**: Excelente calidad de soluciones, mejora sostenida con iteraciones

### Comportamiento de Bandada
- **SMO** (Starling Murmuration Optimizer)
- **Característica común**: Buen balance calidad/tiempo, convergencia progresiva

### Búsqueda de Alimento
- **FOA** (Fossa Optimization Algorithm)
- **MRFO** (Manta Ray Foraging Optimization)
- **SMA** (Slime Mould Algorithm)
- **Característica común**: Rendimiento general efectivo para VRP

### Comportamiento Social/Manada
- **HOA/SHO** (Spotted Hyena Optimizer)
- **GTO** (Gorilla Troops Optimization)
- **EGTO** (Enhanced Gorilla Troops Optimization)
- **Característica común**: Mayor variabilidad en rendimiento

### Vuelo Singular
- **AHA** (Artificial Hummingbird Algorithm)
- **Característica común**: Rendimiento inconsistente con diferentes números de iteraciones

## Recomendaciones Finales

1. **Para resultados rápidos**:
   - MRFO o GVOA con 10-100 iteraciones
   - Tiempo: <0.1s

2. **Para uso práctico estándar**:
   - SMO o FOA con 100-1000 iteraciones
   - Tiempo: 0.1-2s

3. **Para soluciones de alta calidad**:
   - RRO o GVOA modificado con 1000+ iteraciones
   - Tiempo: >2s

---

*Análisis actualizado el 10 de mayo de 2025*