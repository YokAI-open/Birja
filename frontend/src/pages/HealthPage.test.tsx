import { screen, waitFor, within } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";
import { renderWithClient } from "@/test/render";
import HealthPage from "./HealthPage";

function respond(body: unknown, status = 200) {
  return vi.fn(() =>
    Promise.resolve(
      new Response(JSON.stringify(body), {
        status,
        headers: { "Content-Type": "application/json" },
      }),
    ),
  );
}

function rows() {
  const list = screen.getByRole("list", { name: "Service status" });
  return within(list)
    .getAllByRole("listitem")
    .map((li) => li.textContent);
}

afterEach(() => {
  vi.unstubAllGlobals();
});

describe("HealthPage", () => {
  it("shows all services connected when ok", async () => {
    vi.stubGlobal("fetch", respond({ status: "ok", db: "ok", redis: "ok" }));
    renderWithClient(<HealthPage />);
    expect(await screen.findByText("All systems operational")).toBeVisible();
    expect(screen.getByRole("heading", { level: 1, name: "System status" })).toBeVisible();
    expect(rows()).toEqual(["APIConnected", "DatabaseConnected", "RedisConnected"]);
    expect(screen.getByText(/^Last checked/)).toBeVisible();
  });

  it("shows which dependency is down when degraded", async () => {
    vi.stubGlobal("fetch", respond({ status: "degraded", db: "ok", redis: "error" }, 503));
    renderWithClient(<HealthPage />);
    expect(await screen.findByText("Some services are unavailable")).toBeVisible();
    expect(rows()).toEqual(["APIConnected", "DatabaseConnected", "RedisUnavailable"]);
  });

  it("shows a clear message when the backend is unreachable", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn(() => Promise.reject(new TypeError("Failed to fetch"))),
    );
    renderWithClient(<HealthPage />);
    expect(await screen.findByRole("alert")).toHaveTextContent("Can't reach the backend");
    expect(rows()).toEqual(["APIUnavailable", "DatabaseUnknown", "RedisUnknown"]);
    expect(screen.queryByText(/Failed to fetch/)).not.toBeInTheDocument();
  });

  it("shows skeleton rows while loading", () => {
    vi.stubGlobal(
      "fetch",
      vi.fn(() => new Promise<Response>(() => {})),
    );
    renderWithClient(<HealthPage />);
    const list = screen.getByRole("list", { name: "Service status" });
    expect(list).toHaveAttribute("aria-busy", "true");
    expect(within(list).getAllByRole("listitem")).toHaveLength(3);
    expect(screen.queryByText("Connected")).not.toBeInTheDocument();
  });

  it("refetches when Check again is pressed", async () => {
    const fetchMock = respond({ status: "ok", db: "ok", redis: "ok" });
    vi.stubGlobal("fetch", fetchMock);
    const { user } = renderWithClient(<HealthPage />);
    await screen.findByText("All systems operational");
    expect(fetchMock).toHaveBeenCalledTimes(1);
    await user.click(screen.getByRole("button", { name: "Check again" }));
    await waitFor(() => expect(fetchMock).toHaveBeenCalledTimes(2));
  });
});
