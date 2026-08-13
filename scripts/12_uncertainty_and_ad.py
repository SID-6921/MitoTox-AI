"""Model uncertainty and domain-of-applicability analysis for the best model
(scaffold-regime Random Forest, selected in scripts/10 by locked-test AUROC).

Uncertainty: per-chemical std of predicted probability across the forest's
500 trees ("forest disagreement") - a standard RF-native epistemic
uncertainty measure, computed on the already-trained best model rather than
training a separate bootstrap ensemble.

Domain of applicability: 1 - nearest-neighbor Tanimoto similarity to the
scaffold-train set's ECFP4 fingerprints (vectorized via bit-matrix dot
products rather than pairwise RDKit calls, since fingerprints are already
stored as 0/1 columns).

Risk-coverage: rank test chemicals by uncertainty (most confident first),
show how AUROC/error rate on the retained subset changes as coverage shrinks
from 100% down to 50% (i.e. referring the most uncertain 10%, 20%, ... out).
"""
import joblib
import numpy as np
import pandas as pd
from sklearn.metrics import roc_auc_score
from scipy.stats import mannwhitneyu

DATASET_PATH = "data/processed/step2_mmp_dataset.csv"
SPLITS_PATH = "data/processed/step2_splits.csv"
MODEL_PATH = "models/scaffold_random_forest.joblib"
UNCERTAINTY_OUT = "data/processed/step2_uncertainty_ad.csv"
RISK_COVERAGE_OUT = "data/processed/step2_risk_coverage.csv"

FP_COLS = [f"ecfp4_{i}" for i in range(2048)]
DESCRIPTOR_COLS = [
    "mol_weight", "logp", "tpsa", "hbd", "hba",
    "rotatable_bonds", "aromatic_rings", "heavy_atoms", "fraction_csp3",
]
FEATURE_COLS = FP_COLS + DESCRIPTOR_COLS
THRESHOLD = 0.5


def tanimoto_nearest_neighbor(query_bits, ref_bits):
    """query_bits: (n_query, n_bits), ref_bits: (n_ref, n_bits), both 0/1.
    Returns, for each query row, the max Tanimoto similarity to any ref row."""
    intersection = query_bits @ ref_bits.T  # (n_query, n_ref)
    query_pop = query_bits.sum(axis=1, keepdims=True)  # (n_query, 1)
    ref_pop = ref_bits.sum(axis=1, keepdims=True).T  # (1, n_ref)
    union = query_pop + ref_pop - intersection
    tanimoto = np.divide(intersection, union, out=np.zeros_like(intersection, dtype=float), where=union > 0)
    return tanimoto.max(axis=1)


def main():
    df = pd.read_csv(DATASET_PATH, low_memory=False)
    splits = pd.read_csv(SPLITS_PATH, low_memory=False)
    df = df.merge(splits, on="DTXSID", how="inner")

    train = df[df["scaffold_split"] == "train"]
    test = df[df["scaffold_split"] == "test"]

    model = joblib.load(MODEL_PATH)
    X_test = test[FEATURE_COLS].values
    y_test = test["label"].values

    tree_probs = np.stack([tree.predict_proba(X_test)[:, 1] for tree in model.estimators_])
    mean_proba = tree_probs.mean(axis=0)
    uncertainty = tree_probs.std(axis=0)

    train_fp = train[FP_COLS].values.astype(float)
    test_fp = test[FP_COLS].values.astype(float)
    nn_similarity = tanimoto_nearest_neighbor(test_fp, train_fp)
    ad_novelty = 1 - nn_similarity

    y_pred = (mean_proba >= THRESHOLD).astype(int)
    is_error = (y_pred != y_test)

    result = pd.DataFrame({
        "DTXSID": test["DTXSID"].values,
        "label": y_test,
        "predicted_proba": mean_proba,
        "is_error": is_error,
        "uncertainty_std": uncertainty,
        "nn_tanimoto_to_train": nn_similarity,
        "ad_novelty": ad_novelty,
    })
    result.to_csv(UNCERTAINTY_OUT, index=False)

    u_err, u_ok = result.loc[is_error, "uncertainty_std"], result.loc[~is_error, "uncertainty_std"]
    ad_err, ad_ok = result.loc[is_error, "ad_novelty"], result.loc[~is_error, "ad_novelty"]
    u_stat, u_p = mannwhitneyu(u_err, u_ok, alternative="greater")
    ad_stat, ad_p = mannwhitneyu(ad_err, ad_ok, alternative="greater")
    print(f"errors: {is_error.sum()}/{len(result)} ({100*is_error.mean():.1f}%)")
    print(f"mean uncertainty: errors={u_err.mean():.4f} vs correct={u_ok.mean():.4f} "
          f"(Mann-Whitney U, one-sided p={u_p:.4f})")
    print(f"mean AD novelty: errors={ad_err.mean():.4f} vs correct={ad_ok.mean():.4f} "
          f"(Mann-Whitney U, one-sided p={ad_p:.4f})")

    # risk-coverage: sort by ascending uncertainty (most confident first), grow
    # coverage from 10% to 100%, report AUROC/error-rate/accuracy on that subset
    order = np.argsort(result["uncertainty_std"].values)
    n = len(result)
    rows = []
    for coverage_pct in range(10, 101, 10):
        k = max(int(n * coverage_pct / 100), 2)
        idx = order[:k]
        y_sub, p_sub = y_test[idx], mean_proba[idx]
        auroc = roc_auc_score(y_sub, p_sub) if len(set(y_sub)) > 1 else float("nan")
        err_rate = (y_pred[idx] != y_sub).mean()
        rows.append({"coverage_pct": coverage_pct, "n": k, "auroc": auroc, "error_rate": err_rate})
        print(f"coverage {coverage_pct}%: n={k}, AUROC={auroc:.3f}, error_rate={err_rate:.3f}")

    pd.DataFrame(rows).to_csv(RISK_COVERAGE_OUT, index=False)
    print(f"wrote {UNCERTAINTY_OUT} and {RISK_COVERAGE_OUT}")


if __name__ == "__main__":
    main()
