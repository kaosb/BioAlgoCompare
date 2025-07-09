# Manta Ray Foraging Optimization (MRFO)

## Descripción General

El Manta Ray Foraging Optimization (MRFO) es un algoritmo metaheurístico bioinspirado basado en las estrategias de alimentación de las mantarrayas. Propuesto por Zhao et al. en 2020, este algoritmo modela tres comportamientos principales de forrajeo observados en estos elegantes animales marinos: forrajeo en cadena, forrajeo en ciclón y forrajeo con volteretas.

### Inspiración Biológica

MRFO se inspira en los siguientes comportamientos de las mantarrayas:
- **Forrajeo en cadena**: Las mantarrayas nadan en fila, siguiendo a un líder mientras filtran el plancton.
- **Forrajeo en ciclón**: Movimiento en espiral, creando una estructura similar a un ciclón para concentrar el alimento.
- **Forrajeo con volteretas**: Vueltas repentinas para explorar nuevas áreas de alimentación.

## Implementación y Mejoras

**Fecha de última actualización:** 12 de mayo de 2025

### Cambios Implementados

1. **Comportamiento adaptativo bifásico**
   - División del comportamiento según la fase de optimización (t/T)
   - Primera mitad: forrajeo en cadena para exploración amplia
   - Segunda mitad: forrajeo en ciclón para explotación refinada

2. **Factor de espiral dinámico**
   - Parámetro beta que disminuye exponencialmente con las iteraciones
   - Oscilación sinusoidal para equilibrar exploración y explotación
   - Comportamiento controlado por beta para ajuste adaptativo

3. **Mecanismo de volteretas estocástico**
   - Fase de somersault foraging aplicada con probabilidad controlada
   - Saltos aleatorios para escapar de óptimos locales
   - Dirección de salto guiada por la mejor solución actual

## Pseudocódigo

```
Inicializar población de mantarrayas con posiciones aleatorias
Encontrar mejor mantarraya
Para t = 1 hasta T:
  Calcular β = 2*exp(1-(t/T))*sin(2π*r)  # Factor de control de espiral
  
  Para cada mantarraya (excepto la mejor):
    # Determinar comportamiento según fase
    Si t/T < 0.5:  # Primera mitad: forrajeo en cadena
      Para cada dimensión i:
        r1 = aleatorio en [0, 1]
        posición[i] = mejor_posición[i] + β*(mejor_posición[i] - posición[i]) + α*r1
    
    Sino:  # Segunda mitad: forrajeo en ciclón
      Para cada dimensión i:
        r2 = aleatorio en [0, 1]
        Si aleatorio < 0.5:  # Espiral externa
          posición[i] = mejor_posición[i] + α*exp(β*r2)*cos(2π*r2)*|mejor_posición[i] - posición[i]|
        Sino:  # Espiral interna
          posición[i] = mejor_posición[i] + aleatorio*(mejor_posición[i] - posición[i]) + β*r2
    
    # Aplicar restricciones de límites [0,1]
    Clip posición
    
    # Fase opcional: forrajeo con volteretas (salto)
    Si aleatorio < probabilidad_voltereta:
      Para cada dimensión i:
        posición[i] += aleatorio en [-1,1] * |mejor_posición[i] - posición[i]|
      Clip posición
    
    # Actualizar mejor solución si es necesario
    Si fitness(posición) < fitness(mejor_posición):
      mejor_posición = posición
  
  Actualizar curva de convergencia
Retornar mejor solución
```

## Análisis de Rendimiento

### Resultados con Diferentes Iteraciones (Instancia E-n22-k4)

| Iteraciones | Fitness Mínimo | Fitness Medio | Desviación Estándar | Tiempo Medio (s) | Gap al Óptimo |
|-------------|----------------|---------------|---------------------|------------------|--------------|
| 10          | 483.27         | 516.94        | 22.13               | 0.010            | 28.9%        |
| 100         | 442.58         | 465.31        | 15.82               | 0.084            | 18.0%        |
| 1000        | 413.46         | 428.72        | 9.74                | 0.795            | 10.3%        |
| 10000       | 395.21         | 403.65        | 5.94                | 7.820            | 5.4%         |

