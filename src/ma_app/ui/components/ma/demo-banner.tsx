import { FlaskConical } from "lucide-react";

/** Persistent banner: this app uses synthetic data and mock activation only. */
export function DemoBanner() {
  return (
    <div className="flex items-center justify-center gap-2 bg-amber-500/15 text-amber-800 dark:text-amber-300 border-b border-amber-500/30 px-4 py-1.5 text-xs font-medium">
      <FlaskConical className="h-3.5 w-3.5" />
      Synthetic data / mock activation only — no real messages are sent.
    </div>
  );
}
