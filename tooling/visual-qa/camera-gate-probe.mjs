// Problem B probe: camera/fullscreen tools must only be reachable on the 3D
// sub-tab. Verify #central-canvas[data-central-tab] tracks the active tab and
// .c03-camera-tools computed display is inline-flex on 3D, none elsewhere.
// Exit 2 on any mismatch.
// Usage: node camera-gate-probe.mjs [--base <url>]

import { chromium } from "playwright";

const args = process.argv.slice(2);
const flag = (name, def) => {
  const i = args.indexOf(name);
  return i !== -1 ? args[i + 1] : def;
};
const BASE = flag("--base", process.env.QA_BASE_URL || "http://127.0.0.1:8050");

const OTHER_TABS = ["2d", "parameters", "trends", "alarms"];

async function readState(page) {
  return page.evaluate(() => {
    const canvas = document.getElementById("central-canvas");
    const tools = document.querySelector(".c03-camera-tools");
    return {
      dataTab: canvas ? canvas.getAttribute("data-central-tab") : null,
      toolsDisplay: tools ? getComputedStyle(tools).display : null,
    };
  });
}

async function clickTab(page, tabId) {
  await page.click(`[data-tab-id="${tabId}"]`);
  await page.waitForTimeout(700);
}

async function main() {
  const browser = await chromium.launch({
    headless: true,
    args: ["--use-gl=angle", "--use-angle=swiftshader", "--enable-unsafe-swiftshader", "--disable-dev-shm-usage"],
  });
  const ctx = await browser.newContext({ viewport: { width: 1500, height: 900 } });
  const page = await ctx.newPage();
  // defense=true so all camera tools (incl. capture-png) are rendered.
  await page.goto(`${BASE}/dashboard/?theme=concept03&defense=true`, { waitUntil: "networkidle", timeout: 45000 });
  await page.waitForSelector("#central-canvas", { timeout: 20000 });
  await page.waitForTimeout(1200);

  const checks = [];
  let bad = false;

  // Initial: 3D tab, tools visible (any non-"none" display counts).
  const init = await readState(page);
  const initOk = init.dataTab === "3d" && init.toolsDisplay !== "none";
  if (!initOk) bad = true;
  checks.push({ tab: "3d(initial)", ...init, ok: initOk });

  // Switch to each non-3D tab: tools hidden, attr tracks.
  for (const t of OTHER_TABS) {
    await clickTab(page, t);
    const s = await readState(page);
    const ok = s.dataTab === t && s.toolsDisplay === "none";
    if (!ok) bad = true;
    checks.push({ tab: t, ...s, ok });
  }

  // Back to 3D: tools visible again.
  await clickTab(page, "3d");
  const back = await readState(page);
  const backOk = back.dataTab === "3d" && back.toolsDisplay !== "none";
  if (!backOk) bad = true;
  checks.push({ tab: "3d(return)", ...back, ok: backOk });

  console.log(JSON.stringify({ base: BASE, checks }, null, 2));
  await browser.close();
  process.exit(bad ? 2 : 0);
}

main().catch((e) => {
  console.error(e);
  process.exit(1);
});
