"""Weekly Medford update driver.

    python3 -m src.weekly 3            # build week 3 deliverables (runs the experiment if no results yet)
    python3 -m src.weekly 3 --rerun    # rerun the experiment first

Each week lives in weeks/NN/: experiment.py writes results.json; deliverables.py turns results.json into
slide PNGs, a .pptx and slack_draft.md, and writes deliverables_check.json. This driver fails loudly if a
check fails: more than two slides, a slide that overflows, or any number that does not trace to results.json.
"""
import argparse
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('week', type=int)
    parser.add_argument('--rerun', action='store_true')
    args = parser.parse_args()
    week = ROOT/'weeks'/f'{args.week:02d}'
    if args.rerun or not (week/'results.json').exists():
        subprocess.run([sys.executable, str(week/'experiment.py')], check=True, cwd=ROOT)
    subprocess.run([sys.executable, str(week/'deliverables.py')], check=True, cwd=ROOT)
    check = json.loads((week/'deliverables_check.json').read_text())
    problems = []
    if check['slides'] > 2:
        problems.append(f"{check['slides']} slides (Medford asked for 1-2)")
    problems += [f'slide {i+1} overflows by {px:.0f}px' for i, px in enumerate(check['overflow_px']) if px > 0]
    if check['untraced_numbers']:
        problems.append(f"numbers not traced to results.json: {check['untraced_numbers']}")
    for path in check['outputs']:
        print('wrote', path)
    if problems:
        sys.exit('CHECK FAILED: '+'; '.join(problems))
    print('checks passed: slides <= 2, all slides fit, every number traced to results.json')


if __name__ == '__main__':
    main()
