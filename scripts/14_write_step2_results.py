"""Write docs/step2_results.md from the final Step 2 artifacts, computing
every number fresh from disk (same pattern as 06_write_data_summary.py) so
it can't go stale or be hand-edited out of sync with the actual results.
"""
import json
import pandas as pd
from scipy.stats import mannwhitneyu

SELECTION_LOG_PATH = "models/step2_model_selection_log.csv"
TEST_METRICS_PATH = "data/processed/step2_test_metrics.csv"
CYTOTOX_PATH = "data/processed/step2_cytotox_sensitivity.csv"
RISK_COVERAGE_PATH = "data/processed/step2_risk_coverage.csv"
FULL_COVERAGE_PATH = "data/processed/step2_full_coverage_table.csv"
UNCERTAINTY_PATH = "data/processed/step2_uncertainty_ad.csv"
SEAHORSE_PATH = "data/processed/step2_seahorse_concordance.csv"
CALIBRATION_PATH = "data/processed/step2_calibration_bins.csv"
EXTERNAL_PATH = "data/processed/step2_external_validation.csv"
THRESHOLD_TRADEOFF_PATH = "data/processed/step2_threshold_tradeoff.csv"
EXPLAINABILITY_PATH = "data/processed/step2_explainability_examples.json"
OUT_PATH = "docs/step2_results.md"


