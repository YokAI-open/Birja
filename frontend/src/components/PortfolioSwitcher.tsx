import { useId, useState } from "react";
import { useQueryClient } from "@tanstack/react-query";
import { Link, useLocation, useNavigate } from "react-router";
import type { PortfolioSummary } from "@/api/portfolios";
import { Button } from "@/components/ui/button";
import { PortfolioContext } from "@/components/PortfolioContext";
import { useMe } from "@/hooks/useMe";
import { usePortfolioTarget } from "@/hooks/usePortfolioTarget";
import { eventHistorySession } from "@/hooks/useEventHistory";

/** Selection is local navigation intent, never financial authority. */
export function PortfolioSwitcher({ portfolioId }: { portfolioId?: string }) {
  const identity = useMe();
  const client = useQueryClient();
  const session = eventHistorySession(client);
  const { pathname } = useLocation();
  if (!identity.data || identity.isError) return null;
  return (
    <Choices
      key={`${identity.data.email}:${session.epoch}:${pathname}:${portfolioId ?? ""}`}
      owner={identity.data.email}
      portfolioId={portfolioId}
    />
  );
}

function Choices({ owner, portfolioId }: { owner: string; portfolioId?: string }) {
  const [draft, setDraft] = useState(portfolioId ?? "");
  const id = useId();
  const navigate = useNavigate();
  const result = usePortfolioTarget(draft || undefined, { legacyEntry: true });
  const client = useQueryClient();
  // The target hook owns fetching, parsing, subscription and revocation.
  // Reading its accepted list here adds no query or independent authority.
  const metadata = client.getQueryData<readonly PortfolioSummary[]>(["portfolios", owner]);
  const known = !["loading", "error", "signed_out"].includes(result.status);
  const rows = known ? metadata : undefined;
  const current = rows?.find((row) => row.id === portfolioId);
  const target = result.status === "ready" ? result.target : null;
  function open() {
    if (target?.isCurrent()) void navigate(`/portfolios/${target.portfolioId}`);
  }
  return (
    <section
      aria-label="Portfolio navigation"
      className="my-4 flex min-w-0 flex-col gap-4 text-base leading-6 [overflow-wrap:anywhere]"
    >
      {current && <PortfolioContext name={current.name} />}
      <div className="flex min-w-0 flex-wrap items-end gap-2">
        <div className="flex min-w-0 max-w-full flex-1 flex-col gap-1">
          <label htmlFor={id} className="text-sm leading-5">
            Open portfolio
          </label>
          <select
            id={id}
            value={rows?.some((row) => row.id === draft) ? draft : ""}
            onChange={(event) => setDraft(event.target.value)}
            disabled={!known}
            className="h-12 min-w-0 w-full rounded-control border border-input bg-background px-3 text-base focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2"
          >
            <option value="">Choose a portfolio to continue.</option>
            {rows?.map((row) => (
              <option key={row.id} value={row.id}>
                {row.name} · #{row.id}
              </option>
            ))}
          </select>
        </div>
        <Button
          variant="secondary"
          className="min-h-11 whitespace-normal text-base"
          disabled={!target}
          onClick={open}
        >
          Open selected portfolio
        </Button>
        <Link
          className="inline-flex min-h-11 items-center underline focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2"
          to="/portfolios"
        >
          Portfolios
        </Link>
      </div>
      {!known ? (
        <p role={result.status === "error" ? "alert" : "status"}>
          {result.status === "error"
            ? "Can't load your portfolios right now. Try again."
            : "Loading portfolios…"}
        </p>
      ) : rows?.length === 0 ? (
        <p>No portfolios yet. Create a portfolio from Portfolios.</p>
      ) : (
        !target && <p>Choose a portfolio to continue.</p>
      )}
      {result.status === "error" && (
        <Button
          variant="secondary"
          className="self-start"
          onClick={() => void result.refetch().catch(() => {})}
        >
          Retry portfolio choices
        </Button>
      )}
    </section>
  );
}
