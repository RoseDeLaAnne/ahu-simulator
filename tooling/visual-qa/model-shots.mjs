import { chromium } from "playwright";
import fs from "node:fs";
import path from "node:path";
const BASE = "http://127.0.0.1:8050";
const OUT = "out-model-shots";
const TARGETS = [
  ["Флагманская ПВУ", "flagship"],
  ["Учебная ПВУ", "training"],
  ["Промышленная ПВУ", "industrial-hvac"],
];
async function pick(page, selectId, text) {
  await page.click(`#${selectId} .Select-control`).catch(() => page.click(`#${selectId}`));
  await page.waitForTimeout(250);
  const opt = page.locator(`.Select-menu-outer .Select-option`).filter({ hasText: text }).first();
  await opt.click({ timeout: 4000 }).catch(() => {});
  await page.waitForTimeout(400);
}
async function main() {
  fs.mkdirSync(OUT, { recursive: true });
  const browser = await chromium.launch({ headless: true, args: ["--use-gl=angle","--use-angle=swiftshader","--enable-unsafe-swiftshader","--disable-dev-shm-usage"] });
  const page = await browser.newContext({ viewport: { width: 1600, height: 950 } }).then(c => c.newPage());
  await page.goto(`${BASE}/dashboard/?theme=concept03`, { waitUntil: "networkidle", timeout: 60000 });
  await page.waitForSelector("#concept03-shell", { timeout: 20000 });
  await page.click('[data-tab-id="3d"]').catch(() => {});
  await page.waitForFunction(() => window.pvu3d && window.pvu3d.isInitialized && window.pvu3d.isInitialized(), { timeout: 30000 }).catch(()=>{});
  await pick(page, "concept03-scene-mode-select", "Цифровой двойник");
  for (const [label, file] of TARGETS) {
    await pick(page, "concept03-scene-model-select", label);
    await page.waitForTimeout(4000);
    await page.screenshot({ path: path.join(OUT, file + ".png") });
    console.log("shot", file);
  }
  await browser.close();
}
main().catch((e) => { console.error(e); process.exit(1); });
