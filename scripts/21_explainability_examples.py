"""Explainability examples: a correctly predicted toxicant, a correctly
predicted low-liability chemical, and an uncertain/OOD case. Uses SHAP
(TreeExplainer) on the best model (scaffold Random Forest) to identify the
top contributing features per example, then renders the actual substructure
for any top ECFP4-bit feature (not just an opaque bit index) via RDKit's
Morgan-bit drawing utility.
"""
import json
import joblib
import numpy as np
import pandas as pd
import shap
from rdkit import Chem, RDLogger
from rdkit.Chem import AllChem, Draw

RDLogger.DisableLog("rdApp.*")

DATASET_PATH = "data/processed/step2_mmp_dataset.csv"
SPLITS_PATH = "data/processed/step2_splits.csv"
PREDICTIONS_PATH = "data/processed/step2_predictions.csv"
UNCERTAINTY_PATH = "data/processed/step2_uncertainty_ad.csv"
MODEL_PATH = "models/scaffold_random_forest.joblib"
OUT_DIR = "results/figures"
OUT_SUMMARY_PATH = "data/processed/step2_explainability_examples.json"

FP_COLS = [f"ecfp4_{i}" for i in range(2048)]
DESCRIPTOR_COLS = [
    "mol_weight", "logp", "tpsa", "hbd", "hba",
    "rotatable_bonds", "aromatic_rings", "heavy_atoms", "fraction_csp3",
]
FEATURE_COLS = FP_COLS + DESCRIPTOR_COLS
TOP_K = 5


def top_features_for_instance(explainer, x_row, class_idx=1):
    shap_values = explainer.shap_values(x_row.reshape(1, -1))
    # sklearn RF binary classifier: shap_values is (n_samples, n_features, n_classes) in shap>=0.45
    sv = shap_values[0, :, class_idx] if shap_values.ndim == 3 else shap_values[class_idx][0]
    order = np.argsort(-np.abs(sv))[:TOP_K]
    return [(FEATURE_COLS[i], float(sv[i]), float(x_row[i])) for i in order]


def render_bit(mol, bit_idx, out_path):
    bit_info = {}
    AllChem.GetMorganFingerprintAsBitVect(mol, radius=2, nBits=2048, bitInfo=bit_info)
    if bit_idx not in bit_info:
        return False
    img = Draw.DrawMorganBit(mol, bit_idx, bit_info, useSVG=False)
    if hasattr(img, "save"):
        img.save(out_path)
    else:
        with open(out_path, "wb") as f:
            f.write(img)
    return True


def main():
    dataset = pd.read_csv(DATASET_PATH, low_memory=False)
    splits = pd.read_csv(SPLITS_PATH, low_memory=False)
    preds = pd.read_csv(PREDICTIONS_PATH, low_memory=False)
    uncertainty = pd.read_csv(UNCERTAINTY_PATH)

    df = dataset.merge(splits, on="DTXSID", how="inner")
    test = df[df["scaffold_split"] == "test"].merge(
        preds[(preds.regime == "scaffold") & (preds.model == "random_forest") & (preds.split == "test")]
        [["DTXSID", "predicted_proba"]], on="DTXSID"
    ).merge(uncertainty[["DTXSID", "is_error", "uncertainty_std"]], on="DTXSID")

    tp = test[(test.label == 1) & (~test.is_error)].sort_values("predicted_proba", ascending=False).iloc[0]
    tn = test[(test.label == 0) & (~test.is_error)].sort_values("predicted_proba", ascending=True).iloc[0]
    uncertain = test.sort_values("uncertainty_std", ascending=False).iloc[0]

    model = joblib.load(MODEL_PATH)
    # default tree_path_dependent mode hit a numerical additivity failure with
    # this forest (500 trees, 2057 features) - interventional mode against an
    # explicit background sample is the more numerically robust path here
    train_bg = df[df["scaffold_split"] == "train"][FEATURE_COLS].sample(n=100, random_state=42).values
    explainer = shap.TreeExplainer(model, data=train_bg, feature_perturbation="interventional")

    examples = [
        ("correct_toxicant", tp, "Correctly predicted mitochondrial liability (true positive)"),
        ("correct_low_liability", tn, "Correctly predicted low liability (true negative)"),
        ("uncertain_case", uncertain, "Highest-uncertainty prediction (most disagreement across trees)"),
    ]

    summary = []
    for key, row, description in examples:
        mol = Chem.MolFromSmiles(row["canonical_smiles"])
        x_row = row[FEATURE_COLS].values.astype(float)
        top_feats = top_features_for_instance(explainer, x_row)

        rendered_bits = []
        for feat_name, shap_val, feat_val in top_feats:
            if feat_name.startswith("ecfp4_") and feat_val > 0:  # bit must be "on" to render
                bit_idx = int(feat_name.split("_")[1])
                out_path = f"{OUT_DIR}/explain_{key}_bit{bit_idx}.png"
                if render_bit(mol, bit_idx, out_path):
                    rendered_bits.append({"feature": feat_name, "bit": bit_idx, "image": out_path})

        summary.append({
            "key": key,
            "description": description,
            "DTXSID": row["DTXSID"],
            "canonical_smiles": row["canonical_smiles"],
            "label": int(row["label"]),
            "predicted_proba": float(row["predicted_proba"]),
            "uncertainty_std": float(row["uncertainty_std"]),
            "top_features": [
                {"feature": f, "shap_value": s, "feature_value": v} for f, s, v in top_feats
            ],
            "rendered_substructures": rendered_bits,
        })
        print(f"{key}: DTXSID={row['DTXSID']}, proba={row['predicted_proba']:.3f}, "
              f"label={int(row['label'])}, uncertainty={row['uncertainty_std']:.3f}")
        print(f"  top features: {[(f, round(s,3)) for f,s,v in top_feats]}")
        print(f"  rendered {len(rendered_bits)} substructure image(s)")

    with open(OUT_SUMMARY_PATH, "w") as f:
        json.dump(summary, f, indent=2)
    print(f"wrote {OUT_SUMMARY_PATH}")


if __name__ == "__main__":
    main()
