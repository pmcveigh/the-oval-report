# Codex task: Recreate and upgrade The Oval Report

You are a senior full-stack engineer, football data engineer and applied statistician. Build a complete, working, reproducible version of **The Oval Report**, a Glentoran FC / Northern Ireland Premiership intelligence dashboard. Do not give me a concept, wireframe, prototype, pseudocode or implementation plan in place of the finished application. Implement it, obtain and validate data where access permits, run the tests, inspect the rendered UI, and deliver the working files and an honest evaluation report.

## Reference files and overriding constraints

Inspect the supplied `The_Oval_Report.html`, `The_Oval_Report_Accuracy_Audit.csv` and `The_Oval_Report_Formbook_Audit.csv` before changing anything. They are the reference for layout, UI behaviour, source data and the **existing prediction model**, which must remain available as an unchanged, versioned baseline. If the files are not present, reconstruct the features described below, but explicitly state that you cannot truthfully reproduce or compare against the exact old baseline without the source; do not invent its coefficients or outputs. Where the supplied source conflicts with this brief, use this brief for new requirements but retain the established design and functions unless explicitly superseded.

The project must produce a **downloadable, self-contained HTML dashboard** named `The_Oval_Report.html` that can be opened locally in Chrome, Firefox and Edge without installing anything or requiring an internet connection. You may use a Python data/modelling/build pipeline and modular source files, but bundle all essential CSS, JavaScript and data into the final HTML. Implement an explicit regeneration command that updates the source dataset and rebuilds the dashboard; no pretending that an offline file receives live updates. Also deliver the maintainable source project, data provenance, tests, exported audit files and a README with exact run/build instructions. Prefer British English and UK/Belfast dates and times.

**Never fabricate fixtures, historic scores, league standings, performance metrics, backtest predictions, sources, data coverage or test results.** If any data are unavailable, retain the visible feature with an honest 'unavailable' state and document the gap. Do not silently use simulated results where an actual result is implied.

## 1. Identity, aesthetic and layout

Keep the name **THE OVAL REPORT** only. Do not add 'Independent', 'Archive', generic ChatGPT branding or prominent archive disclaimers. Retain the bespoke matchday-poster / sports-editorial design: deep Glentoran green, red, warm cream, strongly contrasted sections, compact statistics, angular composition, restrained borders, oversized but readable match typography and clear desktop/mobile layouts. Use a readable system font stack or bundle an appropriately licensed typeface. Avoid a generic rounded-card SaaS design.

The hero displays **NEXT LEAGUE GAME** with the full home and away club names each on **one line** at supported viewport widths; label the sides **Home** and **Away** (not Visitors). Show date, day of week, kick-off time, venue, latest league result and suitable verified official links. Use **Last League Game**, not 'Previously / Full-time'; **Next Game / [weekday]**, not 'Kick-off / Friday'. Keep cup competitions separately labelled and out of league standings, momentum and league projections. Clearly display data-as-of time as neutral metadata, not an archive notice.

Make the site keyboard accessible and mobile responsive. All controls must work, including horizontal/vertical navigation, scenario selectors, predictions, export links and mobile tables. No horizontal page overflow. Use semantic HTML, accessible labels and adequate colour contrast.

## 2. Existing features to reproduce and preserve

