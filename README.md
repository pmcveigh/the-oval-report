# The Oval Report

Open **`The_Oval_Report.html`** for the Glentoran dashboard. Keep
**`All_Clubs_Predictions.html`** beside it: the compact navigation links the two pages.
Each page embeds its own CSS, JavaScript, data, model parameters and CSV downloads;
no installation or internet connection is needed to use the report. You can also
serve the project with `python -m http.server 8000` and open
`http://localhost:8000/The_Oval_Report.html`. The build writes the hosted pair to
`dist/index.html` and `dist/All_Clubs_Predictions.html`, with matching return links. Source data cover the supplied 2026/27 snapshot through
7 November 2026. Opening the HTML does **not** refresh it.

The compact Glentoran overview shows the next fixture, result prediction, win/draw/loss
chances, latest result, form, position, points and goal difference above the fold at
1366 × 768 and 1920 × 1080. Hash-addressable tabs keep fixtures, form, scenarios,
score chances, Glentoran's historical prediction record and exports accessible.
The season tab pairs the projected league table with Glentoran's finishing chances;
points targets and split details expand below. Current summary statistics stay factual
when a hypothetical result changes the scenario table. Assumed results follow navigation
between the two pages when session storage is available; storage is optional.

All-club match predictions, the full historical record and model comparisons are on
the separate all-clubs page, together with club form and league fixture filters.
Long lists use pages of 12 matches. The information buttons support hover, keyboard
focus, Enter/Space, Escape, tapping, closing and outside-click dismissal. Their content
stays within the viewport. Important data and competition warnings remain visible.
Predicted goals refer to the scoring model, not shot-based xG. Data, fitting,
simulation and historical exports are unchanged by this presentation redesign.
`baseline/` preserves the original HTML, build brief and both audits unchanged.
The original reference is a reconstructed backtest, not a published prediction record.

**Held-out improvement is inconclusive / not demonstrable.** The validation-selected
Elo model scored 0.7273 Brier and 1.2017 log loss on the 19-match test, versus 0.7209
and 1.1670 for the frozen baseline. Selection was not changed after the test.
Poisson's better test point estimates are exploratory, with intervals overlapping zero.
See [engineering report](reports/engineering-report.md) and [validation record](reports/validation.md).

## Reproduce

Requires Python 3.11+ and Node 20+ (tested Python 3.12.14 / Node 24.22.1). Python fits the models; Node executes the frozen
baseline and the JavaScript parity tests. Runtime dependencies are pinned.

```sh
python -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
export PYTHONPATH=src
export OPENBLAS_NUM_THREADS=1
.venv/bin/python -m oval build
.venv/bin/python -m unittest discover -s tests -v
node tests/test_engine.cjs
```

Optional DOM integration tests (no runtime dependency in the HTML):

```sh
npm ci --ignore-scripts --cache work/npm-cache
npm test
```

DOM tests exercise both pages, real event handlers, selections/reset, filters,
pagination across all 87 historical matches and 111 remaining fixtures, matrix,
projections, Glentoran-only scope, navigation and download actions.

Browser checks require Playwright and Chromium, independently of the offline app:

```sh
# With the static server running:
node tests/test_browser.cjs
# Optional: OVAL_BASE_URL=http://localhost:8000 CHROMIUM_PATH=/path/to/chromium
```

Chromium rendering and interaction were tested at 1366 × 768, 1920 × 1080,
768 px, 390 px and 320 px widths. Tests cover every tab's horizontal bounds,
first-viewport essentials, direct URLs and deep links, shared scenarios, mouse /
keyboard / touch help, empty fixtures, no filter matches and calculation errors.
Screenshots are generated under `work/browser/` for visual review. Managed Chrome
blocks `file://` URLs with `ERR_BLOCKED_BY_ADMINISTRATOR`; local-file browser
navigation remains unverified in this environment. HTTP navigation works, and
both self-contained HTML files retain relative sibling links. Firefox, Safari and
physical touchscreen devices have not been tested.

Run the entire declared chronological evaluation again:

```sh
PYTHONPATH=src OPENBLAS_NUM_THREADS=1 python -m oval evaluate
```

The protocol is [evaluation-protocol.json](reports/evaluation-protocol.json), committed
before candidate evaluation. Evaluation writes selected configurations before scoring
the final test. `build` reuses this selection and comparison; it never silently reselects
against the test. Rebuilding unchanged inputs produces identical HTML bytes.

## Update data explicitly

Check access and save raw source responses or exact failure reasons:

```sh
PYTHONPATH=src python -m oval regenerate --check-sources
```

This attempts NIFL, Glentoran and Football-Data and rebuilds the accepted snapshot.
It does **not** pretend that a successful HTML fetch is a verified fixture import.
During this run all three destinations returned proxy HTTP 403. See
[source-access.json](data/source-access.json).

To accept an actual update, provide normalised, documented records:

