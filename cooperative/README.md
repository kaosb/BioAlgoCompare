# cooperative/ — transferencia entre metaheurísticas concurrentes (Fase 3)

Nueva línea de investigación (pivote 13 Jul 2026, dir. R. Olivares). Metaheurísticas
heterogéneas que corren en paralelo y se transfieren conocimiento en tiempo real,
con un **gate anti-transferencia-negativa**. Rebanada de magíster del eje 1 de la
propuesta FONDECYT Regular 2027.

**Diseño completo:** `tesis-mia/gestion_proyecto/DISENO_TRANSFERENCIA_MHS.md`

## Componentes

| Archivo | Rol |
|---|---|
| `orchestrator.py` | `CooperativeRunner`: N solvers, presupuesto FES compartido, transferencia en puntos de control |
| `transfer_gate.py` | `TransferGate`: predicado anti-transferencia-negativa (utilidad + estancamiento + historial) |
| `transfer_memory.py` | `TransferMemory`: memoria online `(condición, transferencia, efecto)`; marca pares dañinos |

## Condiciones experimentales (ver diseño §3)

- **C0** aislado — un solver solo (baseline).
- **C2** sin gate — `gate_enabled=False` (ablación).
- **C3** con gate — `gate_enabled=True` (propuesta).

## Uso

```python
from problems.continuous.cec_problem import CECProblem, FESLimitProblem
from algorithms.de import DE
from algorithms.pso import PSO
from cooperative import CooperativeRunner

prob = FESLimitProblem(CECProblem('CEC2014', 9, 10), max_fes=5000)  # B compartido
runner = CooperativeRunner(prob,
    [('DE', DE, {'population_size': 30, 'max_iterations': 10**9}),
     ('PSO', PSO, {'population_size': 30, 'max_iterations': 10**9})],
    transfer_every=500, gate_enabled=True, seed=7)
res = runner.run()   # best_fitness, per_solver, transfer_stats, usefulness
```

## FES-fairness (crítico)

Todos los solvers comparten **un** `FESLimitProblem` → el presupuesto TOTAL es B.
La cooperación no puede ganar gastando más cómputo que un solver aislado con el
mismo B. El overhead del gate/memoria no consume FES (opera sobre estado ya
evaluado); la re-inyección de una solución sí cuesta 1 FES (contabilizado).

## Estado

- [x] Orquestador, gate y memoria — funcionales (smoke: DE+PSO, FES respetado).
- [x] Transferencia estructural (Nivel A): élite del fuente → peor del destino.
- [ ] Piloto C0/C2/C3 sobre subconjunto CEC2014 10D (`scripts/cec_harness/run_cooperative_pilot.py`).
- [ ] Transferencia paramétrica (Nivel B) vía functional intent.
- [ ] Barrido de `transfer_every` y política de disparo.
