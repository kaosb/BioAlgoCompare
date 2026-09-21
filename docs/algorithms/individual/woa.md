# Whale Optimization Algorithm (WOA)

## Descripción General

El Whale Optimization Algorithm (WOA) es un algoritmo metaheurístico bioinspirado basado en el comportamiento de alimentación de las ballenas jorobadas. Propuesto por Mirjalili y Lewis en 2016, este algoritmo imita la técnica de caza de burbujas en red (bubble-net feeding) y la búsqueda de presas de estos cetáceos, creando un equilibrio entre exploración global y explotación local.

### Inspiración Biológica

WOA se inspira en los siguientes comportamientos de las ballenas jorobadas:
- **Caza de burbujas en red**: Estrategia única donde las ballenas nadan en espiral alrededor de sus presas mientras liberan burbujas de aire.
- **Búsqueda de presas**: Fase de exploración aleatoria para localizar agrupaciones de presas.
- **Encercamiento**: Las ballenas rodean a sus presas antes de atacar.
- **Movimiento en espiral**: Patrón de natación en espiral logarítmica durante la caza.

## Implementación y Mejoras

**Fecha de última actualización:** 12 de mayo de 2025

### Cambios Implementados

1. **Estrategia dual de movimiento**
   - División entre comportamiento de encogimiento (aproximación directa) y espiral
   - Selección estocástica entre estrategias con probabilidad adaptativa
   - Implementación matemática precisa de la espiral logarítmica

2. **Parámetros de control adaptativos**
   - Coeficiente 'a' que disminuye linealmente de 2 a 0 con el progreso de las iteraciones
   - Balance dinámico entre exploración y explotación mediante los vectores A y C
   - Factor de espiral a2 para controlar la forma del movimiento helicoidal

3. **Incorporación de búsqueda aleatoria**
   - Mecanismo para evitar óptimos locales durante la exploración (cuando |A| ≥ 1)
   - Selección de posiciones aleatorias de referencia para diversificación
   - Transición suave entre comportamientos de exploración y explotación

## Pseudocódigo

```
Inicializar población de ballenas con posiciones aleatorias
Encontrar mejor ballena
Para t = 1 hasta T:
  Calcular a = 2 - t*(2/T)  # Decrece linealmente de 2 a 0

  Para cada ballena (excepto la mejor):
    # Seleccionar estrategia
    p = aleatorio en [0, 1]

    Si p < 0.5:  # Estrategia de encercamiento/búsqueda
      r1, r2 = aleatorios en [0, 1]
      A = 2*a*r1 - a
      C = 2*r2

      Si |A| < 1:  # Encercamiento (explotación)
        Para cada dimensión i:
          D = |C*mejor_posición[i] - posición[i]|
          posición[i] = mejor_posición[i] - A*D
      Sino:  # Búsqueda aleatoria (exploración)
        X_rand = posición aleatoria
        Para cada dimensión i:
          D = |C*X_rand[i] - posición[i]|
          posición[i] = X_rand[i] - A*D

    Sino:  # Estrategia de espiral (bubble-net)
      Para cada dimensión i:
        D = |mejor_posición[i] - posición[i]|
        l = aleatorio en [-1, 1]
        posición[i] = D*exp(a2*l)*cos(2π*l) + mejor_posición[i]

    Clip posición a límites [0,1]
    Actualizar mejor solución si es necesario

  Actualizar curva de convergencia
Retornar mejor solución
```

## Análisis de Rendimiento

### Resultados con Diferentes Iteraciones (Instancia E-n22-k4)

| Iteraciones | Fitness Mínimo | Fitness Medio | Desviación Estándar | Tiempo Medio (s) | Gap al Óptimo |
|-------------|----------------|---------------|---------------------|------------------|--------------|
| 10          | 495.38         | 529.54        | 21.74               | 0.009            | 32.1%        |
| 100         | 443.75         | 464.82        | 15.38               | 0.071            | 18.3%        |
| 1000        | 416.93         | 431.58        | 10.24               | 0.685            | 11.2%        |
| 10000       | 402.36         | 411.94        | 6.35                | 6.750            | 7.3%         |

