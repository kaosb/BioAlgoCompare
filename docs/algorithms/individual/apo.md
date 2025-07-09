# Artificial Protozoa Optimizer (APO)

## Descripción General

El Artificial Protozoa Optimizer (APO) es un algoritmo metaheurístico bioinspirado desarrollado en 2024. Está basado en el comportamiento de los protozoos, un grupo diverso de microorganismos unicelulares. El algoritmo modela particularmente sus estrategias de nutrición, mecanismos reproductivos y comportamientos adaptativos para resolver problemas complejos de optimización.

### Inspiración Biológica

APO se inspira en los siguientes comportamientos de los protozoos:
- **Heterotrofia y Autotrofia**: Diferentes estrategias para obtener nutrientes del entorno.
- **Reproducción**: Capacidad de reproducirse tanto de manera asexual como sexual.
- **Dormancia**: Capacidad de entrar en un estado inactivo bajo condiciones desfavorables.
- **Adaptabilidad**: Capacidad de modificar su comportamiento según las condiciones del entorno.

## Implementación y Mejoras

**Fecha de última actualización:** 10 de mayo de 2025

### Cambios Implementados

1. **Comportamiento Nutricional Adaptativo**
   - Implementación de mecanismos de autotrofia y heterotrofia basados en la posición relativa en la población
   - Factores de ponderación dinámicos basados en el fitness relativo
   - Ajuste adaptativo de la intensidad de movimiento según la fase de optimización

2. **Estrategia de Reproducción y Dormancia**
   - Probabilidad de reproducción o dormancia basada en la posición en la población
   - Mecanismo de dormancia para reiniciar soluciones estancadas
   - Reproducción con modificaciones parciales para equilibrar exploración y explotación

3. **Modulación por Fase de Búsqueda**
   - Adaptación de parámetros según la iteración actual y máxima
   - Funciones trigonométricas para modular la intensidad de búsqueda
   - Control dinámico de la exploración/explotación

## Pseudocódigo

```
Inicializar población de protozoos con posiciones aleatorias
Ordenar población por fitness
Seleccionar mejor protozoo como mejor solución global
Para t = 1 hasta T:
  Para cada protozoo i:
    Calcular probabilidades dinámicas (pf, pah, pdr)
    Si rand < pf:
      Si rand < pdr:
        # Dormancia
        Generar nueva posición aleatoria
      Sino:
        # Reproducción
        Seleccionar dimensiones aleatoriamente (matriz Mr)
        Modificar posición con factor aleatorio en dimensiones seleccionadas
    Sino:
      Seleccionar dimensiones según posición en población (matriz Mf)
      Si rand < pah:
        # Autotrofia
        Calcular vector de movimiento basado en vecinos y solución aleatoria
        Modular intensidad según fase de optimización
        Actualizar posición
      Sino:
        # Heterotrofia
        Calcular nueva posición con perturbación adaptativa
        Modular intensidad según fase de optimización
        Actualizar posición
    Aplicar restricciones (clip)
  Ordenar población
  Actualizar mejor solución global
  Registrar convergencia
Retornar mejor solución
```

## Análisis de Rendimiento

### Resultados con Diferentes Iteraciones (Instancia E-n22-k4)

| Iteraciones | Fitness Mínimo | Fitness Medio | Desviación Estándar | Tiempo Medio (s) | Gap al Óptimo |
|-------------|----------------|---------------|---------------------|------------------|--------------|
| 10          | 498.32         | 536.15        | 26.42               | 0.012            | 32.9%        |
| 100         | 467.25         | 485.63        | 16.37               | 0.095            | 24.6%        |
| 1000        | 422.39         | 437.84        | 10.95               | 0.910            | 12.6%        |
| 10000       | 410.57         | 418.72        | 6.88                | 9.120            | 9.5%         |

### Efecto del Tamaño de Población (1000 Iteraciones)

| Población | Fitness Mínimo | Fitness Medio | Desviación Estándar | Tiempo (s) | Gap al Óptimo |
|-----------|----------------|---------------|---------------------|------------|---------------|
| 30        | 422.39         | 437.84        | 10.95               | 0.910      | 12.6%         |
| 50        | 414.82         | 428.49        | 8.76                | 1.520      | 10.6%         |
| 100       | 405.15         | 414.32        | 7.32                | 3.180      | 8.0%          |

### Desempeño por Tipo de Instancia (1000 Iteraciones, Población 50)

| Instancia  | Fitness Mínimo | Óptimo | Gap     | Tiempo (s) |
|------------|----------------|--------|---------|------------|
| E-n22-k4   | 414.82         | 375    | 10.6%   | 1.520      |
| P-n16-k8   | 453.21         | 450    | 0.7%    | 0.970      |
| A-n32-k5   | 864.78         | 784    | 10.3%   | 2.380      |

## Características de Convergencia

- **Patrón de Convergencia**: Mejora rápida inicial seguida de convergencia constante y refinamiento gradual.
- **Reducción de Variabilidad**: Baja variabilidad entre ejecuciones, especialmente con poblaciones grandes.
- **Comportamiento en Múltiples Instancias**: Consistentemente efectivo en diferentes tamaños de instancias, con resultados especialmente cercanos al óptimo en instancias pequeñas.

## Fortalezas y Limitaciones

### Fortalezas
- Excelente equilibrio entre exploración y explotación
- Alta capacidad para escapar de óptimos locales
- Convergencia rápida en etapas iniciales
- Adaptación dinámica a diferentes fases de optimización
- Especialmente eficaz en instancias pequeñas y medianas

### Limitaciones
- Mayor tiempo computacional por individuo que algoritmos más simples
- La complejidad de cálculo aumenta con el tamaño de la población
- Rendimiento menos destacado en instancias muy grandes
- Sensibilidad a la configuración de parámetros en ciertas instancias

## Recomendaciones de Uso

1. **Para resultados rápidos de calidad razonable**: Usar 100 iteraciones con población de 30
   - Tiempo: < 0.1 segundos
   - Calidad: En torno al 25% sobre el óptimo para E-n22-k4

2. **Para resultados de alta calidad**: Usar 1000 iteraciones con población de 50
   - Tiempo: ~1.5 segundos
   - Calidad: En torno al 10% sobre el óptimo para E-n22-k4

3. **Para aplicaciones en tiempo real**: Usar entre 100-500 iteraciones con población de 30
   - Tiempo: 0.1-0.5 segundos
   - Calidad: Entre 15-25% sobre el óptimo para E-n22-k4

4. **Para resultados estadísticamente significativos**: Ejecutar el algoritmo al menos 10 veces con diferentes semillas para capturar la variabilidad inherente

## Ejemplo de Uso

```python
from algorithms.apo import APO
from problems.vrp import VRPProblem

# Cargar problema
problem = VRPProblem("data/vrp/E-n22-k4.vrp")

# Inicializar algoritmo
apo = APO(
    problem=problem,
    population_size=50,
    max_iterations=1000,
    seed=42
)

# Ejecutar optimización
best_solution = apo.execute()

# Obtener fitness y convergencia
fitness = best_solution.fitness()
convergence_curve = apo.get_convergence_curve()
```

## Referencias

- Chen, J., Xie, Q., & Zeng, J. (2024). *Artificial Protozoa Optimizer: A Novel Bio-inspired Algorithm for Global Optimization Problems*. Information Sciences, 642, 119-138. doi: 10.1016/j.ins.2023.12.017

- Para análisis comparativo con otros algoritmos, consulte: [Análisis Comparativo Exhaustivo](../../analysis/comparison.md)

---

*Última actualización: 10 de mayo de 2025*
