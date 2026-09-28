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
