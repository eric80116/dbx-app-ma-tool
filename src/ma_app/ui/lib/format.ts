// Shared display helpers. Timestamps from the API are UTC (SQL "YYYY-MM-DD HH:MM:SS").

export function fmtDateTime(ts?: string | null): string {
  if (!ts) return "—";
  // Treat naive SQL timestamps as UTC and render in the viewer's local time.
  const iso = ts.includes("T") ? ts : ts.replace(" ", "T") + "Z";
  const d = new Date(iso);
  if (isNaN(d.getTime())) return ts;
  return d.toLocaleString(undefined, {
    year: "numeric",
    month: "short",
    day: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });
}

export function fmtDate(ts?: string | null): string {
  if (!ts) return "—";
  const iso = ts.includes("T") ? ts : ts.replace(" ", "T") + "Z";
  const d = new Date(iso);
  if (isNaN(d.getTime())) return ts;
  return d.toLocaleDateString(undefined, {
    year: "numeric",
    month: "short",
    day: "numeric",
  });
}

export function fmtNumber(n?: number | null): string {
  if (n == null) return "—";
  return n.toLocaleString();
}

export function fmtPct(rate?: number | null): string {
  if (rate == null) return "—";
  return `${(rate * 100).toFixed(1)}%`;
}

export const CHANNEL_LABEL: Record<string, string> = {
  APP_PUSH: "App Push",
  SMS: "SMS",
  COUPON: "Coupon",
};

export function channelLabel(ch?: string | null): string {
  if (!ch) return "—";
  return CHANNEL_LABEL[ch] ?? ch;
}

// Badge classes per campaign status (works in light + dark).
export const STATUS_STYLES: Record<string, string> = {
  DRAFT: "bg-muted text-muted-foreground",
  PENDING_APPROVAL:
    "bg-amber-100 text-amber-800 dark:bg-amber-950 dark:text-amber-300",
  APPROVED: "bg-blue-100 text-blue-800 dark:bg-blue-950 dark:text-blue-300",
  SCHEDULED:
    "bg-violet-100 text-violet-800 dark:bg-violet-950 dark:text-violet-300",
  RUNNING: "bg-sky-100 text-sky-800 dark:bg-sky-950 dark:text-sky-300",
  COMPLETED:
    "bg-emerald-100 text-emerald-800 dark:bg-emerald-950 dark:text-emerald-300",
  FAILED: "bg-red-100 text-red-800 dark:bg-red-950 dark:text-red-300",
  CANCELLED: "bg-zinc-200 text-zinc-700 dark:bg-zinc-800 dark:text-zinc-300",
};

export function statusLabel(status?: string | null): string {
  if (!status) return "—";
  return status.replace(/_/g, " ");
}
