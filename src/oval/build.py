"""Build-time bundling, fitted parameters, forecast exports and evidence report."""
import csv
import hashlib
import json
import shutil
import urllib.request
from datetime import datetime, timezone

from .data import ROOT, extract_reference, formbook, import_data, validate, write_csv, write_json
from .evaluate import run_evaluation
from .models import fit, forecast

SOURCE_URLS=[
 'https://www.nifootballleague.com/premiership/2026-2027/',
 'https://www.glentoran.com/matches/fixtures/',
 'https://www.football-data.co.uk/new/NIR.csv',
]


def check_sources():
    """Record access honestly; raw responses are never silently accepted as match data."""
    observations=[]
    for url in SOURCE_URLS:
        row=dict(url=url,attempted_at=datetime.now(timezone.utc).isoformat(),status='unavailable')
        try:
            with urllib.request.urlopen(url,timeout=20) as response:
                content=response.read(10_000_000)
                filename=hashlib.sha256(url.encode()).hexdigest()[:12]+'.raw'
                (ROOT/'data/raw'/filename).write_bytes(content)
                row.update(status='fetched; review/normalisation required',raw_file=filename,bytes=len(content))
        except Exception as e:
            row['reason']=str(e)
        observations.append(row)
    write_json(ROOT/'data/source-access.json',observations)
    return observations


