# BMW iX3: Bass diffusion forecast for Germany

DS 223 Marketing Analytics (AUA), Homework on Bass Model.

**Innovation:** BMW iX3 (Neue Klasse), from TIME's Best Inventions 2025: <https://time.com/collections/best-inventions-2025/7318539/bmw-ix3/>
**Look-alike:** Tesla Model 3 in Germany (new registrations, 2019-2025, source: KBA).
**Scope:** Germany.

## What was done

1. **Look-alike data.** Annual Model 3 registrations in Germany from KBA (as republished by several sources; see `data/` and the report for the cross-checks).
2. **Bass parameters.** Estimated by nonlinear least squares in the lecture's form (adopters(t) = m * f(t)), with a discrete version and the Bass OLS regression as cross-checks. Result: p about 0.017, q about 1.20, m about 120,000.
3. **Market potential M for the iX3 (Fermi estimate).** M = BMW X3-family registrations in Germany in 2025 (25,286) x iX3 share of the family (20% / 40% / 60%) x 7-year lifecycle = about 35,400 / 70,800 / 106,200.
4. **Forecast.** Adopters per year for 2026-2035 for each M, with the fitted q (headline) and a lower q of 0.5 as a sensitivity case.
5. **Validation.** Actual iX3 registrations in Germany (KBA data, Jan-Sep 2026: 9,532) are compared with the forecast.

## Headline result

With the fitted q and the base share (M about 70,800), the model gives about 20,000 iX3 registrations a year at the peak, around 2028-2029. The early data show the model **under-predicts the launch year** (9,532 registrations by September 2026 against a forecast of 3,861 for all of 2026). This is discussed as a limitation in the report: the look-alike's p cannot capture the backlog of pre-launch orders.

## Repository contents

| Path | Description |
|---|---|
| `bass_fit.py` | Estimates p, q, m from the look-alike (lecture-style nls, discrete nls, Bass OLS, bootstrap, hold-out test) and plots the fit |
| `forecast_ix3.py` | iX3 forecast from the look-alike's p and q and the Fermi estimate of M; writes the tables and chart |
| `requirements.txt` | Python packages |
| `data/model3_germany_annual.csv` | Look-alike series: Tesla Model 3 registrations in Germany, 2019-2025 (+ partial 2026, excluded from the fit) |
| `data/modely_germany_annual.csv` | Robustness series: Tesla Model Y registrations in Germany |
| `data/ix3_germany_2026_monthly.csv` | Actual new-iX3 registrations in Germany, Jan-Sep 2026 |
| `data/ix3_forecast_germany.csv` | Forecast: adopters per year and cumulative, 6 scenarios x 10 years |
| `data/ix3_forecast_summary.csv` | One row per scenario (M, peak year, peak size, share of M adopted by year 7 and 10) |
| `img/model3_germany_bass_fit.png` | Observed Model 3 registrations vs the fitted Bass curve |
| `img/ix3_forecast_germany.png` | iX3 forecast with the actual 2026 registrations marked |
| `report/report_source.md` | Source of the report (method, data, assumptions, results, limitations, references) |
| `report/report.pdf` | The report as a PDF, built from `report_source.md` |
| `report/style.css` | Stylesheet used to build the PDF |

## How to run

Run both scripts from the repository root (the second one imports the first):

```
pip install -r requirements.txt
python bass_fit.py
python forecast_ix3.py
```

`bass_fit.py` prints the parameter estimates and writes `img/model3_germany_bass_fit.png`.
`forecast_ix3.py` writes the forecast tables to `data/` and the chart to `img/`.

## Data notes

- Figures are **registrations** (KBA), used as a proxy for sales.
- KBA's own tables were not accessed directly; the figures come from sites that republish KBA data. The report lists which numbers were cross-checked across sources.
- 2026 is a partial year and is not used for fitting.
- The share of the X3 family taken by the iX3 (20-60%) is an assumption; all other Fermi inputs are cited data.

See `report/report.pdf` (or `report/report_source.md`) for all sources and the full list of caveats.

## Rebuilding the report PDF

Requires [pandoc](https://pandoc.org/) and [wkhtmltopdf](https://wkhtmltopdf.org/). Run from the `report/` folder:

```
cd report
pandoc report_source.md -o report.pdf --pdf-engine=wkhtmltopdf --css=style.css \
  --pdf-engine-opt=--enable-local-file-access \
  -V margin-top=18mm -V margin-bottom=18mm -V margin-left=16mm -V margin-right=16mm
```
