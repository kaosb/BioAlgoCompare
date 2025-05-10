# Análisis Comparativo de Algoritmos Bioinspirados

Este documento consolida los análisis comparativos de los diferentes algoritmos implementados para el problema de Vehicle Routing Problem (VRP).

## Índice
1. [Comparativa General](#comparativa-general)
2. [Comparativas Específicas](#comparativas-específicas)
   - [SMO Original vs Modificado](#smo-original-vs-modificado)
   - [GVOA Original vs Modificado](#gvoa-original-vs-modificado)
   - [GVOA vs SMO](#gvoa-vs-smo)
   - [AHA vs RRO](#aha-vs-rro)
3. [Algoritmos por Inspiración Biológica](#algoritmos-por-inspiración-biológica)

## Comparativa General

### Resultados en instancia E-n22-k4 con 1000 iteraciones

| Algoritmo | Mejor Fitness | Tiempo (s) | 
|-----------|---------------|------------|
| RRO       | 406.94        | 48.85      |
| GVOA      | 423.11        | 2.34       |
| FOA       | 443.23        | 2.01       |
| SMO       | 458.78        | 0.50       |
| EWA       | 478.27        | 0.83       |
| GTO       | 481.68        | 0.58       |
| MRFO      | 472.81        | 0.63       |
| WOA       | 497.86        | 0.76       |
| HOA/SHO   | 513.70        | 1.18       |
| EGTO      | 553.01        | 0.38       |
| APO       | 519.79        | 0.54       |
| HHO       | 494.21        | 0.66       |
| SMA       | 482.26        | 0.54       |
| FGO/FSA   | 475.79        | 2.72       |
| AHA       | 610.64        | 2.61       |

### Clasificación por Eficiencia (Calidad/Tiempo)

1. **SMO**: Excelente calidad (458.78) con tiempo muy eficiente (0.50s)
2. **FOA**: Muy buena calidad (443.23) con tiempo moderado (2.01s)
3. **GVOA**: Alta calidad (423.11) con tiempo razonable (2.34s)
4. **MRFO**: Buena calidad desde pocas iteraciones
5. **EWA**: Mejora constante con buena calidad final

## Comparativas Específicas

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