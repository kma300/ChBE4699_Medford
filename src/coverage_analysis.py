"""Analyze the approved eight-gas ethylene-cracker panel using computed pairs only."""

from __future__ import annotations

import json
from html import escape
from pathlib import Path

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
FINAL_CSV = ROOT / "data" / "dmoph25_data" / "final.csv"
OUTPUTS = ROOT / "outputs"
COVERAGE_CSV = OUTPUTS / "coverage_table.csv"
ANALYSIS_JSON = OUTPUTS / "coverage_analysis.json"
REPORT_MD = OUTPUTS / "coverage_report.md"
CHART_SVG = OUTPUTS / "coverage_bar_chart.svg"

HENRY_UNIT = "mol kg^-1 Pa^-1"
TEMPERATURE_K = 300
DATASET_URL = "https://zenodo.org/records/16754752"
PAPER_URL = "https://doi.org/10.1088/2632-2153/ae0241"

# The order follows the process story: fuel/by-product, feed, main product,
# secondary feed/product pairs, then coverage-matched C4/C5 proxies.
PANEL = [
    {
        "molecule_id": "methane",
        "molecule_name": "Methane",
        "process_role": "Cracking by-product / fuel gas",
        "panel_group": "core",
        "selection_basis": "Core outlet light gas",
    },
    {
        "molecule_id": "ethane",
        "molecule_name": "Ethane",
        "process_role": "Primary feed / unconverted feed",
        "panel_group": "core",
        "selection_basis": "Primary ethylene-cracker feed marker",
    },
    {
        "molecule_id": "ethene",
        "molecule_name": "Ethylene",
        "process_role": "Primary product",
        "panel_group": "core",
        "selection_basis": "Primary ethylene-cracker product marker",
    },
    {
        "molecule_id": "propane",
        "molecule_name": "Propane",
        "process_role": "Alternate feed / unconverted co-feed",
        "panel_group": "core",
        "selection_basis": "Secondary feed marker",
    },
    {
        "molecule_id": "propene",
        "molecule_name": "Propylene",
        "process_role": "Co-product",
        "panel_group": "core",
        "selection_basis": "Secondary cracked-product marker",
    },
    {
        "molecule_id": "isobutane",
        "molecule_name": "Isobutane",
        "process_role": "C4 light-end proxy",
        "panel_group": "proxy",
        "selection_basis": "Coverage-matched C4 process-gas proxy",
    },
    {
        "molecule_id": "isopentane",
        "molecule_name": "Isopentane",
        "process_role": "C5 / heavier-feed proxy",
        "panel_group": "proxy",
        "selection_basis": "Coverage-matched C5 paraffin proxy",
    },
    {
        "molecule_id": "2-pentene",
        "molecule_name": "2-Pentene",
        "process_role": "C5 olefin / cracked-product proxy",
        "panel_group": "proxy",
        "selection_basis": "Coverage-matched C5 olefin proxy",
    },
]


def print_sanity(label: str, frame: pd.DataFrame) -> None:
    """Print the requested row, dtype, and missing-value checks."""
    print(f"\nSANITY CHECK — {label}")
    print(f"rows={len(frame):,}; columns={len(frame.columns):,}")
    print("dtypes:")
    print(frame.dtypes.to_string())
    print("NaN counts:")
    print(frame.isna().sum().to_string())


def scientific(value: float) -> str:
    return f"{value:.3e}"


