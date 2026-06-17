import { chromium } from "playwright";
import fs from "node:fs";

const BASE = process.env.QA_BASE_URL || "http://127.0.0.1:8050";

const browser = await chromium.launch({
  headless: true,
  args: ["--use-gl=angle", "--use-angle=swiftshader", "--enable-unsafe-swiftshader", "--disable-dev-shm-usage"],
});
const ctx = await browser.newContext({ viewport: { width: 375, height: 812 } });
const page = await ctx.newPage();
await page.goto(`${BASE}/dashboard/?theme=concept03`, { waitUntil: "networkidle", timeout: 45000 });
await page.waitForSelector("#concept03-shell", { timeout: 20000 });
await page.waitForTimeout(3500);
fs.mkdirSync("out-kpi", { recursive: true });
const kpi = page.locator(".c03-kpi-list").first();
await kpi.scrollIntoViewIfNeeded();
await page.waitForTimeout(500);
await kpi.screenshot({ path: "out-kpi/kpi-mobile.png" });
console.log("saved out-kpi/kpi-mobile.png");
await browser.close();
