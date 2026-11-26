import { useEffect } from "react";
import { act, render, screen, waitFor, within } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { MemoryRouter, useLocation, useNavigate, useOutletContext, useParams } from "react-router";
import userEvent from "@testing-library/user-event";
import { afterEach, expect, it, vi } from "vitest";
import type { PortfolioTarget } from "@/hooks/usePortfolioTarget";
import { PortfolioContext } from "@/components/PortfolioContext";
import App from "./App";
import { DELETION_STORAGE_KEY, openDeletionRecovery } from "@/lib/portfolioDeletionAttempt";
import { capturePortfolioDeletionIntent, DELETION_POLICY } from "@/api/portfolioDeletion";
import { cashPortfolio } from "@/test/portfolioFixtures";

// Real page migration belongs to24/25; these probes verify shell and boundary
// wiring and captured target identity without claiming future page behavior.
const probes = vi.hoisted(() => ({ mounted: vi.fn(), actualPage: false }));
function FinancialProbe({ page }: { page: string }) {
  const target = useOutletContext<PortfolioTarget>();
  const { pathname } = useLocation();
  const { symbol } = useParams();
  const Heading = page === "Portfolio page" ? "h2" : "h1";
  useEffect(() => {
    probes.mounted(pathname, target);
  }, [pathname, target]);
  return (
    <>
      <Heading>
        {page}
        {symbol ? ` ${symbol}` : ""}
      </Heading>
      <PortfolioContext name={target.name} />
      <p>
        Private {target.owner} root {target.portfolioId}
      </p>
      <button>Financial action</button>
    </>
  );
}
vi.mock("@/pages/PortfolioPage", async (importOriginal) => {
  const RealPage = (await importOriginal<typeof import("@/pages/PortfolioPage")>()).default;
  return {
    default: () => (probes.actualPage ? <RealPage /> : <FinancialProbe page="Portfolio page" />),
  };
});
vi.mock("@/pages/HistoryPage", () => ({ default: () => <FinancialProbe page="History page" /> }));
vi.mock("@/pages/TradePage", () => ({ default: () => <FinancialProbe page="Crypto" /> }));
vi.mock("@/pages/StockTradePage", () => ({ default: () => <FinancialProbe page="Stock" /> }));

const json = (body: unknown, status = 200) => new Response(JSON.stringify(body), { status });
const unauthorized = () =>
  json({ detail: { code: "not_authenticated", message: "Unavailable" } }, 401);
const first = { id: "1", name: "My portfolio" },
  second = { id: "2", name: "Second strategy" };

const clients: QueryClient[] = [];
function prices() {
  return json({
    server_time: "2026-11-16T10:00:00Z",
    fresh_seconds: 90,
    stale_seconds: 300,
    items: [
      {
        symbol: "BTC",
        name: "Bitcoin",
        price: "81042.35000000",
        as_of: "2026-11-16T09:59:50Z",
        age_seconds: 10,
        status: "fresh",
      },
    ],
  });
}
function api({
  identity = () => json({ email: "alice@example.test" }),
  metadata = () => json([first]),
}: {
  identity?: () => Response | Promise<Response>;
  metadata?: () => Response | Promise<Response>;
} = {}) {
  const fetch = vi.fn((path: string) =>
    Promise.resolve(
      path === "/api/v2/me"
        ? identity()
        : path === "/api/v2/portfolios"
          ? metadata()
          : path === "/api/v2/portfolios/overview"
            ? json([])
            : path === "/api/v1/prices"
              ? prices()
              : path === "/api/v1/health"
                ? json({ status: "ok", db: "ok", redis: "ok" })
                : path === "/api/v1/auth/refresh"
                  ? unauthorized()
                  : json({}, 500),
    ),
  );
  vi.stubGlobal("fetch", fetch);
  return fetch;
}
function Controls() {
  const navigate = useNavigate();
  return (
    <>
      <button onClick={() => void navigate(-1)}>Back</button>
      <p data-testid="location">{useLocation().pathname}</p>
    </>
  );
}
function setup(route = "/") {
  const client = new QueryClient({ defaultOptions: { queries: { retry: false, gcTime: 0 } } });
  clients.push(client);
  return {
    client,
    user: userEvent.setup(),
    ...render(
      <QueryClientProvider client={client}>
        <MemoryRouter initialEntries={[route]}>
          <Controls />
          <App />
        </MemoryRouter>
      </QueryClientProvider>,
    ),
  };
}
afterEach(() => {
  clients.splice(0).forEach((c) => c.clear());
  vi.unstubAllGlobals();
  probes.mounted.mockReset();
  probes.actualPage = false;
  document.cookie = "bj_csrf=; max-age=0; path=/";
  sessionStorage.clear();
});

const privateJson = (body: unknown, status = 200) =>
  new Response(JSON.stringify(body), { status, headers: { "Content-Type": "application/json" } });
