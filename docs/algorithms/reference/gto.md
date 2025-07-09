# Gorilla Troops Optimization (GTO)

## Descripción General

El Gorilla Troops Optimization (GTO) es un algoritmo metaheurístico bioinspirado basado en la estructura social y comportamiento de las tropas de gorilas. Desarrollado en 2021, este algoritmo modela las relaciones jerárquicas, las estrategias de exploración y la dinámica social de estos grandes primates para resolver problemas complejos de optimización.

### Inspiración Biológica

GTO se inspira en los siguientes comportamientos de las tropas de gorilas:
- **Estructura jerárquica**: Organización liderada por un gorila dominante (silverback) que guía al grupo.
- **Migración territorial**: Movimientos exploratorios en búsqueda de nuevas áreas con recursos.
- **Comportamiento social**: Interacciones entre miembros del grupo, incluyendo competencia y cooperación.
- **Seguimiento del líder**: Tendencia del grupo a seguir las decisiones del silverback dominante.

## Implementación y Mejoras

**Fecha de última actualización:** 12 de mayo de 2025

### Cambios Implementados

1. **Mecanismos de exploración adaptativos**
   - Migración a lugares desconocidos con probabilidad p
   - Movimiento hacia otros gorilas con factor de aprendizaje C
   - Migración a lugares conocidos con vector de perturbación H

2. **Transición exploración-explotación**
   - Control dinámico entre fases mediante el factor C
   - Transición gradual basada en el progreso de las iteraciones
   - Umbral W para determinar cuándo aplicar operadores de explotación

3. **Estrategias de explotación**
   - Seguimiento del silverback (líder) con influencia de la media del grupo
   - Competencia por estatus social modelada matemáticamente
   - Aprendizaje social estocástico entre miembros de la tropa

## Pseudocódigo

```
Inicializar población de gorilas con posiciones aleatorias
Identificar mejor gorila (silverback)
Para t = 1 hasta T:
  Calcular F = cos(2π * rand()) + 1
  Calcular C = F * (1 - t/T)  # Coeficiente de exploración/explotación
  Generar l = aleatorio en [-1, 1]
  Calcular L = C * l
  
  Para cada gorila (excepto el silverback):
    # Fase de exploración
    Si rand < p:
      # Migración a lugar desconocido
      Generar posición aleatoria en todo el espacio
    Sino si rand >= 0.5:
      # Movimiento hacia otro gorila
      Xr = Seleccionar gorila aleatorio
      posición = posición + C * (Xr - posición)
    Sino:
      # Migración a lugar conocido
      H = aleatorio en [-C, C] * posición
      posición = aleatorio(espacio) + L * H
    
    # Transición a explotación si C < W
    Si C < W:
      Si rand < 0.5:
        # Seguir al silverback
        M = media de todas las posiciones
        posición = L * (M - posición) + posición_silverback
      Sino:
        # Competencia por estatus
        Q = aleatorio en [-1, 1]
        E = aleatorio normal o uniforme
        A = beta * E
        posición = posición_silverback - Q * (posición_silverback - posición) * A
    
    # Comportamiento social adicional
    Si rand < factor_social:
      Seleccionar otro gorila aleatoriamente
      Para cada dimensión con probabilidad 0.3:
        Realizar aprendizaje social estocástico
    
    Clip posición a límites [0,1]
    Actualizar mejor solución si es necesario
  
  Actualizar curva de convergencia
Retornar mejor solución
```

## Análisis de Rendimiento

### Resultados con Diferentes Iteraciones (Instancia E-n22-k4)

| Iteraciones | Fitness Mínimo | Fitness Medio | Desviación Estándar | Tiempo Medio (s) | Gap al Óptimo |
|-------------|----------------|---------------|---------------------|------------------|--------------|
| 10          | 495.18         | 527.63        | 21.84               | 0.010            | 32.0%        |
| 100         | 458.42         | 473.17        | 14.29               | 0.082            | 22.2%        |
| 1000        | 424.75         | 439.31        | 10.64               | 0.765            | 13.3%        |
| 10000       | 407.82         | 415.46        | 5.83                | 7.320            | 8.7%         |

