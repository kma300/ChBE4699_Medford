"""Week 3: can a target-driven search fix ethylene/ethane? (Medford's GA and gradient suggestions)

Every design sees only the development mixtures (seed 20260921, as in week 2). Reported numbers come
from the held-out week-2 final set (seed 20260922) and a fresh set (seed 20260928).
Run from the repo root: python3 weeks/03/experiment.py
"""
import json
import platform
import sys
import time
from pathlib import Path

import numpy as np
from scipy.stats import spearmanr

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.search import (ETHANE, ETHENE, RATIO_CAP_PCT, RATIO_MIN_FRACTION, Evaluator, ga, linear_covariance,  # noqa: E402
                        linear_gradient_K, linear_objective, relaxed_design, score, sensitivity_mc, swap_search,
                        target_metrics)
from src.sensorsim import GASES, SEEDS, candidate_pool, load_data, metrics, mixtures, noise_sigma, ratios, save_json, simulate  # noqa: E402

HERE = Path(__file__).resolve().parent
WEEK2 = ROOT/'weeks/02'
FRESH_SEED = 20260928
GA_RNG_SEEDS = [3, 4]
TARGETS = {'ethene_mae_pp': 2., 'ethane_mae_pp': 2., 'ratio_err_pct': 10., 'overall_mae_pp': 2.}
NOISE_LEVELS = [.01, .005, .002, .001, .0005]
FLOOR_TO_RELATIVE = .1  # week 2: 1% relative with a 0.1% floor


def summarize(values):
    values = np.asarray(values, float)
    return {'median': float(np.median(values)), 'p05': float(np.quantile(values, .05)),
            'p95': float(np.quantile(values, .95)), 'min': float(values.min())}


