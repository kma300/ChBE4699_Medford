"""Week 3 deliverables: two slides (PNG + .pptx) and the Slack draft, every number taken from results.json.

Run from the repo root: python3 weeks/03/deliverables.py   (or: python3 -m src.weekly 3)
"""
import json
import math
import re
import sys
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.slides import C, H, Registry, check_numbers, render, to_pptx  # noqa: E402

HERE = Path(__file__).resolve().parent
r = json.loads((HERE/'results.json').read_text())
R = Registry()


def pp(v): return R.num(v, '{:.2f}')
def pct(v): return R.num(v, '{:.0f}%')
def frac(v): return R.num(v, '{:.0%}')
def num(v, fmt='{}'): return R.num(v, fmt)


def final(name): return r['heldout'][name]['final']['target_metrics']


wk2, swaps, ga, every = final('week2_d_optimal'), final('swap_search'), final('genetic_algorithm'), final('all_464')
fresh_ga, fresh_wk2 = r['heldout']['genetic_algorithm']['fresh']['target_metrics'], r['heldout']['week2_d_optimal']['fresh']['target_metrics']
T, protocol = r['targets'], r['protocol']
day = date.fromisoformat(r['date'])
header = f"KEN MA  /  DR. A. J. MEDFORD  /  {day.strftime('%B').upper()} {num(day.day)}, {num(day.year)}"
k, n_gases, pool = num(protocol['array_size']), num(len(r['sensitivity']['genetic_algorithm']['gases'])), num(protocol['candidate_pool'])
combos = math.comb(protocol['candidate_pool'], protocol['array_size'])
exponent = int(math.floor(math.log10(combos)))
combos_text = f"{num(combos/10**exponent, '{:.1f}')} x 10^{num(exponent)}"
n_mix = num(protocol['mixtures_per_set'], '{:,}')
promised = date.fromisoformat(re.search(r'\d{4}-\d{2}-\d{2}', (ROOT/'weeks/02/slack_thread.md').read_text().split('## Ken', 1)[1]).group())
promised_text = f"{promised.strftime('%B')} {num(promised.day)}"
wk = num(r['week'])
kelvin = num(json.loads((ROOT/'weeks/02/protocol_frozen.json').read_text())['temperature_K'])
overlap = num(r['ga_run_overlap'])
evaluations = num(protocol['development_evaluations'], '{:,}')
sweep = {(row['design'], row['relative_noise']): row for row in r['noise_sweep']}
levels = sorted({row['relative_noise'] for row in r['noise_sweep']}, reverse=True)
base_noise = levels[0]
ga_ok = max(level for level in levels if sweep[('genetic_algorithm', level)]['ethene_mae_pp'] <= T['ethene_mae_pp'])
sens = r['sensitivity']['genetic_algorithm']
top = sens['top_entries'][0]
selectivity = r['ethene_ethane_selectivity']
heldout_scores = {name: r['heldout'][name]['final']['score'] for name in ['gradient_design', 'genetic_algorithm']}
gas_names = ['methane', 'ethane', 'ethylene', 'propane', 'propylene', 'isobutane', 'isopentane', '2-pentene']
top_row = sens['mofs'].index(top['mof'])
assert top['gas'] == 'ethane' and sens['mc_score_elasticity'][top_row][sens['gases'].index('ethene')]*top['elasticity'] < 0, \
    'slide text assumes the top lever is an ethane entry whose ethylene entry pushes the other way'
ALLOWED = {'4', '6'}  # planning-doc goal of a 4-6 MOF array