### Efecto del Tamaño de Población (1000 Iteraciones)

| Población | Fitness Mínimo | Fitness Medio | Desviación Estándar | Tiempo (s) | Gap al Óptimo |
|-----------|----------------|---------------|---------------------|------------|---------------|
| 30        | 416.93         | 431.58        | 10.24               | 0.685      | 11.2%         |
| 50        | 409.47         | 422.65        | 8.62                | 1.140      | 9.2%          |
| 100       | 400.81         | 412.37        | 7.34                | 2.280      | 6.9%          |

### Desempeño por Tipo de Instancia (1000 Iteraciones, Población 50)

| Instancia  | Fitness Mínimo | Óptimo | Gap     | Tiempo (s) |
|------------|----------------|--------|---------|------------|
| E-n22-k4   | 409.47         | 375    | 9.2%    | 1.140      |
| P-n16-k8   | 453.78         | 450    | 0.8%    | 0.760      |
| A-n32-k5   | 842.53         | 784    | 7.5%    | 1.640      |

## Características de Convergencia

- **Patrón de Convergencia**: Mejora rápida inicial seguida de progreso más gradual.
- **Reducción de Variabilidad**: Buena consistencia entre ejecuciones, especialmente con poblaciones mayores.
- **Comportamiento en Múltiples Instancias**: Rendimiento adecuado en todas las instancias, destacando en problemas pequeños.

## Fortalezas y Limitaciones

### Fortalezas
- Simplicidad conceptual y facilidad de implementación
- Equilibrio natural entre exploración y explotación
- Mecanismo dual de movimiento que diversifica la búsqueda
- Adaptación automática del comportamiento según el progreso
- Eficiencia computacional (bajo costo por iteración)

### Limitaciones
- Convergencia más lenta que algoritmos más recientes
- Sensibilidad moderada al parámetro de espiral a2
- Rendimiento variable en problemas altamente multimodales
- Tendencia a convergencia prematura en algunas configuraciones

## Recomendaciones de Uso

1. **Para resultados rápidos de calidad razonable**: Usar 100 iteraciones con población de 30
   - Tiempo: ~0.07 segundos
   - Calidad: En torno al 18% sobre el óptimo para E-n22-k4

2. **Para resultados de calidad media**: Usar 1000 iteraciones con población de 50
   - Tiempo: ~1.1 segundos
   - Calidad: En torno al 9% sobre el óptimo para E-n22-k4

3. **Para aplicaciones en tiempo real**: Usar entre 200-500 iteraciones con población de 30
   - Tiempo: 0.14-0.35 segundos
   - Calidad: Entre 12-16% sobre el óptimo para E-n22-k4

4. **Para mejores resultados**: Incrementar el parámetro a2 a 0.7-1.0 puede mejorar el comportamiento espiral y la calidad de la búsqueda.

## Ejemplo de Uso

```python
from algorithms.woa import WOA
from problems.vrp import VRPProblem

# Cargar problema
problem = VRPProblem("data/vrp/E-n22-k4.vrp")

# Inicializar algoritmo
woa = WOA(
    problem=problem,
    population_size=50,
    max_iterations=1000,
    seed=42
)

# Ejecutar optimización
best_solution = woa.execute()

# Obtener fitness y convergencia
fitness = best_solution.fitness()
convergence_curve = woa.get_convergence_curve()
```

## Referencias

- Mirjalili, S., & Lewis, A. (2016). *The Whale Optimization Algorithm*. Advances in Engineering Software, 95, 51-67. doi: 10.1016/j.advengsoft.2016.01.008

- Para análisis comparativo con otros algoritmos, consulte: [Análisis Comparativo Exhaustivo](../../analysis/comparison.md)

---

*Última actualización: 12 de mayo de 2025*
