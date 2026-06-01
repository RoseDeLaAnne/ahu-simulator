// Headless screenshot harness for concept-03 visual QA.
// Usage: node screenshot.mjs [group] [--out <dir>] [--base <url>]
//   group: defense | operator | mobile | tablet | all   (default: all)
// Captures viewport-sized PNGs at the resolutions defined in the
// concept-03 QA checklist (docs §15 N-1..N-7).

import { chromium } from "playwright";
import { mkdir } from "node:fs/promises";
import path from "node:path";

const args = process.argv.slice(2);
const group = args.find((a) => !a.startsWith("--")) || "all";
const outFlagIdx = args.indexOf("--out");
const baseFlagIdx = args.indexOf("--base");
const clickFlagIdx = args.indexOf("--click");
const settleFlagIdx = args.indexOf("--settle");
const OUT_DIR = outFlagIdx !== -1 ? args[outFlagIdx + 1] : "../../artifacts/playwright/concept03/_live";
const BASE = baseFlagIdx !== -1 ? args[baseFlagIdx + 1] : (process.env.QA_BASE_URL || "http://127.0.0.1:8050");
const CLICK = clickFlagIdx !== -1 ? args[clickFlagIdx + 1] : null;
const SETTLE = settleFlagIdx !== -1 ? Number(args[settleFlagIdx + 1]) : 2500;

const DASH = `${BASE}/dashboard/`;

// name, url query, width, height, waitSelector
const TARGETS = {
  defense: [
    { name: "defense-1500x900", q: "?theme=concept03&defense=true", w: 1500, h: 900 },
  ],
  operator: [
    { name: "operator-1366x768", q: "?theme=concept03", w: 1366, h: 768 },
    { name: "operator-1500x900", q: "?theme=concept03", w: 1500, h: 900 },
    { name: "operator-1920x1080", q: "?theme=concept03", w: 1920, h: 1080 },
  ],
  mobile: [
    { name: "mobile-375x812", q: "?theme=concept03", w: 375, h: 812 },
    { name: "mobile-414x896", q: "?theme=concept03", w: 414, h: 896 },
  ],
  tablet: [
    { name: "tablet-768x1024", q: "?theme=concept03", w: 768, h: 1024 },
  ],
};

function resolveTargets(g) {
  if (g === "all") return Object.values(TARGETS).flat();
  if (TARGETS[g]) return TARGETS[g];
  // allow a single target name
  const single = Object.values(TARGETS).flat().find((t) => t.name === g);
  if (single) return [single];
  throw new Error(`Unknown group/target: ${g}`);
}

async function main() {
  const outAbs = path.resolve(OUT_DIR);
  await mkdir(outAbs, { recursive: true });
  const targets = resolveTargets(group);

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
  for (const t of targets) {
    const ctx = await browser.newContext({
      viewport: { width: t.w, height: t.h },
      deviceScaleFactor: 1,
      reducedMotion: "reduce",
    });
    const page = await ctx.newPage();
    const consoleErrors = [];
    page.on("console", (m) => {
      if (m.type() === "error") consoleErrors.push(m.text());
    });
    page.on("pageerror", (e) => consoleErrors.push(`pageerror: ${e.message}`));

    const url = `${DASH}${t.q}`;
    try {
      await page.goto(url, { waitUntil: "networkidle", timeout: 45000 });
      // Dash mounts layout client-side; wait for the shell root.
      await page.waitForSelector("#concept03-shell, .c03-shell", { timeout: 20000 });
      // Give 3D canvas + fonts + initial callback a moment to settle.
      await page.waitForTimeout(2500);
      if (CLICK) {
        try {
          await page.click(CLICK, { timeout: 8000 });
          await page.waitForTimeout(SETTLE);
        } catch (e) {
          console.error(`  (click "${CLICK}" failed: ${e.message})`);
        }
      }
    } catch (err) {
      console.error(`! ${t.name}: ${err.message}`);
    }

    const file = path.join(outAbs, `${t.name}.png`);
    await page.screenshot({ path: file, clip: { x: 0, y: 0, width: t.w, height: t.h } });
    const errCount = consoleErrors.length;
    results.push({ name: t.name, file, errors: errCount });
    console.log(`✓ ${t.name} -> ${file}` + (errCount ? `  [${errCount} console errors]` : ""));
    if (errCount) consoleErrors.slice(0, 8).forEach((e) => console.log(`    · ${e.slice(0, 200)}`));
    await ctx.close();
  }

  await browser.close();
  console.log(`\nDone. ${results.length} screenshot(s) in ${outAbs}`);
}

main().catch((e) => {
  console.error(e);
  process.exit(1);
});
