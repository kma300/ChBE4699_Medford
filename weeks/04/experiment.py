"""Week 4: how much sensor noise can the array take, and does the best known ethylene-selective material fix ethylene?

Answers Dr. Medford's Slack message of 2026-09-29:
1. Keep 1% noise for selection, then treat noise as a sensitivity variable: sweep it on the selected arrays and find the
   noise at which each gas breaks down, instead of fixing one noise level.
2. Ethane vs ethylene: do a literature search for ethylene-selective materials and put the best known one into the array.
   If nothing helps, accept the current floor.

The literature materials are modeled as a 13th sensor added to the week-3 genetic-algorithm array (12 MOFs):
- 'sieve' (UTSA-280-like molecular sieve): responds to ethylene only. Ethane is excluded, and so is every larger panel gas.
  Variants 'sieve_methane_*': the paper reports no methane uptake number, so the sieve also responds to methane at 10%,
  30% or 100% (pessimistic) of its ethylene response.
- 'metal' (open-metal-site or Ag(I) pi-complexation adsorbent with ethylene/ethane selectivity S): a real D-MOPH framework
  whose ethylene coefficient is raised to S times its ethane coefficient. Variant 'olefin': propene is also raised to
  S times propane, because the same sites bind every olefin. The framework is chosen on development mixtures only; the
  spread over all candidate frameworks is reported too.

Selection only ever sees development seed 20260921. Reported numbers use the held-out week-2 final set (20260922) and a
fresh set (20261011). Run from the repo root: python3 weeks/04/experiment.py
"""
import json
import multiprocessing as mp
import os
import platform
import sys
import time
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.search import ETHANE, ETHENE, score, target_metrics  # noqa: E402
from src.sensorsim import GASES, SEEDS, candidate_pool, load_data, mixtures, noise_sigma, save_json, simulate  # noqa: E402

HERE = Path(__file__).resolve().parent
WEEK3 = ROOT/'weeks/03'
FRESH_SEED = 20261011
TARGETS = {'ethene_mae_pp': 2., 'ethane_mae_pp': 2., 'ratio_err_pct': 10., 'overall_mae_pp': 2.}  # week-3 targets
NOISE_LEVELS = [.0005, .001, .002, .005, .01, .02, .05, .1, .2]
REALISTIC = [.05, .1]  # Medford: 1% is likely optimistic, 5-10% probably more realistic
FLOOR_TO_RELATIVE = .1  # week-2 rule: noise floor is 10% of the relative level
BREAKDOWN_FRACTION = .5  # a gas has broken down once its error reaches half of the no-sensor error
SELECTIVITIES = [2, 5, 10, 27, 125, 1000]
OLEFIN_SELECTIVITIES = [27, 125]
METHANE, PROPANE, PROPENE = GASES.index('methane'), GASES.index('propane'), GASES.index('propene')
ADDED = 471  # row index of the added sensor in the augmented coefficient matrix

LITERATURE = [
    {'material': 'UTSA-280, Ca(C4O4)(H2O)', 'mechanism': 'molecular sieving', 'selectivity_low': 10000, 'selectivity_high': None,
     'finding': 'apparent ethylene/ethane selectivity exceeding 10,000: ethylene 2.5 mmol/g vs ethane 0.098 mmol/g at 298 K and '
                '1 bar; apertures 3.2 x 4.5 and 3.8 x 3.8 A; no methane uptake number given (breakthrough enriches ethylene '
                'from a CH4/C2H4/C2H6/C3H8 mixture)',
     'source': 'R.-B. Lin et al., Nature Materials 17, 1128-1133 (2018)', 'url': 'https://doi.org/10.1038/s41563-018-0206-2'},
    {'material': 'PAF-1-SO3Ag', 'mechanism': 'Ag(I) pi-complexation', 'selectivity_low': 27, 'selectivity_high': 125,
     'finding': 'IAST ethylene/ethane selectivity 27 to 125 (equimolar, 296 K); ethylene heat of adsorption over 100 kJ/mol '
                'at low loading',
     'source': 'B. Li et al., J. Am. Chem. Soc. 136, 8654-8660 (2014)', 'url': 'https://www.osti.gov/biblio/1158989'},
    {'material': 'Fe2(dobdc) (Fe-MOF-74)', 'mechanism': 'open Fe(II) metal sites', 'selectivity_low': None,
     'selectivity_high': None, 'finding': 'separates ethylene/ethane and propylene/propane mixtures at 318 K',
     'source': 'E. D. Bloch et al., Science 335, 1606-1610 (2012)', 'url': 'https://doi.org/10.1126/science.1217544'},
]
NOISE_LITERATURE = {'assumed_relative_noise': .05, 'source': 'B. A. Day and C. E. Wilmer, Sensors 20, 924 (2020)',
                    'url': 'https://doi.org/10.3390/s20030924',
                    'note': 'genetic-algorithm MOF array design; noise modeled as a standard deviation of 5% of the signal'}


