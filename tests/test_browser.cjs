/* Run with Playwright and Chromium available: node tests/test_browser.cjs.
   Start the static server first, or set OVAL_BASE_URL for an existing preview. */
const {chromium}=require('playwright'),assert=require('node:assert/strict'),fs=require('node:fs');
const base=process.env.OVAL_BASE_URL||'http://127.0.0.1:8000';
const out='work/browser';fs.mkdirSync(out,{recursive:true});
(async()=>{
 const browser=await chromium.launch({executablePath:process.env.CHROMIUM_PATH||'/usr/bin/chromium',headless:true,args:['--no-sandbox']});
 const context=await browser.newContext({viewport:{width:1366,height:768},locale:'en-GB'}),page=await context.newPage(),errors=[];page.on('pageerror',e=>errors.push(e.message));
 async function go(file){await page.goto(base+'/'+file);await page.waitForFunction(()=>window.ovalReady,{timeout:120000});}
 async function noOverflow(label){assert.equal(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth),true,label+' has no page-wide horizontal overflow');}
 await go('The_Oval_Report.html');
 for(const size of [{width:1366,height:768},{width:1920,height:1080}]){
  await page.setViewportSize(size);await noOverflow('Desktop '+size.width);
  for(const selector of ['#next-fixture','#next-match-prediction','#latest-result','#recent-form','#k-position','#k-points','#k-gd']){
   const box=await page.locator(selector).boundingBox();assert.ok(box&&box.y>=0&&box.y+box.height<size.height,selector+' fits in '+size.width+' × '+size.height);
  }
  await page.screenshot({path:`${out}/glentoran-${size.width}.png`});
 }
 await page.setViewportSize({width:1366,height:768});
 const info=page.locator('.next-match [data-info]').first(),popover=page.locator('#info-popover');
 await info.hover();await popover.waitFor({state:'visible'});assert.match(await popover.innerText(),/winning team/);
 await page.mouse.move(2,2);await page.waitForTimeout(200);assert.equal(await popover.isVisible(),false);
 await info.focus();assert.equal(await popover.isVisible(),true);assert.notEqual(await info.evaluate(e=>getComputedStyle(e).outlineStyle),'none');
 await page.keyboard.press('Escape');assert.equal(await popover.isVisible(),false);
 await page.keyboard.press('Enter');assert.equal(await popover.isVisible(),true);await page.getByRole('button',{name:'Close explanation'}).click();assert.equal(await popover.isVisible(),false);assert.equal(await info.evaluate(e=>e===document.activeElement),true);
 await page.keyboard.press('Enter');await page.locator('.brand-title').click();assert.equal(await popover.isVisible(),false);
 // Every tab is a real hash destination and all main-page selectors stay Glentoran-only.
 for(const filename of ['The_Oval_Report.html','All_Clubs_Predictions.html']){
  for(const width of [1366,768,390,320]){
   await page.setViewportSize({width,height:width===1366?768:844});await go(filename);
   const tabs=await page.locator('[data-tab]').evaluateAll(els=>els.map(e=>e.dataset.tab));
   for(const tab of tabs){
    await page.locator(`[data-tab="${tab}"]`).click();await noOverflow(filename+' '+tab+' '+width);
    assert.equal(await page.locator(`[data-panel="${tab}"]`).isVisible(),true);
    assert.equal(await page.locator('[data-panel]:visible').count(),1);
    // No vertical nested scrolling areas in the primary content.
    assert.deepEqual(await page.locator('main *').evaluateAll(els=>els.filter(e=>e.getBoundingClientRect().height>40&&['auto','scroll'].includes(getComputedStyle(e).overflowY)&&e.scrollHeight>e.clientHeight+2).map(e=>e.id||e.className)),[]);
    if((width===390||width===1366)&&['predictions','backtest','model-report','momentum','scorematrix','projection','fixturelab'].includes(tab))await page.screenshot({path:`${out}/${filename.startsWith('All')?'all':'glens'}-${tab}-${width}.png`,fullPage:true});
   }
  }
 }
 // Direct deep links, sibling navigation and browser back.
 await page.setViewportSize({width:1366,height:768});await go('All_Clubs_Predictions.html#model-report');assert.equal(await page.locator('#model-report').isVisible(),true);
 await page.locator('.back-link').click();await page.waitForURL('**/The_Oval_Report.html');await page.waitForFunction(()=>window.ovalReady);
 await page.locator('.site-nav a').filter({hasText:'All clubs predictions'}).click();await page.waitForURL('**/All_Clubs_Predictions.html');
 await page.getByRole('button',{name:'Entire run-in',exact:true}).click();assert.match(await page.locator('#pred-match-count').innerText(),/111/);
 await page.selectOption('#prediction-club','Glentoran');assert.match(await page.locator('#pred-match-count').innerText(),/19/);
 await page.fill('#prediction-date','2026-11-14');assert.match(await page.locator('#all-match-predictions').innerText(),/No fixtures/);await noOverflow('Empty filter');
 await page.fill('#prediction-date','2026-11-13');await page.locator('[data-fixture-lock]').first().click();assert.match(await page.locator('#all-scenario-status').innerText(),/1 assumed/);
 await page.locator('.back-link').click();await page.waitForURL('**/The_Oval_Report.html');await page.waitForFunction(()=>window.ovalReady);assert.match(await page.locator('#table-heading').innerText(),/Hypothetical/);assert.equal(await page.locator('#k-position').innerText(),'4');
 await page.locator('[data-tab="fixturelab"]').click();await page.getByRole('button',{name:'Reset results',exact:true}).click();await page.waitForFunction(()=>window.ovalReady);assert.equal(await page.evaluate(()=>Object.keys(window.ovalTest.locks).length),0);
 // A nested direct link opens its enclosing disclosure, and recalculation has a visible loading state.
 await go('The_Oval_Report.html#postsplit');assert.equal(await page.locator('.season-more').getAttribute('open'),'');assert.equal(await page.locator('#postsplit').isVisible(),true);
 const loading=await page.evaluate(()=>{setFocus('p2');return document.getElementById('result-model-status').textContent;});assert.match(loading,/Updating/);await page.waitForFunction(()=>window.ovalReady);
 // Hosted build uses index.html as its real return URL.
 await go('dist/index.html');await page.locator('.site-nav a').filter({hasText:'All clubs predictions'}).click();await page.waitForURL('**/dist/All_Clubs_Predictions.html');await page.locator('.back-link').click();await page.waitForURL('**/dist/index.html');
 // Some managed Chrome installations explicitly forbid file:// navigation.
 try{
  await page.goto('file://'+process.cwd()+'/The_Oval_Report.html');await page.waitForFunction(()=>window.ovalReady);await page.locator('.site-nav a').filter({hasText:'All clubs predictions'}).click();await page.waitForURL('file:**/All_Clubs_Predictions.html');assert.equal(await page.locator('#predictions').isVisible(),true);
 }catch(error){if(!error.message.includes('ERR_BLOCKED_BY_ADMINISTRATOR'))throw error;console.log('LIMITATION: managed Chromium policy blocks file:// URLs; local-file browser navigation cannot be verified here. Both static HTTP pages and their links were tested.');}
 // Touch opens, pins and dismisses an explanation within the viewport.
 const touch=await browser.newContext({viewport:{width:390,height:844},isMobile:true,hasTouch:true,locale:'en-GB'}),mobile=await touch.newPage();
 await mobile.goto(base+'/The_Oval_Report.html');await mobile.waitForFunction(()=>window.ovalReady);const touchIcon=mobile.locator('.next-match [data-info]').first();
 await touchIcon.tap();assert.equal(await mobile.locator('#info-popover').isVisible(),true);
 const tip=await mobile.locator('#info-popover').boundingBox();assert.ok(tip.x>=0&&tip.x+tip.width<=390&&tip.y>=0&&tip.y+tip.height<=844);
 await mobile.screenshot({path:`out/mobile-info.png`.replace('out/',out+'/')});await mobile.getByRole('button',{name:'Close explanation'}).tap();assert.equal(await mobile.locator('#info-popover').isVisible(),false);
 await touchIcon.tap();await touchIcon.tap();assert.equal(await mobile.locator('#info-popover').isVisible(),false);
 await mobile.screenshot({path:`${out}/glentoran-mobile.png`,fullPage:true});
 // Missing fixtures and asynchronous calculation errors get visible, bounded states.
 const html=fs.readFileSync('The_Oval_Report.html','utf8'),payload=JSON.parse(html.match(/<script id="oval-data" type="application\/json">(.*?)<\/script>/s)[1]);
 const empty=await context.newPage();payload.fixtures=[];
 await empty.route('**/empty.html',route=>route.fulfill({contentType:'text/html',body:html.replace(/(<script id="oval-data" type="application\/json">).*?(<\/script>)/s,(_,a,b)=>a+JSON.stringify(payload)+b)}));
 await empty.goto(base+'/empty.html');await empty.waitForFunction(()=>window.ovalReady);assert.match(await empty.locator('#next-fixture').innerText(),/unavailable/);assert.match(await empty.locator('#next-match-prediction').innerText(),/No next fixture/);await empty.locator('[data-tab="scorematrix"]').click();assert.match(await empty.locator('#matrix-stats').innerText(),/No fixture/);
 const broken=await context.newPage();await broken.route('**/broken.html',route=>route.fulfill({contentType:'text/html',body:html.replace('currentSimulation=E.simulate(DATA,scenario,10000,20261109,prepared)','currentSimulation=(()=>{throw new Error("Unavailable simulation")})()')}));
 await broken.goto(base+'/broken.html');await broken.locator('#data-status.error').waitFor();assert.match(await broken.locator('#data-status').innerText(),/could not finish loading/);await broken.screenshot({path:`${out}/error.png`});
 assert.deepEqual(errors,[]);console.log('Chromium browser checks passed: all tabs at 1366, 768, 390 and 320px; first-viewport essentials at 1366×768 and 1920×1080; direct/hash navigation; mouse, keyboard and touch help; filters, pagination and shared scenarios; empty and error states. Screenshots: '+out);
 await browser.close();
})().catch(e=>{console.error(e);process.exit(1);});
