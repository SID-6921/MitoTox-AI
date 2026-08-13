"""Stream mc5-6_winning_model_fits-flags (2.5GB) out of INVITRODB_SUMMARY.zip and
keep only rows for the mitochondrial-relevant assay endpoints defined in
docs/endpoint_definitions.md, writing a much smaller filtered CSV.
"""
import zipfile
import pandas as pd

RAW_DIR = "data/raw/invitrodb_v4_3"
ZIP_PATH = f"{RAW_DIR}/INVITRODB_SUMMARY.zip"
MEMBER = "mc5-6_winning_model_fits-flags_invitrodbv4_3_AUG2024.csv"
OUT_PATH = "data/processed/mito_mc5-6_hitcalls.csv"

MITO_AEIDS = {
    # primary: mitochondrial bioenergetic dysfunction (Seahorse respirometry)
    2442, 2444, 2446, 2450,
    # secondary A: mitochondrial membrane potential disruption
    12, 32, 52, 1854,
    # secondary B: mitochondrial oxidative stress
    97, 1110, 1185, 3324, 3325,
    # supporting HCS morphology (same Apredica battery as membrane potential)
    10, 30, 50, 14, 34, 54,
}

CHUNKSIZE = 200_000

def main():
    zf = zipfile.ZipFile(ZIP_PATH)
    kept_chunks = []
    with zf.open(MEMBER) as f:
        reader = pd.read_csv(f, chunksize=CHUNKSIZE, low_memory=False)
        total = 0
        for i, chunk in enumerate(reader):
            total += len(chunk)
            kept = chunk[chunk["aeid"].isin(MITO_AEIDS)]
            if len(kept):
                kept_chunks.append(kept)
            if i % 10 == 0:
                print(f"chunk {i}: scanned {total:,} rows, kept so far {sum(len(k) for k in kept_chunks):,}")

    out = pd.concat(kept_chunks, ignore_index=True)
    out.to_csv(OUT_PATH, index=False)
    print(f"wrote {len(out):,} rows to {OUT_PATH}")
    print(out["aeid"].value_counts())

if __name__ == "__main__":
    main()
