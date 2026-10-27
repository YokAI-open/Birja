import { useState, type FormEvent } from "react";
import { ApiError } from "@/api/client";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { useRequestCode, useVerifyCode } from "@/hooks/useAuthMutations";

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

const LABEL = "text-[13px] leading-[18px] font-medium text-muted-foreground";

function SignInPage() {
  const [email, setEmail] = useState("");
  const [code, setCode] = useState("");
  const [sentTo, setSentTo] = useState<string | null>(null);
  const requestCode = useRequestCode();
  const verifyCode = useVerifyCode();

  const onSendCode = (event: FormEvent) => {
    event.preventDefault();
    const trimmed = email.trim();
    if (!trimmed) return;
    requestCode.mutate(trimmed, {
      onSuccess: () => {
        setSentTo(trimmed);
        setCode("");
        verifyCode.reset();
      },
    });
  };

  const onResend = () => {
    if (sentTo === null) return;
    verifyCode.reset();
    requestCode.mutate(sentTo);
  };

  const onVerify = (event: FormEvent) => {
    event.preventDefault();
    if (sentTo === null || code.length !== 6) return;
    verifyCode.mutate({ email: sentTo, code });
  };

  const onChangeEmail = () => {
    setSentTo(null);
    setCode("");
    requestCode.reset();
    verifyCode.reset();
  };

  if (sentTo === null) {
    const error = requestCode.isError ? errorMessage(requestCode.error, "email") : null;
    const empty = email.trim() === "";
    const describedBy = error ? "email-error" : empty ? "email-help" : undefined;
    return (
      <Card className="mx-auto my-8 max-w-xl">
        <CardContent className="flex flex-col gap-4">
          <h2 className="text-xl leading-7 font-semibold tracking-[-0.01em]">Sign in</h2>
          <p className="text-muted-foreground">
            Enter your email and we will send you a one-time code. No password needed.
          </p>
          <form onSubmit={onSendCode} className="flex flex-col gap-3" noValidate>
            <label htmlFor="email" className={LABEL}>
              Email
            </label>
            <Input
              id="email"
              type="email"
              autoComplete="email"
              inputMode="email"
              value={email}
              onChange={(event) => setEmail(event.target.value)}
              aria-invalid={error ? true : undefined}
              aria-describedby={describedBy}
            />
            {error ? (
              <p id="email-error" role="alert" className="text-sm text-loss-text">
                {error}
              </p>
            ) : (
              empty && (
                <p id="email-help" className="text-xs leading-4 text-muted-foreground">
                  Enter your email to get a code.
                </p>
              )
            )}
            <Button type="submit" disabled={empty || requestCode.isPending}>
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
    <Card className="mx-auto my-8 max-w-xl">
      <CardContent className="flex flex-col gap-4">
        <h2 className="text-xl leading-7 font-semibold tracking-[-0.01em]">Enter your code</h2>
        <p className="text-muted-foreground">
          We sent a code to {sentTo}. It expires in 10 minutes.
        </p>
        <form onSubmit={onVerify} className="flex flex-col gap-3" noValidate>
          <label htmlFor="code" className={LABEL}>
            6-digit code
          </label>
          <Input
            id="code"
            type="text"
            autoComplete="one-time-code"
            inputMode="numeric"
            maxLength={6}
            className="tabular-nums"
            value={code}
            onChange={(event) => setCode(event.target.value.replace(/\D/g, ""))}
            aria-invalid={error ? true : undefined}
            aria-describedby={error ? "code-error" : undefined}
          />
          {error && (
            <p id="code-error" role="alert" className="text-sm text-loss-text">
              {error}
            </p>
          )}
          <Button type="submit" disabled={code.length !== 6 || verifyCode.isPending}>
            {verifyCode.isPending ? "Signing in…" : "Sign in"}
          </Button>
        </form>
        <div className="flex flex-wrap gap-2">
          <Button variant="ghost" size="sm" onClick={onResend} disabled={requestCode.isPending}>
            Send a new code
          </Button>
          <Button variant="ghost" size="sm" onClick={onChangeEmail}>
            Use a different email
          </Button>
        </div>
      </CardContent>
    </Card>
  );
}

export default SignInPage;
