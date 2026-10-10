# Lutenitsa Factory Location Feasibility

Reproducible FE401 infrastructure for Bursa–Mustafakemalpasa, Manisa–Salihli and
Balikesir–Gonen. Code/documentation and file names are in English; the presentation
workbook and final conclusions are in Turkish.

**Evidence status:** a verified profitable-site recommendation is not possible yet.
There are 38 verified provincial crop observations and 45 official KGM
district-center road-distance proxies. The requested 2015–2025 district panel,
local prices, binding offers and parcel approvals are missing.

## Setup and run

Python 3.14 was used and tested. Dependencies are pinned.

```powershell
python -m venv .venv
.\.venv\Scripts\python -m pip install -r requirements.txt
.\.venv\Scripts\python -m src.pipeline all
.\.venv\Scripts\python -m pytest -q
```

Individual commands:

```powershell
.\.venv\Scripts\python -m src.pipeline collect
.\.venv\Scripts\python -m src.pipeline collect --online
.\.venv\Scripts\python -m src.pipeline validate
.\.venv\Scripts\python -m src.pipeline regress
.\.venv\Scripts\python -m src.pipeline optimize
.\.venv\Scripts\python -m src.pipeline finance
.\.venv\Scripts\python -m src.pipeline report
.\.venv\Scripts\python -m src.pipeline import --file path/to/observations.csv
```

Default execution is offline and uses preserved files. Online collection downloads
only registered public files or Excel links published on the official KGM page.
No undocumented API, authentication bypass or aggressive retries are used.
The 28 MB KGM district workbook has about one million rows; extraction streams
its XML and caches selected routes against the raw SHA-256 hash.

## Structure and outputs

- output/Lutenitsa_Factory_Feasibility_2015_2025.xlsx: 24 Turkish presentation
  sheets, verified data, charts, missing-data disclosures and linked finance formulas.
- reports/final_report_tr.md: Turkish conclusion and evidence gaps.
- reports/manual_import.md: exact import process and implementation limits.
- reports/phase_progress_tr.md: phase commands, results and blockers.
- sources.csv and data_dictionary.csv: registry and observation schema.
- config/: recipe, capacities, financial assumptions, site gates, geography,
  product classes, market scenarios and FE401 inputs.
- data/raw/official/: unmodified PDFs, HTML and KGM workbooks.
- data/raw/legacy/: original files, including the original README.
- data/manual/: manual import templates.
- data/processed/: normalized observations, proxies, missingness and model statuses.
- src/: collection, quality, statistics, materials, LP/MILP, finance, decision and CLI.
- tests/: synthetic test-only fixtures and deliverable-integrity checks.

The original Excel, logistics script and root CSV files are unchanged, verified
by SHA-256. This README was expanded; its original is preserved under raw/legacy.
Do not rerun one-time bootstrap/inspection scripts after editing inputs: they are
initial setup tools, not the reproducible CLI.

## Statistical policy

Only VERIFIED district observations with explicit release dates are eligible.
Province totals are not disaggregated. Fresh/processing tomatoes and generic
processing/kapya pepper stay separate. Project codes are not official TUIK codes.
Missing is never zero unless officially reported. Units, duplicate keys,
nonnegative values, outliers and district/province consistency are checked.
Flagged outliers remain. An official same-vintage CPI index normalizes prices;
national producer indices are never treated as local quotes.

Models: naive, rolling average, trend, OLS, Ridge, panel fixed effects and
sample-size-gated Random Forest. Chronological validation uses dated lagged
targets, training-only scaling and 2023–2025 evaluation. Earlier expanding folds
are separate. There are no realized same-year yield or future-weather features.

Future point forecasts need a validated model and a 2025 observation known at
the editable forecast origin. All current regressions/forecasts are NOT_ESTIMABLE.
Multi-year uncertainty calibration, climate-feature integration, optimistic and
pessimistic scenarios and disaggregated herb models remain extensions requiring
data. No coefficients, p-values or uncertainty bounds have been fabricated.

## Materials, optimization and finance

The original gross recipe is ASSUMED. Cleaning, roasting, seasonality and storage
remain missing until measured. Refined oil is a separate processed supplier
product, with salt, vinegar, spices and packaging modeled separately.

The optimizer supports monthly balances, transport shrinkage, shared storage,
quality eligibility, usable supplier participation limits and integer trucks.
Truck mode uses fixed departure cost instead of a simultaneous tonne-km charge.
Actual production is never substituted for offered/contracted supply. Real runs
require complete verified offers and storage settings. Shelf-life constraints,
mixed truck loads, detailed outbound market allocation and robust stochastic
sourcing remain documented extensions.

Finance uses real prices with a real discount rate. Manufactured, demanded,
sold and unsold quantities are distinct. Unsold output retains production costs.
Inbound freight enters landed ingredient cost once. The engine implements EBITDA,
EBIT, depreciation, tax-loss carry, replacement capex, terminal book value/sale
tax, working capital, FCF, NPV, conventional IRR, payback and EBITDA break-even
price/volume. No instant tax-loss cash refunds are assumed. Different capacities
need distinct quotations, so no unverified capex scaling is applied.

Actual NPV remains unavailable because demand, landed costs, outbound distribution
and maintenance are missing. The current engine uses aggregate sauce price/demand;
product/market contracts require extension. The workbook has the requested
ten-year schedule and allows a shorter horizon. Regenerate after configuration edits.

## Optional hypothetical demonstration

```powershell
.\.venv\Scripts\python -m src.pipeline demo
```

Only output/demo receives legacy LP examples, financial arithmetic, deterministic
sensitivity and 500 independent triangular-shock draws per site. These are
ASSUMED, uncalibrated, and never feed the main workbook or recommendation.
Harvest shortfall draws are infeasible; NPV statistics are conditional on feasible
draws. Historical observations are never synthetically extended.

## Spreadsheet QA and editing

Python tests check workbook structure, sources, formulas, missing inputs and hashes.
Optional Codex runtime QA uses @oai/artifact-tool to render and independently
recalculate, then compare finance to Python:

```powershell
.\.venv\Scripts\python -m scripts.check_workbook
node scripts/recalculate_artifact.mjs
.\.venv\Scripts\python -m scripts.verify_formula_caches
node scripts/preview_workbook.mjs
```

The ignored scripts/node_modules junction points to the Codex runtime dependency.
These Node commands are optional outside Codex; the Python pipeline requires no
Node package. Native Excel COM could not open workbooks in this execution session.
Independent recalculation validates formula caches and financial arithmetic;
the original XlsxWriter file retains its charts, tables, panes and validations.
Optional scripts/recalculate_excel.ps1 works where local Excel COM is available.

Yellow spreadsheet cells are editable scenario inputs. Editing them updates
linked finance but cannot rerun LP/MILP or establish procurement feasibility.
Synchronize JSON/CSV inputs and rerun all for reproducible optimization and output.
