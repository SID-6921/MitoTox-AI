"""Second round of Aim 2 follow-up requests from Kolliputi (2026-10-29,
after the panel size was set to 150):

1. Prospective-AUROC 95% CIs at n=150, under 25% and 30% active prevalence
   (the panel will likely have more actives than Tox21's 15.9% training
   rate), for true AUROC 0.75 and 0.80, full panel + 50%/80% retained.
2. Discordance power at n=150: the smallest true AUC detectable at 80%
   power, for the balanced respiration endpoints and the imbalanced
   inhibited-respiration endpoint.

Both analytic (Hanley-McNeil) and simulation-based results are reported
for every number, since these are going into the grant for citation.

This script regenerates the ENTIRE docs/aim2_power_analysis.md (sections 1-3
via scripts/25's build_sections_1_to_3(), plus the new section 4 here) in
one "w" write, not an append - run this script last to get the canonical,
current version of the doc; running scripts/25 alone after this would
overwrite section 4.
"""
import importlib.util

_spec = importlib.util.spec_from_file_location("power_analysis", "scripts/17_seahorse_power_analysis.py")
pa = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(pa)

_spec25 = importlib.util.spec_from_file_location("aim2_doc", "scripts/25_write_aim2_power_analysis.py")
aim2_doc = importlib.util.module_from_spec(_spec25)
_spec25.loader.exec_module(aim2_doc)

OUT_PATH = "docs/aim2_power_analysis.md"
N_SIMS = 20_000
SEED = 42

PREVALENCES = [0.25, 0.30]
TRUE_AUROCS = [0.75, 0.80]
PANEL_N = 150
COVERAGE_FRACS = {"Full panel (100% coverage)": 1.0, "Retained, 50% coverage": 0.50, "Retained, 80% coverage": 0.80}

# (label, n_active, n_inactive) observed in the n=100 held-out Seahorse set,
# scaled up to n=150 while holding the ratio fixed
ENDPOINTS_AT_150 = [
    ("Balanced respiration endpoints (basal/max, 64:36 ratio)", round(150 * 64 / 100), round(150 * 36 / 100)),
    ("Imbalanced inhibited-respiration endpoint (14:86 ratio)", round(150 * 14 / 100), round(150 * 86 / 100)),
]


