"""Compute solvent-vapor coverage statistics from D-MOPH computed pairs only."""

from __future__ import annotations

import json
import re
from html import escape
from pathlib import Path

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
FINAL_CSV = ROOT / "data" / "dmoph25_data" / "final.csv"
QM9_IDENTITIES = ROOT / "data" / "reference" / "qm9_molecule_identities.json"
OUTPUTS = ROOT / "outputs"
ANALYSIS_JSON = OUTPUTS / "coverage_analysis.json"
REPORT_MD = OUTPUTS / "coverage_report.md"
CHART_SVG = OUTPUTS / "coverage_bar_chart.svg"

HENRY_UNIT = "mol kg^-1 Pa^-1"
TEMPERATURE_K = 300

# The 30 initial molecules are already named in D-MOPH. These normalized names
# and structural-family labels make the screening rule explicit and auditable.
INITIAL_MOLECULES: dict[str, dict[str, object]] = {
    "15-heptadiene": {"name": "1,5-Heptadiene", "classes": ["alkene"], "carbons": 7},
    "2-pentene": {"name": "2-Pentene", "classes": ["alkene"], "carbons": 5},
    "23-dimethylbutane": {"name": "2,3-Dimethylbutane", "classes": ["alkane"], "carbons": 6},
    "3-methylpentane": {"name": "3-Methylpentane", "classes": ["alkane"], "carbons": 6},
    "4-hexen-2-one": {"name": "4-Hexen-2-one", "classes": ["ketone", "alkene"], "carbons": 6},
    "4-methyl-1-hexene": {"name": "4-Methyl-1-hexene", "classes": ["alkene"], "carbons": 7},
    "4-methyl-4-penten-2-one": {"name": "4-Methyl-4-penten-2-one", "classes": ["ketone", "alkene"], "carbons": 6},
    "44-dimethyl-1-pentene": {"name": "4,4-Dimethyl-1-pentene", "classes": ["alkene"], "carbons": 7},
    "acetaldehyde": {"name": "Acetaldehyde", "classes": ["aldehyde"], "carbons": 2},
    "acetone": {"name": "Acetone", "classes": ["ketone"], "carbons": 3},
    "acetonitrile": {"name": "Acetonitrile", "classes": ["nitrile"], "carbons": 2},
    "dimethyl_ether": {"name": "Dimethyl ether", "classes": ["ether"], "carbons": 2},
    "dimethylamine": {"name": "Dimethylamine", "classes": ["amine"], "carbons": 2},
    "ethane": {"name": "Ethane", "classes": ["alkane"], "carbons": 2},
    "ethene": {"name": "Ethene", "classes": ["alkene"], "carbons": 2},
    "ethylamine": {"name": "Ethylamine", "classes": ["amine"], "carbons": 2},
    "hydrogen_cyanide": {"name": "Hydrogen cyanide", "classes": ["cyanide"], "carbons": 1},
    "isobutane": {"name": "Isobutane", "classes": ["alkane"], "carbons": 4},
    "isopentane": {"name": "Isopentane", "classes": ["alkane"], "carbons": 5},
    "isopropyl_alcohol": {"name": "Isopropyl alcohol", "classes": ["alcohol"], "carbons": 3},
    "methane": {"name": "Methane", "classes": ["alkane"], "carbons": 1},
    "methyl_isopropyl_ether": {"name": "Methyl isopropyl ether", "classes": ["ether"], "carbons": 4},
    "methyl_propyl_ether": {"name": "Methyl propyl ether", "classes": ["ether"], "carbons": 4},
    "methyl_propyl_ketone": {"name": "2-Pentanone", "classes": ["ketone"], "carbons": 5},
    "methyl_tert-butyl_ether": {"name": "Methyl tert-butyl ether", "classes": ["ether"], "carbons": 5},
    "neopentane": {"name": "Neopentane", "classes": ["alkane"], "carbons": 5},
    "propane": {"name": "Propane", "classes": ["alkane"], "carbons": 3},
    "propene": {"name": "Propene", "classes": ["alkene"], "carbons": 3},
    "propionitrile": {"name": "Propionitrile", "classes": ["nitrile"], "carbons": 3},
    "propyl_alcohol": {"name": "1-Propanol", "classes": ["alcohol"], "carbons": 3},
}

