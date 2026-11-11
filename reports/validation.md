# Dashboard redesign validation — 11 November 2026

The earlier model-validation record is retained below. Its browser limitation is
superseded for HTTP rendering by these checks; local-file browser restrictions remain.

- Rebuilt both offline pages and the `dist/` pair. Exact byte reproducibility now
  checks both generated HTML files and the hosted return URL.
- Python: all 10 existing pipeline tests passed. Numerical JavaScript: all 660
  golden cases passed, maximum error 6.661338147750939e-15; simulation determinism,
  immutable factual records and paired result changes still pass.
- Updated jsdom integration passed for both pages. All 87 historical matches,
  including 21 early unavailable candidate forecasts, and all 111 remaining fixtures
  are reachable through pagination. The main record and selectors are Glentoran-only.
  Filters, sorting, three scenario objectives, coherent projections, reset, form,
  score matrix, all tab links and eight CSV downloads passed.
- Playwright with `/usr/bin/chromium`: required next-fixture, prediction, chances,
  latest-result, form, position, points and goal-difference elements all fit above
  the fold at 1366 × 768 and 1920 × 1080.
- Every tab on both pages checked at 1366, 768, 390 and 320 px. No page-wide
  horizontal overflow or primary-content vertical scroll panes were found.
  Dense mobile tables use row layouts or expandable detail, retaining their data.
- Direct HTTP URLs, hash links, return links, hosted `dist/index.html` navigation,
  shared assumed results, club/date filters and empty filter results passed.
- Information buttons passed hover, keyboard focus, visible focus, Enter, Escape,
  close-button focus return, outside-click and emulated touchscreen tap tests.
  The touch explanation's bounds fit the viewport and its close button works.
- Empty fixtures display unavailable next-match, score and season forecasts without
  inventing data. An injected calculation failure produces a visible error message.
- Screenshots in `work/browser/` were visually inspected, including both desktop
  sizes, mobile overview, model comparison, prediction record, form, forecast,
  score chances and the touch explanation. Visual review led to fixes for narrow
  screens and compact table captions. The browser run reported no unexpected JS errors.
- `git diff --check` and portable packaging passed. Both HTML pages are included
  in the ZIP and CI artifact list. The engine, source data, fitted parameters,
  historical records, baseline and CSV exports have no redesign changes.

Limitations: this managed Chromium policy rejects `file://` navigation with
`ERR_BLOCKED_BY_ADMINISTRATOR`. Both pages work over static HTTP and embed all
required resources, but direct local-file browsing remains unverified here. Firefox,
Safari, physical touchscreen devices and independent verification of the supplied
snapshot / league rules were outside these checks. No data refresh or model retuning
was performed.

---

# Validation record — 9 November 2026

Environment: Python 3.12.14, Node 24.22.1, NumPy 2.3.5, SciPy 1.17.0.
Inputs: frozen supplied v3 HTML, accuracy CSV and Formbook CSV; SHA-256 recorded in
`data/canonical/manifest.json`. Deterministic seed: 20261109.

## Checks run

`PYTHONPATH=src OPENBLAS_NUM_THREADS=1 python -m unittest discover -s tests -v`

**10 tests passed**, covering:

- All 87 original forecast probabilities, goal expectations, predicted scores, Brier
  scores and custom points reproduced from the unchanged baseline algorithm.
- All 174 Formbook pre-date ranks, pulses and momentum indices match the supplied CSV.
- All 12 factual table rows reconcile; 87 completed + 111 remaining fixtures give
  exactly 33 first-phase games per club and three games for each unordered club pair.
- Duplicate IDs, invalid snapshot dates, wrong competitions and unsupported clubs
  rejected; same-date information cut-offs and candidate eligibility agree.
- Identifiable finite goal estimates, zero-goal short samples, unseen-in-training
  clubs with known identity, regularisation and model reproducibility checked.
- Valid Dixon–Coles tau and normalisation over every ordered club pair; numerical
  tails, visible matrix tails, expected points and hybrid market consistency checked.
- Frozen custom-score override, Elo date-batched updates and exact build-byte
  reproducibility checked. CSV audit has 435 rows (87 × five models).

`npm test`

**660 Python/JavaScript golden cases passed** across all ordered club pairs and native
models / deployed hybrid. Maximum absolute numeric difference: 6.661338147750939e-15.
JavaScript integration also checks deterministic simulation, probability sums,
immutable factual data, fixed-seed reset and paired deltas (including zero/negative).

**DOM integration passed** in jsdom 26.1.0, executing the bundled HTML's real scripts
and event handlers. Covered three result-guide objectives, all 87 audit rows and 21
explicit early exclusions, locks/reset with coherent season projections, all 111
prediction rows and 333 scenario choices, club/date filters, fixture filters, Formbook
club selection, difficulty window, 36-cell matrix and tail, navigation targets,
accessible control names and eight CSV download actions. This is DOM integration,
not a visual browser or layout test. Tests load no external page resources.

`node --check web/engine.js`, `node --check web/ui.js`, Python compile checks and
`git diff --check` passed.

`PYTHONPATH=src OPENBLAS_NUM_THREADS=1 python -m oval evaluate` completed with the
committed protocol. Selection remains Elo; the final 19-fixture test did not demonstrate
an improvement. Exact metrics, date windows, per-fixture coverage, fitted coefficients,
optimisation diagnostics, calibration counts and paired uncertainty intervals are saved.

## Attempted browser checks — blocked

The managed `sites-preview start /workspace/the-oval-report` command failed:
`relay could not open browser port 4173: timed out waiting for relay readiness`.
`sites-preview status` then returned `Sites preview stopped`.

An attempt to open the standalone HTML in shared Chrome via the computer-use tool
was rejected by the browser URL policy: local `file:` URLs are prohibited; only HTTP
and HTTPS are permitted. No alternate browser surface, raw browser command, server
replacement or policy workaround was used.

Consequently **rendered desktop/mobile layout, one-line name fit, visual contrast,
horizontal overflow, keyboard focus behaviour and actual Chrome/Firefox/Edge local-file
operation remain unverified**. The source includes semantic labels, visible focus,
one-line hero CSS, narrow-screen layouts and scrollable tables, but those implementation
choices are not presented as successful rendering tests. No screenshot or video exists.

## External data/rules checks — unavailable

NIFL, Glentoran and Football-Data requests failed with proxy HTTP 403; exact URL/time
and errors are saved in `data/source-access.json`. An OpenFootball Northern Ireland
repository lookup returned not found. No authoritative current results, historical
seasons, official split allocation, tie-break rules or European qualification rules
were obtained. These remain explicit data/rules gaps. Internal reconciliation does
not establish that the supplied data are correct official records.

The packaged HTML makes no runtime network requests for essential content. Offline
capability is supported by static resource inspection and successful isolated DOM
execution, with actual local-file browser operation unverified as stated above.
