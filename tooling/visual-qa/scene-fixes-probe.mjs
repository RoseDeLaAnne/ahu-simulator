// Verification probe for the 3D scene / dashboard fixes batch.
// Checks: focus-mode default ON, default model = «Промышленный агрегат»,
// legend/about no overlap, render sharpness (pixelRatio), gradient background.
// Usage: node scene-fixes-probe.mjs [--base <url>] [--out <dir>]

import { chromium } from "playwright";
import fs from "node:fs";
import path from "node:path";

const args = process.argv.slice(2);
const flag = (name, def) => {
  const i = args.indexOf(name);
  return i !== -1 ? args[i + 1] : def;
};
const BASE = flag("--base", process.env.QA_BASE_URL || "http://127.0.0.1:8060");
const OUT = flag("--out", "out-scene-fixes");

async function waitForViewer(page) {
  await page.waitForFunction(
    () => {
      const v = window.pvu3d;
      if (!v || !v.isInitialized || !v.isInitialized()) return false;
      if (v.hasFallback && v.hasFallback()) return true; // fallback is terminal too
      const st = v.getDebugState ? v.getDebugState() : null;
      return Boolean(st && st.activeModel && st.modelMetrics);
    },
    { timeout: 90000 }
  );
}

async function main() {
  fs.mkdirSync(OUT, { recursive: true });
  const browser = await chromium.launch({
    headless: true,
    args: [
      "--use-gl=angle",
      "--use-angle=swiftshader",
      "--enable-unsafe-swiftshader",
      "--disable-dev-shm-usage",
    ],
  });
  const ctx = await browser.newContext({
    viewport: { width: 1920, height: 1080 },
    deviceScaleFactor: 1.5, // эмулируем HiDPI-масштаб Windows, где была размытость
  });
  const page = await ctx.newPage();
  const consoleErrors = [];
  page.on("console", (m) => {
    if (m.type() === "error") consoleErrors.push(m.text());
  });
  // Отключаем авто-деградацию качества, чтобы кадр был стабильно резким.
  await page.addInitScript(() => {
    window.__pvu3dDisableAutoQuality = true;
  });

  await page.goto(`${BASE}/dashboard/`, { waitUntil: "networkidle", timeout: 60000 });
  await page.waitForSelector("#concept03-shell", { timeout: 20000 });
  await page.waitForTimeout(2500);
  try {
    await waitForViewer(page);
  } catch (e) {
    console.log("WARN: viewer not fully ready:", e.message);
  }
  await page.waitForTimeout(2500);

  const report = await page.evaluate(() => {
    const shell = document.getElementById("concept03-shell");
    const focusBtn = document.getElementById("concept03-focus-toggle");
    const modelSelect = document.querySelector(
      "#concept03-scene-model-select .Select-value-label, #concept03-scene-model-select .Select-value"
    );
    const legend = document.querySelector(".viewer3d-legend");
    const about = document.querySelector("#concept03-panel-3d .c03-scene-about");
    const rect = (el) => {
      if (!el) return null;
      const r = el.getBoundingClientRect();
      return { x: Math.round(r.x), y: Math.round(r.y), w: Math.round(r.width), h: Math.round(r.height), right: Math.round(r.right), bottom: Math.round(r.bottom) };
    };
    const overlap = (a, b) => {
      if (!a || !b) return null;
      const ix = Math.max(0, Math.min(a.right, b.right) - Math.max(a.x, b.x));
      const iy = Math.max(0, Math.min(a.bottom, b.bottom) - Math.max(a.y, b.y));
      return { overlapX: ix, overlapY: iy, overlaps: ix > 0 && iy > 0 };
    };
    const dbg = window.pvu3d && window.pvu3d.getDebugState ? window.pvu3d.getDebugState() : null;
    const legendRect = rect(legend);
    const aboutRect = rect(about);
    return {
      focusModeOn: shell ? shell.classList.contains("c03-shell--focus") : null,
      focusBtnPressed: focusBtn ? focusBtn.getAttribute("aria-pressed") : null,
      selectedModelLabel: modelSelect ? modelSelect.textContent.trim() : null,
      legendRect,
      aboutRect,
      legendAboutOverlap: overlap(legendRect, aboutRect),
      hasFallback: window.pvu3d && window.pvu3d.hasFallback ? window.pvu3d.hasFallback() : null,
      performance: dbg ? dbg.performance : null,
      rendering: dbg ? dbg.rendering : null,
      activeModel: dbg && dbg.activeModel ? { id: dbg.activeModel.id, label: dbg.activeModel.label } : null,
      modelMetrics: dbg ? dbg.modelMetrics : null,
      roomMetrics: dbg ? dbg.roomMetrics : null,
      scaleTuning: dbg ? dbg.scaleTuning : null,
    };
  });

  console.log(JSON.stringify({ report, consoleErrors: consoleErrors.slice(0, 8) }, null, 2));
  await page.screenshot({ path: path.join(OUT, "dashboard-default.png") });

  // Crop bottom-left corner to inspect legend/about overlap region.
  await page.screenshot({
    path: path.join(OUT, "bottom-left.png"),
    clip: { x: 0, y: 1080 - 360, width: 520, height: 360 },
  });
  // Crop bottom-right where the legend now lives.
  await page.screenshot({
    path: path.join(OUT, "bottom-right.png"),
    clip: { x: 1920 - 360, y: 1080 - 360, width: 360, height: 360 },
  });

  await ctx.close();
  await browser.close();
}

main().catch((e) => {
  console.error(e);
  process.exit(1);
});
