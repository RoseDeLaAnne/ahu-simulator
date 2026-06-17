// Mobile 3D probe: at phone widths, open the dashboard (3D tab), measure the
// 3D canvas box, check viewer init + rendering state, and capture a real
// 3D frame via the viewer API (headless page.screenshot shows WebGL as black).
// Usage: node mobile-3d-probe.mjs [--base <url>] [--out <dir>]

import { chromium } from "playwright";
import fs from "node:fs";
import path from "node:path";

const args = process.argv.slice(2);
const flag = (name, def) => {
  const i = args.indexOf(name);
  return i !== -1 ? args[i + 1] : def;
};
const BASE = flag("--base", process.env.QA_BASE_URL || "http://127.0.0.1:8050");
const OUT = flag("--out", "out-mobile-3d");

const WIDTHS = [
  { w: 375, h: 812 },
  { w: 414, h: 896 },
];

async function main() {
  fs.mkdirSync(OUT, { recursive: true });
  const browser = await chromium.launch({
    headless: true,
    args: ["--use-gl=angle", "--use-angle=swiftshader", "--enable-unsafe-swiftshader", "--disable-dev-shm-usage"],
  });

  const out = [];
  let anyBad = false;

  for (const vp of WIDTHS) {
    const ctx = await browser.newContext({ viewport: { width: vp.w, height: vp.h } });
    const page = await ctx.newPage();
    const errors = [];
    page.on("pageerror", (e) => errors.push(String(e)));
    await page.goto(`${BASE}/dashboard/?theme=concept03`, { waitUntil: "networkidle", timeout: 45000 });
    await page.waitForSelector("#concept03-shell", { timeout: 20000 });
    await page.waitForTimeout(4000); // give the viewer time to init + load GLB

    const m = await page.evaluate(() => {
      const box = (sel) => {
        const el = document.querySelector(sel);
        if (!el) return null;
        const r = el.getBoundingClientRect();
        const cs = getComputedStyle(el);
        return {
          top: Math.round(r.top), h: Math.round(r.height), w: Math.round(r.width),
          display: cs.display, position: cs.position,
          clientH: el.clientHeight, clientW: el.clientWidth,
        };
      };
      const dbg = window.pvu3d && window.pvu3d.getDebugState ? window.pvu3d.getDebugState() : null;
      const canvasEl = document.querySelector("#concept03-scene-3d-canvas canvas");
      return {
        central: box(".c03-central-canvas"),
        viewport: box(".c03-central-viewport"),
        panel3d: box("#concept03-panel-3d"),
        sceneViewport: box("#concept03-scene-3d-viewport"),
        canvasHost: box("#concept03-scene-3d-canvas"),
        webglCanvas: canvasEl
          ? { w: canvasEl.width, h: canvasEl.height, cssW: canvasEl.clientWidth, cssH: canvasEl.clientHeight }
          : null,
        pvu3d: !!window.pvu3d,
        rendering: dbg ? dbg.rendering : null,
        nodeCount: dbg && dbg.nodeNames ? dbg.nodeNames.length : null,
        fallbackVisible: (() => {
          const f = document.querySelector(".c03-scene-fallback, #concept03-fallback-mnemonic-object");
          if (!f) return null;
          const r = f.getBoundingClientRect();
          return r.height > 0 && getComputedStyle(f).display !== "none";
        })(),
      };
    });

    // Real 3D pixels via the viewer's own API (if alive)
    let shot = null;
    if (m.pvu3d) {
      try {
        shot = await page.evaluate(async () => {
          const r = await window.pvu3d.captureScreenshot({ scale: 1, includeMetadata: false });
          return r && r.dataUrl ? r.dataUrl.slice(0, 64) : null;
        });
        if (shot) {
          const full = await page.evaluate(async () => {
            const r = await window.pvu3d.captureScreenshot({ scale: 1, includeMetadata: false });
            return r.dataUrl;
          });
          const b64 = full.replace(/^data:image\/png;base64,/, "");
          fs.writeFileSync(path.join(OUT, `viewer-${vp.w}.png`), Buffer.from(b64, "base64"));
        }
      } catch (e) {
        shot = `ERR ${String(e).slice(0, 120)}`;
      }
    }

    // Page screenshot for layout/text inspection (WebGL will be black — fine)
    await page.screenshot({ path: path.join(OUT, `page-${vp.w}.png`), fullPage: false });

    const canvasH = m.canvasHost ? m.canvasHost.clientH : 0;
    const bad = !m.pvu3d || !m.rendering || canvasH < 200;
    if (bad) anyBad = true;
    out.push({ width: vp.w, ...m, viewerShot: shot ? "ok" : null, errors, ok: !bad });
    await ctx.close();
  }

  console.log(JSON.stringify({ base: BASE, results: out }, null, 2));
  await browser.close();
  process.exit(anyBad ? 2 : 0);
}

main().catch((e) => {
  console.error(e);
  process.exit(1);
});