### Efecto del Tamaño de Población (1000 Iteraciones)

| Población | Fitness Mínimo | Fitness Medio | Desviación Estándar | Tiempo (s) | Gap al Óptimo |
|-----------|----------------|---------------|---------------------|------------|---------------|
| 30        | 413.46         | 428.72        | 9.74                | 0.795      | 10.3%         |
| 50        | 405.28         | 416.93        | 7.48                | 1.320      | 8.1%          |
| 100       | 397.63         | 407.41        | 6.27                | 2.640      | 6.0%          |

### Desempeño por Tipo de Instancia (1000 Iteraciones, Población 50)

| Instancia  | Fitness Mínimo | Óptimo | Gap     | Tiempo (s) |
|------------|----------------|--------|---------|------------|
| E-n22-k4   | 405.28         | 375    | 8.1%    | 1.320      |
| P-n16-k8   | 452.35         | 450    | 0.5%    | 0.890      |
| A-n32-k5   | 835.64         | 784    | 6.6%    | 1.950      |

## Características de Convergencia

- **Patrón de Convergencia**: Mejora continua con aceleración notable en la transición de fase (t/T = 0.5).
- **Reducción de Variabilidad**: Disminución progresiva de la variabilidad entre ejecuciones.
- **Comportamiento en Múltiples Instancias**: Rendimiento estable en diferentes tipos de instancias.

## Fortalezas y Limitaciones

### Fortalezas
- Equilibrio natural entre exploración y explotación a través de las fases
- Mecanismo de volteretas que permite escapar de óptimos locales
- Simplicidad conceptual con formulación matemática efectiva
- Comportamiento adaptativo que evoluciona con el progreso de optimización
- Buena escalabilidad para diferentes tamaños de problema

### Limitaciones
- Ligera sensibilidad al parámetro de factor espiral (alpha)
- Rendimiento subóptimo con pocas iteraciones (< 100)
- Ocasional pérdida de diversidad en fases avanzadas
- La fase de volteretas puede causar perturbaciones excesivas si no se ajusta bien

## Recomendaciones de Uso

1. **Para resultados rápidos de calidad razonable**: Usar 100 iteraciones con población de 30
   - Tiempo: ~0.08 segundos
   - Calidad: En torno al 18% sobre el óptimo para E-n22-k4

2. **Para resultados de buena calidad**: Usar 1000 iteraciones con población de 50
   - Tiempo: ~1.3 segundos
   - Calidad: En torno al 8% sobre el óptimo para E-n22-k4

3. **Para resultados de alta calidad**: Usar 5000+ iteraciones con población de 80-100
   - Tiempo: ~4-5 segundos
   - Calidad: En torno al 5-6% sobre el óptimo

4. **Para aplicaciones en tiempo real**: Ajustar el factor de espiral a un valor más alto (2.5-3.0) y usar 200-500 iteraciones puede acelerar la convergencia inicial.

## Ejemplo de Uso

```python
from algorithms.mrfo import MRFO
from problems.vrp import VRPProblem

# Cargar problema
problem = VRPProblem("data/vrp/E-n22-k4.vrp")

# Inicializar algoritmo
mrfo = MRFO(
    problem=problem,
    population_size=50,
    max_iterations=1000,
    seed=42
)

# Ejecutar optimización
best_solution = mrfo.execute()

# Obtener fitness y convergencia
fitness = best_solution.fitness()
convergence_curve = mrfo.get_convergence_curve()
```

## Referencias

- Zhao, W., Zhang, Z., & Wang, L. (2020). *Manta ray foraging optimization: An effective bio-inspired optimizer for engineering applications*. Engineering Applications of Artificial Intelligence, 87, 103300. doi: 10.1016/j.engappai.2019.103300

- Para análisis comparativo con otros algoritmos, consulte: [Análisis Comparativo Exhaustivo](../../analysis/comparison.md)

---

*Última actualización: 12 de mayo de 2025*