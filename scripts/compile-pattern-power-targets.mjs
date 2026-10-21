import { createHash } from "node:crypto";
import { readFile, writeFile } from "node:fs/promises";
import { loadImage } from "canvas";
import { decode } from "@msgpack/msgpack";
import { OfflineCompiler } from "mind-ar/src/image-target/offline-compiler.js";

const targetPaths = [
  "printed_page_1_shapes_all_in_a_row.png",
  "printed_page_3_red_blue_red.png",
  "printed_page_5_the_mixed_up_pattern.png",
  "printed_page_6_fixing_the_bug.png",
  "printed_page_7_sorting_by_size.png",
  "printed_page_8_natures_patterns.png",
  "printed_page_12_your_turn_and_cheers.png",
];

async function compile(paths, outputPath) {
  const images = [];
  for (const path of paths) {
    const bytes = await readFile(path);
    const image = await loadImage(bytes);
    if (image.width < 500 || image.height < 350) {
      throw new Error(`Target image is unexpectedly small: ${path} (${image.width}x${image.height})`);
    }
    const sha256 = createHash("sha256").update(bytes).digest("hex");
    console.log(`SOURCE ${path}: ${image.width}x${image.height}; ${bytes.length} bytes; sha256=${sha256}`);
    images.push(image);
  }

  const compiler = new OfflineCompiler();
  await compiler.compileImageTargets(images, (progress) => {
    console.log(`COMPILING ${outputPath}: ${progress.toFixed(2)}%`);
  });

  const buffer = Buffer.from(compiler.exportData());
  const parsed = decode(buffer);
  if (parsed?.v !== 2 || !Array.isArray(parsed.dataList) || parsed.dataList.length !== paths.length) {
    throw new Error(`MindAR output validation failed for ${outputPath}: version/target count mismatch`);
  }

  for (const [index, target] of parsed.dataList.entries()) {
    if (!target?.targetImage?.width || !target?.targetImage?.height) {
      throw new Error(`Target ${index} has invalid image dimensions in ${outputPath}`);
    }
    if (!target?.matchingData?.length || !target?.trackingData?.length) {
      throw new Error(`Target ${index} is missing matching/tracking features in ${outputPath}`);
    }
    console.log(`VALID TARGET ${index}: ${target.targetImage.width}x${target.targetImage.height}`);
  }

  await writeFile(outputPath, buffer);
  console.log(`PASS ${outputPath}: ${buffer.length} bytes; version=2; targets=${parsed.dataList.length}`);
}

await compile(["printed_page_5_the_mixed_up_pattern.png"], "targets-page5.mind");
await compile(targetPaths, "targets.mind");
