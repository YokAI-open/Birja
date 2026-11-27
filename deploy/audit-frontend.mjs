#!/usr/bin/env node
import { readFileSync } from "node:fs";
import { dirname, join, resolve } from "node:path";
import { spawnSync } from "node:child_process";
import { fileURLToPath, pathToFileURL } from "node:url";

const LEVELS = ["info", "low", "moderate", "high", "critical"];
const ROOT = resolve(dirname(fileURLToPath(import.meta.url)), "..");
const object = (value) =>
  value !== null && typeof value === "object" && !Array.isArray(value);
const demand = (condition, message) => {
  if (!condition) throw new Error(message);
};

export function evaluateAudit(report, { status, lock }) {
  demand(
    Number.isInteger(status) && (status === 0 || status === 1),
    "npm audit did not produce a successful audit response",
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
    for (const node of entry.nodes) {
      demand(
        typeof node === "string" &&
          Object.hasOwn(locked.packages, node) &&
          node.endsWith(`node_modules/${name}`),
        "Audit node does not match the lock",
      );
    }
    for (const cause of entry.via) {
      if (typeof cause === "string") {
        demand(
          Object.hasOwn(report.vulnerabilities, cause),
          "Broken vulnerability cause reference",
        );
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
      }
    }
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
  const blocking = counts.high + counts.critical;
  demand(
    status === (blocking ? 1 : 0),
    "npm exit status contradicts HIGH/CRITICAL findings",
  );
  demand(blocking === 0, "npm audit found HIGH or CRITICAL vulnerabilities");
  return { status: "no-blocking-findings", counts };
}

export function runAudit({
  run = spawnSync,
  read = readFileSync,
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
      lock: read(join(directory, "package-lock.json")),
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
