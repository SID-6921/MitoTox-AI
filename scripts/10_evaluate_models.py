"""Evaluate every trained model on its locked test set (primary: scaffold
regime; random regime reported only as a comparison, per Kolliputi). Fixed
0.5 probability threshold for all threshold-dependent metrics - chosen before
looking at any test-set result, not tuned on val or test.
"""
import numpy as np
import pandas as pd
from sklearn.metrics import (
    roc_auc_score, average_precision_score, balanced_accuracy_score,
    f1_score, matthews_corrcoef, confusion_matrix, brier_score_loss,
)

PREDICTIONS_PATH = "data/processed/step2_predictions.csv"
OUT_PATH = "data/processed/step2_test_metrics.csv"
CALIBRATION_OUT_PATH = "data/processed/step2_calibration_bins.csv"

THRESHOLD = 0.5


def compute_metrics(y_true, y_prob):
    y_pred = (y_prob >= THRESHOLD).astype(int)
    tn, fp, fn, tp = confusion_matrix(y_true, y_pred, labels=[0, 1]).ravel()
    sensitivity = tp / (tp + fn) if (tp + fn) else float("nan")
    specificity = tn / (tn + fp) if (tn + fp) else float("nan")
    return {
        "n": len(y_true),
        "n_active": int(y_true.sum()),
        "auroc": roc_auc_score(y_true, y_prob),
        "auprc": average_precision_score(y_true, y_prob),
        "sensitivity": sensitivity,
        "specificity": specificity,
        "balanced_accuracy": balanced_accuracy_score(y_true, y_pred),
        "f1": f1_score(y_true, y_pred),
        "mcc": matthews_corrcoef(y_true, y_pred),
        "tn": tn, "fp": fp, "fn": fn, "tp": tp,
        "brier_score": brier_score_loss(y_true, y_prob),
    }


def calibration_table(y_true, y_prob, model, regime, n_bins=10):
    bins = np.linspace(0, 1, n_bins + 1)
    bin_idx = np.digitize(y_prob, bins[1:-1])
    rows = []
    for b in range(n_bins):
        mask = bin_idx == b
        if mask.sum() == 0:
            continue
        rows.append({
            "model": model, "regime": regime,
            "bin_lo": bins[b], "bin_hi": bins[b + 1],
            "n": int(mask.sum()),
            "mean_predicted": float(y_prob[mask].mean()),
            "observed_frequency": float(y_true[mask].mean()),
        })
    return rows


def main():
    preds = pd.read_csv(PREDICTIONS_PATH, low_memory=False)
    test_preds = preds[preds["split"] == "test"]

    rows = []
    calib_rows = []
    for (regime, model), group in test_preds.groupby(["regime", "model"]):
        y_true = group["label"].values
        y_prob = group["predicted_proba"].values
        metrics = compute_metrics(y_true, y_prob)
        metrics.update({"regime": regime, "model": model})
        rows.append(metrics)
        calib_rows.extend(calibration_table(y_true, y_prob, model, regime))
        print(f"[{regime}/test] {model}: AUROC={metrics['auroc']:.3f} "
              f"AUPRC={metrics['auprc']:.3f} MCC={metrics['mcc']:.3f} "
              f"Brier={metrics['brier_score']:.3f}")

    out = pd.DataFrame(rows)[[
        "regime", "model", "n", "n_active", "auroc", "auprc", "sensitivity",
        "specificity", "balanced_accuracy", "f1", "mcc", "brier_score",
        "tn", "fp", "fn", "tp",
    ]]
    out.to_csv(OUT_PATH, index=False)
    pd.DataFrame(calib_rows).to_csv(CALIBRATION_OUT_PATH, index=False)
    print(f"wrote {OUT_PATH} and {CALIBRATION_OUT_PATH}")


if __name__ == "__main__":
    main()
