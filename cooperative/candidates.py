"""Candidatos de la Fase 2 (pre-registro fase positiva, enmienda v0.3).

Tres mecanismos, cada uno como subclase del orquestador histórico (cuyas rutas
de la campaña v11 quedan intactas). Parámetros CONGELADOS en
docs/preregistro_fase_positiva/ENMIENDA_v0.3.md; no se ajustan tras ver resultados.

  A  BudgetAllocRunner   — asignación de presupuesto por NIVEL con piso de
                           exploración y stop-loss al reparto igual. No
                           transfiere nada (inmune al daño de vocabulario).
                           Lección de Fase 1 (cota 2b): la MEJORA es una guía
                           de asignación engañosa; se asigna por nivel actual.
  B  StructuralGatedRunner — reinyección de la élite de la fuente bajo admisión,
                           con commit/rollback (incumbente) y memoria por efecto
                           (mediana) a nivel de par.
  C  UCBRegimeRunner     — selección de régimen por efecto observado: UCB1 por
                           (destino, estado) sobre el vocabulario acotado
                           PRESETS_V2 + NEUTRAL; el crédito viene del efecto
                           medido (mediana), no de la etiqueta del preset.
  +  BenignControlRunner — control positivo: régimen benigno-por-construcción
                           (mejor estático por función, afinado en semillas
                           separadas) para medir falsos positivos del gate.
"""

import math

import numpy as np

from problems.continuous.cec_problem import BudgetExhausted
from cooperative.orchestrator import CooperativeRunner, elite_of, absorb_migrant
from cooperative.functional_intent import (PRESETS_V2, RegimeController,
                                           INTENSIFY, DIVERSIFY)

NEUTRAL = "NEUTRAL"
BENIGN = "BENIGN"


def _cached_fits(pop):
    return [ind._fitness for ind in pop if getattr(ind, "_fitness", None) is not None]


def _worst_cached_index(pop):
    idx = [i for i, ind in enumerate(pop) if getattr(ind, "_fitness", None) is not None]
    if not idx:
        return 0
    return max(idx, key=lambda i: pop[i]._fitness)


