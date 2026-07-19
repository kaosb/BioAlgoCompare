"""
Cooperative runner — N heterogeneous solvers, shared FES budget, gated transfer.

Design (tesis-mia/gestion_proyecto/DISENO_TRANSFERENCIA_MHS.md):
  * All solvers share ONE FESLimitProblem so the TOTAL evaluation budget is B
    (FES-fairness: cooperation cannot win by spending more compute than an
    isolated solver with the same B).
  * Solvers advance round-robin one step (update_population) at a time.
  * At control points (every ``transfer_every`` FES) each ordered (source,
    target) pair proposes a structural transfer (source elite -> target); the
    gate decides; memory logs the decision and its observed effect.

Conditions (see DISENO):
  C0 isolated      -> run a single solver alone (transfer disabled, pool of 1)
  C2 no-gate       -> gate.enabled = False
  C3 gated         -> gate.enabled = True  (proposed)
"""

import math

import numpy as np

from problems.continuous.cec_problem import BudgetExhausted
from cooperative.transfer_gate import TransferGate
from cooperative.transfer_memory import TransferMemory


class CooperativeRunner:
    def __init__(self, shared_problem, solver_specs, transfer_every=500,
                 gate_enabled=True, seed=0, transfer_mode="structural",
                 intent_mode="source"):
        """
        shared_problem : a FESLimitProblem shared by all solvers (defines B).
        solver_specs   : list of (name, solver_cls, kwargs). Each solver is built
                         on ``shared_problem`` so they share the FES counter.
        transfer_every : FES between control points.
        gate_enabled   : False -> C2 ablation; True -> C3 proposed.
        transfer_mode  : 'structural' (elite injection, 1 FES/transfer) or
                         'parametric' (functional-intent regime, 0 FES).
        intent_mode    : parametric only. 'source' = intent extracted from the
                         source state (the proposed mechanism); 'random' = ABL
                         ablation (random intent, no source knowledge);
                         'adversarial' = CTRL+ positive control (guaranteed-
                         harmful preset; tests that gate/rollback DETECTS it).
        """
        self.problem = shared_problem
        self.transfer_every = int(transfer_every)
        self.memory = TransferMemory()
        self.gate = TransferGate(enabled=gate_enabled, memory=self.memory)
        self.seed = int(seed)
        self.transfer_mode = str(transfer_mode)
        self.intent_mode = str(intent_mode)
        self._rng = np.random.default_rng(self.seed + 777_000)  # intent ABL only

        # FES-fairness / correct schedule (meta-audit fix, jul 2026): each solver
        # gets its FAIR share of the shared budget B (B/N) and a max_iterations
        # COHERENT with that share. Passing max_iterations=1e9 pinned PSO's inertia
        # schedule (base_w = 0.9 - 0.5*iter/max_iterations) at ~0.9 forever, so
        # PSO-in-cooperation never switched to exploitation -> it was crippled
        # regardless of transfer (verified: ~220x worse). The isolated baseline
        # went through run_with_fes, which set this correctly; cooperation did not.
        n = max(1, len(solver_specs))
        budget_per_solver = getattr(shared_problem, "max_fes", None)
        if budget_per_solver is not None:
            budget_per_solver = budget_per_solver / n

        self.solvers = []
        for i, (name, cls, kwargs) in enumerate(solver_specs):
            kw = dict(kwargs)
            # CRN (pre-registro §2.6): each solver-in-cooperation uses the SAME
            # seed as its isolated counterpart, so paired contrasts (DE-coop vs
            # DE-iso, PSO-coop vs PSO-iso) share common random numbers. The old
            # self.seed + i broke the pairing for the second solver.
            kw.setdefault("seed", self.seed)
            if budget_per_solver is not None:
                pop = int(kw.get("population_size", 30))
                epi = max(1, pop)  # per-iteration evals (structural transfer aside)
                kw["max_iterations"] = max(1, math.ceil(budget_per_solver / epi))
            solver = cls(shared_problem, **kw)
            solver.initialize_population()
            self.solvers.append({"name": name, "solver": solver})

        self.stats = {"proposed": 0, "accepted": 0, "rejected": 0,
                      "rolled_back": 0, "kept": 0, "transfers": []}

        # Parametric mode: attach a RegimeController per solver through the
        # existing il_model hook (multiplicative factors; neutral==base algo).
        # 0 FES: only reads evaluated state and writes multipliers.
        self._controllers = {}
        self._pending = {}   # target name -> commit record (deferred effect)
        if self.transfer_mode == "parametric":
            from cooperative.functional_intent import RegimeController, PRESETS
            for e in self.solvers:
                key = (e["name"] if e["name"] in PRESETS
                       else type(e["solver"]).__name__)
                ctrl = RegimeController(key)
                e["solver"].use_il = True
                e["solver"].il_model = ctrl
                self._controllers[e["name"]] = ctrl

    # --- structural transfer: inject source elite into target ---------------
    @staticmethod
    def _worst_index(pop):
        return max(range(len(pop)), key=lambda i: pop[i].fitness())

    def _inject(self, target_solver, position):
        """Replace the target's worst individual with ``position`` (R^d).

        DE and PSO both live in R^d with identical bounds, so the position is
        directly transferable (structural transfer, Nivel A). Cost: 1 FES.
        """
        pop = target_solver.population
        j = self._worst_index(pop)
        ind = pop[j]
        ind.position = np.array(position, dtype=float).copy()
        # invalidate cached fitness (attr name is _fitness across individuals)
        if hasattr(ind, "_fitness"):
            ind._fitness = None
        # reset swarm velocity if present (PSO), so the injected point is stable
        if hasattr(ind, "velocity"):
            try:
                ind.velocity = np.zeros_like(ind.position)
            except Exception:
                pass
        ind.fitness()  # re-evaluate (consumes 1 FES from the shared budget)

    def _target_error(self, solver):
        return float(solver.best_solution.fitness())

    def _target_median(self, solver):
        """Median CACHED fitness of the population (0 FES; harm-sensitive).

        Meta-audit fix (18 Jul 2026): the memory effect was measured on
        best_solution.fitness(), which is MONOTONE non-increasing, so recorded
        effects were <= 0 ALWAYS and is_harmful_pair/triple never fired (dead
        code, verified empirically: 24/24 effects = 0.0 under maximally harmful
        transfer). The population median CAN worsen, making harm measurable.
        Only cached values are read (no re-evaluation -> no FES charged).
        """
        vals = [ind._fitness for ind in solver.population
                if getattr(ind, "_fitness", None) is not None]
        if not vals:
            return self._target_error(solver)
        return float(np.median(vals))

    # --- control point: propose + gate transfers across all ordered pairs ---
    def _control_point(self):
        n = len(self.solvers)
        if n < 2:
            return
        for a in range(n):
            for b in range(n):
                if a == b:
                    continue
                src, tgt = self.solvers[a], self.solvers[b]
                cand = src["solver"].best_solution
                cand_fit = cand.fitness()
                tgt_solver = tgt["solver"]
                tgt_fits = [ind.fitness() for ind in tgt_solver.population]
                curve = tgt_solver.convergence_curve
                self.stats["proposed"] += 1
                allow = self.gate.allows(src["name"], tgt["name"], cand_fit,
                                         tgt_fits, curve)
                # harm-sensitive metric (population median), NOT the monotone
                # incumbent (meta-audit fix: incumbent gave effect<=0 always).
                med_before = self._target_median(tgt_solver)
                if allow:
                    self._inject(tgt_solver, cand.position)
                    self.stats["accepted"] += 1
                else:
                    self.stats["rejected"] += 1
                med_after = self._target_median(tgt_solver)
                effect = (med_after - med_before) if allow else None
                self.memory.record(src["name"], tgt["name"],
                                   {"cand_fit": cand_fit}, allow, effect)
                self.stats["transfers"].append(
                    {"src": src["name"], "tgt": tgt["name"],
                     "applied": allow, "effect": effect})

    # --- parametric control point: commit/rollback of functional intents ----
    def _propose_intent(self, src_solver):
        """Intent per intent_mode: source (mechanism) / random (ABL) /
        adversarial (CTRL+, guaranteed-harmful preset)."""
        from cooperative.functional_intent import (classify_intent, INTENSIFY,
                                                   DIVERSIFY, ADVERSARIAL,
                                                   MODERATE)
        if self.intent_mode == "adversarial":
            return ADVERSARIAL
        if self.intent_mode == "moderate":
            return MODERATE      # E4: subtle harm — does the gate discriminate?
        if self.intent_mode == "random":
            return self._rng.choice([INTENSIFY, DIVERSIFY, None])
        return classify_intent(src_solver)

    def _control_point_parametric(self):
        """Finalize pending commits (deferred effect, 0 FES), then propose new
        intents through the gate.

        Effect of a committed regime = incumbent error at NEXT control point vs
        at commit: if the target did not improve at all under the regime, the
        commit is ROLLED BACK (controller resets to neutral) and the triple is
        recorded harmful (positive effect) so the gate's memory can veto it.
        """
        n = len(self.solvers)
        if n < 2:
            return
        # (1) finalize pending commits
        for tgt_name, rec in list(self._pending.items()):
            tgt = next(e for e in self.solvers if e["name"] == tgt_name)
            err_now = self._target_error(tgt["solver"])
            improvement = rec["err_at_commit"] - err_now
            # Rollback decision keeps the stop-loss semantics (incumbent-based).
            # The MEMORY effect uses the harm-sensitive population median
            # (meta-audit fix): med_now - med_at_commit > 0 = the regime harmed.
            med_now = self._target_median(tgt["solver"])
            effect = med_now - rec.get("med_at_commit", med_now)
            if improvement <= 0.0:
                self._controllers[tgt_name].reset()      # rollback
                self.stats["rolled_back"] += 1
            else:
                self.stats["kept"] += 1
            self.memory.record_triple(rec["src"], tgt_name, rec["intent"],
                                      effect)
            self.stats["transfers"].append(
                {"src": rec["src"], "tgt": tgt_name, "intent": rec["intent"],
                 "applied": True, "effect": float(effect),
                 "rolled_back": bool(improvement <= 0.0)})
            del self._pending[tgt_name]
        # (2) propose new intents (a target holds at most one pending commit)
        for a in range(n):
            for b in range(n):
                if a == b:
                    continue
                src, tgt = self.solvers[a], self.solvers[b]
                if tgt["name"] in self._pending:
                    continue
                intent = self._propose_intent(src["solver"])
                self.stats["proposed"] += 1
                allow = self.gate.allows_parametric(
                    src["name"], tgt["name"],
                    src["solver"].convergence_curve,
                    tgt["solver"].convergence_curve, intent)
                if allow and intent is not None:
                    self._controllers[tgt["name"]].set_intent(intent)
                    self._pending[tgt["name"]] = {
                        "src": src["name"], "intent": intent,
                        "err_at_commit": self._target_error(tgt["solver"]),
                        "med_at_commit": self._target_median(tgt["solver"]),
                    }
                    self.stats["accepted"] += 1
                else:
                    self.stats["rejected"] += 1

    # --- main loop ----------------------------------------------------------
    def run(self):
        """Round-robin steps under the shared budget; transfer at control points.

        Returns the global best (min over solvers) and per-solver results.
        """
        cp = (self._control_point_parametric
              if self.transfer_mode == "parametric" else self._control_point)
        next_cp = self.transfer_every
        try:
            while True:
                for entry in self.solvers:
                    entry["solver"].update_population()
                if self.problem.fes >= next_cp:
                    cp()
                    next_cp += self.transfer_every
        except BudgetExhausted:
            pass

        # Read each solver's best WITHOUT re-evaluating: the budget is exhausted,
        # so calling ind.fitness() on a cache-invalidated individual would charge
        # one more FES and raise BudgetExhausted here (outside the guarded loop).
        # The known best fitness is the cached value or the last convergence point.
        per_solver = {e["name"]: self._safe_best_fitness(e["solver"])
                      for e in self.solvers}
        best_name = min(per_solver, key=per_solver.get)
        best = next(e["solver"].best_solution for e in self.solvers
                    if e["name"] == best_name)
        return {
            "best_fitness": float(per_solver[best_name]),
            "best_position": np.asarray(best.position, dtype=float),
            "per_solver": per_solver,
            "fes_used": int(self.problem.fes),
            "transfer_stats": {k: v for k, v in self.stats.items()
                               if k != "transfers"},
            "usefulness": {"->".join(k): v for k, v
                           in self.memory.usefulness_matrix().items()},
        }

    @staticmethod
    def _safe_best_fitness(solver):
        """Best fitness of a solver without re-evaluating (budget-safe)."""
        ind = solver.best_solution
        cached = getattr(ind, "_fitness", None)
        if cached is not None:
            return float(cached)
        if getattr(solver, "convergence_curve", None):
            return float(solver.convergence_curve[-1])
        return float("inf")
