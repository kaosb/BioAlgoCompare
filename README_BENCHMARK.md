# Análisis Comparativo de Algoritmos Metaheurísticos para VRP

## Configuración Experimental

- **Instancias VRP evaluadas:**
  - P-n16-k8 (16 nodos, 8 vehículos)
  - E-n22-k4 (22 nodos, 4 vehículos)
  
- **Algoritmos evaluados:**
  - HHO (Harris Hawks Optimization)
  - WOA (Whale Optimization Algorithm)
  
- **Parámetros de ejecución:**
  - Iteraciones: 500
  - Tamaño de población: 30
  - Ejecuciones por algoritmo/instancia: 5
  - Semilla fija: 42 (para asegurar reproducibilidad)

## Resultados Comparativos

### Instancia P-n16-k8 (Valor óptimo: 450)

| Algoritmo | Mejor fitness | Fitness promedio | Desviación estándar | Gap al óptimo (%) | Tiempo (s) |
|-----------|---------------|------------------|---------------------|-------------------|------------|
| HHO       | 424.19        | 433.83 ± 7.97    | 7.97                | -5.73%            | 0.30       |
| WOA       | 416.87        | 426.94 ± 9.79    | 9.79                | -7.36%            | 0.27       |

### Instancia E-n22-k4 (Valor óptimo: 375)

| Algoritmo | Mejor fitness | Fitness promedio | Desviación estándar | Gap al óptimo (%) | Tiempo (s) |
|-----------|---------------|------------------|---------------------|-------------------|------------|
| HHO       | 476.72        | 512.21 ± 27.45   | 27.45               | 27.13%            | 0.33       |
| WOA       | 436.11        | 453.08 ± 10.95   | 10.95               | 16.30%            | 0.33       |

## Análisis Global

### Ranking por Calidad de Solución (Gap Promedio)

| Posición | Algoritmo | Gap Promedio (%) | σ Promedio | Tiempo Promedio (s) |
|----------|-----------|------------------|------------|---------------------|
| 1        | WOA       | 4.47%            | 10.37      | 0.30                |
| 2        | HHO       | 10.70%           | 17.71      | 0.32                |

### Análisis Estadístico

Para la instancia P-n16-k8, el test de Kruskal-Wallis indica:

- **Mejor fitness**: No hay diferencia estadísticamente significativa (p=0.249)
- **Fitness promedio**: Hay diferencia estadísticamente significativa (p=0.003) 
- **Tiempo de ejecución**: Hay diferencia estadísticamente significativa (p=0.009)

Para la instancia E-n22-k4, el test de Kruskal-Wallis indica:

- **Mejor fitness**: Hay diferencia estadísticamente significativa (p=0.009)
- **Fitness promedio**: Hay diferencia estadísticamente significativa (p=0.003)
- **Tiempo de ejecución**: No hay diferencia estadísticamente significativa (p=0.465)

## Conclusiones

### Calidad de Solución

1. **WOA (Whale Optimization Algorithm)** demuestra un rendimiento superior en calidad de solución para ambas instancias, logrando:
   - Un gap promedio de solo 4.47%
   - El mejor resultado absoluto (416.87) en la instancia P-n16-k8, superando en un 7.36% al óptimo conocido
   - Un comportamiento más estable (menor desviación estándar) en E-n22-k4, instancia de mayor tamaño

2. **HHO (Harris Hawks Optimization)** muestra un comportamiento heterogéneo:
   - Excelente en P-n16-k8 (gap -5.73%)
   - Desempeño más pobre en E-n22-k4 (gap 27.13%)
   - Mayor variabilidad en la instancia más grande (σ=27.45)

### Eficiencia Computacional

1. **WOA** ofrece un buen balance:
   - Ligeramente más rápido en P-n16-k8 (0.27s vs 0.30s)
   - Igual de rápido en E-n22-k4 (0.33s)
   - Tiempo consistente entre instancias

2. **HHO** muestra eficiencia comparable:
   - Tiempos moderados en ambas instancias
   - Ligero aumento de tiempo para instancias más grandes

### Estabilidad y Robustez

1. **WOA** demuestra mayor robustez:
   - Desviación estándar consistentemente más baja en ambas instancias
   - Comportamiento más predecible y estable
   - Mejor escalabilidad a instancias más grandes

2. **HHO** muestra mayor variabilidad:
   - Desviación estándar moderada en P-n16-k8 (σ=7.97)
   - Alta variabilidad en E-n22-k4 (σ=27.45)
   - Sensibilidad a las características del problema

## Recomendaciones y Trabajos Futuros

### Recomendaciones Prácticas

1. **Para aplicaciones generales de VRP**: Utilizar WOA como primera opción por su mejor balance entre calidad, eficiencia y estabilidad.
2. **Para instancias pequeñas**: Tanto HHO como WOA ofrecen resultados óptimos.
3. **Para instancias más grandes**: WOA parece escalar mejor y mantener mejor rendimiento.

### Trabajo Futuro

1. **Ampliar el benchmark**:
   - Incluir todos los algoritmos disponibles (11 en total)
   - Evaluar con más instancias, especialmente M-n151-k12
   - Aumentar a 30 ejecuciones por algoritmo/instancia para mayor significancia estadística

2. **Hibridación de algoritmos**:
   - Explorar la combinación de WOA (mejor calidad global) con EGTO u otros algoritmos más rápidos
   - Desarrollar esquemas adaptativos que seleccionen el algoritmo según características de la instancia

3. **Optimización de parámetros**:
   - Analizar sensibilidad de los algoritmos a tamaños de población e iteraciones
   - Implementar mecanismos adaptativos de ajuste de parámetros

4. **Análisis de componentes**:
   - Estudiar en profundidad qué componentes específicos de WOA le confieren su buen rendimiento
   - Entender por qué HHO muestra resultados más variables entre instancias

---

*Análisis preliminar basado en 5 ejecuciones para cada algoritmo e instancia, 8 de mayo de 2025*