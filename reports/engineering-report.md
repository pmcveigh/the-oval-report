# The Oval Report — engineering and model evaluation

Held-out predictive performance improvement is **inconclusive / not demonstrable**.
The validation-selected Elo model performed slightly worse than the frozen baseline
on both probability metrics in the 19-fixture final test. Selection was retained;
the final test was not used to switch to Poisson or retune coefficients.

## Evaluation

Protocol was committed before candidate evaluation. Validation windows: 15–26 September
and 3–17 October 2026 (34 matches). Final test: 20 October–7 November (19 matches,
8 calendar-date blocks). All models forecast an entire date before ingesting that day's
results. Fits expand chronologically; later test dates may use earlier test results.
This is reconstructed single-season evaluation, not a prospective experiment.

| Model | N | Summed Brier (0–2) | Log loss | Outcome hit | Exact score hit | Custom /100 |
|---|---:|---:|---:|---:|---:|---:|
| baseline | 19 | 0.7209 | 1.1670 | 36.8% | 5.3% | 38.79 |
| poisson | 19 | 0.6678 | 1.0958 | 31.6% | 21.1% | 50.00 |
| dc | 19 | 0.6696 | 1.0969 | 31.6% | 10.5% | 40.16 |
| elo | 19 | 0.7273 | 1.2017 | 31.6% | N/A | N/A |
| frequency | 19 | 0.7176 | 1.1935 | 31.6% | N/A | N/A |

Common comparison coverage: 66/87. All 87 rows remain visible for all five models.

poisson minus baseline Brier: -0.0531, paired 95% date-block interval [-0.1691, 0.0379].
dc minus baseline Brier: -0.0514, paired 95% date-block interval [-0.1758, 0.0570].
elo minus baseline Brier: 0.0064, paired 95% date-block interval [-0.1109, 0.1010].
frequency minus baseline Brier: -0.0033, paired 95% date-block interval [-0.2076, 0.1625].

Intervals use 2,000 paired date-block bootstrap resamples with seed 20261109. Eight
blocks provide weak precision; none supports a reliable improvement claim. Poisson's
better test point estimate is exploratory. Calibration CSV and the offline reliability
visualisation include counts; bins below 20 pooled class observations are flagged sparse.
Outcome hit rate is reported separately and custom /100 is never a selection objective.

## Models and sign conventions

Goal rates: log λ_home = intercept + home advantage + attack_home − defence_away;
log λ_away = intercept + attack_away − defence_home. Positive defence reduces goals.
Both team vectors sum to zero exactly. Penalised weighted likelihood is fitted by
L-BFGS-B (max 1,000 iterations, ftol 1e-12, gtol 1e-7). The full team vectors receive
L2 shrinkage. League level and home advantage have weak proper priors to handle zero
goals and small samples. Unknown teams are rejected rather than silently aliased.
All supplied clubs start symmetrically; a club with no matches shrinks to the league
mean. No cross-season carry-over or promotion rule is claimed: historical seasons
were unavailable. A future multi-season import requires a predeclared identity and
season-transition policy before it can enter evaluation.

Half-life and penalty are selected on the declared rolling validation dates. Dixon–Coles
uses a documented two-stage fit: penalised Poisson intensities, then weighted conditional
rho maximum likelihood. It is not a fully joint Dixon–Coles optimiser. Tau changes exactly
00: 1−λhλaρ; 10: 1+λaρ; 01: 1+λhρ; 11: 1−ρ. Rho is constrained to the strict valid
region across **all ordered pairs** of fitted clubs. Adaptive goal tails are below 3e-12;
the omitted numerical mass is explicitly recorded, then rescaled at floating-point
precision. The visible 0–5 matrix separately reports all larger scorelines.

Elo uses the Davidson three-way probabilities proportional to exp(x), exp(log ν),
exp(−x), where x=(rating difference + fitted home advantage)×log(10)/800. K is selected
from validation; home advantage and draw weight maximise chronological training
likelihood. Updates use actual outcome points minus P(win)+0.5P(draw). All updates
for a calendar date commit together. Ratings initialise at zero (displayed as 1500).
Frequency uses earlier H/D/A counts plus a Dirichlet(1,1,1) prior.

