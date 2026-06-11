// Catalog-wide GLB probe: load every scene model through the live viewer,
// verify mesh-name/role classification, record load time + renderer stats,
// and capture a real-pixels screenshot per model (WebGL canvas is black in
// page.screenshot under swiftshader — pvu3d.captureScreenshot is required).
//
// Usage:
//   node models-probe.mjs [--base <url>] [--out <dir>] [--label <name>]
//   node models-probe.mjs --compare <baseline-report.json> [...]
//
// Without --compare: writes <out>/<label>-report.json + screenshots, exit 0
// if every model loaded and produced classified meshes.
// With --compare: additionally asserts mesh-name sets and per-section role
// coverage match the baseline report exactly; exit 2 on any mismatch.

import { chromium } from "playwright";
import { mkdir, readFile, writeFile } from "node:fs/promises";
import path from "node:path";

const args = process.argv.slice(2);
const flag = (name, def) => {
  const i = args.indexOf(name);
  return i !== -1 ? args[i + 1] : def;
};
const BASE = flag("--base", process.env.QA_BASE_URL || "http://127.0.0.1:8050");
const OUT_DIR = flag("--out", "../../artifacts/playwright/scene3d/models-probe");
const LABEL = flag("--label", "models");
const COMPARE = flag("--compare", null);

// AHU models load via pvu3d.loadModel; rooms via pvu3d.setRoomTemplate.
const AHU_MODELS = [
  "ahu/master/pvu_installation.glb",
  "ahu/master/modular_ahu_pbr.glb",
  "ahu/master/modular_ahu_shaded.glb",
  "ahu/variants/base_variant_c_pbr.glb",
  "ahu/variants/base_variant_c_shaded.glb",
  "ahu/variants/industrial_hvac_unit.glb",
  "ahu/variants/industrial_machinery_unit.glb",
  "ahu/variants/base_classic.glb",
  "ahu/variants/base_variant_b.glb",
];
const ROOM_MODELS = [
  "rooms/classroom_wing.glb",
  "rooms/lab_cluster.glb",
  "rooms/office_suite.glb",
];

