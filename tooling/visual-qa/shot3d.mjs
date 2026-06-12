// Headless capture of the 3D studio view (scene3d / viewer3d.mjs).
// Boots the dashboard, switches to 3D render mode, lets the WebGL scene
// settle, then screenshots. Used to verify rendering-realism changes
// (IBL, shadows) without a manual browser session.
//
// Usage: node shot3d.mjs [--out <dir>] [--base <url>] [--settle <ms>] [--w <px>] [--h <px>]

import { chromium } from "playwright";
import { mkdir } from "node:fs/promises";
import path from "node:path";

const args = process.argv.slice(2);
const flag = (name, def) => {
  const i = args.indexOf(name);
  return i !== -1 ? args[i + 1] : def;
};

const OUT_DIR = flag("--out", "../../artifacts/playwright/scene3d/_live");
const BASE = flag("--base", process.env.QA_BASE_URL || "http://127.0.0.1:8050");
const SETTLE = Number(flag("--settle", 4000));
const W = Number(flag("--w", 1600));
const H = Number(flag("--h", 1000));
const DASH = `${BASE}/dashboard/?theme=concept03`;

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

  const ctx = await browser.newContext({
    viewport: { width: W, height: H },
    deviceScaleFactor: 1,
  });
  const page = await ctx.newPage();
  // Watchdog авто-качества не должен срабатывать на swiftshader (~3 fps).
  await page.addInitScript(() => {
    window.__pvu3dDisableAutoQuality = true;
  });
  const consoleErrors = [];
  page.on("console", (m) => {
    if (m.type() === "error") consoleErrors.push(m.text());
  });
  page.on("pageerror", (e) => consoleErrors.push(`pageerror: ${e.message}`));

  await page.goto(DASH, { waitUntil: "networkidle", timeout: 45000 });
  await page.waitForTimeout(2000);

  // concept03 defaults to the 3D central tab, so the viewer initialises on
  // load. If a classic render-mode toggle is present and visible, click it;
  // otherwise rely on the default 3D panel.
  const switched = await page
    .click("#render-mode-3d", { timeout: 3000 })
    .then(() => true)
    .catch(() => false);

  // Wait for the WebGL canvas to gain real dimensions (headless layout can
  // collapse to 0x0 until the concept03 grid resolves).
  await page
    .waitForFunction(
      () => {
        const host = document.getElementById("concept03-scene-3d-canvas");
        const c = host && host.querySelector("canvas");
        return c && c.clientWidth > 50 && c.clientHeight > 50;
      },
      { timeout: 20000 }
    )
    .catch(() => console.error("  (canvas never gained dimensions)"));

  // Let IBL/PMREM + shadow map + initial signals settle.
  await page.waitForTimeout(SETTLE);

  const file = path.join(outAbs, "scene3d.png");
  const host = await page.$("#concept03-scene-3d-viewport, #concept03-scene-3d-canvas");
  if (host) {
    await host.screenshot({ path: file });
  } else {
    await page.screenshot({ path: file, clip: { x: 0, y: 0, width: W, height: H } });
  }

  console.log(`✓ scene3d (switched=${switched}) -> ${file}` +
    (consoleErrors.length ? `  [${consoleErrors.length} console errors]` : ""));
  consoleErrors.slice(0, 12).forEach((e) => console.log(`    · ${e.slice(0, 240)}`));

  await ctx.close();
  await browser.close();
}

main().catch((e) => {
  console.error(e);
  process.exit(1);
});
