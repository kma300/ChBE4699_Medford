import fs from "node:fs/promises";
import path from "node:path";
import { fileURLToPath, pathToFileURL } from "node:url";


const nodeRoot = path.resolve(path.dirname(process.execPath), "..");
const artifactModule = path.join(
  nodeRoot,
  "node_modules/@oai/artifact-tool/dist/artifact_tool.mjs",
);
const { SpreadsheetFile, Workbook } = await import(pathToFileURL(artifactModule).href);
const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const outputDir = `${root}/outputs`;
const csvText = await fs.readFile(`${outputDir}/coverage_table.csv`, "utf8");

const workbook = await Workbook.fromCSV(csvText, { sheetName: "Coverage Data" });
const data = workbook.worksheets.getItem("Coverage Data");
const summary = workbook.worksheets.add("Monday Summary");

data.showGridLines = false;
data.freezePanes.freezeRows(1);
data.getRange("A1:V9").format = {
  font: { name: "Aptos", size: 10, color: "#162236" },
  verticalAlignment: "center",
};
data.getRange("A1:V1").format = {
  fill: "#162236",
  font: { name: "Aptos Display", size: 10, bold: true, color: "#FFFFFF" },
  wrapText: true,
  verticalAlignment: "center",
};
data.getRange("A1:V9").format.borders = {
  preset: "all",
  style: "thin",
  color: "#D9E2EC",
};
data.getRange("A2:V9").format.rowHeightPx = 29;
data.getRange("A1:V1").format.rowHeightPx = 42;
data.getRange("H2:K9").format.numberFormat = "0.0";
data.getRange("L2:O9").format.numberFormat = "0.000E+00";
data.getRange("P2:P9").format.numberFormat = "0";
data.getRange("R2:R9").format.numberFormat = "0";
data.getRange("A:B").format.columnWidthPx = 78;
data.getRange("C:D").format.columnWidthPx = 120;
data.getRange("E:E").format.columnWidthPx = 220;
data.getRange("F:F").format.columnWidthPx = 88;
data.getRange("G:G").format.columnWidthPx = 225;
data.getRange("H:K").format.columnWidthPx = 115;
data.getRange("L:P").format.columnWidthPx = 110;
data.getRange("Q:T").format.columnWidthPx = 145;
data.getRange("U:V").format.columnWidthPx = 250;
const dataTable = data.tables.add("A1:V9", true, "CoverageDataTable");
dataTable.style = "TableStyleMedium2";

summary.showGridLines = false;
summary.getRange("A1:O26").format = {
  fill: "#F7F9FC",
  font: { name: "Aptos", size: 11, color: "#162236" },
};
summary.getRange("A1:O2").merge();
summary.getRange("A1").values = [["Eight process gases share a complete 471-MOF comparison set"]];
summary.getRange("A1:O2").format = {
  fill: "#162236",
  font: { name: "Aptos Display", size: 22, bold: true, color: "#FFFFFF" },
  horizontalAlignment: "left",
  verticalAlignment: "center",
};
summary.getRange("A3:O3").merge();
summary.getRange("A3").values = [["MONDAY UPDATE · ETHYLENE-CRACKER OUTLET · COMPUTED PAIRS ONLY"]];
summary.getRange("A3:O3").format = {
  fill: "#3D8DFF",
  font: { name: "Aptos", size: 11, bold: true, color: "#FFFFFF" },
  verticalAlignment: "center",
};

