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
oxidative-stress response proxy, not a direct mitochondrial ROS measurement.

Step 2 (modeling) complete: LR/RF/XGBoost baselines on the locked scaffold split.
Best model (Random Forest) scores AUROC 0.796 on the locked scaffold-held-out test
set (vs 0.892 under a random split - the expected inflation a scaffold split is meant
to catch). Performance persists when cytotoxicity-confounded actives are excluded
(0.796 -> 0.797), and uncertainty-based referral of the most uncertain 20% of
predictions raises retained-set AUROC to 0.909. Seahorse orthogonal concordance is
weak on the genuinely held-out subset (AUROC 0.47-0.56, n=100) - a real, disclosed
limitation, not papered over. Full results: `docs/step2_results.md`. External validation
attempted against a literature-curated Tox21-independent dataset (147 compounds); 82%
overlapped with our own training data, leaving only 26 unseen chemicals (25 active / 1
inactive) - too small to draw a confident conclusion from (`docs/external_validation_search.md`).

## Plan (from project brief, 2026-08-12; Step 2 refined per Kolliputi's 2026-08-12 reply)

### Step 1 — Dataset (done)
- Source: EPA ToxCast/invitrodb, EPA CompTox APIs
- Identify chemicals with usable structures + mitochondrial-relevant assay data
- Clean/standardize structures, dedupe, drop unusable mixtures/ambiguous structures
- Generate Morgan/ECFP fingerprints + standard physicochemical descriptors
- Endpoint definitions circulated and locked (see `docs/endpoint_definitions.md`)

### Step 2 — Modeling (primary endpoint: TOX21_MMP_ratio, aeid 1854) (done)
- Baselines: logistic regression, Random Forest, XGBoost (all three trained; see `docs/step2_results.md`)
- Primary evaluation: Bemis–Murcko scaffold-separated train/val/locked-test partitions (random split reported only as comparison) - verified zero scaffold overlap across partitions
- Locked test set: confirmed never used for feature selection, threshold tuning, endpoint definition, or model optimization
- Positive-hit rule and cytotoxicity filtering/stratification rule documented in `docs/endpoint_definitions.md` before running final models
- Metrics: AUROC, AUPRC, sensitivity, specificity, balanced accuracy, F1, MCC, confusion matrix, calibration/Brier score - all reported per model/regime
- Cytotoxicity-aware sensitivity analysis: performance persists (0.796 -> 0.797 AUROC) when cytotoxicity-confounded actives are excluded
- Uncertainty/domain-of-applicability: forest-disagreement uncertainty is significantly enriched among errors (p<1e-32); risk-coverage referral of the most uncertain 20% raises AUROC 0.796 -> 0.909
- Seahorse respiration endpoints analyzed separately - concordance is weak on the genuinely held-out subset (AUROC 0.47-0.56, n=100), a disclosed limitation
- External validation: candidate dataset identified but inaccessible this round (`docs/external_validation_search.md`) - no claim forced

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
