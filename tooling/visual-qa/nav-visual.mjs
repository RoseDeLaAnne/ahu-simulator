// Capture screenshots proving page content actually swaps on nav (no reload).
import { chromium } from "playwright";
import fs from "node:fs";
import path from "node:path";
const BASE = process.env.QA_BASE_URL || "http://127.0.0.1:8050";
const OUT = "out-nav-visual";

async function main() {
  fs.mkdirSync(OUT, { recursive: true });
  const browser = await chromium.launch({ headless: true, args: ["--use-gl=angle","--use-angle=swiftshader","--enable-unsafe-swiftshader","--disable-dev-shm-usage"] });
  const page = await browser.newContext({ viewport: { width: 1500, height: 900 } }).then(c => c.newPage());
  const errors = [];
  page.on("console", (m) => { if (m.type() === "error") errors.push(m.text().slice(0,160)); });
  await page.goto(`${BASE}/dashboard/?theme=concept03`, { waitUntil: "networkidle", timeout: 60000 });
  await page.waitForSelector("#concept03-shell", { timeout: 20000 });
  await page.waitForTimeout(1500);
  await page.screenshot({ path: path.join(OUT, "1-dashboard.png") });

  for (const [id, name] of [["equipment","2-equipment"],["control","3-control"],["analytics","4-analytics"],["settings","5-settings"],["dashboard","6-back-dashboard"]]) {
    await page.click(`#footer-nav-${id}`);
    await page.waitForTimeout(900);
    const active = await page.evaluate(() => document.getElementById("concept03-shell").getAttribute("data-active-page"));
    const heading = await page.evaluate((p) => {
      const panel = document.querySelector(".c03-page-panel--" + p);
      if (!panel) return "no-panel";
      const h = panel.querySelector("h1,h2,h3");
      return h ? h.textContent.trim().slice(0,50) : "(no heading)";
    }, id);
    console.log(`${name}: data-active-page=${active} heading="${heading}"`);
    await page.screenshot({ path: path.join(OUT, name + ".png") });
  }
  console.log("console errors:", errors.length ? errors : "none");
  await browser.close();
}
main().catch((e) => { console.error(e); process.exit(1); });
