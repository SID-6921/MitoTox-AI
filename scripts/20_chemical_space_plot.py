"""Chemical-space / domain-of-applicability visualization: 2D PCA over ECFP4
fingerprints, train chemicals as background context, test chemicals colored
by correct/incorrect prediction - shows visually whether errors cluster in
sparser (out-of-domain) regions of chemical space.
"""
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from sklearn.decomposition import PCA

DATASET_PATH = "data/processed/step2_mmp_dataset.csv"
SPLITS_PATH = "data/processed/step2_splits.csv"
UNCERTAINTY_PATH = "data/processed/step2_uncertainty_ad.csv"
OUT_PATH = "results/figures/chemical_space_plot.png"

FP_COLS = [f"ecfp4_{i}" for i in range(2048)]
SEED = 42

BLUE = "#2a78d6"
ORANGE = "#eb6834"
INK_PRIMARY = "#0b0b0b"
INK_SECONDARY = "#52514e"
INK_MUTED = "#898781"
GRIDLINE = "#e1e0d9"
BASELINE = "#c3c2b7"
SURFACE = "#fcfcfb"
TRAIN_GRAY = "#c3c2b7"

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


def main():
    dataset = pd.read_csv(DATASET_PATH, low_memory=False)
    splits = pd.read_csv(SPLITS_PATH, low_memory=False)
    uncertainty = pd.read_csv(UNCERTAINTY_PATH)

    df = dataset.merge(splits, on="DTXSID", how="inner")
    train = df[df["scaffold_split"] == "train"]
    test = df[df["scaffold_split"] == "test"].merge(
        uncertainty[["DTXSID", "is_error"]], on="DTXSID", how="left"
    )

    # fit PCA on train fingerprints only (train defines "chemical space" here,
    # test chemicals are then projected into it - matches the AD framing)
    pca = PCA(n_components=2, random_state=SEED)
    train_xy = pca.fit_transform(train[FP_COLS].values)
    test_xy = pca.transform(test[FP_COLS].values)
    var_explained = pca.explained_variance_ratio_

    is_error = test["is_error"].fillna(False).astype(bool).values

    fig, ax = plt.subplots(figsize=(7, 6), dpi=150)
    ax.scatter(train_xy[:, 0], train_xy[:, 1], s=8, color=TRAIN_GRAY, alpha=0.5,
               label=f"Train (n={len(train):,})", zorder=1)
    ax.scatter(test_xy[~is_error, 0], test_xy[~is_error, 1], s=14, color=BLUE, alpha=0.75,
               label=f"Test, correct (n={(~is_error).sum():,})", zorder=2)
    ax.scatter(test_xy[is_error, 0], test_xy[is_error, 1], s=18, color=ORANGE, alpha=0.85,
               marker="x", linewidths=1.3, label=f"Test, error (n={is_error.sum():,})", zorder=3)

    ax.set_xlabel(f"PC1 ({var_explained[0]*100:.1f}% variance)")
    ax.set_ylabel(f"PC2 ({var_explained[1]*100:.1f}% variance)")
    ax.set_title("Chemical space (PCA over ECFP4 fingerprints)\ntrain-fitted projection, primary endpoint")
    ax.legend(loc="best", frameon=False, fontsize=9)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.spines["left"].set_color(BASELINE)
    ax.spines["bottom"].set_color(BASELINE)
    ax.set_axisbelow(True)
    fig.tight_layout()
    fig.savefig(OUT_PATH)
    plt.close(fig)
    print(f"wrote {OUT_PATH} (PC1+PC2 explain {sum(var_explained)*100:.1f}% of variance)")


if __name__ == "__main__":
    main()