def validate_and_select(final: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    required = {"mof", "mol", "K"}
    missing = required.difference(final.columns)
    if missing:
        raise ValueError(f"final.csv lacks required columns: {sorted(missing)}")
    if final.duplicated(["mof", "mol"]).any():
        raise ValueError("final.csv contains duplicate MOF–molecule keys")
    if final["K"].isna().any() or not pd.api.types.is_numeric_dtype(final["K"]):
        raise ValueError("final.csv K values must be numeric and non-missing")

    panel_ids = [row["molecule_id"] for row in PANEL]
    selected = final.loc[final["mol"].isin(panel_ids), ["mof", "mol", "K"]].copy()
    print_sanity("selected eight-gas computed pairs", selected)

    counts = selected.groupby("mol").agg(
        computed_pair_count=("K", "size"),
        computed_mof_count=("mof", "nunique"),
    )
    missing_ids = sorted(set(panel_ids).difference(counts.index))
    if missing_ids:
        raise ValueError(f"Approved panel molecules absent from final.csv: {missing_ids}")
    if not (counts["computed_pair_count"] == 471).all():
        raise ValueError(f"Panel does not have uniform 471-pair coverage:\n{counts}")

    pivot = selected.pivot(index="mof", columns="mol", values="K").reindex(columns=panel_ids)
    print_sanity("common-MOF Henry matrix", pivot)
    if pivot.shape != (471, 8) or pivot.isna().any().any():
        raise ValueError(f"Expected a complete 471 x 8 matrix; got {pivot.shape}")
    if selected["mof"].nunique() != 471:
        raise ValueError("Selected gases do not share exactly 471 MOFs")
    return selected, pivot


def summarize_panel(final: pd.DataFrame, selected: pd.DataFrame, pivot: pd.DataFrame) -> pd.DataFrame:
    panel_metadata = pd.DataFrame(PANEL).reset_index(names="panel_order")
    panel_metadata["panel_order"] += 1

    quantiles = selected.groupby("mol")["K"].quantile([0.25, 0.5, 0.75]).unstack()
    quantiles.columns = ["henry_q1", "henry_median", "henry_q3"]
    summary = (
        selected.groupby("mol")
        .agg(
            computed_pair_count=("K", "size"),
            computed_mof_count=("mof", "nunique"),
            zero_K_count=("K", lambda values: int((values == 0).sum())),
        )
        .join(quantiles)
        .reset_index(names="molecule_id")
    )
    summary["henry_iqr"] = summary["henry_q3"] - summary["henry_q1"]
    summary = panel_metadata.merge(summary, on="molecule_id", validate="one_to_one")
    summary["common_mof_count"] = len(pivot)
    summary["coverage_rank"] = summary["computed_mof_count"].rank(
        method="dense", ascending=False
    ).astype(int)
    summary["coverage_percent"] = 100 * summary["computed_mof_count"] / final["mof"].nunique()
    summary["henry_unit"] = HENRY_UNIT
    summary["temperature_K"] = TEMPERATURE_K
    summary["K_scale"] = "linear"
    summary["quantile_method"] = "pandas linear interpolation; exact zeros retained"
    summary["dataset_source_url"] = DATASET_URL
    summary["process_evidence_url"] = (
        "https://www.epa.gov/sites/default/files/2015-03/documents/"
        "subpartx-tsd-petrochem.pdf"
    )
    summary = summary[
        [
            "panel_order",
            "coverage_rank",
            "molecule_id",
            "molecule_name",
            "process_role",
            "panel_group",
            "selection_basis",
            "computed_pair_count",
            "computed_mof_count",
            "common_mof_count",
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
            "dataset_source_url",
            "process_evidence_url",
        ]
    ]
    print_sanity("eight-gas coverage summary", summary)
    return summary


def matrix_diagnostics(pivot: pd.DataFrame) -> dict[str, object]:
    matrix = pivot.to_numpy(dtype=float)
    normalized = matrix / np.linalg.norm(matrix, axis=0)
    rank = int(np.linalg.matrix_rank(normalized))
    condition_number = float(np.linalg.cond(normalized))

    correlations = pivot.corr(method="spearman")
    pairs: list[dict[str, object]] = []
    for left_index, left in enumerate(correlations.columns):
        for right in correlations.columns[left_index + 1 :]:
            pairs.append(
                {
                    "molecule_1": left,
                    "molecule_2": right,
                    "spearman_rho": float(correlations.loc[left, right]),
                }
            )
    pairs.sort(key=lambda row: abs(float(row["spearman_rho"])), reverse=True)
    diagnostics = {
        "matrix_rows": int(pivot.shape[0]),
        "matrix_columns": int(pivot.shape[1]),
        "matrix_rank_after_column_normalization": rank,
        "condition_number_after_column_normalization": condition_number,
        "two_highest_absolute_spearman_correlations": pairs[:2],
    }
    print("\nSANITY CHECK — matrix diagnostics")
    print(json.dumps(diagnostics, indent=2))
    return diagnostics


def render_chart(summary: pd.DataFrame, total_mofs: int) -> None:
    """Write a dependency-free SVG bar chart from the summary dataframe."""
    plot = summary.sort_values(["computed_mof_count", "panel_order"], ascending=[False, True])
    width, height = 1200, 650
    left, right, top_margin, bottom = 250, 190, 94, 86
    plot_width = width - left - right
    row_height = (height - top_margin - bottom) / len(plot)
    bar_height = row_height * 0.58
    axis_max = 500
    colors = {"core": "#3D8DFF", "proxy": "#6DCBF4"}

    lines = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}" role="img" aria-labelledby="chart-title chart-desc">',
        '<title id="chart-title">Directly computed MOF coverage for the eight-gas process panel</title>',
        f'<desc id="chart-desc">Every gas has a directly computed Henry constant for the same 471 MOFs out of {total_mofs} unique MOFs.</desc>',
        '<rect width="100%" height="100%" fill="#FFFFFF"/>',
        '<g font-family="Arial, Helvetica, sans-serif" fill="#162236">',
        '<text x="24" y="34" font-size="22" font-weight="700">All eight process gases share the same 471 computed MOFs</text>',
        f'<text x="24" y="58" font-size="13" fill="#526071">Computed pairs only · denominator = {total_mofs:,} unique MOFs in final.csv</text>',
    ]
    for tick in range(0, axis_max + 1, 100):
        x = left + plot_width * tick / axis_max
        lines.append(
            f'<line x1="{x:.1f}" y1="{top_margin - 8}" x2="{x:.1f}" y2="{height - bottom + 4}" stroke="#D9E2EC" stroke-width="1"/>'
        )
        lines.append(
            f'<text x="{x:.1f}" y="{height - bottom + 24}" text-anchor="middle" font-size="12" fill="#526071">{tick}</text>'
        )

    for index, row in enumerate(plot.itertuples(index=False)):
        center_y = top_margin + row_height * (index + 0.5)
        y = center_y - bar_height / 2
        bar_width = plot_width * row.computed_mof_count / axis_max
        color = colors[row.panel_group]
        lines.extend(
            [
                f'<text x="{left - 14}" y="{center_y + 5:.1f}" text-anchor="end" font-size="15" font-weight="600">{escape(str(row.molecule_name))}</text>',
                f'<rect x="{left}" y="{y:.1f}" width="{bar_width:.1f}" height="{bar_height:.1f}" rx="4" fill="{color}"/>',
                f'<text x="{left + bar_width + 10:.1f}" y="{center_y + 5:.1f}" font-size="14" font-weight="700">{row.computed_mof_count:,} <tspan fill="#526071" font-weight="400">({row.coverage_percent:.1f}%)</tspan></text>',
            ]
        )

    legend_y = height - 24
    lines.extend(
        [
            f'<text x="{left + plot_width / 2}" y="{height - bottom + 52}" text-anchor="middle" font-size="13" font-weight="700">MOFs with a directly computed Henry constant</text>',
            f'<rect x="24" y="{legend_y - 12}" width="15" height="15" rx="3" fill="#3D8DFF"/><text x="47" y="{legend_y}" font-size="12">Core feed/product gases</text>',
            f'<rect x="205" y="{legend_y - 12}" width="15" height="15" rx="3" fill="#6DCBF4"/><text x="228" y="{legend_y}" font-size="12">C4/C5 coverage-matched proxies</text>',
            '<text x="1176" y="626" text-anchor="end" font-size="11" fill="#526071">Source: D-MOPH-25 final.csv</text>',
            "</g>",
            "</svg>",
        ]
    )
    CHART_SVG.write_text("\n".join(lines) + "\n", encoding="utf-8")


