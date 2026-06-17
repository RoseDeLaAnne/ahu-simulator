// Final end-to-end verification of the 3 fixes + mode robustness.
import { chromium } from "playwright";
import fs from "node:fs";
import path from "node:path";
const BASE = "http://127.0.0.1:8050";
const OUT = "out-final-verify";

async function pick(page, selectId, text) {
  await page.click(`#${selectId} .Select-control`).catch(() => page.click(`#${selectId}`));
  await page.waitForTimeout(250);
  await page.locator(`.Select-menu-outer .Select-option`).filter({ hasText: text }).first().click({ timeout: 4000 }).catch(() => {});
  await page.waitForTimeout(2500);
}

async function main() {
  fs.mkdirSync(OUT, { recursive: true });
  const errors = [];
  const browser = await chromium.launch({ headless: true, args: ["--use-gl=angle","--use-angle=swiftshader","--enable-unsafe-swiftshader","--disable-dev-shm-usage"] });
  const page = await browser.newContext({ viewport: { width: 1600, height: 950 } }).then(c => c.newPage());
  page.on("console", (m) => { if (m.type() === "error") errors.push(m.text().slice(0, 140)); });
  page.on("pageerror", (e) => errors.push("PAGEERROR " + String(e).slice(0, 140)));

  await page.goto(`${BASE}/dashboard/?theme=concept03`, { waitUntil: "networkidle", timeout: 60000 });
  await page.waitForSelector("#concept03-shell", { timeout: 20000 });
  await page.click('[data-tab-id="3d"]').catch(() => {});
  await page.waitForFunction(() => window.pvu3d && window.pvu3d.isInitialized && window.pvu3d.isInitialized() && window.pvu3d.getDebugState().modelMetrics, { timeout: 30000 }).catch(() => {});
  await page.waitForTimeout(3500);

  // ISSUE 2: default = digital_twin → callouts visible with data
  const c = await page.evaluate(() => {
    const layer = document.getElementById("concept03-callout-layer");
    const items = Array.from(layer.querySelectorAll("[data-scene-node]"));
    const visible = items.filter(el => { const r = el.getBoundingClientRect(); return r.width > 0 && r.height > 0; });
    const dup = visible.some(el => Array.from(el.querySelectorAll(".c03-callout__row")).some(row => {
      const t = row.textContent.replace(/\s+/g, "");
      // crude duplicate-caption detector: same word twice back to back (>=5 chars)
      return /([А-Яа-я]{5,})\1/.test(t);
    }));
    return { mode: document.getElementById("concept03-scene-3d-viewport").getAttribute("data-concept03-scene-mode"),
      total: items.length, visible: visible.length, anyDuplicateCaption: dup };
  });
  console.log("ISSUE 2  mode:", c.mode, "| callouts visible:", c.visible + "/" + c.total, "| duplicate-caption:", c.anyDuplicateCaption);

  // ISSUE 1: model normalized + AHU dominates room
  const m = await page.evaluate(() => {
    const s = window.pvu3d.getDebugState();
    const md = Math.max(...s.modelMetrics.size), rd = Math.max(...s.roomMetrics.size);
    return { modelLong: +md.toFixed(2), roomLong: +rd.toFixed(2), ratio: +(rd / md).toFixed(2) };
  });
  console.log("ISSUE 1  model long:", m.modelLong, "| room long:", m.roomLong, "| room/model:", m.ratio, "(want <1 → AHU dominant)");

  await page.screenshot({ path: path.join(OUT, "default-digitaltwin.png") });

  // Mode robustness: switch through every scene mode, ensure no crash / fallback
  for (const mode of ["3D модели", "Рентген", "Схема узлов", "Цифровой двойник"]) {
    await pick(page, "concept03-scene-mode-select", mode);
    const ok = await page.evaluate(() => window.pvu3d && window.pvu3d.isInitialized() && !window.pvu3d.hasFallback());
    console.log("MODE     " + mode + " → initialized & no-fallback:", ok);
  }

  // ISSUE 3: nav round-trip without full reload
  await page.evaluate(() => { window.__m = "ALIVE"; });
  await page.click("#footer-nav-equipment");
  await page.waitForTimeout(600);
  const eq = await page.evaluate(() => ({ alive: window.__m === "ALIVE", page: document.getElementById("concept03-shell").getAttribute("data-active-page") }));
  await page.click("#footer-nav-dashboard");
  await page.waitForTimeout(600);
  const db = await page.evaluate(() => document.getElementById("concept03-shell").getAttribute("data-active-page"));
  console.log("ISSUE 3  no-reload:", eq.alive, "| equipment active:", eq.page === "equipment", "| back-to-dashboard:", db === "dashboard");

  console.log("\nCONSOLE ERRORS:", errors.length ? errors : "none");
  await browser.close();
}
main().catch((e) => { console.error(e); process.exit(1); });