function deletionApi({
  result,
  listFailure = false,
  metadata = () => ({ ...first, description: "Keep this strategy" }),
  rows = () => [first],
}: {
  result?: () => Promise<Response>;
  listFailure?: boolean;
  metadata?: () => { id: string; name: string; description: string };
  rows?: () => { id: string; name: string }[];
} = {}) {
  let closed = false;
  const fetch = vi.fn(async (path: string, init?: RequestInit) => {
    if (path === "/api/v2/me") return privateJson({ email: "alice@example.test" });
    if (path === "/api/v2/portfolios/1" && init?.method === "DELETE") {
      const response = result
        ? await result()
        : privateJson({ portfolio_id: "1", state: "closed" });
      if (response.ok) closed = true;
      return response;
    }
    if (path === "/api/v2/portfolios/1/metadata")
      return closed
        ? privateJson({ detail: { code: "portfolio_unavailable" } }, 404)
        : privateJson(metadata());
    if (path === "/api/v2/portfolios/1") return privateJson(cashPortfolio());
    if (path === "/api/v2/portfolios")
      return closed && listFailure
        ? privateJson({}, 503)
        : privateJson(closed ? rows().filter((row) => row.id !== "1") : rows());
    if (path === "/api/v2/portfolios/overview")
      return closed && listFailure ? privateJson({}, 503) : privateJson([]);
    if (path === "/api/v1/prices") return prices();
    if (path === "/api/v1/health") return privateJson({ status: "ok", db: "ok", redis: "ok" });
    return privateJson({}, 500);
  });
  vi.stubGlobal("fetch", fetch);
  document.cookie = "bj_csrf=test; path=/";
  return fetch;
}
it("mounts static authenticated deletion recovery outside the dynamic financial route", async () => {
  const fetch = deletionApi();
  setup("/portfolios/deletion");
  expect(await screen.findByText("No deletion request to check.")).toBeVisible();
  expect(screen.getByRole("heading", { name: "Deletion request", level: 1 })).toHaveFocus();
  expect(probes.mounted).not.toHaveBeenCalled();
  expect(fetch.mock.calls.some(([path]) => path.includes("/deletion/"))).toBe(false);
  expect(screen.getByRole("button", { name: "Sign out" })).toBeVisible();
});
it("keeps the deletion lease alive while quarantine removes the financial Outlet and then opens the empty overview", async () => {
  let release!: (response: Response) => void;
  const fetch = deletionApi({
    result: () =>
      new Promise((resolve) => {
        release = resolve;
      }),
  });
  const { user } = setup("/portfolios/1");
  await user.click(await screen.findByRole("button", { name: "Remove portfolio" }));
  expect(screen.getByRole("button", { name: "Cancel" })).toHaveFocus();
  expect(screen.getByText(/This is your last active portfolio/)).toBeVisible();
  await user.click(screen.getByRole("button", { name: "Delete portfolio" }));
  await waitFor(() => expect(release).toBeTypeOf("function"));
  expect(await screen.findByRole("heading", { name: "Deleting portfolio…" })).toBeVisible();
  expect(screen.queryByText(/Private alice/)).toBeNull();
  expect(JSON.parse(sessionStorage.getItem(DELETION_STORAGE_KEY)!).attempt.portfolioId).toBe("1");
  await act(async () => release(privateJson({ portfolio_id: "1", state: "closed" })));
  expect(await screen.findByText("No portfolios yet")).toBeVisible();
  expect(screen.getByTestId("location")).toHaveTextContent(/^\/portfolios$/);
  expect(screen.getByRole("heading", { name: "Portfolios", level: 1 })).toHaveFocus();
  expect(screen.getByRole("button", { name: "New portfolio" })).toBeEnabled();
  expect(fetch.mock.calls.filter(([, init]) => init?.method === "DELETE")).toHaveLength(1);
  expect(fetch.mock.calls.some(([, init]) => init?.method === "POST")).toBe(false);
  const financialMounts = probes.mounted.mock.calls.length;
  await user.click(screen.getByRole("button", { name: "Back" }));
  expect(await screen.findByRole("heading", { name: "Portfolio unavailable" })).toBeVisible();
  expect(probes.mounted.mock.calls).toHaveLength(financialMounts);
  expect(fetch.mock.calls.some(([, init]) => init?.method === "POST")).toBe(false);
});
it("keeps a lost original named request in recovery without auto DELETE on navigation or reload", async () => {
  const fetch = deletionApi({ result: () => Promise.reject(new TypeError("lost")) });
  const { user, unmount } = setup("/portfolios/1");
  await user.click(await screen.findByRole("button", { name: "Remove portfolio" }));
  await user.click(screen.getByRole("button", { name: "Delete portfolio" }));
  expect(await screen.findByRole("heading", { name: "Deletion result unconfirmed" })).toBeVisible();
  await user.click(screen.getAllByRole("link", { name: "Portfolios" })[0]);
  await user.click(await screen.findByRole("link", { name: "Review deletion request" }));
  expect(screen.getByTestId("location")).toHaveTextContent(/^\/portfolios\/deletion$/);
  expect(await screen.findByText(/We couldn't confirm whether/)).toHaveTextContent(first.name);
  unmount();
  setup("/portfolios/deletion");
  expect(await screen.findByText(/We couldn't confirm whether/)).toHaveTextContent(first.name);
  expect(fetch.mock.calls.filter(([, init]) => init?.method === "DELETE")).toHaveLength(1);
});
it.each(["signed-out", "same-owner-new-session", "replacement-owner"])(
  "does not navigate on a late closure after %s",
  async (next) => {
    let release!: (response: Response) => void;
    deletionApi({
      result: () =>
        new Promise((resolve) => {
          release = resolve;
        }),
    });
    const { user, client } = setup("/portfolios/1");
    await user.click(await screen.findByRole("button", { name: "Remove portfolio" }));
    await user.click(screen.getByRole("button", { name: "Delete portfolio" }));
    await waitFor(() => expect(release).toBeTypeOf("function"));
    act(() => {
      client.setQueryData(["me"], null);
      if (next !== "signed-out")
        client.setQueryData(["me"], {
          email: next === "same-owner-new-session" ? "alice@example.test" : "bob@example.test",
        });
    });
    if (next === "signed-out")
      expect(await screen.findByRole("heading", { name: "Sign in" })).toBeVisible();
    else await screen.findByRole("navigation", { name: "Main" });
    await act(async () => release(privateJson({ portfolio_id: "1", state: "closed" })));
    expect(screen.getByTestId("location")).toHaveTextContent(/^\/portfolios\/1$/);
    expect(screen.queryByText("Portfolio deleted.")).toBeNull();
  },
);
it("does not turn a failed post-ack overview read into an empty account", async () => {
  deletionApi({ listFailure: true });
  const { user } = setup("/portfolios/1");
  await user.click(await screen.findByRole("button", { name: "Remove portfolio" }));
  await user.click(screen.getByRole("button", { name: "Delete portfolio" }));
  expect(await screen.findByText("Can't load your portfolios right now. Try again.")).toBeVisible();
  expect(screen.queryByText("No portfolios yet")).toBeNull();
});
it("restores only a validated same-tab original on the static recovery route", async () => {
  const recovery = await openDeletionRecovery("alice@example.test", () => true);
  recovery.persist(
    capturePortfolioDeletionIntent({
      portfolioId: "1",
      confirmationName: first.name,
      intentKey: crypto.randomUUID(),
      policyVersion: DELETION_POLICY,
    }),
  );
  const fetch = deletionApi();
  const { user } = setup("/portfolios/deletion");
  expect(await screen.findByText(/We couldn't confirm whether/)).toHaveTextContent(first.name);
  expect(probes.mounted).not.toHaveBeenCalled();
  expect(fetch.mock.calls.some(([, init]) => init?.method === "DELETE")).toBe(false);
  await user.click(screen.getByRole("button", { name: "Check deletion result" }));
  expect(await screen.findByText("No portfolios yet")).toBeVisible();
});
it("cancels before submit with Escape and restores the disclosure without sending DELETE", async () => {
  const fetch = deletionApi();
  const { user } = setup("/portfolios/1");
  await user.click(await screen.findByRole("button", { name: "Remove portfolio" }));
  expect(screen.getByRole("button", { name: "Edit portfolio" })).toBeDisabled();
  await user.keyboard("{Escape}");
  expect(screen.getByRole("button", { name: "Remove portfolio" })).toHaveFocus();
  expect(screen.queryByRole("button", { name: "Delete portfolio" })).toBeNull();
  expect(fetch.mock.calls.some(([, init]) => init?.method === "DELETE")).toBe(false);
  await user.click(screen.getByRole("button", { name: "Edit portfolio" }));
  expect(screen.getByRole("button", { name: "Remove portfolio" })).toBeDisabled();
  await user.type(screen.getByLabelText("Description (optional)"), "Keep this draft");
  expect(screen.getByRole("button", { name: "Remove portfolio" })).toBeDisabled();
});
it("requires a fresh named review after a durable rename conflict without sending twice", async () => {
  let name = first.name;
  const fetch = deletionApi({
    metadata: () => ({ ...first, name, description: "Keep" }),
    result: async () => {
      name = "Changed strategy";
      return privateJson({ detail: { code: "portfolio_confirmation_changed" } }, 409);
    },
  });
  const { user } = setup("/portfolios/1");
  await user.click(await screen.findByRole("button", { name: "Remove portfolio" }));
  await user.click(screen.getByRole("button", { name: "Delete portfolio" }));
  expect(await screen.findByText(/This portfolio's name changed/)).toBeVisible();
  expect(screen.queryByRole("button", { name: "Delete portfolio" })).toBeNull();
  await user.click(screen.getByRole("button", { name: "Review latest portfolio" }));
  await waitFor(() =>
    expect(screen.getByRole("button", { name: "Remove portfolio" })).toBeEnabled(),
  );
  await user.click(screen.getByRole("button", { name: "Remove portfolio" }));
  expect(screen.getByRole("heading", { name: "Delete “Changed strategy”?" })).toBeVisible();
  expect(fetch.mock.calls.filter(([, init]) => init?.method === "DELETE")).toHaveLength(1);
});
it("opens the editor from the toolbar and returns keyboard focus on discard", async () => {
  deletionApi();
  const { user } = setup("/portfolios/1");
  const edit = await screen.findByRole("button", { name: "Edit portfolio" });
  edit.focus();
  await user.keyboard("{Enter}");
  expect(await screen.findByRole("region", { name: "Edit portfolio" })).toHaveFocus();
  await user.click(screen.getByRole("button", { name: "Discard changes" }));
  expect(edit).toHaveFocus();
  const nav = within(screen.getByRole("navigation", { name: "Main" }));
  expect(nav.getByRole("link", { name: "Portfolios" })).toHaveAttribute("aria-current", "page");
});
it("keeps current-page focus and navigation when an obsolete deletion replies after leaving", async () => {
  let release!: (response: Response) => void;
  deletionApi({
    result: () =>
      new Promise((resolve) => {
        release = resolve;
      }),
  });
  const { user } = setup("/portfolios/1");
  await user.click(await screen.findByRole("button", { name: "Remove portfolio" }));
  await user.click(screen.getByRole("button", { name: "Delete portfolio" }));
  await waitFor(() => expect(release).toBeTypeOf("function"));
  await user.click(screen.getByRole("link", { name: "Markets" }));
  const heading = await screen.findByRole("heading", { name: "Markets", level: 1 });
  expect(heading).toHaveFocus();
  await act(async () => release(privateJson({ portfolio_id: "1", state: "closed" })));
  expect(screen.getByTestId("location")).toHaveTextContent(/^\/$/);
  expect(heading).toHaveFocus();
  expect(screen.getByRole("button", { name: "Sign out" })).toBeVisible();
  expect(JSON.parse(sessionStorage.getItem(DELETION_STORAGE_KEY)!).attempt.portfolioId).toBe("1");
});
it("does not expose a prior owner's original on a signed-in replacement session", async () => {
  const recovery = await openDeletionRecovery("another@example.test", () => true);
  recovery.persist(
    capturePortfolioDeletionIntent({
      portfolioId: "1",
      confirmationName: "Private prior strategy",
      intentKey: crypto.randomUUID(),
      policyVersion: DELETION_POLICY,
    }),
  );
  const fetch = deletionApi();
  setup("/portfolios/deletion");
  expect(await screen.findByText("No deletion request to check.")).toBeVisible();
  expect(screen.queryByText(/Private prior strategy/)).toBeNull();
  expect(fetch.mock.calls.some(([, init]) => init?.method === "DELETE")).toBe(false);
});
it("offers explicit storage retry on recovery without implicitly sending any original", async () => {
  const recovery = await openDeletionRecovery("alice@example.test", () => true);
  recovery.persist(
    capturePortfolioDeletionIntent({
      portfolioId: "1",
      confirmationName: first.name,
      intentKey: crypto.randomUUID(),
      policyVersion: DELETION_POLICY,
    }),
  );
  const read = Storage.prototype.getItem;
  const broken = vi.spyOn(Storage.prototype, "getItem").mockImplementation(function (
    this: Storage,
    key,
  ) {
    if (key === DELETION_STORAGE_KEY) throw new Error("storage unavailable");
    return read.call(this, key);
  });
  const fetch = deletionApi();
  const { user } = setup("/portfolios/deletion");
  expect(
    await screen.findByText("Can't check deletion recovery right now. Try again."),
  ).toBeVisible();
  broken.mockRestore();
  await user.click(screen.getByRole("button", { name: "Retry deletion recovery" }));
  expect(await screen.findByText(/We couldn't confirm whether/)).toHaveTextContent(first.name);
  expect(fetch.mock.calls.some(([, init]) => init?.method === "DELETE")).toBe(false);
});
it("never unhides the original when a different same-name strategy is discovered", async () => {
  const recovery = await openDeletionRecovery("alice@example.test", () => true);
  recovery.persist(
    capturePortfolioDeletionIntent({
      portfolioId: "1",
      confirmationName: first.name,
      intentKey: crypto.randomUUID(),
      policyVersion: DELETION_POLICY,
    }),
  );
  const fetch = deletionApi({ rows: () => [{ id: "2", name: first.name }] });
  const { user } = setup("/portfolios/1");
  expect(await screen.findByRole("heading", { name: "Portfolio unavailable" })).toBeVisible();
  expect(probes.mounted).not.toHaveBeenCalled();
  expect(screen.getByTestId("location")).toHaveTextContent(/^\/portfolios\/1$/);
  await user.click(screen.getAllByRole("link", { name: "Portfolios" })[0]);
  expect(await screen.findByRole("link", { name: "Review deletion request" })).toBeVisible();
  expect(fetch.mock.calls.some(([, init]) => init?.method === "DELETE")).toBe(false);
});
it("ends on the overview without auto-opening the one remaining sibling", async () => {
  const fetch = deletionApi({ rows: () => [first, second] });
  const { user } = setup("/portfolios/1");
  await user.click(await screen.findByRole("button", { name: "Remove portfolio" }));
  expect(screen.queryByText(/This is your last active portfolio/)).toBeNull();
  await user.click(screen.getByRole("button", { name: "Delete portfolio" }));
  await screen.findByRole("heading", { name: "Portfolios", level: 1 });
  expect(screen.getByTestId("location")).toHaveTextContent(/^\/portfolios$/);
  expect(probes.mounted.mock.calls.every(([, target]) => target.portfolioId === "1")).toBe(true);
  expect(fetch.mock.calls.some(([, init]) => init?.method === "POST")).toBe(false);
});
it("keeps terminal recovery refusal explicit and links only to fresh same-ID metadata review", async () => {
  const recovery = await openDeletionRecovery("alice@example.test", () => true);
  recovery.persist(
    capturePortfolioDeletionIntent({
      portfolioId: "1",
      confirmationName: first.name,
      intentKey: crypto.randomUUID(),
      policyVersion: DELETION_POLICY,
    }),
  );
  const fetch = deletionApi({
    result: async () => privateJson({ detail: { code: "portfolio_confirmation_changed" } }, 409),
    metadata: () => ({ ...first, name: "Latest strategy", description: "" }),
  });
  const { user } = setup("/portfolios/deletion");
  await user.click(await screen.findByRole("button", { name: "Check deletion result" }));
  expect(await screen.findByText(/This portfolio's name changed/)).toBeVisible();
  const review = screen.getByRole("link", { name: "Review latest portfolio" });
  expect(review).toHaveAttribute("href", "/portfolios/1");
  await user.click(review);
  await waitFor(() =>
    expect(screen.getByRole("button", { name: "Remove portfolio" })).toBeEnabled(),
  );
  await user.click(screen.getByRole("button", { name: "Remove portfolio" }));
  expect(screen.getByRole("heading", { name: "Delete “Latest strategy”?" })).toBeVisible();
  expect(fetch.mock.calls.filter(([, init]) => init?.method === "DELETE")).toHaveLength(1);
});
it("focuses the private unavailable heading when a focused metadata field loses authority", async () => {
  let active = [first];
  deletionApi({ rows: () => active });
  const { user, client } = setup("/portfolios/1");
  await user.click(await screen.findByRole("button", { name: "Edit portfolio" }));
  const field = screen.getByLabelText("Description (optional)");
  await user.type(field, "Private draft");
  expect(field).toHaveFocus();
  active = [];
  await act(async () => client.invalidateQueries({ queryKey: ["portfolios"] }));
  expect(await screen.findByRole("heading", { name: "Portfolio unavailable" })).toHaveFocus();
  expect(screen.queryByDisplayValue(/Private draft/)).toBeNull();
});
it("keeps a terminal-refusal same-ID metadata retry visible after fresh proof fails", async () => {
  probes.actualPage = true;
  let failMetadata = false;
  let deletes = 0;
  const base = deletionApi({
    result: async () => {
      deletes++;
      if (deletes > 1) return privateJson({ portfolio_id: "1", state: "closed" });
      failMetadata = true;
      return privateJson({ detail: { code: "portfolio_confirmation_changed" } }, 409);
    },
    metadata: () => ({
      ...first,
      name: deletes ? "Latest strategy" : first.name,
      description: "Keep",
    }),
  });
  const fetch = vi.fn((path: string, init?: RequestInit) =>
    path === "/api/v2/portfolios/1/metadata" && failMetadata
      ? Promise.resolve(privateJson({}, 503))
      : base(path, init),
  );
  vi.stubGlobal("fetch", fetch);
  const { user } = setup("/portfolios/1");
  await screen.findByRole("region", { name: "Cash" });
  await user.click(await screen.findByRole("button", { name: "Remove portfolio" }));
  await user.click(screen.getByRole("button", { name: "Delete portfolio" }));
  const review = await screen.findByRole("button", { name: "Review latest portfolio" });
  expect(
    await screen.findByText("Can't load portfolio metadata right now. Try again."),
  ).toBeVisible();
  await waitFor(() => expect(review).toBeEnabled());
  expect(screen.getByText(/This portfolio's name changed/)).toBeVisible();
  expect(screen.queryByRole("region", { name: "Cash" })).toBeNull();
  expect(screen.queryByText("Keep")).toBeNull();
  expect(deletes).toBe(1);
  const proofReads = fetch.mock.calls.filter(([path]) => path.endsWith("/metadata")).length;
  await user.click(review);
  await waitFor(() =>
    expect(fetch.mock.calls.filter(([path]) => path.endsWith("/metadata")).length).toBeGreaterThan(
      proofReads,
    ),
  );
  await waitFor(() => expect(review).toBeEnabled());
  expect(screen.getByRole("alert")).toHaveFocus();
  expect(screen.queryByRole("region", { name: "Cash" })).toBeNull();
  expect(deletes).toBe(1);
  failMetadata = false;
  await user.click(review);
  await waitFor(() =>
    expect(screen.getByRole("button", { name: "Remove portfolio" })).toBeEnabled(),
  );
  expect(deletes).toBe(1);
  await user.click(screen.getByRole("button", { name: "Remove portfolio" }));
  expect(screen.getByRole("heading", { name: "Delete “Latest strategy”?" })).toBeVisible();
  expect(deletes).toBe(1);
  await user.click(screen.getByRole("button", { name: "Delete portfolio" }));
  await screen.findByRole("heading", { name: "Portfolios", level: 1 });
  expect(deletes).toBe(2);
  expect(
    fetch.mock.calls
      .filter(([, init]) => init?.method === "DELETE")
      .every(([path]) => path === "/api/v2/portfolios/1"),
  ).toBe(true);
});
it("uses one managed toolbar in chooser, Edit, Update and Remove tab order", async () => {
  probes.actualPage = true;
  const fetch = deletionApi({ rows: () => [first, second] });
  const { user } = setup("/portfolios/1");
  await screen.findByRole("region", { name: "Cash" });
  const toolbar = screen.getByRole("group", { name: "Portfolio controls" });
  const chooser = within(toolbar).getByRole("combobox", { name: "Open portfolio" });
  const edit = within(toolbar).getByRole("button", { name: "Edit portfolio" });
  const update = within(toolbar).getByRole("button", { name: "Update portfolio" });
  const remove = within(toolbar).getByRole("button", { name: "Remove portfolio" });
  await waitFor(() => expect(remove).toBeEnabled());
  expect(screen.getAllByRole("combobox", { name: "Open portfolio" })).toEqual([chooser]);
  expect(screen.getAllByRole("button", { name: "Update portfolio" })).toEqual([update]);
  expect([...toolbar.querySelectorAll("select, button")]).toEqual([chooser, edit, update, remove]);
  expect(update.querySelector("time")).toHaveAttribute("datetime", cashPortfolio().valued_at);
  await user.click(chooser);
  await user.tab();
  expect(edit).toHaveFocus();
  await user.tab();
  expect(update).toHaveFocus();
  await user.tab();
  expect(remove).toHaveFocus();
  await user.click(update);
  await waitFor(() =>
    expect(fetch.mock.calls.filter(([path]) => path === "/api/v2/portfolios/1")).toHaveLength(2),
  );
  expect(fetch.mock.calls.some(([path]) => path === "/api/v2/portfolios/2")).toBe(false);
});

it.each(["/portfolios/1", "/portfolios/1/"])(
  "gives real index %s one primary h1 and the persistent management host",
  async (route) => {
    probes.actualPage = true;
    let reject!: (reason: unknown) => void;
    deletionApi({
      result: () =>
        new Promise((_resolve, rejectResult) => {
          reject = rejectResult;
        }),
    });
    const { user } = setup(route);
    await screen.findByRole("region", { name: "Cash" });
    expect(screen.getAllByRole("heading", { level: 1 })).toHaveLength(1);
    expect(screen.getByRole("heading", { level: 1 })).toBeVisible();
    await waitFor(() =>
      expect(screen.getByRole("button", { name: "Edit portfolio" })).toBeEnabled(),
    );
    await user.click(screen.getByRole("button", { name: "Remove portfolio" }));
    expect(screen.getByRole("button", { name: "Cancel" })).toHaveFocus();
    await user.click(screen.getByRole("button", { name: "Cancel" }));
    expect(screen.getByRole("button", { name: "Remove portfolio" })).toHaveFocus();
    await user.click(screen.getByRole("button", { name: "Remove portfolio" }));
    await user.click(screen.getByRole("button", { name: "Delete portfolio" }));
    await waitFor(() => expect(reject).toBeTypeOf("function"));
    expect(await screen.findByRole("heading", { name: "Deleting portfolio…" })).toBeVisible();
    expect(screen.getAllByRole("heading")[0].tagName).toBe("H1");
    expect(screen.getAllByRole("heading", { level: 1 })).toHaveLength(1);
    await act(async () => reject(new TypeError("lost")));
    expect(
      await screen.findByRole("heading", { name: "Deletion result unconfirmed" }),
    ).toBeVisible();
    expect(screen.getAllByRole("heading")[0].tagName).toBe("H1");
    expect(screen.getAllByRole("heading", { level: 1 })).toHaveLength(1);
    expect(screen.queryByRole("region", { name: "Cash" })).toBeNull();
  },
);
it("places one generic primary h1 before a real restored-unknown detail section", async () => {
  probes.actualPage = true;
  const recovery = await openDeletionRecovery("alice@example.test", () => true);
  recovery.persist(
    capturePortfolioDeletionIntent({
      portfolioId: "1",
      confirmationName: first.name,
      intentKey: crypto.randomUUID(),
      policyVersion: DELETION_POLICY,
    }),
  );
  const fetch = deletionApi();
  setup("/portfolios/1");
  expect(await screen.findByRole("heading", { name: "Deletion result unconfirmed" })).toBeVisible();
  expect(screen.getAllByRole("heading")[0].tagName).toBe("H1");
  expect(screen.getAllByRole("heading", { level: 1 })).toHaveLength(1);
  expect(screen.queryByRole("region", { name: "Cash" })).toBeNull();
  expect(fetch.mock.calls.some(([, init]) => init?.method === "DELETE")).toBe(false);
});
it.each(["/portfolios/1/history", "/portfolios/1/trade/BTC", "/portfolios/1/trade/stocks/AAPL"])(
  "keeps management off nested route %s",
  async (route) => {
    deletionApi();
    setup(route);
    await screen.findByText(/Private alice@example.test root 1/);
    expect(screen.getAllByRole("heading", { level: 1 })).toHaveLength(1);
    expect(screen.queryByRole("button", { name: "Edit portfolio" })).toBeNull();
    expect(screen.queryByRole("button", { name: "Update portfolio" })).toBeNull();
    expect(screen.queryByRole("button", { name: "Remove portfolio" })).toBeNull();
  },
);
it("keeps a trailing-slash inaccessible index generic even if stale metadata is returned", async () => {
  probes.actualPage = true;
  deletionApi({ rows: () => [] });
  setup("/portfolios/1/");
  expect(
    await screen.findByRole("heading", { name: "Portfolio unavailable", level: 1 }),
  ).toBeVisible();
  expect(screen.getAllByRole("heading", { level: 1 })).toHaveLength(1);
  expect(screen.queryByRole("button", { name: "Remove portfolio" })).toBeNull();
  expect(screen.queryByRole("button", { name: "Edit portfolio" })).toBeNull();
  expect(screen.queryByText(first.name)).toBeNull();
  expect(screen.queryByText("Keep this strategy")).toBeNull();
  expect(screen.queryByRole("region", { name: "Cash" })).toBeNull();
});

it("keeps the sign-out door beside three responsive primary destinations", async () => {
  api();
  const { user } = setup();
  const nav = await screen.findByRole("navigation", { name: "Main" });
  expect(nav.querySelectorAll("a")).toHaveLength(3);
  expect(nav).not.toContainElement(screen.getByRole("button", { name: "Sign out" }));
  const header = screen.getByRole("banner");
  expect(header).toContainElement(nav);
  expect(header).toContainElement(screen.getByText("Birja"));
  expect(header).toContainElement(screen.getByRole("button", { name: "Sign out" }));
  expect(screen.getByRole("heading", { name: "Markets", level: 1 })).toHaveClass("sr-only");
  await user.click(screen.getByRole("button", { name: "Crypto" }));
  expect(await screen.findByRole("button", { name: /Bitcoin BTC.*81,042.35/ })).toBeVisible();
  expect(screen.getByRole("link", { name: "Trade BTC" })).toHaveAttribute("href", "/trade/BTC");
  expect(screen.getAllByRole("link", { name: "Portfolios" })[0]).toHaveAttribute(
    "href",
    "/portfolios",
  );
});
it.each([
  ["/portfolios/1", "Portfolio page"],
  ["/portfolios/1/history", "History page"],
  ["/portfolios/1/trade/BTC", "Crypto BTC"],
  ["/portfolios/1/trade/stocks/AAPL", "Stock AAPL"],
])("hands explicit %s to financial children only after metadata", async (path, heading) => {
  let release!: (value: Response) => void;
  api({
    metadata: () =>
      new Promise((r) => {
        release = r;
      }),
  });
  setup(path);
  expect(await screen.findByRole("status", { name: "Loading portfolio" })).toBeVisible();
  expect(probes.mounted).not.toHaveBeenCalled();
  await waitFor(() => expect(release).toBeTypeOf("function"));
  expect(probes.mounted).not.toHaveBeenCalled();
  await act(async () => {
    release(json([first, second]));
  });
  expect(await screen.findByRole("heading", { name: heading })).toBeVisible();
  expect(probes.mounted).toHaveBeenCalledWith(
    path,
    expect.objectContaining({ owner: "alice@example.test", portfolioId: "1", name: first.name }),
  );
  expect(screen.getAllByRole("link", { name: "Portfolios" })[0]).toHaveAttribute(
    "href",
    "/portfolios",
  );
  expect(screen.getByRole("link", { name: "History" })).toHaveAttribute(
    "href",
    "/portfolios/1/history",
  );
});
it.each([
  ["/portfolio", "/portfolios/1", "Portfolio page"],
  ["/history", "/portfolios/1/history", "History page"],
  ["/trade/BTC", "/portfolios/1/trade/BTC", "Crypto BTC"],
  ["/trade/stocks/AAPL", "/portfolios/1/trade/stocks/AAPL", "Stock AAPL"],
])("replaces legacy %s before financial child mount", async (path, next, heading) => {
  api();
  setup(path);
  expect(await screen.findByRole("heading", { name: heading })).toBeVisible();
  expect(screen.getByTestId("location")).toHaveTextContent(next);
  expect(probes.mounted.mock.calls.every(([url]) => url === next)).toBe(true);
});
it.each([
  { values: [], heading: "No portfolio available" },
  { values: [first, second], heading: "Portfolio required" },
])("never selects or grants on legacy $heading", async ({ values, heading }) => {
  const fetch = api({ metadata: () => json(values) });
  setup("/trade/BTC");
  expect(await screen.findByRole("heading", { name: heading })).toBeVisible();
  expect(probes.mounted).not.toHaveBeenCalled();
  expect(screen.getByTestId("location")).toHaveTextContent("/trade/BTC");
  expect(
    fetch.mock.calls.every(([url]) => ["/api/v2/me", "/api/v2/portfolios"].includes(url)),
  ).toBe(true);
  if (values.length === 0) expect(screen.queryByRole("combobox")).toBeNull();
  else expect(screen.getByRole("combobox", { name: "Trading portfolio" })).toBeVisible();
});
it("continues to the original asset only after an explicit portfolio choice", async () => {
  api({ metadata: () => json([first, second]) });
  const { user } = setup("/trade/BTC");
  const chooser = await screen.findByRole("combobox", { name: "Trading portfolio" });
  expect(probes.mounted).not.toHaveBeenCalled();
  expect(chooser).toHaveValue("");
  await user.selectOptions(chooser, second.id);
  expect(await screen.findByRole("heading", { name: "Crypto BTC" })).toBeVisible();
  expect(screen.getByTestId("location")).toHaveTextContent("/portfolios/2/trade/BTC");
});
it.each(["/portfolios/01", "/portfolios/0", "/portfolios/nope/history"])(
  "refuses missing/malformed %s without metadata or finance",
  async (path) => {
    const fetch = api();
    setup(path);
    expect(await screen.findByRole("heading", { name: "Portfolio required" })).toBeVisible();
    expect(probes.mounted).not.toHaveBeenCalled();
    expect(fetch.mock.calls.map(([url]) => url)).toEqual(["/api/v2/me"]);
  },
);
it("never substitutes a sole other strategy for an explicit unavailable root", async () => {
  api({ metadata: () => json([second]) });
  setup("/portfolios/1/history");
  expect(await screen.findByRole("heading", { name: "Portfolio unavailable" })).toBeVisible();
  expect(probes.mounted).not.toHaveBeenCalled();
  expect(screen.getByTestId("location")).toHaveTextContent("/portfolios/1/history");
  expect(screen.getAllByRole("link", { name: "Portfolios" })[0]).toHaveAttribute(
    "href",
    "/portfolios",
  );
});
it("retains verified root through nav, global Markets and trade links", async () => {
  api({ metadata: () => json([first, second]) });
  const { user } = setup("/portfolios/2/history");
  await screen.findByRole("heading", { name: "History page" });
  await user.click(screen.getByRole("link", { name: "Markets" }));
  expect(await screen.findByRole("heading", { name: "Markets" })).toBeVisible();
  await user.click(screen.getByRole("button", { name: "Crypto" }));
  expect(await screen.findByRole("link", { name: "Trade BTC" })).toHaveAttribute(
    "href",
    "/portfolios/2/trade/BTC",
  );
  expect(screen.getAllByRole("link", { name: "Portfolios" })[0]).toHaveAttribute(
    "href",
    "/portfolios",
  );
  await user.click(screen.getByRole("link", { name: "Trade BTC" }));
  expect(await screen.findByRole("heading", { name: "Crypto BTC" })).toBeVisible();
  expect(screen.getByText("Private alice@example.test root 2")).toBeVisible();
});
it("changes the trading portfolio in place and carries the selected instrument", async () => {
  api({ metadata: () => json([first, second]) });
  const { user } = setup();
  const chooser = await screen.findByRole("combobox", { name: "Trading portfolio" });
  await screen.findByRole("option", { name: second.name });
  expect(screen.getAllByRole("combobox")).toHaveLength(1);
  expect(chooser).toHaveAccessibleDescription("Select the portfolio for the next trade.");
  expect(chooser).toHaveValue("");
  await user.click(screen.getByRole("button", { name: "Crypto" }));
  const search = screen.getByRole("searchbox");
  await user.type(search, "bitc");
  await user.click(await screen.findByRole("button", { name: /Bitcoin BTC/ }));
  expect(screen.getByRole("link", { name: "Trade BTC" })).toHaveAttribute("href", "/trade/BTC");

  await user.selectOptions(chooser, first.id);
  await waitFor(() =>
    expect(screen.getByRole("link", { name: "Trade BTC" })).toHaveAttribute(
      "href",
      "/portfolios/1/trade/BTC",
    ),
  );
  await user.selectOptions(chooser, second.id);
  await waitFor(() =>
    expect(screen.getByRole("link", { name: "Trade BTC" })).toHaveAttribute(
      "href",
      "/portfolios/2/trade/BTC",
    ),
  );
  expect(search).toHaveValue("bitc");
  expect(screen.getByRole("button", { name: "Crypto" })).toHaveAttribute("aria-pressed", "true");
  expect(screen.getByTestId("location")).toHaveTextContent(/^\/$/);
  await user.click(screen.getByRole("link", { name: "Trade BTC" }));
  expect(await screen.findByText("Private alice@example.test root 2")).toBeVisible();
});

it("keeps quotes visible when a chosen trading portfolio awaits access or becomes unavailable", async () => {
  let completeRefresh!: (value: Response) => void;
  let metadata = () => Promise.resolve(json([first, second]));
  api({ metadata: () => metadata() });
  const { client, user } = setup();
  const chooser = await screen.findByRole("combobox", { name: "Trading portfolio" });
  await screen.findByRole("option", { name: first.name });
  await user.selectOptions(chooser, first.id);
  await user.click(screen.getByRole("button", { name: "Crypto" }));
  expect(await screen.findByRole("link", { name: "Trade BTC" })).toHaveAttribute(
    "href",
    "/portfolios/1/trade/BTC",
  );

  metadata = () =>
    new Promise<Response>((resolve) => {
      completeRefresh = resolve;
    });
  await act(async () => {
    void client.invalidateQueries({ queryKey: ["portfolios", "alice@example.test"] });
  });
  expect(await screen.findByText("Checking your trading portfolio…")).toBeVisible();
  expect(screen.queryByRole("link", { name: "Trade BTC" })).toBeNull();
  expect(screen.getByRole("heading", { name: "Bitcoin" })).toBeVisible();
  await act(async () => completeRefresh(json([second])));

  const choose = await screen.findByRole("link", { name: "Choose an available portfolio" });
  expect(choose).toHaveAttribute("href", "/portfolios");
  expect(chooser).toHaveValue("");
  expect(screen.queryByRole("link", { name: "Trade BTC" })).toBeNull();

  await user.selectOptions(chooser, second.id);
  expect(await screen.findByRole("link", { name: "Trade BTC" })).toHaveAttribute(
    "href",
    "/portfolios/2/trade/BTC",
  );
});

it("focuses route and Back headings without refetch focus theft", async () => {
  api();
  const { client, user } = setup();
  expect(await screen.findByRole("heading", { name: "Markets", level: 1 })).toHaveFocus();
  await user.click(
    within(screen.getByRole("navigation", { name: "Main" })).getByRole("link", {
      name: "Portfolios",
    }),
  );
  expect(await screen.findByRole("heading", { name: "Portfolios", level: 1 })).toHaveFocus();
  const logout = screen.getByRole("button", { name: "Sign out" });
  logout.focus();
  await act(async () => {
    await client.invalidateQueries({ queryKey: ["me"] });
  });
  expect(logout).toHaveFocus();
  await user.click(screen.getByRole("button", { name: "Back" }));
  expect(await screen.findByRole("heading", { name: "Markets", level: 1 })).toHaveFocus();
});
it("keeps system status available with zero roots and no financial discovery", async () => {
  const fetch = api({ metadata: () => json([]) });
  setup("/health");
  expect(await screen.findByRole("heading", { name: "System status", level: 1 })).toBeVisible();
  expect(screen.getByRole("button", { name: "Sign out" })).toBeEnabled();
  expect(screen.queryByText("Cash")).toBeNull();
  expect(screen.queryByText(/\$10,000/)).toBeNull();
  expect(fetch.mock.calls.some(([url]) => url === "/api/v2/portfolios")).toBe(false);
});
it("masks prior finance and nav memory on account switch", async () => {
  let email = "alice@example.test";
  let values = [first];
  api({ identity: () => json({ email }), metadata: () => json(values) });
  const { client, user } = setup("/portfolios/1");
  await screen.findByText("Private alice@example.test root 1");
  await user.click(screen.getByRole("link", { name: "Markets" }));
  await screen.findByRole("heading", { name: "Markets" });
  email = "bob@example.test";
  values = [];
  await act(async () => {
    await client.invalidateQueries({ queryKey: ["me"] });
  });
  await waitFor(() =>
    expect(screen.getAllByRole("link", { name: "Portfolios" })[0]).toHaveAttribute(
      "href",
      "/portfolios",
    ),
  );
  expect(screen.queryByText(/Private alice/)).toBeNull();
  await user.click(screen.getAllByRole("link", { name: "Portfolios" })[0]!);
  expect(await screen.findByRole("heading", { name: "No portfolios yet" })).toBeVisible();
  expect(screen.queryByRole("button", { name: "Financial action" })).toBeNull();
});
it("removes finance on metadata revocation without redirecting", async () => {
  let values = [first];
  api({ metadata: () => json(values) });
  const { client } = setup("/portfolios/1");
  await screen.findByText("Private alice@example.test root 1");
  values = [second];
  await act(async () => {
    await client.invalidateQueries({ queryKey: ["portfolios", "alice@example.test"] });
  });
  expect(await screen.findByRole("heading", { name: "Portfolio unavailable" })).toBeVisible();
  expect(screen.queryByText(/Private alice/)).toBeNull();
  expect(screen.getByTestId("location")).toHaveTextContent("/portfolios/1");
});
it("shows account skeleton while identity is pending", () => {
  api({ identity: () => new Promise<Response>(() => {}) });
  setup();
  expect(screen.getByRole("status", { name: "Loading your account" })).toHaveAttribute(
    "aria-busy",
    "true",
  );
  expect(screen.queryByRole("navigation")).toBeNull();
});
it.each(["/health", "/portfolio", "/portfolios/1/history", "/trade/BTC"])(
  "keeps signed-out %s behind OTP",
  async (path) => {
    api({ identity: unauthorized });
    setup(path);
    expect(await screen.findByRole("button", { name: "Send code" })).toBeVisible();
    expect(screen.queryByRole("navigation", { name: "Main" })).toBeNull();
    expect(probes.mounted).not.toHaveBeenCalled();
  },
);
it("uses existing sign-in flow after metadata401", async () => {
  api({ metadata: unauthorized });
  setup("/portfolios/1");
  expect(await screen.findByRole("button", { name: "Send code" })).toBeVisible();
  expect(probes.mounted).not.toHaveBeenCalled();
});
it("retries identity failure without synthetic financial fields", async () => {
  let count = 0;
  api({ identity: () => (++count === 1 ? json({}, 500) : json({ email: "alice@example.test" })) });
  const { user } = setup();
  expect(await screen.findByRole("alert")).toHaveTextContent("Can't reach Birja right now.");
  await user.click(screen.getByRole("button", { name: "Try again" }));
  expect(await screen.findByRole("heading", { name: "Markets" })).toBeVisible();
});
it.each(["/unknown", "/account"])("redirects %s to Markets", async (path) => {
  api();
  setup(path);
  expect(await screen.findByRole("heading", { name: "Markets" })).toBeVisible();
});
it("preserves logout CSRF and refuses late identity/root resurrection", async () => {
  document.cookie = "bj_csrf=synthetic; path=/";
  let defer = false;
  let release!: (r: Response) => void;
  let signal!: AbortSignal;
  const base = api();
  const fetch = vi.fn((url: string, init?: RequestInit) => {
    if (url === "/api/v2/me" && defer) {
      signal = init!.signal as AbortSignal;
      return new Promise<Response>((r) => {
        release = r;
      });
    }
    if (url === "/api/v1/auth/logout") return Promise.resolve(new Response(null, { status: 204 }));
    return base(url);
  });
  vi.stubGlobal("fetch", fetch);
  const { client, user } = setup("/portfolios/1/history");
  await screen.findByRole("heading", { name: "History page" });
  const query = client.getQueryCache().find({ queryKey: ["me"] });
  defer = true;
  let pending!: Promise<void>;
  act(() => {
    pending = client.invalidateQueries({ queryKey: ["me"] });
  });
  await waitFor(() => expect(release).toBeTypeOf("function"));
  await user.click(screen.getByRole("button", { name: "Sign out" }));
  expect(await screen.findByRole("button", { name: "Send code" })).toBeVisible();
  expect(signal.aborted).toBe(true);
  expect(client.getQueryCache().find({ queryKey: ["me"] })).toBe(query);
  const call = fetch.mock.calls.find(([url]) => url === "/api/v1/auth/logout")!;
  expect(new Headers(call[1]!.headers).get("X-CSRF-Token")).toBe("synthetic");
  await act(async () => {
    release(json({ email: "alice@example.test" }));
    await pending;
  });
  expect(client.getQueryData(["me"])).toBeNull();
  expect(screen.queryByRole("navigation")).toBeNull();
});
it("keeps the current page and sign-out control usable on failure", async () => {
  document.cookie = "bj_csrf=synthetic; path=/";
  api();
  const { user } = setup("/portfolios/1/history");
  const logout = await screen.findByRole("button", { name: "Sign out" });
  await user.click(logout);
  expect(await screen.findByRole("alert")).toHaveTextContent("Couldn't sign out. Try again.");
  expect(screen.getByRole("heading", { name: "History page" })).toBeVisible();
  expect(logout).toHaveFocus();
  expect(logout).toHaveAttribute("aria-disabled", "false");
});

it.each([{ values: [] }, { values: [first] }, { values: [first, second] }])(
  "routes the real overview independently of target count $values.length",
  async ({ values }) => {
    const fetch = api({ metadata: () => json(values) });
    setup("/portfolios");
    expect(await screen.findByRole("heading", { name: "Portfolios", level: 1 })).toHaveFocus();
    expect(await screen.findByRole("heading", { name: "No portfolios yet" })).toBeVisible();
    expect(screen.getByRole("button", { name: "New portfolio" })).toBeEnabled();
    expect(probes.mounted).not.toHaveBeenCalled();
    expect(fetch.mock.calls.some(([url]) => url === "/api/v2/portfolios/overview")).toBe(true);
  },
);

it("opens the chosen portfolio, preserving the original trade route for Back", async () => {
  api({ metadata: () => json([first, second]) });
  const { user } = setup("/portfolios/1/trade/BTC");
  await screen.findByRole("heading", { name: "Crypto BTC" });
  const select = screen.getByRole("combobox", { name: "Open portfolio" });
  expect(screen.getByText("Private alice@example.test root 1")).toBeVisible();
  expect(probes.mounted.mock.calls.every(([, target]) => target.portfolioId === "1")).toBe(true);
  await user.selectOptions(select, "2");
  expect(await screen.findByRole("heading", { level: 1 })).toHaveFocus();
  expect(screen.getByTestId("location")).toHaveTextContent(/^\/portfolios\/2$/);
  expect(screen.getByText("Private alice@example.test root 2")).toBeVisible();
  await user.click(screen.getByRole("button", { name: "Back" }));
  expect(await screen.findByRole("heading", { name: "Crypto BTC" })).toHaveFocus();
  expect(screen.getByText("Private alice@example.test root 1")).toBeVisible();
});

it("navigates a current real creation receipt to its original ID and focuses detail once", async () => {
  document.cookie = "bj_csrf=synthetic; path=/";
  let values: { id: string; name: string }[] = [];
  const base = api({ metadata: () => json(values) });
  const fetch = vi.fn((url: string, init?: RequestInit) => {
    if (url === "/api/v2/portfolios" && init?.method === "POST") {
      values = [{ id: "19", name: "Created strategy" }];
      return Promise.resolve(json({ id: "19", name: "Created strategy", description: "" }, 201));
    }
    return base(url);
  });
  vi.stubGlobal("fetch", fetch);
  const { user, client } = setup("/portfolios");
  await screen.findByRole("heading", { name: "No portfolios yet" });
  await user.click(screen.getByRole("button", { name: "New portfolio" }));
  const name = screen.getByRole("textbox", { name: "Portfolio name" });
  expect(name).toHaveFocus();
  await user.type(name, "Created strategy");
  await user.click(screen.getByRole("button", { name: "Create portfolio" }));
  const heading = await screen.findByRole("heading", { name: "Created strategy", level: 1 });
  expect(heading).toHaveFocus();
  expect(screen.getByTestId("location")).toHaveTextContent(/^\/portfolios\/19$/);
  const action = screen.getByRole("button", { name: "Financial action" });
  action.focus();
  await act(async () => {
    await client.invalidateQueries({ queryKey: ["portfolios"] });
  });
  // Revalidation may replace financial children; route focus must not rerun.
  expect(
    await screen.findByRole("heading", { name: "Created strategy", level: 1 }),
  ).not.toHaveFocus();
  expect(fetch.mock.calls.filter(([, init]) => init?.method === "POST")).toHaveLength(1);
});

it.each(["route", "owner"])(
  "ignores a late real creation receipt after %s departure",
  async (departure) => {
    document.cookie = "bj_csrf=synthetic; path=/";
    let release!: (response: Response) => void;
    const base = api({ metadata: () => json([first, second]) });
    const fetch = vi.fn((url: string, init?: RequestInit) =>
      url === "/api/v2/portfolios" && init?.method === "POST"
        ? new Promise<Response>((resolve) => {
            release = resolve;
          })
        : base(url),
    );
    vi.stubGlobal("fetch", fetch);
    const { user, client } = setup("/portfolios");
    await screen.findByRole("heading", { name: "No portfolios yet" });
    await user.click(screen.getByRole("button", { name: "New portfolio" }));
    await user.type(
      screen.getByRole("textbox", { name: "Portfolio name" }),
      "Private old creation",
    );
    await user.click(screen.getByRole("button", { name: "Create portfolio" }));
    await waitFor(() => expect(release).toBeTypeOf("function"));
    if (departure === "route") await user.click(screen.getByRole("link", { name: "Markets" }));
    else act(() => client.setQueryData(["me"], { email: "bob@example.test" }));
    await act(async () => {
      release(json({ id: "99", name: "Private old creation", description: "" }, 201));
    });
    await waitFor(() =>
      expect(screen.getByTestId("location")).not.toHaveTextContent("/portfolios/99"),
    );
    expect(screen.queryByText("Private old creation")).toBeNull();
    expect(probes.mounted).not.toHaveBeenCalled();
    expect(fetch.mock.calls.filter(([, init]) => init?.method === "POST")).toHaveLength(1);
  },
);
