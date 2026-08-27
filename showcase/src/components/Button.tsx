import Link from "next/link";
import type { ReactNode } from "react";
import { cn } from "@/lib/utils";

interface ButtonProps {
  href: string;
  children: ReactNode;
  variant?: "primary" | "secondary" | "ghost";
  size?: "md" | "lg";
  className?: string;
}

const VARIANTS: Record<string, string> = {
  primary: "bg-brand text-white hover:bg-brand-dim",
  secondary: "border border-border-strong bg-surface text-foreground hover:bg-surface-raised",
  ghost: "text-muted hover:text-foreground",
};

const SIZES: Record<string, string> = {
  md: "px-4 py-2 text-sm",
  lg: "px-6 py-3 text-base",
};

export function Button({ href, children, variant = "primary", size = "md", className }: ButtonProps) {
  return (
    <Link
      href={href}
      className={cn(
        "inline-flex cursor-pointer items-center justify-center gap-2 rounded-lg font-semibold transition-colors duration-200",
        VARIANTS[variant],
        SIZES[size],
        className
      )}
    >
      {children}
    </Link>
  );
}
