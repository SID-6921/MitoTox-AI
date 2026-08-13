# MitoTox AI

Explainable, uncertainty-aware AI platform for predicting mitochondrial toxicity from environmental and industrial chemicals. Preliminary data/analysis package for the NIH STTR Phase I application (Nexara).

## Key question

Can chemical structure predict experimentally measured mitochondrial liability in previously unseen chemical scaffolds, while also identifying predictions that are uncertain and should be experimentally tested?

## Status

Step 1 (dataset) complete: 8,058 clean, deduped, structure-standardized chemicals
across 19 mitochondrial-relevant ToxCast/Tox21 endpoints, with ECFP4 fingerprints
and physicochemical descriptors. See `docs/data_summary.md` for yield/class-balance.

Endpoints **locked 2026-08-12** per Kolliputi's review - see `docs/endpoint_definitions.md`.
Primary ML endpoint is the Tox21 membrane-potential ratio assay (n=7,268), not the
Seahorse bioenergetics battery (n=253, too small for a scaffold-separated split) -
Seahorse is now an orthogonal mechanistic validation set. Nrf2/ARE is labeled an
oxidative-stress response proxy, not a direct mitochondrial ROS measurement. Step 2
(modeling) not started.

## Plan (from project brief, 2026-08-12; Step 2 refined per Kolliputi's 2026-08-12 reply)

### Step 1 — Dataset (done)
- Source: EPA ToxCast/invitrodb, EPA CompTox APIs
- Identify chemicals with usable structures + mitochondrial-relevant assay data
- Clean/standardize structures, dedupe, drop unusable mixtures/ambiguous structures
- Generate Morgan/ECFP fingerprints + standard physicochemical descriptors
- Endpoint definitions circulated and locked (see `docs/endpoint_definitions.md`)

### Step 2 — Modeling (primary endpoint: TOX21_MMP_ratio, aeid 1854)
- Baselines: logistic regression, Random Forest, XGBoost/LightGBM
- Primary evaluation: Bemis–Murcko scaffold-separated train/val/locked-test partitions (random split reported only as comparison)
- Locked test set: no feature selection, threshold tuning, endpoint definition, or model optimization against it
- Document the exact positive-hit rule and cytotoxicity filtering/stratification rule *before* running final models (not after seeing performance)
- Metrics: AUROC, AUPRC, sensitivity, specificity, balanced accuracy, F1, MCC, confusion matrix, calibration/Brier score
- Cytotoxicity-aware sensitivity analysis: overall + restricted to hits below the cytotoxicity burst threshold specifically (65.7% of active hits are at/above it - see `docs/data_summary.md`) - does predictive performance persist below threshold?
- Uncertainty/domain-of-applicability: risk-coverage / selective-prediction analysis - are high-uncertainty/OOD chemicals enriched among prediction errors?
- Seahorse respiration endpoints analyzed separately as mechanistic/orthogonal support - concordance check against primary MMP predictions
- After the primary analysis: look for a genuinely independent mitochondrial-toxicity dataset for external validation, applied without retraining

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
