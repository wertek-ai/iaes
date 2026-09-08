/**
 * The alias has to survive compilation, not just execution.
 *
 * An earlier version installed the class aliases by assignment after the class
 * body:
 *
 *     (AssetMeasurement as unknown as Record<string, unknown>).fromJSON =
 *       AssetMeasurement.fromObject.bind(AssetMeasurement);
 *
 * That preserves the runtime and not the published type surface. `@iaes/sdk`
 * ships declarations, and a property added outside the class body never reaches
 * dist/models.d.ts — so an existing consumer writing
 * `AssetMeasurement.fromJSON(event)` would keep running and stop compiling on
 * upgrade. An alias that breaks the build is not an alias.
 *
 * So this checks the BUILT ARTIFACT, which is what a consumer actually installs.
 * Checking the source would have passed against the defect: the assignment was
 * right there in models.ts.
 */

const test = require("node:test");
const assert = require("node:assert");
const fs = require("node:fs");
const path = require("node:path");

const DECLARATION = path.join(__dirname, "..", "dist", "models.d.ts");

const CLASSES = [
  "AssetMeasurement",
  "AssetHealth",
  "WorkOrderIntent",
  "MaintenanceCompletion",
  "AssetHierarchy",
  "SensorRegistration",
  "SparePartUsage",
];

function declaration() {
  assert.ok(
    fs.existsSync(DECLARATION),
    "dist/models.d.ts is missing — run `npm run build` first; CI builds before testing",
  );
  return fs.readFileSync(DECLARATION, "utf-8");
}

test("every class declares the canonical name in the published types", () => {
  const dts = declaration();
  for (const cls of CLASSES) {
    const body = dts.slice(dts.indexOf(`declare class ${cls}`));
    assert.match(
      body.slice(0, body.indexOf("declare class", 1) + 1 || undefined),
      /static fromObject\(/,
      `${cls} does not declare fromObject in dist/models.d.ts`,
    );
  }
});

test("every class declares the deprecated alias in the published types", () => {
  const dts = declaration();
  const found = (dts.match(/static fromJSON\(/g) ?? []).length;
  assert.equal(
    found,
    CLASSES.length,
    `dist/models.d.ts declares ${found} of ${CLASSES.length} fromJSON aliases. ` +
      "A consumer on the old name would stop compiling.",
  );
});

test("the alias is marked deprecated where a consumer's editor will see it", () => {
  const dts = declaration();
  assert.match(
    dts,
    /@deprecated[\s\S]{0,120}static fromJSON\(/,
    "the alias is declared and not marked @deprecated, so nobody moves",
  );
});

test("the dispatch alias is declared too", () => {
  const dts = declaration();
  assert.match(dts, /declare function fromJSON\(/, "the module-level alias vanished");
  assert.match(dts, /declare function fromObject\(/, "the canonical dispatch is missing");
});

test("and both still work at runtime", () => {
  const sdk = require("../dist/index.js");
  const event = {
    spec_version: "1.4",
    event_type: "asset.health",
    event_id: "550e8400-e29b-41d4-a716-446655440000",
    correlation_id: "550e8400-e29b-41d4-a716-446655440000",
    timestamp: "2026-09-08T12:00:00Z",
    source: "acme.diagnostics",
    asset: { asset_id: "MOTOR-001" },
    data: { health_index: 0.82, severity: "medium" },
  };
  for (const cls of CLASSES) {
    assert.equal(typeof sdk[cls].fromObject, "function", `${cls}.fromObject`);
    assert.equal(typeof sdk[cls].fromJSON, "function", `${cls}.fromJSON`);
  }
  assert.equal(
    sdk.AssetHealth.fromJSON(event).constructor.name,
    sdk.AssetHealth.fromObject(event).constructor.name,
  );
});