def render_report(
    final: pd.DataFrame,
    selected: pd.DataFrame,
    summary: pd.DataFrame,
    diagnostics: dict[str, object],
) -> None:
    total_mofs = int(final["mof"].nunique())
    top_pairs = diagnostics["two_highest_absolute_spearman_correlations"]
    table_lines = [
        "| Coverage rank | Gas | Process role | Directly computed MOFs | Coverage of 1,940 MOFs | Median K | IQR | Exact zeros |",
        "|---:|---|---|---:|---:|---:|---:|---:|",
    ]
    for row in summary.itertuples(index=False):
        table_lines.append(
            "| "
            f"{row.coverage_rank} | {row.molecule_name} | {row.process_role} | "
            f"{row.computed_mof_count:,} | {row.coverage_percent:.1f}% | "
            f"{scientific(row.henry_median)} | {scientific(row.henry_iqr)} | "
            f"{row.zero_K_count:,} |"
        )

    report = f"""# Eight-gas ethylene-cracker coverage report

## Monday result

The approved process-gas panel is **fully aligned across 471 MOFs**: all eight gases have a directly computed Henry constant for the same MOF set. This produces **{len(selected):,} computed MOF–gas pairs** with no missing values and no duplicate keys.

The 471-MOF set covers **{summary['coverage_percent'].iloc[0]:.1f}%** of the **{total_mofs:,} unique MOFs** in the deposited computed table. Because every gas has the same count, all eight tie for coverage rank 1; coverage does not distinguish among them.

## Approved target gases

{chr(10).join(table_lines)}

`K` is the **linear Henry coefficient at {TEMPERATURE_K} K** in **{HENRY_UNIT}**. Medians and quartiles are pandas dataframe quantiles with linear interpolation over directly computed values only; exact deposited zeros are retained. The paper predicts `log10(K)` during machine learning, but the deposited `final.csv` stores the nonnegative linear `K` values used here.

## Interpretation

- **Core feed/product group:** methane, ethane, ethylene, propane, and propylene.
- **Coverage-matched C4/C5 proxies:** isobutane, isopentane, and 2-pentene. These provide heavier light-end contrast; they are not a claim that each is a dominant product in every cracker.
- **Outlet means a conditioned extractive sample:** the intended measurement location is a post-quench/sample-conditioned sidestream near 300 K, not direct MOF exposure to raw furnace coil effluent near 850 °C.
- The normalized 471 × 8 Henry matrix has **rank {diagnostics['matrix_rank_after_column_normalization']}** but a condition number of **{diagnostics['condition_number_after_column_normalization']:.1f}**. The strongest monotonic similarities are {top_pairs[0]['molecule_1']}/{top_pairs[0]['molecule_2']} (Spearman ρ = {top_pairs[0]['spearman_rho']:.3f}) and {top_pairs[1]['molecule_1']}/{top_pairs[1]['molecule_2']} (ρ = {top_pairs[1]['spearman_rho']:.3f}). This supports starting with 12 MOFs for redundancy and reducing only after mixture testing.

## Four bullets for Monday

- D-MOPH-25 contains **{len(final):,} directly computed pairs**, **{total_mofs:,} MOFs**, and **{final['mol'].nunique():,} molecules** at **{TEMPERATURE_K} K**.
- The eight-gas ethylene-cracker panel yields a complete **471 MOFs × 8 gases = {len(selected):,} pair** comparison matrix.
- The target separates feed/product markers (ethane/ethylene and propane/propylene) and adds methane plus three C4/C5 process-gas proxies.
- Next: select **12 MOFs**, test gas identification, composition drift, and product/feed ratios, then reduce the array if performance is retained.

![Computed-pair coverage bar chart](coverage_bar_chart.svg)

## Boundaries and remaining inputs

- Computed pairs only: no ML-completed values are included.
- Henry constants are pure-component dilute-limit descriptors. Mixture-response assumptions, noise, competitive adsorption, humidity, and sensor transduction are not yet modeled.
- A percentage of the **true total outlet** requires concentrations for water, hydrogen, carbon monoxide, carbon dioxide, acetylene, and other stream species not in this eight-gas D-MOPH panel. Until then, an eight-gas-normalized percentage must be labeled as such.
- The next stage needs a representative post-quench outlet composition and operating ranges, an exact sample location, and a decision on whether to model only normal operation or also startup/upset states.

## Evidence

- Dataset and deposited `final.csv`: [D-MOPH-25 Zenodo record]({DATASET_URL})
- Units, 300 K calculation, and active-learning dataset description: [Choi, Sholl & Medford (2025)]({PAPER_URL})
- Ethylene-cracker process context: [U.S. EPA petrochemical technical support document](https://www.epa.gov/sites/default/files/2015-03/documents/subpartx-tsd-petrochem.pdf)
- Extractive furnace-effluent measurement context: [Siemens ethylene furnace-effluent analyzer note](https://cache.industry.siemens.com/dl/files/563/109770563/att_995347/v1/PIAAP-00002-0118-Ethylene.pdf)
"""
    REPORT_MD.write_text(report, encoding="utf-8")


