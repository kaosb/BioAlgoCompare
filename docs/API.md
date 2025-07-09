# Documentación de API

## Arquitectura v2

La arquitectura v2 de BioAlgoCompare proporciona una base sólida y extensible para implementar algoritmos metaheurísticos.

### Componentes Principales

```
base_v2.py
├── MoveContext      # Contexto para movimiento de individuos
├── Individual       # Clase base para individuos
├── MetaheuristicAlgorithm  # Clase base para algoritmos
└── AbstractProblem  # Interfaz para problemas de optimización
```

## Clase MoveContext

Contiene toda la información necesaria para el movimiento de individuos.

```python
@dataclass
class MoveContext:
    iteration: int                    # Iteración actual
    max_iterations: int              # Máximo de iteraciones
    population: List[Individual]      # Población completa
    best_individual: Optional[Individual]  # Mejor individuo
    algorithm_params: Dict[str, Any]  # Parámetros específicos
```

### Métodos

```python
def get_param(self, key: str, default: Any = None) -> Any:
    """Obtiene un parámetro del algoritmo."""
    
def set_param(self, key: str, value: Any) -> None:
    """Establece un parámetro del algoritmo."""
```

## Clase Individual

Clase abstracta base para todos los individuos en algoritmos metaheurísticos.

### Atributos

- `problem`: Instancia del problema a resolver
- `position`: Posición/solución del individuo (numpy array)
- `_fitness`: Valor de fitness cacheado
- `_fitness_calculated`: Flag de cálculo de fitness

### Métodos Abstractos

```python
@abstractmethod
def initialize(self) -> None:
    """Inicializa la posición del individuo."""
    
@abstractmethod
def move(self, context: MoveContext) -> None:
    """Mueve el individuo según las reglas del algoritmo."""
```

### Métodos Implementados

```python
def fitness(self) -> float:
    """Calcula y cachea el fitness."""
    
def invalidate_fitness(self) -> None:
    """Invalida el fitness cacheado."""
    
def is_better_than(self, other: Individual) -> bool:
    """Compara con otro individuo (minimización por defecto)."""
    
def is_feasible(self) -> bool:
    """Verifica si la solución es factible."""
    
def copy_from(self, other: Individual) -> None:
    """Copia el estado de otro individuo."""
    
def clone(self) -> Individual:
    """Crea una copia profunda del individuo."""
```

## Clase MetaheuristicAlgorithm

Clase base genérica para todos los algoritmos metaheurísticos.

### Constructor

```python
def __init__(
    self,
    problem: AbstractProblem,
    population_size: int = 30,
    max_iterations: int = 100,
    seed: Optional[int] = None,
):
    """
    Args:
        problem: Problema a optimizar
        population_size: Tamaño de población (validado >= 2)
        max_iterations: Número de iteraciones (validado >= 1)
        seed: Semilla para reproducibilidad
    """
```

### Métodos Abstractos

```python
@abstractmethod
def _create_individual(self) -> T:
    """Factory method para crear individuos."""
    
@abstractmethod
def _create_move_context(self) -> MoveContext:
    """Crea el contexto para la iteración actual."""
```

### Métodos Principales

```python
def execute(self) -> T:
    """Ejecuta el algoritmo completo."""
    
def initialize_population(self) -> None:
    """Inicializa la población con individuos aleatorios."""
    
def update_population(self) -> None:
    """Actualiza la población para una iteración."""
    
def update_best_solution(self) -> None:
    """Actualiza la mejor solución encontrada."""
```

### Métodos Opcionales

```python
def _should_sort_population(self) -> bool:
    """Determina si ordenar la población (default: False)."""
    
def _on_iteration_complete(self) -> None:
    """Callback después de cada iteración."""
```

### Métodos de Información

```python
def get_execution_time(self) -> float:
    """Tiempo total de ejecución en segundos."""
    
def get_convergence_curve(self) -> List[float]:
    """Curva de convergencia del algoritmo."""
    
def summary(self) -> Dict[str, Any]:
    """Resumen completo de la ejecución."""
```

