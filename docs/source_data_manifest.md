# Source data manifest

Raw downloads are not committed to this repo (see `.gitignore`) — this manifest is
what makes them reproducible. Run `scripts/00_download_raw.sh` (or the curl commands
below) to refetch.

## invitrodb v4.3 (EPA ToxCast/Tox21, released August 2025)

Hosted on EPA-ORD-CCTE Clowder (the `epa.gov/comptox-tools/exploring-toxcast-data`
page and the GitHub `USEPA/comptox-toxcast-invitrodb` repo are pointers only, not
data sources). DOI: `10.23645/epacomptox.6062623`.

Clowder space: https://clowder.edap-cluster.com/spaces/687e388ce4b02565bc3e28e4

Files used (downloaded to `data/raw/invitrodb_v4_3/`):

| file | clowder file id | size |
|---|---|---|
| `assay_annotations_invitrodb_v4_3_AUG2024.xlsx` | `68af6bd3e4b02565fc7c3aa8` | 1.1 MB |
| `cytotox_invitrodb_v4_3_AUG2024.xlsx` | `68af6bd3e4b02565fc7c3aa4` | 943 KB |
| `assay_target_mappings_invitrodb_v4_3_AUG2024.xlsx` | `68af6bd3e4b02565fc7c3aa0` | 98 KB |
| `DB_release_README_SUMMARY.pdf` | `697b7530e4b0731a6170449e` | 172 KB |
| `INVITRODB_SUMMARY.zip` (contains mc4/mc5-6/sc1-2/etc.) | `68af6b70e4b02565fc7c3a98` | 7.5 GB |

Download pattern: `curl -o <name> "https://clowder.edap-cluster.com/api/files/<id>"`.
A full download at ~20MB/s (~6 min for the 7.5GB zip) was faster and more reliable
than trying to range-read just the needed member out of the remote zip's central
directory, which hung on tail seeks against this particular file server.

From inside `INVITRODB_SUMMARY.zip`, two members are used:
`mc5-6_winning_model_fits-flags_invitrodbv4_3_AUG2024.csv` (2.55 GB uncompressed) — the
hit-call / AC50 / efficacy / QC-flag summary table ("winning model" per assay endpoint
per chemical sample) — and `methods_invitrodb_v4_3_AUG2024.xlsx`'s `method_list` sheet
(read directly from the zip in `scripts/05_enrich_potency_qc_cytotox.py`), which maps
mc6 QC-flag ids to human-readable descriptions.

## DSSTox chemical structures (Dec 2025 dump, version 8 of the DSSTox Figshare dataset)

DOI: `10.23645/epacomptox.5588566` -> redirects to Clowder dataset
`61147fefe4b0856fdc65639b`, folder `69529756e4b0731a616efc47`.

File used: `DSSTox_CCD_dump_12092025_CSVs.zip` (clowder file id
`69529775e4b0731a616efc4b`, 290 MB) containing `DSSToxCCDdump.csv` (664 MB, ~1.2M
chemicals: DTXSID, CASRN, INCHIKEY, SMILES, QSAR_READY_SMILES, MS_READY_SMILES). The
13 `DSSToxCCDdumpN.csv` split files in the same zip are the same data pre-split into
chunks — not needed, the master file has everything.

## External validation dataset (Step 2, Garcia de Lomana et al. 2023)

DOI: `10.1021/acs.chemrestox.3c00086` (PMC10354797, open access). Supplementary file
`tx3c00086_si_002.xlsx` (`mitotox_dataset` sheet), 50.8 MB, downloaded to
`data/raw/external_validation/`.

Download note: `https://pmc.ncbi.nlm.nih.gov/articles/instance/10354797/bin/tx3c00086_si_002.xlsx`
is gated by NCBI PMC's "cloudpmc-viewer" bot-detection (a client-side proof-of-work JS
challenge) - plain `curl` and direct browser navigation both get served a "Preparing to
download..." interstitial indefinitely. It resolves via a normal browser session:
load the article page (`https://pmc.ncbi.nlm.nih.gov/articles/PMC10354797/`), let the
page's own JS solve the PoW challenge (sets a `cloudpmc-viewer-pow` cookie), then
`fetch()`/click the actual link from within that authenticated session. See
`docs/external_validation_search.md` for how this dataset was filtered down to a
genuinely Tox21-independent subset and used in `scripts/15_external_validation.py`.

## Not used / not available

- `api-ccte.epa.gov` CompTox APIs: require an API key requested by email
  (`ccte_api@epa.gov`), not self-service. Not needed since the bulk Clowder/Figshare
  files above cover everything required.
- A dedicated Seahorse/OXPHOS bulk dataset beyond `CCTE_Simmons_MITO_*` (which is
  already inside invitrodb): not located as a separate public bulk file.
