# Decisions

## User-confirmed decisions

- Ken's decision: "Calculate the median and IQR using only directly computed values. Do not include ML-predicted values."
- Ken's decision, recorded word for word: "just clear those 2 paurs that dont get lined and let me know"
- Ken's decision, recorded word for word: "We should remain whtin the 113 computed molecules"
- Ken's decision, recorded word for word: "Dont use one if MEdFord doesnt have one"
- Ken's decision, recorded word for word: "they shuld target petrochemical/refinery gases"
- Ken's decision, recorded word for word: "lets target ethylene cracking"
- Ken's decision, recorded word for word: "molecules with 471 cmputed MOF's to give stronger comparisons"
- Ken's decision, recorded word for word: "good then they are just process gases and no need for a vapor pressure cutoff, tell me whats needed after"
- Ken's decision, recorded word for word: "thats fine ignore this then"
- Ken's decision, recorded word for word: "yes contain roughhly 8-12 and tell me which oens best for finak panel size /selectiob"
- Ken's decision, recorded word for word: "Ok I want 8-gas ethylene cracker target."
- Ken's decision, recorded word for word: "It will be the outlet of the cracker if possible. let me know if this is possible"
- Ken's requested objectives, recorded word for word: "Yes identify which gas leaked, in which percentage of a total prcoess gas, distinguish any feed from product, detect any drift from sampling from the process gas, and estimate the ratio of produce/feed if psosible"
- Ken's decision, recorded word for word: "we can select 12 for reduduencacy and then reduce later when testing."
- Ken's decision, recorded word for word: "We should keep industrial solvent vapors, select 12 and reduce thru testing, and do computed pairs only for now"
- Ken's decision, recorded word for word: "nvm nvm lets just do process gases"
- Use directly computed pairs only for all coverage counts.
- Recommend a target-gas panel for Ken's approval, but do not treat that recommendation as selection of the final MOF sensor-material panel.
- Use the 16,628 unique computed pairs actually present in `final.csv` as the authoritative working dataset. The two absent calculations will not be fabricated, imputed, or represented as rows.
- Keep the working molecule universe within the 113 molecules that occur in `final.csv`.
- Do not use an ML-completed table unless Prof. Medford has and supplies an authoritative table. No such table is currently available, so the working analysis remains computed-pairs only.
- Target petrochemical/refinery process gases, specifically an ethylene-cracking application.
- Restrict the target-gas comparison to molecules with directly computed Henry coefficients for 471 MOFs.
- Do not impose a vapor-pressure cutoff on these process gases.
- Recommend an approximately 8–12 molecule target-gas panel; keep this distinct from the later selection of MOF sensor materials.
- Use the eight-gas ethylene-cracker target panel: methane, ethane, ethene (ethylene), propane, propene (propylene), isobutane, isopentane, and 2-pentene.
- Target the cracker outlet using a conditioned extractive sample if technically possible.
- Design the in-silico task to identify which target gas changed and its percentage of total process gas, distinguish feed compounds from products, detect drift from the baseline process-gas composition, and estimate product/feed ratios where supported.
- Begin the MOF sensor-material stage with 12 selected MOFs for redundancy, then reduce the array only after testing discrimination, composition estimation, drift detection, and ratio accuracy.
- The latest decision keeps the eight ethylene-cracker process-gas target and supersedes the immediately preceding statement about retaining industrial solvent vapors.

## AI decisions

