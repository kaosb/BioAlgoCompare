"""Regression: CECProblem must reproduce the OFFICIAL CEC C code.

Reference values in tests/data/cec_official_reference.json were produced by the
compiled official Suganthan C code (revisión interna del 23-Sep-2026). opfunu
1.0.1 failed this test in 110/142 cases.
"""
import json
import math
import os

import numpy as np
import pytest

from problems.continuous.cec_problem import CECProblem, InvalidEvaluation

_REF = json.load(open(os.path.join(os.path.dirname(__file__), "data", "cec_official_reference.json")))
_CASES = sorted(_REF["cases"])


def _parse(key):
    suite, f, d = key.split(":")
    return suite, int(f[1:]), int(d[1:])


@pytest.mark.parametrize("key", _CASES)
def test_matches_official_c(key):
    suite, f, d = _parse(key)
    case = _REF["cases"][key]
    X = np.vstack([np.random.default_rng(case["seed"]).uniform(-100, 100, (_REF["n"], d)), np.zeros((1, d))])
    p = CECProblem(suite, f, d)
    got = np.array([p.raw(x) for x in X])
    ref = np.array(case["values"])
    rel = np.max(np.abs(got - ref) / np.maximum(1.0, np.abs(ref)))
    assert rel < 1e-8, f"{key}: max rel error {rel:.3e}"


def test_bench_has_71_functions_official_numbering():
    probs = [("CEC2014", f) for f in range(1, 31)] + [("CEC2017", f) for f in range(1, 31) if f != 2] \
        + [("CEC2022", f) for f in range(1, 13)]
    assert len(probs) == 71
    for s, f in probs:
        CECProblem(s, f, 10)


def test_retired_and_unsupported_rejected():
    with pytest.raises(ValueError):
        CECProblem("CEC2017", 2, 10)
    with pytest.raises(ValueError):
        CECProblem("CEC2022", 1, 50)


def test_impossible_value_raises():
    p = CECProblem("CEC2014", 1, 10)
    p.f_global = p.raw(np.zeros(10)) + 1.0  # force a value below the (fake) optimum
    with pytest.raises(InvalidEvaluation):
        p.evaluate(np.zeros(10))


def test_error_non_negative_and_finite_on_random_points():
    rng = np.random.default_rng(0)
    for s, f in [("CEC2014", 10), ("CEC2014", 11), ("CEC2017", 10), ("CEC2017", 18), ("CEC2022", 10)]:
        p = CECProblem(s, f, 10)
        for x in rng.uniform(-100, 100, (200, 10)):
            e = p.evaluate(x)
            assert math.isfinite(e) and e >= 0
