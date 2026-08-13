# Data summary (Step 1, draft)

Source: invitrodb v4.3 (EPA ToxCast/Tox21, Aug 2025) + DSSTox structure dump (Dec 2025).
Endpoint definitions: see `docs/endpoint_definitions.md`.

## Pipeline yield
- Chemicals tested across the 19 mitochondrial-relevant endpoints: 9,398
- Structures found in DSSTox: 9,398 / 9,398 (100%)
- Passed structure standardization (parseable, organic, non-mixture): 8,716
- Unique after canonical-structure dedup: 8,067
- Chemicals with at least one mitochondrial-endpoint label in the final table: 8,067

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
| mmp_ratio_tox21 (aeid 1854) | 7277 | 1160 | 15.9% |
| oxstress_nrf2_are_cis (aeid 97) | 3464 | 1207 | 34.8% |
| oxstress_are_bla_ratio (aeid 1110) | 6626 | 1261 | 19.0% |
| oxstress_are_bla_viability (aeid 1185) | 6626 | 589 | 8.9% |
| oxstress_are_ks_luc (aeid 3324) | 6935 | 1026 | 14.8% |
| oxstress_are_ks_luc_viability (aeid 3325) | 6935 | 961 | 13.9% |
| mitomass_1hr (aeid 10) | 295 | 8 | 2.7% |
| mitomass_24hr (aeid 30) | 990 | 127 | 12.8% |
| mitomass_72hr (aeid 50) | 976 | 132 | 13.5% |
| mitoticarrest_1hr (aeid 14) | 295 | 4 | 1.4% |
| mitoticarrest_24hr (aeid 34) | 990 | 176 | 17.8% |
| mitoticarrest_72hr (aeid 54) | 976 | 250 | 25.6% |

## Notes
- Primary endpoint (bioenergetic dysfunction / Seahorse respirometry) has a much
  smaller tested chemical set (~270-280 chemicals) than the Tox21 qHTS reporter
  assays (~9,000+) used for the secondary endpoints - this caps the primary model's
  training set size regardless of scaffold-split strategy.
- 682 chemicals dropped at structure-cleaning (568 no SMILES, 72 inorganic/no carbon,
  26 mixtures with no dominant fragment, 11 unparseable, 5 too small). Full list in
  `data/processed/mito_chemicals_dropped.csv`.
- These endpoint definitions are a draft for review, not locked (per project brief).
