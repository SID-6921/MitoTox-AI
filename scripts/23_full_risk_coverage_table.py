"""Full selective-prediction (risk-coverage) table with all requested metrics,
per Kolliputi's follow-up. Terminology, made unambiguous after a real
mislabeling was caught: "coverage" = the X% of test chemicals RETAINED
(the most confident ones, lowest forest-disagreement uncertainty first).
The other (100-X)% are REFERRED for experimental confirmation (the most
uncertain ones). Coverage 20% means retain the 218 most-confident chemicals
and refer the 873 most uncertain - NOT "refer the most uncertain 20%".
That distinction was reported backwards in earlier prose (docs/step2_results.md,
docs/step2_verification.md, README.md, docs/preliminary_studies_paragraph.md,
and two emails) and is fixed here and in every doc that cited it.
"""
import numpy as np
import pandas as pd
from sklearn.metrics import (
    roc_auc_score, average_precision_score, balanced_accuracy_score, confusion_matrix,
)

UNCERTAINTY_PATH = "data/processed/step2_uncertainty_ad.csv"
OUT_PATH = "data/processed/step2_full_coverage_table.csv"

THRESHOLD = 0.5
COVERAGE_LEVELS = [100, 90, 80, 70, 60, 50, 40, 30, 20]


def main():
    df = pd.read_csv(UNCERTAINTY_PATH)
    n_total = len(df)
    # ascending uncertainty = most confident first (same ordering as scripts/12)
    order = df.sort_values("uncertainty_std").reset_index(drop=True)

    rows = []
    for coverage_pct in COVERAGE_LEVELS:
        k = max(round(n_total * coverage_pct / 100), 2)
        retained = order.iloc[:k]
        n_referred = n_total - k

        y_true = retained["label"].values
        y_prob = retained["predicted_proba"].values
        y_pred = (y_prob >= THRESHOLD).astype(int)

        if len(set(y_true)) > 1:
            auroc = roc_auc_score(y_true, y_prob)
            auprc = average_precision_score(y_true, y_prob)
        else:
            auroc = auprc = float("nan")

        tn, fp, fn, tp = confusion_matrix(y_true, y_pred, labels=[0, 1]).ravel()
        sensitivity = tp / (tp + fn) if (tp + fn) else float("nan")
        specificity = tn / (tn + fp) if (tn + fp) else float("nan")
        balanced_acc = balanced_accuracy_score(y_true, y_pred) if len(set(y_true)) > 1 else float("nan")
        error_rate = (y_pred != y_true).mean()

        rows.append({
            "coverage_pct": coverage_pct,
            "n_retained": k,
            "n_referred": n_referred,
            "pct_referred": round(100 * n_referred / n_total, 1),
            "auroc": auroc,
            "auprc": auprc,
            "sensitivity": sensitivity,
            "specificity": specificity,
            "balanced_accuracy": balanced_acc,
            "error_rate": error_rate,
        })
        print(f"coverage={coverage_pct}% (retain {k}, refer {n_referred} = "
              f"{rows[-1]['pct_referred']}%): AUROC={auroc:.3f} AUPRC={auprc:.3f} "
              f"sens={sensitivity:.3f} spec={specificity:.3f} bal_acc={balanced_acc:.3f} "
              f"error={error_rate:.3f}")

    pd.DataFrame(rows).to_csv(OUT_PATH, index=False)
    print(f"wrote {OUT_PATH}")


if __name__ == "__main__":
    main()
