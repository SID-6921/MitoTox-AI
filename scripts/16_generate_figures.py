"""Generate the Step 2 figures: ROC curve, PR curve, calibration plot, and
risk-coverage plot for the best model (scaffold-split Random Forest).
Colors from the dataviz skill's validated reference palette.
"""
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from sklearn.metrics import roc_curve, precision_recall_curve, auc, average_precision_score

PREDICTIONS_PATH = "data/processed/step2_predictions.csv"
CALIBRATION_PATH = "data/processed/step2_calibration_bins.csv"
RISK_COVERAGE_PATH = "data/processed/step2_risk_coverage.csv"
OUT_DIR = "results/figures"

BEST_REGIME, BEST_MODEL = "scaffold", "random_forest"

BLUE = "#2a78d6"
ORANGE = "#eb6834"
INK_PRIMARY = "#0b0b0b"
INK_SECONDARY = "#52514e"
INK_MUTED = "#898781"
GRIDLINE = "#e1e0d9"
BASELINE = "#c3c2b7"
SURFACE = "#fcfcfb"

plt.rcParams.update({
    "font.family": "sans-serif",
    "font.sans-serif": ["Segoe UI", "DejaVu Sans", "sans-serif"],
    "text.color": INK_PRIMARY,
    "axes.edgecolor": BASELINE,
    "axes.labelcolor": INK_SECONDARY,
    "xtick.color": INK_MUTED,
    "ytick.color": INK_MUTED,
    "axes.grid": True,
    "grid.color": GRIDLINE,
    "grid.linewidth": 0.8,
    "figure.facecolor": SURFACE,
    "axes.facecolor": SURFACE,
    "savefig.facecolor": SURFACE,
})


def style_axes(ax):
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.spines["left"].set_color(BASELINE)
    ax.spines["bottom"].set_color(BASELINE)
    ax.set_axisbelow(True)


def main():
    preds = pd.read_csv(PREDICTIONS_PATH, low_memory=False)
    test = preds[(preds.regime == BEST_REGIME) & (preds.model == BEST_MODEL) & (preds.split == "test")]
    y_true, y_prob = test["label"].values, test["predicted_proba"].values

    # ROC curve
    fpr, tpr, _ = roc_curve(y_true, y_prob)
    roc_auc = auc(fpr, tpr)
    fig, ax = plt.subplots(figsize=(6, 5), dpi=150)
    ax.plot(fpr, tpr, color=BLUE, linewidth=2, label=f"Random Forest (AUROC = {roc_auc:.3f})")
    ax.plot([0, 1], [0, 1], color=INK_MUTED, linewidth=1.5, linestyle="--", label="Chance")
    ax.set_xlabel("False positive rate")
    ax.set_ylabel("True positive rate")
    ax.set_title("ROC curve - primary endpoint (TOX21_MMP_ratio)\nscaffold-held-out test set")
    ax.legend(loc="lower right", frameon=False)
    style_axes(ax)
    fig.tight_layout()
    fig.savefig(f"{OUT_DIR}/roc_curve.png")
    plt.close(fig)

    # PR curve
    precision, recall, _ = precision_recall_curve(y_true, y_prob)
    # average_precision_score (not auc(recall, precision), which trapezoidally
    # interpolates and gives a slightly different number) - matches the AUPRC
    # already reported in docs/step2_results.md / step2_test_metrics.csv
    pr_auc = average_precision_score(y_true, y_prob)
    prevalence = y_true.mean()
    fig, ax = plt.subplots(figsize=(6, 5), dpi=150)
    ax.plot(recall, precision, color=BLUE, linewidth=2, label=f"Random Forest (AUPRC = {pr_auc:.3f})")
    ax.axhline(prevalence, color=INK_MUTED, linewidth=1.5, linestyle="--",
               label=f"Baseline prevalence ({prevalence:.3f})")
    ax.set_xlabel("Recall (sensitivity)")
    ax.set_ylabel("Precision")
    ax.set_title("Precision-recall curve - primary endpoint\nscaffold-held-out test set")
    ax.legend(loc="upper right", frameon=False)
    style_axes(ax)
    fig.tight_layout()
    fig.savefig(f"{OUT_DIR}/pr_curve.png")
    plt.close(fig)

    # Calibration plot
    calib = pd.read_csv(CALIBRATION_PATH)
    calib = calib[(calib.regime == BEST_REGIME) & (calib.model == BEST_MODEL)].sort_values("bin_lo")
    fig, ax = plt.subplots(figsize=(6, 5), dpi=150)
    ax.plot([0, 1], [0, 1], color=INK_MUTED, linewidth=1.5, linestyle="--", label="Perfect calibration")
    ax.plot(calib["mean_predicted"], calib["observed_frequency"], color=BLUE, linewidth=2,
            marker="o", markersize=6, label="Random Forest")
    ax.set_xlabel("Mean predicted probability")
    ax.set_ylabel("Observed active frequency")
    ax.set_title("Calibration - primary endpoint\nscaffold-held-out test set, 10 bins")
    ax.legend(loc="upper left", frameon=False)
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    style_axes(ax)
    fig.tight_layout()
    fig.savefig(f"{OUT_DIR}/calibration_plot.png")
    plt.close(fig)

    # Risk-coverage plot
    risk_cov = pd.read_csv(RISK_COVERAGE_PATH)
    fig, ax = plt.subplots(figsize=(6, 5), dpi=150)
    ax.plot(risk_cov["coverage_pct"], risk_cov["auroc"], color=BLUE, linewidth=2,
            marker="o", markersize=5, label="AUROC (retained subset)")
    ax.plot(risk_cov["coverage_pct"], risk_cov["error_rate"], color=ORANGE, linewidth=2,
            marker="o", markersize=5, label="Error rate (retained subset)")
    ax.set_xlabel("Coverage (% of test chemicals retained, most confident first)")
    ax.set_ylabel("Value")
    ax.set_title("Risk-coverage (selective prediction) - primary endpoint\nreferring the most uncertain chemicals out")
    ax.legend(loc="center right", frameon=False)
    ax.set_ylim(0, 1)
    style_axes(ax)
    fig.tight_layout()
    fig.savefig(f"{OUT_DIR}/risk_coverage_plot.png")
    plt.close(fig)

    print(f"wrote 4 figures to {OUT_DIR}/")


if __name__ == "__main__":
    main()
