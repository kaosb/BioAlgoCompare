# Procedimientos de Prueba

Este documento describe los procedimientos recomendados para verificar y validar las implementaciones de algoritmos en BioAlgoCompare. Aunque actualmente no se implementan pruebas automatizadas completas, estos procedimientos proporcionan una guía para pruebas manuales y una base para futuras pruebas automatizadas.

## Verificación de Implementación de Algoritmos

Cuando se implementa un nuevo algoritmo o se modifica uno existente, se deben realizar las siguientes verificaciones:

### 1. Validación de Estructura Básica

Verificar que el algoritmo:

- Hereda correctamente de `MetaheuristicAlgorithm`
- Implementa todos los métodos abstractos requeridos:
  - `initialize_population()`
  - `update_population()`
- Maneja correctamente la semilla aleatoria para reproducibilidad
- Incluye documentación adecuada (docstrings, comentarios)

**Procedimiento:**

```bash
# Verificar estructura básica
python -c "from algorithms.<nombre_algoritmo> import <Clase>; print('<Clase> importada correctamente')"

# Verificar herencia
python -c "from algorithms.<nombre_algoritmo> import <Clase>; from algorithms.base import MetaheuristicAlgorithm; print(issubclass(<Clase>, MetaheuristicAlgorithm))"
```

### 2. Verificación de Curvas de Convergencia

Es crítico que los algoritmos actualicen correctamente la curva de convergencia en cada iteración.

**Procedimiento:**

1. Ejecutar el algoritmo con un número pequeño de iteraciones:

```bash
python scripts/run.py --algorithm <algoritmo> --instance P-n16-k8 --iterations 10 --population 20 --visualize
```

2. Verificar que la curva de convergencia se ha generado correctamente:
   - Debe tener exactamente el mismo número de puntos que iteraciones (`len(convergence_curve) == iterations`)
   - Debe ser monótona no creciente (para problemas de minimización)
   - No debe contener valores nulos o incorrectos

3. Probar con diferente número de iteraciones para asegurar consistencia:

```bash
# Verificar con diferentes iteraciones
python scripts/run.py --algorithm <algoritmo> --instance P-n16-k8 --iterations 50 --population 20 --visualize
python scripts/run.py --algorithm <algoritmo> --instance P-n16-k8 --iterations 100 --population 20 --visualize
```

### 3. Prueba de Reproducibilidad

Verificar que el algoritmo produce resultados idénticos cuando se utiliza la misma semilla.

**Procedimiento:**

```bash
# Primera ejecución con semilla específica
python scripts/run.py --algorithm <algoritmo> --instance P-n16-k8 --iterations 100 --population 20 --seed 42 --save

# Segunda ejecución con la misma semilla
python scripts/run.py --algorithm <algoritmo> --instance P-n16-k8 --iterations 100 --population 20 --seed 42 --save

# Comparar los resultados (deberían ser idénticos)
diff results/<algoritmo>_P-n16-k8_run1.csv results/<algoritmo>_P-n16-k8_run2.csv
```

### 4. Verificación de Límites del Espacio de Búsqueda

Asegurarse de que el algoritmo respeta los límites del espacio de búsqueda (valores entre 0 y 1).

**Procedimiento:**

1. Modificar temporalmente el algoritmo para imprimir los rangos de las posiciones después de cada actualización.
2. Ejecutar el algoritmo y verificar que todas las posiciones se mantienen dentro de [0,1].

```python
# Código de verificación a insertar en update_population()
min_pos = np.min(np.array([ind.position for ind in self.population]))
max_pos = np.max(np.array([ind.position for ind in self.population]))
print(f"Rango de posiciones: [{min_pos}, {max_pos}]")
assert min_pos >= 0 and max_pos <= 1, "¡Posiciones fuera de rango!"
```

### 5. Comparación de Rendimiento

Comparar el rendimiento del algoritmo con otros ya implementados para detectar anomalías.

**Procedimiento:**

```bash
# Ejecutar benchmark comparativo
python scripts/analyze.py benchmark --run-benchmark --algorithms <nuevo_algoritmo>,gto,sho,apo --instances P-n16-k8 --runs 10
```

Verificar:
- El algoritmo converge adecuadamente
- El fitness final está dentro de rangos razonables comparado con otros algoritmos
- No hay errores o comportamientos anómalos durante la ejecución

## Pruebas de Instancias Específicas

Para validar que un algoritmo funciona correctamente en diferentes escenarios:

