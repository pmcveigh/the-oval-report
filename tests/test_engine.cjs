const assert=require('node:assert/strict'),fs=require('node:fs'),E=require('../web/engine.js');
const golden=JSON.parse(fs.readFileSync('tests/golden.json','utf8')),cases=golden.cases;
let maxError=0;
function compare(a,b,path=''){
 if(typeof b==='number'){const error=Math.abs(a-b);maxError=Math.max(maxError,error);assert.ok(error<1e-10,`${path}: ${a} vs ${b}`);}
 else if(Array.isArray(b)){assert.equal(a.length,b.length,path);b.forEach((x,i)=>compare(a[i],x,path+'.'+i));}
}
for(const c of cases){const p=E.predict(golden.models[c.model],c.home,c.away,c.goal_model?golden.models[c.goal_model]:null);for(const key of ['p_home','p_draw','p_away','expected_points_home','expected_points_away','expected_home_goals','expected_away_goals','best_score','btts','over_25','other_scorelines','score_distribution'])if(c.expected[key]!=null)compare(p[key],c.expected[key],key);}
const data=JSON.parse(fs.readFileSync('data/canonical/dashboard.json','utf8')),p=E.prepare(data);
const a=E.simulate(data,{},1500,20261109,p),b=E.simulate(data,{},1500,20261109,p);
assert.deepEqual(a,b,'Identical seed and inputs reproduce exactly');
for(const t of a.clubs){assert.ok(Math.abs(t.positions.reduce((s,v)=>s+v,0)-1)<1e-12);assert.ok(t.p10<=t.expectedPoints&&t.expectedPoints<=t.p90);}
assert.ok(Math.abs(a.glens.reduce((s,v)=>s+v,0)-1)<1e-12);
const fixture=data.fixtures[0],copy=JSON.stringify(data.table),locked=E.scenarioTable(data,{[fixture.id]:'D'});
assert.equal(JSON.stringify(data.table),copy,'Scenario does not mutate factual data');
assert.equal(locked.find(t=>t.name===fixture.home).p,data.table.find(t=>t.name===fixture.home).p+1);
assert.deepEqual(E.pairedDelta(a.finishes,b.finishes,0),{delta:0,se:0});
assert.ok(E.pairedDelta(Uint8Array.from([1,1,1]),Uint8Array.from([0,0,1]),0).delta<0);
assert.equal(E.uniform(20261109,12,34),E.uniform(20261109,12,34));
console.log(`Passed ${cases.length} Python/JavaScript golden cases; maximum numeric error ${maxError}. Simulation determinism, distribution sums, immutability and paired deltas passed.`);
