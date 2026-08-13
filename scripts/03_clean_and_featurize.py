"""Standardize structures, drop unusable/mixture/ambiguous entries, dedupe by
canonical structure, and generate Morgan/ECFP fingerprints + physicochemical
descriptors for the mitochondrial-toxicity chemical set.
"""
import pandas as pd
from rdkit import Chem, RDLogger
from rdkit.Chem import AllChem, Descriptors, rdMolDescriptors

RDLogger.DisableLog("rdApp.*")

IN_PATH = "data/processed/mito_chemicals_with_structures.csv"
OUT_CHEM_PATH = "data/processed/mito_chemicals_clean.csv"
OUT_FP_PATH = "data/processed/mito_chemicals_fingerprints.csv"
DROPPED_LOG_PATH = "data/processed/mito_chemicals_dropped.csv"

DESCRIPTOR_FUNCS = {
    "mol_weight": Descriptors.MolWt,
    "logp": Descriptors.MolLogP,
    "tpsa": Descriptors.TPSA,
    "hbd": Descriptors.NumHDonors,
    "hba": Descriptors.NumHAcceptors,
    "rotatable_bonds": Descriptors.NumRotatableBonds,
    "aromatic_rings": Descriptors.NumAromaticRings,
    "heavy_atoms": Descriptors.HeavyAtomCount,
    "fraction_csp3": Descriptors.FractionCSP3,
}


def largest_fragment(mol):
    frags = Chem.GetMolFrags(mol, asMols=True, sanitizeFrags=False)
    return max(frags, key=lambda m: m.GetNumHeavyAtoms())


def standardize(smiles):
    """Returns (canonical_smiles, mol, reason_dropped_or_None)."""
    if not isinstance(smiles, str) or not smiles.strip():
        return None, None, "empty_smiles"
    mol = Chem.MolFromSmiles(smiles)
    if mol is None:
        return None, None, "unparseable_smiles"

    n_frags = len(Chem.GetMolFrags(mol))
    if n_frags > 1:
        mol = largest_fragment(mol)
        # a multi-component structure where the largest fragment is small
        # relative to the whole (e.g. a salt/solvate/formulation mixture with
        # no single dominant organic component) is treated as unusable
        try:
            Chem.SanitizeMol(mol)
        except Exception:
            return None, None, "unsanitizable_fragment"
        if mol.GetNumHeavyAtoms() < 3:
            return None, None, "mixture_no_dominant_fragment"

    if mol.GetNumHeavyAtoms() < 3:
        return None, None, "too_small"

    # organic-only check: require at least one carbon (excludes pure
    # inorganics/metals that ECFP/physicochemical descriptors aren't meant for)
    if not any(atom.GetSymbol() == "C" for atom in mol.GetAtoms()):
        return None, None, "inorganic_no_carbon"

    try:
        Chem.SanitizeMol(mol)
        canonical = Chem.MolToSmiles(mol, canonical=True)
    except Exception:
        return None, None, "sanitize_failed"

    return canonical, mol, None


def main():
    df = pd.read_csv(IN_PATH, low_memory=False)
    print(f"input: {len(df):,} chemicals")

    records = []
    dropped = []
    for row in df.itertuples(index=False):
        smiles = row.QSAR_READY_SMILES if isinstance(row.QSAR_READY_SMILES, str) and row.QSAR_READY_SMILES.strip() else row.SMILES
        canonical, mol, reason = standardize(smiles)
        if reason:
            dropped.append({"DTXSID": row.DTXSID, "PREFERRED_NAME": row.PREFERRED_NAME, "reason": reason})
            continue
        records.append({
            "DTXSID": row.DTXSID,
            "PREFERRED_NAME": row.PREFERRED_NAME,
            "CASRN": row.CASRN,
            "canonical_smiles": canonical,
            "mol_obj": mol,
        })

    print(f"standardized ok: {len(records):,}, dropped: {len(dropped):,}")

    clean_df = pd.DataFrame(records)
    before_dedup = len(clean_df)
    clean_df = clean_df.drop_duplicates(subset="canonical_smiles", keep="first").reset_index(drop=True)
    print(f"deduped by canonical structure: {before_dedup:,} -> {len(clean_df):,}")

    fp_rows = []
    desc_rows = []
    for row in clean_df.itertuples(index=False):
        mol = row.mol_obj
        fp = AllChem.GetMorganFingerprintAsBitVect(mol, radius=2, nBits=2048)
        fp_rows.append({"DTXSID": row.DTXSID, **{f"ecfp4_{i}": int(b) for i, b in enumerate(fp)}})
        desc = {name: func(mol) for name, func in DESCRIPTOR_FUNCS.items()}
        desc_rows.append({"DTXSID": row.DTXSID, **desc})

    fp_df = pd.DataFrame(fp_rows)
    desc_df = pd.DataFrame(desc_rows)

    clean_out = clean_df.drop(columns=["mol_obj"]).merge(desc_df, on="DTXSID")
    clean_out.to_csv(OUT_CHEM_PATH, index=False)
    fp_df.to_csv(OUT_FP_PATH, index=False)
    pd.DataFrame(dropped).to_csv(DROPPED_LOG_PATH, index=False)

    print(f"wrote {len(clean_out):,} clean chemicals -> {OUT_CHEM_PATH}")
    print(f"wrote {len(fp_df):,} fingerprints (2048-bit ECFP4) -> {OUT_FP_PATH}")
    print(f"wrote {len(dropped):,} dropped-chemical log -> {DROPPED_LOG_PATH}")
    print("\ndrop reasons:")
    print(pd.DataFrame(dropped)["reason"].value_counts() if dropped else "none")


if __name__ == "__main__":
    main()