```bash
# Probar con instancias pequeñas
python scripts/run.py --algorithm <algoritmo> --instance P-n16-k8 --iterations 100

# Probar con instancias medianas
python scripts/run.py --algorithm <algoritmo> --instance E-n22-k4 --iterations 100

# Probar con instancias grandes
python scripts/run.py --algorithm <algoritmo> --instance A-n32-k5 --iterations 100
```

## Validación de Visualizaciones

Verificar que las visualizaciones generadas son correctas:

1. Las rutas deben respetar las restricciones del problema (e.g., comenzar y terminar en el depósito)
2. Las curvas de convergencia deben reflejar la mejora del fitness a lo largo de las iteraciones
3. Las visualizaciones deben ser legibles y profesionales

## Lista de Verificación para Nuevos Algoritmos

- [ ] La clase hereda correctamente de `MetaheuristicAlgorithm`
- [ ] Implementa `initialize_population()` correctamente
- [ ] Implementa `update_population()` correctamente
- [ ] Actualiza `self.convergence_curve` en cada iteración
- [ ] Mantiene las posiciones de individuos en el rango [0,1]
- [ ] Respeta la semilla aleatoria para reproducibilidad
- [ ] Documenta todos los parámetros específicos del algoritmo
- [ ] Produce visualizaciones correctas
- [ ] Rinde adecuadamente en diferentes instancias del problema
- [ ] Se comporta consistentemente en ejecuciones múltiples

## Procedimiento de Prueba Recomendado

1. **Prueba unitaria básica**: Verificar estructura y curva de convergencia
2. **Prueba de reproducibilidad**: Verificar determinismo con semillas idénticas
3. **Prueba de rendimiento**: Comparar con algoritmos conocidos
4. **Prueba de escalabilidad**: Verificar comportamiento con diferentes instancias y parámetros
5. **Revisión de código**: Asegurar que sigue las mejores prácticas y convenciones

## Futura Automatización de Pruebas

Para implementaciones futuras de pruebas automatizadas, se recomienda:

1. Crear pruebas unitarias para verificar aspectos específicos de los algoritmos
2. Implementar pruebas de integración para validar el comportamiento del sistema completo
3. Establecer un sistema de integración continua para ejecutar pruebas automáticamente
4. Desarrollar pruebas de regresión para detectar cambios en el rendimiento

## Ejemplo de Script de Prueba

A continuación se muestra un ejemplo básico de cómo se podría implementar un script de prueba manual:

```python
def test_algorithm(algorithm_name, problem_name="P-n16-k8", iterations=100, population=20, seed=42):
    """
    Prueba básica para validar un algoritmo.
    """
    from algorithms.base import MetaheuristicAlgorithm
    from problems.vrp import VRPProblem
    import importlib
    import numpy as np

    # Importar dinámicamente el algoritmo
    module = importlib.import_module(f"algorithms.{algorithm_name.lower()}")
    algorithm_class = getattr(module, algorithm_name.upper())

    # Verificar herencia
    assert issubclass(algorithm_class, MetaheuristicAlgorithm), "La clase no hereda de MetaheuristicAlgorithm"

    # Cargar problema
    problem = VRPProblem(f"data/vrp/{problem_name}.vrp")

    # Crear y ejecutar algoritmo
    algorithm = algorithm_class(problem, population_size=population, max_iterations=iterations, seed=seed)
    best_solution = algorithm.execute()

    # Verificar curva de convergencia
    assert len(algorithm.convergence_curve) == iterations, f"Curva de convergencia incorrecta: {len(algorithm.convergence_curve)} != {iterations}"

    # Verificar monotonicidad (para problemas de minimización)
    for i in range(1, len(algorithm.convergence_curve)):
        assert algorithm.convergence_curve[i] <= algorithm.convergence_curve[i-1], f"Convergencia no monótona en iteración {i}"

    # Verificar posiciones dentro de límites
    for individual in algorithm.population:
        assert np.all(individual.position >= 0) and np.all(individual.position <= 1), "Posiciones fuera de rango [0,1]"

    # Verificar mejor solución
    assert best_solution is not None, "No se encontró una solución válida"
    assert best_solution.fitness() > 0, f"Fitness sospechoso: {best_solution.fitness()}"

    print(f"✅ {algorithm_name} pasó todas las verificaciones básicas")
    print(f"   Mejor fitness: {best_solution.fitness():.2f}")
    print(f"   Tiempo de ejecución: {algorithm.execution_time:.2f} segundos")

    return algorithm, best_solution
```

Este procedimiento de prueba sirve como base para verificar la corrección de las implementaciones de algoritmos hasta que se desarrolle un framework de pruebas automatizadas más completo.
