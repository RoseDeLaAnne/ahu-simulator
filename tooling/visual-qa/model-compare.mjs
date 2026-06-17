// Compare candidate scene models in digital_twin mode: capture scaling metrics,
// callout screen positions (do labels spread + show data?), and a screenshot.
import { chromium } from "playwright";
import fs from "node:fs";
import path from "node:path";
const BASE = process.env.QA_BASE_URL || "http://127.0.0.1:8050";
const OUT = "out-model-compare";

async function pickDropdown(page, selectId, optionText) {
  await page.click(`#${selectId} .Select-control`).catch(() => page.click(`#${selectId}`));
  await page.waitForTimeout(250);
  // dash dcc.Dropdown option
  const opt = page.locator(`#${selectId} .VirtualizedSelectOption, #${selectId} .Select-option, .Select-menu-outer .Select-option`).filter({ hasText: optionText }).first();
  await opt.click({ timeout: 4000 }).catch(async () => {
    // fallback: type + enter
    await page.click(`#${selectId} .Select-input input`).catch(() => {});
    await page.keyboard.type(optionText.slice(0, 8));
    await page.waitForTimeout(300);
    await page.keyboard.press("Enter");
  });
  await page.waitForTimeout(400);
}

async function snap(page, label) {
  await page.waitForTimeout(3500);
  const dbg = await page.evaluate(() => {
    const s = window.pvu3d && window.pvu3d.getDebugState ? window.pvu3d.getDebugState() : null;
    if (!s) return null;
    return { activeModel: s.activeModel && { id: s.activeModel.id, label: s.activeModel.label },
      displayMode: s.displayMode, modelMetrics: s.modelMetrics, roomMetrics: s.roomMetrics,
      viewMetrics: s.viewMetrics, nodeNames: (s.nodeNames || []).length };
  });
  const callouts = await page.evaluate(() => {
    const layer = document.getElementById("concept03-callout-layer");
    if (!layer) return { found: false };
    const disp = getComputedStyle(layer).display;
    const items = Array.from(layer.querySelectorAll("[data-scene-node]")).map((el) => {
      const r = el.getBoundingClientRect();
      return { node: el.getAttribute("data-scene-node"), pos: el.getAttribute("data-positioned"),
        cx: Math.round(r.x + r.width / 2), cy: Math.round(r.y + r.height / 2), w: Math.round(r.width) };
    });
    const cells = new Set(items.filter(i => i.w > 0).map(i => `${Math.round(i.cx/60)},${Math.round(i.cy/60)}`));
    return { found: true, display: disp, count: items.length, visible: items.filter(i => i.w > 0).length, distinctCells: cells.size, items };
  });
  const m = dbg && dbg.modelMetrics ? Math.max(...dbg.modelMetrics.size) : null;
  const r = dbg && dbg.roomMetrics ? Math.max(...dbg.roomMetrics.size) : null;
  console.log(`\n### ${label}`);
  console.log("  model:", dbg && dbg.activeModel && dbg.activeModel.label, "| nodes:", dbg && dbg.nodeNames, "| displayMode:", dbg && dbg.displayMode);
  console.log("  model size:", dbg && dbg.modelMetrics && dbg.modelMetrics.size.map(n=>+n.toFixed(2)), "room size:", dbg && dbg.roomMetrics && dbg.roomMetrics.size.map(n=>+n.toFixed(2)));
  if (m && r) console.log(`  room/model ratio: ${(r/m).toFixed(2)}`);
  console.log("  callout layer display:", callouts.display, "| visible/total:", callouts.visible + "/" + callouts.count, "| distinct 60px cells:", callouts.distinctCells);
  await page.screenshot({ path: path.join(OUT, label.replace(/[^a-z0-9]+/gi, "_") + ".png") });
  return { dbg, callouts };
}

async function main() {
  fs.mkdirSync(OUT, { recursive: true });
  const browser = await chromium.launch({ headless: true, args: ["--use-gl=angle","--use-angle=swiftshader","--enable-unsafe-swiftshader","--disable-dev-shm-usage"] });
  const page = await browser.newContext({ viewport: { width: 1600, height: 950 } }).then(c => c.newPage());
  page.on("console", (m) => { if (m.type() === "error") console.log("  [err]", m.text().slice(0,160)); });
  await page.goto(`${BASE}/dashboard/?theme=concept03`, { waitUntil: "networkidle", timeout: 60000 });
  await page.waitForSelector("#concept03-shell", { timeout: 20000 });
  await page.click('[data-tab-id="3d"]').catch(() => {});
  await page.waitForFunction(() => window.pvu3d && window.pvu3d.isInitialized && window.pvu3d.isInitialized(), { timeout: 30000 }).catch(()=>{});
  // Switch to digital twin so callouts are visible
  await pickDropdown(page, "concept03-scene-mode-select", "Цифровой двойник");
  await snap(page, "0-default-digitaltwin");

  const MODELS = [["Флагманская ПВУ", "flagship"], ["Учебная ПВУ", "training"], ["Промышленная ПВУ", "ind-hvac"], ["Промышленный агрегат", "machinery"]];
  for (const [label, file] of MODELS) {
    await pickDropdown(page, "concept03-scene-model-select", label);
    await snap(page, file);
  }
  await browser.close();
}
main().catch((e) => { console.error(e); process.exit(1); });
