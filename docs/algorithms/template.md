# [Nombre del Algoritmo] ([Acrónimo])

## Descripción General

[Breve descripción del algoritmo, su propósito y origen]

### Inspiración Biológica

[Descripción de los fenómenos naturales o comportamientos biológicos que inspiran el algoritmo]
- **[Comportamiento 1]**: [Descripción]
- **[Comportamiento 2]**: [Descripción]
- **[Comportamiento 3]**: [Descripción]

## Implementación y Mejoras

**Fecha de última actualización:** [Fecha]

### Cambios Implementados

1. **[Área de mejora 1]**
   - [Detalle de implementación 1]
   - [Detalle de implementación 2]
   - [Detalle de implementación 3]

2. **[Área de mejora 2]**
   - [Detalle de implementación 1]
   - [Detalle de implementación 2]

3. **[Área de mejora 3]**
   - [Detalle de implementación 1]
   - [Detalle de implementación 2]

## Pseudocódigo

```
[Pseudocódigo que describe el algoritmo]
Inicializar población
Evaluar fitness y seleccionar mejor solución
Para t = 1 hasta T:
  [Operaciones específicas del algoritmo]
  Actualizar mejor solución
Retornar mejor solución
```

## Análisis de Rendimiento

### Resultados con Diferentes Iteraciones (Instancia [Nombre])

| Iteraciones | Fitness Mínimo | Fitness Medio | Desviación Estándar | Tiempo Medio (s) | Gap al Óptimo |
|-------------|----------------|---------------|---------------------|------------------|--------------|
| 10          | [valor]        | [valor]       | [valor]             | [valor]          | [valor]      |
| 100         | [valor]        | [valor]       | [valor]             | [valor]          | [valor]      |
| 1000        | [valor]        | [valor]       | [valor]             | [valor]          | [valor]      |
| 10000       | [valor]        | [valor]       | [valor]             | [valor]          | [valor]      |

### Efecto del Tamaño de Población ([número] Iteraciones)

| Población | Fitness Mínimo | Fitness Medio | Desviación Estándar | Tiempo (s) | Gap al Óptimo |
|-----------|----------------|---------------|---------------------|------------|---------------|
| 30        | [valor]        | [valor]       | [valor]             | [valor]    | [valor]       |
| 50        | [valor]        | [valor]       | [valor]             | [valor]    | [valor]       |

### Desempeño por Tipo de Instancia ([número] Iteraciones)

| Instancia  | Fitness Mínimo | Óptimo | Gap     | Tiempo (s) |
|------------|----------------|--------|---------|------------|
| [Instancia 1] | [valor]     | [valor]| [valor] | [valor]    |
| [Instancia 2] | [valor]     | [valor]| [valor] | [valor]    |

## Características de Convergencia

- **Patrón de Convergencia**: [Descripción]
- **Reducción de Variabilidad**: [Descripción]
- **Comportamiento en Múltiples Instancias**: [Descripción]

## Fortalezas y Limitaciones

### Fortalezas
- [Fortaleza 1]
- [Fortaleza 2]
- [Fortaleza 3]
- [Fortaleza 4]

### Limitaciones
- [Limitación 1]
- [Limitación 2]
- [Limitación 3]

## Recomendaciones de Uso

1. **Para resultados rápidos de calidad razonable**: Usar [número] iteraciones con población de [número]
   - Tiempo: [rango]
   - Calidad: [descripción]

2. **Para resultados de alta calidad**: Usar [número] iteraciones con población de [número]
   - Tiempo: [rango]
   - Calidad: [descripción]

3. **Para aplicaciones en tiempo real**: Usar entre [rango] iteraciones
   - Tiempo: [rango]
   - Calidad: [descripción]

4. **Para resultados estadísticamente significativos**: [Recomendación]

## Ejemplo de Uso

```python
from algorithms.[acrónimo] import [ACRÓNIMO]
from problems.vrp import VRPProblem

# Cargar problema
problem = VRPProblem("data/vrp/[instancia].vrp")

# Inicializar algoritmo
algoritmo = [ACRÓNIMO](
    problem=problem,
    population_size=30,
    max_iterations=1000,
    seed=42
)

# Ejecutar optimización
best_solution = algoritmo.execute()

# Obtener fitness y convergencia
fitness = best_solution.fitness()
convergence_curve = algoritmo.get_convergence_curve()
```

## Referencias

- [Autor], [Iniciales]. ([Año]). *[Título del Paper]*. [Revista], [Volumen]([Número]), [Páginas]. doi: [DOI]

- Para análisis comparativo con otros algoritmos, consulte: [Análisis Comparativo Exhaustivo](../../analysis/comparison.md)

---

*Última actualización: [Fecha]*
