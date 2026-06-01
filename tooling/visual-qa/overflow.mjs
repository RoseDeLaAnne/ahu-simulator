// Report horizontal overflow for a viewport size.
// Usage: node overflow.mjs <w> <h> [query]
import { chromium } from "playwright";
const [w, h, q] = process.argv.slice(2);
const W = Number(w), H = Number(h);
const query = q || "?theme=concept03";
const browser = await chromium.launch({ headless: true, args: ["--use-gl=angle","--use-angle=swiftshader","--enable-unsafe-swiftshader"] });
const ctx = await browser.newContext({ viewport: { width: W, height: H } });
const page = await ctx.newPage();
await page.goto(`http://127.0.0.1:8050/dashboard/${query}`, { waitUntil: "networkidle" });
await page.waitForSelector("#concept03-shell", { timeout: 20000 });
await page.waitForTimeout(1500);
const r = await page.evaluate(() => ({
  scrollW: document.documentElement.scrollWidth,
  clientW: document.documentElement.clientWidth,
  bodyScrollW: document.body.scrollWidth,
}));
console.log(JSON.stringify({ viewport: `${W}x${H}`, ...r, horizontalOverflow: r.scrollW > r.clientW + 1 }));
await browser.close();
