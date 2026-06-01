// Crop a region from a PNG for detailed visual inspection.
// Usage: node crop.mjs <in.png> <out.png> <x> <y> <w> <h>
//        node crop.mjs <in.png> --dims         (just print dimensions)
import { readFileSync, writeFileSync } from "node:fs";
import { PNG } from "pngjs";

const [inPath, a, b, c, d, e] = process.argv.slice(2);
const src = PNG.sync.read(readFileSync(inPath));
if (a === "--dims") {
  console.log(JSON.stringify({ width: src.width, height: src.height }));
  process.exit(0);
}
let [x, y, w, h] = [a, b, c, d].map((n) => Math.round(Number(n)));
const out = e; // out path is 2nd arg actually; adjust below
// Re-parse: signature is <in> <out> <x> <y> <w> <h>
const outPath = a;
[x, y, w, h] = [b, c, d, e].map((n) => Math.round(Number(n)));
x = Math.max(0, Math.min(x, src.width - 1));
y = Math.max(0, Math.min(y, src.height - 1));
w = Math.max(1, Math.min(w, src.width - x));
h = Math.max(1, Math.min(h, src.height - y));
const dst = new PNG({ width: w, height: h });
for (let row = 0; row < h; row++) {
  for (let col = 0; col < w; col++) {
    const si = ((y + row) * src.width + (x + col)) << 2;
    const di = (row * w + col) << 2;
    dst.data[di] = src.data[si];
    dst.data[di + 1] = src.data[si + 1];
    dst.data[di + 2] = src.data[si + 2];
    dst.data[di + 3] = src.data[si + 3];
  }
}
writeFileSync(outPath, PNG.sync.write(dst));
console.log(`cropped ${w}x${h} from (${x},${y}) -> ${outPath}`);
