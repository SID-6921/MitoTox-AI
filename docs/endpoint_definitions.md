# Endpoint definitions (LOCKED 2026-08-12, per Kolliputi review)

Source: invitrodb v4.3 (EPA ToxCast/Tox21, released Aug 2025), `assay_component_endpoint`
annotation table. Filtered from all 1,647 assay endpoints to those with a direct
mitochondrial mechanism, using the real annotation table (not guessed names) —
see `scripts/01_extract_mito_endpoints.py`.

Status: **locked.** Kolliputi reviewed the draft (see `docs/data_summary.md`) and made
one adjustment to the hierarchy below, replied 2026-08-12: the Seahorse bioenergetics
set (~253 chemicals) is too small to carry the primary ML feasibility analysis after a
scaffold-separated split, so the Tox21 membrane-potential ratio assay (n=7,268) is now
the primary ML endpoint instead. Do not use the locked test set for feature selection,
threshold tuning, endpoint definition, or model optimization from this point forward.

## Primary ML endpoint: mitochondrial membrane-potential disruption

| aeid | assay_component_endpoint_name | signal | n tested | notes |
|------|-------------------------------|--------|----------|-------|
| 1854 | TOX21_MMP_ratio | bidirectional | 7,268 | Tox21 qHTS, JC-10 dye ratio (finalized ratio of aeid 796/798 raw channels). **This is the primary ML modeling target for Step 2.** |

Positive-hit rule (must be documented before running final models, per Kolliputi):
hitcall >= 0.9 (standard EPA/tcpl convention), computed on invitrodb's mc5-6 winning
model fit — see `scripts/04_build_modeling_table.py`.

## Orthogonal mechanistic validation (not the primary ML target)

Seahorse-based cellular respirometry (CCTE_Simmons_MITO battery) — mechanistically the
most direct functional readout of mitochondrial bioenergetics in invitrodb, but too few
tested chemicals (~253) to carry the primary scaffold-separated ML analysis. Per
Kolliputi: analyze separately and determine concordance with the primary MMP
predictions, rather than forcing it to carry the main feasibility claim.

| aeid | assay_component_endpoint_name | signal | n tested | notes |
|------|-------------------------------|--------|----------|-------|
| 2442 | CCTE_Simmons_MITO_basal_resp_rate | bidirectional | 253 | basal oxygen consumption rate |
| 2444 | CCTE_Simmons_MITO_max_resp_rate | bidirectional | 253 | maximal respiration (uncoupled) |
| 2446 | CCTE_Simmons_MITO_inhib_resp_rate | bidirectional | 253 | respiration under ETC inhibition |
| 2450 | CCTE_Simmons_MITO_viability | loss | 229 | companion viability counter-screen, same battery |

## Secondary support: membrane-potential (imaging platform, smaller n)

Same mechanism as the primary endpoint, different (lower-throughput) platform. Useful
as secondary support / covariates, not a replacement for the primary ML target.

| aeid | assay_component_endpoint_name | signal | n tested | notes |
|------|-------------------------------|--------|----------|-------|
| 12 | APR_HepG2_MitoMembPot_1hr | bidirectional | 295 | Apredica HepG2 high-content imaging |
| 32 | APR_HepG2_MitoMembPot_24hr | bidirectional | 990 | |
| 52 | APR_HepG2_MitoMembPot_72hr | bidirectional | 976 | |

## Oxidative-stress response proxy — NOT a direct mitochondrial ROS measurement

Per Kolliputi: label this module as an oxidative-stress response proxy. These are
Nrf2/ARE reporter assays; none of them directly measure mitochondrial ROS, so no
mitochondria-specific claim should be made from this module alone (no dedicated
ROS-probe assay, e.g. DCFDA, exists in invitrodb).

| aeid | assay_component_endpoint_name | signal | n tested | notes |
|------|-------------------------------|--------|----------|-------|
| 97 | ATG_NRF2_ARE_CIS | bidirectional | 3,462 | Attagene factorial reporter |
| 1110 | TOX21_ARE_BLA_Agonist_ratio | gain | 6,617 | Tox21 β-lactamase ARE reporter |
| 1185 | TOX21_ARE_BLA_agonist_viability | loss | 6,617 | companion viability (burst_assay=1) |
| 3324 | TOX21_ARE_KS_LUC_Agonist | gain | 6,926 | Tox21 luciferase ARE reporter |
| 3325 | TOX21_ARE_KS_LUC_Agonist_viability | loss | 6,926 | companion viability |

## Supporting (same imaging battery, not a primary/secondary endpoint)

Co-measured on the same Apredica HepG2 plates as membrane potential; kept as
covariates/context for the multi-parametric HCS profile, not as modeling targets.

| aeid | assay_component_endpoint_name |
|------|-------------------------------|
| 10, 30, 50 | APR_HepG2_MitoMass_1hr/24hr/72hr |
| 14, 34, 54 | APR_HepG2_MitoticArrest_1hr/24hr/72hr |

## Cytotoxicity reference (for the cytotoxicity-aware sensitivity analysis)

`cytotox_invitrodb_v4_3_AUG2024.xlsx` — per-chemical cytotoxicity burst AC50/lower-bound
(median AC50 across all `burst_assay=1` endpoints, minus 3x global MAD). 65.7% of active
hits across the 19 mitochondrial-relevant endpoints occur at/above this threshold (see
`docs/data_summary.md`), so Step 2 must report both the overall analysis and performance
restricted to hits below the cytotoxicity threshold specifically.

**Exact filtering/stratification rule (fixed here, before any Step 2 model is trained):**
a test-set chemical is EXCLUDED from the "below cytotoxicity threshold" subset if and only
if it is a labeled active (hitcall >= 0.9) AND its `mmp_ratio_tox21_cytotox_confound` flag
is true (i.e. its AC50 on the primary endpoint is at/above its own cytotoxicity burst
lower-bound, computed in `scripts/05_enrich_potency_qc_cytotox.py`). All negatives are
kept unconditionally in both the overall and below-threshold subsets - the confound flag
is only meaningful for actives. This is a data-filtering rule for a specific comparison,
not a threshold/hyperparameter tuned on any result, and the underlying confound flag was
computed in Step 1 before any Step 2 model existed.

## What's intentionally excluded

- Assays with only indirect/downstream relevance (e.g. `LTEA_HepaRG_CAT` catalase,
  `LTEA_HepaRG_GADD45A` DNA-damage, `CCTE_Shafer_MEA_*` neuroactivity) — plausible
  crosstalk with oxidative stress, but not a specific enough mitochondrial signal to
  include as a labeled endpoint. Can revisit as covariates later.
- No dedicated ROS-probe (e.g. DCFDA) assay exists in invitrodb; oxidative stress is
  proxied via Nrf2/ARE reporters only, and is explicitly not treated as a direct
  mitochondrial ROS measurement (see oxidative-stress module above).
