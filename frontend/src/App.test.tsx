import { screen } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";
import { renderWithClient } from "@/test/render";
import App from "./App";

afterEach(() => {
  vi.unstubAllGlobals();
});

describe("App", () => {
  it("shows the wordmark and the system status heading", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn(() =>
        Promise.resolve(
          new Response(JSON.stringify({ status: "ok", db: "ok", redis: "ok" }), { status: 200 }),
        ),
      ),
    );
    renderWithClient(<App />);
    expect(screen.getByText("YokaiExchange")).toBeVisible();
    expect(screen.getByRole("heading", { name: "System status" })).toBeVisible();
    expect(await screen.findByText("All systems operational")).toBeVisible();
  });
});
