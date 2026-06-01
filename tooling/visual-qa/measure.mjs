import { chromium } from "playwright";
const sel = process.argv.slice(2);
const browser = await chromium.launch({ headless: true, args: ["--use-gl=angle","--use-angle=swiftshader","--enable-unsafe-swiftshader"] });
const ctx = await browser.newContext({ viewport: { width: 1500, height: 900 } });
const page = await ctx.newPage();
await page.goto("http://127.0.0.1:8050/dashboard/?theme=concept03&defense=true", { waitUntil: "networkidle" });
await page.waitForSelector("#concept03-shell", { timeout: 20000 });
await page.waitForTimeout(1500);
const data = await page.evaluate(() => {
  const out = {};
  const pick = (label, el) => {
    if (!el) return (out[label] = null);
    const r = el.getBoundingClientRect();
    out[label] = { x: Math.round(r.x), w: Math.round(r.width), scrollW: el.scrollWidth, clientW: el.clientWidth };
  };
  pick("header", document.querySelector(".c03-header"));
  pick("brand", document.querySelector(".c03-brand"));
  pick("title", document.querySelector(".c03-installation-title--defense"));
  pick("h1", document.querySelector(".c03-installation-title--defense h1"));
  pick("spacer", document.querySelector(".c03-header__spacer"));
  pick("toolbar", document.querySelector(".c03-action-toolbar"));
  pick("meta", document.querySelector(".c03-header-meta"));
  pick("links", document.querySelector(".c03-header-links"));
  pick("datetime", document.querySelector(".c03-datetime"));
  const h1 = document.querySelector(".c03-installation-title--defense h1");
  if (h1) out.h1_text = h1.textContent;
  const cs = h1 ? getComputedStyle(h1) : null;
  if (cs) out.h1_css = { fontSize: cs.fontSize, whiteSpace: cs.whiteSpace, overflow: cs.overflow };
  const tcs = document.querySelector(".c03-installation-title--defense");
  if (tcs) { const c = getComputedStyle(tcs); out.title_css = { display: c.display, flex: c.flex, maxWidth: c.maxWidth, minWidth: c.minWidth, width: c.width }; }
  const scs = document.querySelector(".c03-header__spacer");
  if (scs) out.spacer_display = getComputedStyle(scs).display;
  return out;
});
console.log(JSON.stringify(data, null, 2));
await browser.close();
