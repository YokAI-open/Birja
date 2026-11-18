import { act, cleanup, render, screen, waitFor } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { MemoryRouter, useLocation } from "react-router";
import userEvent from "@testing-library/user-event";
import { afterEach, expect, it, vi } from "vitest";
import { PortfolioSwitcher } from "./PortfolioSwitcher";

const clients: QueryClient[] = [];
const json = (value: unknown) => new Response(JSON.stringify(value));
function Location() {
  return <p data-testid="location">{useLocation().pathname}</p>;
}
function setup(items: { id: string; name: string }[], portfolioId?: string) {
  const client = new QueryClient({ defaultOptions: { queries: { retry: false, gcTime: 0 } } });
  clients.push(client);
  client.setQueryData(["me"], { email: "alice@example.test" });
  const fetch = vi.fn(() => Promise.resolve(json(items)));
  vi.stubGlobal("fetch", fetch);
  const user = userEvent.setup();
  render(
    <QueryClientProvider client={client}>
      <MemoryRouter initialEntries={["/portfolios/1/trade/BTC"]}>
        <Location />
        <PortfolioSwitcher portfolioId={portfolioId} />
      </MemoryRouter>
    </QueryClientProvider>,
  );
  return { client, user, fetch };
}
afterEach(() => {
  cleanup();
  clients.splice(0).forEach((c) => c.clear());
  vi.unstubAllGlobals();
});

it.each([0, 1, 10])(
  "offers %i identities without selecting or opening one automatically",
  async (count) => {
    const items = Array.from({ length: count }, (_, i) => ({
      id: String(i + 1),
      name: `Strategy ${i + 1}`,
    }));
    const { fetch } = setup(items);
    const select = await screen.findByRole("combobox", { name: "Open portfolio" });
    await waitFor(() => expect(select).toBeEnabled());
    expect(screen.getAllByRole("option")).toHaveLength(count + 1);
    expect(
      screen
        .getAllByRole("option")
        .slice(1)
        .map((option) => option.getAttribute("value")),
    ).toEqual(items.map((item) => item.id));
    expect(select).toHaveValue("");
    expect(screen.getByRole("button", { name: "Open selected portfolio" })).toBeDisabled();
    expect(screen.getByTestId("location")).toHaveTextContent("/portfolios/1/trade/BTC");
    expect(screen.getByRole("link", { name: "Portfolios" })).toHaveAttribute("href", "/portfolios");
    expect(fetch.mock.calls).toHaveLength(1);
  },
);
it("keeps native selection and Escape separate from explicit keyboard Open", async () => {
  const name = "<script>" + "Long".repeat(10) + "</script>";
  const { user } = setup(
    [
      { id: "1", name },
      { id: "2", name: "Second" },
    ],
    "1",
  );
  const select = await screen.findByRole("combobox", { name: "Open portfolio" });
  await waitFor(() => expect(select).toBeEnabled());
  expect(screen.getByRole("option", { name: `${name} · #1` })).toHaveValue("1");
  const current = screen.getByText(name);
  expect(current).toHaveClass("min-w-0");
  expect(current.className).toContain("overflow-wrap:anywhere");
  expect(document.querySelector("script")).toBeNull();
  select.focus();
  await user.keyboard("{ArrowDown}{Escape}");
  await user.selectOptions(select, "2");
  expect(screen.getByTestId("location")).toHaveTextContent("/portfolios/1/trade/BTC");
  expect(current).toHaveTextContent(name);
  await user.tab();
  expect(screen.getByRole("button", { name: "Open selected portfolio" })).toHaveFocus();
  await user.keyboard("{Enter}");
  expect(screen.getByTestId("location")).toHaveTextContent(/^\/portfolios\/2$/);
});
it("revokes a removed choice and does not select its replacement", async () => {
  const { user, client } = setup([
    { id: "1", name: "First" },
    { id: "2", name: "Second" },
  ]);
  const select = await screen.findByRole("combobox");
  await waitFor(() => expect(select).toBeEnabled());
  await user.selectOptions(select, "1");
  vi.stubGlobal("fetch", () => Promise.resolve(json([{ id: "2", name: "Second" }])));
  await act(async () => {
    await client.invalidateQueries({ queryKey: ["portfolios"] });
  });
  await waitFor(() =>
    expect(screen.getByRole("button", { name: "Open selected portfolio" })).toBeDisabled(),
  );
  expect(screen.getByTestId("location")).toHaveTextContent("/portfolios/1/trade/BTC");
});
it("hides old owner labels and selection immediately across session loss", async () => {
  const { user, client } = setup([{ id: "1", name: "Private Alice" }]);
  const select = await screen.findByRole("combobox");
  await waitFor(() => expect(select).toBeEnabled());
  await user.selectOptions(select, "1");
  act(() => client.setQueryData(["me"], null));
  await waitFor(() => expect(screen.queryByRole("combobox")).toBeNull());
  expect(screen.queryByText(/Private Alice/)).toBeNull();
});

it("masks choices on failed discovery refresh rather than using stale labels", async () => {
  const { client } = setup([{ id: "1", name: "Private label" }], "1");
  await screen.findByText("Private label");
  vi.stubGlobal("fetch", () => Promise.resolve(new Response("{}", { status: 500 })));
  await act(async () => {
    await client.invalidateQueries({ queryKey: ["portfolios"] });
  });
  await screen.findByRole("alert");
  expect(screen.queryByText(/Private label/)).toBeNull();
  expect(screen.getByRole("combobox")).toBeDisabled();
  expect(screen.getByRole("button", { name: "Open selected portfolio" })).toBeDisabled();
  expect(screen.getByRole("link", { name: "Portfolios" })).toHaveAttribute("href", "/portfolios");
});

it("discards late old-owner discovery and never restores its draft in a replacement session", async () => {
  const { client, user } = setup([{ id: "1", name: "Alice private" }]);
  const select = await screen.findByRole("combobox");
  await waitFor(() => expect(select).toBeEnabled());
  await user.selectOptions(select, "1");
  let release!: (response: Response) => void;
  let calls = 0;
  vi.stubGlobal("fetch", () =>
    ++calls === 1
      ? new Promise<Response>((resolve) => {
          release = resolve;
        })
      : Promise.resolve(json([{ id: "2", name: "Bob strategy" }])),
  );
  let pending!: Promise<void>;
  act(() => {
    pending = client.invalidateQueries({ queryKey: ["portfolios"] });
  });
  await waitFor(() => expect(release).toBeTypeOf("function"));
  act(() => client.setQueryData(["me"], { email: "bob@example.test" }));
  expect(await screen.findByRole("option", { name: "Bob strategy · #2" })).toBeVisible();
  await act(async () => {
    release(json([{ id: "1", name: "Alice private" }]));
    await pending;
  });
  expect(screen.queryByText(/Alice private/)).toBeNull();
  expect(screen.getByRole("combobox")).toHaveValue("");
  expect(screen.getByRole("button", { name: "Open selected portfolio" })).toBeDisabled();
});