CLASS_ORDER = [
    "alcohol",
    "ketone",
    "ether",
    "alkane",
    "nitrile",
    "ester",
    "aromatic",
    "chlorinated",
    "aldehyde",
    "amine",
    "alkene",
    "cyanide",
]


def print_sanity(label: str, frame: pd.DataFrame) -> None:
    print(f"\nSANITY CHECK — {label}")
    print(f"rows={len(frame):,}; columns={len(frame.columns):,}")
    print("dtypes:")
    print(frame.dtypes.to_string())
    print("NaN counts:")
    print(frame.isna().sum().to_string())


def qm9_classes(smiles: str, iupac_name: str) -> list[str]:
    """Classify the simple acyclic QM9 subset using explicit string rules."""
    name = iupac_name.lower()
    classes: set[str] = set()
    if "nitrile" in name or "#n" in smiles.lower():
        classes.add("nitrile")
    if "amino" in name:
        classes.add("amine")
    if name.endswith("al") or name.endswith("dial"):
        classes.add("aldehyde")
    if name.endswith("one") or name.endswith("dione"):
        classes.add("ketone")
    if name.endswith("ol") or name.endswith("diol") or "hydroxy" in name:
        classes.add("alcohol")
    # All methoxy/ethoxy/propoxy/yloxy links in this curated subset are ethers.
    if any(token in name for token in ("methoxy", "ethoxy", "propoxy", "yloxy")):
        classes.add("ether")
    if re.fullmatch(r"[C()]+", smiles):
        classes.add("alkane")
    return [label for label in CLASS_ORDER if label in classes]


def is_candidate(classes: list[str], carbon_count: int) -> tuple[bool, str]:
    """Apply the documented broad solvent-vapor candidate screen."""
    labels = set(classes)
    if "aldehyde" in labels or "amine" in labels or "cyanide" in labels:
        return False, "excluded functional family"
    if "nitrile" in labels:
        if labels == {"nitrile"}:
            return True, "simple nitrile used as an industrial solvent family"
        return False, "multifunctional nitrile excluded from broad solvent screen"
    if labels.intersection({"alcohol", "ketone", "ether"}):
        return True, "requested solvent family"
    if "alkane" in labels and carbon_count >= 4:
        return True, "C4+ alkane/hydrocarbon solvent family"
    if "alkane" in labels:
        return False, "C1-C3 light gas excluded from solvent-vapor candidates"
    return False, "outside selected solvent families"


def build_identity_table(final_molecules: set[str]) -> pd.DataFrame:
    named_ids = {identifier for identifier in final_molecules if not identifier.startswith("dsgdb9nsd_")}
    if named_ids != set(INITIAL_MOLECULES):
        missing = sorted(named_ids.difference(INITIAL_MOLECULES))
        extra = sorted(set(INITIAL_MOLECULES).difference(named_ids))
        raise ValueError(f"Initial molecule mapping mismatch; missing={missing}; extra={extra}")

    rows: list[dict[str, object]] = []
    for molecule_id, metadata in INITIAL_MOLECULES.items():
        candidate, basis = is_candidate(metadata["classes"], int(metadata["carbons"]))
        rows.append(
            {
                "molecule_id": molecule_id,
                "molecule_name": metadata["name"],
                "chemical_class": " + ".join(metadata["classes"]),
                "candidate": candidate,
                "selection_basis": basis,
                "source_set": "initial named set",
                "qm9_smiles": "not_applicable",
                "identity_source_url": "https://zenodo.org/records/16754752",
            }
        )

    identity_document = json.loads(QM9_IDENTITIES.read_text(encoding="utf-8"))
    for record in identity_document["records"]:
        classes = qm9_classes(record["qm9_smiles"], record["iupac_name"])
        carbon_count = record["qm9_smiles"].count("C")
        candidate, basis = is_candidate(classes, carbon_count)
        title = record["pubchem_title"]
        if "," in title or title.endswith("-"):
            title = record["iupac_name"]
        rows.append(
            {
                "molecule_id": record["molecule_id"],
                "molecule_name": title,
                "chemical_class": " + ".join(classes),
                "candidate": candidate,
                "selection_basis": basis,
                "source_set": "QM9-derived OOD set",
                "qm9_smiles": record["qm9_smiles"],
                "identity_source_url": record["pubchem_source_url"],
            }
        )

    identities = pd.DataFrame(rows)
    if set(identities["molecule_id"]) != final_molecules:
        raise ValueError("Identity table does not exactly cover final.csv molecules")
    return identities


