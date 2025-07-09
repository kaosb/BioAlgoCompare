# Plan de Implementación de Validación por Algoritmo

## Análisis Detallado de Parámetros

### Grupo 1: Sin Parámetros Adicionales
Estos algoritmos no requieren validación adicional más allá de los parámetros estándar.

- **OPA** (Orca Predation Algorithm)
- **HOA** (Hyena Optimization Algorithm)  
- **SHO** (Spotted Hyena Optimizer)
- **FOA** (Fruit Fly Optimization Algorithm)
- **HHO** (Harris Hawks Optimization)

**Acción**: Verificar que no tienen parámetros ocultos y documentar su comportamiento dinámico.

### Grupo 2: Un Parámetro Simple
Algoritmos con un solo parámetro adicional.

#### MRFO (Manta Ray Foraging Optimization)
```python
def __init__(self, ..., spiral_factor: float = 2.0):
    # Validación
    self.spiral_factor = ParameterValidator.validate_positive_float(
        spiral_factor, "spiral_factor", min_value=1.0, max_value=3.0
    )
```
**Nota**: Considerar exponer `somersault_prob` (actualmente hardcodeado en 0.3)

#### AHA (Artificial Hummingbird Algorithm)
```python
def __init__(self, ..., step_size: float = 0.1):
    # Validación
    self.step_size = ParameterValidator.validate_positive_float(
        step_size, "step_size", min_value=0.01, max_value=0.5
    )
```

#### FGO (Flamingo Optimization Algorithm)
```python
def __init__(self, ..., MPb_ratio: float = 0.1):
    # Validación
    self.MPb_ratio = ParameterValidator.validate_probability(
        MPb_ratio, "MPb_ratio"
    )
```
**Recomendación**: Limitar a [0.05, 0.2] para mejor desempeño

### Grupo 3: Dos Parámetros
Algoritmos con dos parámetros relacionados.

#### APO (African Penguin Optimization)
```python
def __init__(self, ..., pf_max: float = 0.1, npairs: int = 1):
    # Validación
    self.pf_max = ParameterValidator.validate_positive_float(
        pf_max, "pf_max", min_value=0.05, max_value=0.3
    )
    self.npairs = ParameterValidator.validate_positive_integer(
        npairs, "npairs", min_value=1
    )
    if self.npairs > 3:
        warnings.warn(
            f"npairs={self.npairs} es alto. Se recomienda usar 1-3 pares.",
            UserWarning
        )
```

#### SMO (Starling Murmuration Optimizer)
```python
def __init__(self, ..., k: Optional[int] = None, mu: float = 0.3):
    # k: número de bandadas
    if k is None:
        self.k = min(10, self.population_size // 3)
    else:
        self.k = ParameterValidator.validate_positive_integer(
            k, "k", min_value=3
        )
        if self.k > self.population_size // 2:
            raise ValidationError(
                f"k debe ser <= population_size//2 ({self.population_size//2})"
            )
    
    # mu: proporción en comportamiento de separación
    self.mu = ParameterValidator.validate_probability(mu, "mu")
```

#### GVOA (Growth Variation Optimization Algorithm)
```python
def __init__(self, ..., elite_ratio: float = 0.2, r: float = 0.2):
    # elite_ratio para calcular elite_size
    self.elite_ratio = ParameterValidator.validate_positive_float(
        elite_ratio, "elite_ratio", min_value=0.1, max_value=0.33
    )
    self.elite_size = max(3, int(self.population_size * self.elite_ratio))
    
    # r: radio de búsqueda inicial
    self.r = ParameterValidator.validate_positive_float(
        r, "r", min_value=0.1, max_value=0.5
    )
```

### Grupo 4: Tres o Más Parámetros
Algoritmos con configuración más compleja.

#### EWA (Earthworm Algorithm)
```python
def __init__(self, ..., alpha: float = 0.8, beta: float = 0.2, 
             gamma: float = 0.99):
    # alpha: intensificación
    self.alpha = ParameterValidator.validate_positive_float(
        alpha, "alpha", min_value=0.5, max_value=0.9
    )
    
    # beta: exploración
    self.beta = ParameterValidator.validate_positive_float(
        beta, "beta", min_value=0.1, max_value=0.5
    )
    
    # gamma: factor de enfriamiento
    self.gamma = ParameterValidator.validate_positive_float(
        gamma, "gamma", min_value=0.9, max_value=0.999
    )
    
    # Validación cruzada
    if self.alpha + self.beta > 1.0:
        warnings.warn(
            f"alpha + beta = {self.alpha + self.beta} > 1.0. "
            "Esto puede causar comportamiento no deseado.",
            UserWarning
        )
```