# =============================================================================
# A — asignación de presupuesto por nivel
# =============================================================================
class BudgetAllocRunner(CooperativeRunner):
    """Ventanas de Δ FES; en cada punto de control (0 FES) el solver con mejor
    incumbente recibe share_hi de la ventana siguiente y el otro share_lo (piso
    de exploración: nadie se apaga). Stop-loss: si el mejor global no mejoró en
    una ventana con reparto desigual, la siguiente ventana vuelve a 0.5/0.5.
    Schedules por iteración fijados al presupuesto completo (declarado)."""

    def __init__(self, shared_problem, solver_specs, delta=500, share_hi=0.8,
                 share_lo=0.2, seed=0, stop_loss=True, log_transfers=False):
        super().__init__(shared_problem, solver_specs, transfer_every=delta,
                         gate_enabled=False, seed=seed, transfer_mode="structural",
                         stop_loss=stop_loss, log_transfers=log_transfers)
        if len(self.solvers) != 2:
            raise ValueError("BudgetAllocRunner está definido para pares")
        if not (0 < share_lo < share_hi < 1) or abs(share_hi + share_lo - 1) > 1e-9:
            raise ValueError("shares inválidos")
        self.delta = int(delta)
        self.share_hi, self.share_lo = float(share_hi), float(share_lo)
        B = int(shared_problem.max_fes)
        # Evaluaciones por iteración de cada solver (ACO_R usa m=2 hormigas, no
        # la población): la fracción de ventana se materializa en iteraciones
        # con esta cifra, igual que run_with_fes. Schedules a presupuesto completo.
        self._epi = []
        for e in self.solvers:
            pop = int(getattr(e["solver"], "population_size", 30))
            epi = getattr(e["solver"], "evals_per_iteration", pop)
            try:
                epi = int(epi() if callable(epi) else epi)
            except Exception:
                epi = pop
            epi = max(1, epi)
            self._epi.append(epi)
            e["solver"].max_iterations = max(1, math.ceil(B / epi))
        self.shares = [0.5, 0.5]
        self.stats.update({"windows": 0, "reverts": 0, "fes_share": [0, 0]})
        self.alloc_log = []

    def run(self):
        a, b = self.solvers
        pa, pb = self._epi
        try:
            while True:
                best0 = min(self._safe_best_fitness(a["solver"]),
                            self._safe_best_fitness(b["solver"]))
                ita = max(1, int(round(self.shares[0] * self.delta / pa)))
                itb = max(1, int(round(self.shares[1] * self.delta / pb)))
                fes0 = self.problem.fes
                for k in range(max(ita, itb)):     # intercalado proporcional
                    if k < ita:
                        f = self.problem.fes; a["solver"].update_population()
                        self.stats["fes_share"][0] += self.problem.fes - f
                    if k < itb:
                        f = self.problem.fes; b["solver"].update_population()
                        self.stats["fes_share"][1] += self.problem.fes - f
                # punto de control (0 FES): nivel actual de cada solver
                ea, eb = self._safe_best_fitness(a["solver"]), self._safe_best_fitness(b["solver"])
                best1 = min(ea, eb)
                unequal = abs(self.shares[0] - 0.5) > 1e-9
                if unequal and self.stop_loss and not (best1 < best0):
                    new = [0.5, 0.5]; self.stats["reverts"] += 1
                elif ea < eb:
                    new = [self.share_hi, self.share_lo]
                elif eb < ea:
                    new = [self.share_lo, self.share_hi]
                else:
                    new = [0.5, 0.5]
                self.stats["windows"] += 1
                if self.log_transfers:
                    self.alloc_log.append({"fes": int(self.problem.fes), "shares_next": new,
                                           "e": [float(ea), float(eb)], "window_fes": int(self.problem.fes - fes0)})
                self.shares = new
        except BudgetExhausted:
            pass
        out = self._finish()
        if self.log_transfers:
            out["alloc_log"] = self.alloc_log
        return out


