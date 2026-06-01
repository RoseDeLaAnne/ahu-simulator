// Probe: confirm IBL + shadows are live via window.pvu3d.getDebugState().
import { chromium } from "playwright";
const BASE = process.env.QA_BASE_URL || "http://127.0.0.1:8050";
const DASH = `${BASE}/dashboard/?theme=concept03`;

const browser = await chromium.launch({
  headless: true,
  args: ["--use-gl=angle", "--use-angle=swiftshader", "--enable-unsafe-swiftshader",
    "--ignore-gpu-blocklist", "--enable-webgl", "--disable-dev-shm-usage"],
});
const ctx = await browser.newContext({ viewport: { width: 1600, height: 1000 } });
const page = await ctx.newPage();
await page.goto(DASH, { waitUntil: "networkidle", timeout: 45000 });
await page.waitForTimeout(8000);

const rendering = await page.evaluate(() => {
  if (!window.pvu3d || !window.pvu3d.getDebugState) return { error: "no getDebugState" };
  return window.pvu3d.getDebugState().rendering;
});
console.log("RENDERING STATE:", JSON.stringify(rendering, null, 2));
await browser.close();
