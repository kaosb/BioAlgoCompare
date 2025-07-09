# Nueva Jerarquía de Problemas - Resumen

## Estado de Implementación

### ✅ Completado

1. **Estructura Base**
   - `AbstractProblem[T]`: Clase genérica base para todos los problemas
   - `ContinuousProblem`: Base para problemas continuos
   - `LegacyAbstractProblem`: Compatibilidad hacia atrás

2. **Problemas Continuos**
   - `ContinuousOptimizationProblem`: Clase base mejorada
   - Benchmarks implementados:
     - `SphereProblem`: Función unimodal simple
     - `RastriginProblem`: Altamente multimodal
     - `AckleyProblem`: Multimodal con región exterior plana
     - `RosenbrockProblem`: Valle estrecho (banana)
     - `GriewankProblem`: Multimodal con término de producto
     - `SchwefelProblem`: Engañoso con óptimo lejos del origen

3. **Problemas Discretos**
   - `DiscreteOptimizationProblem`: Base para problemas discretos
   - `PermutationProblem`: Base para problemas de permutación

4. **Adaptadores**
   - `ContinuousAdapter`: Usa nuevos problemas con algoritmos legacy
   - `DiscreteAdapter`: Usa problemas discretos con algoritmos continuos
   - `ConstraintHandler`: Manejo de restricciones
   - `MultiObjectiveAdapter`: Escalarización multiobjetivo

5. **Compatibilidad**
   - VRPProblem sigue funcionando sin cambios
   - Todos los algoritmos v2 funcionan con nuevos problemas
   - Tests de compatibilidad pasando 100%

## Uso

### Problema Continuo Directo
```python
from problems import SphereProblem
from algorithms.woa_v2 import WOAV2

# Crear problema
problem = SphereProblem(dimension=30)

# Usar con algoritmo
algo = WOAV2(problem, population_size=50)
best = algo.execute()
print(f"Best fitness: {best.fitness()}")
print(f"Distance to optimum: {problem.distance_to_optimum(best.position)}")
```

### Problema con Adaptador (para máxima compatibilidad)
```python
from problems import RastriginProblem, ContinuousAdapter
from algorithms.sma_v2 import SMAV2

# Crear y adaptar problema
rastrigin = RastriginProblem(dimension=20)
adapted = ContinuousAdapter(rastrigin)

# Usar con cualquier algoritmo
algo = SMAV2(adapted, population_size=30)
best = algo.execute()
```

### VRP Sin Cambios
```python
from problems import VRPProblem
from algorithms.gto_v2 import GTOV2

# Funciona exactamente igual que antes
vrp = VRPProblem("data/vrp/A-n32-k5.vrp")
algo = GTOV2(vrp, population_size=50)
best = algo.execute()
```

## Características Nuevas

1. **Métricas de Problema**
   - Contador de evaluaciones
   - Distancia al óptimo conocido
   - Gap al valor óptimo

2. **Información de Gradiente** (donde esté disponible)
   ```python
   if problem.has_gradient():
       grad = problem.gradient(solution)
   ```

3. **Problemas Tipados**
   - Representación natural para cada tipo
   - Conversión automática continuo/discreto
   - Validación de factibilidad específica

## Ventajas de la Nueva Arquitectura

1. **Extensibilidad**: Fácil agregar nuevos tipos de problemas
2. **Type Safety**: Tipos genéricos para mayor seguridad
3. **Compatibilidad**: 100% compatible hacia atrás
4. **Flexibilidad**: Adaptadores para cualquier combinación
5. **Métricas**: Mejor tracking y análisis de rendimiento

## Próximos Pasos

### Pendientes
- [ ] Implementar TSPProblem
- [ ] Implementar JobShopProblem
- [ ] Agregar más benchmarks continuos (CEC suites)
- [ ] Problemas con restricciones (g01-g24)
- [ ] Sistema de registro automático de problemas

### Futuras Mejoras
- Carga lazy de problemas grandes
- Cache de evaluaciones costosas
- Paralelización de evaluaciones batch
- Visualización automática de problemas