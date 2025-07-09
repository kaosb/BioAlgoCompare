# Plan de Implementación - Jerarquía de Problemas

## Análisis de la Situación Actual

### AbstractProblem Actual
- Asume representación continua (np.ndarray)
- Métodos orientados a límites continuos (lower/upper bounds)
- No soporta problemas discretos nativamente
- VRPProblem usa adaptadores para convertir representación continua a discreta

## Diseño de la Nueva Jerarquía

### 1. Refactorización de Base

```python
# problems/base.py

from abc import ABC, abstractmethod
from typing import Any, TypeVar, Generic, Optional, Union
import numpy as np

T = TypeVar('T')  # Tipo de solución

class AbstractProblem(ABC, Generic[T]):
    """Base para todos los problemas de optimización."""
    
    def __init__(self, name: str):
        self.name = name
        self._best_known: Optional[float] = None
    
    @property
    @abstractmethod
    def dimension(self) -> int:
        """Dimensión del problema."""
        pass
    
    @abstractmethod
    def evaluate(self, solution: T) -> float:
        """Evalúa una solución."""
        pass
    
    @abstractmethod
    def is_feasible(self, solution: T) -> bool:
        """Verifica si una solución es factible."""
        pass
    
    @abstractmethod
    def random_solution(self) -> T:
        """Genera una solución aleatoria factible."""
        pass
    
    @property
    def best_known_value(self) -> Optional[float]:
        """Mejor valor conocido (para benchmarking)."""
        return self._best_known
```

### 2. Problemas Continuos

```python
# problems/continuous/base.py

class ContinuousOptimizationProblem(AbstractProblem[np.ndarray]):
    """Base para problemas de optimización continua."""
    
    def __init__(self, name: str, dimension: int):
        super().__init__(name)
        self._dimension = dimension
    
    @property
    @abstractmethod
    def lower_bounds(self) -> np.ndarray:
        """Límites inferiores."""
        pass
    
    @property
    @abstractmethod
    def upper_bounds(self) -> np.ndarray:
        """Límites superiores."""
        pass
    
    @property
    def dimension(self) -> int:
        return self._dimension
    
    def is_feasible(self, solution: np.ndarray) -> bool:
        """Verifica límites."""
        if len(solution) != self.dimension:
            return False
        return np.all(solution >= self.lower_bounds) and \
               np.all(solution <= self.upper_bounds)
    
    def repair(self, solution: np.ndarray) -> np.ndarray:
        """Repara solución por clipping."""
        return np.clip(solution, self.lower_bounds, self.upper_bounds)
    
    def random_solution(self) -> np.ndarray:
        """Solución aleatoria uniforme."""
        return np.random.uniform(
            self.lower_bounds, 
            self.upper_bounds
        )
```

### 3. Problemas Discretos

```python
# problems/discrete/base.py

from typing import List, Tuple

class DiscreteOptimizationProblem(AbstractProblem[List[int]]):
    """Base para problemas de optimización discreta."""
    
    @abstractmethod
    def encode_continuous(self, continuous: np.ndarray) -> List[int]:
        """Convierte representación continua a discreta."""
        pass
    
    @abstractmethod
    def decode_to_continuous(self, discrete: List[int]) -> np.ndarray:
        """Convierte representación discreta a continua."""
        pass
    
    @property
    @abstractmethod
    def search_space_size(self) -> int:
        """Tamaño del espacio de búsqueda."""
        pass
```

## Implementación por Fases

### Fase 1: Infraestructura Base (3 días)

#### Día 1: Refactorización
1. Crear nueva estructura de directorios
2. Implementar AbstractProblem genérico
3. Implementar ContinuousOptimizationProblem
4. Implementar DiscreteOptimizationProblem

#### Día 2: Adaptadores
1. Crear ContinuousAdapter para algoritmos existentes
2. Crear DiscreteAdapter para problemas discretos
3. Sistema de encoding/decoding genérico