#### EGTO (Enhanced Gorilla Troops Optimizer)
```python
def __init__(self, ..., P: float = 0.5, CF: float = 0.5, 
             FADs: float = 0.2):
    # Heredar validación de GTO
    super().__init__(problem, population_size, max_iterations, seed)
    
    # P: factor de perturbación
    self.P = ParameterValidator.validate_positive_float(
        P, "P", min_value=0.3, max_value=0.7
    )
    
    # CF: factor de combinación
    self.CF = ParameterValidator.validate_positive_float(
        CF, "CF", min_value=0.3, max_value=0.7
    )
    
    # FADs: probabilidad de vuelo de Lévy
    self.FADs = ParameterValidator.validate_probability(FADs, "FADs")
    if self.FADs > 0.4:
        warnings.warn(
            f"FADs={self.FADs} es alto. Se recomienda usar valores <= 0.4.",
            UserWarning
        )
```

### Grupo 5: Casos Especiales

#### RRO (Raven Roosting Optimization) - Necesita migración completa
```python
def __init__(self, ..., perception_radius: Optional[float] = None,
             leader_radius: Optional[float] = None, n_perceptions: int = 10,
             n_steps: int = 10, follow_probability: float = 0.2,
             stop_probability: float = 0.1):
    
    # Radios adaptativos basados en dimensión
    if perception_radius is None:
        self.perception_radius = 0.1 * np.sqrt(self.problem.dimension)
    else:
        self.perception_radius = ParameterValidator.validate_positive_float(
            perception_radius, "perception_radius", min_value=0.0
        )
    
    if leader_radius is None:
        self.leader_radius = 0.1 * np.sqrt(self.problem.dimension)
    else:
        self.leader_radius = ParameterValidator.validate_positive_float(
            leader_radius, "leader_radius", min_value=0.0
        )
    
    # Parámetros enteros
    self.n_perceptions = ParameterValidator.validate_positive_integer(
        n_perceptions, "n_perceptions", min_value=5
    )
    self.n_steps = ParameterValidator.validate_positive_integer(
        n_steps, "n_steps", min_value=5
    )
    
    # Probabilidades
    self.follow_probability = ParameterValidator.validate_probability(
        follow_probability, "follow_probability"
    )
    self.stop_probability = ParameterValidator.validate_probability(
        stop_probability, "stop_probability"
    )
```

#### FSA (Fish School Algorithm)
```python
def __init__(self, ..., MPb_ratio: Optional[float] = None):
    # MPb_ratio actualmente hardcodeado, hacerlo configurable
    if MPb_ratio is None:
        self.MPb_ratio = 0.1
    else:
        self.MPb_ratio = ParameterValidator.validate_positive_float(
            MPb_ratio, "MPb_ratio", min_value=0.05, max_value=0.2
        )
```

## Actualización de validators.py

Agregar en `validate_algorithm_specific_params`:

```python
# MRFO
elif algorithm_name == "mrfo":
    if "spiral_factor" in params:
        validated["spiral_factor"] = ParameterValidator.validate_positive_float(
            params["spiral_factor"], "spiral_factor", min_value=1.0, max_value=3.0
        )

# AHA
elif algorithm_name == "aha":
    if "step_size" in params:
        validated["step_size"] = ParameterValidator.validate_positive_float(
            params["step_size"], "step_size", min_value=0.01, max_value=0.5
        )

# EWA
elif algorithm_name == "ewa":
    if "alpha" in params:
        validated["alpha"] = ParameterValidator.validate_positive_float(
            params["alpha"], "alpha", min_value=0.5, max_value=0.9
        )
    if "beta" in params:
        validated["beta"] = ParameterValidator.validate_positive_float(
            params["beta"], "beta", min_value=0.1, max_value=0.5
        )
    if "gamma" in params:
        validated["gamma"] = ParameterValidator.validate_positive_float(
            params["gamma"], "gamma", min_value=0.9, max_value=0.999
        )

# ... continuar con otros algoritmos
```

## Plan de Testing

Para cada algoritmo crear test específico:

```python
# test_[algo]_v2_validation.py
class Test[ALGO]V2Validation:
    def test_valid_parameters(self, problem):
        """Test con parámetros válidos."""
        
    def test_invalid_[param]_parameter(self, problem):
        """Test con parámetro inválido."""
        
    def test_default_values(self, problem):
        """Test valores por defecto."""
        
    def test_warnings(self, problem, recwarn):
        """Test warnings para valores subóptimos."""
```

## Orden de Implementación Sugerido

### Semana 1
1. **Día 1**: Grupo 1 (sin parámetros) - Verificación y documentación
2. **Día 2**: MRFO, AHA, FGO - Un parámetro simple
3. **Día 3**: APO, SMO, GVOA - Dos parámetros
4. **Día 4**: EWA, EGTO - Múltiples parámetros
5. **Día 5**: RRO, FSA - Casos especiales

### Semana 2
6. **Día 6-7**: Crear tests unitarios para cada algoritmo
7. **Día 8**: Actualizar validators.py con todos los casos
8. **Día 9**: Ejecutar suite completa y corregir issues
9. **Día 10**: Documentación final y ejemplos

## Métricas de Completitud

- [ ] 15/15 algoritmos con validación implementada
- [ ] 15/15 algoritmos con tests específicos
- [ ] 0 warnings en ejecución normal
- [ ] 100% cobertura en validators.py
- [ ] Documentación actualizada en VALIDATION_GUIDE.md