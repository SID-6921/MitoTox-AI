# External validation dataset search

Per Kolliputi: "look for a genuinely independent mitochondrial-toxicity dataset for
external validation... do not force an external-validation claim if an appropriate
independent dataset is unavailable." This is that search, done honestly.

## Outcome: obtained and applied as an exploratory analysis, not a validation claim

Per Kolliputi (2026-08-13): report this transparently, but don't present it as definitive
external validation given the extreme class imbalance after overlap removal - call it
exploratory, and reserve rigorous external validation for Phase I.

**Source:** Garcia de Lomana, Marin Zapata & Montanari, "Predicting the Mitochondrial
Toxicity of Small Molecules: Insights from Mechanistic Assays and Cell Painting Data,"
*Chem. Res. Toxicol.* 2023, 36(7), 1107-1120,
[DOI: 10.1021/acs.chemrestox.3c00086](https://doi.org/10.1021/acs.chemrestox.3c00086)
(PMC10354797, open access). Supplementary file `tx3c00086_si_002.xlsx`
(`mitotox_dataset` sheet, 6,814 compounds), obtained after working around NCBI PMC's
"cloudpmc-viewer" bot-detection layer (a client-side proof-of-work JS challenge that
blocks plain `curl`/direct navigation but resolves via a real browser session).

**What's genuinely independent inside it, and what isn't:** the sheet blends multiple
source databases per compound per mechanism (`sources_membrane_potential`,
`sources_respiratory_chain`, etc.). For the membrane-potential mechanism specifically:
4,936 compounds are tagged `['tox21']` only (the same assay family as our training data
- not independent), 402 are tagged both `tox21` and `mitotox_membrane_potential`
(mixed provenance - not usable as independent), and **147 are tagged
`['mitotox_membrane_potential']` only** - literature-curated, no Tox21 contribution.
That 147-compound subset (146 after dropping one unlabeled row) is what was used - see
`scripts/15_external_validation.py`.

**Result:** applying the locked `models/scaffold_random_forest.joblib` without
retraining. First, canonicalized all 146 SMILES and checked for overlap against our own
8,058-chemical clean set: **120 of 146 (82%) turned out to already be in our own data**
- likely because these are common, frequently-cited reference mitochondrial toxicants
that show up across many curated databases, including ToxCast. Excluding that overlap
(not a fair test on chemicals the model has already seen) leaves only **26 genuinely
unseen chemicals**, and the label balance among them is 25 active / 1 inactive - the
literature-curation positive bias described in the paper itself, extreme enough here to
make AUROC/balanced-accuracy on this remainder statistically unreliable (one negative
example provides almost no resolution). Numeric result (AUROC 0.720, balanced accuracy
0.680, n=26) is recorded in `data/processed/step2_external_validation.csv` for the
record, but **no confident external-validation claim is drawn from it** - the honest
read is that this attempt is underpowered, not that it succeeded or failed.

**Other candidates considered, and why not used:**
- MitoTox database (mitotox.org, PMC8283953) - explicitly ingests Tox21 AID720637 (the
  same Tox21 MMP assay family our training data comes from) alongside other sources; not
  independent as a whole without a source-by-source filter we don't currently have.
- XML-CIMT (PMC9779353) - positive labels pulled directly from PubChem AID 720635/720637,
  the same Tox21 MMP assays. Disqualified.
- Hallinger et al. 2020 (*Toxicol. Sci.* 176(1):175) - different assay (Seahorse), but run
  on the same ToxCast chemical library, so chemical-space overlap with our training set
  is severe.
- Montague et al. 2014 (*J. Biomol. Screen.* 19(3):387) - genuinely independent screen,
  but only 14 hits are reported in enough detail to use; no usable public dataset for the
  full inactive set.

## Next step

The 82% overlap finding is itself useful: it suggests future "independent" validation
sourcing should check structure-level overlap against training data explicitly (as done
here) rather than assume a differently-named source is actually a disjoint chemical
set. Rigorous external validation - a larger, better-balanced, structure-checked
independent set, or a prospective panel - is scoped for Phase I, not this preliminary
package; 26 chemicals with 1 negative was never going to be that.