#### Día 3: Migración VRP
1. Adaptar VRPProblem a nueva jerarquía
2. Crear RoutingProblem base
3. Mantener compatibilidad hacia atrás

### Fase 2: Problemas Continuos (2 días)

#### Día 4: Benchmarks Básicos
```python
# problems/continuous/unconstrained/sphere.py
class SphereProblem(ContinuousOptimizationProblem):
    """f(x) = sum(x_i^2)"""
    
    def __init__(self, dimension: int = 30):
        super().__init__(f"Sphere-{dimension}D", dimension)
        self._lower_bounds = np.full(dimension, -100.0)
        self._upper_bounds = np.full(dimension, 100.0)
        self._best_known = 0.0
    
    def evaluate(self, solution: np.ndarray) -> float:
        return np.sum(solution ** 2)

# problems/continuous/unconstrained/rastrigin.py
class RastriginProblem(ContinuousOptimizationProblem):
    """f(x) = 10n + sum(x_i^2 - 10*cos(2*pi*x_i))"""
    
    def evaluate(self, solution: np.ndarray) -> float:
        n = len(solution)
        return 10 * n + np.sum(
            solution**2 - 10 * np.cos(2 * np.pi * solution)
        )

# problems/continuous/unconstrained/ackley.py
class AckleyProblem(ContinuousOptimizationProblem):
    """Ackley function - multimodal with global minimum at origin"""
    
    def evaluate(self, solution: np.ndarray) -> float:
        n = len(solution)
        sum1 = np.sum(solution**2)
        sum2 = np.sum(np.cos(2 * np.pi * solution))
        return -20 * np.exp(-0.2 * np.sqrt(sum1/n)) - \
               np.exp(sum2/n) + 20 + np.e
```

#### Día 5: Suite de Benchmarks
1. Rosenbrock, Griewank, Schwefel
2. Sistema de registro de benchmarks
3. Tests unitarios

### Fase 3: Problemas Discretos (3 días)

#### Día 6: TSP Implementation
```python
# problems/discrete/routing/tsp.py
class TSPProblem(DiscreteOptimizationProblem):
    """Traveling Salesman Problem."""
    
    def __init__(self, distance_matrix: np.ndarray):
        super().__init__(f"TSP-{len(distance_matrix)}")
        self.distance_matrix = distance_matrix
        self.n_cities = len(distance_matrix)
        self._dimension = self.n_cities
    
    def evaluate(self, tour: List[int]) -> float:
        """Calcula longitud del tour."""
        total = 0.0
        for i in range(len(tour)):
            from_city = tour[i]
            to_city = tour[(i + 1) % len(tour)]
            total += self.distance_matrix[from_city, to_city]
        return total
    
    def encode_continuous(self, continuous: np.ndarray) -> List[int]:
        """Random keys encoding."""
        indices = np.argsort(continuous)
        return indices.tolist()
    
    @classmethod
    def from_tsplib(cls, filepath: str) -> 'TSPProblem':
        """Carga desde archivo TSPLIB."""
        # Parser implementation
        pass
```

#### Día 7: Adaptadores Avanzados
1. PermutationAdapter para TSP
2. BinaryAdapter para problemas binarios
3. IntegerAdapter para variables enteras

#### Día 8: Job Shop Problem
```python
# problems/discrete/scheduling/job_shop.py
class JobShopProblem(DiscreteOptimizationProblem):
    """Job Shop Scheduling Problem."""
    
    def __init__(self, jobs: List[List[Tuple[int, int]]]):
        """
        jobs: Lista de trabajos, cada uno con operaciones (máquina, tiempo)
        """
        self.jobs = jobs
        self.n_jobs = len(jobs)
        self.n_machines = max(
            machine for job in jobs 
            for machine, _ in job
        ) + 1
    
    def evaluate(self, schedule: List[int]) -> float:
        """Calcula makespan."""
        # Decodificar y simular schedule
        return makespan
```

### Fase 4: Integración (2 días)

