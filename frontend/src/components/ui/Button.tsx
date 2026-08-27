import { cn } from "@/lib/utils";
import type { ButtonHTMLAttributes } from "react";

interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: "primary" | "secondary" | "ghost" | "danger";
  size?: "sm" | "md";
}

const VARIANTS: Record<string, string> = {
  primary: "bg-accent text-[#04141d] hover:bg-accent/90 border-transparent font-semibold",
  secondary: "bg-surface-raised text-foreground hover:bg-border border-border-strong",
  ghost: "bg-transparent text-muted hover:text-foreground hover:bg-surface-raised border-transparent",
  danger: "bg-status-critical/15 text-status-critical hover:bg-status-critical/25 border-status-critical/30",
};

export function Button({ variant = "secondary", size = "md", className, ...props }: ButtonProps) {
  return (
    <button
      className={cn(
        "inline-flex items-center justify-center gap-1.5 rounded-md border transition-colors disabled:cursor-not-allowed disabled:opacity-50",
        size === "sm" ? "px-2.5 py-1 text-xs" : "px-3.5 py-2 text-sm",
        VARIANTS[variant],
        className
      )}
      {...props}
    />
  );
}
