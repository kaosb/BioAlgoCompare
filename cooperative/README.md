# cooperative/ — cooperación entre metaheurísticas heterogéneas y gate de seguridad

Código del pre-registro de la fase positiva (v0.1 y enmiendas v0.2–v0.6, en
`docs/preregistro_fase_positiva/`). Estado, validez de los resultados, entorno,
pruebas y mapa de tablas: [`../README_FASE_POSITIVA.md`](../README_FASE_POSITIVA.md).

## Componentes

| Archivo | Rol |
|---|---|
| `orchestrator.py` | `CooperativeRunner`: dos solvers sobre un presupuesto total B compartido; transferencia estructural (élite de la fuente → peor del destino, migrante absorbido) o paramétrica (régimen sobre θ_k); stop-loss con commit/rollback sobre el incumbente (élite real, gbest en PSO). `solver_seed(seed, i)`: semillas por solver, mismo mapeo que los baselines aislados (CRN) |
| `transfer_gate.py` | `TransferGate`: admisión si la fuente mejora y el destino está estancado (ventana 5, τ = 10⁻¹²), con veto opcional por memoria |
| `transfer_memory.py` | `TransferMemory`: efecto observado por triple (fuente, destino, intención), métrica de mediana; marca triples dañinos |
| `functional_intent.py` | vocabulario de regímenes `PRESETS_V2` (factores multiplicativos sobre θ_k, acotados a las regiones de convergencia) y `RegimeController` |
| `candidates.py` | candidatos de la Fase 2 (v0.3): A `BudgetAllocRunner` (asignación por nivel), B `StructuralGatedRunner` (élite bajo admisión con rollback), C `UCBRegimeRunner` (UCB1 por destino y estado); control benigno `BenignControlRunner` |
| `curves.py` | `run_with_curve`: curvas C0 en grilla Δ = 500 (Fase 1) |

## Presupuesto (equidad de FES)

- Todos los solvers de una celda evalúan sobre **un** `FESLimitProblem` con tope
  exacto B: la cooperación no puede ganar gastando más evaluaciones que un solver
  aislado con el mismo B.
- **Presupuesto por solver** (v0.5): cada solver evalúa a través de su propia
  vista (`_SolverBudget`), que cuenta sus evaluaciones; en cada paso avanza el
  solver con menos evaluaciones propias, de modo que cada uno usa ≈ B/2 sea cual
  sea su número de evaluaciones por iteración (ACO_R: 2; GA: población − élite).
- El horizonte de los schedules de cada solver (`schedule_horizon`) se calcula
  con su parte real del presupuesto (B/2).
- Baseline del portafolio C1_div: los dos solvers aislados a B/2 (el segundo a
  B − B/2), con las mismas semillas por solver.
- La transferencia paramétrica cuesta 0 FES (solo lee estado evaluado); la
  inyección estructural cuesta 1 FES por migrante, contabilizado.

## Brazos vigentes

**Piloto de la Fase 2 v0.5** (`scripts/cec_harness/run_fase2_piloto.py`, 11 brazos):
SBS_A, SBS_B (solvers aislados a B), C1_div, C1_shared (runner compartido sin
migración), C1_island (migración fija de élites cada Δ, sin gate), C3p_v2,
candidatos A, B y C, BENg y BENn (control benigno con y sin gate).

**Camino alterno v0.6** (`scripts/cec_harness/run_camino_alterno.py`, 15 brazos):

| Grupo | Brazos |
|---|---|
| baselines | C0_A, C0_B, C1_div |
| canal real | C2p (intención de la fuente, sin gate), C3p (con gate), ABL (intención al azar, con gate) |
| control adversarial | CTRLn (sin gate), CTRLn_noSL (sin gate ni stop-loss), CTRLg (con gate), CTRLg_noSL (gate sin stop-loss), CTRLg_nomem (gate sin memoria) |
| daño sutil | MODn (sin gate), MODg (con gate) |
| control benigno | BENn, BENg (régimen afinado por función en semillas separadas) |

Parámetros comunes: Δ = 500 FES, población 30, `PRESETS_V2`, memoria por mediana.

## Uso

Un brazo del camino alterno (CTRLg) y la migración fija (C1_island):

```python
from problems.continuous.cec_problem import CECProblem, FESLimitProblem
from algorithms.de import DE
from algorithms.ga import GA
from cooperative import CooperativeRunner
from cooperative.functional_intent import PRESETS_V2

specs = [("DE", DE, {"population_size": 30}), ("GA", GA, {"population_size": 30})]

prob = FESLimitProblem(CECProblem("CEC2014", 9, 10), max_fes=5000)   # B total
res = CooperativeRunner(prob, specs, transfer_every=500, gate_enabled=True, seed=13000,
                        transfer_mode="parametric", intent_mode="adversarial",
                        stop_loss=True, presets=PRESETS_V2, memory_enabled=True).run()
# res: best_fitness, fes_used (= 5000), fes_per_solver, per_solver, transfer_stats, usefulness

prob = FESLimitProblem(CECProblem("CEC2014", 9, 10), max_fes=5000)
res = CooperativeRunner(prob, specs, transfer_every=500, gate_enabled=False, seed=13000,
                        transfer_mode="structural").run()                # C1_island
```

Pruebas de invariantes (presupuesto exacto, CRN, incumbente, rollback, memoria):
`tests/test_cooperative_invariants.py`.
