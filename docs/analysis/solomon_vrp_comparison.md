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

## Conclusiones

1. **Recomendación principal**: Para instancias Solomon VRP, SMA ofrece el mejor equilibrio entre calidad de solución y tiempo de ejecución, con alta estabilidad.

2. **Alternativa de alta calidad**: WOA produce las mejores soluciones, pero requiere aproximadamente el doble de tiempo que SMA.

3. **No recomendado**: OPA tiene un rendimiento significativamente inferior y debe ser mejorado antes de considerarse para aplicaciones prácticas.

4. **Mejoras futuras**:
   - Optimizar OPA para mejorar su rendimiento en instancias VRP.
   - Evaluar el impacto de aumentar el número de iteraciones en SMA.
   - Analizar el comportamiento de los algoritmos en instancias más grandes.

## Referencia de Archivos

Los resultados detallados y gráficos se encuentran en:
- CSV de resumen: `results/massive_benchmark_20250512_142739/massive_benchmark_summary.csv`
- Reporte HTML: `results/massive_benchmark_20250512_142739/massive_benchmark_report.html`
- Gráficos comparativos: `benchmark_comparisons/`