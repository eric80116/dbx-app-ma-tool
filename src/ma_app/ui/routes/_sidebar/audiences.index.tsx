import { createFileRoute, Link } from "@tanstack/react-router";
import { useListAudiencesSuspense } from "@/lib/api";
import selector from "@/lib/selector";
import { AsyncBoundary } from "@/components/ma/async-boundary";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import { fmtNumber, fmtDateTime } from "@/lib/format";
import { Users, ArrowRight, Database } from "lucide-react";

export const Route = createFileRoute("/_sidebar/audiences/")({
  component: () => <Audiences />,
});

function AudiencesList() {
  const { data } = useListAudiencesSuspense(selector());
  return (
    <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
      {data.map((a) => (
        <Link key={a.audience_id} to="/audiences/$id" params={{ id: a.audience_id }}>
          <Card className="h-full transition-colors hover:border-primary/40">
            <CardHeader>
              <div className="flex items-center justify-between">
                <CardTitle className="flex items-center gap-2">
                  <Users className="h-4 w-4" /> {a.audience_name}
                </CardTitle>
                <Badge variant="secondary" className="text-xs">{a.source_type}</Badge>
              </div>
              <CardDescription>{a.description}</CardDescription>
            </CardHeader>
            <CardContent className="space-y-2 text-sm">
              <div className="flex items-center justify-between">
                <span className="text-muted-foreground">Members</span>
                <span className="font-semibold tabular-nums">{fmtNumber(a.member_count)}</span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-muted-foreground">Version</span>
                <span className="font-mono text-xs">{a.audience_version}</span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-muted-foreground">Refreshed</span>
                <span className="text-xs">{fmtDateTime(a.last_refreshed_at)}</span>
              </div>
              <div className="flex items-center gap-1 pt-1 text-xs text-muted-foreground">
                <Database className="h-3 w-3" />
                <span className="truncate font-mono">{a.source_table}</span>
              </div>
              <div className="flex items-center gap-1 pt-2 text-sm font-medium text-primary">
                View audience <ArrowRight className="h-3.5 w-3.5" />
              </div>
            </CardContent>
          </Card>
        </Link>
      ))}
    </div>
  );
}

function Audiences() {
  return (
    <>
      <div>
        <h1 className="text-2xl font-bold">Audiences</h1>
        <p className="text-sm text-muted-foreground">
          Audiences produced upstream by CustomerLake Campaign Agents. This demo consumes a
          local synthetic snapshot — the App never recreates the segmentation logic.
        </p>
      </div>
      <AsyncBoundary
        fallback={
          <div className="grid gap-4 md:grid-cols-3">
            {Array.from({ length: 3 }).map((_, i) => (
              <Skeleton key={i} className="h-56 w-full" />
            ))}
          </div>
        }
      >
        <AudiencesList />
      </AsyncBoundary>
    </>
  );
}
