# Plan de Implementación Detallado

## Tarea 1: Completar Validación en Algoritmos v2

### Análisis de Parámetros por Algoritmo

| Algoritmo | Parámetros Específicos | Rangos Válidos | Estado |
|-----------|------------------------|----------------|---------|
| WOA | - | - | ✅ No requiere |
| SMA | z | [0.0, 1.0] | ✅ Implementado |
| GTO | p, beta | p: [0.0, 1.0], beta: > 0 | ✅ Implementado |
| MRFO | - | - | ⏳ Pendiente |
| EGTO | Hereda de GTO | - | ⏳ Pendiente |
| AHA | migration_coeff | > 0 | ⏳ Pendiente |
| EWA | similarity, reproduction_rate | [0.0, 1.0] ambos | ⏳ Pendiente |
| FSA | step_individual, step_volitive | > 0 ambos | ⏳ Pendiente |
| APO | z | [0.0, 1.0] | ⏳ Pendiente |
| GVOA | - | - | ⏳ Pendiente |
| OPA | Pa | [0.0, 1.0] | ⏳ Pendiente |
| RRO | perception_probability | [0.0, 1.0] | ⏳ Pendiente |
| SMO | mu, k | mu: [0.0, 1.0], k: >= 1 | ⏳ Pendiente |
| HOA | h, beta | ambos > 0 | ⏳ Pendiente |
| FGO | migration_rate | [0.0, 1.0] | ⏳ Pendiente |
| SHO | - | - | ⏳ Pendiente |
| FOA | - | - | ⏳ Pendiente |
| HHO | E0, jump_strength | E0: [-1, 1], JS: [0, 2] | ⏳ Pendiente |

### Plan de Implementación

#### Semana 1: Algoritmos sin parámetros o simples
**Día 1-2:**
- MRFO (verificar si realmente no tiene parámetros)
- GVOA (verificar si realmente no tiene parámetros)
- SHO (verificar si realmente no tiene parámetros)
- FOA (verificar si realmente no tiene parámetros)

**Día 3-4:**
- AHA (migration_coeff)
- APO (z)
- OPA (Pa)
- RRO (perception_probability)
- FGO (migration_rate)

**Día 5:**
- EWA (similarity, reproduction_rate)
- FSA (step_individual, step_volitive)
- SMO (mu, k)

#### Semana 2: Algoritmos complejos y testing
**Día 6-7:**
- HOA (h, beta)
- HHO (E0, jump_strength)
- EGTO (verificar herencia de GTO)

**Día 8-9:**
- Crear tests unitarios para cada algoritmo
- Ejecutar suite completa de validación
- Documentar en VALIDATION_GUIDE.md

**Día 10:**
- Integración final
- Actualizar validators.py con todos los casos
- Verificación cruzada

## Tarea 2: Jerarquía Completa de Problemas

### Diseño de la Arquitectura

```
AbstractProblem (base)
├── DiscreteOptimizationProblem
│   ├── RoutingProblem
│   │   ├── VRPProblem (existente)
│   │   ├── TSPProblem
│   │   └── CVRPTWProblem
│   ├── SchedulingProblem
│   │   ├── JobShopProblem
│   │   └── FlowShopProblem
│   └── CombinationalProblem
│       ├── KnapsackProblem
│       └── BinPackingProblem
└── ContinuousOptimizationProblem
    ├── UnconstrainedProblem
    │   ├── SphereProblem
    │   ├── RastriginProblem
    │   └── AckleyProblem
    └── ConstrainedProblem
        ├── ConstrainedBenchmark1
        └── ConstrainedBenchmark2
```

### Plan de Implementación

#### Semana 3: Base y Problemas Discretos
**Día 11-12:**
- Refactorizar AbstractProblem
- Crear DiscreteOptimizationProblem base
- Crear ContinuousOptimizationProblem base

**Día 13-14:**
- Implementar TSPProblem
  - Cargar instancias TSPLIB
  - Métodos de evaluación
  - Tests

**Día 15:**
- Implementar adaptadores para conectar problemas con algoritmos
- Sistema de encoding/decoding para problemas discretos

#### Semana 4: Problemas Continuos y Scheduling
**Día 16-17:**
- Implementar problemas continuos básicos:
  - SphereProblem
  - RastriginProblem
  - AckleyProblem

**Día 18-19:**
- Implementar JobShopProblem
  - Parser de instancias
  - Evaluación de makespan
  - Representación de soluciones

**Día 20:**
- Tests de integración
- Documentación completa
- Ejemplos de uso

### Estructura de Archivos Propuesta

```
problems/
├── __init__.py
├── base.py (AbstractProblem refactorizado)
├── discrete/
│   ├── __init__.py
│   ├── routing/
│   │   ├── __init__.py
│   │   ├── vrp.py (existente, adaptar)
│   │   ├── tsp.py
│   │   └── cvrptw.py
│   ├── scheduling/
│   │   ├── __init__.py
│   │   ├── job_shop.py
│   │   └── flow_shop.py
│   └── combinatorial/
│       ├── __init__.py
│       ├── knapsack.py
│       └── bin_packing.py
└── continuous/
    ├── __init__.py
    ├── unconstrained/
    │   ├── __init__.py
    │   ├── sphere.py
    │   ├── rastrigin.py
    │   └── ackley.py
    └── constrained/
        ├── __init__.py
        └── benchmarks.py
```

## Orden de Ejecución Recomendado

### Fase 1 (2 semanas): Completar Validación
1. Implementar validación faltante en algoritmos
2. Crear tests exhaustivos
3. Documentar cada validación
4. Verificar integración con CLI

### Fase 2 (2 semanas): Jerarquía de Problemas
1. Diseñar e implementar estructura base
2. Migrar VRPProblem a nueva estructura
3. Implementar TSP como prueba de concepto
4. Agregar problemas continuos para testing
5. Implementar Job Shop como problema complejo

### Entregables por Fase

#### Fase 1:
- [ ] 15 algoritmos con validación completa
- [ ] Suite de tests de validación pasando
- [ ] Documentación actualizada
- [ ] Guía de validación completa

#### Fase 2:
- [ ] Nueva jerarquía de problemas implementada
- [ ] Al menos 5 nuevos tipos de problemas
- [ ] Adaptadores para algoritmos existentes
- [ ] Tests de integración
- [ ] Documentación y ejemplos

## Consideraciones Técnicas

### Para Validación:
1. Mantener retrocompatibilidad
2. Mensajes de error claros
3. Warnings para valores subóptimos
4. Documentar rangos recomendados

### Para Problemas:
1. Interfaz consistente
2. Métodos de conversión entre representaciones
3. Carga desde archivos estándar (TSPLIB, OR-Library)
4. Visualización de soluciones

## Métricas de Éxito

1. **Validación**: 100% algoritmos con validación, 0 errores en tests
2. **Problemas**: Al menos 3 tipos diferentes funcionando
3. **Integración**: CLI funciona con todos los problemas
4. **Documentación**: Guías actualizadas para cada componente

## Riesgos y Mitigación

| Riesgo | Probabilidad | Impacto | Mitigación |
|--------|--------------|---------|------------|
| Cambios breaking en API | Media | Alto | Versionar cambios, deprecation warnings |
| Complejidad en adaptadores | Alta | Medio | Diseño simple inicial, iterativo |
| Tests tardando mucho | Media | Bajo | Paralelización, tests selectivos |
| Documentación desactualizada | Alta | Medio | Actualizar junto con código |