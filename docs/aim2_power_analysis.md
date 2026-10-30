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

## 4. Follow-up: prevalence sensitivity and discordance power at n=150
(response to Kolliputi, 2026-10-29, after the panel size was set to 150)

Every number below is reported two ways: analytic (Hanley-McNeil variance, the same
method as sections 1-3 above) and simulation-based (20,000-run Monte Carlo per scenario,
binormal model, fixed seed 42). The two methods are independent checks on each other, not
a single pipeline re-run twice.

### 4a. Prospective AUROC 95% CI at n=150, 25% and 30% active prevalence

| Prevalence | True AUROC | Subset | n (active/inactive) | Analytic 95% CI | Simulated 95% CI |
|---|---|---|---|---|---|
| 25% | 0.75 | Full panel (100% coverage) | 150 (38/112) | [0.653, 0.847] | [0.659, 0.836] |
| 25% | 0.75 | Retained, 50% coverage | 75 (19/56) | [0.612, 0.888] | [0.617, 0.870] |
| 25% | 0.75 | Retained, 80% coverage | 120 (30/90) | [0.641, 0.859] | [0.646, 0.845] |
| 25% | 0.8 | Full panel (100% coverage) | 150 (38/112) | [0.710, 0.890] | [0.716, 0.877] |
| 25% | 0.8 | Retained, 50% coverage | 75 (19/56) | [0.672, 0.928] | [0.680, 0.906] |
| 25% | 0.8 | Retained, 80% coverage | 120 (30/90) | [0.698, 0.902] | [0.706, 0.884] |
| 30% | 0.75 | Full panel (100% coverage) | 150 (45/105) | [0.659, 0.841] | [0.663, 0.832] |
| 30% | 0.75 | Retained, 50% coverage | 75 (22/53) | [0.620, 0.880] | [0.624, 0.864] |
| 30% | 0.75 | Retained, 80% coverage | 120 (36/84) | [0.648, 0.852] | [0.651, 0.840] |
| 30% | 0.8 | Full panel (100% coverage) | 150 (45/105) | [0.716, 0.884] | [0.720, 0.873] |
| 30% | 0.8 | Retained, 50% coverage | 75 (22/53) | [0.679, 0.921] | [0.685, 0.901] |
| 30% | 0.8 | Retained, 80% coverage | 120 (36/84) | [0.706, 0.894] | [0.710, 0.881] |

The analytic interval is consistently a little wider than the simulated one across every
row here too, consistent with section 1's validation - Hanley-McNeil is a safe
(conservative) choice for a document that will be cited.

### 4b. Discordance power at n=150: smallest detectable true AUC

| Endpoint | n (active/inactive) | Smallest detectable AUC (80% power) | Analytic power there | Simulated power there |
|---|---|---|---|---|
| Balanced respiration endpoints (basal/max, 64:36 ratio) | 96/54 | 0.635 | 0.800 | 0.797 |
| Imbalanced inhibited-respiration endpoint (14:86 ratio) | 21/129 | 0.691 | 0.800 | 0.826 |

**What Aim 2 can and cannot resolve, stated exactly (for the Approach section):** at
n=150, the discordance analysis can detect a true AUC as small as 0.64 on the
better-balanced respiration endpoints, and 0.69 on the more imbalanced
inhibited-respiration endpoint, each at 80% power. A true discordance effect weaker than
that (closer to the chance level of 0.5) will not reliably separate from noise at this
panel size - a non-significant result would be consistent with either a genuinely small
effect or an underpowered test, and Aim 2 cannot distinguish those two on its own.
