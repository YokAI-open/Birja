import "@testing-library/jest-dom/vitest";
import { cleanup } from "@testing-library/react";
import { afterEach } from "vitest";
import { webcrypto } from "node:crypto";

// jsdom supplies randomUUID but not SubtleCrypto. Exercise actual browser
// recovery hashing with Node's implementation, including after per-test stubs.
Object.defineProperty(globalThis, "crypto", { configurable: true, value: webcrypto });

afterEach(cleanup);
