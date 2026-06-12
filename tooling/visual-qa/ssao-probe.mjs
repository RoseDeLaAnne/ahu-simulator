// Runtime probe for Task 1.1 SSAO post-processing.
//
// THE critical gate: a vendored SSAOPass.mjs that fails to import (e.g. a
// sibling `.js` 404) aborts the whole viewer3d.mjs module -> window.pvu3d is
// never defined -> the 3D viewer silently dies. node --check cannot catch this
// (it doesn't resolve the browser importmap). So we boot the real app and
// assert getDebugState().rendering.ssaoSupported === true, then toggle SSAO on
// and confirm it engages, capturing screenshots + frame timing for both states.
//
// Usage: node ssao-probe.mjs [--out <dir>] [--base <url>] [--settle <ms>]

import { chromium } from "playwright";
import { mkdir } from "node:fs/promises";
import path from "node:path";

const args = process.argv.slice(2);
const flag = (name, def) => {
  const i = args.indexOf(name);
  return i !== -1 ? args[i + 1] : def;
};
const OUT_DIR = flag("--out", "../../artifacts/playwright/scene3d/_ssao");
const BASE = flag("--base", process.env.QA_BASE_URL || "http://127.0.0.1:8050");
const SETTLE = Number(flag("--settle", 4000));
const W = 1600;
const H = 1000;
const DASH = `${BASE}/dashboard/?theme=concept03`;

const fail = (msg) => {
  console.error(`✗ FAIL: ${msg}`);
  process.exitCode = 1;
};

async function sampleFrames(page, ms) {
  return page.evaluate(
    (ms) =>
      new Promise((resolve) => {
        const deltas = [];
        let last = performance.now();
        const start = last;
        function tick(now) {
          deltas.push(now - last);
          last = now;
          if (now - start < ms) requestAnimationFrame(tick);
          else {
            const frames = deltas.length;
            const avg = deltas.reduce((a, b) => a + b, 0) / Math.max(1, frames);
            resolve({ frames, avgFrameMs: avg, fps: 1000 / avg });
          }
        }
        requestAnimationFrame(tick);
      }),
    ms
  );
}

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
  const ctx = await browser.newContext({ viewport: { width: W, height: H }, deviceScaleFactor: 1 });
  const page = await ctx.newPage();
  // Watchdog авто-качества не должен срабатывать на swiftshader (~3 fps).
  await page.addInitScript(() => {
    window.__pvu3dDisableAutoQuality = true;
  });

  const consoleErrors = [];
  const ssaoNetFailures = [];
  page.on("console", (m) => {
    if (m.type() === "error") consoleErrors.push(m.text());
  });
  page.on("pageerror", (e) => consoleErrors.push(`pageerror: ${e.message}`));
  page.on("requestfailed", (r) => {
    const u = r.url();
    if (/SSAO|SimplexNoise|postprocessing|_vendor\/three/i.test(u)) {
      ssaoNetFailures.push(`${u} (${r.failure()?.errorText || "failed"})`);
    }
  });
  page.on("response", (r) => {
    if (r.status() >= 400 && /SSAO|SimplexNoise|_vendor\/three/i.test(r.url())) {
      ssaoNetFailures.push(`${r.url()} -> HTTP ${r.status()}`);
    }
  });

  await page.goto(DASH, { waitUntil: "networkidle", timeout: 45000 });
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
  await page.waitForTimeout(SETTLE);

  // --- GATE 1: viewer module booted (import chain resolved) ---
  const hasViewer = await page.evaluate(
    () => !!(window.pvu3d && window.pvu3d.getDebugState && window.pvu3d.isInitialized && window.pvu3d.isInitialized())
  );
  if (!hasViewer) fail("window.pvu3d missing/uninitialized — viewer module did NOT boot (import abort?)");

  // --- GATE 2: SSAOPass constructed (the import actually resolved) ---
  const r0 = await page.evaluate(() => {
    if (!window.pvu3d || !window.pvu3d.getDebugState) return { error: "no getDebugState" };
    return window.pvu3d.getDebugState().rendering;
  });
  console.log("RENDERING (SSAO off):", JSON.stringify(r0));
  if (r0.ssaoSupported !== true) fail(`ssaoSupported !== true (got ${JSON.stringify(r0.ssaoSupported)})`);
  if (r0.ssaoEnabled !== false) fail(`ssaoEnabled should default to false (got ${JSON.stringify(r0.ssaoEnabled)})`);

  const fpsOff = await sampleFrames(page, 2000);
  await page.screenshot({ path: path.join(outAbs, "ssao-off.png"), clip: { x: 0, y: 0, width: W, height: H } });

  // --- GATE 3: enabling SSAO engages it and the viewer keeps rendering ---
  const enabled = await page.evaluate(() => {
    if (!window.pvu3d.setSSAOEnabled) return { error: "no setSSAOEnabled" };
    window.pvu3d.setSSAOEnabled(true);
    if (window.pvu3d.setSSAOParams) {
      window.pvu3d.setSSAOParams({ kernelRadius: 0.5, minDistance: 0.002, maxDistance: 0.06 });
    }
    return window.pvu3d.getSSAOParams ? window.pvu3d.getSSAOParams() : { error: "no getSSAOParams" };
  });
  console.log("SSAO params after enable:", JSON.stringify(enabled));
  await page.waitForTimeout(1500);
  const r1 = await page.evaluate(() => window.pvu3d.getDebugState().rendering);
  console.log("RENDERING (SSAO on):", JSON.stringify(r1));
  if (r1.ssaoEnabled !== true) fail(`ssaoEnabled !== true after setSSAOEnabled(true) (got ${JSON.stringify(r1.ssaoEnabled)})`);

  const fpsOn = await sampleFrames(page, 2000);
  await page.screenshot({ path: path.join(outAbs, "ssao-on.png"), clip: { x: 0, y: 0, width: W, height: H } });

  // --- Report ---
  console.log("\n--- PERF (headless swiftshader; relative delta only) ---");
  console.log(`  SSAO off: ${fpsOff.fps.toFixed(1)} fps (${fpsOff.avgFrameMs.toFixed(1)} ms/frame, ${fpsOff.frames} frames)`);
  console.log(`  SSAO on : ${fpsOn.fps.toFixed(1)} fps (${fpsOn.avgFrameMs.toFixed(1)} ms/frame, ${fpsOn.frames} frames)`);
  const drop = fpsOff.fps > 0 ? (100 * (fpsOff.fps - fpsOn.fps)) / fpsOff.fps : 0;
  console.log(`  Δ fps: ${drop.toFixed(1)}% lower with SSAO on`);

  if (ssaoNetFailures.length) {
    console.error(`\n✗ SSAO asset network failures (${ssaoNetFailures.length}):`);
    ssaoNetFailures.forEach((u) => console.error(`    · ${u}`));
    fail("SSAO asset(s) failed to load");
  } else {
    console.log("\n✓ No SSAO asset network failures");
  }
  if (consoleErrors.length) {
    console.log(`\nConsole errors (${consoleErrors.length}, first 10):`);
    consoleErrors.slice(0, 10).forEach((e) => console.log(`    · ${e.slice(0, 220)}`));
  } else {
    console.log("✓ No console errors");
  }

  await ctx.close();
  await browser.close();
  console.log(process.exitCode ? "\n=== PROBE FAILED ===" : "\n=== PROBE PASSED ===");
}

main().catch((e) => {
  console.error(e);
  process.exit(1);
});
