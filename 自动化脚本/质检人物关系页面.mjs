import { createRequire } from "node:module";
import { pathToFileURL } from "node:url";
import path from "node:path";

const require = createRequire(import.meta.url);
const { chromium } = require("C:/Users/XinYi Jiang/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/playwright");

const source = path.resolve(process.argv[2]);
const output = path.resolve(process.argv[3]);
const viewportWidth = Number(process.argv[4] || 1440);
const viewportHeight = Number(process.argv[5] || 1000);
const browser = await chromium.launch({
  headless: true,
  executablePath: "C:/Program Files/Google/Chrome/Application/chrome.exe",
});
const page = await browser.newPage({ viewport: { width: viewportWidth, height: viewportHeight }, deviceScaleFactor: 1 });
const errors = [];
page.on("console", message => {
  if (message.type() === "error") errors.push(message.text());
});
page.on("pageerror", error => errors.push(error.message));
await page.goto(pathToFileURL(source).href, { waitUntil: "networkidle" });
await page.screenshot({ path: output, fullPage: true });
const audit = await page.evaluate(() => ({
  title: document.title,
  relationCards: document.querySelectorAll(".relation").length,
  networkNodes: document.querySelectorAll("#network .node").length,
  networkEdges: document.querySelectorAll("#network .edge").length,
  horizontalOverflow: document.documentElement.scrollWidth > document.documentElement.clientWidth,
  bodyHeight: document.body.scrollHeight,
  emptyHeadings: [...document.querySelectorAll("h1,h2,h3")].filter(el => !el.textContent.trim()).length,
}));
console.log(JSON.stringify({ ...audit, errors }, null, 2));
await browser.close();
