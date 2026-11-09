/* Shared serialised model inference. Python/JavaScript parity is checked in tests. */
(function(root){
'use strict';
function rates(m,h,a){const i=m.teams.indexOf(h),j=m.teams.indexOf(a);return [Math.exp(m.intercept+m.home_advantage+m.attack[i]-m.defence[j]),Math.exp(m.intercept+m.attack[j]-m.defence[i])];}
function pmf(l){if(!(l>0&&l<100))throw Error('Unsupported intensity');const a=[Math.exp(-l)];let s=a[0];while(1-s>1e-13||a.length<7){a.push(a.at(-1)*l/a.length);s+=a.at(-1);if(a.length>256)throw Error('Tail failed');}return a;}
function predict(m,h,a,g=null){
 const model=['poisson','dc'].includes(m.model_id)?m:g;
 let probs=null;
 if(m.model_id==='frequency')probs=m.probabilities.slice();
 if(m.model_id==='elo'){const x=(m.ratings[h]-m.ratings[a]+m.home_advantage)/400*Math.log(10)/2;const z=[x,m.draw_log_weight,-x],mmax=Math.max(...z);probs=z.map(v=>Math.exp(v-mmax));const sum=probs.reduce((s,v)=>s+v,0);probs=probs.map(v=>v/sum);}
 if(!model)return {p_home:probs[0],p_draw:probs[1],p_away:probs[2],expected_points_home:3*probs[0]+probs[1],expected_points_away:3*probs[2]+probs[1]};
 const [lh,la]=rates(model,h,a),hp=pmf(lh),ap=pmf(la),r=model.rho;
 const grid=hp.map((p,i)=>ap.map((q,j)=>p*q*(i===0&&j===0?1-lh*la*r:i===1&&j===0?1+la*r:i===0&&j===1?1+lh*r:i===1&&j===1?1-r:1)));
 let sum=0;for(const row of grid)for(const v of row){if(v<0||!Number.isFinite(v))throw Error('Invalid mass');sum+=v;}
 const numerical_tail=Math.max(0,1-sum);if(Math.abs(1-sum)>3e-12)throw Error('Tail too large');
 for(const row of grid)for(let j=0;j<row.length;j++)row[j]/=sum;
 const outcomeMass=[0,0,0];for(let i=0;i<grid.length;i++)for(let j=0;j<grid[i].length;j++)outcomeMass[i>j?0:i===j?1:2]+=grid[i][j];
 if(probs)for(let i=0;i<grid.length;i++)for(let j=0;j<grid[i].length;j++){const k=i>j?0:i===j?1:2;grid[i][j]*=probs[k]/outcomeMass[k];}
 const p=[0,0,0];let eh=0,ea=0,btts=0,over=0,hcs=0,acs=0,visible=0,best=-1,bestScore=[0,0];
 for(let i=0;i<grid.length;i++)for(let j=0;j<grid[i].length;j++){const v=grid[i][j];p[i>j?0:i===j?1:2]+=v;eh+=i*v;ea+=j*v;if(i&&j)btts+=v;if(i+j>=3)over+=v;if(j===0)hcs+=v;if(i===0)acs+=v;if(i<6&&j<6)visible+=v;if(v>best){best=v;bestScore=[i,j];}}
 return {model_id:m.model_id,model_version:m.model_version,trained_through:m.trained_through,training_sample_size:m.training_sample_size,
 p_home:p[0],p_draw:p[1],p_away:p[2],expected_points_home:3*p[0]+p[1],expected_points_away:3*p[2]+p[1],expected_home_goals:eh,expected_away_goals:ea,
 btts,over_25:over,home_clean_sheet:hcs,away_clean_sheet:acs,best_score:bestScore,score_distribution:grid,other_scorelines:1-visible,numerical_tail,
 goal_model:model.model_version,hybrid:probs?`${m.model_version} outcomes + ${model.model_version} conditional goals`:null};
}
// Stateless counter-based common random numbers. Locks never consume a different stream.
function uniform(seed,run,key){let x=(seed^Math.imul(run+1,0x9e3779b1)^Math.imul(key+1,0x85ebca6b))>>>0;x^=x>>>16;x=Math.imul(x,0x7feb352d);x^=x>>>15;x=Math.imul(x,0x846ca68b);x^=x>>>16;return ((x>>>0)+.5)/4294967296;}
function rank(ts){return ts.slice().sort((a,b)=>b.pts-a.pts||(b.gf-b.ga)-(a.gf-a.ga)||b.gf-a.gf||a.tie-b.tie);}
function cdf(p){const cells=[];let s=0;for(let i=0;i<p.score_distribution.length;i++)for(let j=0;j<p.score_distribution[i].length;j++){s+=p.score_distribution[i][j];cells.push([s,i,j]);}cells.at(-1)[0]=1;return cells;}
function sample(c,u){let lo=0,hi=c.length-1;while(lo<hi){const mid=(lo+hi)>>>1;if(c[mid][0]<u)lo=mid+1;else hi=mid;}return [c[lo][1],c[lo][2]];}
function add(ts,h,a,hg,ag){const H=ts[h],A=ts[a];H.p++;A.p++;H.gf+=hg;H.ga+=ag;A.gf+=ag;A.ga+=hg;if(hg>ag){H.w++;A.l++;H.pts+=3;}else if(ag>hg){A.w++;H.l++;A.pts+=3;}else{H.d++;A.d++;H.pts++;A.pts++;}}
function scoreFor(lock){return lock==='H'?[1,0]:lock==='A'?[0,1]:[0,0];}
function scenarioTable(data,locks){const ts=data.table.map((t,i)=>({...t,tie:i})),idx=Object.fromEntries(ts.map((t,i)=>[t.name,i]));for(const f of data.fixtures)if(locks[f.id])add(ts,idx[f.home],idx[f.away],...scoreFor(locks[f.id]));return rank(ts);}
function prepare(data){
 const names=data.table.map(t=>t.name),idx=Object.fromEntries(names.map((n,i)=>[n,i])),pairs={};
 for(let h=0;h<names.length;h++)for(let a=0;a<names.length;a++)if(h!==a)pairs[h+':'+a]=cdf(predict(data.production,names[h],names[a],data.goal_model));
 return {names,idx,pairs,schedule:data.fixtures.map(f=>({h:idx[f.home],a:idx[f.away],id:f.id}))};
}
function quantile(xs,q){return xs[Math.floor((xs.length-1)*q)];}
function simulate(data,locks={},runs=10000,seed=20261109,prepared=null){
 const p=prepared||prepare(data),n=p.names.length,gl=p.idx.Glentoran;
 const hist=Array.from({length:n},()=>Array(n).fill(0)),pointRuns=Array.from({length:n},()=>[]),rankPoints=Array.from({length:n},()=>[]);
 const finishes=new Uint8Array(runs),positionSums=Array(n).fill(0),splitOpp=Array(n).fill(0),groups=new Map();let splitCount=0;
 for(let run=0;run<runs;run++){
  const ts=data.table.map((t,i)=>({...t,tie:uniform(seed,run,500+i)}));
  for(let k=0;k<p.schedule.length;k++){const f=p.schedule[k],score=locks[f.id]?scoreFor(locks[f.id]):sample(p.pairs[f.h+':'+f.a],uniform(seed,run,k));add(ts,f.h,f.a,...score);}
  if(ts.some(t=>t.p!==33))throw Error('First phase must end at 33 games');
  const pre=rank(ts),upper=pre.slice(0,6),lower=pre.slice(6);if(upper.some(t=>t.name==='Glentoran'))splitCount++;
  const group=upper.some(t=>t.name==='Glentoran')?upper:lower;for(const t of group)if(t.name!=='Glentoran')splitOpp[p.idx[t.name]]++;
  const groupKey=upper.map(t=>t.name).sort().join('|');groups.set(groupKey,(groups.get(groupKey)||0)+1);
  for(const six of [upper,lower])for(let i=0;i<6;i++)for(let j=i+1;j<6;j++){
   const first=p.idx[six[i].name],second=p.idx[six[j].name],lo=Math.min(first,second),hi=Math.max(first,second),key=1000+lo*n+hi;
   const flip=uniform(seed,run,key)<.5,h=flip?lo:hi,a=flip?hi:lo;
   add(ts,h,a,...sample(p.pairs[h+':'+a],uniform(seed,run,key+200)));
  }
  if(ts.some(t=>t.p!==38))throw Error('Season must end at 38 games');
  const final=[...rank(upper),...rank(lower)];
  for(let pos=0;pos<n;pos++){const t=final[pos],i=p.idx[t.name];hist[i][pos]++;positionSums[i]+=pos+1;pointRuns[i].push(t.pts);rankPoints[pos].push(t.pts);if(i===gl)finishes[run]=pos;}
 }
 for(const xs of [...pointRuns,...rankPoints])xs.sort((a,b)=>a-b);
 const clubs=p.names.map((name,i)=>({name,expectedPoints:pointRuns[i].reduce((s,v)=>s+v,0)/runs,averagePosition:positionSums[i]/runs,
 p10:quantile(pointRuns[i],.1),p90:quantile(pointRuns[i],.9),positions:hist[i].map(v=>v/runs)})).sort((a,b)=>a.averagePosition-b.averagePosition);
 const glens=hist[gl].map(v=>v/runs),half=Math.floor(runs/2),first=Array(12).fill(0),second=Array(12).fill(0);
 for(let i=0;i<runs;i++)(i<half?first:second)[finishes[i]]++;
 return {runs,seed,clubs,glens,finishes,convergence_max_half_difference:Math.max(...first.map((v,i)=>Math.abs(v/half-second[i]/(runs-half)))),
 pointThresholds:rankPoints.map((xs,i)=>({rank:i+1,low:quantile(xs,.1),median:quantile(xs,.5),high:quantile(xs,.9)})),
 split:{glensTopSix:splitCount/runs,opponents:p.names.filter(n=>n!=='Glentoran').map(name=>({name,probability:splitOpp[p.idx[name]]/runs})).sort((a,b)=>b.probability-a.probability),
 combinations:[...groups].sort((a,b)=>b[1]-a[1]).slice(0,6).map(([teams,count])=>({teams:teams.split('|'),probability:count/runs}))}};
}
function pairedDelta(a,b,position){if(a.length!==b.length)throw Error('Pair counts differ');let s=0,ss=0;for(let i=0;i<a.length;i++){const d=Number(a[i]===position)-Number(b[i]===position);s+=d;ss+=d*d;}const mean=s/a.length;return {delta:mean,se:Math.sqrt(Math.max(0,(ss-a.length*mean*mean)/(a.length-1))/a.length)};}
const api={predict,rates,pmf,uniform,rank,add,scoreFor,scenarioTable,prepare,simulate,pairedDelta};
if(typeof module!=='undefined'&&module.exports)module.exports=api;else root.OvalEngine=api;
})(typeof window==='undefined'?globalThis:window);
