#!/usr/bin/env node
// Owner-approved, temporary exception: https://github.com/YokAI-open/Birja/issues/35
// This reports accepted risk; it does not remediate or hide the advisory.
import { createHash } from "node:crypto";
import { readFileSync } from "node:fs";
import { dirname, join, resolve } from "node:path";
import { spawnSync } from "node:child_process";
import { fileURLToPath, pathToFileURL } from "node:url";

export const POLICY = Object.freeze({
  issue: "https://github.com/YokAI-open/Birja/issues/35",
  advisory: "https://github.com/advisories/GHSA-fc5q-39xc-vjpf",
  expires: "2026-12-17T00:00:00.000Z",
  manifestSha256:
    "c374ffc85980c39fdb3ba0f732648c612a9f4155433d0f40afd3d18b6f356c92",
  lockSha256:
    "e93da90cd5f93730ddd436e84d3bb1b9e25336b82b33f04161b8a2b792d9f497",
});
const LEVELS = ["info", "low", "moderate", "high", "critical"];
const ROOT = resolve(dirname(fileURLToPath(import.meta.url)), "..");
const hash = (value) => createHash("sha256").update(value).digest("hex");
const object = (value) =>
  value !== null && typeof value === "object" && !Array.isArray(value);
const demand = (condition, message) => {
  if (!condition) throw new Error(message);
};

export function evaluateAudit(
  report,
  { status, manifest, lock, now = new Date() },
) {
  demand(
    Number.isInteger(status) && (status === 0 || status === 1),
    "npm audit did not produce a successful audit response",
  );
  demand(
    Number.isFinite(now.valueOf()) && now < new Date(POLICY.expires),
    "Accepted-risk review expired or clock invalid",
  );
  demand(
    hash(manifest) === POLICY.manifestSha256 &&
      hash(lock) === POLICY.lockSha256,
    "Dependency files changed; accepted risk requires fresh review",
  );
  const locked = JSON.parse(lock);
  demand(object(locked.packages), "Invalid locked package inventory");
  demand(
    object(report) &&
      !Object.hasOwn(report, "error") &&
      report.auditReportVersion === 2,
    "Invalid npm audit report",
  );
  demand(
    object(report.vulnerabilities) &&
      object(report.metadata) &&
      object(report.metadata.vulnerabilities),
    "Missing npm audit vulnerability metadata",
  );
  const entries = Object.entries(report.vulnerabilities);
  const counts = Object.fromEntries(LEVELS.map((level) => [level, 0]));
  const references = new Map();
  const roots = new Set();
  for (const [name, entry] of entries) {
    demand(
      object(entry) && entry.name === name && LEVELS.includes(entry.severity),
      "Invalid vulnerability entry",
    );
    demand(
      typeof entry.isDirect === "boolean" && typeof entry.range === "string",
      "Incomplete vulnerability entry",
    );
    demand(
      Array.isArray(entry.via) &&
        entry.via.length > 0 &&
        Array.isArray(entry.nodes) &&
        entry.nodes.length > 0,
      "Missing advisory causes or package nodes",
    );
    demand(
      Array.isArray(entry.effects) &&
        entry.effects.every((effect) => typeof effect === "string"),
      "Invalid vulnerability effects",
    );
    counts[entry.severity] += 1;
    demand(
      entry.severity !== "critical",
      `Critical finding is not excepted: ${name}`,
    );
    for (const node of entry.nodes) {
      demand(
        typeof node === "string" &&
          Object.hasOwn(locked.packages, node) &&
          node.endsWith(`node_modules/${name}`),
        "Audit node does not match the reviewed lock",
      );
    }
    const edges = [];
    for (const cause of entry.via) {
      if (typeof cause === "string") {
        demand(
          Object.hasOwn(report.vulnerabilities, cause),
          "Broken vulnerability cause reference",
        );
        edges.push(cause);
      } else {
        demand(
          object(cause) &&
            LEVELS.includes(cause.severity) &&
            typeof cause.url === "string" &&
            typeof cause.name === "string" &&
            typeof cause.dependency === "string" &&
            typeof cause.range === "string" &&
            Number.isInteger(cause.source),
          "Malformed advisory cause",
        );
        demand(
          LEVELS.indexOf(entry.severity) >= LEVELS.indexOf(cause.severity),
          "Advisory severity is hidden by its entry",
        );
        demand(
          cause.severity !== "critical",
          "Critical advisory cause is not excepted",
        );
        if (cause.severity === "high") {
          demand(
            name === "picomatch" &&
              cause.name === "picomatch" &&
              cause.dependency === "picomatch" &&
              cause.url === POLICY.advisory &&
              cause.range.replaceAll(" ", "") === "<=4.0.7",
            `Unaccepted HIGH advisory: ${cause.url}`,
          );
          demand(
            entry.nodes.every((node) =>
              [
                "node_modules/picomatch",
                "node_modules/micromatch/node_modules/picomatch",
              ].includes(node),
            ),
            "Unreviewed picomatch path",
          );
          roots.add(name);
        }
      }
    }
    references.set(name, edges);
  }
  for (const level of LEVELS) {
    demand(
      Number.isInteger(report.metadata.vulnerabilities[level]) &&
        report.metadata.vulnerabilities[level] === counts[level],
      "Audit severity counts are inconsistent",
    );
  }
  demand(
    report.metadata.vulnerabilities.total === entries.length,
    "Audit total count is inconsistent",
  );
  demand(
    status === (counts.high ? 1 : 0),
    "npm exit status contradicts HIGH findings",
  );
  // Reachability to an actual allowed leaf handles legitimate parent cycles,
  // while a disconnected cycle can never manufacture accepted risk.
  const reachesRoot = (start) => {
    const seen = new Set();
    const pending = [start];
    while (pending.length) {
      const name = pending.pop();
      if (roots.has(name)) return true;
      if (!seen.has(name)) {
        seen.add(name);
        pending.push(...references.get(name));
      }
    }
    return false;
  };
  for (const [name, entry] of entries) {
    if (entry.severity === "high")
      demand(
        reachesRoot(name),
        `HIGH finding has no accepted advisory root: ${name}`,
      );
  }
  return {
    status: counts.high ? "accepted-risk" : "no-blocking-findings",
    counts,
    issue: POLICY.issue,
    expires: POLICY.expires,
  };
}

