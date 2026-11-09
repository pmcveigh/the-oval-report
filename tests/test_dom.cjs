/* DOM integration, deliberately not described as browser or rendering tests. */
const fs=require('node:fs'),assert=require('node:assert/strict'),{JSDOM,VirtualConsole}=require('jsdom');
const errors=[],vc=new VirtualConsole();vc.on('jsdomError',e=>errors.push(e.message));
const html=fs.readFileSync('The_Oval_Report.html','utf8');
const dom=new JSDOM(html,{runScripts:'dangerously',pretendToBeVisual:true,virtualConsole:vc,
 beforeParse(w){w.URL.createObjectURL=()=> 'blob:test-export';w.URL.revokeObjectURL=()=>{};}});
const w=dom.window,d=w.document;
async function ready(){for(let i=0;i<1000;i++){if(w.ovalReady)return;await new Promise(r=>setTimeout(r,10));}throw Error('Scenario calculations did not complete');}
(async()=>{
 await ready();assert.deepEqual(errors,[],'No DOM script errors');
 assert.equal(d.querySelectorAll('.focus-three button').length,3);
 assert.equal(d.querySelectorAll('#league-body tr').length,12);
 assert.equal(d.querySelectorAll('#audit-body tr').length,87);
 const originalTable=JSON.stringify(w.ovalTest.DATA.table),originalScenario=d.querySelector('#league-body').textContent;
 const originalProbability=w.ovalTest.getSimulation().glens.slice();
 assert.equal(d.querySelectorAll('#fixture-list article').length,6);
 for(const button of d.querySelectorAll('.focus-three button')){w.ovalReady=false;button.click();await ready();assert.equal(button.getAttribute('aria-pressed'),'true');assert.ok(d.querySelector('#result-model-status').textContent.includes('Ready'));}
 w.ovalReady=false;d.querySelector('#fixture-list .pick-grid button').click();await ready();
 assert.equal(Object.keys(w.ovalTest.locks).length,1);assert.notEqual(d.querySelector('#league-body').textContent,originalScenario);
 assert.equal(JSON.stringify(w.ovalTest.DATA.table),originalTable,'Factual data unchanged');
 assert.ok(d.querySelector('#table-heading').textContent.includes('Hypothetical'));
 assert.ok(d.querySelector('#scenario-count').textContent.includes('1'));
 assert.ok(d.querySelector('#all-match-predictions').textContent.includes('HYPOTHETICAL'));
 assert.notDeepEqual(w.ovalTest.getSimulation().glens,originalProbability);
 w.ovalReady=false;d.querySelector('.simulation-footer .reset').click();await ready();
 assert.equal(Object.keys(w.ovalTest.locks).length,0);assert.equal(d.querySelector('#league-body').textContent,originalScenario);
 assert.deepEqual(w.ovalTest.getSimulation().glens,originalProbability,'Reset restores deterministic probabilities');
 d.querySelector('#pred-all').click();assert.equal(d.querySelectorAll('#all-match-predictions .prediction-row').length,111);
 assert.equal(d.querySelectorAll('#all-match-predictions [data-fixture-lock]').length,333,'All remaining fixtures expose all three scenario choices');
 d.querySelector('#prediction-club').value='Glentoran';d.querySelector('#prediction-club').dispatchEvent(new w.Event('change'));
 assert.equal(d.querySelectorAll('#all-match-predictions .prediction-row').length,19);
 d.querySelector('#prediction-date').value='2026-11-13';d.querySelector('#prediction-date').dispatchEvent(new w.Event('change'));
 assert.equal(d.querySelectorAll('#all-match-predictions .prediction-row').length,1);
 d.querySelector('#prediction-date').value='2026-11-14';d.querySelector('#prediction-date').dispatchEvent(new w.Event('change'));
 assert.ok(d.querySelector('#all-match-predictions').textContent.includes('No fixtures'));
 d.querySelector('#cal-all').click();assert.equal(d.querySelectorAll('#schedule-list .schedule-row').length,111);
 d.querySelector('#form-club-select').value='Linfield';d.querySelector('#form-club-select').dispatchEvent(new w.Event('change'));
 assert.equal(d.querySelector('#form-club-title').textContent,'Linfield');assert.equal(d.querySelectorAll('#form-match-ledger .ledger-row').length,10);
 d.querySelector('#audit-model').value='elo';d.querySelector('#audit-model').dispatchEvent(new w.Event('change'));
 assert.equal(d.querySelectorAll('#audit-body tr').length,87);assert.equal((d.querySelector('#audit-body').textContent.match(/Fewer than/g)||[]).length,21);
 d.querySelector('#audit-glens').click();assert.equal(d.querySelectorAll('#audit-body tr').length,14);
 d.querySelector('#difficulty-five').click();assert.ok(d.querySelector('#runin-rows').textContent.includes('5 matches'));
 d.querySelector('#matrix-fixture').selectedIndex=1;d.querySelector('#matrix-fixture').dispatchEvent(new w.Event('change'));
 assert.equal(d.querySelectorAll('#matrix-grid td').length,36);assert.ok(d.querySelector('#matrix-key').textContent.includes('Other scorelines'));
 const downloads=[];w.HTMLAnchorElement.prototype.click=function(){downloads.push(this.download);};
 for(const button of d.querySelectorAll('[data-export]'))button.click();
 assert.equal(downloads.length,7);d.querySelector('#scenario-export').click();assert.equal(downloads.at(-1),'forecast_scenario.csv');
 assert.equal(d.querySelectorAll('#projected-tbody tr').length,12);assert.equal(d.querySelectorAll('#position-prob .position-row').length,12);
 for(const a of d.querySelectorAll('a[href^="#"]'))assert.ok(d.querySelector(a.getAttribute('href')),a.getAttribute('href'));
 for(const b of d.querySelectorAll('button'))assert.ok(b.getAttribute('aria-label')||b.textContent.trim(),'Every control has an accessible name');
 assert.deepEqual(errors,[]);
 console.log('DOM integration passed: three objectives, all audit rows, locks/reset, immutable factual data, coherent projections, filters, Formbook, matrix, navigation targets and eight export actions. No browser rendering claim.');
 dom.window.close();
})().catch(e=>{console.error(e);dom.window.close();process.exitCode=1;});
