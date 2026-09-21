# Detalles de Implementación

Este documento proporciona detalles técnicos sobre la implementación de BioAlgoCompare, describiendo las clases clave, estructuras de datos, y decisiones de implementación relevantes.

## Arquitectura General

```
optimizacion/
├── algorithms/           # Implementaciones de algoritmos metaheurísticos
├── problems/             # Problemas de optimización (VRP, etc.)
├── scripts/              # Scripts de ejecución y análisis
├── utils/                # Utilidades comunes
│   └── improved/         # Versiones mejoradas de utilidades
├── data/                 # Datasets para problemas de optimización
│   └── vrp/              # Instancias de Vehicle Routing Problem
│       └── Solomon/      # Instancias Solomon para VRP
└── results/              # Resultados de benchmarks
```

## Estructura de Clases

### Algoritmos Metaheurísticos

La base de todos los algoritmos es la clase abstracta `MetaheuristicAlgorithm` en `algorithms/base.py`:

```python
class MetaheuristicAlgorithm(ABC):
    def __init__(self, problem, population_size=30, max_iterations=100, seed=None):
        self.problem = problem
        self.population_size = population_size
        self.max_iterations = max_iterations
        self.seed = seed
        self.population = []
        self.best_solution = None
        self.convergence_curve = []
        self.execution_time = 0

        # Inicialización de generadores aleatorios
        if seed is not None:
            np.random.seed(seed)
            random.seed(seed)

    @abstractmethod
    def initialize_population(self):
        """Inicializa la población con individuos aleatorios."""
        pass

    @abstractmethod
    def update_population(self):
        """Actualiza la población según el algoritmo específico."""
        pass

    def execute(self):
        """Ejecuta el algoritmo completo."""
        start_time = time.time()

        try:
            # Inicializar población
            self.initialize_population()

            # Actualizar población por max_iterations
            for i in range(self.max_iterations):
                self.update_population()

            return self.best_solution

        finally:
            self.execution_time = time.time() - start_time
```

Cada algoritmo específico implementa los métodos abstractos:

1. `initialize_population()`: Crea la población inicial de soluciones candidatas
2. `update_population()`: Implementa la lógica específica del algoritmo bio-inspirado

### Individuos y Soluciones

Cada algoritmo tiene su propia clase de individuo (e.g., `Earthworm`, `Protozoa`, `Gorilla`) que:

1. Mantiene una posición en el espacio de búsqueda continuo
2. Proporciona métodos para calcular fitness
3. Implementa mecanismos de comparación entre soluciones

Ejemplo de una clase de individuo (simplificado):

```python
class Individual:
    def __init__(self, problem):
        self.problem = problem
        self.dimension = problem.get_dimension()
        self.position = np.random.uniform(0, 1, self.dimension)
        self._fitness = None

    def fitness(self):
        if self._fitness is None:
            self._fitness = self.problem.evaluate(self.position)
        return self._fitness

    def is_better_than(self, other):
        return self.fitness() < other.fitness()  # Minimización
```

### Problema VRP

La clase `VRPProblem` implementa el Vehicle Routing Problem:

```python
class VRPProblem:
    def __init__(self, instance_path):
        # Cargar instancia
        self.nodes, self.capacity, self.demands = self.load_instance(instance_path)
        self.distance_matrix = self.compute_distance_matrix()
        self.optimal_value = self.get_optimal_value(instance_path)

    def decode_solution(self, position):
        """Decodifica una solución continua a rutas discretas."""
        # Convertir posición continua a permutación
        permutation = np.argsort(position) + 1  # +1 porque el depósito es 0

        # Construir rutas respetando restricciones de capacidad
        routes = []
        current_route = [0]  # Iniciar desde el depósito
        current_capacity = 0

        for node in permutation:
            if current_capacity + self.demands[node] <= self.capacity:
                current_route.append(node)
                current_capacity += self.demands[node]
            else:
                current_route.append(0)  # Volver al depósito
                routes.append(current_route)
                current_route = [0, node]  # Nueva ruta
                current_capacity = self.demands[node]

        if len(current_route) > 1:
            current_route.append(0)  # Volver al depósito
            routes.append(current_route)

        # Calcular distancia total
        total_distance = self.calculate_total_distance(routes)

        return routes, total_distance, permutation

    def evaluate(self, position):
        """Evalúa la calidad de una solución (menor es mejor)."""
        _, distance, _ = self.decode_solution(position)
        return distance
```

## Mecanismos Clave

### Adaptación Continua a Combinatoria