Production uses Elo outcomes with DC **conditional** goal shapes. Each outcome block
of the goal grid is reweighted to the corresponding Elo probability. Expected goals,
exact scores, BTTS, clean sheets and totals come from that same hybrid grid. Elo has
no native exact-score metric in the historical comparison. All displayed forecasts,
score grids and season draws use the shared serialised model interface. Python and
JavaScript are checked across every ordered team pair. Parameters do not refit when
a hypothetical result is selected; that result changes season state, not factual data.

## Frozen baseline and formbook

`baseline/` preserves the supplied HTML and both CSVs unchanged. A Node extraction
executes its original backtest with DOM startup calls omitted. All 87 forecast
probabilities, scores and custom points are compared against the supplied accuracy CSV.
The rubric gives 35 for the plurality outcome, 20 per exact team score (8 if one off),
10 for exact margin (4 if one off). An exact-score override awards 100 even if plurality
outcome differs; otherwise the nominal 15-point exact bonus is not added separately.
This actual implementation, including its surprising override, is preserved.

Formbook positions are frozen before any result from a date is ingested. Early ranks
are provisional with confidence min(matches played by either side /4, 1). Fixed pulse
coefficients and bounceback/repeated-setback logic are ported from the reference,
checked against all 174 supplied formbook rows. Last-ten weights are
0.15,0.20,0.25,0.30,0.40,0.55,0.70,1.35,1.80,2.40: the last three carry 68.52%.
Wins have positive pulses; draws against weaker clubs are non-positive; recoveries
receive the original fixed bonuses. Momentum never enters any new predictive model.

## Scenarios, competition assumptions and gaps

All 111 supplied remaining pairings plus 87 results give exactly 33 matches per club.
Ten thousand deterministic season runs produce positions, ranges and points quantiles.
Five thousand paired runs per guide alternative use stateless common random numbers
keyed by run and fixture/pair. Pairing does not drift when a result lock changes.
Recommendation uncertainty is the standard error of paired exact-position indicator
differences. If the best/runner-up gap is within 1.96 standard errors or 0.2 percentage
points, advice is inconclusive. Split-half position differences and Monte Carlo margins
are displayed; neither measures data or model uncertainty.

Each first-phase simulation generates top/bottom six, then one conditional game per
pair within each group (five per club, 38 total). Venues are sampled 50:50; no official
venue balancing rule is asserted. Assumed ranking is points, GD, goals scored; unresolved
ties are sampled for simulation and provisionally ordered for display. Group boundaries
remain fixed after the split. Authoritative competition, tie-break and European access
rules could not be verified. Confirmed official post-split scheduling is not supported
by this supplied pre-split dataset; forecasts remain conditional and must be replaced
with a verified schedule adapter before using published post-split fixtures.

Official NIFL, Glentoran and Football-Data requests returned proxy HTTP 403. A public
OpenFootball Northern Ireland repository lookup also returned not found. No independently
verified prior seasons, complete-season table checks, source licences or contemporary
rules were obtained. The data are attributed to user-supplied files, not represented
as verified official records. Internal consistency is necessary but does not prove truth.
Official outbound links are labelled unchecked. Cup fixtures are separately marked,
never fitted or included in the league table, Formbook or simulations.

## Delivery and verification

The HTML bundles all CSS, JavaScript, data, CSV exports and model metadata. There are
no essential network requests, fonts or third-party assets. Build from `web/` and
`src/oval/`; see README for exact commands. Explicit regeneration imports validated
normalised JSON and source provenance; checking URLs alone never fabricates an update.
The forecast comparison stays frozen to the original audit when later data are imported.
Testing results and browser observations are recorded separately in `reports/validation.md`.
The final PR documents these outstanding data/rules limitations rather than claiming
that every external-data completion criterion has been met.
