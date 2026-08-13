"""Write docs/step2_verification.md - Kolliputi's three "before freezing"
requests: (1) exact error-rate methodology, (2) the random-split MCC
correction, (3) the Seahorse power analysis. Computed fresh from disk, same
pattern as the other doc-writer scripts.
"""
import importlib.util
import subprocess
import pandas as pd
from sklearn.metrics import matthews_corrcoef, f1_score, brier_score_loss

_spec = importlib.util.spec_from_file_location("power_analysis", "scripts/17_seahorse_power_analysis.py")
power_analysis = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(power_analysis)

PREDICTIONS_PATH = "data/processed/step2_predictions.csv"
UNCERTAINTY_PATH = "data/processed/step2_uncertainty_ad.csv"
RISK_COVERAGE_PATH = "data/processed/step2_risk_coverage.csv"
OUT_PATH = "docs/step2_verification.md"

THRESHOLD = 0.5


def main():
    uncertainty = pd.read_csv(UNCERTAINTY_PATH)
    risk_cov = pd.read_csv(RISK_COVERAGE_PATH)

    n_total = len(uncertainty)
    n_errors_100 = int(uncertainty["is_error"].sum())
    row20 = risk_cov[risk_cov.coverage_pct == 20].iloc[0]
    n_20 = int(row20["n"])
    err_20 = row20["error_rate"]
    n_errors_20 = round(err_20 * n_20)

    preds = pd.read_csv(PREDICTIONS_PATH, low_memory=False)
    random_rf = preds[(preds.regime == "random") & (preds.model == "random_forest") & (preds.split == "test")]
    y_true, y_prob = random_rf["label"].values, random_rf["predicted_proba"].values
    y_pred = (y_prob >= THRESHOLD).astype(int)
    mcc_correct = matthews_corrcoef(y_true, y_pred)
    f1_correct = f1_score(y_true, y_pred)
    brier_correct = brier_score_loss(y_true, y_prob)
    tp = int(((y_pred == 1) & (y_true == 1)).sum())
    fn = int(((y_pred == 0) & (y_true == 1)).sum())
    tn = int(((y_pred == 0) & (y_true == 0)).sum())
    fp = int(((y_pred == 1) & (y_true == 0)).sum())
    sensitivity_correct = tp / (tp + fn)
    specificity_correct = tn / (tn + fp)

    power_output = subprocess.run(
        ["python3", "scripts/17_seahorse_power_analysis.py"], capture_output=True, text=True
    ).stdout

    # exact numbers for the summary paragraph below, computed the same way as
    # the printed table above (not hand-typed ranges that could go stale)
    balanced_n60, _, _ = power_analysis.required_n(0.60, 64, 36)
    balanced_n65, _, _ = power_analysis.required_n(0.65, 64, 36)
    imbalanced_n60, _, _ = power_analysis.required_n(0.60, 14, 86)
    imbalanced_n65, _, _ = power_analysis.required_n(0.65, 14, 86)

    lines = [
        "# Step 2 verification (response to Kolliputi's pre-freeze requests, 2026-08-13)",
        "",
        "## 1. Error-rate reduction (20.4% -> 1.4%) - exact calculation",
        "",
        "Both numbers come from the risk-coverage analysis in `scripts/12_uncertainty_and_ad.py`,",
        "applied to the scaffold-split Random Forest model's locked test-set predictions:",
        "",
        "- **Classification threshold:** predicted probability >= 0.5 (the same fixed default",
        "  used for every threshold-dependent metric throughout Step 2, chosen before any",
        "  evaluation was run).",
        "- **Uncertainty ranking:** test chemicals sorted by ascending forest-disagreement",
        "  uncertainty (std of predicted probability across the Random Forest's 500 trees) -",
        "  most confident first.",
        f"- **100% coverage (no referral):** denominator = all {n_total} test chemicals; "
        f"numerator = {n_errors_100} misclassified at the 0.5 threshold; error rate = "
        f"{n_errors_100}/{n_total} = {n_errors_100/n_total:.3f} (20.4%).",
        f"- **20% coverage (referring the most uncertain 80% out):** denominator = only the "
        f"{n_20} *most confident* test chemicals (the 20% with lowest uncertainty), not the",
        f"  full {n_total} - numerator = {n_errors_20} misclassified within that retained subset;",
        f"  error rate = {n_errors_20}/{n_20} = {err_20:.3f} (1.4%).",
        "",
        "**The denominator shrinks as coverage shrinks** - this is standard selective-prediction",
        "methodology (error rate *on the retained/covered subset*, not on the full test set with",
        "referred chemicals scored as correct or excluded some other way). The reduction is real,",
        "not an artifact of a shifting reference population inflating the improvement - the",
        f"numerator (raw error count) also drops in absolute terms, from {n_errors_100} to "
        f"{n_errors_20} misclassified chemicals, even though the denominator dropped too.",
        "",
        "**Addendum, per Kolliputi's follow-up:** this 20%-coverage row is the conservative end of",
        "the spectrum - retain only the most-confident 20%, refer the other 80%. It is a different",
        "operating point from retaining 80% and referring the most-uncertain 20%, which was",
        "conflated with this one in earlier prose (docs/step2_results.md, README, the preliminary",
        "paragraph, and two emails all described 'referring the most uncertain 20%' while showing",
        "these 20%-coverage numbers - backwards). The full corrected 9-row table, including the",
        "80%-coverage operating point Kolliputi specifically asked about, is in",
        "`docs/step2_results.md` under Risk-coverage.",
        "",
        "## 2. Random-split MCC correction",
        "",
        "**The 0.098 figure in the earlier email was a transcription error, not a pipeline bug.**",
        "While condensing the full results table for that email, the random-split Random Forest",
        "row's F1/MCC/Brier values were shifted one column to the right. Corrected values, verified",
        "three ways (repo's `data/processed/step2_test_metrics.csv`, `docs/step2_results.md`, and a",
        "fresh independent recomputation from `data/processed/step2_predictions.csv` directly, all",
        "agreeing to floating-point precision):",
        "",
        "| metric | value sent in email | correct value |",
        "|---|---|---|",
        f"| F1 | 0.535 | {f1_correct:.3f} |",
        f"| MCC | 0.098 | {mcc_correct:.3f} |",
        f"| Brier | (not shown) | {brier_correct:.3f} |",
        "",
        f"MCC of {mcc_correct:.3f} is consistent with the previously-reported sensitivity "
        f"({sensitivity_correct:.3f}), specificity ({specificity_correct:.3f}), and F1 - which is",
        "what looked wrong about 0.098 in the first place.",
        "`docs/step2_results.md` had the correct numbers throughout; only the email table was wrong.",
        "",
        "## 3. Seahorse discordance power analysis",
        "",
        "Method: Hanley-McNeil (1982) nonparametric AUC variance estimator, combined with a",
        "two-sided z-test of H0: AUC=0.5 vs a target 'modest' AUC, solved numerically for the",
        "smallest n (holding each endpoint's observed active:inactive ratio from the n=100",
        "held-out set fixed) that reaches 80% power at alpha=0.05. See",
        "`scripts/17_seahorse_power_analysis.py` for the full implementation.",
        "",
        "```",
        power_output.strip(),
        "```",
        "",
        "**For Aim 2 budget/scope purposes:** detecting a modest true effect (AUC 0.60-0.65) in the",
        f"membrane-potential-vs-respiration relationship would need "
        f"{min(balanced_n60, balanced_n65)}-{max(balanced_n60, balanced_n65)} chemicals",
        "with Seahorse data (vs. the 100 available here) for the two better-balanced endpoints",
        "(basal/max respiration rate, 64 active/36 inactive observed); the more imbalanced",
        f"inhibited-respiration endpoint (14 active/86 inactive) would need "
        f"{min(imbalanced_n60, imbalanced_n65)}-{max(imbalanced_n60, imbalanced_n65)}",
        "depending on target effect size, since class imbalance inflates the variance of the AUC",
        "estimator. This is provided to size the compound panel, not as a claim about what the",
        "true effect actually is.",
    ]

    with open(OUT_PATH, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")
    print(f"wrote {OUT_PATH}")


if __name__ == "__main__":
    main()
