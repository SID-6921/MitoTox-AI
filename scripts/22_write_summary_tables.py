"""Concise, presentation-ready model-comparison and endpoint-performance
tables for the STTR preliminary-data package - the detailed 12-column tables
already in docs/step2_results.md stay as the full record; this is the
condensed version for slides/the Preliminary Studies section.
"""
import pandas as pd

TEST_METRICS_PATH = "data/processed/step2_test_metrics.csv"
CYTOTOX_PATH = "data/processed/step2_cytotox_sensitivity.csv"
SEAHORSE_PATH = "data/processed/step2_seahorse_concordance.csv"
FULL_COVERAGE_PATH = "data/processed/step2_full_coverage_table.csv"
OUT_PATH = "docs/step2_summary_tables.md"


def main():
    metrics = pd.read_csv(TEST_METRICS_PATH)
    cytotox = pd.read_csv(CYTOTOX_PATH)
    seahorse = pd.read_csv(SEAHORSE_PATH)
    full_coverage = pd.read_csv(FULL_COVERAGE_PATH)

    lines = [
        "# Step 2 summary tables (condensed, for the preliminary-data package)",
        "",
        "Full detail (confusion matrices, all metrics, calibration bins) in",
        "`docs/step2_results.md`. These are the condensed versions for slides/writeup.",
        "",
        "## Model comparison (locked scaffold-held-out test set - primary evaluation)",
        "",
        "| Model | AUROC | AUPRC | MCC | Balanced accuracy | Brier |",
        "|---|---|---|---|---|---|",
    ]
    scaffold = metrics[metrics.regime == "scaffold"].sort_values("auroc", ascending=False)
    name_map = {"random_forest": "Random Forest", "xgboost": "XGBoost", "logistic_regression": "Logistic Regression"}
    for _, row in scaffold.iterrows():
        lines.append(
            f"| {name_map[row['model']]} | {row['auroc']:.3f} | {row['auprc']:.3f} | "
            f"{row['mcc']:.3f} | {row['balanced_accuracy']:.3f} | {row['brier_score']:.3f} |"
        )
    lines += [
        "",
        "(Random Forest selected as the primary model - highest scaffold-test AUROC. Random-split",
        "numbers, shown only as a comparison per the pre-registered analysis plan, are in the full",
        "table in `docs/step2_results.md`.)",
        "",
        "## Endpoint-specific performance",
        "",
        "Only the primary endpoint (TOX21_MMP_ratio) was modeled in Step 2, per the locked",
        "endpoint hierarchy - Seahorse and Nrf2/ARE are analyzed as orthogonal support and an",
        "oxidative-stress proxy respectively, not as separately-trained classifiers.",
        "",
        "| Analysis condition | n | AUROC | MCC | Balanced accuracy |",
        "|---|---|---|---|---|",
    ]
    rf_cytotox = cytotox[(cytotox.regime == "scaffold") & (cytotox.model == "random_forest")]
    for _, row in rf_cytotox.iterrows():
        label = "Primary endpoint - overall" if row["subset"] == "overall" else "Primary endpoint - below cytotoxicity threshold"
        lines.append(f"| {label} | {row['n']} | {row['auroc']:.3f} | {row['mcc']:.3f} | {row['balanced_accuracy']:.3f} |")

    lines += [
        "",
        "| Orthogonal analysis | n | AUROC (vs primary model) |",
        "|---|---|---|",
    ]
    held_out = seahorse[seahorse["membership"].str.startswith("held_out")]
    for _, row in held_out.iterrows():
        lines.append(f"| Seahorse {row['seahorse_endpoint']} (held-out chemicals only) | {row['n']} | {row['mmp_model_vs_seahorse_auroc']:.3f} |")

    lines += [
        "",
        "## Selective-prediction (risk-coverage) table",
        "",
        "\"Coverage\" = % of test chemicals *retained* (the most confident ones); the rest are",
        "*referred* for experimental confirmation (the most uncertain ones). 80% coverage - refer",
        "the most uncertain 20% - is the operating point flagged as the more commercially realistic",
        "one.",
        "",
        "| Coverage | Retained | Referred | % referred | AUROC | AUPRC | Sensitivity | Specificity | Balanced acc | Error rate |",
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

    with open(OUT_PATH, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")
    print(f"wrote {OUT_PATH}")


if __name__ == "__main__":
    main()