slide1 = [
    ('header', header),
    ('title', f'Week {wk}: the GA helps, but signal limits ethylene/ethane'),
    ('text', f'Question: can your GA suggestion find {k} MOFs that recover ethylene, ethane and their ratio?', {'size': 25}),
    ('text', f"Targets: ethylene and ethane within {num(T['ethene_mae_pp'], '{:.0f}')} pp, ratio within {pct(T['ratio_err_pct'])}. "
             f"Scored on {n_mix} held-out mixtures at {R.num(base_noise*100, '{:g}%')} sensor noise.", {'size': 21, 'color': C['muted'], 'after': 26}),
    ('table', [f'Promised on {promised_text}', 'Result on held-out mixtures'], [
        ['Refine the objective for ethane/ethylene', 'New score built on these targets, plus an overall guard.'],
        ['Test individual MOF replacements', f"Best single swaps: ethylene {pp(wk2['ethene_mae_pp'])} to {pp(swaps['ethene_mae_pp'])} pp."],
        ['Genetic algorithm (your suggestion)', f"{evaluations} arrays scored: ethylene {pp(ga['ethene_mae_pp'])} pp, ratio error "
                                                 f"{pct(wk2['ratio_err_pct'])} to {pct(ga['ratio_err_pct'])}. Two runs agree on {overlap} of {k} MOFs."]],
     [.36, .64]),
    ('columns', [
        ('heading', 'Ethylene error on held-out mixtures (pp)'),
        ('hbar', {'labels': ['Random median', 'Week 2 array', 'Single swaps', 'Genetic algorithm', f'All {pool} MOFs'],
                  'values': [r['random_baseline_final']['ethene_mae_pp']['median'], wk2['ethene_mae_pp'], swaps['ethene_mae_pp'],
                             ga['ethene_mae_pp'], every['ethene_mae_pp']],
                  'value_labels': [pp(r['random_baseline_final']['ethene_mae_pp']['median']), pp(wk2['ethene_mae_pp']),
                                   pp(swaps['ethene_mae_pp']), pp(ga['ethene_mae_pp']), pp(every['ethene_mae_pp'])],
                  'colors': [C['gray'], '#8DB8F5', '#5E9FF7', C['blue'], C['teal']], 'xmax': 16, 'label_width': 290,
                  'target': T['ethene_mae_pp'], 'target_label': f"target {num(T['ethene_mae_pp'], '{:.0f}')} pp", 'height': 330}),
        ('text', 'The limit is signal, not search', {'size': 25, 'color': C['teal'], 'weight': 'bold', 'after': 6}),
        ('text', f"Even all {pool} MOFs at once only reach {pp(every['ethene_mae_pp'])} pp.", {'size': 21}),
    ], [
        ('heading', 'What limits ethylene/ethane'),
        ('text', f"In {frac(ga['ethene_zeroed_frac'])} of cracker-like mixtures the GA array still reads zero ethylene "
                 f"({frac(every['ethene_zeroed_frac'])} with all {pool} MOFs).", {'size': 21}),
        ('text', f"Ethane outadsorbs ethylene in {frac(selectivity['frac_ethane_stronger'])} of MOFs "
                 f"(median ethylene/ethane Henry ratio {num(selectivity['median'], '{:.2f}')}). "
                 f"The {num(selectivity['n_above_2'])} MOFs that favor ethylene by more than 2x barely adsorb anything.", {'size': 22}),
        ('text', 'Likely cause: D-MOPH is physisorption-only, so metal-site ethylene binding is not in the data.', {'size': 22}),
        ('text', f"The GA gain held on a fresh mixture set: ethylene {pp(fresh_wk2['ethene_mae_pp'])} to {pp(fresh_ga['ethene_mae_pp'])} pp.",
         {'size': 19, 'color': C['muted']}),
    ], .47),
    ('text', 'Next: agree on a realistic sensor noise level, then prune toward 4-6 MOFs before the midterm.', {'size': 26, 'weight': 'bold', 'after': 22}),
    ('text', f'Model limits: computed {kelvin} K dilute-limit coefficients, assumed noise, fractions normalized over eight gases. '
             'All designs were selected on development mixtures only.', {'size': 17, 'color': C['muted']}),
]

M = sens['mc_score_elasticity']
order = sorted(((abs(M[i][j]), i, j) for i in range(len(M)) for j in range(len(M[0]))), reverse=True)[:3]
annotations = {(i, j): num(M[i][j], '{:.2f}') for _, i, j in order}
ga_needed_ratio = sweep[('genetic_algorithm', ga_ok)]['ratio_err_pct']
slide2 = [
    ('header', header),
    ('title', f'Week {wk}: your gradient idea shows where the error comes from'),
    ('text', f'Which of the {k}x{n_gases} Henry coefficients move the error most, and what noise would the targets need?',
     {'size': 25, 'after': 30}),
    ('columns', [
        ('heading', 'Error change per +1% in each coefficient'),
        ('heatmap', {'matrix': M, 'rows': sens['mofs'], 'cols': gas_names, 'annotations': annotations, 'height': 560,
                     'label_width': 150}),
        ('text', 'GA array. Finite differences of the full simulator, noise draws held fixed. Blue: raising that coefficient lowers the error.',
         {'size': 17, 'color': C['muted']}),
    ], [
        ('heading', 'Ethylene error vs. sensor noise (pp)'),
        ('line', {'x': [level*100 for level in levels], 'x_labels': [R.num(level*100, '{:g}%') for level in levels],
                  'series': [{'label': 'Week 2', 'color': C['gray'], 'y': [sweep[('week2_d_optimal', lv)]['ethene_mae_pp'] for lv in levels]},
                             {'label': 'GA', 'color': C['blue'], 'y': [sweep[('genetic_algorithm', lv)]['ethene_mae_pp'] for lv in levels]},
                             {'label': f'All {pool}', 'color': C['teal'], 'y': [sweep[('all_464', lv)]['ethene_mae_pp'] for lv in levels]}],
                  'x_title': 'noise, % of each MOF full scale', 'y_title': 'ethylene error (pp)', 'height': 420,
                  'target': T['ethene_mae_pp'], 'target_label': f"target {num(T['ethene_mae_pp'], '{:.0f}')} pp"}),
        ('text', f"The GA array reaches the ethylene target only at {R.num(ga_ok*100, '{:g}%')} noise, "
                 f"{num(base_noise/ga_ok, '{:.0f}')}x below the week-2 assumption. The ratio target is still missed there "
                 f"({pct(ga_needed_ratio)} error).", {'size': 21}),
    ], .52),
    ('text', f"Biggest lever: {top['mof']}'s {gas_names[r['sensitivity']['genetic_algorithm']['gases'].index(top['gas'])]} coefficient "
             f"(+1% changes the error score by {num(top['elasticity'], '{:.2f}')}%), while its ethylene coefficient pushes the other way. "
             'The array needs ethane-vs-ethylene contrast, which D-MOPH rarely offers.', {'size': 22}),
    ('text', 'A closed-form gradient of a linearized error matched finite differences but only loosely tracked the real constrained solver '
             f"(rank correlation {num(sens['spearman_linear_vs_mc'], '{:.2f}')}); selecting with it scored worse than the GA "
             f"({num(heldout_scores['gradient_design'], '{:.2f}')} vs {num(heldout_scores['genetic_algorithm'], '{:.2f}')}). "
             'Next for your idea: differentiate the actual solver.', {'size': 22}),
    ('text', 'Question for you: what noise level is realistic for MOF sensors? It decides whether to push the ratio or '
             'lump ethane and ethylene into one signal.', {'size': 24, 'weight': 'bold', 'after': 22}),
    ('text', 'Error score: mean over targets of error divided by target, lower is better. Held-out and fresh mixture sets were never used for selection.',
     {'size': 17, 'color': C['muted']}),
]

