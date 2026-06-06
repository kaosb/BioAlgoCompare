"""
Generic Oracle mixin for measuring the achievable parameter-modulation ceiling
of ANY population-based metaheuristic in this framework.
==============================================================================

Motivation
----------
Imitation Learning (behavioural cloning) trains a policy to imitate an expert
that modulates an algorithm's control parameters online. The *upper bound* of
what any such policy can achieve is set by an **oracle**: a (hypothetical)
policy that, at every iteration, picks the modulation that yields the best
continuation. If even the oracle cannot beat the un-modulated (neutral)
algorithm, then no IL policy can -- the negative result is fundamental, not an
artefact of a weak model.

This mixin generalises the HO-specific ``HOOracle`` to arbitrary algorithms.
A concrete oracle is declared by multiple inheritance::

    class DEOracle(OracleMixin, DE):
        IL_NEUTRAL = (1.0, 1.0)             # neutral multiplicative factors
        IL_GRID = [...]                     # candidate factor tuples (excl. neutral)

The base algorithm must:
  * expose ``_get_il_params(iteration)`` as the single hook used inside
    ``update_population`` to read its (multiplicative) modulation factors, and
  * keep its mutable state (``population``, ``best_solution``,
    ``convergence_curve``, plus any algorithm-specific attributes) in
    ``self.__dict__`` and deep-copyable (numpy arrays, floats, lists).

Two shared, non-copyable references are pinned (never deep-copied): the
``problem`` and the per-instance ``rng``/``py_rng``. Stochasticity during the
oracle rollouts is controlled by *resetting the bit-generator state* of the
existing ``rng`` object (not swapping it), so every individual that holds a
reference to ``self.rng`` stays valid across snapshot/restore.

Greedy vs robust
----------------
* ``n_eval_samples == 1`` -> GREEDY (clairvoyant): scores each candidate on the
  single realised random continuation. OVERESTIMATES the ceiling because it
  exploits one lucky RNG draw. Report only as EVPI reference, never as the
  ceiling.
* ``n_eval_samples > 1`` -> ROBUST: scores each candidate by the MEAN over
  ``n_eval_samples`` independent, *paired* continuations (same seed index per
  sample across all candidates). Estimates the ceiling achievable by a policy
  that cannot see future randomness. THIS is the defensible number.

The diagnostic evaluations performed inside the rollouts are NOT meant to be
charged against a MaxFES comparison budget: run the oracle on a RAW problem
(not an FES-limited wrapper) as a separate, declared diagnostic.
"""

import copy
from typing import Sequence, Tuple

import numpy as np


