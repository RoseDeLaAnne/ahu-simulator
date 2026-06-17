// Verify the focused-by-default 3D scene with the model actually rendered:
// waits for pvu3d debug state to report a loaded model, then captures the full
// focused view + a bottom-left crop (Task 2: no overlapping text) and reads
// renderer debug state (Task 6: pixelRatio/sharpness, Task 7: background).
import { chromium } from "playwright";
import fs from "node:fs";
import path from "node:path";

const args = process.argv.slice(2);
const flag = (n, d) => { const i = args.indexOf(n); return i !== -1 ? args[i + 1] : d; };
const BASE = flag("--base", "http://127.0.0.1:8050");
const OUT = flag("--out", "out-render-verify");

async function debugState(page) {
  return page.evaluate(() => {
    try {
      if (!window.pvu3d || !window.pvu3d.isInitialized || !window.pvu3d.isInitialized()) return null;
      return window.pvu3d.getDebugState ? window.pvu3d.getDebugState() : null;
    } catch (e) {
      return { error: String(e && e.message || e) };
    }
  });
}

async function run(browser, { defense, name }) {
  const ctx = await browser.newContext({ viewport: { width: 1920, height: 960 }, deviceScaleFactor: 1 });
  const page = await ctx.newPage();
  const url = `${BASE}/dashboard/?theme=concept03${defense ? "&defense=1" : ""}`;
  await page.goto(url, { waitUntil: "networkidle", timeout: 60000 });
  await page.waitForSelector("#concept03-shell", { timeout: 20000 });

  // Wait until the model is actually loaded into the scene (not just the loader at 100%).
  let state = null;
  for (let i = 0; i < 45; i += 1) {
    await page.waitForTimeout(1000);
    state = await debugState(page);
    if (state && state.modelMetrics && state.roomMetrics) break;
  }
  // extra settle for env/IBL + a render tick
  await page.waitForTimeout(2500);
  state = await debugState(page);

  // Compact scale summary for Task 4 (model ↔ room proportionality).
  const scale = state ? {
    modelSize: state.modelMetrics ? state.modelMetrics.size : null,
    modelScale: state.modelMetrics ? state.modelMetrics.scale : null,
    roomSize: state.roomMetrics ? state.roomMetrics.size : null,
    roomScale: state.roomMetrics ? state.roomMetrics.scale : null,
    separation: state.roomMetrics ? state.roomMetrics.separation : null,
    rendering: state.rendering,
    pixelRatio: state.performance ? state.performance.pixelRatio : null,
  } : null;

  const shell = await page.evaluate(() => {
    const s = document.getElementById("concept03-shell");
    return { focused: s ? s.classList.contains("c03-shell--focus") : null };
  });
  const modelLabel = await page.evaluate(() => {
    const v = document.querySelector('#concept03-scene-model-select .Select-value-label, #concept03-scene-model-select [class*="singleValue"]');
    return v ? v.textContent.trim() : null;
  });

  fs.mkdirSync(OUT, { recursive: true });
  await page.screenshot({ path: path.join(OUT, `${name}-focused-3d.png`) });
  // Bottom-left crop for overlap inspection (Task 2).
  await page.screenshot({
    path: path.join(OUT, `${name}-bottomleft.png`),
    clip: { x: 0, y: 560, width: 720, height: 400 },
  });

  console.log(`\n[${name}] defense=${defense}`);
  console.log("  shell.focused :", shell.focused);
  console.log("  modelLabel    :", modelLabel);
  console.log("  scaleSummary  :", JSON.stringify(scale, null, 2));
  await ctx.close();
  return { shell, modelLabel, state };
}

async function main() {
  const browser = await chromium.launch({
    headless: true,
    args: ["--use-gl=angle", "--use-angle=swiftshader", "--enable-unsafe-swiftshader", "--disable-dev-shm-usage"],
  });
  await run(browser, { defense: false, name: "operator" });
  await browser.close();
}
main().catch((e) => { console.error(e); process.exit(1); });
