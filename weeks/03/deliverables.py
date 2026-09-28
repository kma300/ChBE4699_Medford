"""Week 3 deliverables: a one-page summary card (PDF + PNG) and a TL;DR Slack message.

The card answers Dr. Medford's two questions and summarizes the week; the Slack text is only the TL;DR.
Every number comes from results.json or the frozen week-2 protocol.
Run from the repo root: python3 weeks/03/deliverables.py   (or: python3 -m src.weekly 3)
"""
import json
import math
import sys
from datetime import date
from pathlib import Path

from matplotlib.backends.backend_pdf import PdfPages

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.slides import C, H, Registry, check_numbers, render  # noqa: E402

HERE = Path(__file__).resolve().parent
r = json.loads((HERE/'results.json').read_text())
frozen = json.loads((ROOT/'weeks/02/protocol_frozen.json').read_text())
R = Registry()
ALLOWED = {'4', '6'}  # planning-doc goal of a 4-6 MOF array


def pp(v): return R.num(v, '{:.2f}')
def pct(v): return R.num(v, '{:.0f}%')
def frac(v): return R.num(v, '{:.0%}')
def num(v, fmt='{}'): return R.num(v, fmt)
def noise(level): return R.num(level*100, '{:g}%')


def final(name): return r['heldout'][name]['final']['target_metrics']


wk2, swaps, ga, every = final('week2_d_optimal'), final('swap_search'), final('genetic_algorithm'), final('all_464')
T, protocol, selectivity = r['targets'], r['protocol'], r['ethene_ethane_selectivity']
sens = r['sensitivity']['genetic_algorithm']
top = sens['top_entries'][0]
assert top['gas'] == 'ethane', 'card text names the top lever as an ethane coefficient'

day = date.fromisoformat(r['date'])
header = f"KEN MA  /  DR. A. J. MEDFORD  /  {day.strftime('%B').upper()} {num(day.day)}, {num(day.year)}"
wk = num(r['week'])
k, pool = num(protocol['array_size']), num(protocol['candidate_pool'])
combos = math.comb(protocol['candidate_pool'], protocol['array_size'])
exponent = int(math.floor(math.log10(combos)))
SUPERSCRIPT = str.maketrans('0123456789', '\u2070\u00b9\u00b2\u00b3\u2074\u2075\u2076\u2077\u2078\u2079')
combos_text = f"{num(combos/10**exponent, '{:.1f}')} \u00d7 10{num(exponent).translate(SUPERSCRIPT)}"
n_mix = num(protocol['mixtures_per_set'], '{:,}')
evaluations = num(protocol['development_evaluations'], '{:,}')
base_noise = frozen['primary_relative_full_scale_noise']
sweep = {(row['design'], row['relative_noise']): row for row in r['noise_sweep']}
levels = sorted({row['relative_noise'] for row in r['noise_sweep']}, reverse=True)
ga_ok = max(level for level in levels if sweep[('genetic_algorithm', level)]['ethene_mae_pp'] <= T['ethene_mae_pp'])
fresh_wk2, fresh_ga = (r['heldout'][name]['fresh']['target_metrics']['ethene_mae_pp'] for name in ['week2_d_optimal', 'genetic_algorithm'])
body = {'size': 21, 'after': 16}

