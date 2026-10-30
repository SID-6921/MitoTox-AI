"""Power analysis for the Seahorse concordance discordance finding (AUROC
0.47-0.56 at n=100 held-out chemicals). Kolliputi asked: given that observed
effect, what sample size would detect a real modest AUC (0.55-0.70) at 80%
power - to size the compound panel in Aim 2's budget, not to change the
current finding.

Method: Hanley-McNeil (1982) nonparametric AUC variance estimator,
  Var(AUC) = [AUC(1-AUC) + (n1-1)(Q1-AUC^2) + (n0-1)(Q2-AUC^2)] / (n1*n0)
  Q1 = AUC/(2-AUC), Q2 = 2*AUC^2/(1+AUC)
combined with a two-sided z-test of H0: AUC=0.5 vs H1: AUC=target, holding the
active:inactive prevalence fixed at each endpoint's observed value in the
n=100 held-out set. Solved via binary search over total N (not by scaling the
current n=100 sample by whole multiples, which an earlier version of this
script did and which understated resolution - it can only return answers
that are exact multiples of 100, overstating the true minimum by up to ~65%
for some targets) rather than a closed-form shortcut, since the closed forms
still require Var to be evaluated at a specific n anyway.
"""
import numpy as np
from scipy.stats import norm

ALPHA = 0.05
TARGET_POWER = 0.80
TARGET_AUCS = [0.55, 0.60, 0.65, 0.70]

# (endpoint, n_active, n_inactive) observed in the n=100 genuinely held-out subset
ENDPOINTS = [
    ("primary_basal_resp_rate", 64, 36),
    ("primary_max_resp_rate", 64, 36),
    ("primary_inhib_resp_rate", 14, 86),
]


def hanley_mcneil_var(auc, n1, n0):
    q1 = auc / (2 - auc)
    q2 = 2 * auc**2 / (1 + auc)
    return (auc * (1 - auc) + (n1 - 1) * (q1 - auc**2) + (n0 - 1) * (q2 - auc**2)) / (n1 * n0)


def power_for_n(target_auc, n1, n0, alpha=ALPHA):
    var0 = hanley_mcneil_var(0.5, n1, n0)
    var1 = hanley_mcneil_var(target_auc, n1, n0)
    z_alpha = norm.ppf(1 - alpha / 2)
    auc_crit = 0.5 + z_alpha * np.sqrt(var0)
    z_power = (target_auc - auc_crit) / np.sqrt(var1)
    return norm.cdf(z_power)


def required_n(target_auc, ratio_active, ratio_inactive, max_total=200_000):
    """Find the smallest total N (holding the observed active:inactive
    prevalence fixed, n1 = round(N * prevalence)) with power >= 0.80.

    Searches every integer N (not just whole multiples of the current n=100
    sample) via a binary search on the monotonically-increasing power(N)
    curve, so the result is the true minimum under this prevalence
    constraint rather than an artifact of the current sample size.
    """
    prevalence = ratio_active / (ratio_active + ratio_inactive)

    def power_at_total(total):
        n1 = max(round(total * prevalence), 1)
        n0 = max(total - n1, 1)
        return power_for_n(target_auc, n1, n0), n1, n0

    lo, hi = 4, max_total
    if power_at_total(hi)[0] < TARGET_POWER:
        return None, None, None
    while hi - lo > 1:
        mid = (lo + hi) // 2
        if power_at_total(mid)[0] >= TARGET_POWER:
            hi = mid
        else:
            lo = mid
    _, n1, n0 = power_at_total(hi)
    return n1 + n0, n1, n0


def simulate_auroc_samples(true_auc, n1, n0, n_sims=20_000, seed=42):
    """Binormal-model Monte Carlo: positives ~ N(mu,1), negatives ~ N(0,1),
    with mu chosen so the population AUROC equals true_auc exactly
    (AUROC = Phi(mu/sqrt(2)) for equal-variance binormal). Returns an array
    of n_sims simulated sample AUROCs - the empirical distribution a real
    study of this size would draw from if the model's true discrimination
    were exactly true_auc."""
    from scipy.stats import norm as _norm
    from sklearn.metrics import roc_auc_score
    rng = np.random.default_rng(seed)
    mu = _norm.ppf(true_auc) * np.sqrt(2)
    aurocs = np.empty(n_sims)
    for i in range(n_sims):
        pos = rng.normal(mu, 1, n1)
        neg = rng.normal(0, 1, n0)
        y = np.concatenate([np.ones(n1), np.zeros(n0)])
        s = np.concatenate([pos, neg])
        aurocs[i] = roc_auc_score(y, s)
    return aurocs


def simulated_ci(true_auc, n1, n0, n_sims=20_000, seed=42):
    """95% CI via the 2.5/97.5 percentiles of the simulated AUROC distribution."""
    samples = simulate_auroc_samples(true_auc, n1, n0, n_sims, seed)
    return np.percentile(samples, 2.5), np.percentile(samples, 97.5)


def simulated_power(target_auc, n1, n0, alpha=ALPHA, n_sims=20_000, seed=42):
    """Simulation-based power: fraction of simulated samples (true AUROC =
    target_auc) whose AUROC exceeds the same analytic critical value used
    in power_for_n - i.e. P(reject H0: AUC=0.5 | true AUC=target_auc),
    estimated empirically rather than via the analytic alternative-variance
    approximation."""
    var0 = hanley_mcneil_var(0.5, n1, n0)
    z_alpha = norm.ppf(1 - alpha / 2)
    auc_crit = 0.5 + z_alpha * np.sqrt(var0)
    samples = simulate_auroc_samples(target_auc, n1, n0, n_sims, seed)
    return (samples > auc_crit).mean()


def minimum_detectable_auc(n1, n0, target_power=TARGET_POWER, lo=0.5001, hi=0.999, tol=1e-5):
    """Inverse of required_n: fix n1/n0, find the smallest AUC (closest to
    0.5) whose power still clears target_power. Power is monotonically
    increasing in |AUC-0.5|, so binary search on AUC converges on the
    smallest detectable value."""
    if power_for_n(hi, n1, n0, ) < target_power:
        return None
    while hi - lo > tol:
        mid = (lo + hi) / 2
        if power_for_n(mid, n1, n0) >= target_power:
            hi = mid
        else:
            lo = mid
    return hi


def main():
    print(f"Power analysis: detecting AUC != 0.5 at alpha={ALPHA}, power={TARGET_POWER}\n")
    for endpoint, n_active, n_inactive in ENDPOINTS:
        ratio = n_active / n_inactive
        print(f"{endpoint} (observed n=100, {n_active} active / {n_inactive} inactive, "
              f"active:inactive ratio {ratio:.3f}):")
        for target in TARGET_AUCS:
            total, n1, n0 = required_n(target, n_active, n_inactive)
            if total is None:
                print(f"  target AUC={target}: no solution under {200_000} total")
                continue
            print(f"  target AUC={target}: needs total n={total} "
                  f"({n1} active / {n0} inactive, same observed ratio)")
        print()

    print("Sanity check: current observed n=100 statistical power to detect each target AUC")
    for endpoint, n_active, n_inactive in ENDPOINTS:
        print(f"{endpoint}:")
        for target in TARGET_AUCS:
            p = power_for_n(target, n_active, n_inactive)
            print(f"  at current n=100, power to detect AUC={target}: {p:.3f}")


if __name__ == "__main__":
    main()
