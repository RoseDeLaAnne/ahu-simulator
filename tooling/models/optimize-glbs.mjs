// GLB optimization pipeline for the AHU simulator scene catalog.
//
// Per-class chains (dedup -> prune -> weld -> simplify -> quantize -> meshopt
// -> WebP) tuned for each model family. pvu_installation.glb is HARD-EXCLUDED:
// its 282 named meshes drive role classification and must stay byte-identical.
//
// Guarantees:
//   - no join()/flatten(): node/mesh names are role-classification keys
//   - mesh dedup disabled (PropertyType.MESH excluded) so mesh names survive
//   - prune({keepLeaves:true}) so empty named locator nodes survive
//   - normal maps go to lossless WebP, never lossy
//   - node/mesh name-set audit before vs after; any lost name aborts the file
//   - originals backed up to backup/ (never overwritten on re-runs)
//
// Usage: node optimize-glbs.mjs [--dry-run] [--only <substring>]
//   --dry-run  write results to report/preview/ instead of replacing in place
//   --only     process only files whose path contains <substring>

import { NodeIO, PropertyType } from "@gltf-transform/core";
import { ALL_EXTENSIONS } from "@gltf-transform/extensions";
import {
  dedup,
  prune,
  weld,
  simplify,
  quantize,
  meshopt,
  textureCompress,
} from "@gltf-transform/functions";
import { MeshoptDecoder, MeshoptEncoder, MeshoptSimplifier } from "meshoptimizer";
import sharp from "sharp";
import { copyFile, mkdir, stat, writeFile } from "node:fs/promises";
import { existsSync } from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const HERE = path.dirname(fileURLToPath(import.meta.url));
const PROJECT_ROOT = path.resolve(HERE, "..", "..");
const MODELS_DIR = path.join(PROJECT_ROOT, "models");
const BACKUP_DIR = path.join(HERE, "backup");
const REPORT_DIR = path.join(HERE, "report");
const PREVIEW_DIR = path.join(REPORT_DIR, "preview");

const HARD_EXCLUDED = new Set(["ahu/master/pvu_installation.glb"]);

const MODEL_CLASSES = {
  heavy_scan: {
    files: [
      "ahu/variants/industrial_hvac_unit.glb",
      "ahu/variants/industrial_machinery_unit.glb",
    ],
    simplify: { ratio: 0.4, error: 1e-3 },
    textures: { maxSize: 2048, quality: 85 },
  },
  pbr_authored: {
    files: [
      "ahu/variants/base_variant_c_pbr.glb",
      "ahu/master/modular_ahu_pbr.glb",
    ],
    simplify: { ratio: 0.6, error: 5e-4 },
    textures: { maxSize: 2048, quality: 85 },
  },
  shaded_light: {
    files: [
      "ahu/master/modular_ahu_shaded.glb",
      "ahu/variants/base_variant_c_shaded.glb",
      "ahu/variants/base_classic.glb",
      "ahu/variants/base_variant_b.glb",
    ],
    simplify: { ratio: 0.6, error: 5e-4 },
    textures: { maxSize: 2048, quality: 85 },
  },
  rooms: {
    files: [
      "rooms/classroom_wing.glb",
      "rooms/lab_cluster.glb",
      "rooms/office_suite.glb",
    ],
    simplify: { ratio: 0.3, error: 1e-3 },
    textures: { maxSize: 1024, quality: 80 },
  },
};

const args = process.argv.slice(2);
const DRY_RUN = args.includes("--dry-run");
const onlyIdx = args.indexOf("--only");
const ONLY = onlyIdx !== -1 ? args[onlyIdx + 1] : null;

function collectNames(document) {
  const root = document.getRoot();
  return {
    nodes: new Set(root.listNodes().map((n) => n.getName()).filter(Boolean)),
    meshes: new Set(root.listMeshes().map((m) => m.getName()).filter(Boolean)),
  };
}

function countVertices(document) {
  let total = 0;
  for (const mesh of document.getRoot().listMeshes()) {
    for (const prim of mesh.listPrimitives()) {
      const position = prim.getAttribute("POSITION");
      if (position) total += position.getCount();
    }
  }
  return total;
}

function diffNames(before, after) {
  return [...before].filter((name) => !after.has(name));
}