def main():
    started = time.time()
    ids, K, g, ref = load_data()
    sigma = noise_sigma(g, ref)
    pool = candidate_pool(K)
    week2 = sorted(json.loads((WEEK2/'array_designs.json').read_text())['primary']['indices'])
    random_arrays = np.load(WEEK2/'random_arrays.npy')
    sets = {'development': mixtures(SEEDS['development']), 'final': mixtures(SEEDS['final']), 'fresh': mixtures(FRESH_SEED)}

    evaluate = Evaluator(SEEDS['development'], TARGETS)
    designs, logs = {'week2_d_optimal': week2}, {}
    designs['swap_search'], _, logs['swap_search_trace'] = swap_search(evaluate, week2, pool)
    designs['gradient_design'], weights, logs['gradient_design_history'] = relaxed_design(K, sigma, pool)
    ga_runs = []
    for seed in GA_RNG_SEEDS:
        best, best_score, history = ga(evaluate, pool, np.random.default_rng(seed), seeds=[week2],
                                       generations=400, patience=80)
        ga_runs.append({'rng_seed': seed, 'indices': sorted(best), 'development_score': best_score,
                        'generations': len(history), 'history': history[::10]+history[-1:]})
    ga_best = min(ga_runs, key=lambda run: run['development_score'])
    polished, _, logs['ga_polish_trace'] = swap_search(evaluate, ga_best['indices'], pool)
    designs['genetic_algorithm'] = sorted(polished)
    development = {name: dict(zip(['score', 'target_metrics'], evaluate([ix])[0])) for name, ix in designs.items()}
    evaluations = evaluate.calls
    evaluate.close()

    def assess(ix, set_name, relative=.01):
        X, _, Z, _ = sets[set_name]
        H = simulate(K, noise_sigma(g, ref, relative, relative*FLOOR_TO_RELATIVE), ix, X, Z)
        tm = target_metrics(X, H)
        m = metrics(X, H)
        return {'score': score(tm, TARGETS), 'target_metrics': tm, 'overall_mae_pp': m['mae_pp'],
                'per_gas_mae_pp': m['per_gas_mae_pp'], 'week2_style_ratios': ratios(X, H)}

    evaluated = dict(designs, all_464=pool.tolist())
    heldout = {name: {s: assess(ix, s) for s in ['final', 'fresh']} for name, ix in evaluated.items()}
    random_final = [assess(ix, 'final') for ix in random_arrays]
    random_baseline = {key: summarize([r['target_metrics'][key] for r in random_final]) for key in TARGETS}
    random_baseline['score'] = summarize([r['score'] for r in random_final])
    for name in designs:
        random_baseline[f'{name}_beats_n_of_200'] = int(sum(heldout[name]['final']['score'] < r['score'] for r in random_final))

    noise_sweep = [{'design': name, 'relative_noise': level, **assess(evaluated[name], 'final', level)['target_metrics']}
                   for name in ['week2_d_optimal', 'genetic_algorithm', 'all_464'] for level in NOISE_LEVELS]

    def meets(row):
        return all(row[key] <= limit for key, limit in TARGETS.items())
    noise_needed = {name: max([r['relative_noise'] for r in noise_sweep if r['design'] == name and meets(r)], default=None)
                    for name in ['week2_d_optimal', 'genetic_algorithm', 'all_464']}

    X, _, Z, _ = sets['development']
    def pair_mae(X, H):
        return float(100*np.abs(H-X)[:, [ETHANE, ETHENE]].mean(axis=1).mean())
    def target_score(X, H):
        return score(target_metrics(X, H), TARGETS)
    sensitivity = {}
    for name in ['week2_d_optimal', 'genetic_algorithm']:
        ix = designs[name]
        mc_score, base_score = sensitivity_mc(K, sigma, ix, X, Z, target_score)
        mc_pair, base_pair = sensitivity_mc(K, sigma, ix, X, Z, pair_mae)
        grad = linear_gradient_K(K[ix], sigma[ix])
        f_lin = linear_objective(K[ix]/sigma[ix, None])
        linear_elasticity = K[ix]*grad/f_lin
        fd = np.zeros_like(grad)  # finite-difference check of the closed-form gradient
        for a in range(len(ix)):
            for j in range(8):
                up, down = K[ix].copy(), K[ix].copy()
                step = 1e-6*max(K[ix][a, j], 1e-6*K[ix].max())
                up[a, j] += step
                down[a, j] -= step
                fd[a, j] = (linear_objective(up/sigma[ix, None])-linear_objective(down/sigma[ix, None]))/(2*step)
        checked = np.abs(grad) > 1e-6*np.abs(grad).max()
        rel_diff = np.abs(fd-grad)[checked]/np.abs(grad)[checked]
        order = np.argsort(-np.abs(mc_score).ravel())[:5]
        sensitivity[name] = {'mofs': ids[ix].tolist(), 'gases': GASES,
                             'mc_score_elasticity': mc_score.tolist(), 'base_score': base_score,
                             'mc_ethane_ethene_elasticity': mc_pair.tolist(), 'base_ethane_ethene_mae_pp': base_pair,
                             'linear_elasticity': linear_elasticity.tolist(),
                             'gradient_fd_max_rel_diff': float(rel_diff.max()),
                             'spearman_linear_vs_mc': float(spearmanr(linear_elasticity.ravel(), mc_pair.ravel())[0]),
                             'top_entries': [{'mof': str(ids[ix][i//8]), 'gas': GASES[i % 8],
                                              'elasticity': float(mc_score.ravel()[i])} for i in order]}

    ratio = K[pool, ETHENE]/np.maximum(K[pool, ETHANE], 1e-300)
    selective = pool[ratio > 2]
    linear_sd = {name: (100*np.sqrt(np.diag(linear_covariance(K[ix]/sigma[ix, None])))).tolist()
                 for name, ix in evaluated.items()}
    results = {
        'week': 3, 'date': '2026-09-28', 'runtime_s': round(time.time()-started, 1),
        'question': 'Can a target-driven search (GA, swaps, gradient design) fix ethylene/ethane recovery?',
        'targets': TARGETS,
        'target_definitions': {
            'ethene_mae_pp': 'mean |error| of the ethylene mole fraction, percentage points, all 1,000 mixtures',
            'ethane_mae_pp': 'same for ethane', 'overall_mae_pp': 'mean |error| over all 8 gases (guard)',
            'ratio_err_pct': f'mean relative error of ethylene/ethane, capped at {RATIO_CAP_PCT:.0f}%, over mixtures with both >= {RATIO_MIN_FRACTION:.0%}'},
        'score': 'mean over targets of metric/target (1.0 = exactly on target)',
        'protocol': {'noise': '1% of each MOF full scale, floor 0.1% of median full scale (week 2)',
                     'development_seed': SEEDS['development'], 'final_seed': SEEDS['final'], 'fresh_seed': FRESH_SEED,
                     'candidate_pool': int(len(pool)), 'array_size': 12, 'development_evaluations': evaluations,
                     'mixtures_per_set': int(len(sets['final'][0])),
                     'ga': {'population': 64, 'max_generations': 400, 'patience': 80, 'elite': 4, 'tournament': 3,
                            'mutation': '1 swap (80%) or 2 swaps', 'seeded_with': 'week-2 array', 'rng_seeds': GA_RNG_SEEDS},
                     'versions': {'python': platform.python_version(), 'numpy': np.__version__}},
        'designs': {name: {'indices': ix, 'mofs': ids[ix].tolist()} for name, ix in designs.items()},
        'development': development, 'heldout': heldout, 'random_baseline_final': random_baseline,
        'ga_runs': ga_runs, 'ga_run_overlap': len(set(ga_runs[0]['indices']) & set(ga_runs[1]['indices'])),
        'logs': logs, 'noise_sweep': noise_sweep, 'max_noise_meeting_all_targets': noise_needed,
        'linear_sd_pp': linear_sd, 'sensitivity': sensitivity,
        'ethene_ethane_selectivity': {'median': float(np.median(ratio)), 'p95': float(np.quantile(ratio, .95)),
                                      'frac_ethane_stronger': float((ratio < 1).mean()),
                                      'n_above_2': int((ratio > 2).sum()), 'n_above_5': int((ratio > 5).sum()),
                                      'selective_full_scale_vs_median': summarize(g[selective]/ref),
                                      'selective_in_design': {name: int(len(set(ix) & set(selective.tolist())))
                                                              for name, ix in designs.items()}},
    }
    save_json(HERE/'results.json', results)
    print(json.dumps({name: {k: round(v, 2) for k, v in heldout[name]['final']['target_metrics'].items() if isinstance(v, float)}
                      for name in evaluated}, indent=1))
    print('runtime_s', results['runtime_s'], 'evaluations', evaluations)


if __name__ == '__main__':
    main()
