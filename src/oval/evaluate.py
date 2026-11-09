"""Predeclared rolling validation; freeze choice before scoring final test."""
import json
import math

import numpy as np

from .data import ROOT, write_csv, write_json
from .models import custom_points, fit, forecast, outcome

KINDS=['baseline','poisson','dc','elo','frequency']


def score(pred, match):
    p=np.array([pred['p_home'],pred['p_draw'],pred['p_away']]); y=outcome(match)
    target=np.eye(3)[y]
    return dict(brier=float(((p-target)**2).sum()),log_loss=-math.log(max(1e-15,float(p[y]))),
                correct_outcome=int(np.argmax(p)==y),
                exact_score=None if pred.get('best_score') is None else int(pred['best_score']==[match['hg'],match['ag']]),
                custom_100=custom_points(pred,match['hg'],match['ag']))


def metrics(rows):
    if not rows: return None
    mean=lambda k: float(np.mean([r[k] for r in rows if r[k] is not None])) if any(r[k] is not None for r in rows) else None
    return dict(matches=len(rows),first_date=min(r['date'] for r in rows),last_date=max(r['date'] for r in rows),
                brier=mean('brier'),log_loss=mean('log_loss'),outcome_hit_rate=mean('correct_outcome'),
                exact_score_hit_rate=mean('exact_score'),custom_100=mean('custom_100'))


def baseline_predictions(raw, results):
    lookup={(m['date'],m['homeClub'],m['awayClub']):m for m in raw['audit']}
    forecasts={}
    for m in results:
        old=lookup[m['date'],m['home'],m['away']]
        forecasts[m['id']]=dict(model_id='baseline',model_version='oval-v3-frozen',
            trained_through=max((x['date'] for x in results if x['date']<m['date']),default=None),
            training_sample_size=sum(x['date']<m['date'] for x in results),
            p_home=old['home'],p_draw=old['draw'],p_away=old['away'],
            expected_home_goals=old['expectedHome'],expected_away_goals=old['expectedAway'],best_score=old['bestScore'])
    return forecasts


