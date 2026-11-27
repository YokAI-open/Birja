import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { fileURLToPath } from "node:url";
import test from "node:test";
import { evaluateAudit, main, runAudit } from "../audit-frontend.mjs";

const lock = readFileSync(
  fileURLToPath(new URL("../../frontend/package-lock.json", import.meta.url)),
);
const context = { status: 1, lock };
const advisory = () => ({
  source: 1247710,
  name: "picomatch",
  dependency: "picomatch",
  severity: "high",
  url: "https://github.com/advisories/GHSA-fc5q-39xc-vjpf",
  range: "<=4.0.7",
});
const node = (
  name,
  via,
  severity = "high",
  nodes = [`node_modules/${name}`],
) => ({ name, via, severity, nodes, isDirect: false, effects: [], range: "*" });
function report(
  entries = {
    picomatch: node("picomatch", [advisory()], "high", [
      "node_modules/picomatch",
      "node_modules/micromatch/node_modules/picomatch",
    ]),
    vite: node("vite", ["picomatch"]),
    vitest: node("vitest", ["vite", "@vitest/coverage-v8"]),
    "@vitest/coverage-v8": node("@vitest/coverage-v8", ["vitest"]),
  },
) {
  const counts = {
    info: 0,
    low: 0,
    moderate: 0,
    high: 0,
    critical: 0,
    total: 0,
  };
  for (const entry of Object.values(entries)) {
    counts[entry.severity] += 1;
    counts.total += 1;
  }
  return {
    auditReportVersion: 2,
    vulnerabilities: entries,
    metadata: { vulnerabilities: counts },
  };
}
const evaluate = (value, overrides = {}) =>
  evaluateAudit(value, { ...context, ...overrides });

test("the previously excepted advisory and its inherited findings block", () => {
  assert.throws(() => evaluate(report()), /HIGH or CRITICAL/);
});
test("moderate and clean reports retain original audit-level behavior", () => {
  const moderate = node(
    "minimatch",
    [
      {
        source: 1,
        name: "minimatch",
        dependency: "minimatch",
        severity: "moderate",
        url: "https://github.com/advisories/GHSA-other",
        range: "*",
      },
    ],
    "moderate",
  );
  assert.equal(
    evaluate(report({ minimatch: moderate }), { status: 0 }).counts.moderate,
    1,
  );
  assert.equal(
    evaluate(report({}), { status: 0 }).status,
    "no-blocking-findings",
  );
});
test("another HIGH on the same package and mixed inherited roots are blocked", () => {
  const value = report();
  value.vulnerabilities.picomatch.via.push({
    ...advisory(),
    url: "https://github.com/advisories/GHSA-unaccepted",
  });
  assert.throws(() => evaluate(value), /HIGH or CRITICAL/);
  const roots = report({
    picomatch: node("picomatch", [advisory()]),
    vite: node("vite", [
      "picomatch",
      {
        ...advisory(),
        name: "vite",
        dependency: "vite",
        url: "https://github.com/advisories/GHSA-new",
      },
    ]),
  });
  assert.throws(() => evaluate(roots), /HIGH or CRITICAL/);
});
test("critical entries and advisory causes block", () => {
  assert.throws(
    () =>
      evaluate(
        report({ picomatch: node("picomatch", [advisory()], "critical") }),
      ),
    /CRITICAL/,
  );
  assert.throws(
    () =>
      evaluate(
        report({
          picomatch: node("picomatch", [
            { ...advisory(), severity: "critical" },
          ]),
        }),
      ),
    /severity|CRITICAL/,
  );
});
test("the former advisory URL grants no allowance and lock paths must match", () => {
  assert.throws(
    () => evaluate(report({ vite: node("vite", [advisory()]) })),
    /HIGH or CRITICAL/,
  );
  assert.throws(
    () =>
      evaluate(
        report({
          picomatch: node("picomatch", [{ ...advisory(), range: "*" }]),
        }),
      ),
    /HIGH or CRITICAL/,
  );
  assert.throws(
    () =>
      evaluate(
        report({
          picomatch: node("picomatch", [advisory()], "high", [
            "node_modules/other/node_modules/picomatch",
          ]),
        }),
      ),
    /lock/,
  );
});
test("inherited high findings and broken cause references are refused", () => {
  assert.throws(
    () =>
      evaluate(
        report({
          vite: node("vite", ["vitest"]),
          vitest: node("vitest", ["vite"]),
        }),
      ),
    /HIGH or CRITICAL/,
  );
  assert.throws(
    () => evaluate(report({ vite: node("vite", ["missing"]) })),
    /Broken/,
  );
});
test("malformed report, causes, severity counts and hidden severity fail closed", () => {
  for (const bad of [
    null,
    [],
    {},
    { ...report(), error: {} },
    { ...report(), auditReportVersion: 1 },
    { ...report(), metadata: {} },
  ])
    assert.throws(() => evaluate(bad));
  const malformed = report();
  malformed.vulnerabilities.picomatch.via = [{}];
  assert.throws(() => evaluate(malformed), /Malformed/);
  const counts = report();
  counts.metadata.vulnerabilities.high = 0;
  assert.throws(() => evaluate(counts), /counts/);
  const total = report();
  total.metadata.vulnerabilities.total = 0;
  assert.throws(() => evaluate(total), /total/);
  const hidden = report({
    picomatch: node("picomatch", [advisory()], "moderate"),
  });
  assert.throws(() => evaluate(hidden), /hidden/);
});
test("the current lock inventory is validated without a pinned hash", () => {
  assert.equal(
    evaluate(report({}), { status: 0, lock: Buffer.from('{"packages":{}}') }).status,
    "no-blocking-findings",
  );
  assert.throws(() => evaluate(report({}), { status: 0, lock: Buffer.from("{}") }), /inventory/);
});
test("npm status must agree with complete HIGH and CRITICAL findings", () => {
  for (const status of [null, 2, 127, 0])
    assert.throws(() => evaluate(report(), { status }));
  assert.throws(() => evaluate(report({}), { status: 1 }), /contradicts/);
});

