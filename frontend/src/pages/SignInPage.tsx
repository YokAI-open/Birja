import { useRef, useState, type FormEvent, type MouseEvent, type Ref } from "react";
import { ApiError } from "@/api/client";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { useRequestCode, useVerifyCode } from "@/hooks/useAuthMutations";
import "./signInWorkspace.css";

const pendingButtonClass = "aria-disabled:cursor-not-allowed aria-disabled:opacity-40";

function waitText(seconds: number): string {
  if (seconds < 60) {
    return `${seconds} ${seconds === 1 ? "second" : "seconds"}`;
  }
  const minutes = Math.ceil(seconds / 60);
  return `${minutes} ${minutes === 1 ? "minute" : "minutes"}`;
}

/** Fixed client-side copy only: server text is never rendered. Generic, so no account is revealed. */
function errorMessage(error: unknown, step: "email" | "code"): string {
  if (!(error instanceof ApiError)) {
    return "Something went wrong. Try again.";
  }
  if (error.status === 400 && error.code === "invalid_code") {
    return "That code is wrong or has expired. Check it or send a new code.";
  }
  if (error.status === 422 && step === "email") {
    return "Enter a valid email address.";
  }
  if (error.status === 429) {
    return error.retryAfter === null
      ? "Too many attempts. Try again in a moment."
      : `Too many attempts. Try again in ${waitText(error.retryAfter)}.`;
  }
  if (error.status === 403) {
    return "Your session token is out of date. Reload the page and try again.";
  }
  if (error.status === 503) {
    return "Sign-in is temporarily unavailable. Try again in a moment.";
  }
  return "Something went wrong. Try again.";
}

function SignInPage({ inputRef }: { inputRef?: Ref<HTMLInputElement> }) {
  const [email, setEmail] = useState("");
  const [code, setCode] = useState("");
  const [sentTo, setSentTo] = useState<string | null>(null);
  const [focusEmailOnReturn, setFocusEmailOnReturn] = useState(false);
  const requestCode = useRequestCode();
  const verifyCode = useVerifyCode();
  const actionInFlight = useRef(false);
  const codeForm = useRef<HTMLFormElement>(null);
  const pending = requestCode.isPending || verifyCode.isPending;

  function startAction() {
    if (actionInFlight.current || pending) return false;
    actionInFlight.current = true;
    return true;
  }

  function finishAction() {
    actionInFlight.current = false;
  }

  const onSendCode = (event: FormEvent) => {
    event.preventDefault();
    const trimmed = email.trim();
    if (!trimmed || !startAction()) return;
    requestCode.mutate(trimmed, {
      onSuccess: () => {
        setSentTo(trimmed);
        setCode("");
        verifyCode.reset();
      },
      onSettled: finishAction,
    });
  };

  const onResend = (event: MouseEvent<HTMLButtonElement>) => {
    if (sentTo === null || !startAction()) return;
    const button = event.currentTarget;
    verifyCode.reset();
    requestCode.mutate(sentTo, {
      onSuccess: () => {
        setCode("");
        if (document.activeElement === button) {
          codeForm.current?.querySelector<HTMLInputElement>("input[name='code']")?.focus();
        }
      },
      onSettled: finishAction,
    });
  };

  const onVerify = (event: FormEvent) => {
    event.preventDefault();
    if (sentTo === null || code.length !== 6 || !startAction()) return;
    verifyCode.mutate({ email: sentTo, code }, { onSettled: finishAction });
  };

  const onChangeEmail = () => {
    if (actionInFlight.current || pending) return;
    setFocusEmailOnReturn(true);
    setSentTo(null);
    setCode("");
    requestCode.reset();
    verifyCode.reset();
  };

  if (sentTo === null) {
    const error = requestCode.isError ? errorMessage(requestCode.error, "email") : null;
    const empty = email.trim() === "";
    return (
      <Card className="sign-in-workspace">
        <CardContent>
          <h1 className="sign-in-title">Sign in</h1>
          <form key="email" onSubmit={onSendCode} className="sign-in-form" noValidate>
            <div className="sign-in-field">
              <label htmlFor="email">Email</label>
              <Input
                ref={inputRef}
                id="email"
                name="email"
                type="email"
                autoComplete="email"
                autoFocus={focusEmailOnReturn}
                inputMode="email"
                placeholder="you@example.com"
                value={email}
                onChange={(event) => setEmail(event.target.value)}
                aria-invalid={error ? true : undefined}
                aria-describedby={error ? "email-error" : undefined}
              />
            </div>
            {error && (
              <p id="email-error" role="alert" className="text-sm text-loss-text">
                {error}
              </p>
            )}
            <Button
              size="lg"
              type="submit"
              disabled={empty}
              aria-disabled={pending || undefined}
              className={pendingButtonClass}
            >
              {requestCode.isPending ? "Sending…" : "Send code"}
            </Button>
          </form>
        </CardContent>
      </Card>
    );
  }

  const error = verifyCode.isError
    ? errorMessage(verifyCode.error, "code")
    : requestCode.isError
      ? errorMessage(requestCode.error, "code")
      : null;
  return (
    <Card className="sign-in-workspace">
      <CardContent>
        <h1 className="sign-in-title">Enter your code</h1>
        <p id="code-delivery" className="wrap-anywhere text-muted-foreground">
          We sent a code to {sentTo}. It expires in 10 minutes.
        </p>
        <form ref={codeForm} key="code" onSubmit={onVerify} className="sign-in-form" noValidate>
          <div className="sign-in-field">
            <label htmlFor="code">6-digit code</label>
            <Input
              ref={inputRef}
              id="code"
              name="code"
              type="text"
              autoComplete="one-time-code"
              autoFocus
              inputMode="numeric"
              maxLength={6}
              className="tabular-nums"
              value={code}
              onChange={(event) => setCode(event.target.value.replace(/\D/g, ""))}
              aria-invalid={error ? true : undefined}
              aria-describedby={error ? "code-error" : "code-delivery"}
            />
          </div>
          {error && (
            <p id="code-error" role="alert" className="text-sm text-loss-text">
              {error}
            </p>
          )}
          <Button
            size="lg"
            type="submit"
            disabled={code.length !== 6}
            aria-disabled={pending || undefined}
            className={pendingButtonClass}
          >
            {verifyCode.isPending ? "Signing in…" : "Sign in"}
          </Button>
        </form>
        <div className="flex flex-wrap gap-2">
          <Button
            type="button"
            variant="ghost"
            size="sm"
            onClick={onResend}
            aria-disabled={pending || undefined}
            className={pendingButtonClass}
          >
            {requestCode.isPending ? "Sending…" : "Send a new code"}
          </Button>
          <Button
            type="button"
            variant="ghost"
            size="sm"
            onClick={onChangeEmail}
            aria-disabled={pending || undefined}
            className={pendingButtonClass}
          >
            Use a different email
          </Button>
        </div>
      </CardContent>
    </Card>
  );
}

export default SignInPage;
