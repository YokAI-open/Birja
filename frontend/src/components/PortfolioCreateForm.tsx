import { useEffect, useLayoutEffect, useRef, useState, useSyncExternalStore } from "react";
import { useQueryClient } from "@tanstack/react-query";
import { AlertCircle } from "lucide-react";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { usePortfolioManagement } from "@/hooks/usePortfolioManagement";
import {
  normalizePortfolioDescription,
  portfolioNameDisplay,
  PortfolioManagementError,
  type PortfolioMetadata,
} from "@/api/portfolioManagement";
import { useNow } from "@/hooks/useNow";
import { eventHistorySession } from "@/hooks/useEventHistory";

function metadataErrors(name: string, description: string) {
  const controls = [...name].some((c) => {
    const point = c.codePointAt(0)!;
    return point < 32 || (point >= 127 && point <= 159) || (point >= 0xd800 && point <= 0xdfff);
  });
  return {
    name:
      portfolioNameDisplay(name) === null
        ? controls
          ? "Remove control characters from the name."
          : name === ""
            ? "Enter a portfolio name."
            : "Use 1–60 characters."
        : null,
    description:
      normalizePortfolioDescription(description) === null
        ? [...description.replace(/\r\n?/g, "\n")].length > 1000
          ? "Use 1,000 characters or fewer."
          : "Remove unsupported control characters from the description."
        : null,
  };
}
function managementMessage(error: Error | null) {
  if (!error) return null;
  if (!(error instanceof PortfolioManagementError))
    return "Creation recovery storage or the result is unavailable. Keep your draft and check the original request before trying again.";
  switch (error.code) {
    case "name_taken":
      return "You already have an active portfolio with this name. Choose another name.";
    case "portfolio_limit":
      return "You have 10 active portfolios. You can't create another right now.";
    case "creation_key_conflict":
      return "This creation attempt has different details. Retry the original creation; no new portfolio has been requested.";
    case "portfolio_unavailable":
      return "The original portfolio is unavailable. This creation cannot create it again.";
    case "rate_limited":
    case "creation_quota":
      return "Too many attempts. Try again after the displayed wait.";
    default:
      return error.outcome === "unknown"
        ? "We couldn't confirm whether your portfolio was created. Retry this creation to check its original result."
        : "Couldn't create this portfolio. Review the message below and try again.";
  }
}
export function MetadataFields({
  prefix,
  name,
  description,
  onChange,
  readOnly = false,
  nameIssue,
}: {
  prefix: string;
  name: string;
  description: string;
  onChange: (field: "name" | "description", value: string) => void;
  readOnly?: boolean;
  nameIssue?: string;
}) {
  const errors = metadataErrors(name, description);
  return (
    <div className="flex min-w-0 flex-col gap-4">
      <div className="flex min-w-0 flex-col gap-1">
        <label className="text-sm" htmlFor={`${prefix}-name`}>
          Portfolio name
        </label>
        <Input
          autoFocus
          id={`${prefix}-name`}
          className="min-h-12 w-full text-base"
          value={name}
          readOnly={readOnly}
          onChange={(e) => onChange("name", e.target.value)}
          aria-invalid={!!errors.name || !!nameIssue}
          aria-describedby={`${prefix}-name-help ${prefix}-name-error`}
        />
        <p id={`${prefix}-name-help`} className="text-sm text-muted-foreground">
          1–60 characters. Names must be unique among your active portfolios, ignoring case.
        </p>
        <p id={`${prefix}-name-error`} className="text-sm text-loss-text">
          {nameIssue ?? errors.name}
        </p>
      </div>
      <div className="flex min-w-0 flex-col gap-1">
        <label className="text-sm" htmlFor={`${prefix}-description`}>
          Description (optional)
        </label>
        <textarea
          id={`${prefix}-description`}
          className="min-h-24 w-full rounded-control border border-input bg-popover p-3 text-base leading-6 wrap-anywhere focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2"
          value={description}
          readOnly={readOnly}
          onChange={(e) => onChange("description", e.target.value)}
          aria-invalid={!!errors.description}
          aria-describedby={`${prefix}-description-help ${prefix}-description-count ${prefix}-description-error`}
        />
        <p id={`${prefix}-description-help`} className="text-sm text-muted-foreground">
          Plain text. Up to 1,000 characters.
        </p>
        <p id={`${prefix}-description-count`} className="text-sm tabular-nums">
          {[...description.replace(/\r\n?/g, "\n")].length} / 1,000 characters
        </p>
        <p id={`${prefix}-description-error`} className="text-sm text-loss-text">
          {errors.description}
        </p>
      </div>
    </div>
  );
}
export function FormError({
  message,
  prefix,
  nameError,
  descriptionError,
}: {
  message: string;
  prefix: string;
  nameError?: boolean;
  descriptionError?: boolean;
}) {
  const ref = useRef<HTMLDivElement>(null);
  useEffect(() => {
    ref.current?.focus();
  }, [message]);
  return (
    <div
      ref={ref}
      tabIndex={-1}
      role="alert"
      className="rounded-control bg-loss-soft p-4 text-loss-text outline-offset-2"
    >
      <p className="flex items-start gap-2">
        <AlertCircle size={16} aria-hidden="true" />
        <span>{message}</span>
      </p>
      {nameError && (
        <a
          className="flex min-h-11 items-center underline"
          href={`#${prefix}-name`}
          onClick={(e) => {
            e.preventDefault();
            document.getElementById(`${prefix}-name`)?.focus();
          }}
        >
          Review portfolio name
        </a>
      )}
      {descriptionError && (
        <a
          className="flex min-h-11 items-center underline"
          href={`#${prefix}-description`}
          onClick={(e) => {
            e.preventDefault();
            document.getElementById(`${prefix}-description`)?.focus();
          }}
        >
          Review description
        </a>
      )}
    </div>
  );
}

