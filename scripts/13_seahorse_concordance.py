"""Apply the best model (scaffold-regime Random Forest) to every chemical
with Seahorse respirometry data, and check concordance between the model's
MMP-based prediction and the mechanistically-orthogonal Seahorse bioenergetic
hit calls - per Kolliputi's request to analyze Seahorse separately and check
agreement with the primary predictions, not fold it into the primary model.

Stratified by scaffold_split membership: 60.5% of the 253 Seahorse-tested
chemicals were in this model's own scaffold-train set (independent audit
finding), so a blended concordance number is inflated by in-sample
memorization. The held-out (val+test) subset is the genuine orthogonal
validation signal and is reported separately, not just blended in.
"""
import joblib
import numpy as np
import pandas as pd
from sklearn.metrics import roc_auc_score

MODELING_TABLE_PATH = "data/processed/mito_modeling_table.csv"
FINGERPRINTS_PATH = "data/processed/mito_chemicals_fingerprints.csv"
SPLITS_PATH = "data/processed/step2_splits.csv"
MODEL_PATH = "models/scaffold_random_forest.joblib"
OUT_PATH = "data/processed/step2_seahorse_concordance.csv"

FP_COLS = [f"ecfp4_{i}" for i in range(2048)]
DESCRIPTOR_COLS = [
    "mol_weight", "logp", "tpsa", "hbd", "hba",
    "rotatable_bonds", "aromatic_rings", "heavy_atoms", "fraction_csp3",
]
FEATURE_COLS = FP_COLS + DESCRIPTOR_COLS

SEAHORSE_ENDPOINTS = ["primary_basal_resp_rate", "primary_max_resp_rate", "primary_inhib_resp_rate"]
THRESHOLD = 0.5


def compute_group_metrics(sub, endpoint, membership_label):
    sub = sub[sub[endpoint].notna()]
    y_true = sub[endpoint].values
    y_prob = sub["mmp_predicted_proba"].values
    y_pred = sub["mmp_predicted_class"].values
    agreement = (y_pred == y_true).mean() if len(sub) else float("nan")
    auroc = roc_auc_score(y_true, y_prob) if len(set(y_true)) > 1 else float("nan")
    return {
        "seahorse_endpoint": endpoint, "membership": membership_label,
        "n": len(sub), "n_seahorse_active": int(y_true.sum()) if len(sub) else 0,
        "mmp_model_vs_seahorse_auroc": auroc, "agreement_rate_at_0.5": agreement,
    }


def main():
    modeling = pd.read_csv(MODELING_TABLE_PATH, low_memory=False)
    fps = pd.read_csv(FINGERPRINTS_PATH, low_memory=False)
    splits = pd.read_csv(SPLITS_PATH, low_memory=False)
    model = joblib.load(MODEL_PATH)

    has_seahorse = modeling[modeling[SEAHORSE_ENDPOINTS].notna().any(axis=1)].copy()
    has_seahorse = has_seahorse.merge(fps, on="DTXSID", how="inner")
    has_seahorse = has_seahorse.merge(splits[["DTXSID", "scaffold_split"]], on="DTXSID", how="left")
    print(f"chemicals with any Seahorse respirometry data: {len(has_seahorse):,}")

    n_in_train = int((has_seahorse["scaffold_split"] == "train").sum())
    print(f"of those, in this model's own scaffold-train set: {n_in_train:,} "
          f"({100*n_in_train/len(has_seahorse):.1f}%) - not part of the primary MMP labeled")
    print("set at all for chemicals with scaffold_split NaN (never tested on the primary endpoint).")

    X = has_seahorse[FEATURE_COLS].values
    has_seahorse["mmp_predicted_proba"] = model.predict_proba(X)[:, 1]
    has_seahorse["mmp_predicted_class"] = (has_seahorse["mmp_predicted_proba"] >= THRESHOLD).astype(int)

    is_held_out = has_seahorse["scaffold_split"].isin(["val", "test"]) | has_seahorse["scaffold_split"].isna()
    groups = {
        "blended (all 253, includes in-sample train chemicals)": has_seahorse,
        "in_scaffold_train (in-sample, not a true validation)": has_seahorse[has_seahorse["scaffold_split"] == "train"],
        "held_out (val+test+untested-on-primary - genuine orthogonal signal)": has_seahorse[is_held_out],
    }

    rows = []
    for membership_label, group_df in groups.items():
        for endpoint in SEAHORSE_ENDPOINTS:
            m = compute_group_metrics(group_df, endpoint, membership_label)
            rows.append(m)
            print(f"[{membership_label}] {endpoint}: n={m['n']}, AUROC={m['mmp_model_vs_seahorse_auroc']:.3f}, "
                  f"agreement={m['agreement_rate_at_0.5']:.3f}")

    pd.DataFrame(rows).to_csv(OUT_PATH, index=False)
    print(f"wrote {OUT_PATH}")


if __name__ == "__main__":
    main()