def scientific(value: float) -> str:
    return f"{value:.3e}"


def render_chart(top: pd.DataFrame, total_mofs: int) -> None:
    """Write a dependency-free SVG horizontal bar chart."""
    plot = top.sort_values(
        ["computed_mof_count", "molecule_name"], ascending=[False, True]
    ).copy()
    width, height = 1200, 1010
    left, right, top_margin, bottom = 335, 190, 88, 92
    plot_width = width - left - right
    row_height = (height - top_margin - bottom) / len(plot)
    bar_height = row_height * 0.64
    axis_max = 500
    colors = {"initial named set": "#003057", "QM9-derived OOD set": "#B3A369"}

    lines = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}" role="img" aria-labelledby="chart-title chart-desc">',
        '<title id="chart-title">Top 20 solvent-vapor candidates by computed-pair coverage</title>',
        f'<desc id="chart-desc">Horizontal bars show the number of MOFs with directly computed Henry constants out of {total_mofs} unique MOFs.</desc>',
        '<rect width="100%" height="100%" fill="#FFFFFF"/>',
        '<g font-family="Arial, Helvetica, sans-serif" fill="#17212B">',
        '<text x="24" y="34" font-size="22" font-weight="700">Top 20 solvent-vapor candidates by computed-pair coverage</text>',
    ]
    for tick in range(0, axis_max + 1, 100):
        x = left + plot_width * tick / axis_max
        lines.append(
            f'<line x1="{x:.1f}" y1="{top_margin - 8}" x2="{x:.1f}" y2="{height - bottom + 4}" stroke="#D9D9D9" stroke-width="1"/>'
        )
        lines.append(
            f'<text x="{x:.1f}" y="{height - bottom + 25}" text-anchor="middle" font-size="12" fill="#4B5563">{tick}</text>'
        )

    for index, row in enumerate(plot.itertuples(index=False)):
        center_y = top_margin + row_height * (index + 0.5)
        y = center_y - bar_height / 2
        bar_width = plot_width * row.computed_mof_count / axis_max
        color = colors[row.source_set]
        percent = 100 * row.computed_mof_count / total_mofs
        lines.extend(
            [
                f'<text x="{left - 12}" y="{center_y + 4:.1f}" text-anchor="end" font-size="12.5">{escape(str(row.molecule_name))}</text>',
                f'<rect x="{left}" y="{y:.1f}" width="{bar_width:.1f}" height="{bar_height:.1f}" fill="{color}"/>',
                f'<text x="{left + bar_width + 9:.1f}" y="{center_y + 4:.1f}" font-size="12.5" font-weight="700">{row.computed_mof_count:,} ({percent:.1f}%)</text>',
            ]
        )

    legend_y = height - 28
    lines.extend(
        [
            f'<text x="{left + plot_width / 2}" y="{height - bottom + 53}" text-anchor="middle" font-size="13" font-weight="700">MOFs with a directly computed Henry constant (count)</text>',
            f'<rect x="24" y="{legend_y - 12}" width="14" height="14" fill="#003057"/><text x="45" y="{legend_y}" font-size="12">Initial named set</text>',
            f'<rect x="175" y="{legend_y - 12}" width="14" height="14" fill="#B3A369"/><text x="196" y="{legend_y}" font-size="12">QM9-derived OOD set</text>',
            f'<text x="{width - 24}" y="{legend_y}" text-anchor="end" font-size="11" fill="#4B5563">Computed pairs only; denominator = {total_mofs:,} unique MOFs.</text>',
            "</g>",
            "</svg>",
        ]
    )
    CHART_SVG.write_text("\n".join(lines) + "\n", encoding="utf-8")