## Implementar un Nuevo Algoritmo

### 1. Crear la Clase Individual

```python
from algorithms.base_v2 import Individual, MoveContext
import numpy as np

class MyIndividual(Individual):
    def __init__(self, problem):
        super().__init__(problem)
        self.dimension = problem.get_dimension()
        # Atributos específicos del algoritmo
        self.velocity = None
        
    def initialize(self):
        """Inicialización aleatoria."""
        self.position = np.random.uniform(0, 1, self.dimension)
        self.velocity = np.zeros(self.dimension)
        self.invalidate_fitness()
        
    def move(self, context: MoveContext):
        """Lógica de movimiento del algoritmo."""
        # Obtener parámetros
        w = context.get_param("inertia", 0.7)
        c1 = context.get_param("c1", 2.0)
        
        # Actualizar velocidad y posición
        best = context.best_individual
        r1, r2 = np.random.random(2)
        
        self.velocity = (w * self.velocity + 
                        c1 * r1 * (best.position - self.position))
        self.position += self.velocity
        
        # Aplicar límites
        self.position = np.clip(self.position, 0, 1)
```

### 2. Crear la Clase del Algoritmo

```python
from algorithms.base_v2 import MetaheuristicAlgorithm
from algorithms.validators import ParameterValidator

class MyAlgorithm(MetaheuristicAlgorithm):
    def __init__(
        self,
        problem,
        population_size=30,
        max_iterations=100,
        seed=None,
        inertia=0.7,
        c1=2.0
    ):
        super().__init__(problem, population_size, max_iterations, seed)
        
        # Validar parámetros específicos
        self.inertia = ParameterValidator.validate_positive_float(
            inertia, "inertia", min_value=0.0, max_value=1.0
        )
        self.c1 = ParameterValidator.validate_positive_float(
            c1, "c1", min_value=0.0
        )
        
    def _create_individual(self):
        """Factory method."""
        return MyIndividual(self.problem)
        
    def _create_move_context(self):
        """Contexto con parámetros del algoritmo."""
        context = MoveContext(
            iteration=self.iteration,
            max_iterations=self.max_iterations,
            population=self.population,
            best_individual=self.best_solution
        )
        
        # Agregar parámetros específicos
        context.set_param("inertia", self.inertia)
        context.set_param("c1", self.c1)
        
        return context
```

## Sistema de Validación

### Validadores Disponibles

```python
# Entero positivo
value = ParameterValidator.validate_positive_integer(
    value, "param_name", min_value=1
)

# Flotante positivo con rango
value = ParameterValidator.validate_positive_float(
    value, "param_name", min_value=0.0, max_value=2.0
)

# Probabilidad [0, 1]
value = ParameterValidator.validate_probability(value, "param_name")

# Entero opcional
value = ParameterValidator.validate_optional_integer(
    value, "param_name", default=None, min_value=0
)
```

### Decorador de Validación

```python
from algorithms.validators import with_validation

class MyAlgorithm:
    @with_validation
    def __init__(self, problem, population_size=30, **kwargs):
        # La validación se aplica automáticamente
        pass
```

## Factories

### IndividualFactory

```python
from algorithms.factories import IndividualFactory

# Crear población ordenada
population = IndividualFactory.create_sorted_population(
    individual_class=MyIndividual,
    problem=problem,
    size=50
)

# Crear población con diversidad
population = IndividualFactory.create_diverse_population(
    individual_class=MyIndividual,
    problem=problem,
    size=50,
    diversity_threshold=0.1
)
```

## Problemas

### Interfaz AbstractProblem

```python
class AbstractProblem(ABC):
    @property
    @abstractmethod
    def dimension(self) -> int:
        """Dimensión del problema."""
        
    @property
    @abstractmethod
    def lower_bounds(self) -> np.ndarray:
        """Límites inferiores."""
        
    @property
    @abstractmethod
    def upper_bounds(self) -> np.ndarray:
        """Límites superiores."""
        
    @abstractmethod
    def evaluate(self, solution: np.ndarray) -> float:
        """Evalúa una solución."""
```

