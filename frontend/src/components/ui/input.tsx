import * as React from "react";
import { cn } from "cn";

function Input({ className, type, ...props }: React.ComponentProps<"input">) {
  return (
    <input
      type={type}
      data-slot="input"
      className={cn(
        "h-12 w-full min-w-0 rounded-control border border-input bg-popover px-4 text-base text-foreground transition-colors outline-none placeholder:text-muted-foreground disabled:cursor-not-allowed disabled:opacity-40 aria-invalid:border-loss-text",
        className,
      )}
      {...props}
    />
  );
}

export { Input };