#### Día 9: CLI Integration
1. Actualizar bioalgocompare para soportar nuevos problemas
2. Comando para listar problemas disponibles
3. Auto-detección de tipo de problema

#### Día 10: Testing y Documentación
1. Suite completa de tests
2. Documentación de API
3. Ejemplos de uso

## Estructura Final de Archivos

```
problems/
├── __init__.py
├── base.py                    # AbstractProblem genérico
├── adapters.py               # Adaptadores problema-algoritmo
├── registry.py               # Registro de problemas disponibles
├── continuous/
│   ├── __init__.py
│   ├── base.py              # ContinuousOptimizationProblem
│   ├── unconstrained/
│   │   ├── __init__.py
│   │   ├── sphere.py
│   │   ├── rastrigin.py
│   │   ├── ackley.py
│   │   ├── rosenbrock.py
│   │   ├── griewank.py
│   │   └── schwefel.py
│   └── constrained/
│       ├── __init__.py
│       └── g_functions.py    # G01-G24 benchmarks
├── discrete/
│   ├── __init__.py
│   ├── base.py              # DiscreteOptimizationProblem
│   ├── routing/
│   │   ├── __init__.py
│   │   ├── vrp.py          # Migrado
│   │   ├── tsp.py
│   │   └── cvrptw.py
│   ├── scheduling/
│   │   ├── __init__.py
│   │   ├── job_shop.py
│   │   └── flow_shop.py
│   └── combinatorial/
│       ├── __init__.py
│       ├── knapsack.py
│       └── bin_packing.py
└── utils/
    ├── __init__.py
    ├── tsplib_parser.py
    ├── orlib_parser.py
    └── visualization.py
```

## Ejemplo de Uso Final

```python
# Problema continuo
from problems.continuous.unconstrained import SphereProblem
from algorithms.woa_v2 import WOAV2

problem = SphereProblem(dimension=30)
algorithm = WOAV2(problem, population_size=50)
best = algorithm.execute()
print(f"Best: {best.fitness()}")

# Problema discreto con adaptador
from problems.discrete.routing import TSPProblem
from problems.adapters import PermutationAdapter
from algorithms.sma_v2 import SMAV2

tsp = TSPProblem.from_tsplib("data/tsp/berlin52.tsp")
adapted_problem = PermutationAdapter(tsp)
algorithm = SMAV2(adapted_problem, population_size=50)
best = algorithm.execute()
tour = tsp.encode_continuous(best.position)
print(f"Best tour length: {tsp.evaluate(tour)}")
```

## Consideraciones de Diseño

### 1. Compatibilidad
- Mantener VRPProblem funcionando sin cambios
- Adaptadores transparentes para algoritmos existentes
- Deprecation warnings para métodos obsoletos

### 2. Extensibilidad
- Fácil agregar nuevos tipos de problemas
- Sistema de plugins para problemas externos
- Registro automático de problemas

### 3. Performance
- Lazy loading de problemas
- Caching de evaluaciones costosas
- Paralelización de evaluaciones batch

### 4. Usabilidad
- Auto-detección de tipo de problema
- Conversión automática de representaciones
- Mensajes de error claros

## Métricas de Éxito

1. **Cobertura**: Al menos 5 tipos de problemas diferentes
2. **Compatibilidad**: 100% tests existentes pasando
3. **Performance**: Sin degradación en VRP
4. **Documentación**: Guía completa para cada tipo
5. **Tests**: >90% cobertura en nuevo código

## Riesgos y Mitigación

| Riesgo | Impacto | Probabilidad | Mitigación |
|--------|---------|--------------|------------|
| Breaking changes en VRP | Alto | Baja | Tests exhaustivos, adaptador transparente |
| Complejidad de adaptadores | Medio | Alta | Diseño simple inicial, iterativo |
| Performance en conversiones | Medio | Media | Caching, conversión lazy |
| Confusión de usuarios | Bajo | Media | Documentación clara, ejemplos |