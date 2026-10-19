"""BMW iX3 diffusion forecast for Germany.

p, q  : estimated on the look-alike (Tesla Model 3, Germany) with the lecture-style nls
M     : Fermi estimate = X3-family registrations/yr x iX3 share x lifecycle years
Run from the repo root after bass_fit.py's data exists:  python forecast_ix3.py
"""
import os
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from bass_fit import fit_lecture_nls, bass_f

# ---------------- Fermi inputs (see report/report_source.md, Section 7) ----------------
X3_FAMILY_2025 = 25_286      # DATA: BMW X3-family registrations in Germany, 2025 (KBA via angurten.de)
LIFECYCLE_YEARS = 7          # DATA (rounded): X3 generations 2017 -> 2024
SHARES = {"Low (20%)": 0.20, "Base (40%)": 0.40, "High (60%)": 0.60}   # ASSUMPTION: iX3 share of family
Q_LOW = 0.5                  # ASSUMPTION: sensitivity value for q (Bass 1969 estimates ~0.17-0.65)
LAUNCH_YEAR = 2026           # t = 1
HORIZON = 10                 # forecast years

# ---------------- p, q from the look-alike ----------------
df = pd.read_csv("data/model3_germany_annual.csv")
df = df[df.complete_year == True]
t_obs = df.t.values.astype(float)
S_obs = df.registrations.values.astype(float)
_, (m_look, p, q_fit), _ = fit_lecture_nls(t_obs, S_obs)
print(f"Look-alike (Model 3, Germany): p={p:.4f}  q={q_fit:.3f}  m={m_look:,.0f}")

q_cases = {"Fitted q": q_fit, f"Low q ({Q_LOW})": Q_LOW}

# ---------------- forecast ----------------
t = np.arange(1, HORIZON + 1, dtype=float)
rows, summary = [], []
for share_label, share in SHARES.items():
    M = X3_FAMILY_2025 * share * LIFECYCLE_YEARS
    for q_label, q in q_cases.items():
        adopters = M * bass_f(t, p, q)
        cum = np.cumsum(adopters)
        tstar = np.log(q / p) / (p + q)
        peak = M * (p + q) ** 2 / (4 * q)
        summary.append(dict(share=share_label, q_case=q_label, q=round(q, 3), M=round(M),
                            peak_year=round(LAUNCH_YEAR - 1 + tstar, 1), peak_adopters=round(peak),
                            adopters_2026=round(adopters[0]),
                            pct_of_M_by_t7=round(100 * cum[6] / M), pct_of_M_by_t10=round(100 * cum[9] / M)))
        for i in range(HORIZON):
            rows.append(dict(year=LAUNCH_YEAR + i, t=i + 1, share=share_label, q_case=q_label,
                             M=round(M), adopters=round(adopters[i]), cumulative=round(cum[i]),
                             pct_of_M=round(100 * cum[i] / M, 1)))

out = pd.DataFrame(rows)
os.makedirs("data", exist_ok=True)
out.to_csv("data/ix3_forecast_germany.csv", index=False)
summ = pd.DataFrame(summary)
summ.to_csv("data/ix3_forecast_summary.csv", index=False)
print("\nScenario summary:")
print(summ.to_string(index=False))

# ---------------- early actuals (KBA via goingelectric.de) ----------------
actual = pd.read_csv("data/ix3_germany_2026_monthly.csv")
ytd = int(actual.registrations.sum())
last_month = pd.to_datetime(actual.month.iloc[-1]).strftime("%b")   # e.g. "Sep"
print(f"\nActual new-iX3 registrations in Germany, Jan-{last_month} 2026: {ytd:,}")
for sh in SHARES:
    for ql in q_cases:
        f26 = int(out[(out.share == sh) & (out.q_case == ql) & (out.year == LAUNCH_YEAR)].adopters.iloc[0])
        print(f"  forecast for ALL of 2026, {sh:11s} {ql:12s}: {f26:>6,}   (actual YTD is {ytd / f26:.1f}x)")

# ---------------- chart ----------------
os.makedirs("img", exist_ok=True)
fig, axes = plt.subplots(1, 2, figsize=(11, 4.5), sharey=True)
colors = {"Low (20%)": "#9ecae1", "Base (40%)": "#3182bd", "High (60%)": "#08306b"}
for ax, q_label in zip(axes, q_cases):
    for share_label in SHARES:
        sub = out[(out.q_case == q_label) & (out.share == share_label)]
        ax.plot(sub.year, sub.adopters, marker="o", color=colors[share_label],
                label=f"{share_label}, M={sub.M.iloc[0]:,}")
    ax.scatter([LAUNCH_YEAR], [ytd], marker="D", s=70, color="#d62728", zorder=5,
               label=f"Actual Jan-{last_month} 2026 (KBA): {ytd:,}" if ax is axes[0] else None)
    ax.set_title(f"{q_label}  (p={p:.3f}, q={q_cases[q_label]:.2f})")
    ax.set_xlabel("Year"); ax.grid(alpha=0.3)
axes[0].set_ylabel("New iX3 registrations in Germany")
axes[0].legend(fontsize=8)
fig.suptitle("BMW iX3, Germany: Bass forecast of adopters per year (illustrative)")
fig.tight_layout()
fig.savefig("img/ix3_forecast_germany.png", dpi=150)
print("\nsaved data/ix3_forecast_germany.csv, data/ix3_forecast_summary.csv, img/ix3_forecast_germany.png")
