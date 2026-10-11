"""Week 4 deliverables: a one-page summary card (PDF + PNG) and a TL;DR Slack message.

The card answers Dr. Medford's two points from 2026-09-29 (noise as a sensitivity variable; the best known
ethylene-selective material in the array) and the week-3 promise to prune toward 4-6 MOFs. Every number comes from
results.json. Run from the repo root: python3 weeks/04/deliverables.py   (or: python3 -m src.weekly 4)
"""
import json
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
R = Registry()
# '4' and '6': the planning-doc goal of a 4-6 MOF array. '280', '1', '3': digits inside the material names UTSA-280 and
# PAF-1-SO3Ag.
ALLOWED = {'4', '6', '280', '1', '3'}


def pp(v): return R.num(v, '{:.2f}')
def num(v, fmt='{}'): return R.num(v, fmt)
def noise(level, fmt='{:g}%'): return R.num(level*100, fmt)


sel, limits, T = r['selectivity_sweep'], r['noise_limits'], r['targets']


def tm(name, key='ethene_mae_pp', level='0.01', subset='final'):
    return sel[name][subset][level]['target_metrics'][key]


def breakdown(design, gas): return limits[design][gas]['breakdown']['noise']


ga_e, sieve_e, sieve_e_fresh = tm('ga'), tm('ga+sieve'), tm('ga+sieve', subset='fresh')
metal27_e, metal5_e = tm('ga+metal_S27'), tm('ga+metal_S5')
S27, S5 = r['added_sensors']['metal_S27']['selectivity'], r['added_sensors']['metal_S5']['selectivity']
methane_fraction = r['added_sensors']['sieve_methane_30']['selectivity']  # methane response as a fraction of ethylene
sieve_ethane, sieve_ratio, sieve_overall = tm('ga+sieve', 'ethane_mae_pp'), tm('ga+sieve', 'ratio_err_pct'), tm('ga+sieve', 'overall_mae_pp')
methane30 = tm('ga+sieve_methane_30')
spread = r['metal_S27_framework_spread_final']
pruned = r['pruning']['ga+sieve'][-1]
paf = next(x for x in r['literature'] if x['material'] == 'PAF-1-SO3Ag')
utsa = next(x for x in r['literature'] if x['material'].startswith('UTSA-280'))
base_n = len(r['base_array']['indices'])
gases = list(r['no_sensor_mae_pp']['final'])
light, heavy = ['methane', 'ethane', 'ethene'], ['isobutane', 'isopentane', '2-pentene']
realistic = r['protocol']['realistic_noise']

# Guard every sentence the card makes about the breakdown pattern.
assert max(breakdown('ga', g) for g in light) < .01, 'card says the light gases break down below 1% without the sieve'
assert all(limits['ga+sieve'][g]['breakdown']['bound'] == 'interpolated' for g in gases)
assert round(100*breakdown('ga+sieve', 'methane')) == round(100*breakdown('ga+sieve', 'ethane')) == 2
assert round(100*breakdown('ga+sieve', 'propane')) == round(100*breakdown('ga+sieve', 'propene')) == 5
assert min(breakdown('ga+sieve', g) for g in heavy) == breakdown('ga+sieve', 'isobutane')
assert max(breakdown('ga+sieve', g) for g in heavy) == breakdown('ga+sieve', '2-pentene')
assert pruned['size'] == base_n+1-6 and pruned['removed'] != 'added sensor'
assert all(step['removed'] != 'added sensor' for step in r['pruning']['ga+sieve'])

day = date.fromisoformat(r['date'])
header = f"KEN MA  /  DR. A. J. MEDFORD  /  {day.strftime('%B').upper()} {num(day.day)}, {num(day.year)}"
wk = num(r['week'])
added_n = num(base_n+1)
one = noise(.01)
heavy_lo, heavy_hi = noise(breakdown('ga+sieve', 'isobutane'), '{:.0f}'), noise(breakdown('ga+sieve', '2-pentene'), '{:.0f}%')
body = {'size': 21, 'after': 14}
levels = r['protocol']['noise_levels']
decade_labels = [noise(level) if level in (.001, .01, .1) else '' for level in levels]

