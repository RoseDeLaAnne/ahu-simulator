import { chromium } from "playwright";
const BASE = "http://127.0.0.1:8050";
const b = await chromium.launch({ headless: true, args: ["--use-gl=angle","--use-angle=swiftshader","--enable-unsafe-swiftshader","--disable-dev-shm-usage"] });
const p = await b.newContext({ viewport: { width: 1600, height: 950 } }).then(c=>c.newPage());
await p.goto(`${BASE}/dashboard/?theme=concept03`, { waitUntil: "networkidle", timeout: 60000 });
await p.waitForSelector("#concept03-shell", { timeout: 20000 });
await p.click('[data-tab-id="3d"]').catch(()=>{});
await p.waitForTimeout(4000);
const info = await p.evaluate(() => {
  const layer = document.getElementById("concept03-callout-layer");
  const vp = document.getElementById("concept03-scene-3d-viewport");
  const cs = layer ? getComputedStyle(layer) : null;
  const first = layer && layer.querySelector("[data-scene-node]");
  const fcs = first ? getComputedStyle(first) : null;
  const fr = first ? first.getBoundingClientRect() : null;
  // walk ancestors to find a display:none
  let hiddenAncestor = null;
  let el = first;
  while (el && el !== document.body) {
    const d = getComputedStyle(el);
    if (d.display === "none" || d.visibility === "hidden") { hiddenAncestor = (el.id||el.className||el.tagName) + " => display:"+d.display+" vis:"+d.visibility; break; }
    el = el.parentElement;
  }
  return {
    bodyClass: document.body.className,
    viewportSceneMode: vp ? vp.getAttribute("data-concept03-scene-mode") : "NO-VP",
    layerDisplay: cs ? cs.display : "NO-LAYER",
    layerW: layer ? layer.clientWidth : -1,
    layerH: layer ? layer.clientHeight : -1,
    firstDisplay: fcs ? fcs.display : null,
    firstRect: fr ? {x:Math.round(fr.x), y:Math.round(fr.y), w:Math.round(fr.width), h:Math.round(fr.height)} : null,
    firstCalloutX: first ? first.style.getPropertyValue("--callout-x") : null,
    firstPositioned: first ? first.getAttribute("data-positioned") : null,
    hiddenAncestor,
  };
});
console.log(JSON.stringify(info, null, 2));
await b.close();
