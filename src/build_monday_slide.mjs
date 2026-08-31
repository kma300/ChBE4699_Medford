import fs from "node:fs/promises";
import path from "node:path";
import { fileURLToPath, pathToFileURL } from "node:url";


const nodeRoot = path.resolve(path.dirname(process.execPath), "..");
const artifactModule = path.join(
  nodeRoot,
  "node_modules/@oai/artifact-tool/dist/artifact_tool.mjs",
);
const { Presentation, PresentationFile } = await import(pathToFileURL(artifactModule).href);
const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const outputDir = `${root}/outputs`;

async function writeBlob(path, blob) {
  await fs.writeFile(path, new Uint8Array(await blob.arrayBuffer()));
}

function addText(slide, name, text, position, style = {}) {
  const shape = slide.shapes.add({
    geometry: "textbox",
    name,
    position,
    fill: "none",
    line: { style: "solid", fill: "none", width: 0 },
  });
  shape.text = text;
  shape.text.style = {
    typeface: "Aptos",
    fontSize: 18,
    color: "#162236",
    verticalAlignment: "middle",
    autoFit: "shrinkText",
    insets: { top: 0, right: 0, bottom: 0, left: 0 },
    ...style,
  };
  return shape;
}

function addCard(slide, name, position, fill = "#FFFFFF") {
  return slide.shapes.add({
    geometry: "roundRect",
    name,
    position,
    fill,
    line: { style: "solid", fill: "#D9E2EC", width: 1 },
    borderRadius: 18,
    shadow: "shadow-sm",
  });
}

const presentation = Presentation.create({ slideSize: { width: 1280, height: 720 } });
presentation.theme.colorScheme = {
  name: "Medford Process Panel",
  themeColors: {
    accent1: "#3D8DFF",
    accent2: "#0A7780",
    accent3: "#FFCB47",
    accent4: "#E45756",
    accent5: "#6DCBF4",
    accent6: "#5DBB63",
    bg1: "#F7F9FC",
    bg2: "#FFFFFF",
    tx1: "#162236",
    tx2: "#526071",
    dk1: "#0B1423",
    dk2: "#162236",
    lt1: "#FFFFFF",
    lt2: "#D9E2EC",
    hlink: "#2563EB",
    folHlink: "#7C3AED",
  },
};

const slide = presentation.slides.add();
slide.background.fill = "#F7F9FC";

slide.shapes.add({
  geometry: "rect",
  name: "top-accent",
  position: { left: 0, top: 0, width: 1280, height: 12 },
  fill: "#3D8DFF",
  line: { style: "solid", fill: "none", width: 0 },
});
addText(
  slide,
  "eyebrow",
  "MONDAY UPDATE · ETHYLENE-CRACKER OUTLET · COMPUTED PAIRS ONLY",
  { left: 64, top: 28, width: 760, height: 24 },
  { fontSize: 13, bold: true, color: "#3D8DFF" },
);
addText(
  slide,
  "title",
  "Eight process gases share a complete 471-MOF comparison set",
  { left: 64, top: 56, width: 1150, height: 48 },
  { typeface: "Aptos Display", fontSize: 35, bold: true, color: "#162236" },
);
addText(
  slide,
  "subtitle",
  "The panel is ready for an apples-to-apples MOF screen; coverage alone cannot choose among the gases.",
  { left: 64, top: 110, width: 1110, height: 30 },
  { fontSize: 18, color: "#526071" },
);

