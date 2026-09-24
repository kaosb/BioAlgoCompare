"""Invariants of the cooperative runner.

Each invariant has a test here: per-solver budget split by
evaluations, schedule horizons, migrant retention in every solver, reported
best == minimum evaluated, independent initial populations, no-migration
control, and exact budgets for isolated runs.
"""
import numpy as np
import pytest

from algorithms.aco import ACO
from algorithms.de import DE
from algorithms.ga import GA
from algorithms.gwo import GWO
from algorithms.pso import PSO
from cooperative.orchestrator import CooperativeRunner, elite_of
from problems.continuous.cec_problem import CECProblem, FESLimitProblem, run_with_fes

CLS = {"DE": DE, "GA": GA, "GWO": GWO, "PSO": PSO, "ACO": ACO}
PAIRS = [("GWO", "GA"), ("DE", "GA"), ("PSO", "ACO")]


class Spy(CECProblem):
    def __init__(self, *a):
        super().__init__(*a)
        self.values = []

    def evaluate(self, x):
        v = super().evaluate(x)
        self.values.append(v)
        return v


def _runner(a, b, budget, seed=10000, te=500, f=4):
    spy = Spy("CEC2014", f, 10)
    specs = [(a, CLS[a], {"population_size": 30}), (b, CLS[b], {"population_size": 30})]
    r = CooperativeRunner(FESLimitProblem(spy, budget), specs, transfer_every=te,
                          gate_enabled=False, seed=seed, transfer_mode="structural")
    return r, spy


@pytest.mark.parametrize("budget", [5000, 50000])
@pytest.mark.parametrize("pair", PAIRS)
def test_budget_exact_and_split_by_evaluations(pair, budget):
    r, spy = _runner(*pair, budget)
    res = r.run()
    assert res["fes_used"] == budget == len(spy.values)
    for name, fes in res["fes_per_solver"].items():
        assert abs(fes - budget / 2) <= 60, (pair, name, res["fes_per_solver"])


@pytest.mark.parametrize("pair", PAIRS)
def test_schedules_do_not_overrun(pair):
    r, _ = _runner(*pair, 50000)
    r.run()
    for e in r.solvers:
        s = e["solver"]
        done = len(s.convergence_curve) - 1
        assert done <= s.max_iterations + 1, (e["name"], done, s.max_iterations)


@pytest.mark.parametrize("pair", PAIRS)
def test_reported_best_is_min_evaluated(pair):
    for seed in range(10000, 10006):
        r, spy = _runner(*pair, 5000, seed=seed)
        res = r.run()
        assert res["best_fitness"] == pytest.approx(min(spy.values), rel=0, abs=0)


@pytest.mark.parametrize("target", ["DE", "GA", "GWO", "PSO", "ACO"])
def test_migrant_is_retained_by_every_solver(target):
    other = "DE" if target != "DE" else "GA"
    r, spy = _runner(target, other, 10**6, te=10**12, f=1)
    for _ in range(3):
        for e in r.solvers:
            e["solver"].update_population()
    tgt = r.solvers[0]["solver"]
    x_star = np.asarray(spy._func is not None and _optimum_like(spy), float)
    r._inject(tgt, x_star)
    f_inj = spy.values[-1]
    assert f_inj < elite_of(r.solvers[1]["solver"])[1]
    for _ in range(5):
        tgt.update_population()
        assert elite_of(tgt)[1] <= f_inj + 1e-12, target


def _optimum_like(spy):
    """A point far better than a random population: best of a local search
    around the best point seen so far (no knowledge of the optimum needed)."""
    rng = np.random.default_rng(0)
    best = None
    for _ in range(3000):
        x = rng.uniform(-100, 100, 10)
        v = CECProblem.evaluate(spy, x)
        if best is None or v < best[0]:
            best = (v, x)
    x = best[1]
    for scale in (10, 3, 1, 0.3, 0.1):
        for _ in range(300):
            y = np.clip(x + rng.normal(0, scale, 10), -100, 100)
            if CECProblem.evaluate(spy, y) < CECProblem.evaluate(spy, x):
                x = y
    return x


def test_pair_starts_from_different_populations():
    r, _ = _runner("DE", "GA", 5000)
    pa = np.array([i.position for i in r.solvers[0]["solver"].population])
    pb = np.array([i.position for i in r.solvers[1]["solver"].population])
    assert not np.allclose(pa, pb)


def test_no_migration_control():
    r, _ = _runner("GWO", "GA", 5000, te=10**12)
    res = r.run()
    assert res["transfer_stats"]["proposed"] == 0
    assert res["fes_used"] == 5000


@pytest.mark.parametrize("name", list(CLS))
@pytest.mark.parametrize("budget", [2500, 5000, 25000])
def test_isolated_budget_exact(name, budget):
    spy = Spy("CEC2014", 4, 10)
    run_with_fes(CLS[name], spy, pop_size=30, max_fes=budget, seed=1)
    assert len(spy.values) == budget


def test_gwo_leaders_are_elitist():
    spy = Spy("CEC2014", 4, 10)
    g = GWO(FESLimitProblem(spy, 10**6), population_size=30, max_iterations=200, seed=3)
    g.initialize_population()
    prev = g._alpha_score
    for _ in range(50):
        g.update_population()
        assert g._alpha_score <= prev
        assert g._alpha_score == pytest.approx(min(spy.values))
        prev = g._alpha_score
