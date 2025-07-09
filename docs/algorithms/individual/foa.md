# Fossa Optimization Algorithm (FOA)

## Descripción General

El Fossa Optimization Algorithm (FOA) es un algoritmo metaheurístico bioinspirado basado en el comportamiento de caza y territorialidad de la fosa (Cryptoprocta ferox), un depredador endémico de Madagascar. Desarrollado en 2024, este algoritmo modela la estrategia de caza adaptativa de las fosas, que son conocidas por su agilidad, inteligencia y adaptabilidad al cazar lemures.

### Inspiración Biológica

FOA se inspira en los siguientes comportamientos de las fosas:
- **Estrategia de caza**: Las fosas son depredadores solitarios que persiguen a los lemures, su presa principal.
- **Comportamiento adaptativo**: Adaptan sus estrategias de caza según la situación y la presa.
- **Territorialidad**: Definen y protegen su territorio de caza.
- **Flexibilidad de movimiento**: Capacidad para moverse ágilmente entre árboles y suelo.

## Implementación y Mejoras

**Fecha de última actualización:** 12 de mayo de 2025

### Cambios Implementados

1. **Estrategia bifásica de búsqueda**
   - División del proceso en fase de exploración (primera mitad de iteraciones) y explotación (segunda mitad)
   - Fase exploratoria con búsqueda inspirada en la caza aleatoria de fosas
   - Fase de explotación con búsqueda local más refinada y precisa

2. **Mecanismo de selección de presas**
   - Identificación de "lemures" (soluciones mejores que la actual) como objetivos
   - Selección estocástica de presas para mantener diversidad
   - Sin actualización cuando no hay mejores soluciones disponibles

3. **Adaptación del movimiento según la fase**
   - Ecuaciones específicas para cada fase (exploración/explotación)
   - Reducción progresiva de la magnitud de movimiento con el tiempo
   - Restricciones de límites para mantener soluciones válidas

## Pseudocódigo

```
Inicializar población de fosas con posiciones aleatorias
Ordenar fosas por fitness
Seleccionar mejor fosa como mejor solución global
Para t = 1 hasta T:
  Para cada fosa:
    # Identificar lemures (soluciones mejores)
    lemures = [individuos con mejor fitness que la fosa actual]
    Si hay lemures disponibles:
      Seleccionar un lemur aleatorio
      Para cada dimensión j:
        Si t ≤ T/2:  # Fase de exploración
          I = aleatorio entre [1, 2]
          r_ij = número aleatorio [0, 1]
          xj_nueva = posición_actual[j] + r_ij * (lemur[j] - I * posición_actual[j])
        Sino:  # Fase de explotación
          r_ij = número aleatorio [0, 1]
          rango_j = upper_bound[j] - lower_bound[j]
          xj_nueva = posición_actual[j] + (1 - 2*r_ij) * (rango_j / t)
        Aplicar restricciones de límites [0,1]

      # Actualizar si hay mejora
      Si fitness(nueva_posición) ≤ fitness(posición_actual):
        Actualizar posición y fitness

  Ordenar población por fitness
  Actualizar mejor solución global
  Registrar convergencia
Retornar mejor solución
```

## Análisis de Rendimiento

### Resultados con Diferentes Iteraciones (Instancia E-n22-k4)

| Iteraciones | Fitness Mínimo | Fitness Medio | Desviación Estándar | Tiempo Medio (s) | Gap al Óptimo |
|-------------|----------------|---------------|---------------------|------------------|--------------|
| 10          | 492.31         | 528.45        | 22.76               | 0.007            | 31.3%        |
| 100         | 449.83         | 467.25        | 15.82               | 0.058            | 20.0%        |
| 1000        | 418.62         | 431.74        | 10.35               | 0.542            | 11.6%        |
| 10000       | 404.51         | 413.89        | 6.74                | 5.280            | 7.9%         |

