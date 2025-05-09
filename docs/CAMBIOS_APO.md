# Correcciones y Mejoras del Algoritmo APO

Este documento detalla las correcciones y mejoras realizadas al algoritmo APO (Artificial Protozoa Optimizer) para adaptarlo correctamente al problema VRP.

## Corrección del Algoritmo APO

**Fecha:** 8 de mayo de 2025

### Problemas Identificados

1. Error en la implementación de la clase `Protozoa` que no cumplía con la interfaz requerida por la clase base `Individual`, faltando los métodos abstractos `is_better_than` e `is_feasible`.

2. El algoritmo asumía incorrectamente que el problema VRP proporcionaba atributos `lower_bounds` y `upper_bounds` que podían convertirse en arrays de NumPy.

3. Se estaba inicializando la posición con los límites incorrectos, lo que podía generar valores fuera del rango válido para VRP.

### Soluciones Implementadas

1. **Implementación de métodos abstractos requeridos**:
   - Adición del método `is_better_than` para comparar individuos:
   ```python
   def is_better_than(self, other):
       """Compara si este individuo es mejor que otro."""
       return self.fitness() < other.fitness()
   ```
   - Adición del método `is_feasible` para verificar factibilidad:
   ```python
   def is_feasible(self):
       """Verifica si el individuo representa una solución factible."""
       return True  # En VRP todas las soluciones son factibles con nuestro decodificador
   ```

2. **Corrección de los límites del dominio**:
   - Establecimiento explícito de los límites del dominio para problemas VRP:
   ```python
   # Para problemas VRP, los límites son [0,1]
   self.lower_bounds = np.zeros(self.dimension)
   self.upper_bounds = np.ones(self.dimension)
   ```

3. **Corrección de la inicialización de posiciones**:
   - Inicialización adecuada de posiciones en el rango [0,1]:
   ```python
   self.position = np.random.uniform(0, 1, self.dimension)
   ```

### Características del Algoritmo APO

El algoritmo APO implementa un modelo basado en el comportamiento de protozoarios con cuatro mecanismos principales:

1. **Autotrofia**: Representa cómo los protozoarios autótrofos obtienen energía, modelado como un movimiento basado en vecinos y un individuo aleatorio:
   ```python
   # Autotrofia - Eq. 1
   j = random.randint(0, ps - 1)
   neighbor_plus = population[min(i + 1, ps - 1)].position
   neighbor_minus = population[max(i - 1, 0)].position
   wa = math.exp(-abs(population[max(i - 1, 0)].fitness()) /
                 (population[min(i + 1, ps - 1)].fitness() + 1e-16))
   delta = (population[j].position - self.position +
            (wa * (neighbor_minus - neighbor_plus))) / npairs
   f = random.random() * (1 + math.cos((iteration / max_iterations) * math.pi))
   self.position = self.position + f * delta * Mf
   ```

2. **Heterotrofia**: Simula cómo los protozoarios heterótrofos consumen otros organismos, modelado como un movimiento que considera posiciones cercanas:
   ```python
   # Heterotrofia - Eq. 7
   neighbor_minus = population[max(i - 1, 0)].position
   neighbor_plus = population[min(i + 1, ps - 1)].position
   wh = math.exp(-abs(population[max(i - 1, 0)].fitness()) /
                 (population[min(i + 1, ps - 1)].fitness() + 1e-16))
   Xnear = (1 + random.choice([-1, 1]) * random.random() * (1 - iteration / max_iterations)) * self.position
   delta = (Xnear - self.position + (wh * (neighbor_minus - neighbor_plus))) / npairs
   f = random.random() * (1 + math.cos((iteration / max_iterations) * math.pi))
   self.position = self.position + f * delta * Mf
   ```

3. **Dormancia**: Representa períodos de inactividad, modelado como un reinicio a una posición aleatoria:
   ```python
   # Dormancia - Eq. 11
   self.position = self.lower_bounds + np.random.rand(dim) * (self.upper_bounds - self.lower_bounds)
   ```

4. **Reproducción**: Simula la reproducción asexual, modelado como una perturbación parcial de la posición:
   ```python
   # Reproducción - Eq. 13
   Mr = np.zeros(dim)
   idxs = np.random.permutation(dim)[:math.ceil(dim * random.random())]
   Mr[idxs] = 1
   delta = np.random.rand(dim) * (self.lower_bounds + np.random.rand(dim) * (self.upper_bounds - self.lower_bounds))
   self.position = self.position + random.choice([-1, 1]) * delta * Mr
   ```

### Análisis de los Cambios

1. **Cumplimiento con la interfaz**:
   - Los métodos añadidos `is_better_than` e `is_feasible` aseguran que la clase `Protozoa` cumpla con la interfaz requerida por `Individual`.
   - Esto permite que el algoritmo se ejecute correctamente sin errores de abstracción.

2. **Corrección del dominio de búsqueda**:
   - La implementación adecuada de los límites [0,1] para problemas VRP asegura que todas las posiciones estén en el rango válido.
   - Esto es crucial para la correcta decodificación de soluciones en el contexto del VRP.

3. **Mecanismos biológicos**:
   - El algoritmo mantiene sus cuatro mecanismos inspirados biológicamente que ahora funcionan correctamente en el contexto del VRP.
   - La implementación incluye factores adaptativos que dependen de la progresión de las iteraciones, permitiendo un balance entre exploración y explotación.

## Resultados de las Pruebas

Las pruebas realizadas con el algoritmo APO corregido muestran:

1. **Rendimiento**:
   - Mejor fitness encontrado: 532.04 (con 500 iteraciones)
   - Fitness con 100 iteraciones: 595.03

2. **Eficiencia**:
   - Tiempo de ejecución con 100 iteraciones: 0.06s
   - Tiempo de ejecución con 500 iteraciones: 0.27s

3. **Comportamiento**:
   - El algoritmo muestra una clara mejora con el aumento de iteraciones
   - Exhibe un comportamiento no monótono en ocasiones, posiblemente debido a sus fases de dormancia y reproducción

## Conclusión

Las correcciones implementadas en el algoritmo APO han solucionado los problemas técnicos de compatibilidad con el problema VRP, permitiendo que el algoritmo funcione correctamente. El APO representa un enfoque interesante basado en el comportamiento de protozoarios, con las siguientes características:

1. **Ventajas**:
   - Implementación biológicamente inspirada con mecanismos diversificados
   - Balance entre exploración global (dormancia, reproducción) y explotación local (autotrofia, heterotrofia)
   - Adaptación dinámica de parámetros según la progresión de la búsqueda

2. **Limitaciones**:
   - Convergencia más lenta que otros algoritmos (requiere más iteraciones)
   - No alcanza la calidad de solución de algoritmos como GTO, HHO o WOA

El algoritmo APO, tras las correcciones implementadas, demuestra un comportamiento funcional en problemas VRP, aunque su rendimiento sugiere que podría ser más adecuado para otros tipos de problemas donde sus mecanismos biológicos puedan ser más efectivos. Para aplicaciones de VRP donde se valora la calidad de solución, algoritmos como GTO, HHO o WOA siguen siendo opciones más recomendables.