def extra_noise(seed):
    """Noise draws for the added sensor, independent of the 471 week-2 columns."""
    return np.random.default_rng([seed, 4]).standard_normal((1000, 1))


def load_sets():
    sets = {}
    for name, seed in [('development', SEEDS['development']), ('final', SEEDS['final']), ('fresh', FRESH_SEED)]:
        X, family, Z, _ = mixtures(seed)
        sets[name] = (X, family, np.hstack([Z, extra_noise(seed)]))
    return sets


def augmented(K, row):
    extra = np.zeros(K.shape[1]) if row is None else np.asarray(row, float)
    return np.vstack([K, extra])


def run(K_aug, ix, X, Z_aug, relative, ref):
    sigma = noise_sigma(K_aug.max(axis=1), ref, relative, relative*FLOOR_TO_RELATIVE)
    return simulate(K_aug, sigma, list(ix), X, Z_aug)


def sensor_row(K, ref, kind, template=None, S=None):
    row = np.zeros(K.shape[1])
    if kind == 'sieve':
        row[ETHENE] = ref
    elif kind == 'sieve_methane':  # S carries the methane response as a fraction of the ethylene response
        row[ETHENE] = ref
        row[METHANE] = S*ref
    else:  # 'metal' or 'olefin': a real framework with ethylene (and for 'olefin' also propene) raised by selectivity S
        row = K[template].copy()
        row[ETHENE] = S*row[ETHANE]
        if kind == 'olefin':
            row[PROPENE] = S*row[PROPANE]
    return row


def evaluation(X, H, baseline):
    err = 100*np.abs(H-X)
    c2 = 100*np.abs((H[:, ETHANE]+H[:, ETHENE])-(X[:, ETHANE]+X[:, ETHENE]))
    tm = target_metrics(X, H)
    s = score(tm, TARGETS)
    tm = {k: (None if isinstance(v, float) and not np.isfinite(v) else v) for k, v in tm.items()}  # JSON-safe
    return {'per_gas_mae_pp': dict(zip(GASES, err.mean(axis=0).tolist())),
            'fraction_of_no_sensor': dict(zip(GASES, (err.mean(axis=0)/baseline).tolist())),
            'c2_lumped_mae_pp': float(c2.mean()), 'score': s, 'target_metrics': tm}


def crossing(levels, values, threshold):
    """Noise level at which values first reach threshold, interpolated linearly in log10(noise)."""
    if values[0] >= threshold:
        return {'noise': levels[0], 'bound': 'below_grid'}
    for (l0, v0), (l1, v1) in zip(zip(levels, values), zip(levels[1:], values[1:])):
        if v1 >= threshold:
            t = (threshold-v0)/(v1-v0)
            return {'noise': float(10**(np.log10(l0)+t*(np.log10(l1)-np.log10(l0)))), 'bound': 'interpolated'}
    return {'noise': levels[-1], 'bound': 'above_grid'}


_W = {}


def _init(designs_ix, rows_needed):
    for var in ['OMP_NUM_THREADS', 'MKL_NUM_THREADS', 'OPENBLAS_NUM_THREADS', 'VECLIB_MAXIMUM_THREADS']:
        os.environ[var] = '1'
    ids, K, g, ref = load_data()
    _W.update(K=K, ref=ref, sets=load_sets(), ga=designs_ix)