def render_report(
    final: pd.DataFrame,
    candidates: pd.DataFrame,
    top: pd.DataFrame,
    total_mofs: int,
    zero_count: int,
) -> None:
    class_counts = (
        candidates.assign(single_class=candidates["chemical_class"].str.split(r" \+ "))
        .explode("single_class")["single_class"]
        .value_counts()
        .sort_index()
    )
    class_summary = ", ".join(f"{name}: {count}" for name, count in class_counts.items())
    high_coverage_count = int((candidates["computed_mof_count"] == 471).sum())
    ood_max = int(
        candidates.loc[candidates["source_set"] == "QM9-derived OOD set", "computed_mof_count"].max()
    )

    table_lines = [
        "| Coverage rank | Molecule | Class | Computed MOFs | Coverage | Median K | IQR |",
        "|---:|---|---|---:|---:|---:|---:|",
    ]
    for row in top.itertuples(index=False):
        table_lines.append(
            "| "
            f"{row.coverage_rank} | {row.molecule_name} | {row.chemical_class} | "
            f"{row.computed_mof_count:,} | {row.coverage_percent:.1f}% | "
            f"{scientific(row.henry_median)} | {scientific(row.henry_iqr)} |"
        )

    report = f"""# D-MOPH-25 solvent-vapor coverage report

## Working data

- Directly computed data only: **{len(final):,} unique MOF–molecule pairs**, **{total_mofs:,} MOFs**, and **{final['mol'].nunique():,} molecules**.
- The deposited `K` column is the **linear Henry coefficient at {TEMPERATURE_K} K**, in **{HENRY_UNIT}**.
- The paper's regression model predicts `log10(K)`, but `final.csv` stores linear `K`. No logarithm was applied before the median and IQR calculations below.
- All reported quantiles use pandas' default linear interpolation over the directly computed `K` values for each molecule. Zeros are retained as deposited values.

## Evidence for units and scale

- Paper section 2.2 states that the constants were computed at 300 K by Widom insertion in RASPA2.0.
- Paper section 2.4.1 defines nonporous pairs using `K_H < 10^-15 mol kg^-1 Pa^-1`, establishing the reported unit.
- Figure 2 and section 2.4.2 state that the neural network predicts logarithmic Henry constants.
- Supplement section S9 writes the prediction error in `log(K_H)` and uses the `1/ln(10)` conversion, identifying the model transform as base-10 logarithm.
- The deposited `K` values are non-logarithmic: they are nonnegative and span zero through {final['K'].max():.3e}; a logarithmic column would contain negative values for `K < 1`.

Sources: [open paper](https://www.osti.gov/servlets/purl/3002420), [IOP supplementary data](https://iopscience.iop.org/article/10.1088/2632-2153/ae0241/data), and [Zenodo record](https://zenodo.org/records/16754752).

## Candidate-screen rule

This is a broad coverage screen, not a final panel choice. It includes alcohols, ketones, ethers, C4+ alkanes, and simple nitriles. Nitriles were included because acetonitrile and propionitrile are directly relevant industrial solvent vapors even though the original parenthetical class list did not name them. Multifunctional alcohol/ether and alcohol/ketone molecules are retained. C1–C3 alkanes, alkenes without another included function, aldehydes, amines, hydrogen cyanide, and multifunctional nitriles are excluded.

- Flagged candidates: **{len(candidates)}**
- Structural-family counts (multifunctional candidates can appear more than once): {class_summary}
- No ester, aromatic, or chlorinated molecule occurs among the 113 directly computed molecules.

## Top 20 candidates by computed-pair coverage

Henry statistics are in `{HENRY_UNIT}`.

{chr(10).join(table_lines)}

![Coverage bar chart](coverage_bar_chart.svg)

## Monday update bullets

- The verified working set contains **{len(final):,} directly computed MOF–molecule pairs** spanning **{total_mofs:,} MOFs and {final['mol'].nunique():,} molecules**; the two-pair publication discrepancy is documented and the deposited rows are authoritative for this analysis.
- The broad structural screen flags **{len(candidates)} plausible solvent-vapor candidates**; there are no ester, aromatic, or chlorinated candidates in the computed table.
- **{high_coverage_count} candidates each have 471 computed MOFs ({100 * 471 / total_mofs:.1f}% coverage)**, while the best QM9-derived candidate has only **{ood_max} MOFs ({100 * ood_max / total_mofs:.1f}%)**.
- Coverage is therefore highly uneven; these results identify candidates for Ken's panel decision but do **not** select the final 8–12 vapors or any MOF sensor array.

## Problems and cautions

- The two intended-but-absent pairs cannot be identified from the deposit; the analysis uses the {len(final):,} rows actually present.
- The QM9-derived candidates have sparse direct coverage (at most {ood_max} MOFs), so a panel containing many of them would produce a much less complete MOF × VOC matrix.
- `final.csv` contains **{zero_count:,} exact zero `K` values**. They are retained because they are deposited computed results, but they likely represent numerical underflow or effectively nonporous pairs.
- The structural screen is deliberately broad. Solvent use, toxicity, vapor pressure, and experimental availability must be reviewed before Ken chooses a final panel.
- The public Zenodo deposit does not contain the ML-completed table, optimized classifiers, or neural-network checkpoints described in the paper.
"""
    REPORT_MD.write_text(report, encoding="utf-8")