### VRPProblem

```python
from problems.vrp import VRPProblem

# Cargar problema desde archivo
problem = VRPProblem("data/vrp/P-n16-k8.vrp")

# Propiedades
dimension = problem.get_dimension()
capacity = problem.capacity
depot = problem.depot_index

# Evaluar solución
fitness = problem.evaluate(solution_array)
```

## Uso Completo

```python
# 1. Importar
from problems.vrp import VRPProblem
from algorithms.my_algorithm import MyAlgorithm

# 2. Crear problema
problem = VRPProblem("data/vrp/P-n16-k8.vrp")

# 3. Crear algoritmo con validación
algorithm = MyAlgorithm(
    problem=problem,
    population_size=50,
    max_iterations=200,
    seed=42,
    inertia=0.8,
    c1=1.5
)

# 4. Ejecutar
best_solution = algorithm.execute()

# 5. Obtener resultados
print(f"Mejor fitness: {best_solution.fitness()}")
print(f"Tiempo: {algorithm.get_execution_time():.2f}s")
print(f"Convergencia: {algorithm.get_convergence_curve()}")

# 6. Resumen completo
summary = algorithm.summary()
```

## Mejores Prácticas

1. **Siempre validar parámetros** en el constructor
2. **Usar MoveContext** para pasar información
3. **Invalidar fitness** después de cambiar posición
4. **Implementar clone()** si hay atributos especiales
5. **Documentar** comportamiento específico del algoritmo
6. **Escribir tests** para nuevos algoritmos

## Ejemplo: Agregar PSO

```python
# pso_v2.py
from algorithms.base_v2 import Individual, MetaheuristicAlgorithm, MoveContext
from algorithms.validators import ParameterValidator
import numpy as np

class Particle(Individual):
    def __init__(self, problem):
        super().__init__(problem)
        self.dimension = problem.get_dimension()
        self.velocity = None
        self.personal_best = None
        self.personal_best_fitness = float('inf')
        
    def initialize(self):
        self.position = np.random.uniform(0, 1, self.dimension)
        self.velocity = np.random.uniform(-0.1, 0.1, self.dimension)
        self.personal_best = self.position.copy()
        self.invalidate_fitness()
        
    def move(self, context: MoveContext):
        # Actualizar personal best
        if self.fitness() < self.personal_best_fitness:
            self.personal_best = self.position.copy()
            self.personal_best_fitness = self.fitness()
            
        # Parámetros
        w = context.get_param("w")
        c1 = context.get_param("c1")
        c2 = context.get_param("c2")
        
        # Actualizar velocidad
        r1, r2 = np.random.random(2)
        gbest = context.best_individual.position
        
        self.velocity = (w * self.velocity +
                        c1 * r1 * (self.personal_best - self.position) +
                        c2 * r2 * (gbest - self.position))
                        
        # Actualizar posición
        self.position += self.velocity
        self.position = np.clip(self.position, 0, 1)

class PSO(MetaheuristicAlgorithm):
    def __init__(self, problem, population_size=30, max_iterations=100,
                 seed=None, w=0.7, c1=2.0, c2=2.0):
        super().__init__(problem, population_size, max_iterations, seed)
        
        self.w = ParameterValidator.validate_positive_float(
            w, "w", min_value=0.0, max_value=1.0
        )
        self.c1 = ParameterValidator.validate_positive_float(
            c1, "c1", min_value=0.0
        )
        self.c2 = ParameterValidator.validate_positive_float(
            c2, "c2", min_value=0.0
        )
        
    def _create_individual(self):
        return Particle(self.problem)
        
    def _create_move_context(self):
        context = super()._create_move_context()
        context.set_param("w", self.w)
        context.set_param("c1", self.c1)
        context.set_param("c2", self.c2)
        return context
```