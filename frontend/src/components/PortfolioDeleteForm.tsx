import { useId, useLayoutEffect, useRef } from "react";
import { Link, useLocation, useNavigate } from "react-router";
import { AlertCircle } from "lucide-react";
import { Button } from "@/components/ui/button";
import type { PortfolioMetadata } from "@/api/portfolioManagement";
import { usePortfolioDeletion } from "@/hooks/usePortfolioDeletion";

const action =
  "min-h-11 min-w-11 h-auto py-3 text-base whitespace-normal focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 motion-reduce:transform-none motion-reduce:transition-none";

/** The containing metadata host must survive automatic financial quarantine. */
export function PortfolioDeleteForm({
  portfolioId,
  metadata,
  metadataBusy,
  available = true,
  lastPortfolio = false,
  refreshMetadata,
}: {
  portfolioId?: string;
  metadata?: PortfolioMetadata;
  metadataBusy: boolean;
  available?: boolean;
  lastPortfolio?: boolean;
  refreshMetadata: () => unknown;
}) {
  const navigate = useNavigate();
  const { pathname } = useLocation();
  const controller = usePortfolioDeletion(portfolioId, {
    route: pathname,
    onClosed: (receipt) => {
      if (receipt.isCurrent()) void navigate("/portfolios", { state: { deletionConfirmed: true } });
    },
  });
  const { deletion, ready, canConfirm, canCheck } = controller;
  const id = useId();
  const trigger = useRef<HTMLButtonElement>(null);
  const cancel = useRef<HTMLButtonElement>(null);
  const error = useRef<HTMLDivElement>(null);
  const restore = useRef(false);
  const previousPhase = useRef(deletion.phase);
  const userAction = useRef(false);
  const review = deletion.phase === "review" && deletion.review?.portfolioId === portfolioId;
  const original = deletion.attempt;
  const ownOriginal =
    original !== null && (portfolioId === undefined || original.portfolioId === portfolioId);
  const busy = ["persisting", "submitting", "checking"].includes(deletion.phase);
  useLayoutEffect(() => {
    if (review && previousPhase.current !== "review") cancel.current?.focus();
    if (!review && restore.current) {
      restore.current = false;
      trigger.current?.focus();
    }
    if (deletion.error && userAction.current && !busy) {
      userAction.current = false;
      error.current?.focus();
    }
    previousPhase.current = deletion.phase;
  }, [review, deletion.phase, deletion.error, busy]);
  function cancelReview() {
    if (!review || busy) return;
    restore.current = true;
    controller.cancelReview();
  }
  if (!available && !ownOriginal) return null;
  if (ownOriginal || (busy && review)) {
    const name = original?.confirmationName ?? deletion.review?.confirmationName;
    return (
      <section
        aria-labelledby={`${id}-heading`}
        className="flex max-w-[640px] min-w-0 flex-col gap-4 rounded-card bg-card p-4 text-base leading-6 wrap-anywhere md:p-6"
      >
        <div role="status" aria-live="polite" aria-busy={busy}>
          <h2 id={`${id}-heading`} className="text-xl leading-7 font-medium">
            {busy
              ? deletion.phase === "checking"
                ? "Checking deletion result…"
                : "Deleting portfolio…"
              : "Deletion result unconfirmed"}
          </h2>
          <p>
            {busy ? (
              <>
                Checking the deletion of “{name}”. This portfolio is unavailable for new actions
                while the result is being confirmed.
              </>
            ) : (
              <>
                We couldn&apos;t confirm whether “{name}” was deleted. Check this original deletion
                request before using this portfolio again.
              </>
            )}
          </p>
        </div>
        <p>You can leave this page. Leaving does not cancel the deletion request.</p>
        {deletion.retryAt !== null && !canCheck && !busy && (
          <p className="text-sm">
            Try again after the displayed wait:{" "}
            <time dateTime={new Date(deletion.retryAt).toISOString()}>
              {new Date(deletion.retryAt).toLocaleTimeString()}
            </time>
            .
          </p>
        )}
        <div className="flex flex-col gap-2 min-[375px]:flex-row min-[375px]:flex-wrap">
          <Button
            type="button"
            className={action}
            disabled={!canCheck || busy}
            onClick={() => {
              userAction.current = true;
              void controller.checkDeletionResult();
            }}
          >
            Check deletion result
          </Button>
          <Link className={`${action} flex items-center underline`} to="/portfolios">
            Portfolios
          </Link>
        </div>
      </section>
    );
  }
  const errorText =
    deletion.reviewRequired || deletion.phase === "terminal_refusal"
      ? "This portfolio's name changed. Review its latest name before confirming deletion again."
      : !ready && deletion.error
        ? "Can't preserve this deletion request for recovery. No deletion was sent. Keep this page open and try again."
        : deletion.error
          ? "This portfolio couldn't be safely deleted. Try again later. If this continues, contact the operator."
          : null;
  const another = original !== null;
  return (
    <section
      aria-labelledby={`${id}-heading`}
      className="mt-6 flex max-w-[640px] min-w-0 flex-col gap-4 border-t border-border pt-6 text-base leading-6 wrap-anywhere"
      onKeyDown={(event) => {
        if (event.key === "Escape" && review) {
          event.preventDefault();
          cancelReview();
        }
      }}
    >
      <h2 id={`${id}-heading`} className="text-xl leading-7 font-medium">
        {review ? `Delete “${deletion.review!.confirmationName}”?` : "Delete portfolio"}
      </h2>
      {errorText && (
        <div
          ref={error}
          role="alert"
          tabIndex={-1}
          className="flex min-w-0 items-start gap-2 rounded-control bg-loss-soft p-4 text-loss-text focus-visible:ring-2 focus-visible:ring-ring"
        >
          <AlertCircle aria-hidden="true" className="size-5 shrink-0" />
          <p>{errorText}</p>
        </div>
      )}
      {!ready && deletion.error && (
        <Button
          type="button"
          variant="secondary"
          className={action}
          onClick={() => {
            userAction.current = true;
            void controller.retryRecoveryStorage();
          }}
        >
          Retry deletion recovery
        </Button>
      )}
      {review ? (
        <>
          <p>
            This ends this strategy permanently. Its committed cash, investments and History will be
            frozen and unavailable in normal portfolio screens.
          </p>
          <p>
            Future dividends, splits and corrections—including unpaid dividends already earned—will
            not change this portfolio.
          </p>
          <p>
            Nothing will be sold or moved to another portfolio. Financial records are retained, and
            you cannot undo this in Birja.
          </p>
          {lastPortfolio && (
            <p>
              This is your last active portfolio. You&apos;ll stay signed in and can create a new
              portfolio when you&apos;re ready.
            </p>
          )}
          {deletion.reviewRequired && (
            <Button
              type="button"
              variant="secondary"
              className={action}
              onClick={() => {
                userAction.current = true;
                controller.cancelReview();
                void refreshMetadata();
              }}
            >
              Review latest portfolio
            </Button>
          )}
          <div className="flex flex-col gap-2 min-[375px]:flex-row min-[375px]:flex-wrap">
            <Button
              ref={cancel}
              type="button"
              variant="secondary"
              className={action}
              onClick={cancelReview}
            >
              Cancel
            </Button>
            <Button
              type="button"
              variant="destructive"
              className={action}
              disabled={!canConfirm || metadataBusy}
              onClick={() => {
                userAction.current = true;
                void controller.confirmDeletion();
              }}
            >
              Delete portfolio
            </Button>
          </div>
        </>
      ) : (
        <>
          <p>End this strategy and remove it from your active portfolios.</p>
          {metadataBusy && (
            <p id={`${id}-reason`}>Finish or discard your portfolio changes before deleting.</p>
          )}
          {another && (
            <p id={`${id}-original`}>
              Check your original deletion request before deleting another portfolio. Other active
              portfolios remain available.
            </p>
          )}
          {deletion.phase === "terminal_refusal" && (
            <Button
              type="button"
              variant="secondary"
              className={action}
              onClick={() => void refreshMetadata()}
            >
              Review latest portfolio
            </Button>
          )}
          <Button
            ref={trigger}
            type="button"
            variant="outline"
            className={`${action} self-start text-destructive`}
            aria-expanded={false}
            aria-controls={`${id}-heading`}
            aria-describedby={
              metadataBusy ? `${id}-reason` : another ? `${id}-original` : undefined
            }
            disabled={!ready || !metadata || metadataBusy || another}
            onClick={() => {
              if (metadata) controller.reviewDeletion(metadata);
            }}
          >
            Delete portfolio…
          </Button>
        </>
      )}
    </section>
  );
}
