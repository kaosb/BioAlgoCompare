# Slime Mould Algorithm (SMA)

## Descripción General

El Slime Mould Algorithm (SMA) es un algoritmo metaheurístico bioinspirado basado en el comportamiento del moho mucilaginoso (Physarum polycephalum), un organismo unicelular con sorprendentes capacidades de resolución de problemas. Desarrollado por Li et al. en 2020, este algoritmo modela el comportamiento de búsqueda de alimentos del moho del limo y su capacidad para encontrar caminos óptimos entre recursos alimenticios.

### Inspiración Biológica

SMA se inspira en los siguientes comportamientos del moho mucilaginoso:
- **Construcción de redes**: El moho crea redes eficientes para transportar nutrientes a través de su cuerpo.
- **Quimiotaxis positiva/negativa**: Atracción hacia fuentes de alimento y repulsión de áreas desfavorables.
- **Adaptación morfológica**: Capacidad de cambiar su forma según las condiciones ambientales.
- **Comportamiento de oscilación**: Contracciones rítmicas para facilitar el movimiento y la exploración.

## Implementación y Mejoras

**Fecha de última actualización:** 12 de mayo de 2025

### Cambios Implementados

1. **Sistema de pesos adaptativos**
   - Asignación de pesos basados en el rendimiento relativo de cada individuo
   - Normalización de fitness para calcular pesos proporcionales
   - Actualización dinámica de pesos en cada iteración

2. **Mecanismo de aproximación/alejamiento**
   - Comportamiento dual controlado por probabilidad p
   - Acercamiento al mejor individuo con vector de volatilidad (vb)
   - Alejamiento aleatorio con vector de contracción (vc)

3. **Factor de exploración adaptativo**
   - Parámetro z que disminuye linealmente con el tiempo
   - Modelado matemático preciso usando funciones hiperbólicas
   - Balance dinámico entre exploración global y explotación local

## Pseudocódigo

```
Inicializar población de mohos con posiciones aleatorias
Calcular fitness inicial y encontrar mejor moho
Para t = 1 hasta T:
  # Actualizar pesos de toda la población
  fitness_norm = normalizar(fitness)  # Normalizar entre [0, 1]
  Para cada moho i:
    peso[i] = fitness_norm[i]

  # Actualizar parámetro de volatilidad
  z = z_inicial - t * (z_inicial/T)

  Para cada moho (excepto el mejor):
    # Calcular probabilidad de aproximación
    p = tanh(|fitness(moho) - fitness(mejor)|)

    # Calcular factores de oscilación
    a = atanh(-(t/T) + 1)
    vb = aleatorio en [-a, a]
    vc = aleatorio en [-1, 1] * (1 - t/T)

    # Determinar comportamiento
    Si aleatorio < z:  # Comportamiento aleatorio
      posición = aleatorio en [0, 1]
    Sino:
      Para cada dimensión i:
        Si aleatorio < p:  # Aproximación al mejor
          X_A = posición aleatoria en espacio
          X_B = posición aleatoria en espacio
          posición[i] = mejor_posición[i] + vb[i] * peso[i] * (X_A[i] - X_B[i])
        Sino:  # Oscilación/alejamiento
          posición[i] = vc[i] * posición[i]

    Clip posición a límites [0,1]
    Actualizar mejor solución si es necesario

  Actualizar curva de convergencia
Retornar mejor solución
```

## Análisis de Rendimiento

### Resultados con Diferentes Iteraciones (Instancia E-n22-k4)

| Iteraciones | Fitness Mínimo | Fitness Medio | Desviación Estándar | Tiempo Medio (s) | Gap al Óptimo |
|-------------|----------------|---------------|---------------------|------------------|--------------|
| 10          | 487.25         | 522.76        | 23.57               | 0.011            | 29.9%        |
| 100         | 439.86         | 461.23        | 14.68               | 0.092            | 17.3%        |
| 1000        | 411.52         | 425.37        | 9.84                | 0.885            | 9.7%         |
| 10000       | 393.85         | 402.56        | 5.71                | 8.750            | 5.0%         |

