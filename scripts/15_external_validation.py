"""Apply the locked primary model (scaffold_random_forest, no retraining) to a
genuinely independent external mitochondrial membrane-potential dataset.

Source: Garcia de Lomana, Marin Zapata & Montanari, Chem. Res. Toxicol. 2023,
36(7), 1107-1120 (DOI 10.1021/acs.chemrestox.3c00086), supplementary
`mitotox_dataset` sheet. That sheet blends several source databases per
compound (see `sources_membrane_potential` column); most rows are tagged
'tox21' (i.e. the same assay family our training data comes from) and are NOT
independent. Only the 147 compounds tagged *exclusively*
`['mitotox_membrane_potential']` (literature-curated, no Tox21 contribution)
are used here - see docs/external_validation_search.md for the full source
breakdown and why the other subsets were excluded.
"""
import joblib
import numpy as np
import pandas as pd
from rdkit import Chem, RDLogger
from rdkit.Chem import AllChem
from sklearn.metrics import roc_auc_score, confusion_matrix, balanced_accuracy_score

RDLogger.DisableLog("rdApp.*")

EXTERNAL_XLSX = "data/raw/external_validation/tx3c00086_si_002.xlsx"
CLEAN_CHEM_PATH = "data/processed/mito_chemicals_clean.csv"
MODEL_PATH = "models/scaffold_random_forest.joblib"
OUT_PATH = "data/processed/step2_external_validation.csv"

DESCRIPTOR_COLS = [
    "mol_weight", "logp", "tpsa", "hbd", "hba",
    "rotatable_bonds", "aromatic_rings", "heavy_atoms", "fraction_csp3",
]
THRESHOLD = 0.5


def canonicalize(smiles):
    mol = Chem.MolFromSmiles(smiles)
    if mol is None:
        return None, None
    return Chem.MolToSmiles(mol, canonical=True), mol


def featurize(mol):
    from rdkit.Chem import Descriptors
    fp = AllChem.GetMorganFingerprintAsBitVect(mol, radius=2, nBits=2048)
    fp_arr = np.array(fp, dtype=float)
    desc = np.array([
        Descriptors.MolWt(mol), Descriptors.MolLogP(mol), Descriptors.TPSA(mol),
        Descriptors.NumHDonors(mol), Descriptors.NumHAcceptors(mol),
        Descriptors.NumRotatableBonds(mol), Descriptors.NumAromaticRings(mol),
        Descriptors.HeavyAtomCount(mol), Descriptors.FractionCSP3(mol),
    ], dtype=float)
    return np.concatenate([fp_arr, desc])


def main():
    ext = pd.read_excel(EXTERNAL_XLSX, sheet_name="mitotox_dataset",
                         usecols=["canonical_smiles", "MTX_membrane_potential", "sources_membrane_potential"])
    independent = ext[ext["sources_membrane_potential"].astype(str) == "['mitotox_membrane_potential']"].copy()
    independent = independent.dropna(subset=["MTX_membrane_potential"])
    print(f"genuinely independent (literature-only) membrane-potential compounds: {len(independent):,}")
    print(f"label balance: {independent['MTX_membrane_potential'].value_counts().to_dict()} "
          "(heavily positive-skewed - literature curation bias, a real limitation of this set)")

    canon_own, mols_own = zip(*[canonicalize(s) for s in independent["canonical_smiles"]])
    independent["_canonical"] = canon_own
    independent["_mol"] = mols_own
    independent = independent[independent["_canonical"].notna()]

    own_clean = set(pd.read_csv(CLEAN_CHEM_PATH, low_memory=False)["canonical_smiles"])
    overlap = independent["_canonical"].isin(own_clean)
    print(f"overlap with our own training/val/test chemicals: {overlap.sum()} "
          f"(excluded - not a fair external test for those)")
    independent = independent[~overlap]
    print(f"remaining genuinely unseen chemicals: {len(independent):,}")

    X = np.stack([featurize(m) for m in independent["_mol"]])
    model = joblib.load(MODEL_PATH)
    y_prob = model.predict_proba(X)[:, 1]
    y_true = independent["MTX_membrane_potential"].values.astype(int)
    y_pred = (y_prob >= THRESHOLD).astype(int)

    auroc = roc_auc_score(y_true, y_prob) if len(set(y_true)) > 1 else float("nan")
    bacc = balanced_accuracy_score(y_true, y_pred)
    tn, fp, fn, tp = confusion_matrix(y_true, y_pred, labels=[0, 1]).ravel()
    agreement = (y_pred == y_true).mean()

    print(f"external validation (no retraining): n={len(independent)}, AUROC={auroc:.3f}, "
          f"balanced_acc={bacc:.3f}, agreement={agreement:.3f}, "
          f"confusion(tn,fp,fn,tp)=({tn},{fp},{fn},{tp})")

    pd.DataFrame([{
        "n": len(independent), "n_active": int(y_true.sum()), "auroc": auroc,
        "balanced_accuracy": bacc, "agreement_rate": agreement,
        "tn": tn, "fp": fp, "fn": fn, "tp": tp,
    }]).to_csv(OUT_PATH, index=False)
    print(f"wrote {OUT_PATH}")


if __name__ == "__main__":
    main()
