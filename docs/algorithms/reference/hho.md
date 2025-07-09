# Harris Hawks Optimization (HHO)

## Descripción General

El Harris Hawks Optimization (HHO) es un algoritmo metaheurístico bioinspirado basado en el comportamiento de caza cooperativa de los halcones de Harris (Parabuteo unicinctus). Propuesto por Heidari et al. en 2019, este algoritmo imita las estrategias de caza en equipo, emboscada y persecución que emplean estos depredadores, conocidos por su inteligencia y coordinación grupal al cazar presas.

### Inspiración Biológica

HHO se inspira en los siguientes comportamientos de los halcones de Harris:
- **Caza cooperativa**: Estrategia de caza en equipo donde varios halcones coordinan sus acciones.
- **Tácticas de asedio**: Diferentes patrones de acoso y emboscada hacia la presa.
- **Comportamiento de sorpresa**: Ataques súbitos desde múltiples direcciones.
- **Adaptación a la energía de la presa**: Cambio de tácticas según la energía de escape de la presa.

## Implementación y Mejoras

**Fecha de última actualización:** 12 de mayo de 2025

### Cambios Implementados

1. **Mecanismo de exploración-explotación basado en energía**
   - Modelo de energía de escape (E) que disminuye a lo largo de las iteraciones
   - Transición suave entre exploración (|E| ≥ 1) y explotación (|E| < 1)
   - Factor aleatorio E₀ para diversificar comportamientos entre diferentes halcones

2. **Estrategias de asedio adaptativas**
   - Cuatro tipos diferentes de asedio basados en la energía de escape:
     - Asedio suave: Aproximación gradual a la presa
     - Asedio duro: Aproximación más agresiva a la presa
     - Asedio suave con zambullidas rápidas: Combinación con vuelos de Lévy
     - Asedio duro con zambullidas rápidas: Estrategia de ataque final

3. **Incorporación de vuelos de Lévy**
   - Implementación precisa de la distribución de Lévy para modelar zambullidas
   - Mecanismo de comparación para seleccionar la mejor estrategia de ataque
   - Adaptación dinámica durante la fase de explotación

## Pseudocódigo

```
Inicializar población de halcones con posiciones aleatorias
Identificar mejor halcón (presa objetivo)
Para t = 1 hasta T:
  Calcular vector medio Xm de la población
  
  Para cada halcón (excepto el mejor):
    Calcular E0 = aleatorio en [-1, 1]
    Calcular E = 2 * E0 * (1 - t/T)
    
    # Fase de exploración
    Si |E| >= 1:
      Si q >= 0.5:
        X_rand = posición aleatoria en el espacio
        posición = X_rand - r1 * |X_rand - 2*r2*posición_actual|
      Sino:
        posición = (posición_presa - Xm) - r3 * (LB + r4*(UB - LB))
    
    # Fase de explotación
    Sino:
      r = aleatorio en [0, 1]
      Si r >= 0.5 y |E| >= 0.5:  # Asedio suave
        posición = posición_presa - E * |posición_presa - posición|
      
      Sino Si r >= 0.5 y |E| < 0.5:  # Asedio duro
        posición = posición_presa - E * |posición_presa - posición| / |E|
      
      Sino Si r < 0.5 y |E| >= 0.5:  # Asedio suave con zambullidas
        J = 2 * (1 - aleatorio())
        Y = posición_presa - E * |J * posición_presa - posición|
        Z = Y + aleatorio * levy_flight()
        posición = mejor_entre(Y, Z)
      
      Sino:  # Asedio duro con zambullidas
        Y = posición_presa - E * |posición_presa - posición|
        Z = Y + aleatorio * levy_flight()
        posición = mejor_entre(Y, Z)
    
    Clip posición a límites [0,1]
    Actualizar mejor solución si es necesario
  
  Actualizar curva de convergencia
Retornar mejor solución
```

## Análisis de Rendimiento

### Resultados con Diferentes Iteraciones (Instancia E-n22-k4)

