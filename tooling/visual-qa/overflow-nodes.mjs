// Node-level overflow detector for Problem D (Cyrillic text clipping).
// Finds elements whose content is horizontally clipped (scrollWidth>clientWidth)
// while having real text, plus elements spilling past the viewport. Reports a
// deduped-by-class summary so the sweep targets real offenders, not all 35 rules.
// Usage: node overflow-nodes.mjs [--w 1500] [--h 900] [--query "?theme=concept03&defense=true"] [--top 40]

import { chromium } from "playwright";

const args = process.argv.slice(2);
const flag = (name, def) => {
  const i = args.indexOf(name);
  return i !== -1 ? args[i + 1] : def;
};
const W = Number(flag("--w", "1500"));
const H = Number(flag("--h", "900"));
const QUERY = flag("--query", "?theme=concept03&defense=true");
const TOP = Number(flag("--top", "40"));
const BASE = flag("--base", "http://127.0.0.1:8050");

const browser = await chromium.launch({
  headless: true,
  args: ["--use-gl=angle", "--use-angle=swiftshader", "--enable-unsafe-swiftshader", "--disable-dev-shm-usage"],
});
const ctx = await browser.newContext({ viewport: { width: W, height: H } });
const page = await ctx.newPage();
await page.goto(`${BASE}/dashboard/${QUERY}`, { waitUntil: "networkidle", timeout: 45000 });
await page.waitForSelector("#concept03-shell", { timeout: 20000 });
await page.waitForTimeout(1500);

const data = await page.evaluate((vpW) => {
  const clip = [];
  const spill = [];
  const all = document.querySelectorAll("body *");
  for (const el of all) {
    const cs = getComputedStyle(el);
    if (cs.display === "none" || cs.visibility === "hidden") continue;
    const r = el.getBoundingClientRect();
    if (r.width === 0 || r.height === 0) continue;
    const cls = (el.className && el.className.baseVal !== undefined ? el.className.baseVal : el.className) || "";
    const clsStr = String(cls).trim();
    // direct text only (ignore container scrollWidth from children layout)
    const ownText = Array.from(el.childNodes)
      .filter((n) => n.nodeType === 3)
      .map((n) => n.textContent.trim())
      .join("")
      .trim();
    // horizontal text clip: nowrap + hidden + scrollWidth exceeds clientWidth
    if (
      el.scrollWidth > el.clientWidth + 1 &&
      ownText.length > 1 &&
      (cs.textOverflow === "ellipsis" || cs.overflowX === "hidden" || cs.whiteSpace === "nowrap")
    ) {
      const parent = el.parentElement;
      const pcls = parent
        ? String(
            (parent.className && parent.className.baseVal !== undefined
              ? parent.className.baseVal
              : parent.className) || ""
          ).trim()
        : "";
      clip.push({
        cls: clsStr,
        parentCls: pcls,
        tag: el.tagName.toLowerCase(),
        scrollW: el.scrollWidth,
        clientW: el.clientWidth,
        clipPx: el.scrollWidth - el.clientWidth,
        whiteSpace: cs.whiteSpace,
        textOverflow: cs.textOverflow,
        text: ownText.slice(0, 40),
      });
    }
    // element spilling past the right viewport edge
    if (r.right > vpW + 1 && clsStr) {
      spill.push({ cls: clsStr, tag: el.tagName.toLowerCase(), right: Math.round(r.right) });
    }
  }
  // dedupe clip by own class token, falling back to parentClass>tag for unclassed nodes
  const byClass = {};
  for (const c of clip) {
    const ownKey = c.cls.split(/\s+/)[0];
    const key = ownKey || (c.parentCls.split(/\s+/)[0] || "") + ">" + c.tag;
    if (!byClass[key]) byClass[key] = { key, count: 0, sample: c };
    byClass[key].count += 1;
  }
  return {
    docOverflow: document.documentElement.scrollWidth > document.documentElement.clientWidth + 1,
    clipGroups: Object.values(byClass).sort((a, b) => b.count - a.count),
    spillCount: spill.length,
    spillSample: spill.slice(0, 10),
  };
}, W);

const out = {
  viewport: `${W}x${H}`,
  query: QUERY,
  docOverflow: data.docOverflow,
  clipGroups: data.clipGroups.slice(0, TOP),
  totalClipGroups: data.clipGroups.length,
  spillCount: data.spillCount,
  spillSample: data.spillSample,
};
console.log(JSON.stringify(out, null, 2));
await browser.close();
