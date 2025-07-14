# Genetic Algorithm (GA)

## Descripción General

El Algoritmo Genético (GA) es una de las metaheurísticas evolutivas más fundamentales y ampliamente utilizadas, introducida formalmente por John H. Holland. Se inspira en el proceso de selección natural de Charles Darwin, donde los individuos más aptos son seleccionados para reproducirse y transmitir sus genes a la siguiente generación. Los GAs son particularmente efectivos para problemas de búsqueda y optimización complejos.

### Inspiración Biológica

El GA se basa en conceptos clave de la genética y la evolución:
- **Población de Cromosomas**: Un conjunto de soluciones candidatas (individuos).
- **Función de Fitness**: Una medida que cuantifica la calidad o aptitud de cada solución.
- **Selección**: Proceso que favorece a los individuos más aptos para ser "padres".
- **Crossover (Recombinación)**: Combinación del material genético de dos padres para crear descendencia.
- **Mutación**: Alteraciones aleatorias en el material genético para introducir nueva diversidad.

## Implementación y Mejoras

**Fecha de última actualización:** 14 de julio de 2025

### Cambios Implementados

Esta implementación es una versión canónica de un Algoritmo Genético adaptado para problemas de optimización continua (y por extensión, VRP a través de decodificación).

1.  **Representación de Individuos**:
    -   Cada individuo (`Chromosome`) tiene una `position` (un vector de números reales entre 0 y 1) que representa una solución codificada.
    -   La decodificación de esta representación a una solución de VRP (rutas) es manejada por el objeto `problem`.

2.  **Selección por Torneo**:
    -   Se implementa `tournament_selection`, un método robusto que selecciona a un número de individuos al azar y elige al mejor de ese subgrupo como padre. Esto reduce la presión selectiva en comparación con la selección del mejor absoluto.

3.  **Operadores Genéticos para Permutaciones**:
    -   **Crossover de Orden (Order Crossover - OX)**: Se implementa el método `crossover`. Este operador es ideal para representaciones basadas en permutaciones (como las que subyacen al VRP), ya que preserva el orden relativo de los "genes" (clientes) de los padres.
    -   **Mutación por Intercambio (Swap Mutation)**: El método `mutate` intercambia dos genes (posiciones en el vector) al azar. Es un operador simple y efectivo para mantener la diversidad genética.

4.  **Elitismo**:
    -   Se preserva un número configurable de los mejores individuos (`elitism_size`) de una generación a la siguiente sin modificarlos, asegurando que la mejor solución encontrada nunca se pierda.

## Pseudocódigo

```
Inicializar población de N cromosomas aleatoriamente
Evaluar el fitness de cada cromosoma
Para g = 1 hasta G (generaciones):
  Crear nueva población vacía
  # Elitismo
  Añadir los k mejores cromosomas de la población actual a la nueva población

  Mientras la nueva población no esté llena:
    # Selección
    Padre1 = SelecciónPorTorneo(población)
    Padre2 = SelecciónPorTorneo(población)

    # Crossover
    Si rand() < tasa_crossover:
      Hijo1, Hijo2 = Crossover(Padre1, Padre2)
    Sino:
      Hijo1, Hijo2 = Padre1, Padre2

    # Mutación
    Mutar(Hijo1, tasa_mutación)
    Mutar(Hijo2, tasa_mutación)

    Añadir Hijo1 e Hijo2 a la nueva población

  Reemplazar la población antigua por la nueva
  Evaluar fitness de la nueva población
  Actualizar mejor solución global
Retornar mejor solución global
```

## Fortalezas y Limitaciones

### Fortalezas
-   Robusto y versátil, aplicable a una amplia gama de problemas.
-   Excelente para la exploración global del espacio de soluciones.
-   El paralelismo inherente permite implementaciones eficientes en hardware moderno.
-   Menos propenso a quedarse atascado en óptimos locales en comparación con los algoritmos de búsqueda local.

### Limitaciones
-   La convergencia puede ser lenta, especialmente sin operadores bien ajustados.
-   El rendimiento es muy sensible a la elección de los parámetros (tamaño de población, tasas de crossover/mutación).
-   Para problemas de VRP, la representación continua requiere una decodificación eficiente, que puede ser un cuello de botella.
-   Puede tener dificultades con el ajuste fino de la solución en las etapas finales de la búsqueda.

## Recomendaciones de Uso
-   **Ajuste de Parámetros**: Es crucial realizar un ajuste de los parámetros. Valores típicos son: `population_size` (50-100), `crossover_rate` (0.8-0.95), `mutation_rate` (0.01-0.1).
-   **Hibridación**: Para problemas complejos como el VRP, los GAs a menudo se hibridan con algoritmos de búsqueda local (convirtiéndose en Algoritmos Meméticos) para mejorar la explotación y el ajuste fino de las soluciones.
-   **Representación**: Para VRP, considerar representaciones directas de rutas en lugar de continuas si el rendimiento de la decodificación es un problema.

## Ejemplo de Uso

```python
from algorithms.ga import GA
from problems.vrp import VRPProblem

# Cargar problema
problem = VRPProblem("data/vrp/P-n16-k8.vrp")

# Inicializar algoritmo
ga = GA(
    problem=problem,
    population_size=50,
    max_iterations=1000,
    crossover_rate=0.8,
    mutation_rate=0.1,
    tournament_size=3,
    elitism_size=2,
    seed=42
)

# Ejecutar optimización
best_solution, best_fitness, convergence = ga.execute()

# Obtener fitness y convergencia
print("Mejor fitness GA:", best_fitness)
```

## Referencias

- Holland, J. H. (1975). *Adaptation in Natural and Artificial Systems*. University of Michigan Press.

- Para análisis comparativo con otros algoritmos, consulte: [Análisis Comparativo Exhaustivo](../../analysis/comparison.md)

---

*Última actualización: 14 de julio de 2025*
