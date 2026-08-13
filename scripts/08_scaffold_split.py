"""Bemis-Murcko scaffold-separated train/val/locked-test split (the primary
evaluation partition per Kolliputi) plus a stratified random split of the
same proportions for comparison-only reporting.

Standard greedy scaffold-split algorithm (as in DeepChem's ScaffoldSplitter):
group chemicals by Murcko scaffold, then assign whole scaffold groups (never
split a scaffold across sets) to train/val/test in descending group-size
order, so val/test end up enriched for smaller/singleton scaffolds - i.e.
structurally novel chemicals relative to train, which is the point of a
scaffold split. Groups of equal size are shuffled with a fixed seed before
assignment so the ordering isn't an arbitrary artifact of input row order.
"""
import pandas as pd
from rdkit import Chem, RDLogger
from rdkit.Chem.Scaffolds import MurckoScaffold
from sklearn.model_selection import train_test_split

RDLogger.DisableLog("rdApp.*")

DATASET_PATH = "data/processed/step2_mmp_dataset.csv"
OUT_PATH = "data/processed/step2_splits.csv"

SEED = 42
TRAIN_FRAC, VAL_FRAC, TEST_FRAC = 0.70, 0.15, 0.15


def murcko_scaffold(smiles):
    mol = Chem.MolFromSmiles(smiles)
    if mol is None:
        return ""
    scaffold = MurckoScaffold.GetScaffoldForMol(mol)
    return Chem.MolToSmiles(scaffold) if scaffold is not None else ""


def scaffold_split(df, seed=SEED):
    scaffolds = {}
    for idx, smiles in zip(df.index, df["canonical_smiles"]):
        scaffolds.setdefault(murcko_scaffold(smiles), []).append(idx)

    groups = list(scaffolds.values())
    rng = __import__("random").Random(seed)
    # shuffle within each size bucket so equal-size groups aren't ordered by
    # incidental row order, then sort by size descending
    rng.shuffle(groups)
    groups.sort(key=len, reverse=True)

    n = len(df)
    n_train, n_val = int(n * TRAIN_FRAC), int(n * VAL_FRAC)

    train_idx, val_idx, test_idx = [], [], []
    for g in groups:
        if len(train_idx) + len(g) <= n_train:
            train_idx.extend(g)
        elif len(val_idx) + len(g) <= n_val:
            val_idx.extend(g)
        else:
            test_idx.extend(g)

    return train_idx, val_idx, test_idx


def main():
    df = pd.read_csv(DATASET_PATH, low_memory=False)

    train_idx, val_idx, test_idx = scaffold_split(df)
    scaffold_col = pd.Series("train", index=df.index)
    scaffold_col.loc[val_idx] = "val"
    scaffold_col.loc[test_idx] = "test"

    # scaffold overlap check: assert no scaffold appears in more than one split
    df["_scaffold"] = df["canonical_smiles"].apply(murcko_scaffold)
    scaffold_sets = df.groupby(scaffold_col)["_scaffold"].apply(set)
    overlap_tv = scaffold_sets["train"] & scaffold_sets["val"]
    overlap_tt = scaffold_sets["train"] & scaffold_sets["test"]
    overlap_vt = scaffold_sets["val"] & scaffold_sets["test"]
    assert not overlap_tv and not overlap_tt and not overlap_vt, "scaffold leaked across splits"
    df = df.drop(columns=["_scaffold"])

    print(f"scaffold split: train={sum(scaffold_col=='train'):,} "
          f"val={sum(scaffold_col=='val'):,} test={sum(scaffold_col=='test'):,}")
    print(f"scaffold split label balance (train/val/test active %): "
          f"{df.loc[scaffold_col=='train','label'].mean():.3f} / "
          f"{df.loc[scaffold_col=='val','label'].mean():.3f} / "
          f"{df.loc[scaffold_col=='test','label'].mean():.3f}")

    # random split, comparison only - stratified by label, same proportions
    train_r, rest_r = train_test_split(
        df.index, test_size=(VAL_FRAC + TEST_FRAC), random_state=SEED, stratify=df["label"]
    )
    val_r, test_r = train_test_split(
        rest_r, test_size=TEST_FRAC / (VAL_FRAC + TEST_FRAC), random_state=SEED,
        stratify=df.loc[rest_r, "label"],
    )
    random_col = pd.Series("train", index=df.index)
    random_col.loc[val_r] = "val"
    random_col.loc[test_r] = "test"

    print(f"random split: train={sum(random_col=='train'):,} "
          f"val={sum(random_col=='val'):,} test={sum(random_col=='test'):,}")

    out = pd.DataFrame({
        "DTXSID": df["DTXSID"],
        "scaffold_split": scaffold_col,
        "random_split": random_col,
    })
    out.to_csv(OUT_PATH, index=False)
    print(f"wrote {OUT_PATH}")


if __name__ == "__main__":
    main()