function run(result, overrides = {}) {
  let out = "";
  let err = "";
  let invocation;
  const status = runAudit({
    run: (...args) => {
      invocation = args;
      return result;
    },
    read: () => lock,
    stdout: {
      write: (chunk) => {
        out += chunk;
      },
    },
    stderr: {
      write: (chunk) => {
        err += chunk;
      },
    },
    ...overrides,
  });
  return { status, out, err, invocation };
}
test("CLI runner preserves raw reports and executes full bounded audit", () => {
  const raw = JSON.stringify(report({}));
  const result = run({
    status: 0,
    stdout: raw,
    stderr: "notice",
    signal: null,
  });
  assert.equal(result.status, 0);
  assert.ok(result.out.startsWith(raw));
  assert.match(result.out, /no-blocking-findings/);
  assert.equal(result.err, "notice");
  assert.equal(result.invocation[0], "npm");
  assert.deepEqual(result.invocation[1], [
    "audit",
    "--json",
    "--audit-level=high",
  ]);
  assert.equal(result.invocation[2].timeout, 120000);
  assert.equal(result.invocation[2].maxBuffer, 8 * 1024 * 1024);
  assert.equal(result.invocation[2].env.NPM_CONFIG_OMIT, "");
  assert.equal(result.invocation[2].env.NPM_CONFIG_INCLUDE, "dev");
});
test("a blocking audit still retains the original advisory report", () => {
  const raw = JSON.stringify(report());
  const result = run({ status: 1, stdout: raw });
  assert.equal(result.status, 1);
  assert.ok(result.out.startsWith(raw));
  assert.match(result.err, /HIGH or CRITICAL/);
});
test("network errors, timeout, bad JSON and exit status remain fatal with output retained", () => {
  const inputs = [
    { status: 1, stdout: JSON.stringify({ error: { code: "ENOTFOUND" } }) },
    {
      status: null,
      stdout: "partial",
      error: new Error("timeout"),
      signal: "SIGTERM",
    },
    { status: 1, stdout: "invalid JSON" },
    { status: 2, stdout: JSON.stringify(report()) },
    { status: 1, stdout: JSON.stringify(report()), signal: "SIGTERM" },
  ];
  for (const input of inputs) {
    const result = run(input);
    assert.equal(result.status, 1);
    assert.ok(result.out.startsWith(input.stdout));
    assert.match(result.err, /BLOCKED/);
  }
});

test("CLI rejects policy overrides before invoking npm", () => {
  let stderr = "";
  assert.equal(
    main(["--ignore-all"], {
      run: () => {
        throw new Error("must not invoke npm");
      },
      stderr: {
        write: (chunk) => {
          stderr += chunk;
        },
      },
    }),
    1,
  );
  assert.match(stderr, /No command-line policy overrides/);
});