Los algoritmos metaheurísticos bio-inspirados están diseñados para espacios continuos, pero VRP es un problema combinatorio. La adaptación se implementa mediante:

1. **Codificación ordinal**: La posición continua en [0,1] se traduce a una permutación ordenando los valores.
2. **Decodificación de rutas**: La permutación se convierte en rutas de vehículos respetando restricciones de capacidad.
3. **Evaluación**: Las rutas se evalúan calculando la distancia total.

### Curvas de Convergencia

Cada algoritmo registra la calidad de la mejor solución en cada iteración:

```python
# Al final del método update_population():
self.convergence_curve.append(self.best_solution.fitness())
```

### Sistema de Benchmarking

El sistema de benchmarking (`utils/benchmarking.py`) proporciona:

1. **Ejecución sistemática**: Ejecuta múltiples algoritmos en múltiples instancias con repeticiones
2. **Recopilación de métricas**: Registra fitness, tiempo, curvas de convergencia
3. **Cálculo de estadísticas**: Media, desviación estándar, mínimo, máximo
4. **Comparación con óptimos**: Calcula gap al óptimo conocido

```python
def run_benchmark(algorithms, instances, runs=5, iterations=100, population=30, seed=42, parallel=False):
    results = []

    # Procesar cada combinación algoritmo-instancia
    combinations = [(algo_name, algo_class, instance)
                   for algo_name, algo_class in algorithms.items()
                   for instance in instances]

    if parallel:
        # Ejecutar en paralelo
        with mp.Pool() as pool:
            batch_results = pool.starmap(
                _run_single_benchmark,
                [(algo_name, algo_class, instance, runs, iterations, population, seed)
                 for algo_name, algo_class, instance in combinations]
            )
            results.extend(batch_results)
    else:
        # Ejecutar secuencialmente
        for algo_name, algo_class, instance in tqdm(combinations):
            result = _run_single_benchmark(
                algo_name, algo_class, instance, runs, iterations, population, seed
            )
            results.append(result)

    return results
```

### Análisis Estadístico

El módulo `statistical_analysis.py` implementa pruebas estadísticas rigurosas:

1. **Prueba de Friedman**: Comparación no paramétrica de múltiples algoritmos
2. **Pruebas post-hoc**: Wilcoxon, Nemenyi, con corrección para comparaciones múltiples
3. **Diagramas de diferencia crítica**: Representación visual de rankings
4. **Cálculo de tamaño del efecto**: Cliff's Delta, Vargha-Delaney

## Paralelización

La implementación soporta ejecución paralela en varios niveles:

1. **Múltiples ejecuciones**: Paralelización de repeticiones independientes
2. **Múltiples benchmarks**: Paralelización de combinaciones algoritmo-instancia
3. **Múltiples análisis**: Paralelización de pruebas estadísticas

El paralelismo se implementa principalmente usando `multiprocessing.Pool`:

```python
with mp.Pool() as pool:
    results = pool.starmap(worker_function, parameter_list)
```

## Gestión de Semillas Aleatorias

Para garantizar reproducibilidad científica, cada ejecución recibe una semilla específica:

```python
# En MetaheuristicAlgorithm.__init__:
if seed is not None:
    np.random.seed(seed)
    random.seed(seed)

# En ejecuciones múltiples:
for run in range(runs):
    run_seed = seed + run if seed is not None else None
    algorithm = AlgorithmClass(problem, population_size, iterations, run_seed)
```

## Visualización

El sistema implementa múltiples tipos de visualizaciones:

1. **Soluciones VRP**: Representación gráfica de rutas
2. **Curvas de convergencia**: Progreso de fitness a lo largo de iteraciones
3. **Boxplots**: Distribución de resultados entre algoritmos
4. **Mapas de calor**: Comparación estadística entre pares de algoritmos
5. **Diagramas de diferencia crítica**: Rankings relativos con significancia estadística

## Instancias Solomon para VRP

El proyecto incorpora las instancias Solomon, un conjunto estándar de benchmarks para VRP con ventanas de tiempo:

### Series Incluidas

1. **Series 101** (ventanas de tiempo estrechas):
   - **C101**: Clientes agrupados geográficamente
   - **R101**: Clientes distribuidos aleatoriamente
   - **RC101**: Combinación de agrupados y aleatorios

2. **Series 201** (ventanas de tiempo amplias):
   - **C201**: Clientes agrupados
   - **R201**: Clientes distribuidos aleatoriamente
   - **RC201**: Combinación de agrupados y aleatorios

### Formato de Datos

Para que las instancias Solomon sean compatibles con nuestro parser `VRPProblem`, se requiere un formato específico que incluya:

```
NAME : <nombre_instancia>
DIMENSION : <número_nodos>
CAPACITY : <capacidad_vehículos>
NODE_COORD_SECTION
<id_nodo> <coord_x> <coord_y>
...
DEMAND_SECTION
<id_nodo> <demanda>
...
DEPOT_SECTION
<id_depósito>
-1
EOF
```

### Herramientas de Conversión

Se ha desarrollado el script `convert_solomon_format.py` para convertir las instancias Solomon originales al formato requerido:

```python
def convert_to_vrp_format(data, output_path):
    """Convierte datos Solomon al formato VRP requerido"""
    # Escribir encabezado y datos originales
    # ...

    # Agregar secciones requeridas
    f.write(f"\nNAME : {data['name']}\n")
    f.write(f"DIMENSION : {data['dimension']}\n")
    f.write(f"CAPACITY : {data['capacity']}\n")

    # Sección de coordenadas
    f.write("NODE_COORD_SECTION\n")
    for node_id, x, y in sorted_nodes:
        f.write(f"{node_id} {x} {y}\n")

    # Sección de demandas
    f.write("DEMAND_SECTION\n")
    for node_id, x, y in sorted_nodes:
        f.write(f"{node_id} {demands_dict[node_id]}\n")

    # Sección de depósito
    f.write("DEPOT_SECTION\n")
    f.write("0\n")
    f.write("-1\n")
    f.write("EOF")
```

### Scripts de Benchmarking Específicos

Se han desarrollado scripts especializados para trabajar con estas instancias:

1. `run_full_solomon_benchmark.py`: Ejecuta benchmarks en todas las instancias Solomon
2. `run_extended_solomon_benchmark.py`: Ejecuta benchmarks extendidos con más iteraciones
3. `analyze_solomon_results.py`: Genera visualizaciones y análisis comparativos

## Decisiones de Implementación Destacables

1. **Inmutabilidad de soluciones**: Al encontrar una mejor solución, se crea una copia para evitar modificaciones accidentales:
   ```python
   if new_solution.is_better_than(self.best_solution):
       solution_copy = IndividualClass(self.problem)
       solution_copy.copy(new_solution)
       self.best_solution = solution_copy
   ```

2. **Cálculo perezoso de fitness**: El fitness solo se calcula cuando es necesario y se cachea:
   ```python
   def fitness(self):
       if self._fitness is None:
           self._fitness = self.problem.evaluate(self.position)
       return self._fitness
   ```

3. **Normalización de posiciones**: Se mantienen las posiciones en [0,1] para consistencia:
   ```python
   # Tras actualizar posición
   self.position = np.clip(self.position, 0, 1)
   ```

4. **Interfaces CLI robustas**: Uso de Click para crear interfaces de línea de comandos profesionales con validación de parámetros.

5. **Medición de tiempos por iteración**: Implementación de un sistema de medición precisa del tiempo por iteración:
   ```python
   # En utils/improved/timing.py
   def record_iteration_time(algorithm, instance, run_id, iter_time, total_time, iterations):
       """Registra el tiempo promedio por iteración"""
       global _iteration_times, _time_lock

       avg_iter_time = iter_time / iterations

       new_entry = {
           "algorithm": algorithm,
           "instance": instance,
           "run_id": run_id,
           "avg_iter_time": avg_iter_time,
           "total_time": total_time,
           "iterations": iterations
       }

       # Acceso sincronizado para ejecución paralela
       if _time_lock:
           with _time_lock:
               _iteration_times.append(new_entry)
       else:
           _iteration_times.append(new_entry)
   ```

6. **Propagación de métricas de tiempo**: Asegurando que los tiempos por iteración se incluyan siempre en los informes de benchmark:
   ```python
   # En enhanced_benchmarking.py
   def create_summary_dataframe(benchmark_results):
       # ...

       # Añadir tiempo promedio por iteración si está disponible
       algo_inst_key = (result.algorithm_name, result.instance_name)
       if algo_inst_key in avg_times_dict:
           row["avg_iter_time"] = avg_times_dict[algo_inst_key]
       else:
           # Si no está disponible directamente, calcular el promedio
           matching_records = [entry for entry in recorded if
                             entry["algorithm"] == result.algorithm_name and
                             entry["instance"] == result.instance_name]
           if matching_records:
               row["avg_iter_time"] = sum(r["avg_iter_time"] for r in matching_records) / len(matching_records)

       # ...
   ```

Estas decisiones de implementación contribuyen a un sistema coherente, eficiente y científicamente riguroso para la evaluación y comparación de algoritmos metaheurísticos bio-inspirados.
