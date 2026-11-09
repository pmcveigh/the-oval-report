"""Data import, integrity checks and date-frozen descriptive formbook."""
import csv
import hashlib
import json
import re
import subprocess
from collections import Counter
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
WEIGHTS = [.15, .20, .25, .30, .40, .55, .70, 1.35, 1.80, 2.40]


def write_json(path, obj):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, indent=2, allow_nan=False) + '\n')


def write_csv(path, rows):
    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        return
    with path.open('w', newline='', encoding='utf-8-sig') as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0]), lineterminator='\n')
        writer.writeheader()
        writer.writerows(rows)


def extract_reference():
    """Execute original code unchanged, excluding its DOM startup calls only."""
    source = (ROOT / 'baseline/The_Oval_Report-v3.html').read_text()
    script = source.rsplit('<script>', 1)[1].split('</script>')[0]
    script = script[:script.rindex('\nbuildScoreMatrixOptions();')]
    footer = '''
process.stdout.write(JSON.stringify({table:initial,fixtures:remainingFixtures,
 results:RESULT_LEDGER,audit:runHonestBacktest(),
 formbook:Object.fromEntries(modelNames.map(n=>[n,calculateMomentum(chronologicalClubLedger[n])])),
 next:predict('Glentoran','Bangor'),
 baselineForecasts:remainingFixtures.map(f=>({fixture:f,prediction:predict(f.home,f.away)}))}));
'''
    raw = json.loads(subprocess.check_output(['node', '-e', script + footer], text=True))
    rows = []
    for d, h, hg, a, ag in raw['results']:
        rows.append(dict(id=f'{d}:{h}:{a}', date=d, home=h, away=a,
                         hg=hg, ag=ag, competition='NIFL Premiership', season='2026/27',
                         source='supplied-v3', verification='supplied; not independently verified'))
    fixtures = [dict(f, id=f"{f['date']}:{f['home']}:{f['away']}",
                     competition='NIFL Premiership', season='2026/27',
                     verification='supplied schedule; official verification unavailable') for f in raw['fixtures']]
    for f in fixtures:
        if f['date'] == 'TBC':
            f['date'] = None
    return raw, sorted(rows, key=lambda m: (m['date'], m['home'])), fixtures


def empty_table(names):
    return {n: dict(name=n, p=0, w=0, d=0, l=0, gf=0, ga=0, pts=0) for n in names}


def apply_result(table, m):
    h, a = table[m['home']], table[m['away']]
    for t, gf, ga in [(h, m['hg'], m['ag']), (a, m['ag'], m['hg'])]:
        t['p'] += 1; t['gf'] += gf; t['ga'] += ga
        res = 'w' if gf > ga else 'l' if gf < ga else 'd'
        t[res] += 1; t['pts'] += 3 if res == 'w' else 1 if res == 'd' else 0


def rank(table):
    # Administrative alphabetic ordering of exact ties is provisional, not an official tie-break.
    return sorted(table.values(), key=lambda t: (-t['pts'], t['ga']-t['gf'], -t['gf'], t['name']))


def validate(results, fixtures, names, reference=None, as_of='2026-11-07'):
    ids = [m['id'] for m in results + fixtures]
    if len(ids) != len(set(ids)):
        raise ValueError('Duplicate fixture identity')
    table = empty_table(names)
    for m in results:
        date.fromisoformat(m['date'])
        if m['date'] > as_of:
            raise ValueError('Result beyond declared snapshot')
        if any(type(m[k]) is not int or m[k] < 0 for k in ('hg', 'ag')):
            raise ValueError('Invalid score')
        apply_result(table, m)
    counts = Counter()
    for m in results + fixtures:
        if m['competition'] != 'NIFL Premiership' or m['home'] not in names or m['away'] not in names or m['home'] == m['away']:
            raise ValueError('Club or competition mismatch')
        counts.update([m['home'], m['away']])
        if m['date']:
            date.fromisoformat(m['date'])
    if any(counts[n] != 33 for n in names):
        raise ValueError(f'First-phase fixture counts are not 33: {counts}')
    if sum(t['gf'] for t in table.values()) != sum(t['ga'] for t in table.values()):
        raise ValueError('Goals do not balance')
    if reference:
        for r in reference:
            if table[r['name']] != r:
                raise ValueError(f"Table mismatch: {r['name']}")
    return rank(table)


