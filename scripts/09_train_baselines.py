"""Train logistic regression, Random Forest, and XGBoost baselines for the
primary endpoint (TOX21_MMP_ratio), once under the scaffold-separated split
(the primary evaluation regime) and once under the random split (comparison
only per Kolliputi). Hyperparameters are picked with a small fixed grid,
selected by val-set AUROC only - the locked test set is never touched here.
"""
import json
import joblib
import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import roc_auc_score
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import Pipeline
from xgboost import XGBClassifier

SEED = 42
DATASET_PATH = "data/processed/step2_mmp_dataset.csv"
SPLITS_PATH = "data/processed/step2_splits.csv"
MODELS_DIR = "models"
PREDICTIONS_PATH = "data/processed/step2_predictions.csv"

FP_COLS = [f"ecfp4_{i}" for i in range(2048)]
DESCRIPTOR_COLS = [
    "mol_weight", "logp", "tpsa", "hbd", "hba",
    "rotatable_bonds", "aromatic_rings", "heavy_atoms", "fraction_csp3",
]
FEATURE_COLS = FP_COLS + DESCRIPTOR_COLS

LR_GRID = [{"C": c} for c in (0.01, 0.1, 1.0, 10.0)]
RF_GRID = [{"max_depth": d} for d in (None, 10, 20)]
XGB_GRID = [{"max_depth": d} for d in (3, 6, 9)]


def make_lr(params):
    return Pipeline([
        ("scale", StandardScaler()),
        ("clf", LogisticRegression(
            C=params["C"], class_weight="balanced", max_iter=2000, random_state=SEED
        )),
    ])


def make_rf(params):
    return RandomForestClassifier(
        n_estimators=500, max_depth=params["max_depth"],
        class_weight="balanced", random_state=SEED, n_jobs=-1,
    )


def make_xgb(params, scale_pos_weight):
    return XGBClassifier(
        n_estimators=300, max_depth=params["max_depth"], learning_rate=0.1,
        scale_pos_weight=scale_pos_weight, random_state=SEED,
        eval_metric="logloss", n_jobs=-1,
    )


MODEL_SPECS = {
    "logistic_regression": (make_lr, LR_GRID),
    "random_forest": (make_rf, RF_GRID),
    "xgboost": (make_xgb, XGB_GRID),
}


def fit_and_select(model_name, factory, grid, X_train, y_train, X_val, y_val):
    best_model, best_auroc, best_params = None, -1, None
    for params in grid:
        if model_name == "xgboost":
            spw = (y_train == 0).sum() / max((y_train == 1).sum(), 1)
            model = factory(params, spw)
        else:
            model = factory(params)
        model.fit(X_train, y_train)
        val_pred = model.predict_proba(X_val)[:, 1]
        auroc = roc_auc_score(y_val, val_pred)
        if auroc > best_auroc:
            best_model, best_auroc, best_params = model, auroc, params
    return best_model, best_params, best_auroc


def main():
    df = pd.read_csv(DATASET_PATH, low_memory=False)
    splits = pd.read_csv(SPLITS_PATH, low_memory=False)
    df = df.merge(splits, on="DTXSID", how="inner")
    assert len(df) == len(splits), "split file and dataset chemical sets must match exactly"

    all_predictions = []
    selection_log = []

    for regime in ["scaffold", "random"]:
        split_col = f"{regime}_split"
        train = df[df[split_col] == "train"]
        val = df[df[split_col] == "val"]
        test = df[df[split_col] == "test"]

        X_train, y_train = train[FEATURE_COLS].values, train["label"].values
        X_val, y_val = val[FEATURE_COLS].values, val["label"].values
        X_test = test[FEATURE_COLS].values

        for model_name, (factory, grid) in MODEL_SPECS.items():
            model, params, val_auroc = fit_and_select(
                model_name, factory, grid, X_train, y_train, X_val, y_val
            )
            print(f"[{regime}] {model_name}: best params={params}, val AUROC={val_auroc:.3f}")
            selection_log.append({
                "regime": regime, "model": model_name, "params": json.dumps(params),
                "val_auroc": val_auroc, "seed": SEED,
            })

            model_path = f"{MODELS_DIR}/{regime}_{model_name}.joblib"
            joblib.dump(model, model_path)

            for split_name, X_split, split_df in [("train", X_train, train), ("val", X_val, val), ("test", X_test, test)]:
                proba = model.predict_proba(X_split)[:, 1]
                all_predictions.append(pd.DataFrame({
                    "DTXSID": split_df["DTXSID"].values,
                    "regime": regime,
                    "model": model_name,
                    "split": split_name,
                    "label": split_df["label"].values,
                    "predicted_proba": proba,
                }))

    pd.DataFrame(selection_log).to_csv(f"{MODELS_DIR}/step2_model_selection_log.csv", index=False)
    pd.concat(all_predictions, ignore_index=True).to_csv(PREDICTIONS_PATH, index=False)
    print(f"wrote {MODELS_DIR}/step2_model_selection_log.csv and {PREDICTIONS_PATH}")


if __name__ == "__main__":
    main()