def run_evaluation(raw, results, names):
    protocol=json.loads((ROOT/'reports/evaluation-protocol.json').read_text())
    windows=protocol['validation_windows']; test_start,test_end=protocol['final_test']
    is_validation=lambda d:any(a<=d<=b for a,b in windows)
    configurations={k:[dict(penalty=p,half_life=h) for p in protocol['goal_penalties'] for h in protocol['goal_half_life_days']]
                    for k in ['poisson','dc']}
    configurations['elo']=[dict(K=k) for k in protocol['elo_K_candidates']]
    configurations['frequency']=[{}]
    dates=sorted({m['date'] for m in results})
    cache={}; search=[]; best={}; chosen_rows={}
    def predict_date(kind, config, day):
        key=(kind,json.dumps(config,sort_keys=True),day)
        if key not in cache:
            history=[m for m in results if m['date']<day]
            model=fit(kind,history,names,config)
            cache[key]={m['id']:forecast(model,m['home'],m['away'],include_grid=False)
                        for m in results if m['date']==day}
        return cache[key]
    # Only validation fixtures are touched until this entire search and selection finishes.
    for kind, configs in configurations.items():
        candidates=[]
        for config in configs:
            rows=[]
            for day in dates:
                if not is_validation(day): continue
                if sum(m['date']<day for m in results)<protocol['minimum_training_matches']: continue
                predictions=predict_date(kind,config,day)
                rows.extend(dict(date=m['date'],**score(predictions[m['id']],m)) for m in results if m['date']==day)
            summary=metrics(rows)
            search.append(dict(model_id=kind,configuration=json.dumps(config,sort_keys=True),**summary))
            candidates.append((summary['log_loss'],config,rows))
        _,best[kind],chosen_rows[kind]=min(candidates,key=lambda x:x[0])
    validation={k:metrics(v) for k,v in chosen_rows.items()}
    best_loss=min(v['log_loss'] for v in validation.values())
    production=next(k for k in ['frequency','poisson','elo','dc'] if validation[k]['log_loss']<=best_loss+.01)
    goal_choice=min(['poisson','dc'],key=lambda k:validation[k]['log_loss'])
    selection=dict(production_model=production,goal_model=goal_choice,configurations=best,
                   validation=validation,selection_frozen_before_test=True,
                   rationale=protocol['selection'],final_test=protocol['final_test'])
    write_json(ROOT/'reports/frozen-selection.json',selection)
    # Selection persisted before final-test predictions or metrics are computed.
    predictions={'baseline':baseline_predictions(raw,results)}
    for kind in configurations:
        predictions[kind]={}
        for day in dates:
            if sum(m['date']<day for m in results)<protocol['minimum_training_matches']: continue
            predictions[kind].update(predict_date(kind,best[kind],day))
    audit=[]; export=[]; coverage=[]
    for m in results:
        entry=dict(m,models={})
        for kind in KINDS:
            p=predictions[kind].get(m['id'])
            reason='' if p else f"Fewer than {protocol['minimum_training_matches']} earlier supplied results; no verified earlier seasons"
            coverage.append(dict(fixture_id=m['id'],date=m['date'],model_id=kind,eligible=bool(p),reason=reason))
            common=dict(fixture_id=m['id'],date=m['date'],home=m['home'],away=m['away'],actual_home=m['hg'],actual_away=m['ag'],model_id=kind,
                        forecast_type='reconstructed; never published pre-kick-off',prediction_timestamp=m['date']+'T00:00:00 Europe/Belfast (reconstruction)',
                        period='final_test' if test_start<=m['date']<=test_end else 'validation' if is_validation(m['date']) else 'development',
                        eligible=bool(p),exclusion_reason=reason)
            if p:
                s=score(p,m); entry['models'][kind]=dict(**p,**s)
                export.append(dict(**common,model_version=p['model_version'],trained_through=p['trained_through'],training_sample_size=p['training_sample_size'],
                    p_home=p['p_home'],p_draw=p['p_draw'],p_away=p['p_away'],
                    expected_home_goals=p.get('expected_home_goals'),expected_away_goals=p.get('expected_away_goals'),
                    predicted_score='–'.join(map(str,p['best_score'])) if p.get('best_score') else '',**s))
            else:
                entry['models'][kind]=dict(unavailable=reason)
                export.append(dict(**common,**{k:None for k in ['model_version','trained_through','training_sample_size','p_home','p_draw','p_away',
                    'expected_home_goals','expected_away_goals','predicted_score','brier','log_loss','correct_outcome','exact_score','custom_100']}))
        audit.append(entry)
    common_ids={m['id'] for m in results if all(m['id'] in predictions[k] for k in KINDS)}
    comparison=[]; calibration=[]
    for period in ['validation','final_test','all_common']:
        for kind in KINDS:
            rows=[r for r in export if r['model_id']==kind and r['fixture_id'] in common_ids and (period=='all_common' or r['period']==period)]
            comparison.append(dict(period=period,model_id=kind,**metrics(rows)))
            for lo in np.arange(0,1,.1):
                cells=[]
                for r in rows:
                    actual=next(m for m in results if m['id']==r['fixture_id'])
                    for i,key in enumerate(['p_home','p_draw','p_away']):
                        if min(9,int(r[key]*10)) == int(round(lo*10)):
                            cells.append((r[key],int(outcome(actual)==i)))
                calibration.append(dict(period=period,model_id=kind,band_low=round(float(lo),1),band_high=round(float(lo+.1),1),
                    count=len(cells),predicted_mean=float(np.mean([x[0] for x in cells])) if cells else None,
                    observed_rate=float(np.mean([x[1] for x in cells])) if cells else None,sparse=len(cells)<20))
    # Paired date-block bootstrap: differences candidate minus baseline; negative is better.
    test=[r for r in export if r['period']=='final_test' and r['fixture_id'] in common_ids]
    days=sorted({r['date'] for r in test}); rng=np.random.default_rng(protocol['seed'])
    resamples=rng.integers(0,len(days),size=(2000,len(days)))
    intervals={}
    for kind in KINDS[1:]:
        intervals[kind]={}
        for metric in ['brier','log_loss']:
            sums=[]; counts=[]
            for day in days:
                base={r['fixture_id']:r for r in test if r['date']==day and r['model_id']=='baseline'}
                diffs=[r[metric]-base[r['fixture_id']][metric] for r in test if r['date']==day and r['model_id']==kind]
                sums.append(sum(diffs));counts.append(len(diffs))
            bs=np.array(sums)[resamples].sum(axis=1)/np.array(counts)[resamples].sum(axis=1)
            intervals[kind][metric]=dict(mean=float(sum(sums)/sum(counts)),low=float(np.quantile(bs,.025)),high=float(np.quantile(bs,.975)),blocks=len(days))
    report=dict(selection=selection,comparison=comparison,calibration=calibration,paired_test_intervals=intervals,
                coverage=dict(total=87,common=len(common_ids),excluded=87-len(common_ids)),
                improvement='inconclusive/not demonstrable: small single-season reconstructed holdout and unverified source data')
    write_csv(ROOT/'exports/historical_predictions.csv',export)
    write_csv(ROOT/'exports/coverage.csv',coverage)
    write_csv(ROOT/'exports/model_comparison.csv',comparison)
    write_csv(ROOT/'exports/calibration.csv',calibration)
    write_csv(ROOT/'exports/hyperparameter_search.csv',search)
    write_json(ROOT/'reports/evaluation.json',report)
    write_json(ROOT/'data/canonical/audit.json',audit)
    return report,audit
