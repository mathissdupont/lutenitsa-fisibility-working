# Manual data import protocol

This project does not guess private APIs, bypass login, solve anti-bot challenges,
or retry access restrictions. `sources.csv` records official sources and access methods.

## Agriculture

Open TÜİK MEDAS or the official data browser. Select the original district geography,
2015–2025 and each exact product classification. Export the table to CSV or Excel using
the portal's own controls. Save the original export under `data/raw/manual_exports/`
without modification. Record the download/access date, publication/reference year,
original codes, units and exact source link. If codes or dates are absent, leave them
missing and document the reason. Preserve official zero observations; leave blanks
missing. Never interpret suppression or absence as zero.

`data/manual/agriculture_template.csv` enumerates 2,904 expected measurements for
11 districts, 11 years, six planning product classes and four metrics. Fresh tomatoes,
generic processing peppers and kapya remain separate classifications. Garlic and herb
types must be disaggregated; the generic herb row is a gap request, not a valid pooled
crop for inference. Oilseed sunflower never supplies refined sunflower oil directly.

Fill only observations actually supported by the export. Every VERIFIED row requires
its source URL/institution, reference year, access date, geographic level and preserved
raw file. Set `available_date` to the earliest documented public release, not the date
you downloaded it. It governs ex-ante use. A blank release date excludes the record
from chronological prediction. The source's data status never establishes local offers.

```powershell
.\.venv\Scripts\python -m src.pipeline import --file .\data\manual\agriculture_template.csv
.\.venv\Scripts\python -m src.pipeline validate
.\.venv\Scripts\python -m src.pipeline regress
```

The import command creates an immutable hash-named raw copy. Resolve duplicate
district/year/product/metric exports by a documented vintage selection before
importing multiple files. No automatic overwrite or averaging is performed.
Additional districts require an evidenced `config/geography.csv` row. Province codes
16/10/45 are standard plate/province identifiers; district and official product codes
are blank until verified. Project product identifiers are not official TÜİK codes.

## Deflator

Use the linked official TÜİK CPI series in `sources.csv`. Export monthly index **levels**
for the same rebased vintage, calculate a twelve-month average for each complete year
and fill `deflator_template.csv`. A rate such as year-on-year inflation is not an index
level. All years must have one base/vintage, positive levels and no duplicates. The
general CPI measures purchasing-power normalization, not a local ingredient quote.
Constant price = observed TRY/kg × base-year CPI / observation-year CPI. A base year
without a complete annual average leaves conversion missing. Full-year 2026 CPI is
not yet observable on 10 October 2026. Either wait for it or explicitly change the
base-price year and align all real-currency model inputs.

## Climate

MGM MEVBİS supports membership/authorized ordering. Export station measurements
with station identifiers, units, date coverage and public availability date into the
climate template. Do not use realized future climate. Climate ingestion and predictive
feature integration remain extension points pending an approved station/crop calendar.
The current model uses only a lagged target and deterministic time trend.

## Procurement and logistics

Fill `supplier_offers_template.csv` using dated VERIFIED offers, one row per supplier,
ingredient, factory and month. All eight recipe ingredients need offers. Fields for
price, freight and handling are separate; quotes must be in the configured real
price year. `available_tonnes` is offered gross supply, not agricultural production.
`participation_limit` is the maximum share of annual usable ingredient demand from
one supplier. `transport_loss` is lost fraction before delivery; `quality_eligible`
is 1 or 0. Provide exact quotation and source references.

`freight_try_per_tonne` is used in LP mode. `freight_try_per_truck` is required for
integer truck mode and replaces variable freight. Specify payload, return cost and
route restrictions in the quotation. Current verified KGM distances are district
center proxies; quotes must incorporate OSB/customer access and any empty return.
Do not silently multiply center-to-center zero by a generic freight rate.

Edit `config/assumptions.json` with twelve `monthly_production_fractions` summing
to one, storage capacity, storage cost per tonne-month, inventory loss, integer-truck
policy and any monthly truck limit. Zero initial and terminal inventory is explicit.
Period-end stock incurs holding cost; this monthly approximation needs finer periods
where within-month holding or shelf life is material. Supplier participation is summed
over the horizon. Mixed loads across crops are not modeled; each offer dispatch has
its own truck count. Shelf-life constraints and full outbound network allocation are
not yet implemented, so obtain validated operating designs before investment use.

Store original quotations in `data/raw/quotes/`. Keep prices/volumes for oil, vinegar,
salt, spices and jars separately. Packaging is a financial input, not an agricultural
supply crop. `config/markets.csv` lists Istanbul, Ankara, Izmir, regional and export
markets; all customer demand shares, addresses and prices are currently missing.
The current financial engine uses aggregate net price, aggregate demand and an
explicit per-kg outbound cost. Market-by-market contracts require additional detail.

## Financial and site inputs

Complete site maintenance and outbound cost, customer demand and all supplier
costs. Record scope, real price year, taxes, utility capacities and capex breakdowns.
Every capacity needs its own equipment/land/labor/utility quotations; do not apply
unverified power-law scaling. The spreadsheet's yellow cells show scenario inputs.
Editing Excel updates linked finance but does not rerun LP/MILP; update JSON/CSV
and rerun `all` to regenerate the reproducible report. The generated report supports
the requested ten-year horizon; changing horizon requires regenerating the workbook.

The original FE401 PDF is missing. Five mandatory site gates stay UNVERIFIED until
evidenced parcel-specific approvals exist. For Gönen, this study identifies the
**Leather Specialized and Mixed OSB**, not the greenhouse agricultural zone. Confirm
that identity and parcel before completing screening. A weighted score cannot bypass
a mandatory gate and cannot establish statistical profitability.