1. **Matchday hero:** next official Premiership fixture; previous completed league match; venue/time; full-line club names; verified official ticket/fixture links if available.
2. **Match intelligence:** for the next Glentoran match and the preceding league match, display opponent strength, modelled goal expectations, home/draw/away probabilities, likely score, expected points and recent form. The retrospective panel must use the precise information available before the previous fixture, not today's ratings.
3. **Current league table:** all 12 clubs, P/W/D/L/GF/GA/GD/points, correct tie-break order; highlight Glentoran. Hypothetical results alter the scenario table without overwriting the factual table.
4. **Who Do We Want?:** exactly three objectives/tabs — **League Title (1st)**, **2nd (Direct Europe, subject to current rules/licensing)**, and **3rd**. Remove all 4th/5th/6th tabs. Compare every possible result of relevant other league fixtures by the *change in probability of Glentoran finishing in that exact position*. Indicate preferred home win, draw or away win, the delta in percentage points, and uncertainty when effects are marginal. Avoid hard-coded club allegiances or hand-written preferences. Use paired/common random numbers across alternative scenarios so Monte Carlo noise does not dominate the delta.
5. **Projected final league table:** simulated expected points, finishing-position probabilities and uncertainty ranges for every club; Glentoran title, 2nd, 3rd and top-six probability where useful.
6. **Match prediction centre:** every verified published remaining Premiership fixture, not merely Glentoran games; modelled 1/X/2 probabilities, expected points, expected goals where supported and most likely score where supported; filters for club/round/date.
7. **Scoreline matrix:** display score probabilities, including a meaningful 'other scorelines' tail rather than normalising a truncated 0–5 grid as if it were exhaustive.
8. **Run-in difficulty:** each club's remaining confirmed opponents, opponent strength, home/away context, expected points per match, total expected points and difficulty rank. Clearly distinguish *confirmed pre-split fixtures* from conditional post-split fixtures.
9. **The Formbook / Last 10 League Matches:** actual last ten league results, W/D/L, GF/GA, opponents, historical league position at the time, form trends and momentum 0–100. The last three matches should collectively carry approximately 69% of the indicator's temporal weight. Wins always contribute positive momentum, even for an already-strong team. Draws should normally add momentum only against stronger opponents; weaker-opposition draws should be neutral or adverse. Explicitly reward convincing recovery after a setback (bouncebackability), and penalise another poor result following a rebound, with coefficients fixed and documented. Use *opponents' league positions immediately before those matches*, constructed without looking ahead to same-day outcomes. Label provisional early-season positions appropriately. Keep this **descriptive indicator separate from predictive model covariates** unless a pre-declared, held-out ablation proves it improves forecast quality; no untested 'momentum boost'.
10. **Historical prediction accuracy audit:** retain all 87 Premiership fixtures in the provided 2026/27 audit through 7 November 2026, with date, teams, forecast before the fixture, actual score, 1/X/2 probability, most-likely score, model version, information cut-off, custom /100 accuracy points and probability metrics. A fixture must remain visible even if a particular model lacks a valid historical forecast. Include the existing custom points rubric as a secondary reporting measure; inspect and preserve its exact implementation from the supplied HTML rather than silently changing it. Its documented maximum assigns 35 for correct 1/X/2 outcome, 20 per exact team goals, 10 for correct goal difference and 15 exact-score bonus (100 maximum). If source code handles partial credit differently, identify and preserve that actual rule. Do not retroactively 'fix' scores after inspecting the results.
11. **Post-split explorer:** the standard 33-match first phase and five post-split fixtures between clubs in the top/bottom six, totalling 38; simulate who makes each group, and generate only *conditional/provisional* post-split match-ups until published. Handle confirmed post-split venues/fixtures exactly once known. Enforce the correct league competition rules and tie-breakers after verifying them.
12. **Dynamic points targets:** probabilistic points thresholds for 1st, 2nd, 3rd and top six derived from season simulations, not arbitrary fixed numbers; show quantiles and explain why thresholds are not guarantees.
13. **League odds and scenarios:** finish-position distribution from a sufficiently converged Monte Carlo season simulator; user-selected result locks update all relevant dependent panels coherently. Allow scenario reset. A saved or hypothetical score must never become an official result.
14. **Cup separation:** any Irish Cup, League Cup or other competition fixtures must sit in a separate area and never leak into Premiership training data unless a clearly documented experiment explicitly uses them.
15. **Exports:** downloadable CSV for all historical predictions, model comparison, formbook analysis and forecast tables, with definitions and relevant version/cut-off metadata.

Use the supplied dashboard as the design-and-behaviour reference, not merely the information in this brief.

## 3. Upgrade the prediction engine: opposition-adjusted attack and defence

