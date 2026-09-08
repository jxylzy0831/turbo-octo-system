const { chromium } = require('playwright');
const path = require('path');

(async () => {
  const [videoPath, outputDir] = process.argv.slice(2);
  const browser = await chromium.launch({
    headless: true,
    executablePath: 'C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe',
    args: ['--allow-file-access-from-files'],
  });
  const page = await browser.newPage({ viewport: { width: 1080, height: 1920 } });
  const videoUrl = 'file:///' + videoPath.replace(/\\/g, '/');
  await page.goto(videoUrl);
  await page.addStyleTag({ content: 'html,body{margin:0;background:#000;height:100%}video{width:100%;height:100%;object-fit:contain}' });
  const metadata = await page.evaluate(async () => {
    const video = document.querySelector('video');
    if (!video) throw new Error('video element missing');
    await new Promise((resolve, reject) => {
      if (video.readyState >= 1) return resolve();
      video.addEventListener('loadedmetadata', resolve, { once: true });
      video.addEventListener('error', () => reject(new Error(video.error?.message || 'video load error')), { once: true });
    });
    return { duration: video.duration, width: video.videoWidth, height: video.videoHeight };
  });
  const count = 9;
  for (let i = 0; i < count; i++) {
    const time = metadata.duration * i / (count - 1);
    await page.evaluate(async (t) => {
      const video = document.querySelector('video');
      video.currentTime = Math.min(t, Math.max(0, video.duration - 0.03));
      await new Promise(resolve => video.addEventListener('seeked', resolve, { once: true }));
    }, time);
    await page.locator('video').screenshot({ path: path.join(outputDir, `frame-${String(i + 1).padStart(2, '0')}.png`) });
  }
  console.log(JSON.stringify(metadata));
  await browser.close();
})().catch(error => { console.error(error); process.exit(1); });
