# Endpoint definitions (proposed, pre-lock)

Source: invitrodb v4.3 (EPA ToxCast/Tox21, released Aug 2025), `assay_component_endpoint`
annotation table. Filtered from all 1,647 assay endpoints to those with a direct
mitochondrial mechanism, using the real annotation table (not guessed names) —
see `scripts/01_extract_mito_endpoints.py`.

Status: **draft, to be reviewed by Kolliputi and Lakshmi before modeling is locked** per
the project brief.

## Primary: mitochondrial bioenergetic dysfunction

Seahorse-based cellular respirometry (CCTE_Simmons_MITO battery) — the most direct
functional readout of mitochondrial bioenergetics available in invitrodb.

| aeid | assay_component_endpoint_name | signal | notes |
|------|-------------------------------|--------|-------|
| 2442 | CCTE_Simmons_MITO_basal_resp_rate | bidirectional | basal oxygen consumption rate |
| 2444 | CCTE_Simmons_MITO_max_resp_rate | bidirectional | maximal respiration (uncoupled) |
| 2446 | CCTE_Simmons_MITO_inhib_resp_rate | bidirectional | respiration under ETC inhibition |
| 2450 | CCTE_Simmons_MITO_viability | loss | companion viability counter-screen, same battery |

## Secondary A: mitochondrial membrane-potential disruption

| aeid | assay_component_endpoint_name | signal | notes |
|------|-------------------------------|--------|-------|
| 12 | APR_HepG2_MitoMembPot_1hr | bidirectional | Apredica HepG2 high-content imaging |
| 32 | APR_HepG2_MitoMembPot_24hr | bidirectional | |
| 52 | APR_HepG2_MitoMembPot_72hr | bidirectional | |
| 1854 | TOX21_MMP_ratio | bidirectional | Tox21 qHTS, JC-10 dye ratio (finalized ratio of aeid 796/798 raw channels) |

## Secondary B: mitochondrial oxidative stress

Nrf2/ARE reporter assays as a proxy for oxidative-stress response (no direct ROS-probe
assay exists in invitrodb).

| aeid | assay_component_endpoint_name | signal | notes |
|------|-------------------------------|--------|-------|
| 97 | ATG_NRF2_ARE_CIS | bidirectional | Attagene factorial reporter |
| 1110 | TOX21_ARE_BLA_Agonist_ratio | gain | Tox21 β-lactamase ARE reporter |
| 1185 | TOX21_ARE_BLA_agonist_viability | loss | companion viability (burst_assay=1) |
| 3324 | TOX21_ARE_KS_LUC_Agonist | gain | Tox21 luciferase ARE reporter |
| 3325 | TOX21_ARE_KS_LUC_Agonist_viability | loss | companion viability |

## Supporting (same imaging battery, not a primary/secondary endpoint)

Co-measured on the same Apredica HepG2 plates as membrane potential; kept as
covariates/context for the multi-parametric HCS profile, not as modeling targets.

| aeid | assay_component_endpoint_name |
|------|-------------------------------|
| 10, 30, 50 | APR_HepG2_MitoMass_1hr/24hr/72hr |
| 14, 34, 54 | APR_HepG2_MitoticArrest_1hr/24hr/72hr |

## Cytotoxicity reference (for the cytotoxicity sensitivity analysis)

`cytotox_invitrodb_v4_3_AUG2024.xlsx` — per-chemical cytotoxicity burst AC50/lower-bound
(median AC50 across all `burst_assay=1` endpoints, minus 3x global MAD). Used to check
whether primary/secondary hits are simply tracking general cytotoxicity rather than
mitochondrial-specific liability.

## What's intentionally excluded

- Assays with only indirect/downstream relevance (e.g. `LTEA_HepaRG_CAT` catalase,
  `LTEA_HepaRG_GADD45A` DNA-damage, `CCTE_Shafer_MEA_*` neuroactivity) — plausible
  crosstalk with oxidative stress, but not a specific enough mitochondrial signal to
  include as a labeled endpoint. Can revisit as covariates later.
- No dedicated ROS-probe (e.g. DCFDA) assay exists in invitrodb; oxidative stress is
  proxied via Nrf2/ARE reporters only. Flagging this as a known limitation for the
  STTR write-up.