def formbook(results, names):
    table = empty_table(names); histories = {n: [] for n in names}; out = []
    for day in sorted({m['date'] for m in results}):
        positions = {t['name']: i+1 for i, t in enumerate(rank(table))}
        today = [m for m in results if m['date'] == day]
        for m in today:
            for club, opp, gf, ga, venue in [(m['home'], m['away'], m['hg'], m['ag'], 'H'),
                                             (m['away'], m['home'], m['ag'], m['hg'], 'A')]:
                prior = histories[club]; confidence = min(1, min(table[club]['p'], table[opp]['p'])/4)
                gap = (positions[club]-positions[opp])/11 * confidence
                quality = (12-positions[opp])/11*confidence + .5*(1-confidence)
                res = 'W' if gf > ga else 'L' if gf < ga else 'D'
                pulse = .92+.38*quality+.20*max(0, gap) if res == 'W' else (
                    (-.02+.92*gap if gap > 0 else -.16+.48*gap) if res == 'D' else -.94-.55*max(0, -gap)+.28*max(0, gap))
                if res == 'D' and gap < .065:
                    pulse = min(0, pulse)
                prev = prior[-1]['result'] if prior else None
                prev2 = prior[-2]['result'] if len(prior) > 1 else None
                bounce = res == 'W' and prev is not None and prev != 'W'
                dip = res != 'W' and prev == 'W' and prev2 is not None and prev2 != 'W'
                if res == 'W':
                    if bounce:
                        pulse += (.56 if prev == 'L' else .28) + (.20 if sum(g['result'] == 'W' for g in prior[-5:-1]) >= 2 else 0)
                    elif prev == 'W':
                        streak = 0
                        for g in reversed(prior):
                            if g['result'] != 'W': break
                            streak += 1
                        # Source intentionally gives +.30 when the entire prior history is wins,
                        # even with fewer than three prior games. Preserve that exact rule.
                        pulse += .10*(3 if streak == len(prior) else min(3, max(1, streak)))
                elif prev is not None and prev != 'W':
                    pulse -= .23 + (.18 if prev2 is not None and prev2 != 'W' else 0)
                elif dip:
                    pulse -= .48
                g = dict(date=day, club=club, opponent=opp, home_or_away=venue,
                         club_position_before_matchday=positions[club], opponent_position_before_matchday=positions[opp],
                         club_matches_before=table[club]['p'], opponent_matches_before=table[opp]['p'],
                         rank_confidence=confidence, goals_for=gf, goals_against=ga, result=res,
                         momentum_pulse=pulse, bounceback_win=bounce, repeated_setback_after_recovery=dip)
                prior.append(g)
                last = prior[-10:]; weights = WEIGHTS[-len(last):]
                signal = sum(x['momentum_pulse']*w for x,w in zip(last, weights))/sum(weights)
                g['momentum_index_after_game'] = max(0, min(100, int(50+29*signal+.5)))
                g['position_status'] = 'provisional' if confidence < 1 else 'pre-date reconstructed'
                out.append(g)
        for m in today: apply_result(table, m)
    return out


def import_data():
    raw, results, fixtures = extract_reference()
    names = sorted(t['name'] for t in raw['table'])
    table = validate(results, fixtures, names, raw['table'])
    digest = hashlib.sha256((ROOT/'baseline/The_Oval_Report-v3.html').read_bytes()).hexdigest()
    write_json(ROOT/'data/raw/reference-extract.json', raw)
    write_json(ROOT/'data/canonical/results.json', results)
    write_json(ROOT/'data/canonical/fixtures.json', fixtures)
    write_json(ROOT/'data/canonical/table.json', table)
    write_json(ROOT/'data/canonical/manifest.json', dict(dataset_id='supplied-2026-27-v3',
        source_sha256=digest, results=len(results), remaining=len(fixtures),
        completed_seasons=0, independently_verified=False, snapshot_through='2026-11-07',
        imported_on='2026-11-09', time_zone='Europe/Belfast'))
    return raw, results, fixtures, names, table