Replace simple goals-per-game ratings and arbitrary hand-set strength corrections *in the new candidate models* with **jointly fitted team attack and defence** from match scores. A team's scoring is judged relative to the defence faced; conceding to a strong attack is not treated like conceding to a weak attack.

Implement a regularised **log-linear Poisson goal model**, for example:

- `log(lambda_home) = league_intercept + home_advantage + attack[home] - defence[away]`
- `log(lambda_away) = league_intercept + attack[away] - defence[home]`

Document all sign conventions. Impose identifiable constraints such as sum-to-zero team effects, and apply a coherent, fitted shrinkage penalty / prior so that short samples are stable. Carefully handle small samples, zero goals, promoted/new clubs and changing club identities. Treat the original dashboard model as frozen baseline, not something to rewrite to look like the new model.

## 4. Learn coefficients from verified historic results

Acquire and cross-check several completed seasons of Northern Ireland Premiership results if available, plus 2026/27 to the dated snapshot. Prefer official NIFL and club records; use reputable alternative historical fixture sources where appropriate. For each season record the source URL, retrieval date, data licence/access notes, match coverage, postponed/replayed games, any discrepancy resolutions and known gaps. Keep raw source extracts separate from normalised canonical match records. Never substitute assumed or invented results.

Fit rather than hand-set, using chronological training/validation:

- League scoring baseline / intercept.
- Home advantage.
- Attack and defence ratings.
- **Recency decay** (older observations gradually lose weight).
- Regularisation/shrinkage strength.

Explain season boundaries, promoted clubs, clubs without history, withdrawn/rebranded clubs and the transition from historical seasons to 2026/27. Do not allow the present or future league table, score or season total to influence a past forecast. Prefer weighted penalised likelihood with an explicit, auditable optimisation process, numerical diagnostics, reproducible seeds and documented convergence criteria. If historical data collection proves inadequate, implement only the models genuinely supported by the available dataset and state limitations prominently in the engineering report and comparison table, rather than making up coverage.

## 5. Dixon–Coles model

Add a **Dixon–Coles low-score correction** on top of the fitted Poisson intensities, modifying exactly the 0–0, 1–0, 0–1 and 1–1 outcomes using the documented Dixon–Coles `tau` formulation. Estimate `rho` from the training data, constrained to the valid region for every intensity in the fitted dataset and prediction set (or use a mathematically safe reparameterisation). Test that every cell is non-negative, the distribution is finite and its total mass is one to numerical tolerance. Use an adaptively large goal grid or explicitly track the omitted high-score tail. Never silently force a tiny grid to sum to 100%.

Derive 1/X/2, expected points, exact scores, expected goals, BTTS/clean-sheet/over-under probabilities (where displayed) from the **same properly normalised joint distribution**. Retain the fitted **independent Poisson** as a separate comparison model. Do not presume Dixon–Coles is superior.

## 6. Elo as a separate competing model

Implement chronological Elo, with fitted home advantage and fitted rating-update rate `K`. Convert rating difference to **valid three-way home/draw/away probabilities** with a documented fitted draw-aware method (for instance a Davidson/Bradley–Terry draw extension). Include rating initialisation, prior-season carry-over or regression to league mean, promotion handling and season transitions. Each matchday's fixtures must be predicted using ratings available **before any result from that date is processed**; only afterwards apply updates, consistently across all models and the audit.

Fit all Elo hyperparameters on the permitted training/validation periods. Do not invent Elo exact-score probabilities: only present exact scores or goal-market forecasts if a separately fitted goal model supplies them, visibly labelled with that goal model's name and version. If Elo wins the 1/X/2 comparison, make the dashboard transparent about any hybrid use of a separate goal model for scorelines and goal-difference tie-breakers during season simulation.

## 7. Honest chronological evaluation and selection

Evaluate on the **same eligible fixtures**:

1. The existing Oval Report model, preserved unchanged as an explicit versioned baseline.
2. Fitted opposition-adjusted independent Poisson.
3. Fitted Dixon–Coles.
4. Fitted draw-aware Elo.
5. A simple home/draw/away frequency baseline using **earlier results only**, with documented smoothing for short histories.

