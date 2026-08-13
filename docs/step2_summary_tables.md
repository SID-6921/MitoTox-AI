# Step 2 summary tables (condensed, for the preliminary-data package)

Full detail (confusion matrices, all metrics, calibration bins) in
`docs/step2_results.md`. These are the condensed versions for slides/writeup.

## Model comparison (locked scaffold-held-out test set - primary evaluation)

| Model | AUROC | AUPRC | MCC | Balanced accuracy | Brier |
|---|---|---|---|---|---|
| Random Forest | 0.796 | 0.451 | 0.311 | 0.633 | 0.148 |
| XGBoost | 0.763 | 0.458 | 0.336 | 0.670 | 0.162 |
| Logistic Regression | 0.673 | 0.342 | 0.197 | 0.598 | 0.213 |

(Random Forest selected as the primary model - highest scaffold-test AUROC. Random-split
numbers, shown only as a comparison per the pre-registered analysis plan, are in the full
table in `docs/step2_results.md`.)

## Endpoint-specific performance

Only the primary endpoint (TOX21_MMP_ratio) was modeled in Step 2, per the locked
endpoint hierarchy - Seahorse and Nrf2/ARE are analyzed as orthogonal support and an
oxidative-stress proxy respectively, not as separately-trained classifiers.

| Analysis condition | n | AUROC | MCC | Balanced accuracy |
|---|---|---|---|---|
| Primary endpoint - overall | 1091 | 0.796 | 0.311 | 0.633 |
| Primary endpoint - below cytotoxicity threshold | 940 | 0.797 | 0.290 | 0.666 |

| Orthogonal analysis | n | AUROC (vs primary model) |
|---|---|---|
| Seahorse primary_basal_resp_rate (held-out chemicals only) | 100 | 0.470 |
| Seahorse primary_max_resp_rate (held-out chemicals only) | 100 | 0.558 |
| Seahorse primary_inhib_resp_rate (held-out chemicals only) | 100 | 0.508 |