type CreateProps = {
  count: number | undefined;
  onClose: () => void;
  onCreated: (metadata: PortfolioMetadata, replay: boolean) => void;
};
export function PortfolioCreateForm(props: CreateProps) {
  const client = useQueryClient();
  const identity = useSyncExternalStore(
    (notify) => client.getQueryCache().subscribe(notify),
    () => {
      const session = eventHistorySession(client);
      return `${session.email}:${session.epoch}`;
    },
  );
  return <CreationEditor key={identity} {...props} />;
}
function CreationEditor({ count, onClose, onCreated }: CreateProps) {
  const management = usePortfolioManagement();
  const { creation } = management;
  const [name, setName] = useState(creation.attempt?.name ?? "");
  const [description, setDescription] = useState(creation.attempt?.description ?? "");
  const [attemptKey, setAttemptKey] = useState(creation.attempt?.key);
  if (creation.attempt && creation.attempt.key !== attemptKey) {
    setAttemptKey(creation.attempt.key);
    setName(creation.attempt.name);
    setDescription(creation.attempt.description ?? "");
  }
  const [attempted, setAttempted] = useState(false);
  const frozen = creation.phase === "unknown" || creation.phase === "submitting";
  const displayedName = creation.attempt?.name ?? name;
  const displayedDescription = creation.attempt?.description ?? description;
  const errors = metadataErrors(displayedName, displayedDescription);
  // A receipt predating this editor is already resolved; opening a fresh
  // intent must not navigate back to an earlier creation.
  const handled = useRef<object | null>(creation.receipt ?? null);
  const replay = useRef(creation.phase === "unknown");
  useLayoutEffect(() => {
    const receipt = creation.receipt;
    if (receipt && handled.current !== receipt && receipt.isCurrent()) {
      handled.current = receipt;
      onCreated(receipt.metadata, replay.current);
    }
  }, [creation.receipt, onCreated]);
  const now = useNow();
  // A discarded, definitively refused name belongs to the previous editor.
  // Keep the shared attempt untouched: unknown/pending recovery, resource
  // limits and timing refusals must still govern the original operation.
  const refusal =
    !attempted &&
    attemptKey === undefined &&
    creation.phase === "editing" &&
    creation.attempt === null &&
    creation.error instanceof PortfolioManagementError &&
    creation.error.outcome === "refused" &&
    creation.error.code === "name_taken"
      ? null
      : creation.error;
  const [timing, setTiming] = useState<{ error: Error | null; until: number }>({
    error: null,
    until: 0,
  });
  if (timing.error !== refusal)
    setTiming({
      error: refusal,
      until:
        now + ((refusal instanceof PortfolioManagementError ? refusal.retryAfter : 0) ?? 0) * 1000,
    });
  const waiting = now < timing.until;
  const message =
    managementMessage(refusal) ??
    (attempted && (errors.name || errors.description)
      ? "Review the highlighted fields before creating your portfolio."
      : null);
  const capped =
    count === undefined ||
    count >= 10 ||
    (refusal instanceof PortfolioManagementError && refusal.code === "portfolio_limit");
  return (
    <Card className="min-w-0 p-4 md:p-6">
      <CardContent className="min-w-0">
        <form
          className="flex max-w-[640px] min-w-0 flex-col gap-4 text-base leading-6"
          onSubmit={(e) => {
            e.preventDefault();
            setAttempted(true);
            if (
              !frozen &&
              !capped &&
              !errors.name &&
              !errors.description &&
              management.ready &&
              !waiting
            )
              void management.submitCreation({ name, description });
          }}
        >
          <h2 className="text-xl leading-7 font-medium">Create portfolio</h2>
          <p>
            Each new portfolio starts with $10,000.00 in virtual cash. Its cash and investments stay
            separate.
          </p>
          {message && (
            <FormError
              message={message}
              prefix="create"
              nameError={
                !!errors.name ||
                (refusal instanceof PortfolioManagementError && refusal.code === "name_taken")
              }
              descriptionError={!!errors.description}
            />
          )}
          {creation.phase === "unknown" && (
            <p role="status">
              We couldn&apos;t confirm whether your portfolio was created. Retry this creation to
              check its original result.
            </p>
          )}
          {creation.phase === "submitting" && <p role="status">Creating portfolio…</p>}
          <MetadataFields
            prefix="create"
            name={displayedName}
            description={displayedDescription}
            readOnly={frozen}
            nameIssue={
              refusal instanceof PortfolioManagementError && refusal.code === "name_taken"
                ? "You already have an active portfolio with this name. Choose another name."
                : undefined
            }
            onChange={(field, value) => (field === "name" ? setName(value) : setDescription(value))}
          />
          {capped && !frozen && (
            <p>
              {count === undefined
                ? "Wait for your portfolios to load before creating a new portfolio."
                : "You have 10 active portfolios. You can't create another right now."}
            </p>
          )}
          {waiting && (
            <p role="status">Try again in {Math.ceil((timing.until - now) / 1000)} seconds.</p>
          )}
          <div className="flex flex-col gap-2 min-[375px]:flex-row min-[375px]:flex-wrap">
            {creation.phase === "unknown" ? (
              <Button
                type="button"
                className="min-h-11 text-base motion-reduce:transform-none motion-reduce:transition-none"
                disabled={!management.ready || waiting}
                onClick={() => {
                  replay.current = true;
                  void management.retryCreation();
                }}
              >
                Retry creation
              </Button>
            ) : (
              <Button
                type="submit"
                className="min-h-11 text-base motion-reduce:transform-none motion-reduce:transition-none"
                disabled={
                  frozen ||
                  capped ||
                  !management.ready ||
                  !!errors.name ||
                  !!errors.description ||
                  waiting
                }
              >
                {creation.phase === "submitting" ? "Creating portfolio…" : "Create portfolio"}
              </Button>
            )}
            <Button
              type="button"
              className="min-h-11 text-base motion-reduce:transform-none motion-reduce:transition-none"
              variant="secondary"
              onClick={onClose}
            >
              {frozen ? "Close creation" : "Discard draft"}
            </Button>
          </div>
        </form>
      </CardContent>
    </Card>
  );
}
