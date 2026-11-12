import { execFileSync } from "node:child_process";
import { fileURLToPath } from "node:url";
const root = fileURLToPath(new URL("../../", import.meta.url));
/** Fixed argv, guarded disposable DB only; no provider or production input. */
export function stockFixture(
  operation:
    "fresh" | "open" | "close" | "status" | "halt" | "hold" | "reprice" | "stale" | "long-name",
  symbol = "AAPL",
  argument = "",
) {
  if (process.env.COMPOSE_PROJECT_NAME !== "birja-phase09-e2e-test")
    throw new Error("Requires owned Phase9 browser stack");
  execFileSync(
    "docker",
    [
      "compose",
      "exec",
      "-T",
      "backend",
      "python",
      "/e2e/stock-trade-fixture.py",
      operation,
      symbol,
      argument,
    ],
    { cwd: root, stdio: "pipe", timeout: 20000 },
  );
}
