# Guía de Validación de Parámetros

Esta guía muestra cómo agregar validación de parámetros a los algoritmos v2.

## Pasos para Agregar Validación

### 1. Importar el Validador

```python
from algorithms.validators import ParameterValidator
```

### 2. Actualizar el Constructor

Agregar parámetros específicos del algoritmo con valores por defecto:

```python
def __init__(
    self,
    problem: AbstractProblem,
    population_size: int = 30,
    max_iterations: int = 100,
    seed: Optional[int] = None,
    # Parámetros específicos del algoritmo
    param1: float = 0.5,
    param2: int = 10
):
```

### 3. Validar Parámetros

Usar los métodos de `ParameterValidator`:

```python
# Después de llamar a super().__init__()

# Para probabilidades (0.0 - 1.0)
self.mutation_rate = ParameterValidator.validate_probability(
    mutation_rate, "mutation_rate"
)

# Para flotantes positivos con rango
self.alpha = ParameterValidator.validate_positive_float(
    alpha, "alpha", min_value=0.0, max_value=2.0
)

# Para enteros positivos
self.k_neighbors = ParameterValidator.validate_positive_integer(
    k_neighbors, "k_neighbors", min_value=1
)
```

## Ejemplos por Algoritmo

### AHA (Artificial Hummingbird Algorithm)

```python
def __init__(
    self,
    problem: AbstractProblem,
    population_size: int = 30,
    max_iterations: int = 100,
    seed: Optional[int] = None,
    migration_coeff: float = 2.0
):
    super().__init__(problem, population_size, max_iterations, seed)
    
    self.migration_coeff = ParameterValidator.validate_positive_float(
        migration_coeff, "migration_coeff", min_value=0.0
    )
```

### EWA (Earthworm Algorithm)

```python
def __init__(
    self,
    problem: AbstractProblem,
    population_size: int = 30,
    max_iterations: int = 100,
    seed: Optional[int] = None,
    similarity: float = 0.98,
    reproduction_rate: float = 0.9
):
    super().__init__(problem, population_size, max_iterations, seed)
    
    self.similarity = ParameterValidator.validate_probability(
        similarity, "similarity"
    )
    self.reproduction_rate = ParameterValidator.validate_probability(
        reproduction_rate, "reproduction_rate"
    )
```

### SMO (Starling Murmuration Optimizer)

```python
def __init__(
    self,
    problem: AbstractProblem,
    population_size: int = 30,
    max_iterations: int = 100,
    seed: Optional[int] = None,
    mu: float = 0.8,
    k: int = 5
):
    super().__init__(problem, population_size, max_iterations, seed)
    
    self.mu = ParameterValidator.validate_probability(mu, "mu")
    self.k = ParameterValidator.validate_positive_integer(
        k, "k", min_value=1
    )
```

### HOA (Hyena Optimization Algorithm)

```python
def __init__(
    self,
    problem: AbstractProblem,
    population_size: int = 30,
    max_iterations: int = 100,
    seed: Optional[int] = None,
    h: float = 5.0,
    beta: float = 1.5
):
    super().__init__(problem, population_size, max_iterations, seed)
    
    self.h = ParameterValidator.validate_positive_float(
        h, "h", min_value=0.0
    )
    self.beta = ParameterValidator.validate_positive_float(
        beta, "beta", min_value=0.0
    )
```

## Validación Completa

Para ver todos los algoritmos con validación implementada:

1. **WOA**: No requiere parámetros adicionales
2. **SMA**: Validado con parámetro `z`
3. **GTO**: Validado con parámetros `p` y `beta`
4. **MRFO**: No requiere parámetros adicionales
5. **EGTO**: Hereda validación de GTO

## Ejecutar Tests

Para verificar que la validación funciona correctamente:

```bash
# Tests específicos de validación
python -m pytest tests/test_validators.py -v

# Tests de un algoritmo específico
python -m pytest tests/test_sma_v2.py -v
```

## Mensajes de Error

Los mensajes de error son descriptivos:

```python
# Error: "mutation_rate debe ser <= 1.0, se recibió: 1.5"
# Error: "k_neighbors debe ser >= 1, se recibió: 0"
# Error: "alpha debe ser un número, se recibió: str"
```

## Advertencias

El sistema genera advertencias para valores poco comunes:

- `population_size < 10`: Advertencia de población muy pequeña
- `max_iterations < 10`: Advertencia de pocas iteraciones

## Extensión del Sistema

Para agregar nuevos tipos de validación:

1. Agregar método en `ParameterValidator`
2. Agregar caso en `validate_algorithm_specific_params`
3. Crear tests en `test_validators.py`