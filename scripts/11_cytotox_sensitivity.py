"""Cytotoxicity-aware sensitivity analysis: does predictive performance
persist when the confounded actives (hits at/above the chemical's own
cytotoxicity burst threshold) are excluded from the test set?

Filtering rule (documented here per Kolliputi, before running this):
drop test-set rows where label == 1 AND mmp_ratio_tox21_cytotox_confound is
True. All negatives are kept as-is (the confound flag is only meaningful for
actives - a negative can't be a "confounded hit"). This leaves only the
inactives plus the actives whose hit occurs below the chemical's cytotoxicity
burst threshold, i.e. the subset of positives most likely to reflect a
mitochondria-specific effect rather than general cytotoxicity.
"""
import pandas as pd
from sklearn.metrics import (
    roc_auc_score, average_precision_score, balanced_accuracy_score,
    f1_score, matthews_corrcoef, confusion_matrix, brier_score_loss,
)

DATASET_PATH = "data/processed/step2_mmp_dataset.csv"
SPLITS_PATH = "data/processed/step2_splits.csv"
PREDICTIONS_PATH = "data/processed/step2_predictions.csv"
OUT_PATH = "data/processed/step2_cytotox_sensitivity.csv"

THRESHOLD = 0.5


def compute_metrics(y_true, y_prob):
    y_pred = (y_prob >= THRESHOLD).astype(int)
    tn, fp, fn, tp = confusion_matrix(y_true, y_pred, labels=[0, 1]).ravel()
    sensitivity = tp / (tp + fn) if (tp + fn) else float("nan")
    specificity = tn / (tn + fp) if (tn + fp) else float("nan")
    return {
        "n": len(y_true), "n_active": int(y_true.sum()),
        "auroc": roc_auc_score(y_true, y_prob) if len(set(y_true)) > 1 else float("nan"),
        "auprc": average_precision_score(y_true, y_prob) if len(set(y_true)) > 1 else float("nan"),
        "sensitivity": sensitivity, "specificity": specificity,
        "balanced_accuracy": balanced_accuracy_score(y_true, y_pred),
        "f1": f1_score(y_true, y_pred), "mcc": matthews_corrcoef(y_true, y_pred),
        "brier_score": brier_score_loss(y_true, y_prob),
    }


def main():
    dataset = pd.read_csv(DATASET_PATH, low_memory=False)
    splits = pd.read_csv(SPLITS_PATH, low_memory=False)
    preds = pd.read_csv(PREDICTIONS_PATH, low_memory=False)

    confound = dataset[["DTXSID", "mmp_ratio_tox21_cytotox_confound"]]
    test_preds = preds[preds["split"] == "test"].merge(confound, on="DTXSID", how="left")

    n_confounded_actives = int(
        ((test_preds["label"] == 1) & (test_preds["mmp_ratio_tox21_cytotox_confound"] == True)
         & (test_preds["regime"] == "scaffold") & (test_preds["model"] == "random_forest")).sum()
    )
    print(f"confounded actives excluded from sub-threshold analysis (scaffold/RF test set): {n_confounded_actives}")

    rows = []
    for (regime, model), group in test_preds.groupby(["regime", "model"]):
        overall = compute_metrics(group["label"].values, group["predicted_proba"].values)
        overall.update({"regime": regime, "model": model, "subset": "overall"})
        rows.append(overall)

        sub = group[~((group["label"] == 1) & (group["mmp_ratio_tox21_cytotox_confound"] == True))]
        below = compute_metrics(sub["label"].values, sub["predicted_proba"].values)
        below.update({"regime": regime, "model": model, "subset": "below_cytotox_threshold"})
        rows.append(below)

        print(f"[{regime}] {model}: overall AUROC={overall['auroc']:.3f} (n={overall['n']}) "
              f"vs below-threshold AUROC={below['auroc']:.3f} (n={below['n']})")

    out = pd.DataFrame(rows)[[
        "regime", "model", "subset", "n", "n_active", "auroc", "auprc",
        "sensitivity", "specificity", "balanced_accuracy", "f1", "mcc", "brier_score",
    ]]
    out.to_csv(OUT_PATH, index=False)
    print(f"wrote {OUT_PATH}")


if __name__ == "__main__":
    main()
