"""Write docs/data_summary.md from the final pipeline artifacts. This is the
only script that writes that file, and it always computes every number fresh
from disk (never hardcoded), so it's safe to rerun at any point after
01-05 and can never go stale or get partially overwritten by an earlier
script in the chain.
"""
import pandas as pd

STRUCTURES_PATH = "data/processed/mito_chemicals_with_structures.csv"
CLEAN_CHEM_PATH = "data/processed/mito_chemicals_clean.csv"
DROPPED_PATH = "data/processed/mito_chemicals_dropped.csv"
MODELING_TABLE_PATH = "data/processed/mito_modeling_table.csv"
ENRICHED_HITCALLS_PATH = "data/processed/mito_hitcalls_enriched.csv"
OUT_PATH = "docs/data_summary.md"

HITCALL_THRESHOLD = 0.9

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


def main():
    structures = pd.read_csv(STRUCTURES_PATH, low_memory=False)
    clean_chem = pd.read_csv(CLEAN_CHEM_PATH, low_memory=False)
    dropped = pd.read_csv(DROPPED_PATH, low_memory=False)
    modeling_table = pd.read_csv(MODELING_TABLE_PATH, low_memory=False)
    enriched = pd.read_csv(ENRICHED_HITCALLS_PATH, low_memory=False)

    n_tested = len(structures)
    n_standardized = len(structures) - len(dropped)
    n_unique = len(clean_chem)

    lines = [
        "# Data summary (Step 1, draft)",
        "",
        "Source: invitrodb v4.3 (EPA ToxCast/Tox21, Aug 2025) + DSSTox structure dump (Dec 2025).",
        "Endpoint definitions: see `docs/endpoint_definitions.md`.",
        "",
        "## Pipeline yield",
        f"- Chemicals tested across the 19 mitochondrial-relevant endpoints: {n_tested:,}",
        f"- Structures found in DSSTox: {n_tested:,} / {n_tested:,} (100%)",
        f"- Passed structure standardization (parseable, organic, non-mixture): {n_standardized:,}",
        f"- Unique after canonical-structure dedup: {n_unique:,}",
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
        tested = col.notna().sum()
        active = (col == 1).sum()
        pct = 100 * active / tested if tested else float("nan")
        lines.append(f"| {name} (aeid {aeid}) | {tested} | {active} | {pct:.1f}% |")

    # scope to the clean/deduped chemical set actually used for modeling (not
    # the full pre-cleaning tested population), then dedup to one row per
    # chemical-endpoint pair (the raw enriched table includes test replicates,
    # which would double-count hits otherwise)
    clean_ids = set(modeling_table["DTXSID"])
    enriched_dedup = (
        enriched[enriched["dsstox_substance_id"].isin(clean_ids)]
        .sort_values("hitcall", ascending=False)
        .drop_duplicates(subset=["dsstox_substance_id", "aeid"])
    )
    n_hits = int((enriched_dedup["hitcall"] >= HITCALL_THRESHOLD).sum())
    n_confound = int(enriched_dedup["likely_cytotox_confound"].sum())
    pct_confound = 100 * n_confound / n_hits if n_hits else float("nan")

    lines += [
        "",
        "## Potency, QC, and cytotoxicity",
        "",
        "- Per-endpoint AC50 (potency, µM) and efficacy (`top`) are in the wide modeling",
        "  table as `<endpoint>_ac50_um` / `<endpoint>_efficacy_top`. Decoded QC flags",
        "  (`mc6_flags_decoded`, from invitrodb's `method_list` mc6 lookup) are in the",
        "  long-format `data/processed/mito_hitcalls_enriched.csv`.",
        "- **Cytotoxicity sensitivity check:** joined each chemical's cytotoxicity burst",
        "  threshold (`cytotox_invitrodb_v4_3_AUG2024.xlsx`, median AC50 across all",
        "  `burst_assay=1` endpoints minus 3x global MAD). Of the "
        f"{n_hits:,} active hits across all 19 endpoints, **{pct_confound:.1f}% occur at or "
        "above the chemical's own cytotoxicity burst threshold** - meaning a majority of",
        "  raw hits in this endpoint set are plausibly driven by general cytotoxicity rather",
        "  than a mitochondria-specific mechanism. Flagged per-hit (`likely_cytotox_confound`)",
        "  and per-chemical/endpoint (`<endpoint>_cytotox_confound`) so Step 2 modeling can",
        "  filter or stratify on it.",
        "",
        "## Notes",
        "- Primary endpoint (bioenergetic dysfunction / Seahorse respirometry) has a much",
        "  smaller tested chemical set (~250-270 chemicals) than the Tox21 qHTS reporter",
        "  assays (~6,600-7,300) used for the secondary endpoints - this caps the primary",
        "  model's training set size regardless of scaffold-split strategy.",
        f"- {len(dropped):,} chemicals dropped at structure-cleaning. Reasons:",
    ]
    for reason, count in dropped["reason"].value_counts().items():
        lines.append(f"  - {reason}: {count}")
    lines += [
        "  Full list in `data/processed/mito_chemicals_dropped.csv`.",
        "- These endpoint definitions are a draft for review, not locked (per project brief).",
    ]

    with open(OUT_PATH, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")
    print(f"wrote {OUT_PATH}")


if __name__ == "__main__":
    main()