# =============================================================================
# B — transferencia estructural con admisión, commit/rollback y memoria
# =============================================================================
class StructuralGatedRunner(CooperativeRunner):
    """Élite de la fuente -> peor individuo del destino, solo bajo admisión
    (utilidad: candidato < mediana del destino; destino estancado; par no vetado
    por la memoria). Commit provisional: si en el siguiente punto de control el
    incumbente del destino no mejoró, ROLLBACK = se reinserta el individuo
    desplazado (posición + fitness cacheado, 0 FES) en lugar del peor actual.
    Efecto para la memoria = mediana_now - mediana_commit (nivel de par)."""

    def __init__(self, shared_problem, solver_specs, delta=500, seed=0,
                 gate_enabled=True, stop_loss=True, log_transfers=False):
        super().__init__(shared_problem, solver_specs, transfer_every=delta,
                         gate_enabled=gate_enabled, seed=seed,
                         transfer_mode="structural", stop_loss=stop_loss,
                         log_transfers=log_transfers)
        self._pending_struct = {}

    def _inject_saving(self, tgt_solver, position):
        pop = tgt_solver.population
        j = _worst_cached_index(pop)
        ind = pop[j]
        saved = (np.array(ind.position, dtype=float).copy(),
                 getattr(ind, "_fitness", None))
        ind.position = np.array(position, dtype=float).copy()
        if hasattr(ind, "_fitness"):
            ind._fitness = None
        if hasattr(ind, "velocity"):
            try:
                ind.velocity = np.zeros_like(ind.position)
            except Exception:
                pass
        ind.fitness()                              # 1 FES (presupuesto compartido)
        absorb_migrant(tgt_solver, j)   # rollback repone el individuo, no deshace líderes/pbest/gbest
        return saved

    def _rollback(self, tgt_solver, saved):
        pos, fit = saved
        if fit is None:
            return
        pop = tgt_solver.population
        j = _worst_cached_index(pop)
        ind = pop[j]
        ind.position = pos.copy()
        ind._fitness = fit                          # 0 FES: fitness cacheado
        if hasattr(ind, "velocity"):
            try:
                ind.velocity = np.zeros_like(ind.position)
            except Exception:
                pass

    def _control_point(self):
        n = len(self.solvers)
        if n < 2:
            return
        # (1) finalizar commits provisionales
        for tgt_name, rec in list(self._pending_struct.items()):
            tgt = next(e for e in self.solvers if e["name"] == tgt_name)
            err_now = self._safe_best_fitness(tgt["solver"])
            improvement = rec["err_at_commit"] - err_now
            med_now = self._target_median(tgt["solver"])
            effect = med_now - rec["med_at_commit"]
            do_rollback = self.stop_loss and improvement <= 0.0
            if do_rollback:
                self._rollback(tgt["solver"], rec["saved"]); self.stats["rolled_back"] += 1
            else:
                self.stats["kept"] += 1
            self.memory.record(rec["src"], tgt_name, {"structural": True}, True, float(effect))
            self.stats["transfers"].append({"src": rec["src"], "tgt": tgt_name,
                                            "intent": "ELITE", "applied": True,
                                            "effect": float(effect),
                                            "rolled_back": bool(do_rollback)})
            del self._pending_struct[tgt_name]
        # (2) proponer (un commit pendiente por destino)
        for a in range(n):
            for b in range(n):
                if a == b or self.solvers[b]["name"] in self._pending_struct:
                    continue
                src, tgt = self.solvers[a], self.solvers[b]
                cand_pos, cand_fit = elite_of(src["solver"])
                tgt_fits = _cached_fits(tgt["solver"].population) or [cand_fit]
                self.stats["proposed"] += 1
                allow = self.gate.allows(src["name"], tgt["name"], cand_fit,
                                         tgt_fits, tgt["solver"].convergence_curve)
                if allow:
                    med0 = self._target_median(tgt["solver"])
                    err0 = self._safe_best_fitness(tgt["solver"])
                    saved = self._inject_saving(tgt["solver"], cand_pos)
                    self._pending_struct[tgt["name"]] = {
                        "src": src["name"], "saved": saved,
                        "err_at_commit": err0, "med_at_commit": med0}
                    self.stats["accepted"] += 1
                else:
                    self.stats["rejected"] += 1