def _template_job(job):
    """Ethylene error of the GA array plus one metal-site sensor built on one framework."""
    kind, S, template, set_name, relative = job
    K, ref = _W['K'], _W['ref']
    X, _, Z = _W['sets'][set_name]
    row = sensor_row(K, ref, kind, template, S)
    H = run(augmented(K, row), _W['ga']+[ADDED], X, Z, relative, ref)
    tm = target_metrics(X, H)
    return float(tm['ethene_mae_pp']), score(tm, TARGETS)


def main():
    started = time.time()
    ids, K, g, ref = load_data()
    pool = candidate_pool(K)
    r3 = json.loads((WEEK3/'results.json').read_text())
    ga = sorted(r3['designs']['genetic_algorithm']['indices'])
    sets = load_sets()
    Xdev = sets['development'][0]
    baseline = {name: 100*np.abs(sets[name][0]-Xdev.mean(axis=0)).mean(axis=0) for name in sets}

    # Part B first (the noise sweep below reuses the chosen frameworks): metal-site sensors on every candidate framework.
    workers = max(1, (os.cpu_count() or 2))
    jobs = [('metal', S, int(t), 'development', .01) for S in SELECTIVITIES for t in pool]
    jobs += [('olefin', S, int(t), 'development', .01) for S in OLEFIN_SELECTIVITIES for t in pool]
    jobs += [('metal', 27, int(t), 'final', .01) for t in pool]  # spread over frameworks on held-out mixtures
    with mp.get_context('spawn').Pool(workers, initializer=_init, initargs=(ga, None)) as p:
        out = p.map(_template_job, jobs, chunksize=max(1, len(jobs)//(8*workers)))
    table = {job: res for job, res in zip(jobs, out)}

    def best_template(kind, S):
        dev = [(table[(kind, S, int(t), 'development', .01)][0], int(t)) for t in pool]
        return min(dev)[1]

    configs = {}
    for S in SELECTIVITIES:
        configs[f'metal_S{S}'] = ('metal', S, best_template('metal', S))
    for S in OLEFIN_SELECTIVITIES:
        configs[f'olefin_S{S}'] = ('olefin', S, best_template('olefin', S))
    configs['sieve'] = ('sieve', None, None)
    for fraction in [.1, .3, 1.]:
        configs[f'sieve_methane_{fraction*100:.0f}'] = ('sieve_methane', fraction, None)

    def design_rows():
        rows = {'ga': None}
        for name, (kind, S, t) in configs.items():
            rows[f'ga+{name}'] = sensor_row(K, ref, kind, t, S)
        return rows
    rows = design_rows()

    def assess(name, set_name, relative):
        row = rows[name]
        ix = ga if row is None else ga+[ADDED]
        X, _, Z = sets[set_name]
        return evaluation(X, run(augmented(K, row), ix, X, Z, relative, ref), baseline[set_name])

    selectivity_sweep = {name: {s: {f'{lvl:g}': assess(name, s, lvl) for lvl in [.01]+REALISTIC} for s in ['final', 'fresh']}
                         for name in rows}
    final27 = np.array([table[('metal', 27, int(t), 'final', .01)][0] for t in pool])
    spread = {'median': float(np.median(final27)), 'p10': float(np.quantile(final27, .1)), 'p90': float(np.quantile(final27, .9)),
              'min': float(final27.min()), 'n_frameworks': int(len(pool)),
              'n_below_ga': int((final27 < selectivity_sweep['ga']['final']['0.01']['target_metrics']['ethene_mae_pp']).sum())}

    # Part A: noise as a sensitivity variable on the selected arrays.
    sweep_designs = ['ga', 'ga+sieve', 'ga+metal_S27', 'ga+olefin_S27']
    noise_sweep = {name: {s: [assess(name, s, lvl) for lvl in NOISE_LEVELS] for s in ['final', 'fresh']} for name in sweep_designs}
    limits = {}
    for name in sweep_designs:
        rows_final = noise_sweep[name]['final']
        limits[name] = {
            gas: {'breakdown': crossing(NOISE_LEVELS, [r['fraction_of_no_sensor'][gas] for r in rows_final], BREAKDOWN_FRACTION),
                  'two_pp': crossing(NOISE_LEVELS, [r['per_gas_mae_pp'][gas] for r in rows_final], TARGETS['ethene_mae_pp'])}
            for gas in GASES}
        limits[name]['c2_lumped_two_pp'] = crossing(NOISE_LEVELS, [r['c2_lumped_mae_pp'] for r in rows_final], 2.)

    # Part D: prune toward the 4-6 MOF planning goal. Backward elimination on development mixtures at 1% noise.
    def prune(start, row):
        current = list(start)
        K_aug = augmented(K, row)
        X, _, Z = sets['development']
        path = []
        def dev_score(ix):
            return score(target_metrics(X, run(K_aug, ix, X, Z, .01, ref)), TARGETS)
        while len(current) > 7:
            trials = [[i for i in current if i != out] for out in current]
            scores_ = [dev_score(ix) for ix in trials]
            j = int(np.argmin(scores_))
            removed = current[j]
            current = trials[j]
            Xf, _, Zf = sets['final']
            ev = evaluation(Xf, run(K_aug, current, Xf, Zf, .01, ref), baseline['final'])
            path.append({'size': len(current), 'removed': 'added sensor' if removed == ADDED else str(ids[removed]),
                         'development_score': scores_[j], 'final': ev})
        return path
    pruning = {'ga': prune(ga, None), 'ga+sieve': prune(ga+[ADDED], rows['ga+sieve'])}

    ratio = K[pool, ETHENE]/np.maximum(K[pool, ETHANE], 1e-300)
    results = {
        'week': 4, 'date': '2026-10-11', 'runtime_s': round(time.time()-started, 1),
        'question': 'How much noise can the array take, and does the best known ethylene-selective material fix ethylene?',
        'targets': TARGETS,
        'protocol': {'noise': 'relative to each sensor full scale, floor 10% of the relative level times the median full scale',
                     'noise_levels': NOISE_LEVELS, 'realistic_noise': REALISTIC, 'breakdown_fraction': BREAKDOWN_FRACTION,
                     'breakdown_definition': 'noise at which a gas error reaches half of the no-sensor error (always guessing '
                                             'the development-set mean composition), interpolated in log noise',
                     'development_seed': SEEDS['development'], 'final_seed': SEEDS['final'], 'fresh_seed': FRESH_SEED,
                     'candidate_frameworks': int(len(pool)), 'base_array': 'week-3 genetic algorithm array (12 MOFs)',
                     'selectivities': SELECTIVITIES, 'olefin_selectivities': OLEFIN_SELECTIVITIES,
                     'mixtures_per_set': 1000, 'simulations': len(jobs),
                     'versions': {'python': platform.python_version(), 'numpy': np.__version__}},
        'base_array': {'indices': ga, 'mofs': ids[ga].tolist()},
        'no_sensor_mae_pp': {name: dict(zip(GASES, b.tolist())) for name, b in baseline.items()},
        'added_sensors': {name: {'kind': kind, 'selectivity': S, 'framework': None if t is None else str(ids[t]),
                                 'framework_ethene_ethane_dmoph': None if t is None else float(K[t, ETHENE]/K[t, ETHANE])}
                          for name, (kind, S, t) in configs.items()},
        'selectivity_sweep': selectivity_sweep, 'metal_S27_framework_spread_final': spread,
        'noise_sweep': noise_sweep, 'noise_limits': limits, 'pruning': pruning,
        'dmoph_ethene_ethane': {'frac_ethane_stronger': float((ratio < 1).mean()), 'max': float(ratio.max()),
                                'n_above_27': int((ratio > 27).sum())},
        'literature': LITERATURE, 'noise_literature': NOISE_LITERATURE,
    }
    save_json(HERE/'results.json', results)
    brief = {name: {lvl: round(v['target_metrics']['ethene_mae_pp'], 2) for lvl, v in d['final'].items()}
             for name, d in selectivity_sweep.items()}
    print(json.dumps(brief, indent=1))
    print('runtime_s', results['runtime_s'])


if __name__ == '__main__':
    main()
