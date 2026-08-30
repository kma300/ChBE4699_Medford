# D-MOPH-25 solvent-vapor coverage report

## Working data

- Directly computed data only: **16,628 unique MOF–molecule pairs**, **1,940 MOFs**, and **113 molecules**.
- The deposited `K` column is the **linear Henry coefficient at 300 K**, in **mol kg^-1 Pa^-1**.
- The paper's regression model predicts `log10(K)`, but `final.csv` stores linear `K`. No logarithm was applied before the median and IQR calculations below.
- All reported quantiles use pandas' default linear interpolation over the directly computed `K` values for each molecule. Zeros are retained as deposited values.

## Evidence for units and scale

- Paper section 2.2 states that the constants were computed at 300 K by Widom insertion in RASPA2.0.
- Paper section 2.4.1 defines nonporous pairs using `K_H < 10^-15 mol kg^-1 Pa^-1`, establishing the reported unit.
- Figure 2 and section 2.4.2 state that the neural network predicts logarithmic Henry constants.
- Supplement section S9 writes the prediction error in `log(K_H)` and uses the `1/ln(10)` conversion, identifying the model transform as base-10 logarithm.
- The deposited `K` values are non-logarithmic: they are nonnegative and span zero through 2.389e+89; a logarithmic column would contain negative values for `K < 1`.

Sources: [open paper](https://www.osti.gov/servlets/purl/3002420), [IOP supplementary data](https://iopscience.iop.org/article/10.1088/2632-2153/ae0241/data), and [Zenodo record](https://zenodo.org/records/16754752).

## Candidate-screen rule

This is a broad coverage screen, not a final panel choice. It includes alcohols, ketones, ethers, C4+ alkanes, and simple nitriles. Nitriles were included because acetonitrile and propionitrile are directly relevant industrial solvent vapors even though the original parenthetical class list did not name them. Multifunctional alcohol/ether and alcohol/ketone molecules are retained. C1–C3 alkanes, alkenes without another included function, aldehydes, amines, hydrogen cyanide, and multifunctional nitriles are excluded.

- Flagged candidates: **89**
- Structural-family counts (multifunctional candidates can appear more than once): alcohol: 34, alkane: 17, alkene: 2, ether: 29, ketone: 13, nitrile: 6
- No ester, aromatic, or chlorinated molecule occurs among the 113 directly computed molecules.

## Top 20 candidates by computed-pair coverage

Henry statistics are in `mol kg^-1 Pa^-1`.

| Coverage rank | Molecule | Class | Computed MOFs | Coverage | Median K | IQR |
|---:|---|---|---:|---:|---:|---:|
| 1 | 1-Propanol | alcohol | 471 | 24.3% | 5.467e-03 | 1.266e-01 |
| 1 | 2,3-Dimethylbutane | alkane | 471 | 24.3% | 1.869e-02 | 1.490e+00 |
| 1 | 2-Pentanone | ketone | 471 | 24.3% | 1.469e-02 | 7.760e-01 |
| 1 | 3-Methylpentane | alkane | 471 | 24.3% | 5.755e-02 | 2.807e+00 |
| 1 | 4-Hexen-2-one | ketone + alkene | 471 | 24.3% | 2.231e+00 | 2.211e+02 |
| 1 | 4-Methyl-4-penten-2-one | ketone + alkene | 471 | 24.3% | 1.055e+00 | 7.187e+01 |
| 1 | Acetone | ketone | 471 | 24.3% | 4.235e-02 | 5.781e-01 |
| 1 | Acetonitrile | nitrile | 471 | 24.3% | 3.744e-03 | 3.229e-02 |
| 1 | Dimethyl ether | ether | 471 | 24.3% | 2.488e-03 | 1.490e-02 |
| 1 | Isobutane | alkane | 471 | 24.3% | 3.778e-03 | 2.889e-02 |
| 1 | Isopentane | alkane | 471 | 24.3% | 1.716e-02 | 2.743e-01 |
| 1 | Isopropyl alcohol | alcohol | 471 | 24.3% | 8.288e-03 | 1.714e-01 |
| 1 | Methyl isopropyl ether | ether | 471 | 24.3% | 3.804e-02 | 6.079e-01 |
| 1 | Methyl propyl ether | ether | 471 | 24.3% | 3.280e-02 | 2.448e-01 |
| 1 | Methyl tert-butyl ether | ether | 471 | 24.3% | 5.486e-03 | 6.729e-01 |
| 1 | Neopentane | alkane | 471 | 24.3% | 1.202e-03 | 5.136e-02 |
| 1 | Propionitrile | nitrile | 471 | 24.3% | 1.917e-02 | 2.176e-01 |
| 2 | 3,3-dimethylbutan-1-ol | alcohol | 55 | 2.8% | 3.218e-10 | 1.230e+01 |
| 2 | Diethylene Glycol | alcohol + ether | 55 | 2.8% | 2.584e-02 | 2.076e+02 |
| 3 | 3-Methoxy-1-butanol | alcohol + ether | 53 | 2.7% | 8.103e-01 | 1.350e+02 |

![Coverage bar chart](coverage_bar_chart.svg)

## Monday update bullets

- The verified working set contains **16,628 directly computed MOF–molecule pairs** spanning **1,940 MOFs and 113 molecules**; the two-pair publication discrepancy is documented and the deposited rows are authoritative for this analysis.
- The broad structural screen flags **89 plausible solvent-vapor candidates**; there are no ester, aromatic, or chlorinated candidates in the computed table.
- **17 candidates each have 471 computed MOFs (24.3% coverage)**, while the best QM9-derived candidate has only **55 MOFs (2.8%)**.
- Coverage is therefore highly uneven; these results identify candidates for Ken's panel decision but do **not** select the final 8–12 vapors or any MOF sensor array.

## Problems and cautions

- The two intended-but-absent pairs cannot be identified from the deposit; the analysis uses the 16,628 rows actually present.
- The QM9-derived candidates have sparse direct coverage (at most 55 MOFs), so a panel containing many of them would produce a much less complete MOF × VOC matrix.
- `final.csv` contains **522 exact zero `K` values**. They are retained because they are deposited computed results, but they likely represent numerical underflow or effectively nonporous pairs.
- The structural screen is deliberately broad. Solvent use, toxicity, vapor pressure, and experimental availability must be reviewed before Ken chooses a final panel.
- The public Zenodo deposit does not contain the ML-completed table, optimized classifiers, or neural-network checkpoints described in the paper.
