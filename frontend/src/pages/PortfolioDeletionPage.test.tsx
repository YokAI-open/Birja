import { cleanup, render, screen } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { MemoryRouter } from "react-router";
import { afterEach, expect, it, vi } from "vitest";
import PortfolioDeletionPage from "./PortfolioDeletionPage";

afterEach(() => { cleanup(); sessionStorage.clear(); vi.unstubAllGlobals(); });
it("offers private overview navigation when a direct recovery URL has no original", async () => {
  const fetch = vi.fn(() => Promise.reject(new Error("No financial request allowed")));
  vi.stubGlobal("fetch", fetch);
  const client = new QueryClient({ defaultOptions: { queries: { retry: false, staleTime: Infinity } } });
  client.setQueryData(["me"], { email: "alice@example.test" });
  render(<QueryClientProvider client={client}><MemoryRouter initialEntries={["/portfolios/deletion"]}><PortfolioDeletionPage /></MemoryRouter></QueryClientProvider>);
  expect(await screen.findByText("No deletion request to check.")).toBeVisible();
  expect(screen.getByRole("link", { name: "Portfolios" })).toHaveAttribute("href", "/portfolios");
  expect(screen.queryByRole("button", { name: "Delete portfolio" })).toBeNull();
  expect(fetch).not.toHaveBeenCalled();
  client.clear();
});
