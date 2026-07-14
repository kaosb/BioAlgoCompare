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
                 gate_enabled=True, seed=0):
        """
        shared_problem : a FESLimitProblem shared by all solvers (defines B).
        solver_specs   : list of (name, solver_cls, kwargs). Each solver is built
                         on ``shared_problem`` so they share the FES counter.
        transfer_every : FES between control points.
        gate_enabled   : False -> C2 ablation; True -> C3 proposed.
        """
        self.problem = shared_problem
        self.transfer_every = int(transfer_every)
        self.memory = TransferMemory()
        self.gate = TransferGate(enabled=gate_enabled, memory=self.memory)
        self.seed = int(seed)

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
            kw.setdefault("seed", self.seed + i)
            if budget_per_solver is not None:
                pop = int(kw.get("population_size", 30))
                epi = max(1, pop)  # per-iteration evals (structural transfer aside)
                kw["max_iterations"] = max(1, math.ceil(budget_per_solver / epi))
            solver = cls(shared_problem, **kw)
            solver.initialize_population()
            self.solvers.append({"name": name, "solver": solver})

        self.stats = {"proposed": 0, "accepted": 0, "rejected": 0,
                      "transfers": []}

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
                err_before = self._target_error(tgt_solver)
                if allow:
                    self._inject(tgt_solver, cand.position)
                    self.stats["accepted"] += 1
                else:
                    self.stats["rejected"] += 1
                err_after = self._target_error(tgt_solver)
                effect = (err_after - err_before) if allow else None
                self.memory.record(src["name"], tgt["name"],
                                   {"cand_fit": cand_fit}, allow, effect)
                self.stats["transfers"].append(
                    {"src": src["name"], "tgt": tgt["name"],
                     "applied": allow, "effect": effect})

    # --- main loop ----------------------------------------------------------
    def run(self):
        """Round-robin steps under the shared budget; transfer at control points.

        Returns the global best (min over solvers) and per-solver results.
        """
        next_cp = self.transfer_every
        try:
            while True:
                for entry in self.solvers:
                    entry["solver"].update_population()
                if self.problem.fes >= next_cp:
                    self._control_point()
                    next_cp += self.transfer_every
        except BudgetExhausted:
            pass

        best = min((e["solver"].best_solution for e in self.solvers),
                   key=lambda s: s.fitness())
        return {
            "best_fitness": float(best.fitness()),
            "best_position": np.asarray(best.position, dtype=float),
            "per_solver": {e["name"]: float(e["solver"].best_solution.fitness())
                           for e in self.solvers},
            "fes_used": int(self.problem.fes),
            "transfer_stats": {k: v for k, v in self.stats.items()
                               if k != "transfers"},
            "usefulness": {f"{s}->{t}": v for (s, t), v
                           in self.memory.usefulness_matrix().items()},
        }
