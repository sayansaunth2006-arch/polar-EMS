"use client";

import { useToastStore } from "@/lib/toast";
import { cn } from "@/lib/utils";
import { CheckCircle2, XCircle, Info } from "lucide-react";

const ICON = { success: CheckCircle2, error: XCircle, info: Info };
const COLOR = {
  success: "border-status-normal/30 text-status-normal",
  error: "border-status-critical/30 text-status-critical",
  info: "border-status-info/30 text-status-info",
};

export function Toaster() {
  const toasts = useToastStore((s) => s.toasts);
  return (
    <div className="pointer-events-none fixed bottom-4 right-4 z-50 flex flex-col gap-2">
      {toasts.map((t) => {
        const Icon = ICON[t.variant];
        return (
          <div
            key={t.id}
            className={cn(
              "pointer-events-auto flex items-center gap-2 rounded-md border bg-surface-raised px-3 py-2 text-sm shadow-lg",
              COLOR[t.variant]
            )}
          >
            <Icon className="h-4 w-4 shrink-0" />
            <span className="text-foreground">{t.message}</span>
          </div>
        );
      })}
    </div>
  );
}