def main() -> None:
    OUTPUTS.mkdir(parents=True, exist_ok=True)
    final = pd.read_csv(FINAL_CSV)
    print_sanity("D-MOPH final.csv", final)
    print("\nSANITY CHECK — final computed dataset inventory")
    print(f"unique_MOFs={final['mof'].nunique():,}")
    print(f"unique_molecules={final['mol'].nunique():,}")
    print(f"unique_pairs={final[['mof', 'mol']].drop_duplicates().shape[0]:,}")
    print(f"duplicate_keys={final.duplicated(['mof', 'mol']).sum():,}")

    selected, pivot = validate_and_select(final)
    summary = summarize_panel(final, selected, pivot)
    diagnostics = matrix_diagnostics(pivot)

    summary.to_csv(COVERAGE_CSV, index=False)
    render_chart(summary, int(final["mof"].nunique()))
    render_report(final, selected, summary, diagnostics)

    analysis = {
        "dataset": {
            "computed_pair_rows": int(len(final)),
            "unique_computed_pairs": int(final[["mof", "mol"]].drop_duplicates().shape[0]),
            "unique_mofs": int(final["mof"].nunique()),
            "unique_molecules": int(final["mol"].nunique()),
            "K_unit": HENRY_UNIT,
            "temperature_K": TEMPERATURE_K,
            "K_scale": "linear",
            "source_url": DATASET_URL,
        },
        "approved_panel": {
            "gas_count": int(summary["molecule_id"].nunique()),
            "computed_pairs": int(len(selected)),
            "common_mofs": int(len(pivot)),
            "missing_K": int(selected["K"].isna().sum()),
            "duplicate_keys": int(selected.duplicated(["mof", "mol"]).sum()),
            "molecules": summary["molecule_id"].tolist(),
        },
        "matrix_diagnostics": diagnostics,
    }
    ANALYSIS_JSON.write_text(json.dumps(analysis, indent=2) + "\n", encoding="utf-8")

    written = pd.read_csv(COVERAGE_CSV)
    print_sanity("written coverage_table.csv", written)
    print("\nSANITY CHECK — generated output files")
    for path in (COVERAGE_CSV, ANALYSIS_JSON, REPORT_MD, CHART_SVG):
        print(f"{path.relative_to(ROOT)}: {path.stat().st_size:,} bytes")
    print(f"coverage_rows={len(written):,}")
    print(f"coverage_counts={sorted(written['computed_mof_count'].unique().tolist())}")
    print(f"coverage_missing_values={int(written.isna().sum().sum()):,}")


if __name__ == "__main__":
    main()