Use multiple **rolling chronological training and validation windows**, then a **final untouched test period** selected *before* looking at its performance. Select coefficients, hyperparameters and candidate production model on training/validation only. Freeze that selection before the final test is scored. In a walk-forward test, a later fixture may incorporate earlier observed results, but never results or table states from its own or a future date. Predict a whole calendar date before ingesting that day's results. Record each fixture's model-fit data cut-off, prediction timestamp (or reconstructed timestamp), model version and training sample size. Distinguish reconstructed backtests from truly pre-kick-off published prediction snapshots. Never call reconstructed predictions 'live historical predictions'.

Report, per model and on the same common subset:

- Matches evaluated and exact date/season coverage, plus exclusions or missing predictions by fixture and reason.
- **Summed three-class Brier score**, `sum((p_home-y_home)^2 + (p_draw-y_draw)^2 + (p_away-y_away)^2) / N`, range 0–2, lower better.
- Mean three-way log loss, using a documented numerical floor strictly for stability.
- Predicted-outcome hit rate based on the highest 1/X/2 probability.
- Calibration in probability bands **with sample counts**, with separate or pooled class analysis and a reliability visualisation; flag sparse bins.
- Exact-score hit rate for score-producing models only.
- The existing custom /100 score for score-producing models as a **secondary** metric, not model-selection objective.
- Appropriate uncertainty intervals / date-block bootstrap where sample sizes permit.

Keep all **87 originally audited matches visible**, even when a model cannot forecast them. Provide a fair all-87 comparison where historical pre-match data support it; otherwise report a labelled **common comparison subset** and the full coverage matrix. Do not silently drop early-season matches, difficult matches, losses or draws. Do not optimise against the final test results. Include the simple historical-frequency baseline to establish whether complexity actually helps.

Pick the production model primarily by **held-out probability quality**, considering both Brier and log loss, plus calibration and coverage. Report outcome hit rate separately. If scores are similar or uncertainty intervals overlap, prefer the better calibrated and/or simpler robust model and explicitly describe the inconclusive evidence. Do not promise that a more complex model must win or assert improved accuracy without the held-out measurements. Show model selection rationale in plain English.

**Important baseline discipline:** the frozen existing dashboard is a historical point of comparison, not a parameter source to be secretly retuned after seeing the 87 results. If the baseline implementation or data cut-offs cannot be exactly reconstructed, report that constraint rather than claiming an equal all-match comparison.

## 8. One shared prediction engine and dashboard integration

Implement a single tested forecast interface returning (as supported) `model_id`, `model_version`, `trained_through`, `P(home)`, `P(draw)`, `P(away)`, `expected_home_goals`, `expected_away_goals`, `expected_points_home`, `expected_points_away`, and a **normalised score distribution**. The backtest, match previews, scoreline matrix, 'Who Do We Want?' scenarios, run-in difficulty and season simulator must call the *same underlying algorithm/version*, not independent hand-coded approximations or stale precalculated figures mislabelled as live.

If the production model is Elo, use Elo for 1/X/2 and expected points, and a clearly attributed separate fitted goal model for score distributions. Identify every hybrid output. Use shared serialised fitted parameters and strict Python-vs-browser golden tests if inference exists in both runtimes. A sensible architecture is Python for data acquisition, fitting, walk-forward evaluation and export; lean vanilla HTML/CSS/JavaScript for offline presentation and scenario simulation, with build-time bundling. Do not rely on third-party CDNs or external font fetches for basic offline operation.

Season simulations must use all **verified published remaining league fixtures** for the correct 2026/27 schedule, account for unplayed/postponed fixtures according to their actual status, calculate the 33-match standings, generate conditional five-match split-group schedules, then calculate the 38-match finish. Validate league-specific ranking and European-qualification rules against contemporaneous authoritative sources. The actual published post-split schedule, if eventually available, supersedes provisional scheduling. All expected-points displays must use `3 * P(win) + P(draw)`, with the relevant club's perspective.

