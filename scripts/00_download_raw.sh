#!/bin/sh
# Fetch raw source data. See docs/source_data_manifest.md for provenance/versions.
set -e

RAW="data/raw"
mkdir -p "$RAW/invitrodb_v4_3" "$RAW/dsstox"

curl -o "$RAW/invitrodb_v4_3/assay_annotations_invitrodb_v4_3_AUG2024.xlsx" \
  "https://clowder.edap-cluster.com/api/files/68af6bd3e4b02565fc7c3aa8"
curl -o "$RAW/invitrodb_v4_3/cytotox_invitrodb_v4_3_AUG2024.xlsx" \
  "https://clowder.edap-cluster.com/api/files/68af6bd3e4b02565fc7c3aa4"
curl -o "$RAW/invitrodb_v4_3/assay_target_mappings_invitrodb_v4_3_AUG2024.xlsx" \
  "https://clowder.edap-cluster.com/api/files/68af6bd3e4b02565fc7c3aa0"
curl -o "$RAW/invitrodb_v4_3/DB_release_README_SUMMARY.pdf" \
  "https://clowder.edap-cluster.com/api/files/697b7530e4b0731a6170449e"
# 7.5 GB - the big one, contains mc5-6 hit calls used by scripts/01_extract_mito_endpoints.py
curl -o "$RAW/invitrodb_v4_3/INVITRODB_SUMMARY.zip" \
  "https://clowder.edap-cluster.com/api/files/68af6b70e4b02565fc7c3a98"

# 290 MB, chemical structures (DTXSID -> SMILES)
curl -o "$RAW/dsstox/DSSTox_CCD_dump_12092025_CSVs.zip" \
  "https://clowder.edap-cluster.com/api/files/69529775e4b0731a616efc4b"