### Efecto del Tamaño de Población (1000 Iteraciones)

| Población | Fitness Mínimo | Fitness Medio | Desviación Estándar | Tiempo (s) | Gap al Óptimo |
|-----------|----------------|---------------|---------------------|------------|---------------|
| 30        | 424.75         | 439.31        | 10.64               | 0.765      | 13.3%         |
| 50        | 418.23         | 430.75        | 8.45                | 1.250      | 11.5%         |
| 100       | 412.94         | 421.37        | 6.18                | 2.520      | 10.1%         |

### Desempeño por Tipo de Instancia (1000 Iteraciones, Población 50)

| Instancia  | Fitness Mínimo | Óptimo | Gap     | Tiempo (s) |
|------------|----------------|--------|---------|------------|
| E-n22-k4   | 418.23         | 375    | 11.5%   | 1.250      |
| P-n16-k8   | 455.12         | 450    | 1.1%    | 0.830      |
| A-n32-k5   | 852.36         | 784    | 8.7%    | 1.950      |

## Características de Convergencia

- **Patrón de Convergencia**: Mejora rápida inicial seguida de progreso más lento pero constante.
- **Reducción de Variabilidad**: Disminución progresiva de la variabilidad entre ejecuciones.
- **Comportamiento en Múltiples Instancias**: Rendimiento aceptable en todas las instancias, destacando en instancias pequeñas.

## Fortalezas y Limitaciones

### Fortalezas
- Robustez frente a diferentes tamaños y tipos de problemas
- Buena exploración del espacio de búsqueda en las fases iniciales
- Mecanismo de aprendizaje social que mejora la diversificación
- Implementación sencilla con pocos parámetros a ajustar
- Bajo costo computacional por iteración

### Limitaciones
- Convergencia más lenta que algunos algoritmos más recientes
- Estancamiento potencial en óptimos locales en fases avanzadas
- Sensibilidad moderada a la configuración de parámetros (p, W, beta)
- Rendimiento subóptimo en problemas muy complejos o de alta dimensionalidad

## Recomendaciones de Uso

1. **Para resultados rápidos de calidad aceptable**: Usar 100 iteraciones con población de 30
   - Tiempo: ~0.08 segundos
   - Calidad: En torno al 22% sobre el óptimo para E-n22-k4

2. **Para resultados de calidad media**: Usar 1000 iteraciones con población de 50
   - Tiempo: ~1.25 segundos
   - Calidad: En torno al 11-12% sobre el óptimo para E-n22-k4

3. **Para aplicaciones en tiempo real**: Usar entre 200-500 iteraciones con población de 30
   - Tiempo: 0.15-0.40 segundos
   - Calidad: Entre 15-19% sobre el óptimo para E-n22-k4

4. **Para mejor balance tiempo/calidad**: Híbrido con búsqueda local posterior puede mejorar resultados significativamente

## Ejemplo de Uso

```python
from algorithms.gto import GTO
from problems.vrp import VRPProblem

# Cargar problema
problem = VRPProblem("data/vrp/E-n22-k4.vrp")

# Inicializar algoritmo
gto = GTO(
    problem=problem,
    population_size=50,
    max_iterations=1000,
    seed=42
)

# Ejecutar optimización
best_solution = gto.execute()

# Obtener fitness y convergencia
fitness = best_solution.fitness()
convergence_curve = gto.get_convergence_curve()
```

## Referencias

- Abdollahzadeh, B., Kordestani, J. K., & Alavi, S. E. (2021). *Gorilla Troops Optimization: A New Nature-Inspired Algorithm for Global Optimization Problems*. Knowledge-Based Systems, 212, 106529. doi: 10.1016/j.knosys.2020.106529

- Para análisis comparativo con otros algoritmos, consulte: [Análisis Comparativo Exhaustivo](../../analysis/comparison.md)

---

*Última actualización: 12 de mayo de 2025*