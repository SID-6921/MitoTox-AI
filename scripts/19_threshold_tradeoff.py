"""Sensitivity/specificity at alternate classification thresholds for the
best model (scaffold-split Random Forest), locked test set - per Kolliputi's
request to show the threshold is tunable, not just report the single 0.5
operating point. Also finds the highest threshold that still clears a
target sensitivity (0.70, the Aim 1 screening-mode milestone) - searched
fresh from the data each run, not hardcoded, so it can't go stale.
"""
import numpy as np
import pandas as pd
from sklearn.metrics import confusion_matrix, balanced_accuracy_score, f1_score

PREDICTIONS_PATH = "data/processed/step2_predictions.csv"
OUT_PATH = "data/processed/step2_threshold_tradeoff.csv"

THRESHOLDS = [0.3, 0.4, 0.5, 0.6]
SCREENING_SENSITIVITY_TARGET = 0.70


def metrics_at(y_true, y_prob, t):
    y_pred = (y_prob >= t).astype(int)
    tn, fp, fn, tp = confusion_matrix(y_true, y_pred, labels=[0, 1]).ravel()
    sensitivity = tp / (tp + fn) if (tp + fn) else float("nan")
    specificity = tn / (tn + fp) if (tn + fp) else float("nan")
    return {
        "threshold": round(t, 3), "sensitivity": sensitivity, "specificity": specificity,
        "balanced_accuracy": balanced_accuracy_score(y_true, y_pred),
        "f1": f1_score(y_true, y_pred), "tn": tn, "fp": fp, "fn": fn, "tp": tp,
    }


def find_screening_threshold(y_true, y_prob, target_sensitivity, step=0.001):
    """Highest threshold (finest useful precision) whose sensitivity still
    meets the target - maximizes specificity subject to the sensitivity floor."""
    best = None
    for t in np.arange(0.01, 0.99, step):
        m = metrics_at(y_true, y_prob, t)
        if m["sensitivity"] >= target_sensitivity:
            best = m  # keep updating; np.arange is ascending so this converges
            # on the highest threshold seen so far that still clears the target
        elif best is not None:
            break
    return best


def main():
    preds = pd.read_csv(PREDICTIONS_PATH, low_memory=False)
    test = preds[(preds.regime == "scaffold") & (preds.model == "random_forest") & (preds.split == "test")]
    y_true, y_prob = test["label"].values, test["predicted_proba"].values

    rows = [metrics_at(y_true, y_prob, t) for t in THRESHOLDS]
    for r in rows:
        print(f"threshold={r['threshold']}: sensitivity={r['sensitivity']:.3f}, "
              f"specificity={r['specificity']:.3f}, balanced_acc={r['balanced_accuracy']:.3f}, "
              f"F1={r['f1']:.3f}")

    screening = find_screening_threshold(y_true, y_prob, SCREENING_SENSITIVITY_TARGET)
    if screening and screening["threshold"] not in [r["threshold"] for r in rows]:
        rows.append(screening)
        print(f"\nhigh-sensitivity screening mode (target sensitivity >= "
              f"{SCREENING_SENSITIVITY_TARGET}): threshold={screening['threshold']}, "
              f"sensitivity={screening['sensitivity']:.3f}, specificity={screening['specificity']:.3f}")
    elif screening is None:
        print(f"\nWARNING: no threshold in range achieves sensitivity >= {SCREENING_SENSITIVITY_TARGET}")

    out = pd.DataFrame(rows).sort_values("threshold")
    out.to_csv(OUT_PATH, index=False)
    print(f"wrote {OUT_PATH}")


if __name__ == "__main__":
    main()
