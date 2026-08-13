"""Build the final wide modeling table: one row per clean chemical, one column
per mitochondrial endpoint (binary hit call at hitcall >= 0.9), joined to
descriptors. Fingerprints are kept in a separate file (2048 columns) to keep
this one readable.

docs/data_summary.md is written by scripts/06_write_data_summary.py, which
reads this table after 05_enrich_potency_qc_cytotox.py has added potency/
efficacy/cytotoxicity columns to it - not here, so the doc is always built
from final data instead of being partially overwritten by whichever script
ran last.
"""
import pandas as pd

HITCALLS_PATH = "data/processed/mito_mc5-6_hitcalls.csv"
CLEAN_CHEM_PATH = "data/processed/mito_chemicals_clean.csv"
OUT_PATH = "data/processed/mito_modeling_table.csv"

HITCALL_THRESHOLD = 0.9

ENDPOINT_LABELS = {
    2442: "primary_basal_resp_rate",
    2444: "primary_max_resp_rate",
    2446: "primary_inhib_resp_rate",
    2450: "primary_mito_viability",
    12: "mmp_1hr", 32: "mmp_24hr", 52: "mmp_72hr", 1854: "mmp_ratio_tox21",
    97: "oxstress_nrf2_are_cis",
    1110: "oxstress_are_bla_ratio", 1185: "oxstress_are_bla_viability",
    3324: "oxstress_are_ks_luc", 3325: "oxstress_are_ks_luc_viability",
    10: "mitomass_1hr", 30: "mitomass_24hr", 50: "mitomass_72hr",
    14: "mitoticarrest_1hr", 34: "mitoticarrest_24hr", 54: "mitoticarrest_72hr",
}

def main():
    hitcalls = pd.read_csv(HITCALLS_PATH, low_memory=False)
    clean_chem = pd.read_csv(CLEAN_CHEM_PATH, low_memory=False)
    clean_ids = set(clean_chem["DTXSID"])

    hitcalls = hitcalls[hitcalls["dsstox_substance_id"].isin(clean_ids)].copy()
    hitcalls["active"] = (hitcalls["hitcall"] >= HITCALL_THRESHOLD).astype(int)
    hitcalls["endpoint"] = hitcalls["aeid"].map(ENDPOINT_LABELS)

    # one chemical can appear more than once per aeid across model reruns; keep max hitcall
    dedup = hitcalls.sort_values("hitcall", ascending=False).drop_duplicates(subset=["dsstox_substance_id", "aeid"])

    wide = dedup.pivot_table(index="dsstox_substance_id", columns="endpoint", values="active", aggfunc="max")
    wide = wide.reset_index().rename(columns={"dsstox_substance_id": "DTXSID"})

    modeling_table = clean_chem.merge(wide, on="DTXSID", how="inner")
    modeling_table.to_csv(OUT_PATH, index=False)
    print(f"wrote {len(modeling_table):,} chemicals x {modeling_table.shape[1]} columns -> {OUT_PATH}")


if __name__ == "__main__":
    main()
