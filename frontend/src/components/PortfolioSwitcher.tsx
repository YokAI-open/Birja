import { useId } from "react";
import { useNavigate } from "react-router";
import { cn } from "@/lib/utils";
import { usePortfolioTarget } from "@/hooks/usePortfolioTarget";

type SwitcherProps = {
  portfolioId?: string;
  destination?: (id: string) => string;
  onSelect?: (id: string) => void;
  prominent?: boolean;
  inline?: boolean;
  label?: string;
};

export function PortfolioSwitcher({
  portfolioId,
  destination,
  onSelect,
  prominent = false,
  inline = false,
  label = destination || onSelect ? "Trading portfolio" : "Open portfolio",
}: SwitcherProps) {
  const id = useId();
  const navigate = useNavigate();
  const result = usePortfolioTarget(undefined, { legacyEntry: true });
  if (result.status === "signed_out") return null;

  const ready = result.status === "redirect" || result.status === "ambiguous";
  const rows = ready ? (result.portfolios ?? []) : [];
  const current = rows.find((row) => row.id === portfolioId);
  const placeholder =
    result.status === "loading"
      ? "Loading portfolios…"
      : result.status === "error"
        ? "Couldn’t load portfolios"
        : rows.length
          ? "Choose a portfolio"
          : "No portfolios available";

  return (
    <section
      aria-label="Portfolio navigation"
      className={cn("w-full min-w-0", !inline && "my-4", prominent ? "md:max-w-md" : "md:max-w-xs")}
    >
      <label htmlFor={id} className="sr-only">
        {label}
      </label>
      <span id={id + "-action"} className="sr-only">
        {onSelect ? "Select the portfolio for the next trade." : "Selecting a portfolio opens it."}
      </span>
      <select
        id={id}
        aria-describedby={id + "-action"}
        value={current?.id ?? ""}
        disabled={rows.length === 0}
        className={cn(
          "h-13 w-full min-w-0 rounded-control border border-input bg-background px-3",
          prominent ? "text-sm font-semibold tracking-tight sm:text-xl md:text-2xl" : "text-base",
        )}
        onChange={(event) => {
          const selected = rows.find((row) => row.id === event.target.value);
          if (!selected || selected.id === portfolioId) return;
          if (onSelect) {
            onSelect(selected.id);
          } else {
            // The destination route verifies access before it mounts financial content.
            void navigate(destination ? destination(selected.id) : `/portfolios/${selected.id}`);
          }
        }}
      >
        <option value="" disabled>
          {placeholder}
        </option>
        {rows.map((row) => (
          <option key={row.id} value={row.id}>
            {row.name}
          </option>
        ))}
      </select>
    </section>
  );
}