slack = f"""Hi Dr. Medford, sorry for the slow reply, I was out visiting customer pilot plants last week. Answers to your questions:

1. Selection: greedy D-optimal design. From the {pool} MOFs that respond at all, I added one MOF at a time to maximize the log-determinant of the noise-weighted Fisher information (the {k}x{n_gases} response matrix projected onto the {num(len(gas_names)-1)} independent composition directions, since fractions sum to 1), then did one-for-one swaps until nothing improved.
2. Simulation: each MOF's signal is its Henry coefficients times the mole fractions (dilute limit), plus Gaussian noise at {R.num(base_noise*100, '{:g}%')} of that MOF's full-scale response (with a small floor). I recover the composition with exact nonnegative, sum-to-one least squares and score {n_mix} held-out mixtures (all {n_gases} gases, 2-7 gas subsets, and ethane/ethylene and propane/propylene ratio sweeps). Designs are picked on a separate development set.

This week I tried both of your suggestions (slides attached):
- GA over {k} of {pool} MOFs (about {combos_text} combinations): ethylene error went from {pp(wk2['ethene_mae_pp'])} to {pp(ga['ethene_mae_pp'])} pp on held-out mixtures and held up on a fresh set. But even all {pool} MOFs at once only reach {pp(every['ethene_mae_pp'])} pp, so at {R.num(base_noise*100, '{:g}%')} noise the limit looks like signal rather than search.
- Gradient map: the error hinges on the ethane/ethylene contrast of a few MOFs (mostly {top['mof']}). In D-MOPH, ethane outadsorbs ethylene in {frac(selectivity['frac_ethane_stronger'])} of MOFs (median ratio {num(selectivity['median'], '{:.2f}')}), and the MOFs that favor ethylene barely adsorb. Steering the selection with a linearized gradient did worse than the GA, so next I'd differentiate the actual constrained solver.
- Ethylene only reaches my {num(T['ethene_mae_pp'], '{:.0f}')} pp target at about {R.num(ga_ok*100, '{:g}%')} noise.

Question: what noise level is realistic for MOF sensors? That decides whether I keep pushing the ethylene/ethane ratio or treat ethane and ethylene as one signal and prune toward 4-6 MOFs before the midterm.
"""

outputs, overflow, texts = [], [], []
for i, blocks in enumerate([slide1, slide2], start=1):
    png = HERE/f'week3_slide_{i}.png'
    slide_texts, bottom = render(blocks, png)
    texts += slide_texts
    overflow.append(max(0., bottom-(H-30)))
    outputs.append(str(png.relative_to(ROOT)))
to_pptx([ROOT/p for p in outputs], HERE/'week3_update.pptx')
(HERE/'slack_draft.md').write_text(slack)
outputs += [str((HERE/'week3_update.pptx').relative_to(ROOT)), str((HERE/'slack_draft.md').relative_to(ROOT))]
check = {'slides': 2, 'overflow_px': overflow, 'untraced_numbers': check_numbers(texts+[slack], R, ALLOWED), 'outputs': outputs}
(HERE/'deliverables_check.json').write_text(json.dumps(check, indent=2)+'\n')
print(json.dumps(check, indent=2))
