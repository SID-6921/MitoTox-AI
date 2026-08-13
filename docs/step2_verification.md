# Step 2 verification (response to Kolliputi's pre-freeze requests, 2026-08-13)

## 1. Error-rate reduction (20.4% -> 1.4%) - exact calculation

Both numbers come from the risk-coverage analysis in `scripts/12_uncertainty_and_ad.py`,
applied to the scaffold-split Random Forest model's locked test-set predictions:

- **Classification threshold:** predicted probability >= 0.5 (the same fixed default
  used for every threshold-dependent metric throughout Step 2, chosen before any
  evaluation was run).
- **Uncertainty ranking:** test chemicals sorted by ascending forest-disagreement
  uncertainty (std of predicted probability across the Random Forest's 500 trees) -
  most confident first.
- **100% coverage (no referral):** denominator = all 1091 test chemicals; numerator = 223 misclassified at the 0.5 threshold; error rate = 223/1091 = 0.204 (20.4%).
- **20% coverage (referring the most uncertain 80% out):** denominator = only the 218 *most confident* test chemicals (the 20% with lowest uncertainty), not the
  full 1091 - numerator = 3 misclassified within that retained subset;
  error rate = 3/218 = 0.014 (1.4%).

**The denominator shrinks as coverage shrinks** - this is standard selective-prediction
methodology (error rate *on the retained/covered subset*, not on the full test set with
referred chemicals scored as correct or excluded some other way). The reduction is real,
not an artifact of a shifting reference population inflating the improvement - the
numerator (raw error count) also drops in absolute terms, from 223 to 3 misclassified chemicals, even though the denominator dropped too.

## 2. Random-split MCC correction

**The 0.098 figure in the earlier email was a transcription error, not a pipeline bug.**
While condensing the full results table for that email, the random-split Random Forest
row's F1/MCC/Brier values were shifted one column to the right. Corrected values, verified
three ways (repo's `data/processed/step2_test_metrics.csv`, `docs/step2_results.md`, and a
fresh independent recomputation from `data/processed/step2_predictions.csv` directly, all
agreeing to floating-point precision):

| metric | value sent in email | correct value |
|---|---|---|
| F1 | 0.535 | 0.611 |
| MCC | 0.098 | 0.535 |
| Brier | (not shown) | 0.098 |

MCC of 0.535 is consistent with the previously-reported sensitivity (0.626), specificity (0.919), and F1 - which is
what looked wrong about 0.098 in the first place.
`docs/step2_results.md` had the correct numbers throughout; only the email table was wrong.

## 3. Seahorse discordance power analysis

Method: Hanley-McNeil (1982) nonparametric AUC variance estimator, combined with a
two-sided z-test of H0: AUC=0.5 vs a target 'modest' AUC, solved numerically for the
smallest n (holding each endpoint's observed active:inactive ratio from the n=100
held-out set fixed) that reaches 80% power at alpha=0.05. See
`scripts/17_seahorse_power_analysis.py` for the full implementation.

```
Power analysis: detecting AUC != 0.5 at alpha=0.05, power=0.8

primary_basal_resp_rate (observed n=100, 64 active / 36 inactive, active:inactive ratio 1.778):
  target AUC=0.55: needs total n=1127 (721 active / 406 inactive, same observed ratio)
  target AUC=0.6: needs total n=278 (178 active / 100 inactive, same observed ratio)
  target AUC=0.65: needs total n=121 (77 active / 44 inactive, same observed ratio)
  target AUC=0.7: needs total n=67 (43 active / 24 inactive, same observed ratio)

primary_max_resp_rate (observed n=100, 64 active / 36 inactive, active:inactive ratio 1.778):
  target AUC=0.55: needs total n=1127 (721 active / 406 inactive, same observed ratio)
  target AUC=0.6: needs total n=278 (178 active / 100 inactive, same observed ratio)
  target AUC=0.65: needs total n=121 (77 active / 44 inactive, same observed ratio)
  target AUC=0.7: needs total n=67 (43 active / 24 inactive, same observed ratio)

primary_inhib_resp_rate (observed n=100, 14 active / 86 inactive, active:inactive ratio 0.163):
  target AUC=0.55: needs total n=2197 (308 active / 1889 inactive, same observed ratio)
  target AUC=0.6: needs total n=554 (78 active / 476 inactive, same observed ratio)
  target AUC=0.65: needs total n=247 (35 active / 212 inactive, same observed ratio)
  target AUC=0.7: needs total n=136 (19 active / 117 inactive, same observed ratio)

Sanity check: current observed n=100 statistical power to detect each target AUC
primary_basal_resp_rate:
  at current n=100, power to detect AUC=0.55: 0.125
  at current n=100, power to detect AUC=0.6: 0.375
  at current n=100, power to detect AUC=0.65: 0.715
  at current n=100, power to detect AUC=0.7: 0.941
primary_max_resp_rate:
  at current n=100, power to detect AUC=0.55: 0.125
  at current n=100, power to detect AUC=0.6: 0.375
  at current n=100, power to detect AUC=0.65: 0.715
  at current n=100, power to detect AUC=0.7: 0.941
primary_inhib_resp_rate:
  at current n=100, power to detect AUC=0.55: 0.090
  at current n=100, power to detect AUC=0.6: 0.227
  at current n=100, power to detect AUC=0.65: 0.435
  at current n=100, power to detect AUC=0.7: 0.669
```

**For Aim 2 budget/scope purposes:** detecting a modest true effect (AUC 0.60-0.65) in the
membrane-potential-vs-respiration relationship would need 121-278 chemicals
with Seahorse data (vs. the 100 available here) for the two better-balanced endpoints
(basal/max respiration rate, 64 active/36 inactive observed); the more imbalanced
inhibited-respiration endpoint (14 active/86 inactive) would need 247-554
depending on target effect size, since class imbalance inflates the variance of the AUC
estimator. This is provided to size the compound panel, not as a claim about what the
true effect actually is.
