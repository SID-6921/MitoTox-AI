# Data summary (Step 1, draft)

Source: invitrodb v4.3 (EPA ToxCast/Tox21, Aug 2025) + DSSTox structure dump (Dec 2025).
Endpoint definitions: see `docs/endpoint_definitions.md`.

## Pipeline yield
- Chemicals tested across the 19 mitochondrial-relevant endpoints: 9,398
- Structures found in DSSTox: 9,398 / 9,398 (100%)
- Passed structure standardization (parseable, organic, non-mixture): 8,705
- Unique after canonical-structure dedup: 8,058
- Chemicals with at least one mitochondrial-endpoint label in the final table: 8,058

(Hit-call threshold for 'active': hitcall >= 0.9, the standard EPA/tcpl convention.)

## Class balance by endpoint

| endpoint | n tested | n active | % active |
|---|---|---|---|
| primary_basal_resp_rate (aeid 2442) | 253 | 165 | 65.2% |
| primary_max_resp_rate (aeid 2444) | 253 | 134 | 53.0% |
| primary_inhib_resp_rate (aeid 2446) | 253 | 28 | 11.1% |
| primary_mito_viability (aeid 2450) | 229 | 52 | 22.7% |
| mmp_1hr (aeid 12) | 295 | 22 | 7.5% |
| mmp_24hr (aeid 32) | 990 | 155 | 15.7% |
| mmp_72hr (aeid 52) | 976 | 107 | 11.0% |
| mmp_ratio_tox21 (aeid 1854) | 7268 | 1158 | 15.9% |
| oxstress_nrf2_are_cis (aeid 97) | 3462 | 1207 | 34.9% |
| oxstress_are_bla_ratio (aeid 1110) | 6617 | 1259 | 19.0% |
| oxstress_are_bla_viability (aeid 1185) | 6617 | 586 | 8.9% |
| oxstress_are_ks_luc (aeid 3324) | 6926 | 1024 | 14.8% |
| oxstress_are_ks_luc_viability (aeid 3325) | 6926 | 957 | 13.8% |
| mitomass_1hr (aeid 10) | 295 | 8 | 2.7% |
| mitomass_24hr (aeid 30) | 990 | 127 | 12.8% |
| mitomass_72hr (aeid 50) | 976 | 132 | 13.5% |
| mitoticarrest_1hr (aeid 14) | 295 | 4 | 1.4% |
| mitoticarrest_24hr (aeid 34) | 990 | 176 | 17.8% |
| mitoticarrest_72hr (aeid 54) | 976 | 250 | 25.6% |

## Potency, QC, and cytotoxicity

- Per-endpoint AC50 (potency, µM) and efficacy (`top`) are in the wide modeling
  table as `<endpoint>_ac50_um` / `<endpoint>_efficacy_top`. Decoded QC flags
  (`mc6_flags_decoded`, from invitrodb's `method_list` mc6 lookup) are in the
  long-format `data/processed/mito_hitcalls_enriched.csv`.
- **Cytotoxicity sensitivity check:** joined each chemical's cytotoxicity burst
  threshold (`cytotox_invitrodb_v4_3_AUG2024.xlsx`, median AC50 across all
  `burst_assay=1` endpoints minus 3x global MAD). Of the 7,551 active hits across all 19 endpoints, **65.7% occur at or above the chemical's own cytotoxicity burst threshold** - meaning a majority of
  raw hits in this endpoint set are plausibly driven by general cytotoxicity rather
  than a mitochondria-specific mechanism. Flagged per-hit (`likely_cytotox_confound`)
  and per-chemical/endpoint (`<endpoint>_cytotox_confound`) so Step 2 modeling can
  filter or stratify on it.

## Notes
- Primary endpoint (bioenergetic dysfunction / Seahorse respirometry) has a much
  smaller tested chemical set (~250-270 chemicals) than the Tox21 qHTS reporter
  assays (~6,600-7,300) used for the secondary endpoints - this caps the primary
  model's training set size regardless of scaffold-split strategy.
- 693 chemicals dropped at structure-cleaning. Reasons:
  - empty_smiles: 566
  - inorganic_no_carbon: 72
  - mixture_no_dominant_fragment: 26
  - unparseable_smiles: 11
  - ambiguous_wildcard_atom: 9
  - too_small: 5
  - likely_uvcb_name_pattern: 4
  Full list in `data/processed/mito_chemicals_dropped.csv`.
- These endpoint definitions are a draft for review, not locked (per project brief).
