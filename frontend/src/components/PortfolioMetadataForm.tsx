import { useLayoutEffect, useRef, useState } from "react";
import { Link } from "react-router";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { FormError, MetadataFields } from "@/components/PortfolioCreateForm";
import { usePortfolioManagement } from "@/hooks/usePortfolioManagement";
import {
  normalizePortfolioDescription,
  portfolioNameDisplay,
  PortfolioManagementError,
} from "@/api/portfolioManagement";
import { useNow } from "@/hooks/useNow";

export function PortfolioMetadataForm({ portfolioId }: { portfolioId: string }) {
  const management = usePortfolioManagement(portfolioId);
  const [editing, setEditing] = useState(false);
  const [announcement, setAnnouncement] = useState("");
  const trigger = useRef<HTMLButtonElement>(null);
  const [restore, setRestore] = useState(false);
  const saving = useRef(false);
  const { metadata, draft, metadataError, metadataPending, reviewRequired } = management;
  const now = useNow();
  const [timing, setTiming] = useState<{ error: Error | null; until: number }>({
    error: null,
    until: 0,
  });
  if (timing.error !== metadataError)
    setTiming({
      error: metadataError,
      until:
        now +
        ((metadataError instanceof PortfolioManagementError ? metadataError.retryAfter : 0) ?? 0) *
          1000,
    });
  const waiting = now < timing.until;
  const expanded = editing || draft !== null;
  useLayoutEffect(() => {
    if (!expanded && restore) {
      trigger.current?.focus();
    }
  }, [expanded, restore]);
  const name = draft?.name ?? metadata?.name ?? "";
  const description = draft?.description ?? metadata?.description ?? "";
  const valid =
    portfolioNameDisplay(name) !== null && normalizePortfolioDescription(description) !== null;
  const errorMessage = metadataError
    ? metadataError instanceof PortfolioManagementError && metadataError.code === "name_taken"
      ? "You already have an active portfolio with this name. Choose another name."
      : reviewRequired
        ? "We couldn't confirm the save. Review the latest portfolio details before saving again."
        : "Couldn't save portfolio metadata. Your changes are kept here. Try again later."
    : null;
  async function save() {
    if (!valid || !draft || metadataPending || reviewRequired || waiting || saving.current) return;
    saving.current = true;
    await management.saveMetadata();
    saving.current = false;
    // The hook alone decides whether a save committed. Do not infer success
    // from the promise resolving: refused and ambiguous saves also resolve.
  }
  const [submitted, setSubmitted] = useState(false);
  if (submitted && !metadataPending && !draft && !metadataError && metadata) {
    setSubmitted(false);
    setEditing(false);
    setAnnouncement("Portfolio updated.");
    setRestore(true);
  }
  return (
    <Card className="min-w-0 p-4 md:p-6">
      <CardContent className="min-w-0 text-base leading-6 wrap-anywhere">
        <Link to="/portfolios" className="flex min-h-11 items-center underline">
          Back to Portfolios
        </Link>
        <p role={announcement ? "status" : undefined} aria-live="polite">
          {announcement}
        </p>
        {!metadata ? (
          <div>
            {metadataError ? (
              <>
                <p role="alert">Can&apos;t load portfolio metadata right now. Try again.</p>
                <Button
                  className="mt-2 min-h-11 text-base"
                  variant="secondary"
                  onClick={() => void management.refreshMetadata()}
                  disabled={metadataPending}
                >
                  Try again
                </Button>
              </>
            ) : (
              <p role="status">Loading portfolio details…</p>
            )}
          </div>
        ) : expanded ? (
          <form
            className="flex max-w-[640px] min-w-0 flex-col gap-4"
            onSubmit={(event) => {
              event.preventDefault();
              if (valid && draft && !metadataPending && !reviewRequired && !waiting) {
                setSubmitted(true);
                void save();
              }
            }}
          >
            <h2 className="text-xl leading-7 font-medium">Edit portfolio</h2>
            <p>Changes to the name or description do not change cash, investments or History.</p>
            {errorMessage && (
              <FormError
                message={errorMessage}
                prefix="metadata"
                nameError={
                  portfolioNameDisplay(name) === null ||
                  (metadataError instanceof PortfolioManagementError &&
                    metadataError.code === "name_taken")
                }
                descriptionError={normalizePortfolioDescription(description) === null}
              />
            )}
            {reviewRequired && (
              <div className="flex min-w-0 flex-col gap-2 rounded-control bg-warn-soft p-4 text-warn-text">
                <p role="status">
                  This portfolio changed. Your draft is kept below. Review the latest details before
                  saving.
                </p>
                <p>Latest portfolio name: {metadata.name}</p>
                <p className="whitespace-pre-wrap">
                  Latest description: {metadata.description || "No description."}
                </p>
                <Button
                  className="min-h-11 h-auto py-3 text-base whitespace-normal"
                  variant="secondary"
                  disabled={metadataPending || (!!metadataError && !metadata)}
                  onClick={() => management.reviewMetadata()}
                >
                  I have reviewed the latest details
                </Button>
              </div>
            )}
            <MetadataFields
              prefix="metadata"
              name={name}
              description={description}
              readOnly={metadataPending}
              nameIssue={
                metadataError instanceof PortfolioManagementError &&
                metadataError.code === "name_taken"
                  ? "You already have an active portfolio with this name. Choose another name."
                  : undefined
              }
              onChange={(field, value) => management.editMetadata({ [field]: value })}
            />
            {waiting && (
              <p role="status">Try again in {Math.ceil((timing.until - now) / 1000)} seconds.</p>
            )}
            <div className="flex flex-col gap-2 min-[375px]:flex-row min-[375px]:flex-wrap">
              <Button
                type="submit"
                className="min-h-11 text-base"
                disabled={!valid || !draft || metadataPending || reviewRequired || waiting}
              >
                {metadataPending ? "Saving changes…" : "Save changes"}
              </Button>
              <Button
                type="button"
                className="min-h-11 text-base"
                variant="secondary"
                disabled={metadataPending}
                onClick={() => {
                  management.discardMetadata();
                  setRestore(true);
                  setEditing(false);
                  setSubmitted(false);
                }}
              >
                Discard changes
              </Button>
            </div>
          </form>
        ) : (
          <div className="flex min-w-0 flex-col gap-3">
            <h2 className="text-xl leading-7 font-medium">{metadata.name}</h2>
            <p className="whitespace-pre-wrap">{metadata.description || "No description."}</p>
            <Button
              ref={trigger}
              variant="secondary"
              className="min-h-11 self-start text-base"
              disabled={metadataPending}
              onClick={() => {
                setAnnouncement("");
                setRestore(false);
                setEditing(true);
              }}
            >
              Edit portfolio
            </Button>
          </div>
        )}
      </CardContent>
    </Card>
  );
}
