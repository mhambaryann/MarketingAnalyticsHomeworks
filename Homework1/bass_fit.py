"""Bass diffusion model: estimate p, q, M from the look-alike series.

Look-alike: Tesla Model 3, Germany, annual new registrations (KBA), 2019-2025.
Run:  python bass_fit.py
"""
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from scipy.optimize import curve_fit

DATA = "data/model3_germany_annual.csv"
FIG = "img/model3_germany_bass_fit.png"
RNG = np.random.default_rng(42)


# ---------- Bass model ----------
def F(t, p, q):
    """Cumulative adoption fraction at the END of period t (F(0)=0)."""
    e = np.exp(-(p + q) * t)
    return (1 - e) / (1 + (q / p) * e)


def bass_sales(t, p, q, M):
    """Adopters in period t (discrete version: F(t) - F(t-1))."""
    return M * (F(t, p, q) - F(t - 1, p, q))


# ---------- Lecture formulation (DS 223 slides 17 and 34): a(t) = m * f(t) ----------
def bass_f(t, p, q):
    """Continuous Bass density f(t), evaluated at integer t."""
    e = np.exp(-(p + q) * t)
    return ((p + q) ** 2 / p) * e / (1 + (q / p) * e) ** 2


def lecture_sales(t, m, p, q):
    return m * bass_f(t, p, q)


def fit_lecture_nls(t, S, n_starts=500):
    """nls as in the lecture (start m=sum(sales), p=.02, q=.4), plus multi-start."""
    best = None
    starts = [[S.sum(), 0.02, 0.4]]
    for _ in range(n_starts):
        starts.append([S.sum() * RNG.uniform(0.6, 3), 10 ** RNG.uniform(-4, -0.7),
                       RNG.uniform(0.05, 2.0)])
    for s in starts:
        try:
            po, pc = curve_fit(lecture_sales, t, S, p0=s,
                               bounds=([1e4, 1e-6, 1e-3], [5e6, 0.9, 5.0]), maxfev=50_000)
            sse = ((S - lecture_sales(t, *po)) ** 2).sum()
            if best is None or sse < best[0]:
                best = (sse, po, np.sqrt(np.diag(pc)))
        except Exception:
            continue
    return best  # (SSE, [m, p, q], [se_m, se_p, se_q])


# ---------- Method 1: OLS (Bass 1969) ----------
def fit_ols(S):
    """S_t = a + b*N_{t-1} + c*N_{t-1}^2  ->  M, p, q."""
    N_prev = np.concatenate([[0], np.cumsum(S)[:-1]])
    X = np.column_stack([np.ones_like(N_prev), N_prev, N_prev ** 2])
    a, b, c = np.linalg.lstsq(X, S, rcond=None)[0]
    disc = b * b - 4 * a * c
    if disc < 0 or c == 0:
        return None
    roots = [(-b + np.sqrt(disc)) / (2 * c), (-b - np.sqrt(disc)) / (2 * c)]
    M = max(roots)                       # the positive root
    return dict(p=a / M, q=-M * c, M=M)


# ---------- Method 2: NLS with many starting values ----------
def fit_nls(t, S, M_min=30_000, n_starts=500):
    sols = []
    for _ in range(n_starts):
        p0 = 10 ** RNG.uniform(-4, -0.7)
        q0 = RNG.uniform(0.05, 2.0)
        M0 = S.sum() * RNG.uniform(0.6, 3.0)
        try:
            po, _ = curve_fit(bass_sales, t, S, p0=[p0, q0, M0],
                              bounds=([1e-6, 1e-3, M_min], [0.9, 5.0, 5e6]),
                              maxfev=50_000)
            sols.append((((S - bass_sales(t, *po)) ** 2).sum(), *po))
        except Exception:
            continue
    sols = np.array(sorted(sols))
    return sols  # columns: SSE, p, q, M  (best first)


