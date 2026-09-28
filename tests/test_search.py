"""Checks for the week-3 search tools."""
import json
from pathlib import Path

import numpy as np

from src.search import _project_capped_simplex, ga, linear_gradient_K, linear_objective, target_metrics
from src.sensorsim import load_data, mixtures, noise_sigma

WEEK2 = Path(__file__).resolve().parents[1] / 'weeks/02'


def test_linear_gradient_matches_finite_differences():
    ids, K, g, ref = load_data()
    sigma = noise_sigma(g, ref)
    ix = json.loads((WEEK2 / 'array_designs.json').read_text())['primary']['indices']
    Ks, ss = K[ix], sigma[ix]
    grad = linear_gradient_K(Ks, ss)
    for a, j in [(0, 1), (3, 2), (7, 0), (11, 4)]:
        step = 1e-6 * Ks[a, j]
        up, down = Ks.copy(), Ks.copy()
        up[a, j] += step
        down[a, j] -= step
        fd = (linear_objective(up / ss[:, None]) - linear_objective(down / ss[:, None])) / (2 * step)
        assert abs(fd - grad[a, j]) <= 1e-4 * abs(grad[a, j])


def test_capped_simplex_projection_is_feasible():
    w = _project_capped_simplex(np.random.default_rng(0).normal(size=464), 12)
    assert abs(w.sum() - 12) < 1e-6 and w.min() >= 0 and w.max() <= 1


def test_target_metrics_are_zero_for_perfect_recovery():
    X = mixtures(20260921)[0]
    tm = target_metrics(X, X)
    assert tm['overall_mae_pp'] == 0 and tm['ethene_mae_pp'] == 0 and tm['ratio_err_pct'] == 0
    assert tm['ratio_cases'] > 0


def test_ga_never_loses_its_seed():
    pool = np.arange(40)
    seed = tuple(range(12))

    def evaluate(arrays):
        return [(float(sum(a)), {}) for a in arrays]
    best, best_score, _ = ga(evaluate, pool, np.random.default_rng(1), seeds=[seed], generations=5, pop_size=16)
    assert best_score <= sum(seed)