def build(results_path=None,fixtures_path=None,as_of=None,provenance_path=None,reevaluate=False):
    # Reference inputs and baseline evaluation never change during an update.
    if not (ROOT/'data/canonical/results.json').exists(): import_data()
    raw,original_results,original_fixtures=extract_reference()
    names=sorted(t['name'] for t in raw['table'])
    manifest=json.loads((ROOT/'data/canonical/manifest.json').read_text())
    if results_path or fixtures_path:
        if not all([results_path,fixtures_path,as_of,provenance_path]):
            raise ValueError('Updates require --results, --fixtures, --as-of and --provenance together')
        results=json.loads(results_path.read_text()); fixtures=json.loads(fixtures_path.read_text())
        provenance=json.loads(provenance_path.read_text())
        if not all(provenance.get(k) for k in ['source_urls','retrieved_at','licence_notes','coverage','discrepancies']):
            raise ValueError('Provenance requires source_urls, retrieved_at, licence_notes, coverage, discrepancies (use "none reported" if appropriate)')
        original_lookup={m['id']:m for m in original_results}
        current={m['id']:m for m in results}
        for key,m in original_lookup.items():
            if key not in current or any(current[key][k]!=m[k] for k in ['date','home','away','hg','ag','competition']):
                raise ValueError('Original audited matches must remain intact; corrections require a separate reviewed dataset version')
        table=validate(results,fixtures,names,as_of=as_of)
        manifest.update(snapshot_through=as_of,results=len(results),remaining=len(fixtures),
            imported_on=provenance['retrieved_at'],independently_verified=False,
            source_update=provenance,source_sha256=hashlib.sha256(results_path.read_bytes()+fixtures_path.read_bytes()).hexdigest())
        write_json(ROOT/'data/canonical/results.json',results);write_json(ROOT/'data/canonical/fixtures.json',fixtures)
        write_json(ROOT/'data/canonical/manifest.json',manifest)
    else:
        results=json.loads((ROOT/'data/canonical/results.json').read_text())
        fixtures=json.loads((ROOT/'data/canonical/fixtures.json').read_text())
        table=validate(results,fixtures,names,raw['table'] if len(results)==87 else None,manifest['snapshot_through'])
    if reevaluate or not (ROOT/'reports/evaluation.json').exists():
        evaluation,audit=run_evaluation(raw,original_results,names)
    else:
        evaluation=json.loads((ROOT/'reports/evaluation.json').read_text())
        audit=json.loads((ROOT/'data/canonical/audit.json').read_text())
    selection=evaluation['selection']; configurations=selection['configurations']
    models={k:fit(k,results,names,configurations[k]) for k in configurations}
    production=models[selection['production_model']]; goal_model=models[selection['goal_model']]
    write_json(ROOT/'reports/fitted-models.json',models)
    previous=max((m for m in results if 'Glentoran' in (m['home'],m['away'])),key=lambda m:m['date'])
    before=[m for m in results if m['date']<previous['date']]
    previous_models=dict(production=fit(selection['production_model'],before,names,configurations[selection['production_model']]),
                         goal_model=fit(selection['goal_model'],before,names,configurations[selection['goal_model']]))
    forms=formbook(results,names); write_csv(ROOT/'exports/formbook_analysis.csv',forms)
    forecasts=[]
    for f in fixtures:
        p=forecast(production,f['home'],f['away'],goal_model,False)
        forecasts.append(dict(fixture_id=f['id'],date=f['date'],home=f['home'],away=f['away'],status=f['status'],
            verification=f['verification'],**{k:p.get(k) for k in ['model_id','model_version','trained_through','training_sample_size',
            'p_home','p_draw','p_away','expected_points_home','expected_points_away','expected_home_goals','expected_away_goals','goal_model']},
            most_likely_score='-'.join(map(str,p['best_score'])),goal_method='outcome-reweighted conditional goal distribution; explicit hybrid'))
    write_csv(ROOT/'exports/forecast_table.csv',forecasts)
    # Golden fixtures cover every ordered club pair, all candidate families, and deployed hybrid.
    golden=[]
    for model_key in [*models,'deployed']:
        model=production if model_key=='deployed' else models[model_key]
        hybrid=goal_model if model_key=='deployed' else None
        for h in names:
            for a in names:
                if h==a: continue
                p=forecast(model,h,a,hybrid)
                keys=['p_home','p_draw','p_away','expected_points_home','expected_points_away',
                      'expected_home_goals','expected_away_goals','best_score','btts','over_25','other_scorelines']
                # Full grids for representative golden fixtures; all scalar outputs for every pair.
                if h=='Glentoran' and a=='Bangor': keys.append('score_distribution')
                golden.append(dict(model=model_key,goal_model=selection['goal_model'] if hybrid else None,
                                   home=h,away=a,expected={k:p[k] for k in keys if k in p}))
    write_json(ROOT/'tests/golden.json',dict(models=dict(models,deployed=production),cases=golden))
    payload=dict(table=table,results=results,fixtures=fixtures,formbook=forms,audit=audit,evaluation=evaluation,
                 production=production,goal_model=goal_model,previous=previous,previous_models=previous_models,manifest=manifest,
                 exports={p.name:p.read_text(encoding='utf-8-sig') for p in sorted((ROOT/'exports').glob('*.csv'))})
    write_json(ROOT/'data/canonical/dashboard.json',payload)
    template=(ROOT/'web/template.html').read_text()
    css=(ROOT/'web/style.css').read_text()+'\n'+(ROOT/'web/overrides.css').read_text()
    # Escaping prevents an imported club/source string terminating the inline JSON script.
    data_json=json.dumps(payload,separators=(',',':'),allow_nan=False).replace('<','\\u003c').replace('\u2028','\\u2028').replace('\u2029','\\u2029')
    output=template.replace('/* STYLE */',css).replace('/* DATA */',data_json).replace('/* ENGINE */',(ROOT/'web/engine.js').read_text()).replace('/* UI */',(ROOT/'web/ui.js').read_text())
    (ROOT/'The_Oval_Report.html').write_text(output)
    (ROOT/'dist').mkdir(exist_ok=True); (ROOT/'dist/index.html').write_text(output)
    engineering_report(evaluation,manifest)
    return payload


def engineering_report(report,manifest):
    rows=[r for r in report['comparison'] if r['period']=='final_test']; selection=report['selection']
    text='''# The Oval Report — engineering and model evaluation

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
'''
    for r in rows:
        exact='N/A' if r['exact_score_hit_rate'] is None else f"{100*r['exact_score_hit_rate']:.1f}%"
        custom='N/A' if r['custom_100'] is None else f"{r['custom_100']:.2f}"
        text+=f"| {r['model_id']} | {r['matches']} | {r['brier']:.4f} | {r['log_loss']:.4f} | {100*r['outcome_hit_rate']:.1f}% | {exact} | {custom} |\n"
    text+=f"\nCommon comparison coverage: {report['coverage']['common']}/87. All 87 rows remain visible for all five models.\n"
    for kind,v in report['paired_test_intervals'].items():
        ci=v['brier'];text+=f"\n{kind} minus baseline Brier: {ci['mean']:.4f}, paired 95% date-block interval [{ci['low']:.4f}, {ci['high']:.4f}]."
    text+='''

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
'''
    (ROOT/'reports/engineering-report.md').write_text(text)
