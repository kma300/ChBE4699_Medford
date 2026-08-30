# Data provenance

## Zenodo record

- Dataset: *D–MOPH–25: Diverse MOF–molecule Pairs for Henry's Constants Prediction*
- Concept DOI supplied by Ken: `10.5281/zenodo.13131706`
- Concept DOI resolved through the official Zenodo API on 2026-08-30 to record `16754752`.
- Version DOI: `10.5281/zenodo.16754752`
- Publication date in the record: 2025-08-06
- Record API: <https://zenodo.org/api/records/16754752>
- Record page: <https://zenodo.org/records/16754752>

## Deposited files

Checksums were calculated on the downloaded bytes. The MD5 values exactly match the checksums returned by Zenodo.

| Deposited filename | Local path | Exact size (bytes) | Zenodo MD5 | Locally calculated SHA-256 |
|---|---|---:|---|---|
| `data.tar.gz` | `data/data.tar.gz` | 85,531,520 | `8272a2457205d39e3badeb63a2c42c6c` | `f189eeb8d72ab9d7b20aa006cb4aba939bb53dea5730e3ca89271bcfa1ebd778` |
| `codes.tar.gz` | `data/codes.tar.gz` | 72,349 | `c0c8567ff2daabe8e932895a7aee5a79` | `ed87c821cbe70c4825e887fb3a7004f3c714d7964b1efae6ba80bcc0c0b9ab64` |

Direct download endpoints:

- <https://zenodo.org/api/records/16754752/files/data.tar.gz/content>
- <https://zenodo.org/api/records/16754752/files/codes.tar.gz/content>

## Extraction

- `data.tar.gz` was extracted without modification under `data/dmoph25_data/` (58 files).
- `codes.tar.gz` was extracted without modification under `data/dmoph25_codes/` (170 files).
- The original archives are retained so all extracted files remain traceable to the exact deposited bytes.

## Paper used for cross-checking

- S. Choi, D. S. Sholl, and A. J. Medford, “D–MOPH–25: diverse MOF–molecule pairs for Henry’s constants prediction,” *Machine Learning: Science and Technology* **6** (2025) 035058. DOI: <https://doi.org/10.1088/2632-2153/ae0241>
- Open manuscript: <https://www.osti.gov/servlets/purl/3002420>

## Inventory discrepancy and resolution

The deposited file and paper do not agree exactly:

- `data/dmoph25_data/final.csv`: 16,628 rows, 16,628 unique MOF–molecule keys, 1,940 unique MOFs, and 113 unique molecules.
- Paper section 3.1: 16,630 final pairs, 1,940 MOFs, and 113 molecules in the active-learning data; section 2.1 defines a wider target space of 5,613 MOFs and 128 molecules.
- Planning/request expectation: approximately 140 molecules and approximately 16,600 computed pairs.

Per Ken's instruction to print both and stop when the files disagree with expectations, downstream analysis was not performed.

The iteration files localize the two-row shortfall to two active-learning batches:

- Iteration 5 to iteration 6 increases from 14,380 to 14,429 rows: 49 added rather than 50.
- Iteration 39 to iteration 40 increases from 16,079 to 16,128 rows: 49 added rather than 50.
- Iteration 49 to `final.csv` increases from 16,578 to 16,628 rows: the expected 50 added.

The deposited files do not contain a selection manifest identifying the two intended-but-absent MOF–molecule pairs. No missing rows were invented or imputed. Ken subsequently cleared this discrepancy and directed that the 16,628 unique computed pairs actually present be used as the authoritative working data; his wording is preserved in `notes/decisions.md`.

## Henry-constant units and scale

- Paper section 2.2 states that the Henry constants were computed at 300 K with Widom insertion in RASPA2.0.
- Paper section 2.4.1 defines effectively nonporous pairs as `K_H < 10^-15 mol kg^-1 Pa^-1`. This establishes the unit used for the physical Henry coefficient.
- Figure 2 and section 2.4.2 state that the neural network predicts logarithmic Henry constants.
- Supplement section S9 expresses the regression error in `log(K_H)` and introduces the factor `1/ln(10)`, establishing that the model transform is `log10(K_H)`.
- The deposited `final.csv` column is named `K`, contains only nonnegative values, and ranges from 0 to `2.38864e+89`. It is therefore the linear physical coefficient, not the model's logarithmic target.

The coverage summaries report untransformed `K` in `mol kg^-1 Pa^-1` at 300 K.

## QM9 molecule-identity reference

The 83 OOD molecule identifiers in D-MOPH are filenames from the official QM9/GDB-9 archive. The archive was downloaded on 2026-08-30 from the official Figshare record and used only to extract the 83 matching SMILES and InChI records.

- Figshare dataset: <https://springernature.figshare.com/articles/dataset/Data_for_133885_GDB-9_molecules/1057646>
- Figshare API: <https://api.figshare.com/v2/articles/1057646>
- Deposited filename: `dsgdb9nsd.xyz.tar.bz2`
- Exact size: 86,144,227 bytes
- Figshare/local MD5: `ad1ebd51ee7f5b3a6e32e974e5d54012`
- Locally calculated SHA-256: `3a63848ac80691bdb8d41834b575afad345b9300d7a2db0c38adb7f6eaa8360c`

Names and identifiers were cross-checked by InChI through the NIH PubChem PUG REST service. The resulting 83-record reference is `data/reference/qm9_molecule_identities.json` (45,763 bytes; SHA-256 `79f63ad7e2e524864018a3eaaa2d9d5901340616739f967b03af9cb9986ab367`). It contains no missing identity fields and exactly matches the 83 D-MOPH OOD identifiers.