def bootstrap(t, S, p, q, M, B=1000):
    fit = bass_sales(t, p, q, M)
    resid = S - fit
    out = []
    for _ in range(B):
        Sb = np.maximum(fit + RNG.choice(resid, len(S), replace=True), 1)
        try:
            po, _ = curve_fit(bass_sales, t, Sb, p0=[p, q, M],
                              bounds=([1e-6, 1e-3, 30_000], [0.9, 5.0, 5e6]),
                              maxfev=50_000)
            out.append(po)
        except Exception:
            continue
    return np.array(out)


if __name__ == "__main__":
    df = pd.read_csv(DATA)
    df = df[df.complete_year == True].copy()     # drop the partial 2026 row
    df["year"] = df.year.astype(int)             # the partial row made it text
    t = df.t.values.astype(float)
    S = df.registrations.values.astype(float)

    print("OLS (Bass 1969, lagged cumulative):", fit_ols(S))

    # Lecture-style nls: sales = m * f(t)
    sse_l, (m_l, p_l, q_l), (se_m, se_p, se_q) = fit_lecture_nls(t, S)
    dof = len(S) - 3
    print(f"Lecture-style nls: m={m_l:,.0f} (SE {se_m:,.0f})  p={p_l:.4f} (SE {se_p:.4f})  "
          f"q={q_l:.3f} (SE {se_q:.3f})  RSE={np.sqrt(sse_l/dof):,.0f} on {dof} df")
    print(f"  predicted peak t*={np.log(q_l/p_l)/(p_l+q_l):.2f}  actual peak t={int(np.argmax(S))+1}")

    sols = fit_nls(t, S)
    sse, p, q, M = sols[0]
    fit = bass_sales(t, p, q, M)
    r2 = 1 - sse / ((S - S.mean()) ** 2).sum()
    print(f"NLS best: p={p:.4f}  q={q:.3f}  M={M:,.0f}  R2={r2:.3f}  RMSE={np.sqrt(sse/len(S)):,.0f}")
    print(f"Observed cumulative sales: {S.sum():,.0f}  (compare with M!)")
    print(f"Peak at t*={np.log(q/p)/(p+q):.2f}, peak sales={M*(p+q)**2/(4*q):,.0f}")

    # Are there other local minima? (shows why multi-start matters)
    print("Distinct local solutions (SSE, p, q, M):")
    shown = []
    for r in sols:
        if not any(np.allclose(r[1:], s[1:], rtol=2e-2) for s in shown):
            shown.append(r)
        if len(shown) == 3:
            break
    for r in shown:
        print("  ", np.round(r, 4))

    bs = bootstrap(t, S, p, q, M)
    for i, name in enumerate(["p", "q", "M"]):
        lo, mid, hi = np.percentile(bs[:, i], [2.5, 50, 97.5])
        print(f"bootstrap {name}: {lo:.4g} | {mid:.4g} | {hi:.4g}")

    # Hold-out check: fit on 2019-2023, predict 2024-2025
    k = 5
    s5 = fit_nls(t[:k], S[:k], M_min=S[:k].sum(), n_starts=300)[0]
    pred = bass_sales(t[k:], *s5[1:])
    print("Hold-out: predicted", pred.round(0), "actual", S[k:])

    # Plot
    fig, ax = plt.subplots(figsize=(8, 4.5))
    ax.bar(df.year, S, color="#9ecae1", label="Observed (KBA)")
    tt = np.linspace(1, 7, 200)
    ax.plot(2018 + tt, bass_sales(tt, p, q, M), color="#08519c", lw=2, label="Bass fit")
    ax.plot(df.year, fit, "o", color="#08519c")
    ax.set_xlabel("Year"); ax.set_ylabel("New registrations in Germany")
    ax.set_title("Tesla Model 3, Germany: observed vs fitted Bass curve")
    ax.legend(); fig.tight_layout()
    import os; os.makedirs("img", exist_ok=True)
    fig.savefig(FIG, dpi=150)
    print("saved", FIG)
