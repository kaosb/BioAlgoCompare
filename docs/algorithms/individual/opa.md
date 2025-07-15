# Orca Predator Algorithm (OPA)

## Descripción General

El **Orca Predator Algorithm (OPA)** es una metaheurística bioinspirada propuesta por Jiang et al. (2021) que simula el comportamiento cooperativo de caza de las orcas. El algoritmo alterna entre dos fases: persecución (exploración del espacio de búsqueda) y ataque (explotación intensiva alrededor de la mejor solución conocida).

En esta implementación, el OPA ha sido adaptado al problema de ruteo de vehículos (VRP) utilizando representación canónica de rutas y operadores discretos para búsqueda vecina, siguiendo estrictos estándares de rigor científico.

## Implementación con rigor científico

- **Representación canónica VRP:** Cada orca es una solución representada como `List[List[int]]` donde:
  - Cada lista interna es una ruta que comienza y termina en el depósito (índice 0)
  - Todos los clientes (1...n) aparecen exactamente una vez en alguna ruta
  - Cada ruta respeta la restricción de capacidad del vehículo

- **Evaluación determinista:**
  - La función `evaluate_routes()` calcula el costo directamente de las rutas
  - No usa números aleatorios (RNG) durante la evaluación
  - Aplicación consistente de penalizaciones para soluciones no factibles

- **Operadores discretos preservando factibilidad:**
  - **_random_swap:** Intercambia dos clientes aleatorios entre dos rutas distintas
  - **_two_opt:** Aplica 2‑opt a una sola ruta para mejorar su recorrido
  - **_relocate:** Mueve un cliente entre rutas, preferentemente hacia rutas del líder

- **Rigor en convergencia:**
  - Mejor solución se guarda exactamente como se encontró
  - La curva de convergencia es monotónica decreciente o constante
  - Reproducibilidad garantizada con semillas aleatorias
  - Tests unitarios verifican todas las propiedades de rigor científico

## Pseudocódigo

```text
Inicializar población de orcas con soluciones VRP aleatorias factibles
Para cada orca: personal_best ← posición inicial

Para t = 1 … T:
    líder_global ← mejor orca actual
    Para cada orca i:
        Elegir fase:
            if t < T/2 → Persecución (chase)
            else → Ataque (attack)
        Aplicar operador discreto correspondiente
        Reparar solución si es necesario
        Verificar factibilidad
        if solución factible y (mejor o rand < probabilidad_aceptación):
            actualizar posición actual
            actualizar personal_best si corresponde
    Actualizar líder_global y curva de convergencia
Retornar líder_global
```

## Análisis de Rendimiento

| Instancia   | Iteraciones | Fitness mín | Fitness medio ± std | Tiempo medio |
|-------------|-------------|-------------|---------------------|--------------|
| P-n16-k8    | 50          | 424.16      | -                   | 0.05 s       |
| E-n22-k4    | 100         | 518.82      | -                   | 0.09 s       |
| E-n22-k4    | 1000        | 463.93      | 503.01 ± 17.43      | -            |

Los resultados muestran que el algoritmo tiene un rendimiento competitivo en la instancia E-n22-k4 con 1000 iteraciones. En comparación con otros algoritmos metaheurísticos evaluados para esta instancia:

- OPA tiene un rendimiento intermedio en términos de fitness promedio (posición 8 de 17)
- El mejor fitness de OPA (463.93) se queda detrás de algoritmos como FOA (384.86), GVOA (388.50) y SMO (392.90)
- OPA supera a algoritmos como APO, AHA y HHO en calidad de solución

Estos resultados sugieren que OPA tiene un buen equilibrio entre calidad de solución y eficiencia computacional, aunque tiene margen de mejora en términos de calidad de solución para algunas instancias.

## Características de Convergencia

- **Patrón de convergencia**: Los experimentos con 1000 iteraciones muestran una convergencia rápida en las primeras ~100 iteraciones (fase de persecución/"chase"), seguida de un mejoramiento más gradual durante la fase de ataque ("attack").
- **Estabilidad**: La curva de convergencia tiende a estabilizarse después de aproximadamente 200-300 iteraciones, sugiriendo que el algoritmo encuentra buenas soluciones relativamente pronto.
- **Mejora tardía**: En algunos casos, se observan mejoras significativas cerca del final de la ejecución, como se ve en la semilla 55 donde el mejor fitness (463.93) se alcanzó en las iteraciones finales.
- **Reproducibilidad**: Las ejecuciones con las mismas semillas producen exactamente los mismos resultados, confirmando el determinismo del algoritmo.
- **Escape de óptimos locales**: La aceptación estocástica facilitó escapar de óptimos locales durante la fase inicial, lo que se refleja en los saltos de la curva de convergencia.

## Fortalezas y Limitaciones

**Fortalezas**
- Implementación con rigor científico y reproducibilidad garantizada.
- Inspiración biológica con lógica clara y adaptable.
- Operadores discretos especializados para VRP.
- Eficiente en problemas con restricciones.
- Excelente rendimiento computacional.

**Limitaciones**
- Requiere operadores bien diseñados para mantener factibilidad.
- Sensible al balance entre fases en problemas de alta complejidad.

## Recomendaciones de Uso

- **Parámetros óptimos**: `population_size = 40`, `max_iterations = 1000` proporcionan un buen equilibrio entre calidad de solución y tiempo de ejecución para instancias VRP medianas.
- **Semillas recomendadas**: Utilizar semillas estadísticamente significativas como secuencias de Fibonacci (1, 2, 3, 5, 8, 13, ...) o potencias de 2 (2, 4, 8, 16, ...) para una exploración más completa del espacio de soluciones.
- **Verificación**: Incluir verificación de factibilidad en cada operador para mantener soluciones válidas.
- **Hibridación**: Dado que FOA, GVOA y SMO obtuvieron mejores resultados en algunos casos, considerar la hibridación de OPA con estos algoritmos para mejorar su rendimiento.
- **Aplicaciones**: Ideal para aplicaciones con restricciones de tiempo donde se necesita una solución razonable rápidamente, aunque para soluciones de máxima calidad se recomiendan algoritmos como FOA.

## Verificación científica

Esta implementación de OPA ha sido verificada con tests unitarios que comprueban:
- Correcta inicialización de rutas factibles
- Evaluación determinista y coherente
- Reparación correcta de rutas no factibles
- Convergencia monotónica o constante
- Reproducibilidad con semillas aleatorias

## Ejemplo de Uso

```python
from algorithms.opa import OPA
from problems.vrp import VRPProblem

# Cargar instancia VRP
problem = VRPProblem("data/vrp/E-n22-k4.vrp")

# Crear y ejecutar OPA con semilla para reproducibilidad
opa = OPA(problem, population_size=50, max_iterations=1000, seed=42)
best = opa.execute()

# Obtener mejor solución encontrada
print("Mejor fitness OPA:", best.fitness())
print("Tiempo de ejecución:", opa.get_execution_time(), "s")

# Visualizar convergencia
import matplotlib.pyplot as plt
plt.plot(opa.get_convergence_curve())
plt.xlabel("Iteración")
plt.ylabel("Fitness")
plt.title("Curva de Convergencia OPA")
plt.show()
```

## Referencias

- Jiang, Y., Wu, Q., Zhu, S., & Zhang, L. (2021). Orca predation algorithm: A novel bio-inspired algorithm for global optimization problems. *Expert Systems with Applications*, 188, 116026. https://doi.org/10.1016/j.eswa.2021.116026
- [Análisis comparativo de todos los algoritmos](../../analysis/comparison.md)
