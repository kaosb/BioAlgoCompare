# Orca Predator Algorithm (OPA)

## Descripción General

El **Orca Predator Algorithm (OPA)** es una metaheurística bioinspirada propuesta por Jiang et al. (2021) que simula el comportamiento cooperativo de caza de las orcas. El algoritmo alterna entre dos fases: persecución (exploración del espacio de búsqueda) y ataque (explotación intensiva alrededor de la mejor solución conocida).

En esta implementación, el OPA ha sido adaptado al problema de ruteo de vehículos (VRP) utilizando representaciones permutacionales y operadores discretos para búsqueda vecina.

## Implementación

- **Representación VRP:** Cada orca es una solución representada como una lista de rutas factibles por vehículo, donde cada ruta es una lista de enteros que representa la secuencia de clientes visitados.
- **Fase de persecución ("chase"):**  
  - Uso de operadores como **swap** y **2-opt** para modificar rutas.
- **Fase de ataque ("attack"):**  
  - Inserción de clientes desde una ruta hacia otra basada en la mejor solución global.
- **Aceptación estocástica:**  
  - Probabilidad de aceptar soluciones peores decrece linealmente con las iteraciones.
- **Curva de convergencia** registrada en cada iteración para evaluación posterior.

## Pseudocódigo

```text
Inicializar población de orcas con soluciones VRP aleatorias
Para cada orca: personal_best ← posición inicial

Para t = 1 … T:
    líder_global ← mejor orca actual
    Para cada orca i:
        Elegir fase:
            if t < T/2 → Persecución (chase)
            else → Ataque (attack)
        Aplicar operador discreto correspondiente
        if solución válida y mejor o rand < probabilidad_aceptación:
            actualizar posición actual
            actualizar personal_best si corresponde
    Actualizar líder_global y curva de convergencia
Retornar líder_global
```

## Análisis de Rendimiento

| Iteraciones | Fitness mín | Tiempo medio |
|-------------|-------------|--------------|
| 10          | 671.33      | 0.01 s       |
| 100         | 536.34      | 0.07 s       |
| 1 000       | 472.71      | 0.65 s       |
| 10 000      | 555.16      | 6.71 s       |
| 100 000     | 501.10      | 67.87 s      |

*El mejor resultado se obtuvo a las 1 000 iteraciones. Luego, el fitness muestra deterioro leve, lo que sugiere sobreajuste o exploración subóptima en fases posteriores.*

## Características de Convergencia

- Fase de persecución permite una exploración más amplia del espacio de soluciones.
- Fase de ataque mejora soluciones cercanas al óptimo con movimientos dirigidos.
- La aceptación estocástica facilita escapar de óptimos locales en etapas tempranas.

## Fortalezas y Limitaciones

**Fortalezas**
- Inspiración biológica con lógica clara y adaptable.
- Simplicidad estructural que facilita hibridación.
- Eficiente en problemas con restricciones.

**Limitaciones**
- Requiere operadores bien diseñados para mantener factibilidad.
- Sensible al balance entre fases en problemas de alta complejidad.

## Recomendaciones de Uso

- `population_size ≥ 40`, `T ≥ 2 000` para instancias VRP medianas.
- Incluir verificación de factibilidad en cada operador.
- Usar reinicio poblacional o intensificación local si la convergencia se estanca.

## Ejemplo de Uso

```python
from algorithms.opa import OPA

opa = OPA(problem, population_size=50, max_iterations=2000, seed=42)
best = opa.execute()
print("Mejor fitness OPA:", best.fitness())
```

## Referencias

- Jiang, Y., Wu, Q., Zhu, S., & Zhang, L. (2021). Orca predation algorithm: A novel bio-inspired algorithm for global optimization problems. *Expert Systems with Applications*, 188, 116026. https://doi.org/10.1016/j.eswa.2021.116026
- [Análisis comparativo de todos los algoritmos](../../COMPARATIVA_GLOBAL.md)