| Iteraciones | Fitness Mínimo | Fitness Medio | Desviación Estándar | Tiempo Medio (s) | Gap al Óptimo |
|-------------|----------------|---------------|---------------------|------------------|--------------|
| 10          | 489.54         | 521.67        | 20.83               | 0.014            | 30.5%        |
| 100         | 436.21         | 458.43        | 15.26               | 0.115            | 16.3%        |
| 1000        | 407.93         | 422.58        | 9.31                | 1.080            | 8.8%         |
| 10000       | 391.26         | 399.87        | 5.43                | 10.450           | 4.3%         |

### Efecto del Tamaño de Población (1000 Iteraciones)

| Población | Fitness Mínimo | Fitness Medio | Desviación Estándar | Tiempo (s) | Gap al Óptimo |
|-----------|----------------|---------------|---------------------|------------|---------------|
| 30        | 407.93         | 422.58        | 9.31                | 1.080      | 8.8%          |
| 50        | 401.65         | 412.74        | 7.48                | 1.750      | 7.1%          |
| 100       | 392.83         | 401.56        | 5.92                | 3.250      | 4.8%          |

### Desempeño por Tipo de Instancia (1000 Iteraciones, Población 50)

| Instancia  | Fitness Mínimo | Óptimo | Gap     | Tiempo (s) |
|------------|----------------|--------|---------|------------|
| E-n22-k4   | 401.65         | 375    | 7.1%    | 1.750      |
| P-n16-k8   | 451.86         | 450    | 0.4%    | 1.120      |
| A-n32-k5   | 827.35         | 784    | 5.5%    | 2.450      |

## Características de Convergencia

- **Patrón de Convergencia**: Mejora rápida inicial con progresos significativos tanto en fases tempranas como intermedias.
- **Reducción de Variabilidad**: Estabilidad creciente con más iteraciones y poblaciones más grandes.
- **Comportamiento en Múltiples Instancias**: Rendimiento consistentemente bueno en todas las instancias, con gaps al óptimo moderados.

## Fortalezas y Limitaciones

### Fortalezas
- Equilibrio eficaz entre exploración global y explotación local
- Capacidad de escape de óptimos locales gracias a los vuelos de Lévy
- Adaptabilidad dinámica a diferentes fases de búsqueda
- Rendimiento sólido en diferentes tipos y tamaños de problemas
- Baja sensibilidad a valores iniciales y parámetros

### Limitaciones
- Mayor costo computacional que algoritmos más simples (evalúa Y y Z en explotación)
- Complejidad matemática moderada en implementación
- Sensibilidad al parámetro de energía
- Puede requerir más iteraciones para refinamiento preciso

## Recomendaciones de Uso

1. **Para resultados rápidos de calidad razonable**: Usar 100 iteraciones con población de 30
   - Tiempo: ~0.12 segundos
   - Calidad: En torno al 16% sobre el óptimo para E-n22-k4

2. **Para resultados de alta calidad**: Usar 1000 iteraciones con población de 50
   - Tiempo: ~1.75 segundos
   - Calidad: En torno al 7% sobre el óptimo para E-n22-k4

3. **Para resultados premium**: Usar 5000+ iteraciones con población de 80
   - Tiempo: ~6-7 segundos
   - Calidad: Alrededor del 4-5% sobre el óptimo

4. **Para aplicaciones en tiempo real**: Este algoritmo es especialmente efectivo cuando se requiere un buen equilibrio entre exploración y explotación en tiempo limitado. Usar 300-500 iteraciones con población de 30.

## Ejemplo de Uso

```python
from algorithms.hho import HHO
from problems.vrp import VRPProblem

# Cargar problema
problem = VRPProblem("data/vrp/E-n22-k4.vrp")

# Inicializar algoritmo
hho = HHO(
    problem=problem,
    population_size=50,
    max_iterations=1000,
    seed=42
)

# Ejecutar optimización
best_solution = hho.execute()

# Obtener fitness y convergencia
fitness = best_solution.fitness()
convergence_curve = hho.get_convergence_curve()
```

## Referencias

- Heidari, A. A., Mirjalili, S., Faris, H., Aljarah, I., Mafarja, M., & Chen, H. (2019). *Harris hawks optimization: Algorithm and applications*. Future Generation Computer Systems, 97, 849-872. doi: 10.1016/j.future.2019.02.028

- Para análisis comparativo con otros algoritmos, consulte: [Análisis Comparativo Exhaustivo](../../analysis/comparison.md)

---

*Última actualización: 12 de mayo de 2025*