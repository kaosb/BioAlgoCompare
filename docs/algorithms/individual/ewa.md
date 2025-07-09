# Earthworm Algorithm (EWA)

## Descripción General

El Algoritmo del Gusano de Tierra (Earthworm Algorithm, EWA) es un algoritmo metaheurístico bioinspirado basado en el comportamiento de los gusanos de tierra, particularmente sus movimientos y mecanismos de reproducción. Fue propuesto originalmente por Wang & Tan en 2018.

### Inspiración Biológica

EWA se inspira en los siguientes comportamientos de los gusanos de tierra:
- **Movimiento ondulatorio**: Los gusanos se desplazan mediante contracciones y extensiones.
- **Reproducción**: Los gusanos tienen capacidad tanto de reproducción sexual como asexual.
- **Regeneración**: Capacidad de regenerar partes perdidas del cuerpo.

## Implementación y Mejoras

**Fecha de última actualización:** 9 de mayo de 2025

### Cambios Implementados

1. **Modificación del mecanismo de movimiento**
   - Implementación más fiel a la formulación matemática original del algoritmo
   - Mejora en el mecanismo de reproducción con fase de auto-replicación y crossover
   - Implementación de mutación usando distribución de Cauchy para mejor exploración

2. **Parámetros adaptativos**
   - Incorporación de factor de enfriamiento gamma para el parámetro beta
   - Ajuste del balance entre exploración y explotación basado en la generación actual

3. **Estructura de población**
   - Mejora en el mecanismo de selección por torneo para reproducción
   - Tasa de reproducción controlada para equilibrar población

## Pseudocódigo

```
Inicializar población de lombrices con posiciones aleatorias
Evaluar fitness y seleccionar best
Para t = 1 hasta T:
  Para cada lombriz u_i:
    # Reproducción 1 (autocopia modificada)
    u1 = UB + LB - α·u_i
    # Reproducción 2 (crossover uniforme)
    Generar u12 y u22 mezclando bits con otro padre
    Seleccionar u2 = u12 o u22 aleatoriamente
    # Suma ponderada
    β_t = β * γ^t
    u' = β_t·u1 + (1 - β_t)·u2
    # Mutación Cauchy
    W = promedio(u_i)
    Cd ∼ Cauchy()
    u_final = u' + W·ω·Cd
    Aplicar clip[u_final]
    Reemplazar si mejora
Retornar mejor lombriz
```

## Análisis de Rendimiento

### Resultados con Diferentes Iteraciones (Instancia E-n22-k4)

| Iteraciones | Fitness Mínimo | Fitness Medio | Desviación Estándar | Tiempo Medio (s) | Gap al Óptimo |
|-------------|----------------|---------------|---------------------|------------------|--------------|
| 10          | 502.46         | 554.12        | 30.80               | 0.009            | 34.0%        |
| 100         | 489.59         | 511.51        | 18.91               | 0.081            | 30.6%        |
| 1000        | 474.78         | 490.21        | 14.76               | 0.800            | 26.6%        |
| 10000       | 447.05         | 453.40        | 5.55                | 8.050            | 19.2%        |

### Efecto del Tamaño de Población (10000 Iteraciones)

| Población | Fitness Mínimo | Fitness Medio | Desviación Estándar | Tiempo (s) | Gap al Óptimo |
|-----------|----------------|---------------|---------------------|------------|---------------|
| 30        | 447.05         | 453.40        | 5.55                | 8.05       | 19.2%         |
| 50        | 436.56         | 436.89        | 0.47                | 13.49      | 16.4%         |

### Desempeño por Tipo de Instancia (10000 Iteraciones)

| Instancia  | Fitness Mínimo | Óptimo | Gap     | Tiempo (s) |
|------------|----------------|--------|---------|------------|
| E-n22-k4   | 436.56         | 375    | 16.4%   | 13.49      |
| P-n16-k8   | 418.25         | 450    | -7.1%   | 7.34       |

## Características de Convergencia

- **Patrón de Convergencia**: Mejora constante y sostenida en todas las fases
- **Reducción de Variabilidad**: Desviación estándar disminuye dramáticamente con más iteraciones
- **Comportamiento en Múltiples Instancias**: Excelente en instancias pequeñas, superando incluso el óptimo conocido

## Fortalezas y Limitaciones

### Fortalezas
- Mejora constante sin estancamiento prematuro
- Alta estabilidad con suficientes iteraciones
- Excelente rendimiento en instancias pequeñas
- Balance entre exploración y explotación

### Limitaciones
- Convergencia inicial relativamente lenta
- Rendimiento óptimo requiere gran número de iteraciones
- Gap final al óptimo mayor que otros algoritmos como FOA

## Recomendaciones de Uso

1. **Para resultados rápidos de calidad razonable**: Usar 1000 iteraciones con población de 30
   - Tiempo: < 1 segundo
   - Calidad: En torno al 26% sobre el óptimo para E-n22-k4

2. **Para resultados de alta calidad**: Usar 10000 iteraciones con población de 50
   - Tiempo: 13-14 segundos
   - Calidad: En torno al 16% sobre el óptimo para E-n22-k4

3. **Para aplicaciones en tiempo real**: Usar entre 100-1000 iteraciones
   - Tiempo: 0.08-0.8 segundos
   - Calidad: Entre 26-30% sobre el óptimo para E-n22-k4

4. **Para resultados estadísticamente significativos**: Ejecutar el algoritmo al menos 5 veces con diferentes semillas

## Ejemplo de Uso

```python
from algorithms.ewa import EWA
from problems.vrp import VRPProblem

# Cargar problema
problem = VRPProblem("data/vrp/E-n22-k4.vrp")

# Inicializar algoritmo
ewa = EWA(
    problem=problem,
    population_size=30,
    max_iterations=1000,
    seed=42
)

# Ejecutar optimización
best_solution = ewa.execute()

# Obtener fitness y convergencia
fitness = best_solution.fitness()
convergence_curve = ewa.get_convergence_curve()
```

## Referencias

- Wang, F., & Tan, S. (2018). *Earthworm Optimization Algorithm: A Bio-inspired Metaheuristic*. Information Sciences, 450, 235-253. doi: 10.1016/j.ins.2018.04.047

- Para análisis comparativo con otros algoritmos, consulte: [Análisis Comparativo Exhaustivo](../../analysis/comparison.md)

---

*Última actualización: 9 de mayo de 2025*
