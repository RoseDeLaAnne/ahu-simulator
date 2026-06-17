// Nav-latency probe. Each click measured from a SETTLED state (networkidle),
// matching the real user scenario: open page, click one nav item, wait.
import { chromium } from "playwright";
const BASE = process.env.QA_BASE_URL || "http://127.0.0.1:8050";

async function settle(page) {
  await page.waitForLoadState("networkidle", { timeout: 20000 }).catch(() => {});
  await page.waitForTimeout(400);
}

async function clickAndMeasure(page, linkId, expectPage) {
  await settle(page);
  await page.evaluate(() => { window.__navMark = "M" + Date.now(); });
  const before = await page.evaluate(() => window.__navMark);
  const t0 = Date.now();
  await page.click(linkId);
  let activeMs = "TIMEOUT";
  try {
    await page.waitForFunction((p) => {
      const sh = document.getElementById("concept03-shell");
      return sh && sh.getAttribute("data-active-page") === p;
    }, expectPage, { timeout: 15000 });
    activeMs = Date.now() - t0;
  } catch (e) {}
  // also confirm the panel is actually visible
  const visible = await page.evaluate((p) => {
    const panel = document.querySelector(".c03-page-panel--" + p);
    if (!panel) return "no-panel";
    const r = panel.getBoundingClientRect();
    return r.width > 50 && r.height > 50 ? "visible" : "hidden(" + Math.round(r.width) + "x" + Math.round(r.height) + ")";
  }, expectPage);
  const after = await page.evaluate(() => window.__navMark);
  console.log(`  ${linkId} -> ${expectPage}: reload=${before !== after} active=${activeMs}ms panel=${visible}`);
}

async function main() {
  const browser = await chromium.launch({ headless: true, args: ["--disable-dev-shm-usage"] });
  const page = await browser.newContext({ viewport: { width: 1500, height: 900 } }).then(c => c.newPage());
  await page.goto(`${BASE}/dashboard/?theme=concept03`, { waitUntil: "networkidle", timeout: 60000 });
  await page.waitForSelector("#concept03-shell", { timeout: 20000 });
  console.log("=== NAV LATENCY (settled between clicks) ===");
  await clickAndMeasure(page, "#footer-nav-equipment", "equipment");
  await clickAndMeasure(page, "#footer-nav-control", "control");
  await clickAndMeasure(page, "#footer-nav-analytics", "analytics");
  await clickAndMeasure(page, "#footer-nav-library", "library");
  await clickAndMeasure(page, "#footer-nav-settings", "settings");
  await clickAndMeasure(page, "#footer-nav-dashboard", "dashboard");
  await browser.close();
}
main().catch((e) => { console.error(e); process.exit(1); });
