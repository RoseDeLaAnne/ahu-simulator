// Pixel-diff two PNGs of identical dimensions and report % mismatch.
// Usage: node diff.mjs <a.png> <b.png> [out-diff.png] [--threshold 0.1]
// Intended for REGRESSION diffs (before/after my own changes, or vs a saved
// baseline) — not for literal comparison against the AI concept renders,
// which differ by construction (photoreal 3D, different fonts).

import { readFileSync, writeFileSync } from "node:fs";
import { PNG } from "pngjs";
import pixelmatch from "pixelmatch";

const args = process.argv.slice(2);
const [aPath, bPath, outPath] = args.filter((a) => !a.startsWith("--"));
const thrIdx = args.indexOf("--threshold");
const threshold = thrIdx !== -1 ? parseFloat(args[thrIdx + 1]) : 0.1;

if (!aPath || !bPath) {
  console.error("Usage: node diff.mjs <a.png> <b.png> [out-diff.png] [--threshold 0.1]");
  process.exit(2);
}

const a = PNG.sync.read(readFileSync(aPath));
const b = PNG.sync.read(readFileSync(bPath));

if (a.width !== b.width || a.height !== b.height) {
  console.error(`Dimension mismatch: ${a.width}x${a.height} vs ${b.width}x${b.height}`);
  process.exit(3);
}

const { width, height } = a;
const diff = new PNG({ width, height });
const mismatched = pixelmatch(a.data, b.data, diff.data, width, height, { threshold });
const total = width * height;
const pct = (mismatched / total) * 100;

if (outPath) writeFileSync(outPath, PNG.sync.write(diff));

console.log(JSON.stringify({
  a: aPath, b: bPath,
  dimensions: `${width}x${height}`,
  mismatchedPixels: mismatched,
  totalPixels: total,
  percent: Number(pct.toFixed(3)),
  out: outPath || null,
}, null, 2));
