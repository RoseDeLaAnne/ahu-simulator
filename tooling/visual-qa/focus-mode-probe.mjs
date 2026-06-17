// Verify the central-canvas focus mode: a "Развернуть" button in the canvas
// substrip that hides the side rails + bottom strip so the central content
// fills the screen. Shoots defense + operator, normal vs focused, and asserts
// the geometry actually grew.
// Usage: node focus-mode-probe.mjs [--base <url>] [--out <dir>]

import { chromium } from "playwright";
import fs from "node:fs";
import path from "node:path";

const args = process.argv.slice(2);
const flag = (name, def) => {
  const i = args.indexOf(name);
  return i !== -1 ? args[i + 1] : def;
};
const BASE = flag("--base", process.env.QA_BASE_URL || "http://127.0.0.1:8050");
const OUT = flag("--out", "out-focus");

async function measure(page) {
  return page.evaluate(() => {
    const shell = document.getElementById("concept03-shell");
    const center = document.getElementById("concept03-page-content");
    const left = document.getElementById("left-rail");
    const right = document.getElementById("right-rail");
    const bottom = document.getElementById("bottom-strip");
    const r = (el) => (el ? el.getBoundingClientRect() : null);
    const cr = r(center);
    return {
      focused: shell ? shell.classList.contains("c03-shell--focus") : null,
      centerW: cr ? Math.round(cr.width) : 0,
      centerH: cr ? Math.round(cr.height) : 0,
      leftVisible: left ? r(left).width > 1 : false,
      rightVisible: right ? r(right).width > 1 : false,
      bottomVisible: bottom ? r(bottom).height > 1 : false,
    };
  });
}

async function run(browser, { defense, name }) {
  const ctx = await browser.newContext({ viewport: { width: 1920, height: 960 } });
  const page = await ctx.newPage();
  const url = `${BASE}/dashboard/?theme=concept03${defense ? "&defense=1" : ""}`;
  await page.goto(url, { waitUntil: "networkidle", timeout: 45000 });
  await page.waitForSelector("#concept03-shell", { timeout: 20000 });
  await page.waitForTimeout(4000);

  const before = await measure(page);
  await page.screenshot({ path: path.join(OUT, `${name}-normal.png`) });

  const toggle = await page.$("#concept03-focus-toggle");
  if (!toggle) {
    throw new Error(`[${name}] focus toggle button not found`);
  }
  await toggle.click();
  await page.waitForTimeout(1200);

  const after = await measure(page);
  await page.screenshot({ path: path.join(OUT, `${name}-focused.png`) });

  // Toggle back to confirm round-trip.
  await page.click("#concept03-focus-toggle");
  await page.waitForTimeout(600);
  const restored = await measure(page);

  await ctx.close();

  const ok =
    before.focused === false &&
    after.focused === true &&
    after.centerW > before.centerW &&
    after.leftVisible === false &&
    after.rightVisible === false &&
    after.bottomVisible === false &&
    restored.focused === false &&
    restored.leftVisible === true;

  console.log(`\n[${name}] (defense=${defense})`);
  console.log("  before :", JSON.stringify(before));
  console.log("  focused:", JSON.stringify(after));
  console.log("  restore:", JSON.stringify(restored));
  console.log(`  RESULT : ${ok ? "PASS ✅" : "FAIL ❌"}`);
  return ok;
}

async function main() {
  fs.mkdirSync(OUT, { recursive: true });
  const browser = await chromium.launch({
    headless: true,
    args: ["--use-gl=angle", "--use-angle=swiftshader", "--enable-unsafe-swiftshader", "--disable-dev-shm-usage"],
  });
  let allOk = true;
  allOk = (await run(browser, { defense: true, name: "defense" })) && allOk;
  allOk = (await run(browser, { defense: false, name: "operator" })) && allOk;
  await browser.close();
  console.log(`\noverall: ${allOk ? "PASS ✅" : "FAIL ❌"}  (shots in ${OUT})`);
  process.exit(allOk ? 0 : 1);
}

main().catch((e) => {
  console.error(e);
  process.exit(1);
});