async function main() {
  const outAbs = path.resolve(OUT_DIR);
  await mkdir(outAbs, { recursive: true });

  const browser = await chromium.launch({
    headless: true,
    args: [
      "--use-gl=angle",
      "--use-angle=swiftshader",
      "--enable-unsafe-swiftshader",
      "--ignore-gpu-blocklist",
      "--enable-webgl",
      "--disable-dev-shm-usage",
    ],
  });
  const ctx = await browser.newContext({ viewport: { width: 1600, height: 1000 } });
  const page = await ctx.newPage();
  // Auto-quality watchdog must stay quiet under swiftshader (~3 fps).
  await page.addInitScript(() => {
    window.__pvu3dDisableAutoQuality = true;
  });
  const consoleErrors = [];
  page.on("console", (m) => {
    if (m.type() === "error") consoleErrors.push(m.text());
  });
  page.on("pageerror", (e) => consoleErrors.push(`pageerror: ${e.message}`));

  await page.goto(`${BASE}/dashboard/?theme=concept03`, {
    waitUntil: "networkidle",
    timeout: 45000,
  });
  await page.waitForFunction(
    () => !!(window.pvu3d && window.pvu3d.isInitialized && window.pvu3d.isInitialized()),
    { timeout: 30000 }
  );
  await page.waitForTimeout(3000);

  const report = { label: LABEL, base: BASE, models: {} };

  for (const relPath of AHU_MODELS) {
    const entry = await page.evaluate(async (rel) => {
      const url = "/models/" + rel.split("/").map(encodeURIComponent).join("/");
      const id = rel.split("/").pop().replace(".glb", "");
      const t0 = performance.now();
      try {
        await window.pvu3d.loadModel(url, [], { id: "probe_" + id, profile: {} });
      } catch (error) {
        return { ok: false, error: String((error && error.message) || error) };
      }
      const loadMs = Math.round(performance.now() - t0);
      await new Promise((r) => setTimeout(r, 800));
      const roles = window.pvu3d
        .getMeshRoles()
        .filter((m) => m.source === "modelRoot");
      const state = window.pvu3d.getDebugState();
      return {
        ok: true,
        loadMs,
        meshCount: roles.length,
        meshNames: roles.map((m) => m.name).sort(),
        sections: roles.reduce((acc, m) => {
          const key = m.section || m.kind || "unknown";
          acc[key] = (acc[key] || 0) + 1;
          return acc;
        }, {}),
        rendererInfo: state.rendering ? state.rendering.rendererInfo : null,
        modelSize: state.modelMetrics ? state.modelMetrics.size : null,
      };
    }, relPath);

    report.models[relPath] = entry;
    const shotName = `${LABEL}-${relPath.split("/").pop().replace(".glb", "")}.png`;
    if (entry.ok) {
      const shot = await page.evaluate(async () => {
        const res = await window.pvu3d.captureScreenshot({ scale: 1, includeMetadata: false });
        return res && res.dataUrl ? res.dataUrl : null;
      });
      if (shot) {
        await writeFile(
          path.join(outAbs, shotName),
          Buffer.from(shot.split(",")[1], "base64")
        );
        entry.screenshot = shotName;
      }
      console.log(
        `OK   ${relPath}  ${entry.loadMs}ms  ${entry.meshCount} meshes  ` +
          `${entry.rendererInfo ? entry.rendererInfo.triangles + " tris" : "?"}`
      );
    } else {
      console.log(`FAIL ${relPath}  ${entry.error}`);
    }
  }

  for (const relPath of ROOM_MODELS) {
    const entry = await page.evaluate(async (rel) => {
      const url = "/models/" + rel.split("/").map(encodeURIComponent).join("/");
      const id = rel.split("/").pop().replace(".glb", "");
      const t0 = performance.now();
      try {
        window.pvu3d.setRoomTemplate({ id: "probe_room_" + id, model_url: url });
        // Room loads lazily; poll debug state until metrics appear.
        for (let i = 0; i < 120; i++) {
          await new Promise((r) => setTimeout(r, 500));
          const state = window.pvu3d.getDebugState();
          if (
            state.activeRoom &&
            state.activeRoom.id === "probe_room_" + id &&
            state.roomMetrics
          ) {
            return {
              ok: true,
              loadMs: Math.round(performance.now() - t0),
              roomSize: state.roomMetrics.size,
              rendererInfo: state.rendering ? state.rendering.rendererInfo : null,
            };
          }
        }
        return { ok: false, error: "timeout waiting for roomMetrics" };
      } catch (error) {
        return { ok: false, error: String((error && error.message) || error) };
      }
    }, relPath);
    report.models[relPath] = entry;
    console.log(entry.ok ? `OK   ${relPath}  ${entry.loadMs}ms` : `FAIL ${relPath}  ${entry.error}`);
  }

  report.consoleErrors = consoleErrors.slice(0, 20);
  const reportPath = path.join(outAbs, `${LABEL}-report.json`);
  await writeFile(reportPath, JSON.stringify(report, null, 2));
  console.log(`report -> ${reportPath}`);

  await ctx.close();
  await browser.close();

  const failures = Object.entries(report.models).filter(([, e]) => !e.ok);
  let compareFailures = [];
  if (COMPARE) {
    const baseline = JSON.parse(await readFile(path.resolve(COMPARE), "utf8"));
    for (const [rel, baseEntry] of Object.entries(baseline.models)) {
      const current = report.models[rel];
      if (!baseEntry.ok) continue;
      if (!current || !current.ok) {
        compareFailures.push(`${rel}: loaded in baseline but failed now`);
        continue;
      }
      if (baseEntry.meshNames) {
        const a = JSON.stringify(baseEntry.meshNames);
        const b = JSON.stringify(current.meshNames);
        if (a !== b) {
          const missing = baseEntry.meshNames.filter((n) => !current.meshNames.includes(n));
          compareFailures.push(
            `${rel}: mesh-name set changed (${missing.length} missing: ${missing.slice(0, 5).join(", ")})`
          );
        }
      }
      if (baseEntry.sections) {
        const a = JSON.stringify(baseEntry.sections);
        const b = JSON.stringify(current.sections);
        if (a !== b) compareFailures.push(`${rel}: section role coverage changed ${a} -> ${b}`);
      }
    }
    compareFailures.forEach((f) => console.error(`COMPARE FAIL: ${f}`));
    if (!compareFailures.length) console.log("compare: all mesh-name sets and role coverage match baseline");
  }

  if (failures.length || compareFailures.length) process.exit(2);
}

main().catch((e) => {
  console.error(e);
  process.exit(1);
});
