"""Target-driven MOF array search on top of the week-2 simulator (src/sensorsim.py).

Pieces, all selecting k MOFs from the candidate pool:
- target_metrics / score: the week-3 objective (each metric divided by its target, averaged).
- Evaluator: parallel, cached scoring of arrays on one fixed mixture set (common random numbers).
- ga: genetic algorithm (tournament selection, set crossover, swap mutation, elitism).
- swap_search: best-improvement one-for-one MOF replacements.
- linear_covariance / linear_gradient_K: closed-form error covariance of the sum-to-one least-squares
  estimate and its exact derivative with respect to each MOF/gas Henry coefficient.
- sensitivity_mc: central finite differences of the full simulator with respect to each K entry.
- relaxed_design: continuous relaxation over all candidates (weights in [0,1], sum k), optimized by
  projected gradient on the linearized ethane/ethylene variance, then rounded to the top k.
"""
from __future__ import annotations
import multiprocessing as mp
import os

import numpy as np

from src.sensorsim import B, GASES, load_data, mixtures, noise_sigma, simulate

ETHANE, ETHENE = GASES.index('ethane'), GASES.index('ethene')
RATIO_MIN_FRACTION = .05
RATIO_CAP_PCT = 100.


def target_metrics(X, H):
    """Errors that the week-3 targets are stated in (pp of mole fraction, % for the ratio)."""
    err = 100*np.abs(H-X)
    both = (X[:, ETHANE] >= RATIO_MIN_FRACTION) & (X[:, ETHENE] >= RATIO_MIN_FRACTION)
    actual = X[both, ETHENE]/X[both, ETHANE]
    with np.errstate(divide='ignore', invalid='ignore'):
        estimated = np.where(H[both, ETHANE] > 0, H[both, ETHENE]/H[both, ETHANE], np.inf)
    relative = 100*np.abs(estimated-actual)/actual
    return {'overall_mae_pp': float(err.mean()), 'ethane_mae_pp': float(err[:, ETHANE].mean()),
            'ethene_mae_pp': float(err[:, ETHENE].mean()),
            'ratio_err_pct': float(np.minimum(relative, RATIO_CAP_PCT).mean()),
            'ratio_median_pct': float(np.median(relative)),
            'ratio_within_10pct_frac': float((relative <= 10).mean()),
            'ethene_zeroed_frac': float((H[both, ETHENE] <= 1e-9).mean()),
            'ethane_zeroed_frac': float((H[both, ETHANE] <= 1e-9).mean()),
            'ratio_cases': int(both.sum())}


def score(tm, targets):
    return float(np.mean([tm[name]/limit for name, limit in targets.items()]))


_STATE = {}


def _init(seed, relative, floor, targets):
    ids, K, g, ref = load_data()
    X, _, Z, _ = mixtures(seed)
    _STATE.update(K=K, sigma=noise_sigma(g, ref, relative, floor), X=X, Z=Z, targets=targets)


def _evaluate(indices):
    s = _STATE
    tm = target_metrics(s['X'], simulate(s['K'], s['sigma'], indices, s['X'], s['Z']))
    return score(tm, s['targets']), tm