card = [
    ('header', header),
    ('title', f'Week {wk}: an ethylene-selective sensor fixes ethylene, not ethane'),
    ('table', ['Your question or idea', 'Answer'], [
        ['Lit search: ethylene-selective MOFs',
         f"Strongest found: UTSA-280 sieving (apparent selectivity over {num(utsa['selectivity_low'], '{:,}')}) and Ag(I) "
         f"π-complexation (PAF-1-SO3Ag, {num(paf['selectivity_low'])} to {num(paf['selectivity_high'])}). D-MOPH has no "
         "metal-site binding."],
        ['Best known material in the array',
         f"As a {added_n}th sensor, the sieve cuts ethylene error from {pp(ga_e)} to {pp(sieve_e)} pp at {one} noise "
         f"(fresh set: {pp(sieve_e_fresh)}). Metal sites on the best host: {pp(metal27_e)} pp at selectivity {num(S27)}, "
         f"{pp(metal5_e)} at {num(S5)}."],
        ['Noise as a sensitivity variable',
         f"Without the sieve, the three lightest gases break down below {one} noise. With it: ethylene "
         f"{noise(breakdown('ga+sieve', 'ethene'), '{:.1f}%')}, methane and ethane about "
         f"{noise(breakdown('ga+sieve', 'methane'), '{:.0f}%')}, propane and propylene about "
         f"{noise(breakdown('ga+sieve', 'propane'), '{:.0f}%')}, heavier gases {heavy_lo}\u00a0to\u00a0{heavy_hi}."],  # keep the range on one line
        ['Pruning toward 4-6 MOFs',
         f"{num(len(gases))} gases need at least {num(pruned['size'])} sensors. {num(pruned['size']-1)} MOFs plus the sieve keep "
         f"ethylene at {pp(pruned['final']['target_metrics']['ethene_mae_pp'])} pp and overall error at "
         f"{pp(pruned['final']['target_metrics']['overall_mae_pp'])} pp (all {added_n}: {pp(sieve_overall)})."]],
     [.25, .75]),
    ('columns', [
        ('heading', 'Ethylene error vs sensor noise (pp)'),
        ('line', {'x': levels, 'x_labels': decade_labels, 'invert_x': False, 'right_pad': 130, 'height': 305, 'ymax': 16,
                  'series': [{'label': 'Week 3 GA array', 'color': C['gray'],
                              'y': [row['target_metrics']['ethene_mae_pp'] for row in r['noise_sweep']['ga']['final']]},
                             {'label': '+ ethylene sieve', 'color': C['teal'],
                              'y': [row['target_metrics']['ethene_mae_pp'] for row in r['noise_sweep']['ga+sieve']['final']]}],
                  'legend_loc': 'upper left', 'x_title': 'sensor noise (% of full scale)', 'y_title': 'ethylene error (pp)',
                  'target': T['ethene_mae_pp'], 'target_label': f"target {num(T['ethene_mae_pp'], '{:.0f}')} pp",
                  'band': realistic, 'band_label': f"your {noise(realistic[0])} to {noise(realistic[1])}", 'band_label_y': .4}),
    ], [
        ('heading', 'Why ethane is still the limit'),
        ('text', f"Each MOF's full scale is set by the heavy gases, so methane and ethane signals sit near the noise. With the "
                 f"sieve, ethane error is still {pp(sieve_ethane)} pp and the ratio error {R.num(sieve_ratio, '{:.0f}%')} "
                 f"(target {R.num(T['ratio_err_pct'], '{:.0f}%')}).", body),
        ('text', f"Caveats: literature selectivities come from isotherms, not dilute-limit Henry ratios. The gain depends on the "
                 f"host (median of {num(spread['n_frameworks'])} hosts: {pp(spread['median'])} pp). A sieve that also took up methane "
                 f"at {R.num(100*methane_fraction, '{:.0f}%')} of its ethylene response still gives {pp(methane30)} pp.", body),
    ], .5),
    ('text', 'Next: a light-gas channel. Could we do a quick call on model architectures for that?',
     {'size': 24, 'weight': 'bold', 'after': 16}),
    ('text', "Held-out mixtures; hosts and pruning chosen on development mixtures only. "
             f"Breakdown: error reaches half of always guessing the average composition. Sources: Lin et al., Nat. Mater. (UTSA-280); "
             f"Li et al., JACS (PAF-1-SO3Ag); Day and Wilmer, Sensors (GA arrays, {noise(r['noise_literature']['assumed_relative_noise'])} "
             'noise assumed).', {'size': 16, 'color': C['muted']}),
]

slack = f"""Hi Dr. Medford, sorry for the slow reply, the startup took most of the last two weeks. I went with your split the difference idea, and the week {wk} one-pager is attached.

TL;DR:
- Lit search: the strongest ethylene-selective materials we found are molecular sieves (UTSA-280, apparent ethylene/ethane selectivity over {num(utsa['selectivity_low'], '{:,}')}) and silver π-complexation (PAF-1-SO3Ag, {num(paf['selectivity_low'])} to {num(paf['selectivity_high'])}).
- Adding one of these as a {added_n}th sensor cuts ethylene error from {pp(ga_e)} to {pp(sieve_e)} pp at {one} noise, and {num(pruned['size']-1)} MOFs plus that sensor hold it there.
- Treating noise as the variable: ethylene now holds up to {noise(breakdown('ga+sieve', 'ethene'), '{:.1f}%')} noise, but methane and ethane break down near {noise(breakdown('ga+sieve', 'methane'), '{:.0f}%')}, so ethane ({pp(sieve_ethane)} pp) and the ratio are still the limit.

Question: would you be open to a quick call this week? I'd love to hear what model architectures you'd propose for the next step, like using ODAC/UMA to screen frameworks that could host these ethylene sites, or a learned model in place of the least squares inversion.
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
