"""Fill three gaps left by 01-04: potency/efficacy weren't carried into the
modeling table, QC flags weren't decoded, and the cytotoxicity burst table
was downloaded but never used. Kolliputi's brief asked for all three
("hit calls, potency/AC50, efficacy, QC information, and relevant
cytotoxicity information").
"""
import zipfile
import pandas as pd

HITCALLS_PATH = "data/processed/mito_mc5-6_hitcalls.csv"
MODELING_TABLE_PATH = "data/processed/mito_modeling_table.csv"
METHODS_ZIP_MEMBER = "methods_invitrodb_v4_3_AUG2024.xlsx"
INVITRODB_ZIP = "data/raw/invitrodb_v4_3/INVITRODB_SUMMARY.zip"
CYTOTOX_XLSX = "data/raw/invitrodb_v4_3/cytotox_invitrodb_v4_3_AUG2024.xlsx"

OUT_LONG_PATH = "data/processed/mito_hitcalls_enriched.csv"
# ponytail: reads and overwrites the same file 04 produces, so rerunning this
# script twice in a row without rerunning 04 first double-merges and breaks.
# Always run 04 then 05, not 05 alone.
OUT_MODELING_PATH = "data/processed/mito_modeling_table.csv"

ENDPOINT_LABELS = {
    2442: "primary_basal_resp_rate", 2444: "primary_max_resp_rate",
    2446: "primary_inhib_resp_rate", 2450: "primary_mito_viability",
    12: "mmp_1hr", 32: "mmp_24hr", 52: "mmp_72hr", 1854: "mmp_ratio_tox21",
    97: "oxstress_nrf2_are_cis",
    1110: "oxstress_are_bla_ratio", 1185: "oxstress_are_bla_viability",
    3324: "oxstress_are_ks_luc", 3325: "oxstress_are_ks_luc_viability",
    10: "mitomass_1hr", 30: "mitomass_24hr", 50: "mitomass_72hr",
    14: "mitoticarrest_1hr", 34: "mitoticarrest_24hr", 54: "mitoticarrest_72hr",
}


def decode_flags(flag_str, flag_lookup):
    if not isinstance(flag_str, str) or not flag_str.strip():
        return ""
    ids = [int(x) for x in flag_str.split(",")]
    return "; ".join(flag_lookup.get(i, f"unknown_flag_{i}") for i in ids)


def main():
    hitcalls = pd.read_csv(HITCALLS_PATH, low_memory=False)

    # decode QC flags
    zf = zipfile.ZipFile(INVITRODB_ZIP)
    with zf.open(METHODS_ZIP_MEMBER) as f:
        methods = pd.read_excel(f, sheet_name="method_list")
    mc6 = methods[methods["lvl"] == "mc6"]
    flag_lookup = dict(zip(mc6["mthd_id"], mc6["mthd"]))
    hitcalls["mc6_flags_decoded"] = hitcalls["mc6_flags"].apply(lambda s: decode_flags(s, flag_lookup))

    # join cytotoxicity burst reference and flag hits at/below the burst threshold
    cytotox = pd.read_excel(CYTOTOX_XLSX)[["dsstox_substance_id", "cytotox_median_um", "cytotox_lower_bound_um"]]
    hitcalls = hitcalls.merge(cytotox, on="dsstox_substance_id", how="left")
    hitcalls["likely_cytotox_confound"] = (
        (hitcalls["hitcall"] >= 0.9)
        & hitcalls["ac50"].notna()
        & hitcalls["cytotox_lower_bound_um"].notna()
        & (hitcalls["ac50"] >= hitcalls["cytotox_lower_bound_um"])
    )

    hitcalls.to_csv(OUT_LONG_PATH, index=False)
    print(f"wrote {len(hitcalls):,} rows (includes test replicates) -> {OUT_LONG_PATH}")

    # dedup to one row per chemical-endpoint pair (keep highest hitcall) before
    # computing any aggregate stat or building the wide table - 61,664 raw rows
    # include 10,186 replicate retests, which would otherwise double-count hits
    dedup = hitcalls.sort_values("hitcall", ascending=False).drop_duplicates(subset=["dsstox_substance_id", "aeid"])
    dedup = dedup.copy()
    dedup["endpoint"] = dedup["aeid"].map(ENDPOINT_LABELS)

    n_hits = int((dedup["hitcall"] >= 0.9).sum())
    n_confound = int(dedup["likely_cytotox_confound"].sum())
    print(f"unique chemical-endpoint pairs: {len(dedup):,}; active hits: {n_hits:,}; "
          f"of those, at/above the chemical's cytotoxicity burst threshold: "
          f"{n_confound:,} ({100*n_confound/n_hits:.1f}%)")

    ac50_wide = dedup.pivot_table(index="dsstox_substance_id", columns="endpoint", values="ac50", aggfunc="first")
    ac50_wide.columns = [f"{c}_ac50_um" for c in ac50_wide.columns]
    efficacy_wide = dedup.pivot_table(index="dsstox_substance_id", columns="endpoint", values="top", aggfunc="first")
    efficacy_wide.columns = [f"{c}_efficacy_top" for c in efficacy_wide.columns]
    confound_wide = dedup.pivot_table(index="dsstox_substance_id", columns="endpoint", values="likely_cytotox_confound", aggfunc="first")
    confound_wide.columns = [f"{c}_cytotox_confound" for c in confound_wide.columns]

    modeling = pd.read_csv(MODELING_TABLE_PATH, low_memory=False)
    modeling = modeling.merge(ac50_wide, left_on="DTXSID", right_index=True, how="left")
    modeling = modeling.merge(efficacy_wide, left_on="DTXSID", right_index=True, how="left")
    modeling = modeling.merge(confound_wide, left_on="DTXSID", right_index=True, how="left")
    modeling = modeling.merge(
        cytotox.rename(columns={"dsstox_substance_id": "DTXSID"}), on="DTXSID", how="left"
    )
    modeling.to_csv(OUT_MODELING_PATH, index=False)
    print(f"wrote {len(modeling):,} chemicals x {modeling.shape[1]} columns -> {OUT_MODELING_PATH}")


if __name__ == "__main__":
    main()
