// Проверка FPS-watchdog'а авто-качества (см. viewer3d.mjs):
//  1) disabled — с window.__pvu3dDisableAutoQuality виджет остаётся на L0;
//  2) enabled  — на swiftshader (~3-7 fps) ступенчато деградирует до L3
//     (pixelRatio x0.75, тени и SSAO выключены); подсказка НЕ обязательна,
//     т.к. деградация может поднять fps выше 10;
//  3, hint     — c CPU-троттлингом fps удерживается <10 даже на L3,
//     должна показаться одноразовая подсказка про 2D-режим.
import { chromium } from "playwright";

const BASE = process.env.QA_BASE_URL || "http://127.0.0.1:8050";

async function run({ disable = false, cpuThrottle = 0, settleMs = 30000 } = {}) {
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
  if (disable) {
    await page.addInitScript(() => {
      window.__pvu3dDisableAutoQuality = true;
    });
  }
  const logs = [];
  page.on("console", (m) => {
    if (m.text().includes("auto-quality")) logs.push(m.text());
  });
  await page.goto(`${BASE}/dashboard/?theme=concept03`, { waitUntil: "networkidle", timeout: 45000 });
  await page.waitForFunction(
    () => !!(window.pvu3d && window.pvu3d.isInitialized && window.pvu3d.isInitialized()),
    { timeout: 30000 }
  );
  if (cpuThrottle > 0) {
    // Троттлинг включаем после инициализации, чтобы не ловить таймауты загрузки.
    const cdp = await ctx.newCDPSession(page);
    await cdp.send("Emulation.setCPUThrottlingRate", { rate: cpuThrottle });
  }
  await page.waitForTimeout(settleMs);
  const state = await page.evaluate(() => {
    const s = window.pvu3d.getDebugState();
    return {
      performance: s.performance,
      ssaoEnabled: s.rendering.ssaoEnabled,
      shadowMapEnabled: s.rendering.shadowMapEnabled,
      hintVisible: !!document.querySelector(".viewer3d-quality-hint"),
    };
  });
  await ctx.close();
  await browser.close();
  return { state, logs };
}

const off = await run({ disable: true, settleMs: 8000 });
console.log("disabled :", JSON.stringify(off.state));

const on = await run({ settleMs: 30000 });
console.log("enabled  :", JSON.stringify(on.state));
on.logs.forEach((l) => console.log("  log:", l));

const hint = await run({ cpuThrottle: 10, settleMs: 35000 });
console.log("hint     :", JSON.stringify(hint.state));
hint.logs.forEach((l) => console.log("  log:", l));

const okOff =
  off.state.performance.qualityLevel === 0 &&
  off.state.performance.autoQualityEnabled === false;
const okOn =
  on.state.performance.qualityLevel === 3 &&
  on.state.performance.pixelRatio === 0.75 &&
  on.state.ssaoEnabled === false &&
  on.state.shadowMapEnabled === false;
const okHint =
  hint.state.performance.qualityLevel === 3 &&
  hint.state.performance.hintShown === true;

const ok = okOff && okOn && okHint;
console.log(ok ? "WATCHDOG_OK" : `WATCHDOG_FAIL off=${okOff} on=${okOn} hint=${okHint}`);
process.exit(ok ? 0 : 2);
