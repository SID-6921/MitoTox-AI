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

## Selective-prediction (risk-coverage) table

"Coverage" = % of test chemicals *retained* (the most confident ones); the rest are
*referred* for experimental confirmation (the most uncertain ones). 80% coverage - refer
the most uncertain 20% - is the operating point flagged as the more commercially realistic
one.

| Coverage | Retained | Referred | % referred | AUROC | AUPRC | Sensitivity | Specificity | Balanced acc | Error rate |
|---|---|---|---|---|---|---|---|---|---|
| 100% | 1091 | 0 | 0.0% | 0.796 | 0.451 | 0.352 | 0.914 | 0.633 | 0.204 |
| 90% | 982 | 109 | 10.0% | 0.796 | 0.424 | 0.302 | 0.934 | 0.618 | 0.181 |
| 80% | 873 | 218 | 20.0% | 0.796 | 0.397 | 0.241 | 0.951 | 0.596 | 0.157 |
| 70% | 764 | 327 | 30.0% | 0.776 | 0.343 | 0.261 | 0.964 | 0.613 | 0.116 |
| 60% | 655 | 436 | 40.0% | 0.743 | 0.268 | 0.214 | 0.975 | 0.595 | 0.090 |
| 50% | 546 | 545 | 50.0% | 0.764 | 0.274 | 0.195 | 0.984 | 0.590 | 0.075 |
| 40% | 436 | 655 | 60.0% | 0.785 | 0.280 | 0.269 | 0.993 | 0.631 | 0.050 |
| 30% | 327 | 764 | 70.0% | 0.848 | 0.327 | 0.267 | 0.990 | 0.629 | 0.043 |
| 20% | 218 | 873 | 80.0% | 0.909 | 0.482 | 0.667 | 0.995 | 0.831 | 0.014 |
