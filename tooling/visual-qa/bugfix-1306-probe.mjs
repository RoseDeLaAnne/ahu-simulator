// QA probe for the 2026-06-13 bugfix batch (6 fixes).
// Captures: desktop central expansion + strip collapse, settings central,
// 3D scene-select dark dropdown open, 3D ghost-room/neutral-connector scale,
// mobile model-select restored, mnemonic (2D) data render.
// Usage: node bugfix-1306-probe.mjs [--base <url>] [--out <dir>]

import { chromium } from "playwright";
import fs from "node:fs";
import path from "node:path";

const args = process.argv.slice(2);
const flag = (name, def) => {
  const i = args.indexOf(name);
  return i !== -1 ? args[i + 1] : def;
};
const BASE = flag("--base", process.env.QA_BASE_URL || "http://127.0.0.1:8050");
const OUT = flag("--out", "out-bugfix-1306");

async function newPage(browser, width, height, query = "") {
  const ctx = await browser.newContext({ viewport: { width, height } });
  const page = await ctx.newPage();
  await page.goto(`${BASE}/dashboard/?theme=concept03${query}`, {
    waitUntil: "networkidle",
    timeout: 45000,
  });
  await page.waitForSelector("#concept03-shell", { timeout: 20000 });
  await page.waitForTimeout(4500);
  return { ctx, page };
}

async function main() {
  fs.mkdirSync(OUT, { recursive: true });
  const browser = await chromium.launch({
    headless: true,
    args: [
      "--use-gl=angle",
      "--use-angle=swiftshader",
      "--enable-unsafe-swiftshader",
      "--disable-dev-shm-usage",
    ],
  });
  const report = {};

  // 1) Desktop dashboard — 3D tab default (scale/ghost/connectors), then strip collapse.
  {
    const { ctx, page } = await newPage(browser, 1500, 920);
    await page.screenshot({ path: path.join(OUT, "01-desktop-3d-default.png") });

    // Bug #4/#5 viewer state: is 3D alive, room ghosted, connector neutral?
    report.viewer = await page.evaluate(() => {
      const v = window.pvu3d;
      const st = v && v.getDebugState ? v.getDebugState() : null;
      return st ? { ok: true, rendering: st.rendering, scene: st.scene } : { ok: false };
    });

    // Strip collapse (bug #2 central expansion).
    const toggle = await page.$('[data-strip-toggle]');
    report.stripTogglePresent = Boolean(toggle);
    if (toggle) {
      const before = await page.$eval("#central-canvas", (el) => el.getBoundingClientRect().height);
      await toggle.click();
      await page.waitForTimeout(700);
      const after = await page.$eval("#central-canvas", (el) => el.getBoundingClientRect().height);
      report.centralHeight = { before, after, grew: after > before + 40 };
      await page.screenshot({ path: path.join(OUT, "02-desktop-3d-strip-collapsed.png") });
    }
    await ctx.close();
  }

  // 2) 3D scene-select dropdown open (bug #4 dark menu).
  {
    const { ctx, page } = await newPage(browser, 1500, 920);
    const ctrl = await page.$(".c03-scene-select .Select-control, .c03-scene-select .Select__control");
    report.sceneSelectPresent = Boolean(ctrl);
    if (ctrl) {
      await ctrl.click();
      await page.waitForTimeout(600);
      const menu = await page.$(".c03-scene-select .Select-menu-outer, .c03-scene-select .Select__menu");
      if (menu) {
        report.menuBg = await menu.evaluate((el) => getComputedStyle(el).backgroundColor);
      }
      await page.screenshot({ path: path.join(OUT, "03-desktop-3d-dropdown-open.png") });
    }
    await ctx.close();
  }

  // 3) Settings page central area (bug #3).
  {
    const { ctx, page } = await newPage(browser, 1500, 920, "&page=settings");
    await page.screenshot({ path: path.join(OUT, "04-desktop-settings.png") });
    await ctx.close();
  }

  // 4) 2D mnemonic — data render (bug #1).
  {
    const { ctx, page } = await newPage(browser, 1500, 920);
    await page.click('[data-tab-id="2d"]');
    await page.waitForTimeout(3500);
    await page.screenshot({ path: path.join(OUT, "05-desktop-2d-mnemonic.png") });
    await ctx.close();
  }

  // 5) Mobile — model select restored (bug #6) + mobile full page.
  {
    const { ctx, page } = await newPage(browser, 375, 812);
    const fields = await page.$$(".c03-scene-control-field");
    let secondVisible = false;
    if (fields.length >= 2) {
      secondVisible = await fields[1].evaluate((el) => getComputedStyle(el).display !== "none");
    }
    report.mobile = { fieldCount: fields.length, modelSelectVisible: secondVisible };
    await page.screenshot({ path: path.join(OUT, "06-mobile-3d-controls.png") });
    await page.screenshot({ path: path.join(OUT, "07-mobile-full.png"), fullPage: true });
    await ctx.close();
  }

  await browser.close();
  fs.writeFileSync(path.join(OUT, "report.json"), JSON.stringify(report, null, 2));
  console.log(JSON.stringify(report, null, 2));
  console.log("done:", OUT);
}

main().catch((e) => {
  console.error(e);
  process.exit(1);
});
