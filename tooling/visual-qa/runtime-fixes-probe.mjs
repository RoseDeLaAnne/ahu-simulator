// Проверка runtime-исправлений Phase 3:
//  1) flow_field.json грузится без 404 (URL относительно модуля);
//  2) поле стрелок — 2 InstancedMesh (2 draw call), а не ArrowHelper на точку;
//  3) LOD использует meshopt simplifier (без предупреждения о готовности);
//  4) visibilitychange ставит рендер на паузу и возобновляет.
import { chromium } from "playwright";

const BASE = process.env.QA_BASE_URL || "http://127.0.0.1:8050";

const browser = await chromium.launch({
  headless: true,
  args: [
    "--use-gl=angle",
    "--use-angle=swiftshader",
    "--enable-unsafe-swiftshader",
    "--ignore-gpu-blocklist",
    "--enable-webgl",
    "--disable-dev-shm-usage",
  ],
});
const ctx = await browser.newContext({ viewport: { width: 1600, height: 1000 } });
const page = await ctx.newPage();
await page.addInitScript(() => {
  window.__pvu3dDisableAutoQuality = true;
});

const consoleErrors = [];
const consoleWarnings = [];
page.on("console", (m) => {
  if (m.type() === "error") consoleErrors.push(m.text());
  if (m.type() === "warning") consoleWarnings.push(m.text());
});

await page.goto(`${BASE}/dashboard/?theme=concept03`, { waitUntil: "networkidle", timeout: 45000 });
await page.waitForFunction(
  () => !!(window.pvu3d && window.pvu3d.isInitialized && window.pvu3d.isInitialized()),
  { timeout: 30000 }
);
// Даём время на асинхронную загрузку flow field и компиляцию WASM-симплификатора.
await page.waitForTimeout(3000);

const checks = [];
function check(name, ok, detail) {
  checks.push({ name, ok, detail });
  console.log(`${ok ? "PASS" : "FAIL"}  ${name}${detail ? "  — " + detail : ""}`);
}

// --- 1. Flow field загружен -------------------------------------------------
const ffStats = await page.evaluate(() => window.pvu3d.getFlowFieldStats());
check("flow-field: dataLoaded", ffStats.dataLoaded === true, JSON.stringify(ffStats));
const ffErrors = consoleErrors.filter((t) => t.toLowerCase().includes("flow field"));
check("flow-field: нет ошибок загрузки", ffErrors.length === 0, ffErrors.join(" | "));

// --- 2. Стрелки = 2 InstancedMesh -------------------------------------------
const arrows = await page.evaluate(async () => {
  const before = window.pvu3d.getDebugState().rendering.rendererInfo;
  const ok = window.pvu3d.setFlowFieldMode("arrows", { density: 1 });
  await new Promise((r) => setTimeout(r, 800));
  const stats = window.pvu3d.getFlowFieldStats();
  const after = window.pvu3d.getDebugState().rendering.rendererInfo;
  return { ok, stats, drawCallsBefore: before.drawCalls, drawCallsAfter: after.drawCalls };
});
check(
  "arrows: 2 объекта (InstancedMesh x2)",
  arrows.ok === true && arrows.stats.visibleObjects === 2,
  `visibleObjects=${arrows.stats.visibleObjects}, drawCalls ${arrows.drawCallsBefore}→${arrows.drawCallsAfter}`
);
check(
  "arrows: +2 draw call, не +2N",
  arrows.drawCallsAfter - arrows.drawCallsBefore <= 4,
  `delta=${arrows.drawCallsAfter - arrows.drawCallsBefore}`
);
await page.evaluate(() => window.pvu3d.setFlowFieldMode("off"));

// --- 3. LOD через meshopt simplifier ----------------------------------------
const lod = await page.evaluate(async () => {
  const ok = window.pvu3d.setLODMode(true, { distances: [0, 15, 30] });
  await new Promise((r) => setTimeout(r, 500));
  const stats = window.pvu3d.getLODStats();
  window.pvu3d.setLODMode(false);
  return { ok, stats };
});
check(
  "lod: включается, объекты сконвертированы",
  lod.ok === true && lod.stats.totalObjects > 0,
  `totalObjects=${lod.stats.totalObjects}`
);
const lodWarn = consoleWarnings.filter((t) => t.includes("meshopt simplifier"));
check("lod: simplifier был готов", lodWarn.length === 0, lodWarn.join(" | "));

// --- 4. visibilitychange пауза/возобновление ---------------------------------
const vis = await page.evaluate(async () => {
  const before = window.pvu3d.getDebugState().performance.animationActive;
  Object.defineProperty(document, "hidden", { configurable: true, get: () => true });
  document.dispatchEvent(new Event("visibilitychange"));
  await new Promise((r) => setTimeout(r, 300));
  const paused = window.pvu3d.getDebugState().performance.animationActive;
  Object.defineProperty(document, "hidden", { configurable: true, get: () => false });
  document.dispatchEvent(new Event("visibilitychange"));
  await new Promise((r) => setTimeout(r, 300));
  const resumed = window.pvu3d.getDebugState().performance.animationActive;
  return { before, paused, resumed };
});
check(
  "visibility: пауза в фоне и возобновление",
  vis.before === true && vis.paused === false && vis.resumed === true,
  JSON.stringify(vis)
);

await ctx.close();
await browser.close();

const failed = checks.filter((c) => !c.ok);
console.log(failed.length === 0 ? "RUNTIME_FIXES_OK" : `RUNTIME_FIXES_FAIL (${failed.length})`);
process.exit(failed.length === 0 ? 0 : 2);
