"""Build the final wide modeling table: one row per clean chemical, one column
per mitochondrial endpoint (binary hit call at hitcall >= 0.9), joined to
descriptors. Fingerprints are kept in a separate file (2048 columns) to keep
this one readable.
"""
import pandas as pd

HITCALLS_PATH = "data/processed/mito_mc5-6_hitcalls.csv"
CLEAN_CHEM_PATH = "data/processed/mito_chemicals_clean.csv"
OUT_PATH = "data/processed/mito_modeling_table.csv"
SUMMARY_PATH = "docs/data_summary.md"

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

GROUPS = {
    "primary": [2442, 2444, 2446],
    "secondary_membrane_potential": [12, 32, 52, 1854],
    "secondary_oxidative_stress": [97, 1110, 3324],
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

    lines = [
        "# Data summary (Step 1, draft)",
        "",
        f"Source: invitrodb v4.3 (EPA ToxCast/Tox21, Aug 2025) + DSSTox structure dump (Dec 2025).",
        f"Endpoint definitions: see `docs/endpoint_definitions.md`.",
        "",
        "## Pipeline yield",
        f"- Chemicals tested across the 19 mitochondrial-relevant endpoints: 9,398",
        f"- Structures found in DSSTox: 9,398 / 9,398 (100%)",
        f"- Passed structure standardization (parseable, organic, non-mixture): 8,716",
        f"- Unique after canonical-structure dedup: 8,067",
        f"- Chemicals with at least one mitochondrial-endpoint label in the final table: {len(modeling_table):,}",
        "",
        f"(Hit-call threshold for 'active': hitcall >= {HITCALL_THRESHOLD}, the standard EPA/tcpl convention.)",
        "",
        "## Class balance by endpoint",
        "",
        "| endpoint | n tested | n active | % active |",
        "|---|---|---|---|",
    ]
    for aeid, name in ENDPOINT_LABELS.items():
        if name not in modeling_table.columns:
            continue
        col = modeling_table[name]
        n_tested = col.notna().sum()
        n_active = (col == 1).sum()
        pct = 100 * n_active / n_tested if n_tested else float("nan")
        lines.append(f"| {name} (aeid {aeid}) | {n_tested} | {n_active} | {pct:.1f}% |")

    lines += [
        "",
        "## Notes",
        "- Primary endpoint (bioenergetic dysfunction / Seahorse respirometry) has a much",
        "  smaller tested chemical set (~270-280 chemicals) than the Tox21 qHTS reporter",
        "  assays (~9,000+) used for the secondary endpoints - this caps the primary model's",
        "  training set size regardless of scaffold-split strategy.",
        "- 682 chemicals dropped at structure-cleaning (568 no SMILES, 72 inorganic/no carbon,",
        "  26 mixtures with no dominant fragment, 11 unparseable, 5 too small). Full list in",
        "  `data/processed/mito_chemicals_dropped.csv`.",
        "- These endpoint definitions are a draft for review, not locked (per project brief).",
    ]

    with open(SUMMARY_PATH, "w") as f:
        f.write("\n".join(lines) + "\n")
    print(f"wrote {SUMMARY_PATH}")


if __name__ == "__main__":
    main()
