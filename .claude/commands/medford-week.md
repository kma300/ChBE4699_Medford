---
description: Build this week's research update for Dr. Medford (experiment, 1-2 slides, Slack draft)
argument-hint: "[week number, optional]"
---

Build Ken's weekly ChBE 4699 research update for Dr. A. J. Medford. Week number: $ARGUMENTS (if empty, use the
highest `weeks/NN/` folder plus one).

## 1. Get context (read only)

- Read the Slack DM with Medford in the Slack desktop app. Never type in Slack.
  - Open it: `open "slack://channel?team=TKM8PQGNP&id=D0BQX2KLG0G"`.
  - Capture the message pane: `screencapture -x /tmp/slack.png`, crop with `sips`, then Read the image.
  - Scroll with Page Up only: `osascript -e 'tell application "Slack" to activate' -e 'tell application "System Events" to key code 116'`.
  - Afterwards, give focus back to the terminal.
- Read last week's `weeks/NN/results.json`, `weeks/NN/slack_draft.md`, `weeks/02/slack_thread.md` and `notes/decisions.md`.
- Answer these before planning:
  - What did Ken promise last time?
  - What did Medford ask or suggest since then?

## 2. Plan the week's experiment

- One experiment that follows through on the last promise and answers Medford's latest message.
- Reuse `src/sensorsim.py` (week-2 simulator, regression-tested) and `src/search.py` (GA, swaps, gradients, relaxed design).
- Selection may only see the development seed. Report on the held-out seed and a fresh seed.

## 3. Build it

- Copy the previous week's `experiment.py` and `deliverables.py` into `weeks/NN/` and adapt them.
  - `experiment.py` writes `results.json`.
  - `deliverables.py` builds the slides with `src/slides.py`. Every number must go through `Registry.num()`.
- Run `python3 -m pytest`, then `python3 -m src.weekly NN`. The driver fails on:
  - more than 2 slides
  - a slide that overflows
  - any number that is not traced to `results.json`
- Look at every rendered slide PNG before showing it. A passing check does not prove the layout is right.

## 4. Hand off to Ken

- Show Ken:
  - the slide PNG paths
  - the exact Slack text from `weeks/NN/slack_draft.md`
  - a 3-line summary of what changed
- Never send anything to Medford without Ken's explicit approval of the exact text.
- After approval, Ken either posts it himself or asks you to post it.
- Append Ken's decisions to `notes/decisions.md`, then commit with a conventional message (`feat(weekNN): ...`).
