"""95% CI on prospective AUROC for a blinded Aim 2 validation panel, at a
few candidate panel sizes and two assumed true AUROC values (0.75, 0.80) -
per Kolliputi's request. Also used to recommend a panel size and show the
marginal benefit of 120 vs 150 vs 200 compounds.

Method: same Hanley-McNeil (1982) nonparametric AUC variance estimator as
scripts/17_seahorse_power_analysis.py, used here for a CI around a given
AUROC rather than solving for n against a null. CI = AUROC +/- z*sqrt(Var).

Prevalence assumption: the Aim 2 panel is deliberately curated (specific
chemical classes, enriched for uncertain chemicals) and not a random draw
from the Tox21 population, so its true active/inactive split is genuinely
unknown in advance. Two scenarios are reported: (a) same prevalence as the
Tox21 training set (15.9% active, 1,158/7,268) as the most defensible
available anchor, and (b) a more balanced 30% active assumption, to show
how much the answer actually depends on this unknown.
"""
import importlib.util
import numpy as np
from scipy.stats import norm

_spec = importlib.util.spec_from_file_location("power_analysis", "scripts/17_seahorse_power_analysis.py")
power_analysis = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(power_analysis)

Z_95 = norm.ppf(0.975)
TRAINING_PREVALENCE = 1158 / 7268
BALANCED_PREVALENCE = 0.30

TRUE_AUROCS = [0.75, 0.80]
PANEL_SIZES = {
    "full panel (100% coverage)": 1.0,
    "retained at 50% coverage": 0.50,
    "retained at 80% coverage": 0.80,
}
TOTAL_N_CANDIDATES = [120, 150, 200]


def ci_for(auroc, n_total, prevalence):
    n1 = max(round(n_total * prevalence), 1)
    n0 = max(n_total - n1, 1)
    var = power_analysis.hanley_mcneil_var(auroc, n1, n0)
    se = np.sqrt(var)
    lo, hi = auroc - Z_95 * se, auroc + Z_95 * se
    return lo, hi, se, n1, n0


def main():
    print("=" * 70)
    print("95% CI on prospective AUROC, full ~120-compound panel and retained subsets")
    print("=" * 70)
    for prevalence, label in [(TRAINING_PREVALENCE, "training prevalence 15.9%"),
                              (BALANCED_PREVALENCE, "balanced-panel assumption 30%")]:
        print(f"\n--- assumed prevalence: {label} ---")
        for true_auroc in TRUE_AUROCS:
            print(f"\n  true AUROC = {true_auroc}:")
            for coverage_label, coverage_frac in PANEL_SIZES.items():
                n_total = round(120 * coverage_frac)
                lo, hi, se, n1, n0 = ci_for(true_auroc, n_total, prevalence)
                print(f"    {coverage_label} (n={n_total}, {n1} active/{n0} inactive): "
                      f"95% CI [{lo:.3f}, {hi:.3f}], half-width {Z_95*se:.3f}")

    print("\n" + "=" * 70)
    print("Panel-size sensitivity (full panel, training prevalence): 120 vs 150 vs 200")
    print("=" * 70)
    for true_auroc in TRUE_AUROCS:
        print(f"\n  true AUROC = {true_auroc}:")
        for n_total in TOTAL_N_CANDIDATES:
            lo, hi, se, n1, n0 = ci_for(true_auroc, n_total, TRAINING_PREVALENCE)
            print(f"    n={n_total} ({n1} active/{n0} inactive): "
                  f"95% CI [{lo:.3f}, {hi:.3f}], half-width {Z_95*se:.3f}")


if __name__ == "__main__":
    main()
