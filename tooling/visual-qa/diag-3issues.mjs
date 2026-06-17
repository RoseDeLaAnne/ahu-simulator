// Ground-truth probe for the 3 reported issues:
//  1) 3D model scaling vs room
//  2) callout labels clustering + missing data
//  3) tab/page switch latency (full reload vs client-side)
// Usage: node diag-3issues.mjs [--base http://127.0.0.1:8050]
import { chromium } from "playwright";
import fs from "node:fs";
import path from "node:path";

const args = process.argv.slice(2);
const flag = (n, d) => { const i = args.indexOf(n); return i !== -1 ? args[i + 1] : d; };
const BASE = flag("--base", process.env.QA_BASE_URL || "http://127.0.0.1:8050");
const OUT = "out-diag3";

async function main() {
  fs.mkdirSync(OUT, { recursive: true });
  const browser = await chromium.launch({
    headless: true,
    args: ["--use-gl=angle", "--use-angle=swiftshader", "--enable-unsafe-swiftshader", "--disable-dev-shm-usage"],
  });
  const ctx = await browser.newContext({ viewport: { width: 1600, height: 950 } });
  const page = await ctx.newPage();
  page.on("console", (m) => { if (m.type() === "error") console.log("  [console.error]", m.text().slice(0, 200)); });

  // Tag the window so we can detect a full navigation (reload wipes the flag).
  await page.goto(`${BASE}/dashboard/?theme=concept03`, { waitUntil: "networkidle", timeout: 60000 });
  await page.waitForSelector("#concept03-shell", { timeout: 20000 });
  await page.evaluate(() => { window.__navProbeMarker = "ALIVE-" + Date.now(); });
  await page.waitForTimeout(500);

  // Ensure 3D tab active
  await page.click('[data-tab-id="3d"]').catch(() => {});
  // Wait for model load
  await page.waitForFunction(() => {
    return window.pvu3d && window.pvu3d.isInitialized && window.pvu3d.isInitialized()
      && window.pvu3d.getDebugState && window.pvu3d.getDebugState().modelMetrics;
  }, { timeout: 30000 }).catch((e) => console.log("  model load wait failed:", e.message));
  await page.waitForTimeout(3500);

  // ---- ISSUE 1: scaling ----
  const dbg = await page.evaluate(() => {
    const s = window.pvu3d.getDebugState();
    return {
      activeModel: s.activeModel ? { id: s.activeModel.id, label: s.activeModel.label } : null,
      activeRoom: s.activeRoom ? { id: s.activeRoom.id } : null,
      scaleTuning: s.scaleTuning,
      modelMetrics: s.modelMetrics,
      roomMetrics: s.roomMetrics,
      viewMetrics: s.viewMetrics,
      nodeNames: s.nodeNames,
      cameraPreset: s.cameraPreset,
      displayMode: s.displayMode,
    };
  });
  console.log("\n===== ISSUE 1: SCALING =====");
  console.log("activeModel:", JSON.stringify(dbg.activeModel));
  console.log("activeRoom:", JSON.stringify(dbg.activeRoom));
  console.log("model size:", dbg.modelMetrics && dbg.modelMetrics.size.map(n => +n.toFixed(2)));
  console.log("model scale:", dbg.modelMetrics && dbg.modelMetrics.scale.map(n => +n.toFixed(3)));
  console.log("room size:", dbg.roomMetrics && dbg.roomMetrics.size.map(n => +n.toFixed(2)));
  console.log("room scale:", dbg.roomMetrics && dbg.roomMetrics.scale.map(n => +n.toFixed(3)));
  console.log("room placementRuntime:", dbg.roomMetrics && JSON.stringify(dbg.roomMetrics.placementRuntime));
  if (dbg.modelMetrics && dbg.roomMetrics) {
    const m = Math.max(...dbg.modelMetrics.size), r = Math.max(...dbg.roomMetrics.size);
    console.log(`>>> room/model maxdim ratio: ${(r / m).toFixed(2)} (room ${r.toFixed(2)} vs model ${m.toFixed(2)})`);
  }
  console.log("viewMetrics.markerSize:", dbg.viewMetrics && +dbg.viewMetrics.markerSize.toFixed(4));

  // ---- ISSUE 2: callouts ----
  const callouts = await page.evaluate(() => {
    const layer = document.getElementById("concept03-callout-layer");
    if (!layer) return { found: false };
    const items = Array.from(layer.querySelectorAll("[data-scene-node]")).map((el) => {
      const r = el.getBoundingClientRect();
      const title = (el.querySelector(".c03-callout__title") || {}).textContent || "";
      const rows = Array.from(el.querySelectorAll(".c03-callout__row")).map(
        (row) => row.textContent.replace(/\s+/g, " ").trim()
      );
      let projected = null;
      try { projected = window.pvu3d.getProjectedNode(el.getAttribute("data-scene-node")); } catch (e) {}
      return {
        sceneNode: el.getAttribute("data-scene-node"),
        visualId: el.getAttribute("data-visual-id"),
        positioned: el.getAttribute("data-positioned"),
        title: title.trim(),
        rows,
        cx: +(r.x + r.width / 2).toFixed(0),
        cy: +(r.y + r.height / 2).toFixed(0),
        projected: projected ? { x: +projected.x.toFixed(0), y: +projected.y.toFixed(0) } : null,
      };
    });
    return { found: true, count: items.length, items };
  });
  console.log("\n===== ISSUE 2: CALLOUTS =====");
  if (!callouts.found) console.log("NO callout layer");
  else {
    console.log(`callout count: ${callouts.count}`);
    callouts.items.forEach((c) => {
      console.log(`  [${c.positioned === "true" ? "POS" : "fallback"}] node=${c.sceneNode} proj=${JSON.stringify(c.projected)} screen=(${c.cx},${c.cy}) title="${c.title}" rows=${JSON.stringify(c.rows)}`);
    });
    // cluster check: how many distinct screen positions
    const pts = callouts.items.map(c => `${Math.round(c.cx / 40)},${Math.round(c.cy / 40)}`);
    console.log(`distinct ~40px-cells occupied: ${new Set(pts).size} of ${callouts.count}`);
  }

  await page.screenshot({ path: path.join(OUT, "3d-state.png") });

  // ---- ISSUE 3: nav latency / full reload detection ----
  console.log("\n===== ISSUE 3: NAV LATENCY =====");
  const beforeMarker = await page.evaluate(() => window.__navProbeMarker);
  const navStart = Date.now();
  // Click "Оборудование" footer link
  await page.click("#footer-nav-equipment").catch((e) => console.log("click failed", e.message));
  // Wait until the equipment page becomes visibly active (data-active-page) OR a full reload occurs
  await page.waitForTimeout(300);
  const afterMarker = await page.evaluate(() => window.__navProbeMarker);
  const reloaded = beforeMarker !== afterMarker;
  // measure when shell shows equipment active
  let activeShown = null;
  try {
    await page.waitForFunction(() => {
      const sh = document.getElementById("concept03-shell");
      return sh && sh.getAttribute("data-active-page") === "equipment";
    }, { timeout: 8000 });
    activeShown = Date.now() - navStart;
  } catch (e) { activeShown = "TIMEOUT"; }
  console.log(`window marker before=${beforeMarker} after=${afterMarker}`);
  console.log(`>>> FULL RELOAD occurred: ${reloaded}  (marker wiped means browser navigated/reloaded)`);
  console.log(`>>> time until equipment page active: ${activeShown} ms`);

  await page.screenshot({ path: path.join(OUT, "after-nav-equipment.png") });

  await ctx.close();
  await browser.close();
}
main().catch((e) => { console.error(e); process.exit(1); });
