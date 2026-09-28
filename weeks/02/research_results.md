# Week 2: 12-MOF array selection and mixture testing

Ken Ma · Dr. A. J. Medford research · September 20, 2026

**This continues the checkpoint in the graphic sent to Medford on August 31.** That update established the eight-gas panel and complete 471 × 8 matrix, then listed response analysis, selection of 12 MOFs, mixture testing and pruning as the next steps. We have now completed the response analysis and provisional selection and run the first synthetic mixture benchmark. Pruning remains pending. [Original graphic and update](https://gt-energyhack.slack.com/archives/D0BQX2KLG0G/p1788206909156549).

**The selected array improves synthetic composition recovery, but it does not yet meet the full gas-identification, ratio and small-change objectives.** On 1,000 held-out mixtures, its mean absolute error was **3.52 percentage points**, versus **9.56 pp** for the median of 200 random arrays: a **63.1% reduction in error**. It outperformed all 200 sampled random arrays on this average-error metric. Methane, ethane and especially ethylene remain difficult; large individual errors persist.

## Progress against the earlier graphic

| Earlier checkpoint or planned step | Progress reported here |
|---|---|
| Repository/data, inventory/units, eight-gas panel, 471 × 8 matrix | Already complete in the prior update. Retained as the starting point. |
| Analyze response patterns | Completed the computational exploration. |
| Select 12 MOFs | Completed a provisional, noise-aware selection. |
| Test gas identification, mixtures, drift and ratios | Completed a first synthetic pass. Significant light-gas, ratio and small-change limitations remain. |
| Prune the array | Pending. Keep all 12 selected materials for now. |

[Medford's September 1 reply](https://gt-energyhack.slack.com/archives/D0BQX2KLG0G/p1788266413547309) confirmed the objective of an array for mixtures containing all eight gases or subsets. The current benchmark tests exactly those mixture types. His concern about co-occurring vapors remains an open practical limitation. Ken reaffirmed the same research objective on September 18. The [checkpoint record](progress_checkpoint.md) preserves this context for subsequent updates.

This is an eight-gas ethylene-cracker study. The LNG/naphtha/crude scope alternatives were not adopted. Reported fractions sum to 100% over these eight gases only, not necessarily over a real plant stream. A percentage-point error is an absolute difference in composition; for example, estimating 24% when the true fraction is 20% is a 4 pp error. The mean error is not a classification accuracy percentage.

## Provisional selected materials

**CISMAT01, FERHAN, FUDQIF, GEDLIM, GEHSAN, GIZJOP, LOFZUB, MEJQEZ, MOGVAG, PUQXUV, RURPEA, XUWVEQ.**

The [selected-material table](selected_12_mofs.csv) contains all 96 original Henry coefficients and the assumed per-channel noise standard deviation. MOF identifiers are database structure codes, not verified purchasable or experimentally ready sensor products. Selection is provisional, and no pruning below 12 has occurred.

Seven candidates with all eight K values below 10⁻¹⁵ mol kg⁻¹ Pa⁻¹ were excluded from the computational candidate pool: CEHZAR01, CUYHIO, EQIWAD, IYIGEC, LENRUS, PEPXIS and WIJDID. The remaining 464 candidates retain partial zeros and extreme values. The threshold is the paper's effectively nonporous-pair criterion, not a hardware detection limit. The original 471 × 8 source matrix remains intact.

![Selected and random arrays](01_array_comparison.png)

## What the final test showed

| Gas | Mean composition error (pp) | Presence recall at 1% estimated threshold |
| --- | --- | --- |
| Methane | 6.61 | 73.7% |
| Ethane | 6.77 | 75.2% |
| Ethylene | 9.91 | 53.7% |
| Propane | 1.50 | 92.5% |
| Propylene | 1.97 | 88.5% |
| Isobutane | 0.52 | 93.8% |
| Isopentane | 0.48 | 93.5% |
| 2-Pentene | 0.43 | 95.8% |

The 95th percentile of the selected array's per-mixture average error was **8.74 pp**. Its worst mixture-average error was **16.70 pp**, and its largest single-gas error was **66.69 pp**. Random-array average errors ranged from 5.54 to 13.45 pp, with a 5th–95th percentile interval of 7.00–12.58 pp. These are results for sampled arrays and simulated cases, not confidence bounds on plant performance or proof of a globally optimal array.

A concrete failure appears in final mixture **941**: true ethylene was **65.12%**, but the estimate was **0%**. Methane and ethane were overestimated instead. This exposes a serious light-gas ambiguity that the overall average conceals.

| Mixture family | Cases | Mean error (pp) | 95th-percentile mixture error (pp) |
| --- | --- | --- | --- |
| All eight gases | 500 | 3.93 | 8.30 |
| Ethane/ethylene stress | 50 | 5.78 | 12.09 |
| Propane/propylene stress | 50 | 2.20 | 2.84 |
| Subsets of 2–7 gases | 400 | 2.90 | 8.57 |

The separate development set gave 3.47 pp selected-array error. The final set was generated only after the method and selected materials were frozen; all 2,000 development/final compositions were checked to be distinct. No selection rule or noise setting was adjusted after inspecting final results.

## Presence and product/feed ratios

Presence was scored as estimated fraction ≥1%, against true fraction >0. This is an explicit scoring threshold, not a measured detection limit. Overall precision was 95.7% and recall was 83.3%, but ethylene recall was only 53.7%. Missed ethylene fractions ranged from 0.09% to 65.12%; failures were not limited to trace concentrations. [Full presence counts and missed-fraction ranges](final_presence_metrics.csv).

| Ratio | Eligible mixtures | Estimated-feed failures | Scored positive-product cases | Median relative error |
| --- | --- | --- | --- | --- |
| ethylene/ethane | 767 | 176 | 519 | 100.0% |
| propylene/propane | 781 | 43 | 655 | 41.4% |

Ratio eligibility requires true feed ≥1%. Estimated feed <1% is recorded as a failure and excluded from finite ratio-error summaries; the failures above remain part of the assessment. Ethylene/ethane therefore failed this denominator check in 176 of 767 eligible cases, and propylene/propane in 43 of 781. Relative errors additionally require positive true product. The zero-product cases receive absolute ratio errors: mean 0.585 over 72 cases for ethylene/ethane, and 0.050 over 83 for propylene/propane. [All ratio metrics, including random baselines and upper-tail errors](final_ratio_metrics.csv).

The ratio objective is not satisfied convincingly under the primary noise assumptions. A 100% median relative error for ethylene/ethane should not be presented as successful ratio estimation.

## Composition changes

| Actual increase | Feasible cases | Error in recovered increase (pp) | Estimated increase has correct positive sign |
| --- | --- | --- | --- |
| +1 pp | 1000 | 4.44 | 62.1% |
| +5 pp | 998 | 5.11 | 81.4% |

Each mixture receives an increase in one target gas, cycling evenly through all eight; other fractions decrease proportionally to retain a unit sum. Before/after observations have independent noise. All 1,000 +1 pp changes were feasible; two +5 pp changes would exceed 100% and were excluded and counted, leaving 998. The median random-array error in the recovered increase was 10.78 pp for +1 pp and 12.01 pp for +5 pp, so selection helps, but errors remain large compared with the intended small changes.

![Composition-change errors](03_composition_changes.png)

The heavier gases recover increases better in this model. For methane, ethane and ethylene, both the size and sometimes the sign of the change are unreliable. Sign agreement is not a calibrated change-detection test; there is no no-change false-alarm benchmark here. This experiment concerns changes in gas composition and does not show that sensor drift can be separated from process change. [All change metrics](final_drift_metrics.csv).

## Noise and design sensitivity

![Noise sensitivity](02_noise_sensitivity.png)

Keeping the same 12 MOFs, the nine assumed-noise cases produced mean errors from **0.41 to 7.52 pp**. The primary case used a standard deviation equal to the larger of 1% of each material's maximum eight-gas coefficient and 0.1% of the fixed reference coefficient. The reference is 0.0467015 mol kg⁻¹ Pa⁻¹; the common floor is 4.67015 × 10⁻⁵ in modeled uptake-slope units. These are synthetic assumptions, not measured instrument specifications or coefficient uncertainty.

The zero-noise check recovered the final compositions to a maximum absolute fraction error of 1.42e-14. This checks the mathematical implementation when the same coefficients generate and fit the observations; it does not validate actual mixture physics.

All five design runs selected exactly the same 12 MOFs: primary ridge 10⁻⁶; ridges 10⁻⁸ and 10⁻⁴; all 471 candidates; and the 464-candidate pool with GOMREG/GOMRAC additionally omitted. Thus this selection did not rely on those two extreme-response materials. The seven-direction, noise-weighted matrix has full numerical rank 7, minimum singular value 1.656, and condition number 121.00. These checks establish stability to the tested design settings, not universal robustness. Greedy selection made 12 additions and one improving swap, then stopped when no swap improved the score by more than 10⁻⁸. [Selection traces](array_designs.json).

## Method and verification

The experiment follows the [approved proposal](../medford-week2/selection_proposal.md). It models the ideal additive molar-uptake slope **r = Kx** in the 300 K dilute limit. A noise-weighted D-optimal score selects 12 materials across the seven independent composition directions. Reconstruction minimizes noise-weighted squared error subject to nonnegative fractions summing to one. Signed noisy observations are retained. No finite operating pressure, transduction law, adsorption saturation, mixture competition or coefficient uncertainty is inferred from Henry constants alone.

Each development/final set contains 500 all-eight Dirichlet mixtures, 400 random subsets of 2–7 gases, and 50 stress mixtures each for ethane/ethylene and propane/propylene. In the stress cases the focal pair occupies 80% of the mixture, with its product share stratified across 1%–99%; the other six gases divide the remaining 20%. These broad cases are not a measured distribution of cracker operation. The same mixture and per-MOF noise realizations are used for every array. Fixed seeds are 20260920 (arrays), 20260921 (development) and 20260922 (final). [Frozen protocol](protocol_frozen.json).

The solver enumerates simplex faces and uses direct SVD calculations, with feasibility and optimality checks. An independent SciPy SLSQP check on 69 development observations agreed within **0.00016 pp** in any estimated fraction. Two SLSQP runs reported line-search warnings; both returned feasible solutions with objective differences below 10⁻⁶. One development observation required exhaustive comparison of all feasible faces after a strict early optimality tolerance was missed by roundoff; its scaled residual was 1.35 × 10⁻¹². None of the 603,000 final primary-noise reconstructions across 201 arrays required that fallback. Noiseless development checks included 1,008 compositions per checked array, including all eight pure-gas vertices. [Numerical validation](solver_validation.json).

An additional [artifact audit](final_verification.json) checked the 96 exported source coefficients, recomputed every array's average and 95th-percentile mixture error from stored predictions, and verified all 3,216,000 development/final predicted fractions and composition constraints. The three worst final mixtures were independently solved with SLSQP and agreed within 0.000009 pp; their large errors persist under that separate method. Frozen script/design hashes and the unchanged source were verified.

Source: [D-MOPH-25 deposited record](https://zenodo.org/records/16754752) and [Choi, Sholl & Medford (2025)](https://doi.org/10.1088/2632-2153/ae0241). The authoritative local deposit contains 16,628 unique computed pairs, including the unchanged 3,768 pairs used here. Source SHA-256: `a748213897204191619a43c6d6c08f80e8109b943e936233a1a0bf9e96f5d938`. The dataset, existing research slides and Slack were not edited; nothing was sent to Dr. Medford.

## Interpretation for the next research update

We have a reproducible candidate array that substantially improves the chosen synthetic benchmark. We also have a clear failure mode: the light gases and their ratios remain unreliable at the primary assumed noise level. Keep the 12-material baseline for now. The next research decision should focus on the accuracy actually needed for those gases and whether realistic measurement sensitivity can support it, before pruning materials or claiming plant utility.

[Reproducibility package](reproducibility.zip) · [Final per-mixture estimates](final_selected_predictions.csv) · [All final array comparisons](final_array_metrics.csv).
