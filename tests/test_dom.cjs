/* Offline DOM integration. Browser rendering is checked separately. */
const fs=require('node:fs'),assert=require('node:assert/strict'),{JSDOM,VirtualConsole}=require('jsdom');
const errors=[],vc=new VirtualConsole();vc.on('jsdomError',e=>errors.push(e.message));
function open(file){return new JSDOM(fs.readFileSync(file,'utf8'),{url:'https://oval.test/'+file,runScripts:'dangerously',pretendToBeVisual:true,virtualConsole:vc,beforeParse(w){w.URL.createObjectURL=()=> 'blob:test-export';w.URL.revokeObjectURL=()=>{};}});}
const main=open('The_Oval_Report.html'),all=open('All_Clubs_Predictions.html');
async function ready(w){for(let i=0;i<1500;i++){if(w.ovalReady)return;await new Promise(r=>setTimeout(r,10));}throw Error('Scenario calculations did not complete');}
function collectPages(d,key,selector){const results=[];for(let i=0;i<50;i++){results.push(...[...d.querySelectorAll(selector)].map(e=>e.textContent));const next=d.querySelector(`[data-pagination="${key}"] [data-step="1"]`);if(!next||next.disabled)return results;next.click();}throw Error('Pagination did not end');}
(async()=>{
 const w=main.window,d=w.document,a=all.window,ad=a.document;
 await Promise.all([ready(w),ready(a)]);assert.deepEqual(errors,[]);
 assert.equal(d.querySelector('#predictions'),null,'All-club predictions are absent from the main page');
 assert.equal(d.querySelector('#model-report'),null,'Model comparisons are on the separate page');
 assert.equal(d.querySelector('#audit-all'),null,'Main historical record is Glentoran only');
 assert.equal(d.querySelectorAll('#matrix-fixture option').length,19);
 assert.equal(d.querySelector('#form-club-select'),null);
 assert.equal(d.querySelector('#k-position').textContent,'4');assert.equal(d.querySelector('#k-points').textContent,'22');assert.equal(d.querySelector('#k-gd').textContent,'+6');
 assert.ok(d.querySelector('#next-fixture').textContent.includes('19:45'));assert.ok(d.querySelector('#next-fixture').textContent.includes('BetMcLean Oval'));
 assert.equal(d.querySelectorAll('#recent-form .form-badge').length,5);
 assert.equal(d.querySelectorAll('#league-body tr').length,12);
 assert.equal(collectPages(d,'backtest','#audit-body tr').length,14);
 assert.equal(collectPages(d,'calendar','#schedule-list .schedule-row').length,19);
 const originalTable=JSON.stringify(w.ovalTest.DATA.table),originalScenario=d.querySelector('#league-body').textContent;
 const originalProbability=w.ovalTest.getSimulation().glens.slice();
 assert.equal(d.querySelectorAll('#fixture-list article').length,6);
 for(const button of d.querySelectorAll('.focus-three button')){w.ovalReady=false;button.click();await ready(w);assert.equal(button.getAttribute('aria-pressed'),'true');assert.ok(d.querySelector('#result-model-status').textContent.includes('Ready'));}
 w.ovalReady=false;d.querySelector('#fixture-list .pick-grid button').click();await ready(w);
 assert.equal(Object.keys(w.ovalTest.locks).length,1);assert.notEqual(d.querySelector('#league-body').textContent,originalScenario);
 assert.equal(JSON.stringify(w.ovalTest.DATA.table),originalTable,'Factual data unchanged');
 assert.ok(d.querySelector('#table-heading').textContent.includes('Hypothetical'));
 assert.equal(d.querySelector('#k-position').textContent,'4','Current summary stays factual under scenarios');
 assert.equal(d.querySelector('#factual-table').hidden,false);
 assert.notDeepEqual(w.ovalTest.getSimulation().glens,originalProbability);
 w.ovalReady=false;d.querySelector('.simulation-footer .reset').click();await ready(w);
 assert.equal(Object.keys(w.ovalTest.locks).length,0);assert.equal(d.querySelector('#league-body').textContent,originalScenario);
 assert.deepEqual(w.ovalTest.getSimulation().glens,originalProbability,'Reset restores deterministic probabilities');
 ad.querySelector('#pred-all').click();assert.equal(ad.querySelectorAll('#all-match-predictions .prediction-row').length,12);
 assert.equal(collectPages(ad,'predictions','#all-match-predictions .prediction-row').length,111);
 ad.querySelector('#prediction-club').value='Glentoran';ad.querySelector('#prediction-club').dispatchEvent(new a.Event('change'));
 assert.equal(collectPages(ad,'predictions','#all-match-predictions .prediction-row').length,19);
 ad.querySelector('#prediction-date').value='2026-11-13';ad.querySelector('#prediction-date').dispatchEvent(new a.Event('change'));
 assert.equal(ad.querySelectorAll('#all-match-predictions .prediction-row').length,1);
 ad.querySelector('[data-fixture-lock]').click();assert.equal(Object.keys(a.ovalTest.locks).length,1);assert.match(ad.querySelector('#all-match-predictions').textContent,/HYPOTHETICAL/);
 a.resetPicks();assert.equal(Object.keys(a.ovalTest.locks).length,0);
 ad.querySelector('#prediction-date').value='2026-11-14';ad.querySelector('#prediction-date').dispatchEvent(new a.Event('change'));
 assert.match(ad.querySelector('#all-match-predictions').textContent,/No fixtures/);
 ad.querySelector('#prediction-date').value='31/02/2026';ad.querySelector('#prediction-date').dispatchEvent(new a.Event('change'));assert.equal(ad.querySelector('#prediction-date').getAttribute('aria-invalid'),'true');assert.match(ad.querySelector('#prediction-date-help').textContent,/DD\/MM\/YYYY/);
 ad.querySelector('#cal-all').click();assert.equal(collectPages(ad,'calendar','#schedule-list .schedule-row').length,111);
 ad.querySelector('#form-club-select').value='Linfield';ad.querySelector('#form-club-select').dispatchEvent(new a.Event('change'));
 assert.equal(ad.querySelector('#form-club-title').textContent,'Linfield');assert.equal(ad.querySelectorAll('#form-match-ledger .ledger-row').length,10);
 ad.querySelector('#audit-model').value='elo';ad.querySelector('#audit-model').dispatchEvent(new a.Event('change'));
 const audit=collectPages(ad,'backtest','#audit-body tr');assert.equal(audit.length,87);assert.equal(audit.filter(t=>t.includes('Fewer than')).length,21);
 ad.querySelector('#audit-glens').click();assert.equal(collectPages(ad,'backtest','#audit-body tr').length,14);
 ad.querySelector('#audit-others').click();assert.equal(collectPages(ad,'backtest','#audit-body tr').length,73);
 ad.querySelector('#audit-sort').value='best';ad.querySelector('#audit-sort').dispatchEvent(new a.Event('change'));assert.match(ad.querySelector('[data-pagination="backtest"]').textContent,/Page 1/);
 ad.querySelector('#difficulty-five').click();assert.ok(ad.querySelector('#runin-rows').textContent.includes('5 matches'));
 d.querySelector('#difficulty-five').click();assert.equal(d.querySelectorAll('#glens-runin .runin-mini').length,5);
 ad.querySelector('#matrix-fixture').selectedIndex=1;ad.querySelector('#matrix-fixture').dispatchEvent(new a.Event('change'));
 assert.equal(ad.querySelectorAll('#matrix-grid td').length,36);assert.ok(ad.querySelector('#matrix-key').textContent.includes('Other scorelines'));
 const downloads=[],anchorClick=w.HTMLAnchorElement.prototype.click;w.HTMLAnchorElement.prototype.click=function(){downloads.push(this.download);};
 for(const button of d.querySelectorAll('[data-export]'))button.click();assert.equal(downloads.length,7);
 d.querySelector('#scenario-export').click();assert.equal(downloads.at(-1),'forecast_scenario.csv');w.HTMLAnchorElement.prototype.click=anchorClick;
 assert.equal(d.querySelectorAll('#projected-tbody tr').length,12);assert.equal(d.querySelectorAll('#position-prob .position-row').length,12);
 for(const doc of [d,ad]){
  for(const link of doc.querySelectorAll('[data-tab]')){link.click();assert.equal(doc.querySelector(`[data-panel="${link.dataset.tab}"]`).hidden,false);assert.equal(doc.querySelectorAll('[data-panel]:not([hidden])').length,1);}
  for(const link of doc.querySelectorAll('a[href^="#"]'))assert.ok(doc.querySelector(link.getAttribute('href')),link.getAttribute('href'));
  for(const button of doc.querySelectorAll('button'))assert.ok(button.getAttribute('aria-label')||button.textContent.trim(),'Every control has an accessible name');
  const ids=[...doc.querySelectorAll('[id]')].map(e=>e.id);assert.equal(new Set(ids).size,ids.length,'IDs are unique');
 }
 assert.equal(d.querySelector('a[href="All_Clubs_Predictions.html"]').textContent.trim(),'All clubs predictions →');
 assert.ok(ad.querySelector('a[href="The_Oval_Report.html"]'));
 assert.deepEqual(errors,[]);
 console.log('DOM integration passed for both offline pages: Glentoran scope, all 87 historical records and 111 fixtures through pagination, all filters, scenarios/reset, factual summary, form, matrix, tab navigation, accessible control names and eight downloads.');
})().catch(e=>{console.error(e);process.exitCode=1;}).finally(()=>{main.window.close();all.window.close();});