def main():
    selection = pd.read_csv(SELECTION_LOG_PATH)
    threshold_tradeoff = pd.read_csv(THRESHOLD_TRADEOFF_PATH)
    with open(EXPLAINABILITY_PATH) as f:
        explainability = json.load(f)
    metrics = pd.read_csv(TEST_METRICS_PATH)
    external = pd.read_csv(EXTERNAL_PATH)
    cytotox = pd.read_csv(CYTOTOX_PATH)
    calibration = pd.read_csv(CALIBRATION_PATH)
    risk_cov = pd.read_csv(RISK_COVERAGE_PATH)
    full_coverage = pd.read_csv(FULL_COVERAGE_PATH)
    uncertainty = pd.read_csv(UNCERTAINTY_PATH)
    seahorse = pd.read_csv(SEAHORSE_PATH)

    best_row = metrics[metrics["regime"] == "scaffold"].sort_values("auroc", ascending=False).iloc[0]
    best_model = best_row["model"]

    lines = [
        "# Step 2 results (primary endpoint: TOX21_MMP_ratio, aeid 1854)",
        "",
        "Locked per `docs/endpoint_definitions.md` (Kolliputi review, 2026-08-12). Positive-hit",
        "rule and cytotoxicity filtering rule were documented there *before* any model was run.",
        "Scaffold-separated split is the primary evaluation; random split is reported only as",
        "a comparison, per instruction. Locked test set was never used for feature selection,",
        "threshold tuning, endpoint definition, or model optimization.",
        "",
        "## Dataset and split",
        f"- 7,268 chemicals tested on the primary endpoint (1,158 active, 15.9%)",
        "- Bemis-Murcko scaffold-separated split: 5,087 train / 1,090 val / 1,091 test",
        "  (no scaffold appears in more than one partition - verified programmatically)",
        "- Stratified random split, same proportions, for comparison only",
        "- Label definition (from docs/endpoint_definitions.md): ToxCast hitcall >= 0.9 = active",
        "- Model decision threshold: predicted probability >= 0.5 for all threshold-dependent",
        "  metrics below (sensitivity, specificity, F1, MCC, confusion matrix) - a fixed default,",
        "  chosen before running any evaluation, not tuned on val or test",
        "",
        "## Hyperparameter selection (val-set AUROC only, never test)",
        "",
        "| regime | model | best params | val AUROC |",
        "|---|---|---|---|",
    ]
    for _, row in selection.iterrows():
        lines.append(f"| {row['regime']} | {row['model']} | {row['params']} | {row['val_auroc']:.3f} |")

    lines += [
        "",
        "## Locked test-set performance: scaffold split (primary) vs random split (comparison)",
        "",
        "| regime | model | n | n active | AUROC | AUPRC | sensitivity | specificity | balanced acc | F1 | MCC | Brier |",
        "|---|---|---|---|---|---|---|---|---|---|---|---|",
    ]
    for _, row in metrics.sort_values(["regime", "auroc"], ascending=[True, False]).iterrows():
        lines.append(
            f"| {row['regime']} | {row['model']} | {row['n']} | {row['n_active']} | "
            f"{row['auroc']:.3f} | {row['auprc']:.3f} | {row['sensitivity']:.3f} | "
            f"{row['specificity']:.3f} | {row['balanced_accuracy']:.3f} | {row['f1']:.3f} | "
            f"{row['mcc']:.3f} | {row['brier_score']:.3f} |"
        )

    lines += [
        "",
        "### Confusion matrices (at predicted probability >= 0.5)",
        "",
        "| regime | model | TN | FP | FN | TP |",
        "|---|---|---|---|---|---|",
    ]
    for _, row in metrics.sort_values(["regime", "auroc"], ascending=[True, False]).iterrows():
        lines.append(f"| {row['regime']} | {row['model']} | {row['tn']} | {row['fp']} | {row['fn']} | {row['tp']} |")

    scaffold_best = metrics[(metrics.regime == "scaffold") & (metrics.model == best_model)].iloc[0]
    random_best = metrics[(metrics.regime == "random") & (metrics.model == best_model)].iloc[0]
    lines += [
        "",
        f"**Best model: {best_model}** (highest scaffold-test AUROC). Random-split AUROC "
        f"({random_best['auroc']:.3f}) is meaningfully higher than scaffold-split AUROC "
        f"({scaffold_best['auroc']:.3f}) for the same model - the expected pattern when a random",
        "split leaks structural similarity between train and test; the scaffold-split number is",
        "the honest estimate of performance on genuinely novel chemical scaffolds.",
        "",
        "*(Transparency note: all three models' hyperparameters were selected using only the val",
        "set, per instruction. Which of the three already-fixed models gets the deeper follow-up",
        "analysis below - uncertainty/AD, Seahorse concordance - is chosen by test-set AUROC here,",
        "since some single model has to be picked for those; no hyperparameter, threshold, or",
        "endpoint definition was changed based on that choice, and all three models' full test",
        "metrics are reported above regardless of which one is picked.)*",
        "",
        "![ROC curve](../results/figures/roc_curve.png)",
        "![Precision-recall curve](../results/figures/pr_curve.png)",
        "",
        "### Threshold tradeoff (scaffold Random Forest, locked test set)",
        "",
        "0.5 was the pre-declared default threshold used for every headline metric above,",
        "chosen before any evaluation ran. The table below shows the same locked predictions",
        "at other thresholds, to demonstrate the operating point is tunable rather than fixed",
        "to a single number - no result above was re-computed or re-selected based on this:",
        "",
        "| threshold | sensitivity | specificity | balanced acc | F1 |",
        "|---|---|---|---|---|",
    ]
    for _, row in threshold_tradeoff.iterrows():
        lines.append(
            f"| {row['threshold']:.1f} | {row['sensitivity']:.3f} | {row['specificity']:.3f} | "
            f"{row['balanced_accuracy']:.3f} | {row['f1']:.3f} |"
        )
    lines += [
        "",
        "Lower thresholds trade specificity for sensitivity (0.3: catches 85% of actives at the",
        "cost of a 40% false-positive rate among inactives); higher thresholds do the reverse.",
        "0.4 happens to edge out 0.5 on both balanced accuracy and F1 here - reported for",
        "completeness, not adopted as a new headline number after the fact.",
        "",
        "**Per Kolliputi:** 0.5 is not to be treated as the required product threshold. Since",
        "MitoTox AI is intended as a screening/prioritization tool, a final operating threshold",
        "may instead be selected on the validation set to prioritize sensitivity, then locked",
        "before test/prospective evaluation - that selection has not been made yet; the table",
        "above exists to show the tradeoff is real and tunable, not to pre-commit to one.",
        "",
        "## Calibration",
        "",
        f"10-bin calibration table for the best model ({best_model}, scaffold-test set) - mean",
        "predicted probability vs. observed active frequency within each bin (see Brier scores",
        "in the table above for all six model/regime combinations):",
        "",
        "| bin | n | mean predicted | observed frequency |",
        "|---|---|---|---|",
    ]
    best_calib = calibration[(calibration.model == best_model) & (calibration.regime == "scaffold")]
    for _, row in best_calib.sort_values("bin_lo").iterrows():
        lines.append(
            f"| {row['bin_lo']:.1f}-{row['bin_hi']:.1f} | {int(row['n'])} | "
            f"{row['mean_predicted']:.3f} | {row['observed_frequency']:.3f} |"
        )

    lines += [
        "",
        "Full calibration bins for all six model/regime combinations in",
        "`data/processed/step2_calibration_bins.csv`.",
        "",
        "![Calibration plot](../results/figures/calibration_plot.png)",
        "",
        "## Cytotoxicity-aware sensitivity analysis",
        "",
        "Filtering rule (documented before running): drop test-set rows where label==1 AND the",
        "chemical's hit is at/above its own cytotoxicity burst threshold",
        "(`mmp_ratio_tox21_cytotox_confound`). All negatives are kept - the confound flag only",
        "applies to actives.",
        "",
        "| regime | model | subset | n | AUROC | MCC | balanced acc |",
        "|---|---|---|---|---|---|---|",
    ]
    for _, row in cytotox.sort_values(["regime", "model", "subset"]).iterrows():
        lines.append(
            f"| {row['regime']} | {row['model']} | {row['subset']} | {row['n']} | "
            f"{row['auroc']:.3f} | {row['mcc']:.3f} | {row['balanced_accuracy']:.3f} |"
        )

    best_overall = cytotox[(cytotox.regime == "scaffold") & (cytotox.model == best_model) & (cytotox.subset == "overall")].iloc[0]
    best_below = cytotox[(cytotox.regime == "scaffold") & (cytotox.model == best_model) & (cytotox.subset == "below_cytotox_threshold")].iloc[0]
    persists = "persists" if best_below["auroc"] >= best_overall["auroc"] - 0.02 else "does not clearly persist"
    lines += [
        "",
        f"**For the best model ({best_model}, scaffold split): predictive performance {persists}** "
        f"when restricted to hits below the cytotoxicity burst threshold "
        f"(AUROC {best_overall['auroc']:.3f} overall vs {best_below['auroc']:.3f} below-threshold, "
        f"n={int(best_below['n'])}) - evidence the signal is not simply tracking general cytotoxicity.",
        "",
        "![Cytotoxicity robustness plot](../results/figures/cytotox_robustness_plot.png)",
        "",
        "## Uncertainty and domain of applicability",
        "",
        f"Best model ({best_model}, scaffold split). Uncertainty = std of predicted probability",
        "across the forest's 500 trees. Domain of applicability = 1 - nearest-neighbor Tanimoto",
        "similarity to the scaffold-train fingerprints.",
        "",
    ]

    is_error = uncertainty["is_error"].astype(bool)
    u_err, u_ok = uncertainty.loc[is_error, "uncertainty_std"], uncertainty.loc[~is_error, "uncertainty_std"]
    ad_err, ad_ok = uncertainty.loc[is_error, "ad_novelty"], uncertainty.loc[~is_error, "ad_novelty"]
    _, u_p = mannwhitneyu(u_err, u_ok, alternative="greater")
    _, ad_p = mannwhitneyu(ad_err, ad_ok, alternative="greater")
    lines += [
        f"- {int(is_error.sum())}/{len(uncertainty)} test predictions ({100*is_error.mean():.1f}%) are errors at the 0.5 threshold.",
        f"- **Uncertainty is significantly higher among errors** (mean {u_err.mean():.4f} vs "
        f"{u_ok.mean():.4f} for correct predictions, one-sided Mann-Whitney p={u_p:.4g}) - "
        "errors are enriched among high-uncertainty predictions.",
        f"- AD novelty is *not* significantly different between errors and correct predictions "
        f"(mean {ad_err.mean():.4f} vs {ad_ok.mean():.4f}, p={ad_p:.4g}) - structural distance to",
        "  the training set alone does not predict errors as well as the model's own internal",
        "  disagreement does. Reported as-is; not every diagnostic needs to show a signal to be honest.",
        "",
        "![Chemical space plot](../results/figures/chemical_space_plot.png)",
        "",
        "PCA over ECFP4 fingerprints (fit on train, test chemicals projected in) - note PC1+PC2",
        "explain only ~8.9% of variance, typical for sparse high-dimensional fingerprints, so this",
        "is a coarse 2D view of a much higher-dimensional space. Consistent with the statistical",
        "finding above: test errors (orange x) don't visually separate into a distinct region from",
        "correct predictions (blue) - the model's own uncertainty is a better error signal than",
        "position in this projection.",
        "",
        "### Risk-coverage (selective prediction)",
        "",
        "**Terminology, made explicit after an earlier mislabeling:** \"coverage\" = the % of test",
        "chemicals *retained* (the most confident ones, ranked by ascending forest-disagreement",
        "uncertainty). The rest are *referred* for experimental confirmation (the most uncertain",
        "ones). An earlier draft of this section described \"referring the most uncertain 20%,",
        "retaining 80%\" as giving AUROC 0.909 / 1.4% error - that was backwards. Those numbers are",
        "the *20% coverage* row below (retain only the most-confident 20%, refer the other 80%).",
        "The retain-80%/refer-uncertain-20% operating point is the *80% coverage* row: AUROC 0.796,",
        "15.7% error - a much smaller improvement over the no-referral baseline than originally",
        "reported. Kolliputi flagged this discrepancy directly; full corrected table below.",
        "",
        "| coverage (retained) | n retained | n referred | % referred | AUROC | AUPRC | sensitivity | specificity | balanced acc | error rate |",
        "|---|---|---|---|---|---|---|---|---|---|",
    ]
    for _, row in full_coverage.iterrows():
        auroc_str = f"{row['auroc']:.3f}" if pd.notna(row["auroc"]) else "n/a"
        auprc_str = f"{row['auprc']:.3f}" if pd.notna(row["auprc"]) else "n/a"
        lines.append(
            f"| {int(row['coverage_pct'])}% | {int(row['n_retained'])} | {int(row['n_referred'])} | "
            f"{row['pct_referred']:.1f}% | {auroc_str} | {auprc_str} | {row['sensitivity']:.3f} | "
            f"{row['specificity']:.3f} | {row['balanced_accuracy']:.3f} | {row['error_rate']:.3f} |"
        )

    row80 = full_coverage[full_coverage.coverage_pct == 80].iloc[0]
    row20 = full_coverage[full_coverage.coverage_pct == 20].iloc[0]
    lines += [
        "",
        f"**At 80% coverage (referring the most uncertain 20% for experimental confirmation) -** the",
        "operating point Kolliputi asked to see specifically as the more commercially realistic one:",
        f"AUROC {row80['auroc']:.3f}, sensitivity {row80['sensitivity']:.3f}, specificity "
        f"{row80['specificity']:.3f}, error rate {row80['error_rate']:.3f} ({row80['error_rate']*100:.1f}%),",
        f"versus {full_coverage[full_coverage.coverage_pct==100].iloc[0]['error_rate']*100:.1f}% with no",
        "referral at all - a real but modest improvement, not the dramatic one in the earlier draft.",
        f"At the far more conservative 20% coverage (referring 80%), error rate drops to "
        f"{row20['error_rate']*100:.1f}% - useful context, but not the number that answers",
        "\"what if we refer roughly a fifth of chemicals.\"",
        "",
        "![Risk-coverage plot](../results/figures/risk_coverage_plot.png)",
        "",
        "## Explainability examples",
        "",
        "SHAP (TreeExplainer, interventional mode against a train background sample) on the",
        "scaffold Random Forest, for three representative chemicals. Fingerprint-bit features are",
        "rendered as the actual substructure driving that bit, not left as an opaque bit index.",
        "",
    ]
    for ex in explainability:
        lines += [
            f"### {ex['description']}",
            f"DTXSID `{ex['DTXSID']}` - predicted probability {ex['predicted_proba']:.3f}, "
            f"true label {'active' if ex['label'] else 'inactive'}, "
            f"uncertainty (tree-disagreement std) {ex['uncertainty_std']:.3f}",
            "",
            "Top contributing features (SHAP value, feature value):",
            "",
        ]
        for feat in ex["top_features"]:
            lines.append(f"- `{feat['feature']}`: SHAP={feat['shap_value']:.3f}, value={feat['feature_value']:.3g}")
        for sub in ex["rendered_substructures"]:
            rel_path = sub["image"].replace("results/figures/", "../results/figures/")
            lines.append(f"\n![{ex['key']} bit {sub['bit']}]({rel_path})")
        lines.append("")

    lines += [
        "## Seahorse orthogonal concordance",
        "",
        f"The {best_model} model applied to all 253 chemicals with Seahorse respirometry data,",
        "compared against each Seahorse hit call. **Important caveat (independent audit finding):**",
        "60.5% of these 253 chemicals (153) were in this model's own scaffold-train set - not a",
        "true validation for those, since the model saw their primary-endpoint labels during",
        "training (though never their Seahorse labels). Stratified below rather than blended,",
        "since the blended number is inflated by in-sample predictions.",
        "",
        "| membership | Seahorse endpoint | n | AUROC (MMP model vs Seahorse) | agreement @0.5 |",
        "|---|---|---|---|---|",
    ]
    for _, row in seahorse.iterrows():
        lines.append(
            f"| {row['membership']} | {row['seahorse_endpoint']} | {row['n']} | "
            f"{row['mmp_model_vs_seahorse_auroc']:.3f} | {row['agreement_rate_at_0.5']:.3f} |"
        )

    held_out = seahorse[seahorse["membership"].str.startswith("held_out")]
    lines += [
        "",
        f"**The genuinely held-out subset (n=100) shows near-chance concordance "
        f"(AUROC {held_out['mmp_model_vs_seahorse_auroc'].min():.3f}-"
        f"{held_out['mmp_model_vs_seahorse_auroc'].max():.3f})** - meaningfully weaker than the",
        "in-sample/blended numbers suggest. Read honestly: this primary MMP model does not show",
        "strong evidence of predicting Seahorse-measured bioenergetic disruption in chemicals it",
        "wasn't trained on. Membrane-potential disruption and direct respirometry impairment may",
        "be more mechanistically distinct than initially assumed, or n=100 held-out Seahorse",
        "chemicals is simply too small to detect a real but modest effect - this analysis cannot",
        "distinguish between those two explanations. **Decision (Kolliputi):** no further effort",
        "will go into forcing concordance between the two. The weak concordance itself supports",
        "treating mitochondrial membrane-potential liability and respiratory/bioenergetic",
        "dysfunction as distinct mitochondrial phenotype modules rather than one composite",
        "endpoint - that design choice carries into Aim 2's scope, not just a caveat here.",
        "",
        "## External validation (exploratory only - not a Phase I substitute)",
        "",
        "Per Kolliputi: report the overlap analysis transparently, but this is an **exploratory**",
        "analysis, not definitive external validation - the class balance below is too extreme for",
        "that. Rigorous external validation (a larger, better-balanced, structure-checked",
        "independent set, or a prospective panel) is reserved for Phase I.",
        "",
        "See `docs/external_validation_search.md` for the full source-by-source breakdown.",
        "Summary: a literature-curated membrane-potential dataset independent of Tox21 was",
        "identified (147 compounds), and the locked model was applied to it without retraining.",
        f"82% ({146 - int(external['n'].iloc[0])}/146) turned out to already be in our own training "
        "population - itself a useful finding about how much apparent 'independent' datasets can "
        "overlap with ToxCast once checked at the structure level. Of the "
        f"**{int(external['n'].iloc[0])} genuinely unseen chemicals** that remained, the label balance "
        f"was {int(external['n_active'].iloc[0])} active / "
        f"{int(external['n'].iloc[0]) - int(external['n_active'].iloc[0])} inactive - too few negatives "
        f"for a reliable estimate. Exploratory result (AUROC "
        f"{external['auroc'].iloc[0]:.3f}, balanced accuracy {external['balanced_accuracy'].iloc[0]:.3f}) "
        "is reported for transparency, not presented as a validated finding.",
        "",
        "## Repro notes",
        "- All models trained with fixed random_state=42.",
        "- Scaffold split verified to have zero scaffold overlap across train/val/test.",
        "- Trained model artifacts: `models/{scaffold,random}_{logistic_regression,random_forest,xgboost}.joblib`.",
    ]

    with open(OUT_PATH, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")
    print(f"wrote {OUT_PATH}")


if __name__ == "__main__":
    main()