def main() -> None:
    OUTPUTS.mkdir(parents=True, exist_ok=True)

    final = pd.read_csv(FINAL_CSV, usecols=["mof", "mol", "K"])
    print_sanity("final.csv analysis columns", final)
    if final.duplicated(["mof", "mol"]).any():
        raise ValueError("final.csv contains duplicate MOF–molecule pairs")
    if not pd.api.types.is_numeric_dtype(final["K"]):
        raise TypeError("K is not numeric")

    total_mofs = final["mof"].nunique()
    identities = build_identity_table(set(final["mol"]))
    print_sanity("molecule identity and candidate flags", identities)
    print("candidate flag counts:")
    print(identities["candidate"].value_counts().to_string())

    grouped = final.groupby("mol", sort=False).agg(
        computed_pair_count=("K", "size"),
        computed_mof_count=("mof", "nunique"),
        henry_q1=("K", lambda values: values.quantile(0.25)),
        henry_median=("K", "median"),
        henry_q3=("K", lambda values: values.quantile(0.75)),
        zero_K_count=("K", lambda values: int((values == 0).sum())),
    )
    grouped["henry_iqr"] = grouped["henry_q3"] - grouped["henry_q1"]
    grouped["coverage_percent"] = 100 * grouped["computed_mof_count"] / total_mofs
    grouped = grouped.reset_index(names="molecule_id")
    print_sanity("per-molecule computed-pair statistics", grouped)
    if not (grouped["computed_pair_count"] == grouped["computed_mof_count"]).all():
        raise ValueError("A molecule has duplicate MOF entries")

    candidates = identities.loc[identities["candidate"]].merge(
        grouped, on="molecule_id", how="left", validate="one_to_one"
    )
    candidates = candidates.sort_values(
        ["computed_mof_count", "molecule_name", "molecule_id"],
        ascending=[False, True, True],
        kind="mergesort",
    ).reset_index(drop=True)
    candidates.insert(
        0,
        "coverage_rank",
        candidates["computed_mof_count"].rank(method="dense", ascending=False).astype(int),
    )
    candidates["henry_unit"] = HENRY_UNIT
    candidates["temperature_K"] = TEMPERATURE_K
    candidates["K_scale"] = "linear"
    candidates["quantile_method"] = "pandas linear interpolation"
    print_sanity("flagged solvent-vapor coverage table", candidates)

    ordered_columns = [
        "coverage_rank",
        "molecule_id",
        "molecule_name",
        "chemical_class",
        "source_set",
        "selection_basis",
        "computed_pair_count",
        "computed_mof_count",
        "coverage_percent",
        "henry_q1",
        "henry_median",
        "henry_q3",
        "henry_iqr",
        "zero_K_count",
        "henry_unit",
        "temperature_K",
        "K_scale",
        "quantile_method",
        "qm9_smiles",
        "identity_source_url",
    ]
    candidates = candidates[ordered_columns]
    top = candidates.head(20).copy()

    payload = {
        "metadata": {
            "computed_pair_rows": len(final),
            "unique_mofs": total_mofs,
            "unique_molecules": final["mol"].nunique(),
            "candidate_count": len(candidates),
            "henry_unit": HENRY_UNIT,
            "temperature_K": TEMPERATURE_K,
            "K_scale": "linear",
            "quantile_method": "pandas linear interpolation",
        },
        "columns": ordered_columns,
        "rows": candidates.replace({np.nan: None}).to_dict(orient="records"),
    }
    ANALYSIS_JSON.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    render_chart(top, total_mofs)
    render_report(final, candidates, top, total_mofs, int((final["K"] == 0).sum()))

    print("\nSANITY CHECK — generated outputs")
    for path in (ANALYSIS_JSON, REPORT_MD, CHART_SVG):
        print(f"{path.name}: exists={path.exists()}; bytes={path.stat().st_size:,}")


if __name__ == "__main__":
    main()
