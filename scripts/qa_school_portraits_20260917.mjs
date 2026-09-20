import { createRequire } from 'node:module';
import { pathToFileURL } from 'node:url';
import fs from 'node:fs/promises';
import path from 'node:path';
import assert from 'node:assert/strict';
const require=createRequire(import.meta.url);
const {chromium}=require('C:/Users/XinYi Jiang/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/playwright');
const root=path.resolve('drafts/末日学校-20260917-v1');
const qa=path.resolve('qa/末日学校-20260917-v1');
await fs.mkdir(qa,{recursive:true});
const browser=await chromium.launch({headless:true,executablePath:'C:/Program Files/Google/Chrome/Application/chrome.exe'});
const page=await browser.newPage({viewport:{width:1440,height:1100},deviceScaleFactor:1});
const errors=[],network=[];
page.on('pageerror',e=>errors.push(e.message));
page.on('console',m=>{if(m.type()==='error')errors.push(m.text())});
page.on('request',r=>{if(/^https?:/.test(r.url()))network.push(r.url())});
const checks=[];
try{
 await page.goto(pathToFileURL(path.join(root,'末日学校-人物与情绪体验.html')).href,{waitUntil:'load'});
 assert.equal(await page.locator('.pair-tab').count(),4);
 assert.equal(await page.locator('.stage-button').count(),9);
 await page.screenshot({path:path.join(qa,'desktop-experience.png'),fullPage:true});
 for(let pair=0;pair<4;pair++){
  await page.locator('.pair-tab').nth(pair).click();
  for(let stage=0;stage<9;stage++){
   await page.locator('.stage-button').nth(stage).click();
   assert.ok((await page.locator('#belief').innerText()).length>3);
   assert.equal(await page.locator('#stage-range').inputValue(),String(stage));
   assert.equal(await page.locator('.stage-button[aria-current="step"]').count(),1);
  }
 }
 checks.push('4 pairs × 9 stages: labels, actions and slider state verified');
 await page.locator('.reveal summary').click();
 assert.ok(await page.locator('#reveal-two').isVisible());
 await page.locator('#tab-portraits').click();
 assert.equal(await page.locator('.person-button').count(),9);
 const names=['许照','迟野','周砚','周晴','叶停','七号','闻笙','陈渡','谷雨'];
 for(let i=0;i<9;i++){
  await page.locator('.person-button').nth(i).click();
  assert.equal(await page.locator('#person-name').innerText(),names[i]);
  const prose=await page.locator('#person-body').innerText();
  assert.ok((prose.match(/[\u4e00-\u9fff]/g)||[]).length>=1950,names[i]+' too short');
 }
 await page.locator('#person-search').fill('N3');
 assert.equal(await page.locator('.person-button').count(),1);
 await page.locator('.person-button').click();
 assert.equal(await page.locator('#person-name').innerText(),'七号');
 await page.screenshot({path:path.join(qa,'desktop-portrait.png'),fullPage:false});
 await page.locator('#person-search').fill('不存在的人');
 assert.ok(await page.locator('#no-results').isVisible());
 await page.locator('#person-search').fill('');
 checks.push('All 9 full portraits, search and empty state verified');
 await page.locator('#tab-event').click();
 assert.ok((await page.locator('#event-body').innerText()).includes('公共事件大纲'));
 await page.locator('#tab-ending').click();
 assert.ok((await page.locator('#ending').innerText()).includes('数十年'));
 await page.screenshot({path:path.join(qa,'desktop-ending.png'),fullPage:true});
 const overflow=[];
 for(const width of [1440,768,390]){
  await page.setViewportSize({width,height:1000});
  for(const view of ['experience','portraits','event','ending']){
   await page.locator('#tab-'+view).click();
   const tooWide=await page.evaluate(()=>document.documentElement.scrollWidth>document.documentElement.clientWidth);
   overflow.push({width,view,overflow:tooWide});
   assert.equal(tooWide,false,`${view} overflows at ${width}`);
  }
 }
 checks.push('All four views at 1440, 768 and 390 px: no horizontal overflow');
 await page.locator('#tab-experience').click();
 await page.locator('.pair-tab').nth(2).click();
 await page.locator('.stage-button').nth(3).click();
 await page.screenshot({path:path.join(qa,'mobile-experience.png'),fullPage:true});
 await page.locator('#stage-range').focus();
 await page.keyboard.press('ArrowRight');
 assert.equal(await page.locator('#stage-range').inputValue(),'4');
 checks.push('Stage slider keyboard navigation verified');
 const source=JSON.parse(await page.locator('#school-data').textContent());
 for(const p of source.people)await fs.access(path.join(root,p.file));
 await fs.access(path.join(root,'末日学校-九人人物小传-合订版.md'));
 checks.push('All Markdown download targets exist');
 assert.equal(network.length,0);assert.equal(errors.length,0);
 await fs.writeFile(path.join(qa,'browser-check.json'),JSON.stringify({checks,overflow,errors,externalRequests:network},null,2),'utf8');
 console.log(JSON.stringify({checks,errors,externalRequests:network},null,2));
}finally{await browser.close()}
