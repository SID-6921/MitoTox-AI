"""Sensitivity/specificity at alternate classification thresholds for the
best model (scaffold-split Random Forest), locked test set - per Kolliputi's
request to show the threshold is tunable, not just report the single 0.5
operating point.
"""
import pandas as pd
from sklearn.metrics import confusion_matrix, balanced_accuracy_score, f1_score

PREDICTIONS_PATH = "data/processed/step2_predictions.csv"
OUT_PATH = "data/processed/step2_threshold_tradeoff.csv"

THRESHOLDS = [0.3, 0.4, 0.5, 0.6]


def main():
    preds = pd.read_csv(PREDICTIONS_PATH, low_memory=False)
    test = preds[(preds.regime == "scaffold") & (preds.model == "random_forest") & (preds.split == "test")]
    y_true, y_prob = test["label"].values, test["predicted_proba"].values

    rows = []
    for t in THRESHOLDS:
        y_pred = (y_prob >= t).astype(int)
        tn, fp, fn, tp = confusion_matrix(y_true, y_pred, labels=[0, 1]).ravel()
        sensitivity = tp / (tp + fn) if (tp + fn) else float("nan")
        specificity = tn / (tn + fp) if (tn + fp) else float("nan")
        rows.append({
            "threshold": t, "sensitivity": sensitivity, "specificity": specificity,
            "balanced_accuracy": balanced_accuracy_score(y_true, y_pred),
            "f1": f1_score(y_true, y_pred), "tn": tn, "fp": fp, "fn": fn, "tp": tp,
        })
        print(f"threshold={t}: sensitivity={sensitivity:.3f}, specificity={specificity:.3f}, "
              f"balanced_acc={rows[-1]['balanced_accuracy']:.3f}, F1={rows[-1]['f1']:.3f}")

    pd.DataFrame(rows).to_csv(OUT_PATH, index=False)
    print(f"wrote {OUT_PATH}")


if __name__ == "__main__":
    main()
