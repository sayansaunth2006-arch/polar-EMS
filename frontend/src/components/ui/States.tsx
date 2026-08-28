import { AlertTriangle, Loader2, Inbox } from "lucide-react";

export function LoadingState({ label = "Loading data…" }: { label?: string }) {
  return (
    <div className="flex flex-col items-center justify-center gap-2 py-12 text-muted">
      <Loader2 className="h-5 w-5 animate-spin text-accent" />
      <p className="text-sm">{label}</p>
    </div>
  );
}

export function ErrorState({ message, onRetry }: { message: string; onRetry?: () => void }) {
  return (
    <div className="flex flex-col items-center justify-center gap-3 py-12 text-center">
      <AlertTriangle className="h-6 w-6 text-status-critical" />
      <p className="max-w-sm text-sm text-muted">{message}</p>
      {onRetry && (
        <button onClick={onRetry} className="rounded-md border border-border-strong bg-surface-raised px-3 py-1.5 text-xs text-foreground hover:bg-border">
          Retry
        </button>
      )}
    </div>
  );
}

export function EmptyState({ label = "Nothing to show yet." }: { label?: string }) {
  return (
    <div className="flex flex-col items-center justify-center gap-2 py-12 text-center text-muted">
      <Inbox className="h-6 w-6" />
      <p className="text-sm">{label}</p>
    </div>
  );
}
