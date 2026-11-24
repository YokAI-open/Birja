import { useOutletContext, useParams } from "react-router";
import { ApiError } from "@/api/client";
import { isCatalogId } from "@/api/stockCatalog";
import { MarketOpening } from "@/components/MarketOpening";
import { StockDate } from "@/components/StockTradeReceipt";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { useNow } from "@/hooks/useNow";
import { usePortfolio } from "@/hooks/usePortfolio";
import type { PortfolioTarget } from "@/hooks/usePortfolioTarget";
import { catalogDisplay, useCatalogTradeContext } from "@/hooks/useStockCatalog";
import { formatUnitPrice, formatUsd } from "@/lib/money";

function CatalogTicket({ target, catalogId }: { target: PortfolioTarget; catalogId: string }) {
  const context = useCatalogTradeContext(target, catalogId);
  const portfolio = usePortfolio(target);
  const now = useNow(1000);
  if (!target.isCurrent()) return null;
  if (context.isPending)
    return (
      <div className="app-page">
        <p role="status">Loading stock…</p>
      </div>
    );

  if (context.isError || !context.data) {
    const error = context.error;
    const unavailable = error instanceof ApiError && error.status === 404;
    return (
      <div className="app-page flex flex-col items-start gap-4">
        <h1 className="app-heading">
          {error instanceof ApiError && error.code === "portfolio_unavailable"
            ? "Portfolio unavailable"
            : "Stock unavailable"}
        </h1>
        {!unavailable && (
          <Button variant="secondary" onClick={() => void context.refetch()}>
            Try again
          </Button>
        )}
      </div>
    );
  }

  const { listing, session } = context.data;
  const { quote, closed, message } = catalogDisplay(context.data, now);
  const restriction =
    listing.state === "retired"
      ? "This listing is no longer active."
      : listing.state === "review"
        ? "This listing needs review."
        : "Orders aren't available for this stock yet.";

  return (
    <div className="app-page flex flex-col gap-7 md:gap-9">
      <header className="min-w-0">
        <h1 className="app-heading wrap-anywhere">{listing.company_name}</h1>
        <p className="mt-2 wrap-anywhere text-muted-foreground">
          {listing.ticker} · {listing.listing_exchange}
          {listing.share_class && ` · Class ${listing.share_class}`}
        </p>
      </header>
      <Card className="min-w-0 max-w-2xl">
        <CardContent className="flex flex-col gap-4">
          {quote && (
            <div>
              <p className="text-3xl font-semibold wrap-anywhere tabular-nums">
                {formatUnitPrice(quote.mid)}
              </p>
              {!closed && (
                <p className="text-sm text-muted-foreground">
                  IEX price · <StockDate value={quote.event_at} />
                </p>
              )}
            </div>
          )}
          {closed ? (
            <p>
              Market closed. <MarketOpening nextOpen={session.next_open_at} now={now} />
            </p>
          ) : (
            listing.state === "active" && message && <p role="status">{message}</p>
          )}
          {portfolio.data && (
            <p className="text-sm text-muted-foreground">
              Cash available {formatUsd(portfolio.data.cash)}
            </p>
          )}
          {(!closed || listing.state !== "active") && <p>{restriction}</p>}
        </CardContent>
      </Card>
    </div>
  );
}

export default function StockCatalogTradePage() {
  const { catalogId } = useParams();
  const target = useOutletContext<PortfolioTarget | null>();
  if (!isCatalogId(catalogId))
    return (
      <div className="app-page">
        <h1 className="app-heading">Unknown stock</h1>
      </div>
    );
  if (!target) return null;
  return <CatalogTicket target={target} catalogId={catalogId} />;
}
