# Requisitos para Implementación de Algoritmos

Este documento define los requisitos técnicos y de implementación que deben cumplir todos los algoritmos metaheurísticos integrados en BioAlgoCompare, para garantizar la consistencia, reproducibilidad y rigor científico del proyecto.

## Implementación de la Clase Base

Todos los algoritmos deben heredar de la clase base `MetaheuristicAlgorithm` definida en `algorithms/base.py`. Esta clase proporciona la estructura básica y funcionalidades comunes:

```python
class MetaheuristicAlgorithm(ABC):
    def __init__(self, problem, population_size=30, max_iterations=100, seed=None):
        # Inicialización común
        ...
    
    @abstractmethod
    def initialize_population(self):
        # Cada algoritmo debe implementar su propio método de inicialización
        pass
    
    @abstractmethod
    def update_population(self):
        # Cada algoritmo debe implementar su propio método de actualización
        pass
    
    def execute(self):
        # Ejecución común
        ...
    
    def get_convergence_curve(self):
        # Retorna la curva de convergencia
        ...
```

## Requisitos de Implementación

### 1. Inicialización de la Población

El método `initialize_population()` debe:

- Crear individuos con posiciones aleatorias en el espacio de búsqueda [0,1]
- Establecer el mejor individuo inicial
- Garantizar reproducibilidad respetando la semilla aleatoria

### 2. Actualización de la Población

El método `update_population()` debe:

- Implementar el algoritmo específico de actualización
- Asegurarse de que las posiciones de los individuos permanezcan en el rango [0,1]
- Actualizar el mejor individuo si se encuentra una mejor solución
- **IMPORTANTE**: Actualizar la curva de convergencia con el mejor fitness en cada iteración:
  ```python
  # Al final del método update_population():
  self.convergence_curve.append(self.best_solution.fitness())
  ```

### 3. Curvas de Convergencia

La correcta actualización de `self.convergence_curve` es crítica para:

- Visualización del progreso de optimización
- Análisis comparativo entre algoritmos
- Estudios de convergencia en publicaciones científicas
- La validación de la calidad del algoritmo

### 4. Reproducibilidad

Para garantizar la reproducibilidad científica, todos los algoritmos deben:

- Respetar la semilla aleatoria proporcionada en la inicialización
- Utilizar los generadores aleatorios de NumPy y random de Python de manera consistente
- Documentar cualquier componente estocástico o aleatorio

### 5. Parámetros de Algoritmo

Cada algoritmo debe definir sus parámetros específicos en el constructor y:

- Proporcionar valores predeterminados razonables
- Documentar cada parámetro claramente con su significado y rango recomendado
- Permitir la configuración externa cuando sea apropiado

## Lista de Verificación para Nuevos Algoritmos

- [ ] Hereda correctamente de `MetaheuristicAlgorithm`
- [ ] Implementa `initialize_population()` correctamente
- [ ] Implementa `update_population()` correctamente
- [ ] **Actualiza `self.convergence_curve` en cada iteración**
- [ ] Maneja correctamente las restricciones del espacio de búsqueda [0,1]
- [ ] Respeta la semilla aleatoria para reproducibilidad
- [ ] Documenta todos los parámetros específicos del algoritmo
- [ ] Incluye referencia al artículo científico original

## Ejemplo de Actualización de Curva de Convergencia

Todos los algoritmos deben incluir al final de su método `update_population()` el siguiente código para garantizar la generación correcta de curvas de convergencia:

```python
def update_population(self):
    # Implementación del algoritmo
    # ...
    
    # Actualizar cada individuo
    for i in range(self.population_size):
        # No mover el mejor individuo
        if self.population[i] is not self.best_solution:
            # Actualizar según el algoritmo
            # ...
            
            # Actualizar mejor solución si es necesario
            if self.population[i].is_better_than(self.best_solution):
                individual_copy = Individual(self.problem)
                individual_copy.copy(self.population[i])
                self.best_solution = individual_copy
    
    # IMPORTANTE: Registrar el mejor fitness en la curva de convergencia
    self.convergence_curve.append(self.best_solution.fitness())
```

La ausencia de esta actualización impedirá la correcta visualización y análisis del algoritmo, comprometiendo su validez científica y comparabilidad con otros métodos.