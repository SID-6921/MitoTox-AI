# MitoTox AI

Explainable, uncertainty-aware AI platform for predicting mitochondrial toxicity from environmental and industrial chemicals. Preliminary data/analysis package for the NIH STTR Phase I application (Nexara).

## Key question

Can chemical structure predict experimentally measured mitochondrial liability in previously unseen chemical scaffolds, while also identifying predictions that are uncertain and should be experimentally tested?

## Status

Step 1 (dataset) draft complete: 8,060 clean, deduped, structure-standardized
chemicals across 19 mitochondrial-relevant ToxCast/Tox21 endpoints, with ECFP4
fingerprints and physicochemical descriptors. See `docs/data_summary.md` for
yield/class-balance and `docs/endpoint_definitions.md` for the proposed endpoint
set (draft, pending Kolliputi/Lakshmi review before locking). Modeling (Step 2)
not started.

## Plan (from project brief, 2026-08-12)

### Step 1 — Dataset
- Source: EPA ToxCast/invitrodb, EPA CompTox APIs
- Identify chemicals with usable structures + mitochondrial-relevant assay data (bioenergetic dysfunction primary; membrane-potential disruption and oxidative stress secondary modules)
- Clean/standardize structures, dedupe, drop unusable mixtures/ambiguous structures
- Generate Morgan/ECFP fingerprints + standard physicochemical descriptors
- Endpoint definitions to be circulated for review before locking

### Step 2 — Modeling
- Baselines first: logistic regression, Random Forest, XGBoost/LightGBM (deep learning only if justified)
- Primary evaluation: Bemis–Murcko scaffold-aware train/val/test split (random split shown only as comparison)
- Locked scaffold-held-out test metrics: AUROC, AUPRC, sensitivity, specificity, balanced accuracy, F1, MCC, confusion matrix, calibration/Brier score
- Cytotoxicity sensitivity analysis (is the model learning general cytotoxicity vs. mitochondrial-specific liability?)
- Uncertainty / domain-of-applicability component + risk-coverage analysis (referring uncertain 10%/20%/... to experimental testing)

### Step 3 — Preliminary-data package
- Workflow diagram, ROC/PR curves, calibration plot, risk-coverage plot, chemical-space/AD visualization
- Explainability examples (correct toxicant, correct low-liability, uncertain/OOD case)
- Model-comparison + endpoint-specific performance tables
- Independent external validation dataset applied without retraining, if one exists (no forced claim otherwise)

## Repro requirements

No optimizing endpoint definitions, exclusions, or test sets to hit a target AUROC. Fixed random seeds/splits. Honest reporting of where it works and where it doesn't.

## Structure

```
data/raw/          # untouched source pulls (ToxCast/invitrodb, external validation set)
data/processed/     # cleaned/standardized structures, fingerprints, descriptors
scripts/            # data pipeline, modeling, evaluation code
notebooks/          # exploratory analysis
models/             # trained model artifacts, fixed splits/seeds
results/figures/    # generated figures and tables
docs/               # endpoint definitions, source-data manifest, decisions log
```
