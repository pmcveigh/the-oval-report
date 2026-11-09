import csv
import io
import json
import math
import subprocess
import unittest
from collections import Counter
from copy import deepcopy

import numpy as np

from oval.data import ROOT, WEIGHTS, extract_reference, formbook, validate
from oval.models import custom_points, fit, forecast, goal_rates, outcome, rho_bounds, tau


class PipelineTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.raw,cls.results,cls.fixtures=extract_reference()
        cls.names=sorted(t['name'] for t in cls.raw['table'])
        cls.report=json.loads((ROOT/'reports/evaluation.json').read_text())

    def test_table_and_schedule(self):
        self.assertEqual(len(self.results),87);self.assertEqual(len(self.fixtures),111)
        table=validate(self.results,self.fixtures,self.names,self.raw['table'])
        self.assertEqual(sum(t['p'] for t in table),174)
        pairs=Counter(tuple(sorted([m['home'],m['away']])) for m in self.results+self.fixtures)
        self.assertTrue(all(v==3 for v in pairs.values()))
        bad=deepcopy(self.results);bad.append(bad[0])
        with self.assertRaises(ValueError):validate(bad,self.fixtures,self.names)
        bad=deepcopy(self.results);bad[0]['date']='2030-01-01'
        with self.assertRaises(ValueError):validate(bad,self.fixtures,self.names)
        bad=deepcopy(self.results);bad[0]['competition']='Irish Cup'
        with self.assertRaises(ValueError):validate(bad,self.fixtures,self.names)

    def test_frozen_baseline_all_87(self):
        rows=list(csv.DictReader(io.StringIO((ROOT/'baseline/The_Oval_Report_Accuracy_Audit.csv').read_text(encoding='utf-8-sig'))))
        old={(r['date'],r['home'],r['away']):r for r in rows}
        for r in self.raw['audit']:
            expected=old[r['date'],r['homeClub'],r['awayClub']]
            for k,original in [('home','win_probability'),('draw','draw_probability'),('away','away_probability'),('expectedHome','expected_home_goals'),('expectedAway','expected_away_goals'),('brier','brier')]:
                self.assertAlmostEqual(r[k],float(expected[original]),places=12)
            self.assertEqual(r['score'],int(expected['score_100']))
            self.assertEqual(r['bestScore'],[int(expected['predicted_home_goals']),int(expected['predicted_away_goals'])])

    def test_formbook_exact_source_and_no_same_day_lookahead(self):
        forms=formbook(self.results,self.names)
        source=list(csv.DictReader(io.StringIO((ROOT/'baseline/The_Oval_Report_Formbook_Audit.csv').read_text(encoding='utf-8-sig'))))
        lookup={(g['date'],g['club']):g for g in forms}
        for old in source:
            g=lookup[old['date'],old['club']]
            for key in ['club_position_before_matchday','opponent_position_before_matchday','momentum_index_after_game']:
                self.assertEqual(g[key],int(old[key]))
            self.assertAlmostEqual(g['momentum_pulse'],float(old['momentum_pulse']),places=5)
            if g['result']=='W':self.assertGreater(g['momentum_pulse'],0)
        self.assertAlmostEqual(sum(WEIGHTS[-3:])/sum(WEIGHTS),.6851851851851851)
        day='2026-10-31';changed=deepcopy(self.results)
        for m in changed:
            if m['date']==day:m['hg']=15;m['ag']=0
        alternative={(g['date'],g['club']):g for g in formbook(changed,self.names)}
        for key,g in lookup.items():
            if g['date']==day:
                self.assertEqual(g['opponent_position_before_matchday'],alternative[key]['opponent_position_before_matchday'])

    def test_identifiability_shrinkage_zero_goals_and_unseen_club(self):
        history=deepcopy(self.results[:5])
        for m in history:m['hg']=0;m['ag']=0
        model=fit('poisson',history,self.names,dict(penalty=24,half_life=120))
        self.assertAlmostEqual(sum(model['attack']),0,places=12)
        self.assertAlmostEqual(sum(model['defence']),0,places=12)
        self.assertTrue(np.isfinite(model['attack']).all());self.assertTrue(model['diagnostics']['converged'])
        p=forecast(model,'Larne','Bangor');self.assertAlmostEqual(p['p_home']+p['p_draw']+p['p_away'],1)
        # New-to-training club with known identity has finite shrunk effects.
        self.assertLess(abs(model['attack'][self.names.index('Larne')]),.2)
        with self.assertRaises(ValueError):forecast(model,'Unrecognised club','Bangor')

    def test_dc_tau_and_distribution_consistency(self):
        model=fit('dc',self.results,self.names)
        for h in self.names:
            for a in self.names:
                if h==a:continue
                lh,la=goal_rates(model,h,a)
                for i,j in [(0,0),(1,0),(0,1),(1,1)]:self.assertGreaterEqual(tau(i,j,lh,la,model['rho']),0)
                p=forecast(model,h,a);grid=np.array(p['score_distribution'])
                self.assertAlmostEqual(float(grid.sum()),1,places=12)
                self.assertGreaterEqual(grid.min(),0)
                self.assertAlmostEqual(p['expected_points_home'],3*p['p_home']+p['p_draw'])
                self.assertAlmostEqual(p['expected_points_away'],3*p['p_away']+p['p_draw'])
                self.assertAlmostEqual(p['other_scorelines'],1-grid[:6,:6].sum())
                self.assertLess(p['numerical_tail'],3e-12)
        self.assertEqual(tau(2,0,3,4,.1),1)
        lo,hi=rho_bounds([(8,.05),(.05,8)])
        self.assertLess(lo,hi)

    def test_same_date_cutoffs_equal_eligibility(self):
        audit=json.loads((ROOT/'data/canonical/audit.json').read_text())
        for m in audit:
            candidates=[m['models'][k] for k in ['poisson','dc','elo','frequency']]
            self.assertEqual(len({bool(p.get('unavailable')) for p in candidates}),1)
            for p in m['models'].values():
                if p.get('unavailable'):continue
                self.assertTrue(p['trained_through'] is None or p['trained_through']<m['date'])
                self.assertEqual(p['training_sample_size'],sum(x['date']<m['date'] for x in self.results))
                self.assertAlmostEqual(sum(p[k] for k in ['p_home','p_draw','p_away']),1)
        sizes={r['matches'] for r in self.report['comparison'] if r['period']=='final_test'}
        self.assertEqual(sizes,{19});self.assertTrue(self.report['selection']['selection_frozen_before_test'])
        self.assertEqual(self.report['selection']['production_model'],'elo')

    def test_elo_no_same_day_update_and_reproducibility(self):
        from oval.models import elo_sequence
        forward=elo_sequence(self.results,self.names,48,20,0)
        backward=elo_sequence(list(reversed(self.results)),self.names,48,20,0)
        for n in self.names:self.assertAlmostEqual(forward[n],backward[n],places=12)
        history=[m for m in self.results if m['date']<'2026-10-20']
        a=fit('elo',history,self.names,dict(K=48));b=fit('elo',history,self.names,dict(K=48))
        self.assertEqual(a,b)

    def test_original_custom_score_override(self):
        p=dict(p_home=.6,p_draw=.3,p_away=.1,best_score=[1,1])
        self.assertEqual(custom_points(p,1,1),100)
        self.assertEqual(custom_points(p,2,1),67)
        self.assertEqual(custom_points(dict(p,best_score=None),2,1),None)

    def test_hybrid_markets_share_distribution(self):
        models=json.loads((ROOT/'reports/fitted-models.json').read_text())
        p=forecast(models['elo'],'Glentoran','Bangor',models['dc'])
        native=forecast(models['elo'],'Glentoran','Bangor')
        for k in ['p_home','p_draw','p_away']:self.assertAlmostEqual(p[k],native[k],places=12)
        grid=np.array(p['score_distribution']);h,a=np.indices(grid.shape)
        self.assertAlmostEqual(p['btts'],grid[1:,1:].sum());self.assertAlmostEqual(p['over_25'],grid[h+a>=3].sum())
        self.assertAlmostEqual(p['expected_home_goals'],(h*grid).sum())

    def test_exports_and_build_reproducibility(self):
        rows=list(csv.DictReader(io.StringIO((ROOT/'exports/historical_predictions.csv').read_text(encoding='utf-8-sig'))))
        self.assertEqual(len(rows),435)
        self.assertTrue(all('reconstructed' in r['forecast_type'] for r in rows))
        before=(ROOT/'The_Oval_Report.html').read_bytes()
        subprocess.run(['python','-m','oval','build'],cwd=ROOT,check=True,capture_output=True)
        self.assertEqual(before,(ROOT/'The_Oval_Report.html').read_bytes())
        text=before.decode();self.assertEqual(text.count('id="focus-p'),3)
        self.assertNotIn('<script src=',text);self.assertNotIn('@import',text)


if __name__=='__main__':unittest.main()
