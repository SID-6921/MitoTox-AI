"""Build the Step 2 modeling dataset: ECFP4 fingerprints + physicochemical
descriptors joined to the locked primary label (mmp_ratio_tox21, aeid 1854),
restricted to the 7,268 chemicals actually tested on that endpoint.
"""
import pandas as pd

MODELING_TABLE_PATH = "data/processed/mito_modeling_table.csv"
FINGERPRINTS_PATH = "data/processed/mito_chemicals_fingerprints.csv"
OUT_PATH = "data/processed/step2_mmp_dataset.csv"

DESCRIPTOR_COLS = [
    "mol_weight", "logp", "tpsa", "hbd", "hba",
    "rotatable_bonds", "aromatic_rings", "heavy_atoms", "fraction_csp3",
]


def main():
    modeling = pd.read_csv(MODELING_TABLE_PATH, low_memory=False)
    fps = pd.read_csv(FINGERPRINTS_PATH, low_memory=False)

    labeled = modeling[modeling["mmp_ratio_tox21"].notna()].copy()
    print(f"chemicals tested on primary endpoint (mmp_ratio_tox21): {len(labeled):,}")

    keep_cols = [
        "DTXSID", "canonical_smiles", "mmp_ratio_tox21",
        "mmp_ratio_tox21_ac50_um", "mmp_ratio_tox21_efficacy_top",
        "mmp_ratio_tox21_cytotox_confound",
    ] + DESCRIPTOR_COLS
    dataset = labeled[keep_cols].merge(fps, on="DTXSID", how="inner")
    assert len(dataset) == len(labeled), "lost rows joining to fingerprints - every clean chemical should have one"

    dataset = dataset.rename(columns={"mmp_ratio_tox21": "label"})
    dataset.to_csv(OUT_PATH, index=False)
    print(f"label balance: {dataset['label'].value_counts().to_dict()}")
    print(f"wrote {len(dataset):,} chemicals x {dataset.shape[1]} columns -> {OUT_PATH}")


if __name__ == "__main__":
    main()
