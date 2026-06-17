import { chromium } from "playwright";
const BASE = "http://127.0.0.1:8050";
const b = await chromium.launch({ headless: true, args: ["--use-gl=angle","--use-angle=swiftshader","--enable-unsafe-swiftshader","--disable-dev-shm-usage"] });
const p = await b.newContext({ viewport: { width: 1600, height: 950 } }).then(c=>c.newPage());
await p.goto(`${BASE}/dashboard/?theme=concept03`, { waitUntil: "networkidle", timeout: 60000 });
await p.waitForSelector("#concept03-shell", { timeout: 20000 });
await p.click('[data-tab-id="3d"]').catch(()=>{});
await p.waitForFunction(() => window.pvu3d && window.pvu3d.isInitialized && window.pvu3d.isInitialized() && window.pvu3d.getDebugState().modelMetrics, { timeout: 30000 }).catch(()=>{});
await p.waitForTimeout(3000);
const out = await p.evaluate(() => {
  const s = window.pvu3d.getDebugState();
  const am = s.activeModel || {};
  return {
    sceneMode: document.getElementById("concept03-scene-3d-viewport")?.getAttribute("data-concept03-scene-mode"),
    modelId: am.id,
    transform: am.profile && am.profile.transform ? am.profile.transform : "(no profile.transform)",
    modelSize: s.modelMetrics && s.modelMetrics.size.map(n=>+n.toFixed(3)),
    modelScale: s.modelMetrics && s.modelMetrics.scale.map(n=>+n.toFixed(3)),
  };
});
console.log(JSON.stringify(out, null, 2));
await b.close();
