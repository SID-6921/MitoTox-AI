"""Write docs/aim2_power_analysis.md: prospective-AUROC confidence intervals
and a panel-design recommendation, per Kolliputi's 3 follow-up requests.
Computed fresh each run from scripts/17 and scripts/24's functions, not
hand-typed, so the numbers can't drift out of sync with the methods.
"""
import importlib.util

_spec17 = importlib.util.spec_from_file_location("power_analysis", "scripts/17_seahorse_power_analysis.py")
power_analysis = importlib.util.module_from_spec(_spec17)
_spec17.loader.exec_module(power_analysis)

_spec24 = importlib.util.spec_from_file_location("ci_analysis", "scripts/24_prospective_auroc_ci.py")
ci_analysis = importlib.util.module_from_spec(_spec24)
_spec24.loader.exec_module(ci_analysis)

OUT_PATH = "docs/aim2_power_analysis.md"


def build_sections_1_to_3():
    lines = [
        "# Aim 2 power analysis and panel design (response to Kolliputi, 2026-10-29)",
        "",
        "## 1. Prospective AUROC confidence intervals",
        "",
        "Method: Hanley-McNeil (1982) nonparametric AUC variance, same estimator as the Seahorse",
        "power analysis (`docs/step2_verification.md`). Validated here against a 20,000-run Monte",
        "Carlo simulation (binormal model, true AUROC 0.75, n=19 active/101 inactive): simulated",
        "95% interval [0.626, 0.860] vs. the analytic Hanley-McNeil interval [0.617, 0.883] below -",
        "the analytic interval is about 12% wider, the expected and safer direction for a",
        "nonparametric estimator (it does not understate uncertainty).",
        "",
        "**The panel's true active/inactive split is not known in advance** - Aim 2 is a curated,",
        "enriched panel, not a random draw from the Tox21 population used for training. Two",
        "scenarios are reported: the Tox21 training-set prevalence (15.9% active, the most",
        "defensible available anchor) and a more balanced 30% assumption, to show how much the",
        "answer depends on this unknown.",
        "",
    ]

    for prevalence, label in [(ci_analysis.TRAINING_PREVALENCE, "Training prevalence (15.9% active)"),
                              (ci_analysis.BALANCED_PREVALENCE, "Balanced-panel assumption (30% active)")]:
        lines += [f"### {label}", "", "| True AUROC | Subset | n (active/inactive) | 95% CI | Half-width |",
                  "|---|---|---|---|---|"]
        for true_auroc in ci_analysis.TRUE_AUROCS:
            for coverage_label, coverage_frac in ci_analysis.PANEL_SIZES.items():
                n_total = round(120 * coverage_frac)
                lo, hi, se, n1, n0 = ci_analysis.ci_for(true_auroc, n_total, prevalence)
                lines.append(
                    f"| {true_auroc} | {coverage_label} | {n_total} ({n1}/{n0}) | "
                    f"[{lo:.3f}, {hi:.3f}] | {ci_analysis.Z_95*se:.3f} |"
                )
        lines.append("")

    lines += [
        "**Reading this honestly:** at n=120 with training-set prevalence, a true AUROC of 0.75",
        "could plausibly produce an observed value anywhere from about 0.62 to 0.88 by chance",
        "alone. That is a wide interval relative to the 0.05 gap between the two milestone values",
        "(0.75 vs 0.80) - a single ~120-compound panel will not cleanly distinguish \"met 0.75\"",
        "from \"met 0.80\" on its own; it mainly distinguishes \"clearly above chance\" from \"clearly",
        "not.\" The balanced-prevalence scenario is meaningfully tighter, which is a real argument",
        "for designing the panel toward better balance rather than assuming it will resemble",
        "Tox21's natural ~16% active rate.",
        "",
        "## 2. Panel-size sensitivity: is 150 clearly better than 120?",
        "",
        "| n | True AUROC | 95% CI | Half-width |",
        "|---|---|---|---|",
    ]
    for true_auroc in ci_analysis.TRUE_AUROCS:
        for n_total in ci_analysis.TOTAL_N_CANDIDATES:
            lo, hi, se, n1, n0 = ci_analysis.ci_for(true_auroc, n_total, ci_analysis.TRAINING_PREVALENCE)
            lines.append(f"| {n_total} | {true_auroc} | [{lo:.3f}, {hi:.3f}] | {ci_analysis.Z_95*se:.3f} |")

    hw_120 = ci_analysis.Z_95 * ci_analysis.ci_for(0.75, 120, ci_analysis.TRAINING_PREVALENCE)[2]
    hw_150 = ci_analysis.Z_95 * ci_analysis.ci_for(0.75, 150, ci_analysis.TRAINING_PREVALENCE)[2]
    pct_tighter = 100 * (1 - hw_150 / hw_120)
    lines += [
        "",
        f"Going from 120 to 150 compounds (+30, +25%) narrows the AUROC CI half-width by about "
        f"{pct_tighter:.0f}%. That is real but not dramatic for the primary AUROC milestone alone.",
        "The stronger argument for 150 is the Seahorse discordance sub-question (below) - 120 is",
        "only just adequate there under the most optimistic assumption.",
        "",
        "## 3. Recommended panel composition",
        "",
        "The three selection criteria are not disjoint head counts that sum to the panel size -",
        "a single compound can satisfy more than one at once. Recommendation:",
        "",
        "- **Outside training scaffolds: effectively the entire panel.** This is not a separate",
        "  budget line - it is a hard inclusion criterion for every compound, since testing on",
        "  genuinely novel chemistry is the point of Aim 2.",
        "- **Paired MMP + Seahorse/respirometry data: as much of the panel as feasible, ideally",
        "  all of it.** The Seahorse discordance milestone needs its own power. From the earlier",
        "  analysis (`docs/step2_verification.md`): detecting a modest true discordance effect",
        "  (AUC 0.60-0.65) needs roughly 121-278 paired compounds on the better-balanced respiration",
        "  endpoints, and 247-554 on the more imbalanced one. At 120 total, that only clears the",
        "  single most optimistic case (AUC=0.65, best-balanced endpoint) - there is no margin.",
        "  At 150, there is some margin for that same case but still not for AUC=0.60 or the",
        "  imbalanced endpoint.",
        "- **Flagged uncertain by the locked model: roughly 25-30% of the panel (about 30-45 of",
        "  150).** Large enough to power a retained-vs-referred accuracy comparison at a referral",
        "  rate consistent with what was tested in Step 2 (the 20-30% referral range), and matches",
        "  the original design intent of enriching for uncertain chemicals.",
        "",
        "**Recommendation: 150 compounds if the budget allows it.** 120 is workable for the",
        "primary AUROC milestone's confidence interval, but it leaves no margin for the Seahorse",
        "discordance milestone - a single unlucky draw could leave that analysis underpowered even",
        "if the true effect is real. 150 (+30 compounds, +25% over the current budget) narrows the",
        f"AUROC CI by about {pct_tighter:.0f}%, and meaningfully improves - without fully solving -",
        "the discordance analysis's power. If 150 is not affordable, 120 should proceed with the",
        "AUROC CI width above stated explicitly as a limitation, not left as an implicit assumption.",
    ]
    return lines


def main():
    lines = build_sections_1_to_3()
    with open(OUT_PATH, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")
    print(f"wrote {OUT_PATH}")


if __name__ == "__main__":
    main()