addCard(slide, "coverage-card", { left: 64, top: 170, width: 670, height: 368 });
addText(
  slide,
  "coverage-heading",
  "Directly computed coverage",
  { left: 90, top: 188, width: 360, height: 28 },
  { fontSize: 20, bold: true, color: "#162236" },
);
addText(
  slide,
  "coverage-note",
  "All eight gases share the same 471 MOFs (24.3% of 1,940)",
  { left: 90, top: 216, width: 500, height: 22 },
  { fontSize: 13, color: "#526071" },
);
slide.charts.add("bar", {
  position: { left: 86, top: 244, width: 620, height: 268 },
  categories: [
    "Methane",
    "Ethane",
    "Ethylene",
    "Propane",
    "Propylene",
    "Isobutane",
    "Isopentane",
    "2-Pentene",
  ],
  series: [
    {
      name: "Computed MOFs",
      values: [471, 471, 471, 471, 471, 471, 471, 471],
      fill: "#3D8DFF",
      points: [
        { idx: 5, fill: "#6DCBF4" },
        { idx: 6, fill: "#6DCBF4" },
        { idx: 7, fill: "#6DCBF4" },
      ],
    },
  ],
  hasLegend: false,
  barOptions: { direction: "bar", grouping: "clustered", gapWidth: 38 },
  xAxis: {
    visible: true,
    min: 0,
    max: 500,
    majorUnit: 100,
    numberFormatCode: "0",
    textStyle: { fontSize: 10, fill: "#526071" },
    line: { style: "solid", fill: "#D9E2EC", width: 1 },
    majorGridlines: { style: "solid", fill: "#D9E2EC", width: 1 },
  },
  yAxis: {
    visible: true,
    textStyle: { fontSize: 11, fill: "#162236" },
    line: { style: "solid", fill: "none", width: 0 },
    majorGridlines: null,
  },
  dataLabels: {
    showValue: true,
    position: "outEnd",
    textStyle: { fontSize: 11, bold: true, fill: "#162236" },
  },
  chartFill: "#FFFFFF",
  chartLine: { style: "solid", fill: "none", width: 0 },
  plotAreaFill: "#FFFFFF",
  plotAreaLine: { style: "solid", fill: "none", width: 0 },
});

addCard(slide, "panel-card", { left: 754, top: 170, width: 462, height: 368 });
addText(
  slide,
  "panel-heading",
  "Eight-gas target panel",
  { left: 782, top: 190, width: 380, height: 28 },
  { fontSize: 20, bold: true, color: "#162236" },
);
addText(
  slide,
  "core-label",
  "CORE FEED / PRODUCT GROUP",
  { left: 782, top: 232, width: 255, height: 20 },
  { fontSize: 11, bold: true, color: "#3D8DFF" },
);
addText(
  slide,
  "core-list",
  "Methane\nEthane  →  Ethylene\nPropane  →  Propylene",
  { left: 782, top: 258, width: 252, height: 104 },
  { fontSize: 19, bold: true, color: "#162236", lineSpacing: 1.12 },
);
slide.shapes.add({
  geometry: "line",
  name: "panel-divider",
  position: { left: 1049, top: 232, width: 0, height: 130 },
  fill: "none",
  line: { style: "solid", fill: "#D9E2EC", width: 1 },
});
addText(
  slide,
  "proxy-label",
  "C4 / C5 PROXIES",
  { left: 1072, top: 232, width: 120, height: 20 },
  { fontSize: 11, bold: true, color: "#0A7780" },
);
addText(
  slide,
  "proxy-list",
  "Isobutane\nIsopentane\n2-Pentene",
  { left: 1072, top: 258, width: 122, height: 104 },
  { fontSize: 18, bold: true, color: "#162236", lineSpacing: 1.12 },
);