class Evaluator:
    """Scores arrays on one mixture set in worker processes; results are cached by MOF set."""

    def __init__(self, seed, targets, relative=.01, floor=.001, workers=None):
        for var in ['OMP_NUM_THREADS', 'MKL_NUM_THREADS', 'OPENBLAS_NUM_THREADS', 'VECLIB_MAXIMUM_THREADS']:
            os.environ[var] = '1'
        self.workers = workers or max(1, (os.cpu_count() or 2)-2)
        self.pool = mp.get_context('spawn').Pool(self.workers, initializer=_init, initargs=(seed, relative, floor, targets))
        self.cache = {}
        self.calls = 0

    def __call__(self, arrays):
        keys = [tuple(sorted(int(i) for i in a)) for a in arrays]
        todo = [k for k in dict.fromkeys(keys) if k not in self.cache]
        if todo:
            chunk = max(1, len(todo)//(4*self.workers))
            for key, result in zip(todo, self.pool.map(_evaluate, todo, chunksize=chunk)):
                self.cache[key] = result
            self.calls += len(todo)
        return [self.cache[k] for k in keys]

    def close(self):
        self.pool.close()
        self.pool.join()


def ga(evaluate, pool, rng, seeds=(), k=12, pop_size=64, generations=300, patience=60, elite=4, tournament=3):
    """Minimize the score over k-subsets of pool. Returns (best_indices, best_score, history)."""
    pool = np.asarray(pool)
    population = [tuple(sorted(int(i) for i in s)) for s in seeds]
    while len(population) < pop_size:
        population.append(tuple(sorted(rng.choice(pool, k, replace=False).tolist())))
    scores = np.array([r[0] for r in evaluate(population)])
    best, best_score, stall, history = population[int(scores.argmin())], float(scores.min()), 0, []

    def pick():
        contenders = rng.choice(len(population), tournament, replace=False)
        return population[contenders[np.argmin(scores[contenders])]]

    def crossover(a, b):
        common = sorted(set(a) & set(b))
        rest = sorted((set(a) | set(b))-set(common))
        return common+rng.choice(rest, k-len(common), replace=False).tolist()

    def mutate(child):
        child = list(child)
        for _ in range(1 if rng.random() < .8 else 2):
            outside = np.setdiff1d(pool, child)
            child[int(rng.integers(k))] = int(rng.choice(outside))
        return tuple(sorted(child))

    for generation in range(generations):
        order = np.argsort(scores)
        children = [population[i] for i in order[:elite]]
        while len(children) < pop_size:
            children.append(mutate(crossover(pick(), pick())))
        population = children
        scores = np.array([r[0] for r in evaluate(population)])
        if scores.min() < best_score-1e-12:
            best, best_score, stall = population[int(scores.argmin())], float(scores.min()), 0
        else:
            stall += 1
        history.append({'generation': generation+1, 'best_score': best_score, 'median_score': float(np.median(scores))})
        if stall >= patience:
            break
    return list(best), best_score, history


def swap_search(evaluate, start, pool, max_steps=12):
    """Best-improvement one-for-one replacements until no single swap lowers the score."""
    current = tuple(sorted(int(i) for i in start))
    current_score = evaluate([current])[0][0]
    trace = []
    for step in range(max_steps):
        outside = [int(i) for i in pool if i not in current]
        trials = [tuple(sorted([i for i in current if i != out]+[inn])) for out in current for inn in outside]
        results = evaluate(trials)
        j = int(np.argmin([r[0] for r in results]))
        if results[j][0] >= current_score-1e-9:
            break
        removed = sorted(set(current)-set(trials[j]))[0]
        added = sorted(set(trials[j])-set(current))[0]
        current, current_score = trials[j], results[j][0]
        trace.append({'step': step+1, 'removed': removed, 'added': added, 'score': current_score})
    return list(current), current_score, trace


def linear_covariance(W, ridge=0.):
    """Covariance (unit whitened noise) of the unconstrained sum-to-one least-squares composition."""
    A = W@B
    return B@np.linalg.inv(A.T@A+ridge*np.eye(7))@B.T


def linear_objective(W, gases=(ETHANE, ETHENE)):
    C = linear_covariance(W)
    return float(sum(np.sqrt(C[j, j]) for j in gases))


def linear_gradient_K(K_sel, sigma_sel, gases=(ETHANE, ETHENE)):
    """Exact d(sum of linearized sd over gases)/dK for each MOF/gas entry, noise held fixed.

    With W = K/sigma and C = B (B'W'WB)^-1 B', dC_jj/dW_mg = -2 (W C)_mj C_gj.
    """
    W = K_sel/sigma_sel[:, None]
    C = linear_covariance(W)
    WC = W@C
    grad_W = np.zeros_like(W)
    for j in gases:
        grad_W += (-2*WC[:, [j]]*C[j][None, :])/(2*np.sqrt(C[j, j]))
    return grad_W/sigma_sel[:, None]


def sensitivity_mc(K, sigma, indices, X, Z, metric, step=.05):
    """Elasticity of metric(X, H) to each selected MOF/gas K entry: central differences, fixed noise."""
    indices = list(indices)
    base = metric(X, simulate(K, sigma, indices, X, Z))
    S = np.zeros((len(indices), K.shape[1]))
    for a, m in enumerate(indices):
        for j in range(K.shape[1]):
            up, down = K.copy(), K.copy()
            up[m, j] *= 1+step
            down[m, j] *= 1-step
            delta = metric(X, simulate(up, sigma, indices, X, Z))-metric(X, simulate(down, sigma, indices, X, Z))
            S[a, j] = delta/(2*step)/base
    return S, base


def _project_capped_simplex(v, k):
    lo, hi = v.min()-1, v.max()
    for _ in range(100):
        tau = (lo+hi)/2
        if np.clip(v-tau, 0, 1).sum() > k:
            lo = tau
        else:
            hi = tau
    return np.clip(v-(lo+hi)/2, 0, 1)


def relaxed_design(K, sigma, pool, k=12, gases=(ETHANE, ETHENE), iterations=3000, step=.05, ridge=1e-9):
    """Projected gradient on weights w in [0,1]^n, sum k, minimizing sum_j C_jj(w); returns top-k indices."""
    pool = np.asarray(pool)
    A = (K[pool]/sigma[pool, None])@B
    w = np.full(len(pool), k/len(pool))
    history = []
    for it in range(iterations):
        F = (A.T*w)@A+ridge*np.eye(7)
        M = A@np.linalg.solve(F, B.T)
        objective = float(sum((B@np.linalg.solve(F, B.T))[j, j] for j in gases))
        grad = -(M[:, list(gases)]**2).sum(axis=1)
        w = _project_capped_simplex(w-step*grad/np.abs(grad).max(), k)
        if it % 100 == 0 or it == iterations-1:
            history.append({'iteration': it, 'objective_variance': objective})
    top = pool[np.argsort(-w)[:k]]
    return sorted(int(i) for i in top), w, history
