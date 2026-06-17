// Precise nav probe: measure the EXACT moment data-active-page flips (via
// MutationObserver) vs when the network/main-thread settles. Separates the
// user-perceived switch from background server work.
import { chromium } from "playwright";
const BASE = process.env.QA_BASE_URL || "http://127.0.0.1:8050";

async function measure(page, linkId, expectPage) {
  await page.waitForLoadState("networkidle", { timeout: 20000 }).catch(() => {});
  await page.waitForTimeout(300);
  // install observer + record click time inside the page
  await page.evaluate(() => {
    window.__flipMs = null;
    window.__t0 = performance.now();
    const sh = document.getElementById("concept03-shell");
    if (window.__obs) window.__obs.disconnect();
    window.__obs = new MutationObserver(() => {
      if (window.__flipMs === null) window.__flipMs = performance.now() - window.__t0;
    });
    window.__obs.observe(sh, { attributes: true, attributeFilter: ["data-active-page"] });
  });
  await page.click(linkId);
  // read the flip time as soon as we can
  let flip = null;
  for (let i = 0; i < 60; i++) {
    flip = await page.evaluate(() => window.__flipMs);
    if (flip !== null) break;
    await page.waitForTimeout(50);
  }
  const settle = await page.evaluate(() => performance.now() - window.__t0);
  const correct = await page.evaluate((p) => {
    const sh = document.getElementById("concept03-shell");
    return sh && sh.getAttribute("data-active-page") === p;
  }, expectPage);
  console.log(`  ${expectPage}: flip=${flip === null ? "NONE" : Math.round(flip) + "ms"} correct=${correct} (read-after≈${Math.round(settle)}ms)`);
}

async function main() {
  const browser = await chromium.launch({ headless: true, args: ["--disable-dev-shm-usage"] });
  const page = await browser.newContext({ viewport: { width: 1500, height: 900 } }).then(c => c.newPage());
  await page.goto(`${BASE}/dashboard/?theme=concept03`, { waitUntil: "networkidle", timeout: 60000 });
  await page.waitForSelector("#concept03-shell", { timeout: 20000 });
  await page.waitForTimeout(1500);
  console.log("=== PRECISE flip timing (perceived switch = flip ms) ===");
  await measure(page, "#footer-nav-equipment", "equipment");
  await measure(page, "#footer-nav-control", "control");
  await measure(page, "#footer-nav-analytics", "analytics");
  await measure(page, "#footer-nav-settings", "settings");
  await measure(page, "#footer-nav-dashboard", "dashboard");
  await measure(page, "#footer-nav-equipment", "equipment");
  await browser.close();
}
main().catch((e) => { console.error(e); process.exit(1); });
