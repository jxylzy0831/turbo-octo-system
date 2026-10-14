const fs = require('fs');
const path = require('path');
const { chromium } = require('C:/Users/Yu/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/playwright');

(async () => {
  const output = path.resolve(__dirname, '..', '质检', '故事节奏与恩书本-20261014-第1版');
  const url = new URL('file:///' + path.join(output, '故事节奏预览.html').replaceAll('\\', '/')).href;
  const browser = await chromium.launch({ headless: true, channel: 'chrome' });
  const page = await browser.newPage({viewport:{width:1100,height:1000}});
  const errors=[];
  page.on('pageerror',e=>errors.push(e.message));
  await page.goto(url);
  const frame = page.frameLocator('iframe');
  const root = frame.locator('#spring-story-rhythm');
  await root.locator('.stage-nav button').first().waitFor();
  const checks=[];
  for (let id=1;id<=7;id++) {
    await root.locator('.stage-nav button').nth(id-1).click();
    const title = await root.locator('.selected-title').textContent();
    const chosen = await root.locator('.stage-nav button[aria-pressed="true"]').count();
    const book = await root.locator('.player-book').textContent();
    const host = await root.locator('.host-book').textContent();
    if (chosen!==1 || !book.trim() || !host.includes('恩0'+id)) throw new Error('Act '+id+' content failed');
    checks.push({act:id,title,selectedButtons:chosen,bookChars:book.length,hostChars:host.length});
  }
  await root.locator('.stage-nav button').nth(5).click();
  await root.locator('.book-details summary').click();
  if (!(await root.locator('.book-details').getAttribute('open')) && await root.locator('.book-details').getAttribute('open') !== '') throw new Error('Book expand failed');
  if (!(await root.locator('.player-book').textContent()).includes('乙册')) throw new Error('Act 6 boundary missing');
  await root.locator('.book-details summary').click();
  await root.locator('.stage-nav button').nth(2).click();
  await page.screenshot({path:path.join(output,'桌面界面.png'),fullPage:true});
  const widths=[];
  for (const width of [736,360,320]) {
    await page.setViewportSize({width,height:1000});
    await page.waitForTimeout(100);
    const metrics = await root.evaluate(el=>({scroll:el.scrollWidth,width:el.getBoundingClientRect().width,body:document.body.scrollWidth,window:innerWidth}));
    if(metrics.scroll>metrics.width+2 || metrics.body>metrics.window+2) throw new Error('Overflow at '+width+' '+JSON.stringify(metrics));
    widths.push({viewportWidth:width,...metrics});
  }
  await page.setViewportSize({width:320,height:2600});
  await page.waitForTimeout(300);
  await page.screenshot({path:path.join(output,'窄屏界面.png'),fullPage:true});
  if(errors.length) throw new Error(errors.join('\n'));
  fs.writeFileSync(path.join(output,'界面检查.json'),JSON.stringify({checks,widths,errors},null,2),'utf8');
  console.log(JSON.stringify({acts:checks.length,widths:widths.map(x=>x.viewportWidth),errors}));
  await browser.close();
})().catch(e=>{console.error(e);process.exitCode=1;});