export function runAudit({
  run = spawnSync,
  read = readFileSync,
  now = new Date(),
  stdout = process.stdout,
  stderr = process.stderr,
} = {}) {
  const directory = join(ROOT, "frontend");
  let result;
  try {
    result = run("npm", ["audit", "--json", "--audit-level=high"], {
      cwd: directory,
      encoding: "utf8",
      timeout: 120_000,
      maxBuffer: 8 * 1024 * 1024,
      env: {
        ...process.env,
        NPM_CONFIG_OMIT: "",
        NPM_CONFIG_INCLUDE: "dev",
        NPM_CONFIG_IGNORE_SCRIPTS: "true",
      },
    });
    // Preserve the full original report even when evaluation refuses it.
    if (result.stdout) stdout.write(result.stdout + "\n");
    if (result.stderr) stderr.write(result.stderr);
    demand(
      !result.error && result.signal == null,
      "npm audit failed or timed out",
    );
    const verdict = evaluateAudit(JSON.parse(result.stdout), {
      status: result.status,
      manifest: read(join(directory, "package.json")),
      lock: read(join(directory, "package-lock.json")),
      now,
    });
    stdout.write(JSON.stringify(verdict) + "\n");
    return 0;
  } catch (error) {
    stderr.write(`Frontend audit BLOCKED: ${error.message}\n`);
    return 1;
  }
}

export function main(args = process.argv.slice(2), dependencies = {}) {
  if (args.length !== 0) {
    (dependencies.stderr ?? process.stderr).write(
      "No command-line policy overrides are supported\n",
    );
    return 1;
  }
  return runAudit(dependencies);
}

if (
  process.argv[1] &&
  import.meta.url === pathToFileURL(resolve(process.argv[1])).href
) {
  process.exitCode = main();
}
