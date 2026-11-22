import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { fileURLToPath } from "node:url";
import test from "node:test";
import { evaluateAudit, main, POLICY, runAudit } from "../audit-frontend.mjs";

const manifest = readFileSync(
  fileURLToPath(new URL("../../frontend/package.json", import.meta.url)),
);
const lock = readFileSync(
  fileURLToPath(new URL("../../frontend/package-lock.json", import.meta.url)),
);
const now = new Date("2026-11-17T20:00:00Z");
const context = { status: 1, manifest, lock, now };
const advisory = () => ({
  source: 1247710,
  name: "picomatch",
  dependency: "picomatch",
  severity: "high",
  url: POLICY.advisory,
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

test("accepted leaf and inherited parent cycle stay visible as accepted risk", () => {
  const value = evaluate(report());
  assert.equal(value.status, "accepted-risk");
  assert.equal(value.counts.high, 4);
  assert.equal(value.issue, "https://github.com/YokAI-open/Birja/issues/35");
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
  assert.throws(() => evaluate(value), /Unaccepted HIGH/);
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
  assert.throws(() => evaluate(roots), /Unaccepted HIGH/);
});
test("critical entry or direct cause can never use the exception", () => {
  assert.throws(
    () =>
      evaluate(
        report({ picomatch: node("picomatch", [advisory()], "critical") }),
      ),
    /Critical/,
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
    /severity|Critical/,
  );
});
test("matching URL on another package, changed range, or unreviewed node is refused", () => {
  assert.throws(
    () => evaluate(report({ vite: node("vite", [advisory()]) })),
    /Unaccepted HIGH/,
  );
  assert.throws(
    () =>
      evaluate(
        report({
          picomatch: node("picomatch", [{ ...advisory(), range: "*" }]),
        }),
      ),
    /Unaccepted HIGH/,
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
test("cycle without any accepted leaf and broken cause references are refused", () => {
  assert.throws(
    () =>
      evaluate(
        report({
          vite: node("vite", ["vitest"]),
          vitest: node("vitest", ["vite"]),
        }),
      ),
    /no accepted advisory root/,
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
test("changed manifest/lock, expired review and invalid time are refused", () => {
  assert.throws(
    () => evaluate(report(), { manifest: Buffer.from("changed") }),
    /Dependency files changed/,
  );
  assert.throws(
    () => evaluate(report(), { lock: Buffer.from("changed") }),
    /Dependency files changed/,
  );
  assert.throws(
    () => evaluate(report(), { now: new Date(POLICY.expires) }),
    /expired/,
  );
  assert.throws(
    () => evaluate(report(), { now: new Date("invalid") }),
    /expired/,
  );
});
test("npm status must agree with complete HIGH findings", () => {
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
    read: (path) => (path.endsWith("package-lock.json") ? lock : manifest),
    now,
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
  const raw = JSON.stringify(report());
  const result = run({
    status: 1,
    stdout: raw,
    stderr: "notice",
    signal: null,
  });
  assert.equal(result.status, 0);
  assert.ok(result.out.startsWith(raw));
  assert.match(result.out, /accepted-risk/);
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