slide.shapes.add({
  geometry: "roundRect",
  name: "pairs-stat",
  position: { left: 782, top: 390, width: 190, height: 104 },
  fill: "#E8F1FF",
  line: { style: "solid", fill: "none", width: 0 },
  borderRadius: 14,
});
addText(
  slide,
  "pairs-number",
  "3,768",
  { left: 800, top: 403, width: 154, height: 42 },
  { typeface: "Aptos Display", fontSize: 34, bold: true, color: "#162236", alignment: "center" },
);
addText(
  slide,
  "pairs-label",
  "computed pairs",
  { left: 800, top: 448, width: 154, height: 24 },
  { fontSize: 13, bold: true, color: "#526071", alignment: "center" },
);
slide.shapes.add({
  geometry: "roundRect",
  name: "mofs-stat",
  position: { left: 990, top: 390, width: 198, height: 104 },
  fill: "#EAF7F8",
  line: { style: "solid", fill: "none", width: 0 },
  borderRadius: 14,
});
addText(
  slide,
  "mofs-number",
  "471",
  { left: 1008, top: 403, width: 162, height: 42 },
  { typeface: "Aptos Display", fontSize: 34, bold: true, color: "#0A7780", alignment: "center" },
);
addText(
  slide,
  "mofs-label",
  "common MOFs",
  { left: 1008, top: 448, width: 162, height: 24 },
  { fontSize: 13, bold: true, color: "#526071", alignment: "center" },
);

slide.shapes.add({
  geometry: "roundRect",
  name: "dataset-strip",
  position: { left: 64, top: 556, width: 1152, height: 48 },
  fill: "#162236",
  line: { style: "solid", fill: "none", width: 0 },
  borderRadius: 12,
});
addText(
  slide,
  "dataset-stats",
  "FULL COMPUTED DATASET    16,628 pairs   ·   1,940 MOFs   ·   113 molecules   ·   300 K   ·   linear K",
  { left: 88, top: 568, width: 1104, height: 24 },
  { fontSize: 15, bold: true, color: "#FFFFFF", alignment: "center" },
);

slide.shapes.add({
  geometry: "roundRect",
  name: "next-strip",
  position: { left: 64, top: 620, width: 1152, height: 62 },
  fill: "#FFCB47",
  line: { style: "solid", fill: "none", width: 0 },
  borderRadius: 12,
});
addText(
  slide,
  "next-label",
  "NEXT",
  { left: 88, top: 636, width: 62, height: 26 },
  { fontSize: 13, bold: true, color: "#162236", alignment: "center" },
);
addText(
  slide,
  "next-step",
  "Select 12 MOFs  →  test gas identification, composition drift & product/feed ratios  →  reduce if performance holds",
  { left: 168, top: 632, width: 1014, height: 34 },
  { fontSize: 18, bold: true, color: "#162236" },
);

slide.speakerNotes.textFrame.setText(`Conditioned outlet means an extractive, post-quench/sample-conditioned sidestream near 300 K—not a MOF placed directly in the raw furnace effluent. The C4/C5 targets are coverage-matched process-gas proxies, not universal claims about dominant cracker products.

[Sources]
- https://zenodo.org/records/16754752 (D-MOPH-25 deposited computed data; accessed 2026-08-30)
- https://doi.org/10.1088/2632-2153/ae0241 (dataset methods, units, 300 K, and active-learning inventory)
- https://www.epa.gov/sites/default/files/2015-03/documents/subpartx-tsd-petrochem.pdf (ethylene-process context)
- https://cache.industry.siemens.com/dl/files/563/109770563/att_995347/v1/PIAAP-00002-0118-Ethylene.pdf (conditioned extractive furnace-effluent analysis context)
[/Sources]`);
slide.speakerNotes.setVisible(true);

const inspection = await presentation.inspect({
  kind: "slide,textbox,shape,chart,notes",
  maxChars: 12000,
});
console.log(inspection.ndjson);

await fs.mkdir(outputDir, { recursive: true });
await writeBlob(
  `${outputDir}/monday_update_ethylene_cracker_preview.png`,
  await presentation.export({ slide, format: "png", scale: 1 }),
);
const layout = await slide.export({ format: "layout" });
await fs.writeFile(
  `${outputDir}/monday_update_ethylene_cracker.layout.json`,
  await layout.text(),
);
const pptx = await PresentationFile.exportPptx(presentation);
await pptx.save(`${outputDir}/monday_update_ethylene_cracker.pptx`);
console.log(`saved=${outputDir}/monday_update_ethylene_cracker.pptx`);
