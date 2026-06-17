// Final verification shots: mobile 3D tab, mobile full page (KPI tiles),
// mobile + desktop 2D tab (mnemonic SVG overlap check from reviewer feedback).
// Usage: node final-check.mjs [--base <url>] [--out <dir>]

import { chromium } from "playwright";
import fs from "node:fs";
import path from "node:path";

const args = process.argv.slice(2);
const flag = (name, def) => {
  const i = args.indexOf(name);
  return i !== -1 ? args[i + 1] : def;
};
const BASE = flag("--base", process.env.QA_BASE_URL || "http://127.0.0.1:8050");
const OUT = flag("--out", "out-final");

async function shoot(browser, { width, height, name, click, fullPage, settle }) {
  const ctx = await browser.newContext({ viewport: { width, height } });
  const page = await ctx.newPage();
  await page.goto(`${BASE}/dashboard/?theme=concept03`, { waitUntil: "networkidle", timeout: 45000 });
  await page.waitForSelector("#concept03-shell", { timeout: 20000 });
  await page.waitForTimeout(settle || 4000);
  if (click) {
    await page.click(click);
    // <object> внутри display:none не грузит SVG до показа вкладки — ждём дольше.
    await page.waitForTimeout(3000);
  }
  await page.screenshot({ path: path.join(OUT, `${name}.png`), fullPage: Boolean(fullPage) });
  await ctx.close();
}

async function main() {
  fs.mkdirSync(OUT, { recursive: true });
  const browser = await chromium.launch({
    headless: true,
    args: ["--use-gl=angle", "--use-angle=swiftshader", "--enable-unsafe-swiftshader", "--disable-dev-shm-usage"],
  });
  await shoot(browser, { width: 375, height: 812, name: "mobile-3d" });
  await shoot(browser, { width: 375, height: 812, name: "mobile-full", fullPage: true });
  await shoot(browser, { width: 375, height: 812, name: "mobile-2d", click: '[data-tab-id="2d"]' });
  await shoot(browser, { width: 1500, height: 900, name: "desktop-2d", click: '[data-tab-id="2d"]' });
  await browser.close();
  console.log("done:", OUT);
}

main().catch((e) => {
  console.error(e);
  process.exit(1);
});