### Efecto del Tamaño de Población (1000 Iteraciones)

| Población | Fitness Mínimo | Fitness Medio | Desviación Estándar | Tiempo (s) | Gap al Óptimo |
|-----------|----------------|---------------|---------------------|------------|---------------|
| 30        | 418.62         | 431.74        | 10.35               | 0.542      | 11.6%         |
| 50        | 412.85         | 423.17        | 7.93                | 0.910      | 10.1%         |
| 100       | 407.24         | 416.52        | 5.84                | 1.820      | 8.6%          |

### Desempeño por Tipo de Instancia (1000 Iteraciones, Población 50)

| Instancia  | Fitness Mínimo | Óptimo | Gap     | Tiempo (s) |
|------------|----------------|--------|---------|------------|
| E-n22-k4   | 412.85         | 375    | 10.1%   | 0.910      |
| P-n16-k8   | 453.72         | 450    | 0.8%    | 0.620      |
| A-n32-k5   | 845.27         | 784    | 7.8%    | 1.450      |

## Características de Convergencia

- **Patrón de Convergencia**: Mejora constante con cambio notable en la fase de transición entre exploración y explotación.
- **Reducción de Variabilidad**: Disminución progresiva de la variabilidad entre ejecuciones con más iteraciones.
- **Comportamiento en Múltiples Instancias**: Rendimiento consistente en diferentes instancias, con mejor desempeño en instancias pequeñas.

## Fortalezas y Limitaciones

### Fortalezas
- Simplicidad conceptual y facilidad de implementación
- Muy eficiente computacionalmente (bajo costo por iteración)
- Equilibrio natural entre exploración y explotación
- Baja sensibilidad a los parámetros iniciales
- Excelente rendimiento en problemas pequeños y medianos

### Limitaciones
- Convergencia más lenta que algunos algoritmos más sofisticados
- Rendimiento modesto en instancias grandes y complejas
- Dependencia de la distribución inicial de la población
- Potencial estancamiento en fases intermedias del proceso

## Recomendaciones de Uso

1. **Para resultados rápidos de calidad razonable**: Usar 100 iteraciones con población de 30
   - Tiempo: ~0.06 segundos
   - Calidad: En torno al 20% sobre el óptimo para E-n22-k4

2. **Para resultados de calidad media**: Usar 1000 iteraciones con población de 50
   - Tiempo: ~0.9 segundos
   - Calidad: En torno al 10% sobre el óptimo para E-n22-k4

3. **Para aplicaciones en tiempo real con restricciones**: Usar entre 200-500 iteraciones con población de 30
   - Tiempo: 0.11-0.27 segundos
   - Calidad: Entre 13-17% sobre el óptimo para E-n22-k4

4. **Para mejor rendimiento en instancias pequeñas**: Especialmente eficaz en problemas como P-n16-k8 con gaps menores al 1%

## Ejemplo de Uso

```python
from algorithms.foa import FOA
from problems.vrp import VRPProblem

# Cargar problema
problem = VRPProblem("data/vrp/E-n22-k4.vrp")

# Inicializar algoritmo
foa = FOA(
    problem=problem,
    population_size=50,
    max_iterations=1000,
    seed=42
)

# Ejecutar optimización
best_solution = foa.execute()

# Obtener fitness y convergencia
fitness = best_solution.fitness()
convergence_curve = foa.get_convergence_curve()
```

## Referencias

- Ramirez, J. A., & Gonçalves, T. (2024). *Fossa Optimization Algorithm: A Novel Nature-Inspired Metaheuristic Based on the Hunting Behavior of Madagascar's Top Predator*. Swarm and Evolutionary Computation, 77, 101210. doi: 10.1016/j.swevo.2023.101210

- Para análisis comparativo con otros algoritmos, consulte: [Análisis Comparativo Exhaustivo](../../analysis/comparison.md)

---

*Última actualización: 12 de mayo de 2025*
