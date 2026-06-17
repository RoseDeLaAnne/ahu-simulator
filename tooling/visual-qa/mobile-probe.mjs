// Mobile probe for Problem C: for each page, at phone widths, measure the
// center page-content height and the ACTIVE panel's rendered box, and confirm
// the panel actually has visible content height (not collapsed to ~0).
// Exit 2 if any active panel is shorter than MIN_OK px.
// Usage: node mobile-probe.mjs [--base <url>]

import { chromium } from "playwright";

const args = process.argv.slice(2);
const flag = (name, def) => {
  const i = args.indexOf(name);
  return i !== -1 ? args[i + 1] : def;
};
const BASE = flag("--base", process.env.QA_BASE_URL || "http://127.0.0.1:8050");
const MIN_OK = 200;

const PAGES = ["dashboard", "equipment", "control", "analytics", "library", "settings"];
const WIDTHS = [
  { w: 375, h: 812 },
  { w: 414, h: 896 },
];

async function main() {
  const browser = await chromium.launch({
    headless: true,
    args: ["--use-gl=angle", "--use-angle=swiftshader", "--enable-unsafe-swiftshader", "--disable-dev-shm-usage"],
  });

  const out = [];
  let anyBad = false;

  for (const vp of WIDTHS) {
    const ctx = await browser.newContext({ viewport: { width: vp.w, height: vp.h } });
    const page = await ctx.newPage();
    for (const pg of PAGES) {
      const url =
        pg === "dashboard"
          ? `${BASE}/dashboard/?theme=concept03`
          : `${BASE}/dashboard/?theme=concept03&page=${pg}`;
      await page.goto(url, { waitUntil: "networkidle", timeout: 45000 });
      await page.waitForSelector("#concept03-shell", { timeout: 20000 });
      await page.waitForTimeout(1200);
      const m = await page.evaluate((expected) => {
        const shell = document.getElementById("concept03-shell");
        const activeAttr = shell ? shell.getAttribute("data-active-page") : null;
        const content = document.querySelector(".c03-page-content");
        const panel = document.querySelector(`.c03-page-panel--${expected}`);
        const box = (el) => {
          if (!el) return null;
          const r = el.getBoundingClientRect();
          return { top: Math.round(r.top), h: Math.round(r.height), w: Math.round(r.width) };
        };
        const cs = panel ? getComputedStyle(panel) : null;
        return {
          activeAttr,
          content_h: content ? content.clientHeight : null,
          panel_box: box(panel),
          panel_display: cs ? cs.display : null,
          panel_scrollH: panel ? panel.scrollHeight : null,
        };
      }, pg);
      const bad = !m.panel_box || m.panel_box.h < MIN_OK || m.activeAttr !== pg;
      if (bad) anyBad = true;
      out.push({ width: vp.w, page: pg, ...m, ok: !bad });
    }
    await ctx.close();
  }

  console.log(JSON.stringify({ base: BASE, minOk: MIN_OK, results: out }, null, 2));
  await browser.close();
  process.exit(anyBad ? 2 : 0);
}

main().catch((e) => {
  console.error(e);
  process.exit(1);
});
