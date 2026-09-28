"""Regression: the ported simulator must reproduce the week-2 frozen results."""
import json
from pathlib import Path

from src.sensorsim import SEEDS, candidate_pool, design, load_data, metrics, mixtures, noise_sigma, ratios, simulate

WEEK2 = Path(__file__).resolve().parents[1] / 'weeks/02'
TOL = 1e-9


def _week2():
    return json.loads((WEEK2 / 'array_designs.json').read_text()), json.loads((WEEK2 / 'final_summary.json').read_text())


def test_design_reproduces_week2_selection():
    ids, K, g, ref = load_data()
    designs, _ = _week2()
    chosen = design(K, noise_sigma(g, ref), ids, candidate_pool(K))
    assert chosen['mofs'] == designs['primary']['mofs']


def test_simulation_reproduces_week2_final_numbers():
    ids, K, g, ref = load_data()
    designs, summary = _week2()
    X, _, Z, _ = mixtures(SEEDS['final'])
    H = simulate(K, noise_sigma(g, ref), designs['primary']['indices'], X, Z)
    got, want = metrics(X, H), summary['primary']['overall']
    assert abs(got['mae_pp'] - want['mae_pp']) < TOL
    for gas, value in want['per_gas_mae_pp'].items():
        assert abs(got['per_gas_mae_pp'][gas] - value) < TOL
    ratio = ratios(X, H)[0]
    assert ratio['ratio'] == 'ethylene/ethane'
    assert abs(ratio['relative_error_median_pct_positive_product']
               - summary['primary']['ratios'][0]['relative_error_median_pct_positive_product']) < TOL