- Resolve the supplied Zenodo concept DOI through the official Zenodo API and use its latest published version, record `16754752` / DOI `10.5281/zenodo.16754752`.
- Retain both deposited archives unchanged and extract them into separate subdirectories under `data/` so their contents remain traceable.
- Treat `final.csv` as a table of directly simulated/computed pairs based on the paper's description of the final active-learning dataset; no ML-completed table or prediction columns were found in the deposited archives.
- The original mandatory stop was applied when the deposited and reported pair counts disagreed. Ken subsequently cleared the two-pair discrepancy by accepting the 16,628 deposited rows for downstream work.
- Interpret “clear” as resolving the bookkeeping decision, not altering the source data. The two intended-but-absent pair identities cannot be recovered from the deposited files.
- Interpret the deposited `K` column as the linear Henry coefficient in `mol kg^-1 Pa^-1` at 300 K. The paper and supplement show that `log10(K)` is the regression target, while the deposited nonnegative `K` values are the back-transformed physical quantity.
- Resolve all 83 `dsgdb9nsd_*` identifiers against the official QM9 Figshare archive, then cross-check structures and names through NIH PubChem. Preserve the identifier, QM9 SMILES, InChI, PubChem CID, and source URLs in `data/reference/qm9_molecule_identities.json`.
- Use a broad structural candidate screen rather than claiming a molecule's final suitability: include alcohols, ketones, ethers, C4+ alkanes, and simple nitriles; retain multifunctional alcohol/ether and alcohol/ketone molecules; exclude C1-C3 light alkanes, alkene-only molecules, aldehydes, amines, hydrogen cyanide, and multifunctional nitriles.
- Add simple nitriles to the screen because acetonitrile and propionitrile are relevant industrial solvent vapors even though nitriles were not named in Ken's parenthetical class list.
- Retain all deposited `K` values, including exact zeros. Calculate Q1, median, and Q3 with pandas' default linear interpolation and define IQR as Q3 minus Q1; do not log-transform values for these summaries.
- Rank coverage by the number of unique MOFs with a computed pair. Use dense ranks for ties and break display-order ties alphabetically; the chart shows the first 20 displayed candidates without implying panel selection.
- Recommend an eight-molecule ethylene-cracker target-gas panel for Ken's approval: methane, ethane, ethene (ethylene), propane, propene (propylene), isobutane, isopentane, and 2-pentene. All eight have directly computed values for the same 471 MOFs.
- Treat methane, ethane, ethene, propane, and propene as the core feed/product/light-gas group. Treat isobutane, isopentane, and 2-pentene as coverage-matched C4/C5 light-end or heavier-feed proxies, not as claims that they are the dominant products of every ethylene cracker.
- Prefer eight targets under the current constraints. Expanding to ten is justified only for a mixed-feed or naphtha-cracker scenario, in which case 2,3-dimethylbutane and 3-methylpentane are the next coverage-matched feed proxies.
- Interpret “cracker outlet” as an extractive sidestream of furnace effluent after rapid quench/sample conditioning, not direct placement of a MOF sensor in the roughly 850 °C raw coil effluent. Condition the sample to approximately 300 K and controlled pressure, while recognizing that removing water or condensables can change the sample composition.
- Keep two composition bases explicit in future calculations: mole percent of the true total outlet stream, including species absent from D-MOPH-25, and mole percent renormalized over the eight modeled target gases. Never label the renormalized eight-gas percentage as total process-gas percentage.
- Use at least eight independent MOF response channels for an eight-component quantitative composition estimate. Because the column-normalized 471-by-8 Henry matrix is full rank but ill-conditioned (condition number approximately 1.0e3), begin MOF subset selection with 10–12 materials for redundancy and test whether it can be pruned without losing identification and ratio accuracy.
- Treat “which gas leaked” as identifying which modeled component increased relative to the sampled outlet baseline. A single outlet sampling point cannot locate the physical equipment leak; localization would require multiple spatial sampling points or additional plant information.

## Deferred to Ken

- The exact conditioned outlet sampling point: immediately after the transfer-line exchanger/quench, after the quench tower, or after compression/drying.
- The representative full outlet composition and concentration ranges to use when moving beyond pure-component Henry coefficients, preferably from plant GC data or a documented process simulation.
- Whether the first model should represent normal operation only or also startup, shutdown, decoking, and upset states.
- Selection of the identities of the initial 12 MOF sensor materials after the target-gas panel, outlet-composition scenarios, and discrimination objective are fixed.

## Week 3 (2026-09-28)

### Ken's decisions

- Ken's decision, recorded word for word: "Week 3 is what we're doing." (follow the plan promised to Dr. Medford on 2026-09-21)
- Ken's decision, recorded word for word: "We're using the genetic algorithm that we're doing to solve based off of what Medford talked about, right? Just use the agentic to solve that and see what we can do."
- Ken approved the week-3 plan: targets, ceiling check, single-MOF swaps, genetic algorithm, gradient sensitivity map, relaxed gradient design, 1-2 slides, a Slack draft for his approval, and the reusable weekly pipeline (`python3 -m src.weekly N`, `/medford-week`).