```sh
PYTHONPATH=src python -m oval regenerate \
  --results work/results.json \
  --fixtures work/fixtures.json \
  --as-of 2026-11-14 \
  --provenance work/provenance.json
```

Use the exact field schema in `data/canonical/results.json` and `fixtures.json`.
Results require `id`, ISO `date`, canonical `home`/`away`, integer `hg`/`ag`,
`competition: "NIFL Premiership"`, `season`, `source`, `verification`. Fixtures require
`id`, ISO `date` or null, `time` or null, `home`, `away`, `status`, `competition`,
`season`, `verification`. Remove played fixtures from the remaining list. Preserve
all original 87 audited matches; corrections require a separately reviewed version.
All twelve canonical club names are explicit; unknown clubs/competitions fail validation.

Provenance JSON requires `source_urls` (array), `retrieved_at` (timestamp),
`licence_notes`, `coverage` and `discrepancies` (use `"none reported"` where appropriate).
Source access/licence claims must be supported by the source; an import is never
automatically marked independently verified. Keep raw source extracts separately
under `data/raw/`. Do not feed cup scores into the league model.

The supported update scope is this season **before the split**. Results and remaining
fixtures must complete exactly 33 matches per club. Published post-split fixtures,
cross-season identities and prior-season promotion/carry-over need a reviewed adapter
and verified rules; the present build does not claim to handle them. The original
87-match comparison stays frozen when newer results are imported. Production models
refit to the accepted factual snapshot using the validation-selected hyperparameters.

## Data and forecast interpretation

- 87 supplied results internally reconstruct all 12 table rows exactly. All 111 supplied
  remaining fixtures complete the 33-game first phase, with three games per club pair.
- No independently verified earlier seasons were obtained. Candidates have 66 common
  eligible fixtures after a 20-match training minimum. All 87 remain visible for each
  model, with explicit unavailability reasons for the opening 21.
- Models: frozen Oval v3, regularised opposition-adjusted Poisson, two-stage Dixon–Coles,
  draw-aware Davidson Elo and smoothed earlier-result frequency.
- Production is an explicit hybrid: Elo 1/X/2 plus Dixon–Coles conditional goal shapes.
  The joint score grid is reweighted by outcome to match Elo exactly. Every displayed
  market and the season simulator derive from this same distribution. Elo does not
  receive a native exact-score metric in the comparison.
- Momentum is the original descriptive Formbook indicator; it never enters candidates.
- Scenario locks use 1–0 / 0–0 / 0–1. They update the scenario table, projections, position
  probabilities, points thresholds, difficulty and result advice. Factual results and
  fitted parameters remain immutable. Unplayed match probabilities keep the factual
  information cut-off, rather than refitting to invented scores.
- Season simulation uses 10,000 runs; advice uses 5,000 paired runs with stateless common
  random numbers. Marginal recommendations display uncertainty. Numerical precision
  does not measure uncertainty in team parameters, the data or competition assumptions.
- Split fixtures and 50:50 venues are conditional, not published. Current official rules,
  tie-breakers and European access could not be verified. Assumed ranking is points,
  GD and goals scored; exact ties use provisional display order / sampled simulation
  order. The sixth/seventh boundary cannot be crossed after the split.

## Project map and exports

| Path | Purpose |
|---|---|
| `web/template.html`, `all-clubs.html`, `style.css`, `overrides.css` | Separate offline pages and shared compact design |
| `web/engine.js` | Browser inference, joint distributions, paired season simulation |
| `web/ui.js` | Offline interactions and downloads |
| `src/oval/` | Import, quality checks, fitting, evaluation, build and update CLI |
| `data/raw/`, `data/canonical/` | Separate supplied source extract and canonical records |
| `reports/` | Protocol, frozen selection, learned coefficients/diagnostics, evidence |
| `exports/` | CSV audit, coverage, comparison, calibration, hyperparameters, formbook, forecasts |
| `tests/` | Unit, numerical, parity and DOM integration checks |

Historical CSVs include reconstructed prediction timestamps, model versions, training
counts, cut-offs and eligibility reasons. Brier is the **summed three-class** score
(0–2), log loss uses a 1e-15 stability floor. Calibration bands pool H/D/A class
observations; counts below 20 are sparse. Historical exact-score and custom metrics
are N/A for native Elo/frequency. `formbook_analysis.csv` has pre-date ranks, rank
confidence and original momentum pulses. `forecast_table.csv` identifies the hybrid.
The browser's scenario export additionally labels locks as hypothetical.

Create a portable ZIP without virtual environments, dependencies, cache or Git history:

```sh
python scripts/package.py
```

The ZIP contains both offline HTML pages, sources, baseline, documented data, reports,
CSV exports and tests. No external fonts, badges or third-party artwork are bundled.
Source/data licensing is not inferred from the user-supplied files; see provenance.