# =============================================================================
# C — régimen por efecto observado (UCB1 por destino y estado)
# =============================================================================
class UCBRegimeRunner(CooperativeRunner):
    """En cada punto de control, cada solver elige su régimen de la ventana
    siguiente con UCB1 sobre {INTENSIFY, DIVERSIFY, NEUTRAL} condicionado a su
    estado (estancado / mejorando). Recompensa = 1 si el efecto medido sobre la
    mediana fue una mejora (effect < 0), 0 si no. Stop-loss (incumbente) se
    mantiene. No usa la intención de la fuente: el crédito es por efecto."""

    ARMS = (INTENSIFY, DIVERSIFY, NEUTRAL)

    def __init__(self, shared_problem, solver_specs, delta=500, seed=0,
                 c_ucb=math.sqrt(2.0), presets=None, stop_loss=True,
                 log_transfers=False):
        super().__init__(shared_problem, solver_specs, transfer_every=delta,
                         gate_enabled=True, seed=seed, transfer_mode="parametric",
                         intent_mode="source", stop_loss=stop_loss,
                         log_transfers=log_transfers)
        table = presets if presets is not None else PRESETS_V2
        for e in self.solvers:                      # vocabulario acotado
            key = e["name"] if e["name"] in table else type(e["solver"]).__name__
            ctrl = RegimeController(key, presets=table)
            e["solver"].il_model = ctrl
            self._controllers[e["name"]] = ctrl
        self.c_ucb = float(c_ucb)
        self._bandit = {e["name"]: {} for e in self.solvers}   # name -> state -> arm -> [n, sum]
        self.stats.update({"arm_counts": {e["name"]: {a: 0 for a in self.ARMS}
                                          for e in self.solvers}})

    def _state(self, solver):
        return "estancado" if self.gate._is_stagnating(solver.convergence_curve) else "mejorando"

    def _choose(self, name, state):
        table = self._bandit[name].setdefault(state, {a: [0, 0.0] for a in self.ARMS})
        for a in self.ARMS:                          # brazos no probados primero
            if table[a][0] == 0:
                return a
        N = sum(v[0] for v in table.values())
        return max(self.ARMS, key=lambda a: table[a][1] / table[a][0]
                   + self.c_ucb * math.sqrt(math.log(N) / table[a][0]))

    def _control_point_parametric(self):
        # (1) finalizar commits: stop-loss por incumbente + recompensa por mediana
        for name, rec in list(self._pending.items()):
            e = next(x for x in self.solvers if x["name"] == name)
            err_now = self._safe_best_fitness(e["solver"])
            improvement = rec["err_at_commit"] - err_now
            med_now = self._target_median(e["solver"])
            effect = med_now - rec["med_at_commit"]
            do_rollback = self.stop_loss and improvement <= 0.0 and rec["intent"] != NEUTRAL
            if do_rollback:
                self._controllers[name].reset(); self.stats["rolled_back"] += 1
            else:
                self.stats["kept"] += 1
            reward = 1.0 if effect < 0.0 else 0.0
            cell = self._bandit[name][rec["state"]][rec["intent"]]
            cell[0] += 1; cell[1] += reward
            self.stats["transfers"].append({"src": name, "tgt": name, "intent": rec["intent"],
                                            "state": rec["state"], "applied": True,
                                            "effect": float(effect), "reward": reward,
                                            "rolled_back": bool(do_rollback)})
            del self._pending[name]
        # (2) elegir régimen para la ventana siguiente
        for e in self.solvers:
            name = e["name"]
            if name in self._pending:
                continue
            state = self._state(e["solver"])
            arm = self._choose(name, state)
            self.stats["proposed"] += 1; self.stats["accepted"] += 1
            self.stats["arm_counts"][name][arm] += 1
            if arm == NEUTRAL:
                self._controllers[name].reset()
            else:
                self._controllers[name].set_intent(arm)
            self._pending[name] = {"src": name, "intent": arm, "state": state,
                                   "err_at_commit": self._safe_best_fitness(e["solver"]),
                                   "med_at_commit": self._target_median(e["solver"])}


# =============================================================================
# Control positivo: transferencia benigna por construcción
# =============================================================================
class BenignControlRunner(CooperativeRunner):
    """Como el runner paramétrico de la campaña, pero la intención propuesta es
    siempre BENIGN = el mejor régimen estático por función del destino (afinado
    en semillas separadas). Con gate (BENg) vs sin gate (BENn): la diferencia
    mide cuánta transferencia útil bloquea o revierte el gate (falsos
    positivos)."""

    def __init__(self, shared_problem, solver_specs, benign_factors, delta=500,
                 seed=0, gate_enabled=True, stop_loss=True, log_transfers=False,
                 presets=None):
        super().__init__(shared_problem, solver_specs, transfer_every=delta,
                         gate_enabled=gate_enabled, seed=seed,
                         transfer_mode="parametric", intent_mode="source",
                         stop_loss=stop_loss, log_transfers=log_transfers)
        base = presets if presets is not None else PRESETS_V2
        for e in self.solvers:
            key = e["name"] if e["name"] in base else type(e["solver"]).__name__
            table = {key: dict(base[key])}
            table[key][BENIGN] = tuple(benign_factors[e["name"]])
            ctrl = RegimeController(key, presets=table)
            e["solver"].il_model = ctrl
            self._controllers[e["name"]] = ctrl

    def _propose_intent(self, src_solver):
        return BENIGN
