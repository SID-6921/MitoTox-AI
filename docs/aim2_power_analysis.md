# Aim 2 power analysis and panel design (response to Kolliputi, 2026-10-29)

## 1. Prospective AUROC confidence intervals

Method: Hanley-McNeil (1982) nonparametric AUC variance, same estimator as the Seahorse
power analysis (`docs/step2_verification.md`). Validated here against a 20,000-run Monte
Carlo simulation (binormal model, true AUROC 0.75, n=19 active/101 inactive): simulated
95% interval [0.626, 0.860] vs. the analytic Hanley-McNeil interval [0.617, 0.883] below -
the analytic interval is about 12% wider, the expected and safer direction for a
nonparametric estimator (it does not understate uncertainty).

**The panel's true active/inactive split is not known in advance** - Aim 2 is a curated,
enriched panel, not a random draw from the Tox21 population used for training. Two
scenarios are reported: the Tox21 training-set prevalence (15.9% active, the most
defensible available anchor) and a more balanced 30% assumption, to show how much the
answer depends on this unknown.

### Training prevalence (15.9% active)

| True AUROC | Subset | n (active/inactive) | 95% CI | Half-width |
|---|---|---|---|---|
| 0.75 | full panel (100% coverage) | 120 (19/101) | [0.617, 0.883] | 0.133 |
| 0.75 | retained at 50% coverage | 60 (10/50) | [0.565, 0.935] | 0.185 |
| 0.75 | retained at 80% coverage | 96 (15/81) | [0.600, 0.900] | 0.150 |
| 0.8 | full panel (100% coverage) | 120 (19/101) | [0.675, 0.925] | 0.125 |
| 0.8 | retained at 50% coverage | 60 (10/50) | [0.627, 0.973] | 0.173 |
| 0.8 | retained at 80% coverage | 96 (15/81) | [0.660, 0.940] | 0.140 |

### Balanced-panel assumption (30% active)

| True AUROC | Subset | n (active/inactive) | 95% CI | Half-width |
|---|---|---|---|---|
| 0.75 | full panel (100% coverage) | 120 (36/84) | [0.648, 0.852] | 0.102 |
| 0.75 | retained at 50% coverage | 60 (18/42) | [0.605, 0.895] | 0.145 |
| 0.75 | retained at 80% coverage | 96 (29/67) | [0.636, 0.864] | 0.114 |
| 0.8 | full panel (100% coverage) | 120 (36/84) | [0.706, 0.894] | 0.094 |
| 0.8 | retained at 50% coverage | 60 (18/42) | [0.666, 0.934] | 0.134 |
| 0.8 | retained at 80% coverage | 96 (29/67) | [0.695, 0.905] | 0.105 |

**Reading this honestly:** at n=120 with training-set prevalence, a true AUROC of 0.75
could plausibly produce an observed value anywhere from about 0.62 to 0.88 by chance
alone. That is a wide interval relative to the 0.05 gap between the two milestone values
(0.75 vs 0.80) - a single ~120-compound panel will not cleanly distinguish "met 0.75"
from "met 0.80" on its own; it mainly distinguishes "clearly above chance" from "clearly
not." The balanced-prevalence scenario is meaningfully tighter, which is a real argument
for designing the panel toward better balance rather than assuming it will resemble
Tox21's natural ~16% active rate.

## 2. Panel-size sensitivity: is 150 clearly better than 120?

| n | True AUROC | 95% CI | Half-width |
|---|---|---|---|
| 120 | 0.75 | [0.617, 0.883] | 0.133 |
| 150 | 0.75 | [0.631, 0.869] | 0.119 |
| 200 | 0.75 | [0.647, 0.853] | 0.103 |
| 120 | 0.8 | [0.675, 0.925] | 0.125 |
| 150 | 0.8 | [0.689, 0.911] | 0.111 |
| 200 | 0.8 | [0.704, 0.896] | 0.096 |

Going from 120 to 150 compounds (+30, +25%) narrows the AUROC CI half-width by about 11%. That is real but not dramatic for the primary AUROC milestone alone.
The stronger argument for 150 is the Seahorse discordance sub-question (below) - 120 is
only just adequate there under the most optimistic assumption.

## 3. Recommended panel composition

The three selection criteria are not disjoint head counts that sum to the panel size -
a single compound can satisfy more than one at once. Recommendation:

- **Outside training scaffolds: effectively the entire panel.** This is not a separate
  budget line - it is a hard inclusion criterion for every compound, since testing on
  genuinely novel chemistry is the point of Aim 2.
- **Paired MMP + Seahorse/respirometry data: as much of the panel as feasible, ideally
  all of it.** The Seahorse discordance milestone needs its own power. From the earlier
  analysis (`docs/step2_verification.md`): detecting a modest true discordance effect
  (AUC 0.60-0.65) needs roughly 121-278 paired compounds on the better-balanced respiration
  endpoints, and 247-554 on the more imbalanced one. At 120 total, that only clears the
  single most optimistic case (AUC=0.65, best-balanced endpoint) - there is no margin.
  At 150, there is some margin for that same case but still not for AUC=0.60 or the
  imbalanced endpoint.
- **Flagged uncertain by the locked model: roughly 25-30% of the panel (about 30-45 of
  150).** Large enough to power a retained-vs-referred accuracy comparison at a referral
  rate consistent with what was tested in Step 2 (the 20-30% referral range), and matches
  the original design intent of enriching for uncertain chemicals.

**Recommendation: 150 compounds if the budget allows it.** 120 is workable for the
primary AUROC milestone's confidence interval, but it leaves no margin for the Seahorse
discordance milestone - a single unlucky draw could leave that analysis underpowered even
if the true effect is real. 150 (+30 compounds, +25% over the current budget) narrows the
AUROC CI by about 11%, and meaningfully improves - without fully solving -
the discordance analysis's power. If 150 is not affordable, 120 should proceed with the
AUROC CI width above stated explicitly as a limitation, not left as an implicit assumption.