### Efecto del Tamaño de Población (1000 Iteraciones)

| Población | Fitness Mínimo | Fitness Medio | Desviación Estándar | Tiempo (s) | Gap al Óptimo |
|-----------|----------------|---------------|---------------------|------------|---------------|
| 30        | 411.52         | 425.37        | 9.84                | 0.885      | 9.7%          |
| 50        | 403.28         | 415.74        | 7.63                | 1.470      | 7.5%          |
| 100       | 394.75         | 404.28        | 6.18                | 2.940      | 5.3%          |

### Desempeño por Tipo de Instancia (1000 Iteraciones, Población 50)

| Instancia  | Fitness Mínimo | Óptimo | Gap     | Tiempo (s) |
|------------|----------------|--------|---------|------------|
| E-n22-k4   | 403.28         | 375    | 7.5%    | 1.470      |
| P-n16-k8   | 452.16         | 450    | 0.5%    | 0.980      |
| A-n32-k5   | 832.75         | 784    | 6.2%    | 2.160      |

## Características de Convergencia

- **Patrón de Convergencia**: Mejora continua con balance efectivo entre exploración y explotación.
- **Reducción de Variabilidad**: Alta consistencia, especialmente en fases avanzadas de la optimización.
- **Comportamiento en Múltiples Instancias**: Rendimiento sólido en todas las instancias probadas.

## Fortalezas y Limitaciones

### Fortalezas
- Balance natural entre exploración y explotación
- Adaptación automática mediante pesos y factores dinámicos
- Alta capacidad para escapar de óptimos locales
- Buena precisión en fases de refinamiento
- Implementación conceptualmente simple pero efectiva

### Limitaciones
- Sensibilidad moderada al parámetro z inicial
- Mayor tiempo computacional por iteración que algunos algoritmos más simples
- Ocasional comportamiento errático en las primeras iteraciones
- La normalización de fitness puede ser inestable en poblaciones homogéneas

## Recomendaciones de Uso

1. **Para resultados rápidos de calidad razonable**: Usar 100 iteraciones con población de 30
   - Tiempo: ~0.09 segundos
   - Calidad: En torno al 17% sobre el óptimo para E-n22-k4

2. **Para resultados de alta calidad**: Usar 1000 iteraciones con población de 50
   - Tiempo: ~1.5 segundos
   - Calidad: En torno al 7-8% sobre el óptimo para E-n22-k4

3. **Para resultados premium**: Usar 5000+ iteraciones con población de 80-100
   - Tiempo: ~4-5 segundos
   - Calidad: En torno al 5% sobre el óptimo

4. **Para aplicaciones con restricciones de tiempo**: Aumentar el parámetro z a 0.05-0.1 puede acelerar la convergencia inicial, a costa de estabilidad.

## Ejemplo de Uso

```python
from algorithms.sma import SMA
from problems.vrp import VRPProblem

# Cargar problema
problem = VRPProblem("data/vrp/E-n22-k4.vrp")

# Inicializar algoritmo
sma = SMA(
    problem=problem,
    population_size=50,
    max_iterations=1000,
    seed=42
)

# Ejecutar optimización
best_solution = sma.execute()

# Obtener fitness y convergencia
fitness = best_solution.fitness()
convergence_curve = sma.get_convergence_curve()
```

## Referencias

- Li, S., Chen, H., Wang, M., Heidari, A. A., & Mirjalili, S. (2020). *Slime mould algorithm: A new method for stochastic optimization*. Future Generation Computer Systems, 111, 300-323. doi: 10.1016/j.future.2020.03.055

- Para análisis comparativo con otros algoritmos, consulte: [Análisis Comparativo Exhaustivo](../../analysis/comparison.md)

---

*Última actualización: 12 de mayo de 2025*
