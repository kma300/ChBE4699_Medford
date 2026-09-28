# Week 2 Slack thread (GT Slack DM with Dr. Medford, channel D0BQX2KLG0G)

Copied from the Slack desktop app on 2026-09-28.

## Ken, Monday 2026-09-21 7:21 PM (sent, with the week-2 slide images)

Hey Dr. Medford - attached is the research update for Monday. We continued from the 8 gas checkpoint, but encountered some mixed results:

- Average mixture recovery improved from our selected array
- Light-gas separation & feed/product ratios remain difficult

Since our main focus is to identify the product quality of ethylene steam crackers, I'm planning to refine the selection objective to maximize on ethane/ethylene separation + ratio accuracy and then test individual MOF replacements. The backup would be to integrate some data-driven methods like a genetic algorithm search that might help find new materials. Let me know if there's anything that might pose a stronger method to nail down the current scope.

## ajm (Dr. Medford), Tuesday 2026-09-22 11:05 PM

Sounds good, thanks for the update! What was the selection method you used here? And how are you simulating the detection experiment?

I assume the general challenge you have is that this is a "471 choose 8" combinatorial explosion so brute force sampling won't work. A genetic algorithm would be a natural choice to try (Claude can probably code this up in an hour or less).

Another thing to consider: If you have a function that deterministically computes your composition error as a function of the 12x8 adsorption strength matrix, then you can potentially differentiate that function with automatic differentiation to get determine which MOF/gas point has the most impact. This could then be used to adaptively update the MOF selection through a stochastic optimization. Not quite as straightforward, but also well within agentic coding capabilities.

## Earlier guidance in the same DM

- 2026-08-26: planning doc (~1 page), then weekly updates (~1-2 slides) each Monday; discuss on Slack, meet only if necessary.
- 2026-08-27: keep a 2-week cadence for written updates, with a quick weekly Slack check-in in between.
- 2026-09-01: send slides whenever convenient, as long as they arrive regularly. Confirmed the goal: the MOF array with the best sensing of each of the 8 gases in mixtures of all 8 or subsets. Flagged co-occurring plant vapors as a later concern, not needed this semester.
- 2026-09-15: happy to let the scope shift based on industry feedback.
