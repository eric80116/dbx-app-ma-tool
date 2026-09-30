import { cn } from "@/lib/utils";
import { STATUS_STYLES, statusLabel } from "@/lib/format";

export function StatusBadge({ status }: { status?: string | null }) {
  const cls = (status && STATUS_STYLES[status]) || "bg-muted text-muted-foreground";
  return (
    <span
      className={cn(
        "inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium",
        cls,
      )}
    >
      {statusLabel(status)}
    </span>
  );
}