async function processFile(io, relPath, className, classConfig) {
  const srcPath = path.join(MODELS_DIR, relPath);
  if (!existsSync(srcPath)) {
    return { file: relPath, class: className, status: "missing" };
  }
  const startedAt = Date.now();
  const bytesBefore = (await stat(srcPath)).size;

  const document = await io.read(srcPath);
  const namesBefore = collectNames(document);
  const vertsBefore = countVertices(document);

  await document.transform(
    // MESH excluded: duplicate-named meshes must keep their identities.
    dedup({
      propertyTypes: [
        PropertyType.ACCESSOR,
        PropertyType.MATERIAL,
        PropertyType.TEXTURE,
        PropertyType.SKIN,
      ],
    }),
    prune({ keepLeaves: true }),
    weld({}),
    simplify({
      simplifier: MeshoptSimplifier,
      ratio: classConfig.simplify.ratio,
      error: classConfig.simplify.error,
      lockBorder: true,
    }),
    quantize(),
    meshopt({ encoder: MeshoptEncoder, level: "medium" }),
    // Lossy WebP for everything except normal maps...
    textureCompress({
      encoder: sharp,
      targetFormat: "webp",
      quality: classConfig.textures.quality,
      resize: [classConfig.textures.maxSize, classConfig.textures.maxSize],
      slots: /^(?!normalTexture).*$/,
    }),
    // ...normal maps stay lossless (artifacts there warp lighting).
    textureCompress({
      encoder: sharp,
      targetFormat: "webp",
      lossless: true,
      resize: [classConfig.textures.maxSize, classConfig.textures.maxSize],
      slots: /^normalTexture$/,
    })
  );

  const namesAfter = collectNames(document);
  const lostNodes = diffNames(namesBefore.nodes, namesAfter.nodes);
  const lostMeshes = diffNames(namesBefore.meshes, namesAfter.meshes);
  if (lostNodes.length || lostMeshes.length) {
    return {
      file: relPath,
      class: className,
      status: "aborted_name_loss",
      lostNodes,
      lostMeshes,
    };
  }

  let outPath;
  if (DRY_RUN) {
    outPath = path.join(PREVIEW_DIR, relPath);
    await mkdir(path.dirname(outPath), { recursive: true });
  } else {
    const backupPath = path.join(BACKUP_DIR, relPath);
    await mkdir(path.dirname(backupPath), { recursive: true });
    if (!existsSync(backupPath)) {
      await copyFile(srcPath, backupPath);
    }
    outPath = srcPath;
  }
  await io.write(outPath, document);

  const bytesAfter = (await stat(outPath)).size;
  return {
    file: relPath,
    class: className,
    status: "ok",
    bytesBefore,
    bytesAfter,
    bytesRatio: +(bytesAfter / bytesBefore).toFixed(3),
    vertsBefore,
    vertsAfter: countVertices(document),
    nodeNames: namesAfter.nodes.size,
    meshNames: namesAfter.meshes.size,
    ms: Date.now() - startedAt,
    output: DRY_RUN ? path.relative(PROJECT_ROOT, outPath) : "in-place",
  };
}

async function main() {
  await Promise.all([MeshoptDecoder.ready, MeshoptEncoder.ready, MeshoptSimplifier.ready]);

  const io = new NodeIO()
    .registerExtensions(ALL_EXTENSIONS)
    .registerDependencies({
      "meshopt.decoder": MeshoptDecoder,
      "meshopt.encoder": MeshoptEncoder,
    });

  await mkdir(REPORT_DIR, { recursive: true });

  const results = [];
  for (const [className, classConfig] of Object.entries(MODEL_CLASSES)) {
    for (const relPath of classConfig.files) {
      if (HARD_EXCLUDED.has(relPath)) {
        throw new Error(`Hard-excluded file in class list: ${relPath}`);
      }
      if (ONLY && !relPath.includes(ONLY)) continue;
      process.stdout.write(`[${className}] ${relPath} ... `);
      try {
        const result = await processFile(io, relPath, className, classConfig);
        results.push(result);
        if (result.status === "ok") {
          const mb = (n) => (n / 1024 / 1024).toFixed(1);
          console.log(
            `${mb(result.bytesBefore)}MB -> ${mb(result.bytesAfter)}MB, ` +
              `${result.vertsBefore} -> ${result.vertsAfter} verts, ${result.ms}ms`
          );
        } else {
          console.log(result.status);
        }
      } catch (error) {
        console.log(`ERROR: ${error.message}`);
        results.push({ file: relPath, class: className, status: "error", error: String(error.message) });
      }
    }
  }

  const summary = {
    dryRun: DRY_RUN,
    totalBefore: results.reduce((n, r) => n + (r.bytesBefore || 0), 0),
    totalAfter: results.reduce((n, r) => n + (r.bytesAfter || 0), 0),
    files: results,
  };
  const reportPath = path.join(REPORT_DIR, "optimize-report.json");
  await writeFile(reportPath, JSON.stringify(summary, null, 2));

  const mb = (n) => (n / 1024 / 1024).toFixed(1);
  console.log(`\nTotal: ${mb(summary.totalBefore)}MB -> ${mb(summary.totalAfter)}MB`);
  console.log(`Report: ${reportPath}`);

  const failed = results.filter((r) => r.status !== "ok" && r.status !== "missing");
  if (failed.length) {
    console.error(`FAILED files: ${failed.map((r) => r.file).join(", ")}`);
    process.exit(2);
  }
}

main().catch((error) => {
  console.error(error);
  process.exit(1);
});