When a user locks a hypothetical result, update the scenario table, candidate probabilities, fixtures/difficulty, projected standings, target points and the preferred-results guide consistently. Different scenario evaluations should use **common random numbers**, sufficient simulation draws and numerical uncertainty thresholds so advice does not flip because of sampling noise. Surface high-uncertainty cases honestly. Keep actual results immutable. Use deterministic seeds and versioned model/simulation metadata.

Keep the **Formbook momentum indicator independent** of core prediction unless a pre-specified momentum-augmented candidate is tested on chronological validation and a never-touched final holdout against the otherwise identical model. If there is no credible improvement, leave momentum as a descriptive panel only; do not stealthily feed it into predictions.

## 9. Robustness, tests and build quality

Write automated unit, integration, end-to-end, numerical and data-quality tests. At minimum verify:

- No duplicated fixtures, incorrect clubs/competitions, future results leaking into past cut-offs, invalid dates or mismatched score totals.
- Reconstruction of every official completed-season table from canonical league results; reconcile the existing 87-match 2026/27 snapshot exactly if the reference dataset is trustworthy, otherwise list specific discrepancies and supporting sources.
- No same-day leakage in any model, especially Elo and Formbook positions; correct handling of postponements and rescheduled match dates.
- Identifiability and finite estimates in the fitted attack/defence model; credible shrinkage for small samples and newly promoted clubs.
- Dixon–Coles low-score probability adjustments, non-negativity, tail handling, normalisation and valid `rho` constraints under edge cases.
- Each match's 1/X/2 probabilities sums to one; expected points and goal-market probabilities agree with the same distribution.
- Equal fixture eligibility and recorded data cut-offs across evaluation models; no retroactive tuning or look-ahead in held-out tests.
- Reproducible results from a pinned dataset/version/random seed, with fit and simulation convergence diagnostics.
- Exactly three preferred-result tabs (1st, 2nd, 3rd); correct handling of draw-preferred results, zero/negative deltas and uncertain differences.
- Scenario result selection, state reset, export integrity, accurate league-split handling and correct remaining-match counts.
- Mobile/desktop rendering, readable one-line team names, functional tabs, accessible navigation and no page overflow.
- Historic audit and new predictions match the very same inference functions used for displayed forecasts. Include golden-test fixture cases with stable expected values.

Do not call a browser interaction 'tested' unless it was run. Use Playwright or a comparable browser test where available and record what succeeded or failed.

## 10. Deliverables and completion criteria

Deliver all of the following:

1. **`The_Oval_Report.html`** — complete standalone offline dashboard, matching the reference visual language and including all old and new features.
2. **Maintainable source project** with a reproducible install, data fetch/update, fit, test and build workflow; pinned dependencies and deterministic seeds.
3. **Documented canonical results/fixtures data** with source URLs, fetched-at timestamps, coverage table, known gaps and integrity checks. Do not embed unlicensed third-party assets.
4. **Full historical audit**, retaining the 87 existing matches, pre-match projections, predicted versus actual outcomes, custom /100 scoring and each model's eligibility/coverage; provide CSV exports.
5. **Model comparison and calibration report** showing the frozen baseline, fitted independent Poisson, Dixon–Coles, Elo and historical-frequency baseline, with identical-fixture comparison and a final untouched test. Include learned coefficients/hyperparameters, test-window cut-offs and selection rationale.
6. **Summary of what changed**, concrete validation/test results, known limitations and a direct answer to **'Did held-out predictive performance improve?'** supported by numbers, or 'inconclusive/not demonstrable' if that is what the evidence shows.
7. **A ZIP bundle** containing the HTML, reports, CSVs and source as appropriate for downloading and transferring to another machine.

Work end to end using tools available in the environment. Start by inspecting the supplied reference files and verifying the available source data, then implement and test. Do not stop at an architecture outline; do not ask me to supply data that you can obtain legitimately yourself. If an external source or package is unavailable, make a truthful, usable partial implementation and describe the exact missing capability, with no fake metrics or claims of success.
