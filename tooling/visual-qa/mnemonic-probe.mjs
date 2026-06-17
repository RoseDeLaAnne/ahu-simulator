// Probe: why the 2D mnemonic SVG looks blank on mobile.
// Measures the <object> bbox, checks contentDocument, captures element shot.
// Usage: node mnemonic-probe.mjs [--base <url>]

import { chromium } from "playwright";
import fs from "node:fs";
import path from "node:path";

const args = process.argv.slice(2);
const flag = (name, def) => {
  const i = args.indexOf(name);
  return i !== -1 ? args[i + 1] : def;
};
const BASE = flag("--base", process.env.QA_BASE_URL || "http://127.0.0.1:8050");
const OUT = "out-mnemonic";

async function probe(browser, width, height, label) {
  const ctx = await browser.newContext({ viewport: { width, height } });
  const page = await ctx.newPage();
  await page.goto(`${BASE}/dashboard/?theme=concept03`, { waitUntil: "networkidle", timeout: 45000 });
  await page.waitForSelector("#concept03-shell", { timeout: 20000 });
  await page.waitForTimeout(3000);
  await page.click('[data-tab-id="2d"]');
  await page.waitForTimeout(2500);
  const info = await page.evaluate(() => {
    const obj = document.getElementById("concept03-mnemonic-svg-object");
    if (!obj) return { found: false };
    const rect = obj.getBoundingClientRect();
    const style = getComputedStyle(obj);
    let docState = "no-contentDocument";
    let svgViewBox = null;
    try {
      const doc = obj.contentDocument;
      if (doc) {
        docState = doc.readyState;
        const svg = doc.querySelector("svg");
        svgViewBox = svg ? svg.getAttribute("viewBox") : "no-svg-root";
      }
    } catch (e) {
      docState = "cross-origin:" + e.message;
    }
    const panel = document.getElementById("concept03-panel-2d");
    const panelRect = panel ? panel.getBoundingClientRect() : null;
    return {
      found: true,
      rect: { x: rect.x, y: rect.y, w: rect.width, h: rect.height },
      display: style.display,
      visibility: style.visibility,
      panelRect: panelRect
        ? { x: panelRect.x, y: panelRect.y, w: panelRect.width, h: panelRect.height }
        : null,
      panelClass: panel ? panel.className : null,
      docState,
      svgViewBox,
      dataAttr: obj.getAttribute("data"),
    };
  });
  console.log(`[${label}]`, JSON.stringify(info, null, 2));
  const obj = page.locator("#concept03-mnemonic-svg-object");
  try {
    await obj.screenshot({ path: path.join(OUT, `object-${label}.png`) });
  } catch (e) {
    console.log(`[${label}] element screenshot failed:`, e.message);
  }
  await ctx.close();
}

async function main() {
  fs.mkdirSync(OUT, { recursive: true });
  const browser = await chromium.launch({
    headless: true,
    args: ["--use-gl=angle", "--use-angle=swiftshader", "--enable-unsafe-swiftshader", "--disable-dev-shm-usage"],
  });
  await probe(browser, 375, 812, "mobile");
  await probe(browser, 1500, 900, "desktop");
  await browser.close();
}

main().catch((e) => {
  console.error(e);
  process.exit(1);
});