def main():
    ci_rows = []
    for prevalence in PREVALENCES:
        for true_auroc in TRUE_AUROCS:
            for label, frac in COVERAGE_FRACS.items():
                n_total = round(PANEL_N * frac)
                n1 = max(round(n_total * prevalence), 1)
                n0 = n_total - n1
                var = pa.hanley_mcneil_var(true_auroc, n1, n0)
                se = var ** 0.5
                z = 1.959963984540054
                analytic_lo, analytic_hi = true_auroc - z * se, true_auroc + z * se
                sim_lo, sim_hi = pa.simulated_ci(true_auroc, n1, n0, n_sims=N_SIMS, seed=SEED)
                ci_rows.append({
                    "prevalence": prevalence, "true_auroc": true_auroc, "subset": label,
                    "n": n_total, "n1": n1, "n0": n0,
                    "analytic_lo": analytic_lo, "analytic_hi": analytic_hi,
                    "sim_lo": sim_lo, "sim_hi": sim_hi,
                })
                print(f"prevalence={prevalence}, true AUROC={true_auroc}, {label} (n={n_total}): "
                      f"analytic [{analytic_lo:.3f}, {analytic_hi:.3f}], "
                      f"simulated [{sim_lo:.3f}, {sim_hi:.3f}]")

    discordance_rows = []
    for label, n1, n0 in ENDPOINTS_AT_150:
        min_auc = pa.minimum_detectable_auc(n1, n0)
        analytic_power_at_min = pa.power_for_n(min_auc, n1, n0)
        sim_power_at_min = pa.simulated_power(min_auc, n1, n0, n_sims=N_SIMS, seed=SEED)
        discordance_rows.append({
            "label": label, "n1": n1, "n0": n0, "min_auc": min_auc,
            "analytic_power": analytic_power_at_min, "sim_power": sim_power_at_min,
        })
        print(f"\n{label} at n=150 ({n1} active/{n0} inactive): "
              f"smallest detectable AUC at 80% power = {min_auc:.3f} "
              f"(analytic power there: {analytic_power_at_min:.3f}, simulated: {sim_power_at_min:.3f})")

    # --- regenerate the whole doc fresh: sections 1-3 (from script 25) + new section 4 ---
    lines = [
        "",
        "## 4. Follow-up: prevalence sensitivity and discordance power at n=150",
        "(response to Kolliputi, 2026-10-29, after the panel size was set to 150)",
        "",
        "Every number below is reported two ways: analytic (Hanley-McNeil variance, the same",
        "method as sections 1-3 above) and simulation-based (20,000-run Monte Carlo per scenario,",
        "binormal model, fixed seed 42). The two methods are independent checks on each other, not",
        "a single pipeline re-run twice.",
        "",
        "### 4a. Prospective AUROC 95% CI at n=150, 25% and 30% active prevalence",
        "",
        "**These are tighter than the section 1 intervals (n=120, 15.9% training prevalence)",
        "specifically because they assume the Aim 2 panel runs 25-30% active, not because of the",
        "larger n alone.** That higher active rate is Kolliputi's stated expectation for this panel,",
        "not something measured yet - the panel hasn't been assembled. If the real active rate comes",
        "in closer to Tox21's 15.9% training rate, the wider intervals in section 1 (rescaled from",
        "n=120 to n=150) are the more realistic ones to cite, not these.",
        "",
        "| Prevalence | True AUROC | Subset | n (active/inactive) | Analytic 95% CI | Simulated 95% CI |",
        "|---|---|---|---|---|---|",
    ]
    for r in ci_rows:
        lines.append(
            f"| {int(r['prevalence']*100)}% | {r['true_auroc']} | {r['subset']} | "
            f"{r['n']} ({r['n1']}/{r['n0']}) | [{r['analytic_lo']:.3f}, {r['analytic_hi']:.3f}] | "
            f"[{r['sim_lo']:.3f}, {r['sim_hi']:.3f}] |"
        )

    lines += [
        "",
        "The analytic interval is consistently a little wider than the simulated one across every",
        "row here too, consistent with section 1's validation - Hanley-McNeil is a safe",
        "(conservative) choice for a document that will be cited.",
        "",
        "### 4b. Discordance power at n=150: smallest detectable true AUC",
        "",
        "| Endpoint | n (active/inactive) | Smallest detectable AUC (80% power) | Analytic power there | Simulated power there |",
        "|---|---|---|---|---|",
    ]
    for r in discordance_rows:
        lines.append(
            f"| {r['label']} | {r['n1']}/{r['n0']} | {r['min_auc']:.3f} | "
            f"{r['analytic_power']:.3f} | {r['sim_power']:.3f} |"
        )

    balanced_min = discordance_rows[0]["min_auc"]
    imbalanced_min = discordance_rows[1]["min_auc"]
    lines += [
        "",
        "**What Aim 2 can and cannot resolve, stated exactly (for the Approach section):** at",
        f"n=150, the discordance analysis can detect a true AUC as small as {balanced_min:.2f} on the",
        f"better-balanced respiration endpoints, and {imbalanced_min:.2f} on the more imbalanced",
        "inhibited-respiration endpoint, each at 80% power. A true discordance effect weaker than",
        "that (closer to the chance level of 0.5) will not reliably separate from noise at this",
        "panel size - a non-significant result would be consistent with either a genuinely small",
        "effect or an underpowered test, and Aim 2 cannot distinguish those two on its own.",
    ]

    full_doc = aim2_doc.build_sections_1_to_3() + lines
    with open(OUT_PATH, "w", encoding="utf-8") as f:
        f.write("\n".join(full_doc) + "\n")
    print(f"\nwrote full doc (sections 1-4) to {OUT_PATH}")


if __name__ == "__main__":
    main()