class OracleMixin:
    """Greedy/robust parameter-modulation oracle, algorithm-agnostic.

    Concrete subclasses MUST define two class attributes:
        IL_NEUTRAL : tuple   neutral factors that reduce to the base algorithm.
        IL_GRID    : list[tuple]   candidate factor tuples to search each
                                   iteration (should EXCLUDE the neutral point).
    """

    IL_NEUTRAL: Tuple[float, ...] = (1.0,)
    IL_GRID: Sequence[Tuple[float, ...]] = ()

    # Attributes that must NOT be deep-copied during snapshot/restore:
    # shared references and the oracle's own bookkeeping.
    _SNAPSHOT_SKIP = frozenset({
        "problem", "rng", "py_rng", "il_model",
        "_in_rollout", "_fixed_params", "oracle_log",
        "oracle_lookahead", "n_eval_samples", "record_oracle",
    })

    def __init__(self, *args, oracle_lookahead: int = 1,
                 n_eval_samples: int = 1, record_oracle: bool = True,
                 **kwargs):
        # The oracle does not use a learned model; strip IL kwargs the factory
        # may pass through.
        kwargs.pop("use_il", None)
        kwargs.pop("il_model", None)
        kwargs.pop("il_model_path", None)
        super().__init__(*args, **kwargs)

        # Force the base update path to consult _get_il_params (this mixin's).
        self.use_il = True
        self.il_model = None

        self.oracle_lookahead = int(oracle_lookahead)
        self.n_eval_samples = int(n_eval_samples)
        self.record_oracle = bool(record_oracle)

        self._in_rollout = False
        self._fixed_params = self.IL_NEUTRAL
        self.oracle_log = []  # per-iteration diagnostic records

    # --- generic state snapshot / restore ---------------------------------
    def _snapshot(self) -> dict:
        """Deep-copy the mutable algorithm state, pinning shared references."""
        memo = {
            id(self.problem): self.problem,
            id(self.rng): self.rng,
            id(self.py_rng): self.py_rng,
        }
        data = {
            k: copy.deepcopy(v, memo)
            for k, v in self.__dict__.items()
            if k not in self._SNAPSHOT_SKIP
        }
        return {
            "data": data,
            "rng_state": copy.deepcopy(self.rng.bit_generator.state),
            "py_rng_state": self.py_rng.getstate(),
        }

    def _restore(self, snap: dict) -> None:
        """Restore state captured by :meth:`_snapshot`."""
        memo = {
            id(self.problem): self.problem,
            id(self.rng): self.rng,
            id(self.py_rng): self.py_rng,
        }
        for k, v in snap["data"].items():
            setattr(self, k, copy.deepcopy(v, memo))
        # Reset the EXISTING rng object's internal state (do not swap objects,
        # so individuals holding a reference to self.rng stay valid).
        self.rng.bit_generator.state = copy.deepcopy(snap["rng_state"])
        self.py_rng.setstate(snap["py_rng_state"])

    # --- scoring ----------------------------------------------------------
    def _oracle_score(self) -> float:
        """Objective used to rank candidates (lower is better)."""
        return float(self.best_solution.fitness())

    def _rollout(self, params) -> float:
        """Roll the population forward ``oracle_lookahead`` steps with ``params``."""
        self._fixed_params = params
        for _ in range(self.oracle_lookahead):
            self.update_population()
        return self._oracle_score()

    def _score(self, params, snap: dict, iteration: int):
        """Score a candidate from ``snap``.

        Returns ``(robust_mean, single_draw)`` where:
          * ``robust_mean`` averages ``n_eval_samples`` paired continuations
            (the defensible, non-clairvoyant score), and
          * ``single_draw`` is the j=0 continuation (seed ``[iteration, 0]``),
            the realised draw a *clairvoyant* policy would optimise for.

        Capturing both in one pass makes the EVPI (greedy - robust) come for
        free and -- crucially -- measured from the SAME snapshot, so it is a
        valid within-decision quantity (not a comparison of divergent runs).
        """
        if self.n_eval_samples <= 1:
            self._restore(snap)
            self.rng.bit_generator.state = (
                np.random.default_rng([iteration, 0]).bit_generator.state
            )
            v = self._rollout(params)
            return v, v
        vals = []
        for j in range(self.n_eval_samples):
            self._restore(snap)
            # Paired across candidates: same (iteration, j) seed for everyone.
            self.rng.bit_generator.state = (
                np.random.default_rng([iteration, j]).bit_generator.state
            )
            vals.append(self._rollout(params))
        return float(np.mean(vals)), float(vals[0])

    # --- the hook the base update_population() calls ----------------------
    def _get_il_params(self, iteration: int):
        """Return the oracle-selected modulation factors for this iteration."""
        if self._in_rollout:
            return self._fixed_params

        snap = self._snapshot()
        self._in_rollout = True
        try:
            neutral_robust, neutral_single = self._score(
                self.IL_NEUTRAL, snap, iteration)
            # Robust selection (defensible) and, in parallel, the clairvoyant
            # single-draw best (for EVPI), both from the SAME snapshot.
            best_params, best_robust = self.IL_NEUTRAL, float("inf")
            best_single = float("inf")
            for params in self.IL_GRID:
                robust, single = self._score(params, snap, iteration)
                if robust < best_robust:
                    best_robust, best_params = robust, params
                if single < best_single:
                    best_single = single
        finally:
            self._restore(snap)
            self._in_rollout = False

        if self.record_oracle:
            gain_robust = neutral_robust - best_robust
            gain_greedy = neutral_single - best_single
            self.oracle_log.append({
                "iteration": int(iteration),
                "neutral_fit": float(neutral_robust),
                "best_il_fit": float(best_robust),
                "best_params": tuple(float(x) for x in best_params),
                # positive => non-trivial modulation beats neutral at this step
                "gain_vs_neutral": float(gain_robust),
                # clairvoyant (single realised draw) gain, and the EVPI gap
                "gain_greedy": float(gain_greedy),
                "evpi": float(gain_greedy - gain_robust),
            })

        # Apply whichever is better for the forward run (the oracle is allowed
        # to fall back to neutral if no grid point improves on it).
        return best_params if best_robust < neutral_robust else self.IL_NEUTRAL

    # --- aggregate report -------------------------------------------------
    def get_oracle_summary(self) -> dict:
        """Aggregate the per-iteration oracle log into a single summary."""
        if not self.oracle_log:
            return {}
        gains = np.array([r["gain_vs_neutral"] for r in self.oracle_log])
        neutral = np.array([r["neutral_fit"] for r in self.oracle_log])
        best = np.array([r["best_il_fit"] for r in self.oracle_log])
        evpi = np.array([r.get("evpi", 0.0) for r in self.oracle_log])
        # Per-step RELATIVE gain (bounded, comparable across functions): how much
        # the robust ceiling beats neutral at each step as a fraction of neutral.
        denom = np.where(neutral > 1e-12, neutral, np.nan)
        rel_gain = np.nanmean(gains / denom)
        rel_evpi = np.nanmean(evpi / denom)
        # Final-incumbent relative ceiling (per-step composed trajectory).
        final_neutral = float(neutral[-1])
        final_best = float(best[-1])
        rel_ceiling = (
            (final_neutral - final_best) / final_neutral
            if final_neutral > 1e-12 else 0.0
        )
        return {
            "n_decisions": int(len(self.oracle_log)),
            "mean_gain_vs_neutral": float(gains.mean()),
            "frac_iters_modulation_helps": float((gains > 1e-9).mean()),
            "max_gain": float(gains.max()),
            "final_neutral_fit": final_neutral,
            "final_best_il_fit": final_best,
            "relative_ceiling": float(rel_ceiling),
            "mean_rel_gain": float(rel_gain),
            "mean_rel_evpi": float(rel_evpi),
        }