const kpiLabels = [["TARGET GASES"], ["COMPUTED PAIRS"], ["COMMON MOFS"], ["FULL DATASET"]];
const kpiRanges = ["A5:C5", "D5:F5", "G5:I5", "J5:O5"];
const valueRanges = ["A6:C7", "D6:F7", "G6:I7", "J6:O7"];
const kpiValues = [
  { formula: "=ROWS('Coverage Data'!A2:A9)", display: "0" },
  { formula: "=ROWS('Coverage Data'!A2:A9)*MIN('Coverage Data'!J2:J9)", display: "#,##0" },
  { formula: "=MIN('Coverage Data'!J2:J9)", display: "#,##0" },
  { value: "16,628 pairs · 1,940 MOFs · 113 molecules", display: "@" },
];
for (let i = 0; i < kpiRanges.length; i += 1) {
  summary.getRange(kpiRanges[i]).merge();
  summary.getRange(kpiRanges[i]).values = [kpiLabels[i]];
  summary.getRange(kpiRanges[i]).format = {
    fill: i < 3 ? "#E8F1FF" : "#EAF7F8",
    font: { name: "Aptos", size: 9, bold: true, color: "#526071" },
    horizontalAlignment: "center",
    verticalAlignment: "center",
  };
  summary.getRange(valueRanges[i]).merge();
  if (kpiValues[i].formula) {
    summary.getRange(valueRanges[i].split(":")[0]).formulas = [[kpiValues[i].formula]];
  } else {
    summary.getRange(valueRanges[i].split(":")[0]).values = [[kpiValues[i].value]];
  }
  summary.getRange(valueRanges[i]).format = {
    fill: "#FFFFFF",
    font: {
      name: "Aptos Display",
      size: i < 3 ? 22 : 15,
      bold: true,
      color: i < 3 ? "#162236" : "#0A7780",
    },
    horizontalAlignment: "center",
    verticalAlignment: "center",
    borders: { preset: "outside", style: "thin", color: "#D9E2EC" },
  };
  summary.getRange(valueRanges[i]).format.numberFormat = kpiValues[i].display;
}

summary.getRange("A9:F9").values = [[
  "Gas",
  "Process role",
  "Group",
  "Computed MOFs",
  "Median K",
  "IQR",
]];
const formulas = [];
for (let row = 2; row <= 9; row += 1) {
  formulas.push([
    `='Coverage Data'!D${row}`,
    `='Coverage Data'!E${row}`,
    `='Coverage Data'!F${row}`,
    `='Coverage Data'!I${row}`,
    `='Coverage Data'!M${row}`,
    `='Coverage Data'!O${row}`,
  ]);
}
summary.getRange("A10:F17").formulas = formulas;
summary.getRange("A9:F17").format = {
  fill: "#FFFFFF",
  font: { name: "Aptos", size: 10, color: "#162236" },
  verticalAlignment: "center",
  borders: { preset: "all", style: "thin", color: "#D9E2EC" },
};
summary.getRange("A9:F9").format = {
  fill: "#162236",
  font: { name: "Aptos", size: 10, bold: true, color: "#FFFFFF" },
  wrapText: true,
  horizontalAlignment: "center",
  verticalAlignment: "center",
};
summary.getRange("A10:A17").format.font = { name: "Aptos", size: 10, bold: true, color: "#162236" };
summary.getRange("D10:D17").format.numberFormat = "0";
summary.getRange("E10:F17").format.numberFormat = "0.00E+00";
summary.getRange("A9:F9").format.rowHeightPx = 34;
summary.getRange("A10:F17").format.rowHeightPx = 31;
const panelTable = summary.tables.add("A9:F17", true, "MondayPanelTable");
panelTable.style = "TableStyleMedium2";

summary.getRange("P9:Q9").values = [["Gas", "Computed MOFs"]];
const chartFormulas = [];
for (let row = 2; row <= 9; row += 1) {
  chartFormulas.push([`='Coverage Data'!D${row}`, `='Coverage Data'!I${row}`]);
}
summary.getRange("P10:Q17").formulas = chartFormulas;
summary.getRange("P9:Q17").format = {
  fill: "#FFFFFF",
  font: { name: "Aptos", size: 9, color: "#526071" },
  borders: { preset: "all", style: "thin", color: "#E6EBF2" },
};
summary.getRange("P9:Q9").format.font = { name: "Aptos", size: 9, bold: true, color: "#162236" };
const chart = summary.charts.add("bar", summary.getRange("P9:Q17"));
chart.title = "Directly computed coverage (MOFs)";
chart.titleTextStyle.fontSize = 14;
chart.hasLegend = false;
chart.xAxis = {
  min: 0,
  max: 500,
  majorUnit: 100,
  numberFormatCode: "0",
  majorGridlines: { style: "solid", color: "#D9E2EC", width: 1 },
  textStyle: { fontSize: 9, color: "#526071" },
};
chart.yAxis = { axisType: "textAxis", textStyle: { fontSize: 9, color: "#162236" } };
chart.setPosition("H9", "O18");

