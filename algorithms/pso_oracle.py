"""
Oracle variant of PSO -- POSITIVE CONTROL for the HO modulation study.

PSO genuinely depends on its parameters (c1, c2, w), unlike the parameter-free
HO. This oracle quantifies the upper bound of improvement achievable by greedy
per-iteration modulation of (c1, c2, w), using the same snapshot/rollout
methodology as the HO oracle.

Interpretation: if the PSO oracle yields a substantially larger gain than the
HO oracle (~3%), it supports the thesis that HO's parameter-free design leaves
little room for parametric modulation, whereas parametric algorithms like PSO
benefit more -- the expected contrast from the literature.
"""

from itertools import product

import numpy as np

from algorithms.pso import PSO

# Candidate grid for (c1, c2, w). Neutral PSO default is (2.0, 2.0, w_linear(t)).
PSO_GRID = list(product([0.5, 1.5, 2.5], [0.5, 1.5, 2.5], [0.4, 0.65, 0.9]))


def _clone_pso(p):
    return {
        "pos": [x.position.copy() for x in p.population],
        "vel": [x.velocity.copy() for x in p.population],
        "pbp": [x.pbest_position.copy() for x in p.population],
        "pbf": [x.pbest_fitness for x in p.population],
        "fit": [x._fitness for x in p.population],
        "gbp": None if p.gbest_position is None else p.gbest_position.copy(),
        "gbf": p.gbest_fitness,
        "curve": p.convergence_curve.copy(),
        "rng": p.rng.bit_generator.state,
    }


def _restore_pso(p, s):
    for i, x in enumerate(p.population):
        x.position = s["pos"][i].copy()
        x.velocity = s["vel"][i].copy()
        x.pbest_position = s["pbp"][i].copy()
        x.pbest_fitness = s["pbf"][i]
        x._fitness = s["fit"][i]
    p.gbest_position = None if s["gbp"] is None else s["gbp"].copy()
    p.gbest_fitness = s["gbf"]
    p.convergence_curve = s["curve"].copy()
    p.rng.bit_generator.state = s["rng"]


class PSOOracle(PSO):
    """PSO whose per-iteration (c1, c2, w) are chosen by a greedy oracle."""

    def __init__(self, *args, oracle_grid=None, oracle_lookahead: int = 1,
                 n_eval_samples: int = 1, **kwargs):
        kwargs.pop("use_il", None)
        kwargs.pop("il_model_path", None)
        super().__init__(*args, **kwargs)
        self.oracle_grid = oracle_grid or PSO_GRID
        self.oracle_lookahead = oracle_lookahead
        # n_eval_samples > 1 => ROBUST: score by mean over n rng continuations.
        self.n_eval_samples = n_eval_samples
        self._in_rollout = False
        self._fixed = (2.0, 2.0, 0.9)
        self.oracle_log = []

    def _apply_and_step(self, c1, c2, w):
        for x in self.population:
            x.c1, x.c2, x.w = c1, c2, w
        for x in self.population:
            x.update_velocity_position(self.gbest_position)
        self.update_global_best()
        self.convergence_curve.append(self.gbest_fitness)
        self.best_solution = min(self.population, key=lambda p: p.fitness())

    def _oracle_select(self, iteration):
        snapshot = _clone_pso(self)
        w_lin = 0.9 - (0.9 - 0.4) * iteration / self.max_iterations
        neutral = (2.0, 2.0, w_lin)

        def _one(params):
            self._fixed = params
            for _ in range(self.oracle_lookahead):
                self._apply_and_step(*params)
            return self.gbest_fitness

        def score(params):
            if self.n_eval_samples <= 1:
                _restore_pso(self, snapshot)
                return _one(params)
            # ROBUST: mean gbest over n independent rng continuations (paired by j).
            # Particles share self.rng object, so reseed its internal state per sample.
            vals = []
            for j in range(self.n_eval_samples):
                _restore_pso(self, snapshot)
                self.rng.bit_generator.state = np.random.default_rng(
                    [iteration, j]).bit_generator.state
                vals.append(_one(params))
            return float(np.mean(vals))

        self._in_rollout = True
        try:
            neutral_fit = score(neutral)
            best, best_fit = neutral, neutral_fit
            for params in self.oracle_grid:
                f = score(params)
                if f < best_fit:
                    best_fit, best = f, params
        finally:
            _restore_pso(self, snapshot)
            self._in_rollout = False

        self.oracle_log.append({
            "iteration": iteration, "neutral_fit": float(neutral_fit),
            "best_fit": float(best_fit), "gain_vs_neutral": float(neutral_fit - best_fit),
        })
        return best

    def update_population(self) -> None:
        iteration = len(self.convergence_curve) - 1
        if self._in_rollout:
            self._apply_and_step(*self._fixed)
            return
        c1, c2, w = self._oracle_select(iteration)
        self._apply_and_step(c1, c2, w)

    def get_parameters(self) -> dict:
        params = super().get_parameters()
        params["algorithm"] = "PSO+Oracle"
        return params
