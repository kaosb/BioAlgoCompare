# Hippopotamus Optimization (HO)

## Descripción General

El Hippopotamus Optimization (HO) es un algoritmo metaheurístico novedoso, inspirado en la naturaleza, propuesto por Amiri et al. en 2024. El algoritmo modela matemáticamente los comportamientos sociales y de supervivencia de los hipopótamos, incluyendo su movimiento en el agua, sus estrategias de defensa contra depredadores y sus mecanismos de evasión. El HO destaca por su equilibrio entre las fases de exploración y explotación.

### Inspiración Biológica

El algoritmo simula tres comportamientos clave de los hipopótamos:
- **Fase de Posición**: Los hipopótamos ajustan su posición en el río, influenciados por la ubicación del líder del grupo y la mejor ubicación global encontrada por la manada.
- **Fase de Defensa**: Cuando se enfrentan a una amenaza, los hipopótamos forman grupos defensivos. Esta implementación modela este comportamiento mediante clustering jerárquico para agrupar soluciones similares y aplicar operadores de mejora local dentro de los clusters.
- **Fase de Evasión**: Para escapar de un peligro inminente, los hipopótamos realizan movimientos erráticos y rápidos. Esto se modela utilizando vuelos de Lévy para introducir perturbaciones significativas y escapar de óptimos locales.

## Implementación y Mejoras

**Fecha de última actualización:** 14 de julio de 2025

### Cambios Implementados

Esta implementación del algoritmo HO es particularmente avanzada y está adaptada para problemas de VRP complejos como el QC-DVRP (Quality and Cost Dynamic Vehicle Routing Problem).

1.  **Fases de Comportamiento Adaptativo**:
    -   El algoritmo transita entre las tres fases (posición, defensa, evasión) basándose en el progreso de la optimización y en la calidad de la solución actual (`fitness_ratio`).
    -   Los parámetros clave (`alpha`, `beta`, `gamma`) se actualizan dinámicamente en cada iteración para ajustar la intensidad de los operadores.

2.  **Operadores Específicos para VRP**:
    -   **Fase de Posición**: El movimiento hacia el líder y el mejor global se traduce en la aplicación del operador **2-opt** a las rutas decodificadas, mejorando la explotación local.
    -   **Fase de Defensa**: El clustering jerárquico se utiliza para identificar grupos de soluciones. Para rutas desbalanceadas (alto coeficiente de variación de tiempo), se aplica un operador de **swap de clientes** para mejorar el equilibrio de carga.
    -   **Fase de Evasión**: La perturbación de Lévy se aplica al vector de solución continua para una exploración amplia.

3.  **Integración con Imitation Learning (IL)**:
    -   La implementación incluye una opción (`use_il`) para cargar un modelo de aprendizaje por imitación pre-entrenado.
    -   Este modelo puede predecir los parámetros óptimos (`alpha`, `beta`, `gamma`) en cada iteración basándose en el estado actual del problema, en lugar de usar la actualización lineal estándar. Esto representa un enfoque de vanguardia para la parametrización de metaheurísticas.

## Pseudocódigo

```
Inicializar población de N hipopótamos aleatoriamente
Evaluar fitness y encontrar el mejor global (gbest)

Para t = 1 hasta T (iteraciones):
  # Actualizar parámetros (estándar o con IL)
  alpha, beta, gamma = actualizar_parametros(t, T, il_model)

  # Determinar fase
  fitness_ratio = gbest.fitness / promedio_fitness(población)
  Si fitness_ratio < theta:
    Fase = POSICIÓN
  Sino si t/T < 0.7:
    Fase = DEFENSA
  Sino:
    Fase = EVASIÓN

  Para cada hipopótamo i:
    Si Fase == POSICIÓN:
      líder = seleccionar_líder_aleatorio()
      movimiento = alpha*(líder.pos - pos_i) + beta*rand()*(gbest.pos - pos_i)
      pos_i += movimiento
      Aplicar 2-opt a las rutas decodificadas
    Si Fase == DEFENSA:
      Realizar clustering jerárquico
      Para rutas desbalanceadas:
        Aplicar swap de clientes para balancear carga
    Si Fase == EVASIÓN:
      perturbación = gamma * LevyFlight()
      pos_i += perturbación

    Sujetar posición a los límites del dominio
    Evaluar nuevo fitness y actualizar pbest y gbest

Retornar gbest
```

## Fortalezas y Limitaciones

### Fortalezas
-   Estructura novedosa con tres fases bien diferenciadas que equilibran exploración y explotación.
-   Adaptación de operadores específicos del dominio (2-opt, swap) dentro de las fases, lo que lo hace muy potente para VRP.
-   La fase de defensa con clustering es una técnica avanzada para la mejora de subconjuntos de la población.
-   La capacidad de integrar Imitation Learning lo sitúa en la frontera de la investigación en metaheurísticas.

### Limitaciones
-   Mayor complejidad de implementación en comparación con algoritmos más simples.
-   El rendimiento puede ser sensible a la correcta implementación de los operadores discretos y del clustering.
-   La versión con IL requiere un proceso de entrenamiento previo, que es costoso.

## Recomendaciones de Uso
-   **Sin IL**: Es un algoritmo potente por sí mismo. Asegurarse de que el problema implementa los métodos de decodificación y evaluación de rutas necesarios para los operadores.
-   **Con IL**: Para obtener el máximo rendimiento, se debe entrenar un modelo (`.pkl` o `.pth`) con datos de ejecuciones de alta calidad. El estado del problema debe ser cuidadosamente diseñado para proporcionar información relevante al modelo.
-   **Parámetros**: Los umbrales `theta` y el `0.7` para el cambio de fase son sensibles y pueden requerir ajuste según la naturaleza del problema de optimización.

## Ejemplo de Uso

```python
from algorithms.ho import HO
from problems.vrp import VRPProblem

# Cargar problema
problem = VRPProblem("data/vrp/P-n16-k8.vrp")

# Inicializar algoritmo (versión estándar)
ho_standard = HO(
    problem=problem,
    population_size=30,
    max_iterations=1000,
    seed=42
)
best_solution_std = ho_standard.execute()
print("Mejor fitness HO (estándar):", best_solution_std.fitness())

# Inicializar algoritmo (con Imitation Learning)
# Nota: Requiere un modelo pre-entrenado en 'models/ho_il_model.pkl'
ho_il = HO(
    problem=problem,
    population_size=30,
    max_iterations=1000,
    seed=42,
    use_il=True,
    il_model_path="models/ho_il_model.pkl" # o .pth
)
best_solution_il = ho_il.execute()
print("Mejor fitness HO (con IL):", best_solution_il.fitness())
```

## Referencias

- Amiri, M. H., Hashjin, N. M., Montazeri, M., Mirjalili, S., & Khodadadi, N. (2024). Hippopotamus optimization algorithm: a novel nature-inspired optimization algorithm. *Scientific Reports*, 14(1), 5032. doi: 10.1038/s41598-024-54909-3

- Para análisis comparativo con otros algoritmos, consulte: [Análisis Comparativo Exhaustivo](../../analysis/comparison.md)

---

*Última actualización: 14 de julio de 2025*
