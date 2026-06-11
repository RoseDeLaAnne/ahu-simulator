// One-shot probe: verify the synthetic 3D scene contains the recuperator
// marker and exhaust-branch flows (reviewer edits editing-2/editing-3), the
// renderer is alive, and capture a full-page screenshot of the 3D tab.
// Usage: node recuperator-probe.mjs [--base <url>] [--out <dir>]

import { chromium } from "playwright";
import { mkdir } from "node:fs/promises";
import path from "node:path";

const args = process.argv.slice(2);
const flag = (name, def) => {
  const i = args.indexOf(name);
  return i !== -1 ? args[i + 1] : def;
};
const BASE = flag("--base", process.env.QA_BASE_URL || "http://127.0.0.1:8050");
const OUT_DIR = flag("--out", "../../artifacts/playwright/scene3d/_editing_check");

async function main() {
  const outAbs = path.resolve(OUT_DIR);
  await mkdir(outAbs, { recursive: true });

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
  const consoleErrors = [];
  page.on("console", (m) => {
    if (m.type() === "error") consoleErrors.push(m.text());
  });
  page.on("pageerror", (e) => consoleErrors.push(`pageerror: ${e.message}`));

  await page.goto(`${BASE}/dashboard/?theme=concept03`, { waitUntil: "networkidle", timeout: 45000 });
  await page.waitForFunction(
    () => !!(window.pvu3d && window.pvu3d.getDebugState && window.pvu3d.isInitialized && window.pvu3d.isInitialized()),
    { timeout: 30000 }
  );
  await page.waitForTimeout(4000);

  const probe = await page.evaluate(() => {
    const state = window.pvu3d.getDebugState();
    const names = state.nodeNames || [];
    return {
      hasRecuperator: names.includes("pvu.recuperator.core"),
      hasRoomToRecuperator: names.includes("building.flow.room_to_recuperator"),
      hasRecuperatorToExhaust: names.includes("pvu.flow.recuperator_to_exhaust"),
      rendering: state.rendering || null,
      nodeCount: names.length,
      canvas: (() => {
        const host = document.getElementById("concept03-scene-3d-canvas");
        const c = host && host.querySelector("canvas");
        return c
          ? { w: c.clientWidth, h: c.clientHeight, attrW: c.width, attrH: c.height }
          : null;
      })(),
    };
  });

  const file = path.join(outAbs, "scene3d-recuperator.png");
  await page.screenshot({ path: file });

  console.log(JSON.stringify(probe, null, 2));
  console.log(`screenshot -> ${file}`);
  if (consoleErrors.length) {
    console.log(`console errors (${consoleErrors.length}):`);
    consoleErrors.slice(0, 8).forEach((e) => console.log(`  · ${e.slice(0, 200)}`));
  }

  await ctx.close();
  await browser.close();

  const ok = probe.hasRecuperator && probe.hasRoomToRecuperator && probe.hasRecuperatorToExhaust;
  process.exit(ok ? 0 : 2);
}

main().catch((e) => {
  console.error(e);
  process.exit(1);
});