### AI decisions

- Proposed targets, to confirm with Dr. Medford: ethylene and ethane mean absolute error of at most 2 pp each, ethylene/ethane ratio error of at most 10%, and overall eight-gas error of at most 2 pp as a guard so a search cannot trade away the other gases.
- Ratio metric: mean relative error of the ethylene/ethane ratio, capped at 100%, over mixtures where both gases are at least 5% (cracker-like). An estimated ethane of zero counts as 100%. The week-2 median metric sat flat at 100% and could not guide a search.
- Score: the mean over targets of metric divided by target, used by the swap search and the genetic algorithm. Selection only ever sees development seed 20260921. Reported numbers use held-out seed 20260922 and a fresh seed 20260928.
- Gradients: no autodiff library is installed (jax and torch are absent, and new dependencies need Ken's approval). The week uses the closed-form derivative of the linearized sum-to-one least-squares covariance, checked against finite differences, and central finite differences of the full constrained simulator with the noise draws held fixed.
- Noise sweep keeps the week-2 floor-to-relative ratio (the floor is 10% of the relative noise level).
- Ken's decision, recorded word for word: "That's good to go. Just put it to my clipboard and then just open the PDF one-pager. I'll send everything myself." (approved `weeks/03/slack_draft.md` as written, with `weeks/03/week3_onepager.pdf` as the attachment; Ken sends it himself)

## Week 4 (2026-10-11)

### Ken's decisions

- Ken's decision, recorded word for word: "dont send it broi, we need to do our weekly research and continue with the agenda and then ill approve"
- Ken's decision, recorded word for word: "find the repos urself and run the research"
- Pending Ken's approval: `weeks/04/slack_draft.md` (typed into the Slack DM composer, not sent) with `weeks/04/week4_onepager.png` as the attachment.

### AI decisions

- Follow Dr. Medford's "split the difference" suggestion from 2026-09-29: search the literature for ethylene-selective materials, then put the best known one into the array. Lumping ethane and ethylene is reported only as the C2-lumped error, pending Ken's call on how critical the pair is to the business case.
- Literature anchors, checked against the sources: UTSA-280 (Lin et al., Nature Materials 2018) has an apparent ethylene/ethane selectivity exceeding 10,000 (ethylene 2.5 mmol/g vs ethane 0.098 mmol/g at 298 K and 1 bar) and reports no methane uptake number; PAF-1-SO3Ag (Li et al., JACS 2014) has an IAST selectivity of 27 to 125 (equimolar, 296 K). Fe2(dobdc) (Bloch et al., Science 2012) is recorded only qualitatively because no selectivity number was verified. Day and Wilmer (Sensors 2020) assumed 5% relative noise for genetic-algorithm MOF arrays.
- Literature selectivities are IAST or apparent values from isotherms, not dilute-limit Henry ratios. They are used as proxies.
- Material models, each added as a 13th sensor next to the week-3 genetic-algorithm array: the sieve responds to ethylene only; sieve variants also respond to methane at 10%, 30% or 100% of the ethylene response; metal sites are a real D-MOPH framework with ethylene raised to S times its ethane coefficient (the olefin variant also raises propene to S times propane). The host framework is chosen on development mixtures only, and the spread over all 464 hosts is reported.
- Noise sweep from 0.05% to 20%, keeping the week-2 floor rule (floor is 10% of the relative level). Breakdown noise is the noise at which a gas's error reaches half of the no-sensor error (always guessing the development-set mean composition), interpolated in log noise.
- Pruning: backward elimination on development mixtures at 1% noise with the week-3 score, down to 7 sensors, the minimum for 8 gases under the sum-to-one constraint.
- Fresh mixture seed 20261011. Noise draws for the added sensor come from `default_rng([seed, 4])`, independent of the 471 week-2 columns.
- The D-MOPH archive was downloaded again on 2026-10-11 for a cloud run; its MD5, SHA-256 and the `final.csv` hash match `notes/data_provenance.md`.
- `src/slides.py` now falls back to Liberation Sans (Arial metrics) before DejaVu Sans, so cards built on Linux wrap like Arial on the Mac. `_line` gained optional `invert_x`, `band`, `ymax`, `legend_loc` and `right_pad`; the defaults keep the old behavior.
