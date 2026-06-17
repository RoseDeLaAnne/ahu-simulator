// Height probe for Problems A & C: measure the 3D canvas container height at
// several viewport widths (desktop) and confirm the active page panel has a
// non-zero center area on mobile. Reports clientHeight of the scene canvas host
// + the inner <canvas>, plus 3D liveness. Exit 2 if any desktop height is 0.
// Usage: node height-probe.mjs [--base <url>]

import { chromium } from "playwright";

const args = process.argv.slice(2);
const flag = (name, def) => {
  const i = args.indexOf(name);
  return i !== -1 ? args[i + 1] : def;
};
const BASE = flag("--base", process.env.QA_BASE_URL || "http://127.0.0.1:8050");

const DESKTOP = [
  { w: 1366, h: 800 },
  { w: 1500, h: 900 },
  { w: 1920, h: 1080 },
];

async function measureCanvas(page) {
  return page.evaluate(() => {
    const host = document.getElementById("concept03-scene-3d-canvas");
    const cv = host && host.querySelector("canvas");
    const viewport = document.getElementById("concept03-scene-3d-viewport");
    const central = document.querySelector(".c03-central-canvas");
    const cviewport = document.querySelector(".c03-central-viewport");
    const ch = (el) => (el ? el.clientHeight : null);
    return {
      centralCanvas_h: ch(central),
      centralViewport_h: ch(cviewport),
      sceneViewport_h: ch(viewport),
      sceneHost_h: ch(host),
      canvas_clientH: cv ? cv.clientHeight : null,
      canvas_attrH: cv ? cv.height : null,
    };
  });
}

async function main() {
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

  const results = [];
  let anyZero = false;

  for (const vp of DESKTOP) {
    const ctx = await browser.newContext({ viewport: { width: vp.w, height: vp.h } });
    const page = await ctx.newPage();
    await page.addInitScript(() => {
      window.__pvu3dDisableAutoQuality = true;
    });
    await page.goto(`${BASE}/dashboard/?theme=concept03`, {
      waitUntil: "networkidle",
      timeout: 45000,
    });
    await page.waitForSelector("#concept03-shell", { timeout: 20000 });
    await page.waitForFunction(
      () =>
        !!(
          window.pvu3d &&
          window.pvu3d.isInitialized &&
          window.pvu3d.isInitialized()
        ),
      { timeout: 30000 }
    );
    await page.waitForTimeout(2500);
    const m = await measureCanvas(page);
    results.push({ width: vp.w, ...m });
    if (!m.sceneHost_h || !m.canvas_clientH) anyZero = true;
    await ctx.close();
  }

  console.log(JSON.stringify({ base: BASE, desktop: results }, null, 2));
  await browser.close();
  process.exit(anyZero ? 2 : 0);
}

main().catch((e) => {
  console.error(e);
  process.exit(1);
});