card = [
    ('header', header),
    ('title', f'Week {wk}: the GA helps, but signal limits ethylene/ethane'),
    ('table', ['Your question or idea', 'Answer'], [
        ['Selection method?',
         f"Greedy D-optimal design: add one of the {pool} responsive MOFs at a time to maximize log det of the noise-weighted "
         'Fisher information, then swap one-for-one until nothing improves.'],
        ['Detection simulation?',
         f"Signal = Henry coefficients \u00d7 mole fractions, plus {noise(base_noise)} noise. Composition is recovered by "
         f"nonnegative, sum-to-one least squares on {n_mix} held-out mixtures."],
        ['Genetic algorithm',
         f"{evaluations} of about {combos_text} possible {k}-MOF arrays scored: ethylene error {pp(wk2['ethene_mae_pp'])} to "
         f"{pp(ga['ethene_mae_pp'])} pp, and the gain held on a fresh mixture set ({pp(fresh_wk2)} to {pp(fresh_ga)} pp)."],
        ['Gradient idea',
         f"The error hinges on ethane-vs-ethylene contrast ({top['mof']}'s ethane coefficient is the biggest lever). Selecting "
         'with a linearized gradient did worse than the GA.']],
     [.24, .76]),
    ('columns', [
        ('heading', 'Ethylene error on held-out mixtures (pp)'),
        ('hbar', {'labels': ['Random median', 'Week 2 array', 'Single swaps', 'Genetic algorithm', f'All {pool} MOFs'],
                  'values': [r['random_baseline_final']['ethene_mae_pp']['median'], wk2['ethene_mae_pp'], swaps['ethene_mae_pp'],
                             ga['ethene_mae_pp'], every['ethene_mae_pp']],
                  'value_labels': [pp(r['random_baseline_final']['ethene_mae_pp']['median']), pp(wk2['ethene_mae_pp']),
                                   pp(swaps['ethene_mae_pp']), pp(ga['ethene_mae_pp']), pp(every['ethene_mae_pp'])],
                  'colors': [C['gray'], '#8DB8F5', '#5E9FF7', C['blue'], C['teal']], 'xmax': 16, 'label_width': 290,
                  'target': T['ethene_mae_pp'], 'target_label': f"target {num(T['ethene_mae_pp'], '{:.0f}')} pp", 'height': 320}),
    ], [
        ('heading', 'Why: the limit is signal, not search'),
        ('text', f"Even all {pool} MOFs at once only reach {pp(every['ethene_mae_pp'])} pp and still read zero ethylene in "
                 f"{frac(every['ethene_zeroed_frac'])} of cracker-like mixtures.", body),
        ('text', f"Ethane outadsorbs ethylene in {frac(selectivity['frac_ethane_stronger'])} of MOFs; the ones that favor ethylene "
                 'barely adsorb. D-MOPH is physisorption-only, so metal-site ethylene binding is likely missing.', body),
        ('text', f"Hitting the {num(T['ethene_mae_pp'], '{:.0f}')} pp target would take about {noise(ga_ok)} sensor noise, "
                 f"{num(base_noise/ga_ok, '{:.0f}')}x lower than assumed.", body),
    ], .47),
    ('text', 'Question: what noise level is realistic for MOF sensors? Then we prune toward 4-6 MOFs.',
     {'size': 25, 'weight': 'bold', 'after': 20}),
    ('text', f"Proposed targets: ethylene and ethane within {num(T['ethene_mae_pp'], '{:.0f}')} pp, ethylene/ethane ratio within "
             f"{pct(T['ratio_err_pct'])}. Model limits: {num(frozen['temperature_K'])} K dilute-limit coefficients, assumed noise, "
             'eight-gas normalization. All designs were selected on development mixtures only.', {'size': 17, 'color': C['muted']}),
]

slack = f"""Hi Dr. Medford, sorry for the slow reply, I was out visiting customer pilot plants last week. The week {wk} one-pager is attached, including answers to your two questions: selection was greedy D-optimal design plus one-for-one swaps, and detection is simulated as a linear Henry's-law response with {noise(base_noise)} noise, inverted by nonnegative, sum-to-one least squares on {n_mix} held-out mixtures.

TL;DR:
- Your GA suggestion helped a little: ethylene error {pp(wk2['ethene_mae_pp'])} to {pp(ga['ethene_mae_pp'])} pp ({evaluations} arrays scored).
- Even all {pool} MOFs together only reach {pp(every['ethene_mae_pp'])} pp, so ethylene/ethane is limited by signal, not by the search.
- Your gradient idea shows why: the error hinges on ethane-vs-ethylene contrast, and in D-MOPH ethane outadsorbs ethylene in {frac(selectivity['frac_ethane_stronger'])} of MOFs.
- A {num(T['ethene_mae_pp'], '{:.0f}')} pp ethylene target would need about {noise(ga_ok)} sensor noise.

Question: what noise level is realistic for MOF sensors? That decides whether we keep pushing the ratio or lump ethane and ethylene and prune toward 4-6 MOFs before the midterm.
"""

name = f"week{int(r['week'])}_onepager"
with PdfPages(HERE/f'{name}.pdf', metadata={'Title': f"Week {int(r['week'])} research update", 'Author': 'Ken Ma'}) as pdf:
    texts, bottom = render(card, HERE/f'{name}.png', pdf)
(HERE/'slack_draft.md').write_text(slack)
outputs = [str((HERE/f'{name}{ext}').relative_to(ROOT)) for ext in ['.pdf', '.png']]+[str((HERE/'slack_draft.md').relative_to(ROOT))]
check = {'slides': 1, 'overflow_px': [max(0., bottom-(H-30))], 'untraced_numbers': check_numbers(texts+[slack], R, ALLOWED),
         'outputs': outputs}
(HERE/'deliverables_check.json').write_text(json.dumps(check, indent=2)+'\n')
print(json.dumps(check, indent=2))
