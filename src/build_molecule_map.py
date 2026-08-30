"""Build an auditable D-MOPH/QM9 molecule identity map.

The D-MOPH OOD molecule identifiers are QM9 filenames. This script reads only
the 83 requested records from the official QM9 archive and resolves display
names through the NIH PubChem PUG REST service.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import tarfile
import time
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
OOD_MOLECULES = ROOT / "data" / "dmoph25_data" / "datasets" / "ood" / "mol.csv"
DEFAULT_OUTPUT = ROOT / "data" / "reference" / "qm9_molecule_identities.json"

QM9_ARTICLE_URL = (
    "https://springernature.figshare.com/articles/dataset/"
    "Data_for_133885_GDB-9_molecules/1057646"
)
QM9_DEPOSITED_FILENAME = "dsgdb9nsd.xyz.tar.bz2"
QM9_API_URL = "https://api.figshare.com/v2/articles/1057646"
QM9_DOWNLOAD_URL = "https://ndownloader.figshare.com/files/3195389"
PUBCHEM_ENDPOINT = (
    "https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/inchi/property/"
    "Title,IUPACName,CanonicalSMILES,IsomericSMILES,InChIKey/JSON"
)


def file_hash(path: Path, algorithm: str) -> str:
    digest = hashlib.new(algorithm)
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def parse_qm9_xyz(payload: bytes) -> tuple[str, str]:
    lines = payload.decode("utf-8").splitlines()
    atom_count = int(lines[0])
    smiles = lines[atom_count + 3].split()[0]
    inchi = lines[atom_count + 4].split()[0]
    return smiles, inchi


def pubchem_lookup(inchi: str) -> dict[str, object]:
    body = urllib.parse.urlencode({"inchi": inchi}).encode("utf-8")
    last_error: Exception | None = None
    for attempt in range(5):
        try:
            request = urllib.request.Request(
                PUBCHEM_ENDPOINT,
                data=body,
                headers={"User-Agent": "GeorgiaTech-ChBE4699-research/1.0"},
            )
            with urllib.request.urlopen(request, timeout=45) as response:
                result = json.load(response)
            return result["PropertyTable"]["Properties"][0]
        except Exception as error:  # PubChem occasionally rate-limits requests.
            last_error = error
            time.sleep(2**attempt)
    raise RuntimeError(f"PubChem lookup failed for {inchi}: {last_error}")


def print_sanity(label: str, frame: pd.DataFrame) -> None:
    print(f"\nSANITY CHECK — {label}")
    print(f"rows={len(frame):,}; columns={len(frame.columns):,}")
    print("dtypes:")
    print(frame.dtypes.to_string())
    print("NaN counts:")
    print(frame.isna().sum().to_string())


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("qm9_archive", type=Path)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()

    ood = pd.read_csv(OOD_MOLECULES, usecols=["mol"])
    print_sanity("D-MOPH OOD molecule identifiers", ood)
    if ood["mol"].duplicated().any():
        raise ValueError("OOD molecule list contains duplicate identifiers")

    wanted = set(ood["mol"])
    records: list[dict[str, object]] = []
    with tarfile.open(args.qm9_archive, mode="r:bz2") as archive:
        for molecule_id in sorted(wanted):
            member_name = f"{molecule_id}.xyz"
            extracted = archive.extractfile(member_name)
            if extracted is None:
                raise FileNotFoundError(f"QM9 archive lacks {member_name}")
            smiles, inchi = parse_qm9_xyz(extracted.read())
            pubchem = pubchem_lookup(inchi)
            records.append(
                {
                    "molecule_id": molecule_id,
                    "qm9_smiles": smiles,
                    "inchi": inchi,
                    "pubchem_cid": pubchem.get("CID"),
                    "pubchem_title": pubchem.get("Title"),
                    "iupac_name": pubchem.get("IUPACName"),
                    "pubchem_smiles": pubchem.get("SMILES"),
                    "inchi_key": pubchem.get("InChIKey"),
                    "qm9_source_url": QM9_ARTICLE_URL,
                    "pubchem_source_url": (
                        "https://pubchem.ncbi.nlm.nih.gov/compound/"
                        f"{pubchem.get('CID')}"
                    ),
                }
            )
            time.sleep(0.12)

    identities = pd.DataFrame(records)
    print_sanity("resolved QM9 molecule identities", identities)
    if set(identities["molecule_id"]) != wanted:
        raise ValueError("Resolved QM9 identifiers do not exactly match D-MOPH OOD list")
    if identities["molecule_id"].duplicated().any():
        raise ValueError("Resolved identity map contains duplicate identifiers")

    document = {
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "qm9_archive": {
            "deposited_filename": QM9_DEPOSITED_FILENAME,
            "local_input_filename": args.qm9_archive.name,
            "size_bytes": args.qm9_archive.stat().st_size,
            "md5": file_hash(args.qm9_archive, "md5"),
            "sha256": file_hash(args.qm9_archive, "sha256"),
            "figshare_article_url": QM9_ARTICLE_URL,
            "figshare_api_url": QM9_API_URL,
            "download_url": QM9_DOWNLOAD_URL,
        },
        "pubchem_endpoint": PUBCHEM_ENDPOINT,
        "record_count": len(records),
        "records": records,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(document, indent=2) + "\n", encoding="utf-8")
    print(f"\nwrote={args.output}")


if __name__ == "__main__":
    main()
