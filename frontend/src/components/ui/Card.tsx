import { cn } from "@/lib/utils";
import type { ReactNode } from "react";

export function Card({ children, className }: { children: ReactNode; className?: string }) {
  return (
    <div className={cn("rounded-lg border border-border bg-surface", className)}>
      {children}
    </div>
  );
}

export function CardHeader({ children, className }: { children: ReactNode; className?: string }) {
  return <div className={cn("flex items-center justify-between gap-2 border-b border-border px-4 py-3", className)}>{children}</div>;
}

export function CardTitle({ children, className }: { children: ReactNode; className?: string }) {
  return <h3 className={cn("text-sm font-semibold tracking-wide text-foreground", className)}>{children}</h3>;
}

export function CardBody({ children, className }: { children: ReactNode; className?: string }) {
  return <div className={cn("p-4", className)}>{children}</div>;
}
