"""Join the filtered mitochondrial hit-call table to DSSTox chemical structures
(DTXSID -> SMILES / QSAR-ready SMILES), streaming the 664MB DSSTox master dump
in chunks so only the ~9.4k chemicals we actually need are kept in memory.
"""
import zipfile
import pandas as pd

HITCALLS_PATH = "data/processed/mito_mc5-6_hitcalls.csv"
DSSTOX_ZIP = "data/raw/dsstox/DSSTox_CCD_dump_12092025_CSVs.zip"
DSSTOX_MEMBER = "DSSTox_CCD_dump_12092025/DSSToxCCDdump.csv"
OUT_PATH = "data/processed/mito_chemicals_with_structures.csv"

CHUNKSIZE = 100_000

def main():
    hitcalls = pd.read_csv(HITCALLS_PATH, low_memory=False)
    needed_ids = set(hitcalls["dsstox_substance_id"].dropna().unique())
    print(f"need structures for {len(needed_ids):,} chemicals")

    zf = zipfile.ZipFile(DSSTOX_ZIP)
    keep_cols = ["DTXSID", "PREFERRED_NAME", "CASRN", "SMILES", "QSAR_READY_SMILES", "MOLECULAR_FORMULA"]
    kept_chunks = []
    with zf.open(DSSTOX_MEMBER) as f:
        reader = pd.read_csv(f, chunksize=CHUNKSIZE, usecols=keep_cols, low_memory=False)
        for i, chunk in enumerate(reader):
            kept = chunk[chunk["DTXSID"].isin(needed_ids)]
            if len(kept):
                kept_chunks.append(kept)

    structures = pd.concat(kept_chunks, ignore_index=True).drop_duplicates(subset="DTXSID")
    print(f"found structures for {len(structures):,} / {len(needed_ids):,} chemicals")
    missing = needed_ids - set(structures["DTXSID"])
    if missing:
        print(f"missing structures for {len(missing)} DTXSIDs (e.g. {list(missing)[:5]})")

    structures.to_csv(OUT_PATH, index=False)
    print(f"wrote {OUT_PATH}")

if __name__ == "__main__":
    main()