summary.getRange("A19:O19").merge();
summary.getRange("A19").values = [["NEXT: SELECT 12 MOFS → TEST IDENTIFICATION, DRIFT & RATIOS → PRUNE"]];
summary.getRange("A19:O19").format = {
  fill: "#FFCB47",
  font: { name: "Aptos", size: 12, bold: true, color: "#162236" },
  horizontalAlignment: "center",
  verticalAlignment: "center",
};
summary.getRange("A21:O22").merge();
summary.getRange("A21").values = [[
  "Interpretation: conditioned extractive post-quench outlet sample near 300 K—not direct exposure to the raw furnace effluent. C4/C5 species are coverage-matched process-gas proxies.",
]];
summary.getRange("A21:O22").format = {
  fill: "#FFFFFF",
  font: { name: "Aptos", size: 10, italic: true, color: "#526071" },
  wrapText: true,
  verticalAlignment: "center",
  borders: { preset: "outside", style: "thin", color: "#D9E2EC" },
};
summary.getRange("A24:O26").merge();
summary.getRange("A24").values = [[
  "Sources: D-MOPH-25 Zenodo record 16754752; Choi, Sholl & Medford (2025), DOI 10.1088/2632-2153/ae0241. Values link to Coverage Data, which is generated from pandas operations on final.csv.",
]];
summary.getRange("A24:O26").format = {
  fill: "#F1F4F8",
  font: { name: "Aptos", size: 9, color: "#526071" },
  wrapText: true,
  verticalAlignment: "center",
};

summary.getRange("A:A").format.columnWidthPx = 110;
summary.getRange("B:B").format.columnWidthPx = 225;
summary.getRange("C:C").format.columnWidthPx = 82;
summary.getRange("D:D").format.columnWidthPx = 105;
summary.getRange("E:F").format.columnWidthPx = 100;
summary.getRange("G:G").format.columnWidthPx = 22;
summary.getRange("H:I").format.columnWidthPx = 90;
summary.getRange("J:J").format.columnWidthPx = 20;
summary.getRange("K:O").format.columnWidthPx = 93;
summary.getRange("1:2").format.rowHeightPx = 30;
summary.getRange("3:3").format.rowHeightPx = 24;
summary.getRange("5:5").format.rowHeightPx = 20;
summary.getRange("6:7").format.rowHeightPx = 28;
summary.getRange("19:19").format.rowHeightPx = 34;
summary.getRange("21:22").format.rowHeightPx = 26;
summary.getRange("24:26").format.rowHeightPx = 23;

const inspection = await workbook.inspect({
  kind: "workbook,sheet,table,drawing",
  maxChars: 8000,
  tableMaxRows: 5,
  tableMaxCols: 8,
});
console.log(inspection.ndjson);

const preview = await workbook.render({
  sheetName: "Monday Summary",
  range: "A1:O26",
  scale: 1,
  format: "png",
});
await fs.writeFile(`${outputDir}/ethylene_cracker_panel_preview.png`, new Uint8Array(await preview.arrayBuffer()));

const xlsx = await SpreadsheetFile.exportXlsx(workbook);
await xlsx.save(`${outputDir}/ethylene_cracker_panel.xlsx`);
console.log(`saved=${outputDir}/ethylene_cracker_panel.xlsx`);
