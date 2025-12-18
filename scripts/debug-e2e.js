const { _electron: electron } = require('@playwright/test');
const fs = require('fs');
(async () => {
  const app = await electron.launch({ args: [require('path').join(__dirname, '../out/main/index.js')] });
  const windows = await app.windows();
  let page = windows.find(w => w.url().includes('index.html'));
  if (!page) page = await app.waitForEvent('window', w => w.url().includes('index.html'));
  page.on('console', msg => console.log('PAGE LOG>', msg.type(), msg.text()));
  page.on('pageerror', err => console.log('PAGE ERROR>', err));
  await page.waitForLoadState('domcontentloaded');
  console.log('title:', await page.title());
  const html = await page.content();
  fs.writeFileSync('out/debug-page.html', html);
  console.log('Wrote out/debug-page.html (length:', html.length, ')');
  await app.close();
})();
