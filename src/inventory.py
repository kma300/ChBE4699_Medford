"""Inventory the deposited D-MOPH-25 tables without modifying source data."""

from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data" / "dmoph25_data"


def print_frame_sanity(label: str, frame: pd.DataFrame) -> None:
    """Print the requested row, dtype, and missing-value checks."""
    print(f"\nSANITY CHECK — {label}")
    print(f"rows={len(frame):,}; columns={len(frame.columns):,}")
    print("dtypes:")
    print(frame.dtypes.to_string())
    print("NaN counts:")
    print(frame.isna().sum().to_string())


def main() -> None:
    final_path = DATA / "final.csv"
    final = pd.read_csv(final_path)
    print_frame_sanity("final.csv", final)

    required = {"mof", "mol", "K"}
    missing = required.difference(final.columns)
    if missing:
        raise ValueError(f"final.csv lacks required columns: {sorted(missing)}")

    pair_duplicates = final.duplicated(["mof", "mol"]).sum()
    print("\nSANITY CHECK — final computed-pair keys")
    print(f"unique_MOFs={final['mof'].nunique():,}")
    print(f"unique_molecules={final['mol'].nunique():,}")
    print(f"rows={len(final):,}")
    print(f"unique_MOF_molecule_pairs={final[['mof', 'mol']].drop_duplicates().shape[0]:,}")
    print(f"duplicate_MOF_molecule_rows={pair_duplicates:,}")
    print(f"K_non_numeric={pd.to_numeric(final['K'], errors='coerce').isna().sum():,}")

    split_counts: dict[str, dict[str, int]] = {}
    for split in ("initial", "val", "ood"):
        mof = pd.read_csv(DATA / "datasets" / split / "mof.csv")
        mol = pd.read_csv(DATA / "datasets" / split / "mol.csv")
        print_frame_sanity(f"datasets/{split}/mof.csv", mof)
        print_frame_sanity(f"datasets/{split}/mol.csv", mol)
        split_counts[split] = {
            "mofs": mof["mof"].nunique(),
            "molecules": mol["mol"].nunique(),
        }

    all_mofs = set()
    all_molecules = set()
    for split in ("initial", "val", "ood"):
        all_mofs.update(pd.read_csv(DATA / "datasets" / split / "mof.csv", usecols=["mof"])["mof"])
        all_molecules.update(pd.read_csv(DATA / "datasets" / split / "mol.csv", usecols=["mol"])["mol"])

    print("\nSANITY CHECK — declared target-space descriptor lists")
    for split, counts in split_counts.items():
        print(f"{split}: MOFs={counts['mofs']:,}; molecules={counts['molecules']:,}")
    print(f"union_MOFs={len(all_mofs):,}")
    print(f"union_molecules={len(all_molecules):,}")
    print(f"Cartesian_target_pairs={len(all_mofs) * len(all_molecules):,}")

    iteration_rows = []
    for iteration in range(50):
        frame = pd.read_csv(
            DATA / "iterations" / f"{iteration}.csv",
            usecols=["mof", "mol", "K"],
        )
        iteration_rows.append((iteration, len(frame), frame["mof"].nunique(), frame["mol"].nunique()))

    print("\nSANITY CHECK — active-learning iteration endpoints")
    for iteration, rows, mofs, molecules in (iteration_rows[0], iteration_rows[-1]):
        print(f"iteration={iteration}; rows={rows:,}; MOFs={mofs:,}; molecules={molecules:,}")
    increments = [iteration_rows[i][1] - iteration_rows[i - 1][1] for i in range(1, 50)]
    print(f"iteration_row_increment_min={min(increments):,}")
    print(f"iteration_row_increment_max={max(increments):,}")
    print(f"final_minus_iteration_49={len(final) - iteration_rows[-1][1]:,}")


if __name__ == "__main__":
    main()
