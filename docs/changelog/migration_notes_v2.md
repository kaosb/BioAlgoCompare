# Notas de Migración a Arquitectura v2

## Algoritmos Migrados

### 1. SHO (Spotted Hyena Optimization)
- **Archivo**: `algorithms/sho_v2.py`
- **Estado**: ✅ Completado
- **Cambios principales**:
  - Usa MoveContext para pasar parámetros
  - Implementa initialize() en Individual
  - Implementa _create_move_context() en Algorithm

### 2. HHO (Harris Hawks Optimization)
- **Archivo**: `algorithms/hho_v2.py`
- **Estado**: ✅ Completado
- **Cambios principales**:
  - Migrado de Individual.move() con múltiples parámetros a MoveContext
  - Añadido método initialize() para inicialización de posición
  - Implementado _create_move_context() para crear contexto de iteración
  - Cambio de get_summary() a summary()
  - Usa clone() en lugar de copy() personalizado
  - Pruebas completas en `tests/test_hho_v2_migration.py`

### 3. FOA (Fossa Optimization Algorithm)
- **Archivo**: `algorithms/foa_v2.py`
- **Estado**: ✅ Completado
- **Cambios principales**:
  - Migrado de move() con (population, iteration, max_iterations) a MoveContext
  - Implementado initialize() para inicialización de posición
  - Implementado _create_move_context() básico
  - Implementado _should_sort_population() retornando True (FOA necesita población ordenada)
  - Mantiene las fases de exploración/explotación basadas en iteración
  - Pruebas completas en `tests/test_foa_v2_migration.py`

## Patrón de Migración

Para migrar un algoritmo a v2:

1. **Clase Individual**:
   ```python
   class AlgorithmIndividualV2(Individual):
       def __init__(self, problem: AbstractProblem):
           super().__init__(problem)
           # Agregar atributos específicos si necesario
           
       def initialize(self) -> None:
           """Inicializar posición aleatoria"""
           self.position = np.random.uniform(0, 1, self.problem.get_dimension())
           self.invalidate_fitness()
           
       def move(self, context: MoveContext) -> None:
           """Mover usando contexto en lugar de parámetros individuales"""
           # Extraer parámetros del contexto
           best = context.best_individual
           iteration = context.iteration
           max_iterations = context.max_iterations
           # ... lógica de movimiento
   ```

2. **Clase Algorithm**:
   ```python
   class AlgorithmV2(MetaheuristicAlgorithm):
       def _create_individual(self) -> Individual:
           return AlgorithmIndividualV2(self.problem)
           
       def _create_move_context(self) -> MoveContext:
           return MoveContext(
               iteration=len(self.convergence_curve),
               max_iterations=self.max_iterations,
               population=self.population,
               best_individual=self.best_solution,
               algorithm_params={}  # Parámetros específicos del algoritmo
           )
   ```

3. **Consideraciones importantes**:
   - La curva de convergencia v2 tiene `max_iterations + 1` elementos (incluye valor inicial)
   - Usar `invalidate_fitness()` después de modificar posición
   - No es necesario invalidar fitness manualmente en update_population si se usa la implementación base
   - Cambiar `get_summary()` por `summary()` y llamar a `super().summary()` primero



## Beneficios de la Nueva Arquitectura

1. **Consistencia**: Todos los algoritmos usan la misma interfaz
2. **Mantenibilidad**: Menos duplicación de código
3. **Extensibilidad**: Fácil agregar nuevos parámetros vía MoveContext
4. **Testabilidad**: Estructura más clara facilita las pruebas
5. **Reproducibilidad**: Mejor manejo de semillas aleatorias