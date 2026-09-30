import { createFileRoute, Link } from "@tanstack/react-router";
import { Suspense } from "react";
import { QueryErrorResetBoundary } from "@tanstack/react-query";
import { ErrorBoundary } from "react-error-boundary";
import { useGetDashboardSuspense } from "@/lib/api";
import selector from "@/lib/selector";
import { StatCard } from "@/components/ma/stat-card";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import {
  Users,
  Megaphone,
  FileEdit,
  Clock,
  CalendarClock,
  Send,
  MailCheck,
  MousePointerClick,
  Eye,
  Ticket,
  AlertCircle,
} from "lucide-react";
import { fmtNumber, fmtPct, fmtDateTime } from "@/lib/format";

export const Route = createFileRoute("/_sidebar/dashboard")({
  component: () => <Dashboard />,
});

function DashboardContent() {
  const { data } = useGetDashboardSuspense(selector());
  return (
    <div className="space-y-6">
      <div className="grid gap-3 grid-cols-2 md:grid-cols-3 lg:grid-cols-4">
        <StatCard label="Audiences" value={fmtNumber(data.total_audiences)} icon={<Users className="h-4 w-4" />} />
        <StatCard label="Campaigns" value={fmtNumber(data.total_campaigns)} icon={<Megaphone className="h-4 w-4" />} />
        <StatCard label="Drafts" value={fmtNumber(data.draft_campaigns)} icon={<FileEdit className="h-4 w-4" />} />
        <StatCard label="Pending approvals" value={fmtNumber(data.pending_approvals)} icon={<Clock className="h-4 w-4" />} />
        <StatCard label="Scheduled" value={fmtNumber(data.scheduled_campaigns)} icon={<CalendarClock className="h-4 w-4" />} />
        <StatCard label="Completed dispatches" value={fmtNumber(data.completed_dispatches)} icon={<Send className="h-4 w-4" />} />
        <StatCard label="Total delivered" value={fmtNumber(data.total_delivered)} icon={<MailCheck className="h-4 w-4" />} />
        <StatCard label="Open rate" value={fmtPct(data.open_rate)} icon={<Eye className="h-4 w-4" />} />
        <StatCard label="Click rate" value={fmtPct(data.click_rate)} icon={<MousePointerClick className="h-4 w-4" />} />
        <StatCard label="Redemption rate" value={fmtPct(data.redemption_rate)} icon={<Ticket className="h-4 w-4" />} />
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Recent activity</CardTitle>
          <CardDescription>Latest audit events across campaigns.</CardDescription>
        </CardHeader>
        <CardContent>
          {(data.recent_activity ?? []).length === 0 ? (
            <p className="text-sm text-muted-foreground">No activity yet.</p>
          ) : (
            <div className="divide-y">
              {(data.recent_activity ?? []).map((a) => (
                <div key={a.audit_id} className="flex items-center justify-between py-2 text-sm">
                  <div className="flex items-center gap-3">
                    <span className="font-mono text-xs rounded bg-muted px-2 py-0.5">{a.action}</span>
                    <span className="text-muted-foreground">
                      {a.resource_type} <span className="font-medium text-foreground">{a.resource_id}</span>
                    </span>
                  </div>
                  <div className="flex items-center gap-4 text-muted-foreground">
                    <span>{a.actor}</span>
                    <span className="tabular-nums">{fmtDateTime(a.created_at)}</span>
                  </div>
                </div>
              ))}
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}

function Dashboard() {
  return (
    <>
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold">Dashboard</h1>
          <p className="text-sm text-muted-foreground">
            Campaign activation overview. All metrics computed from Delta tables.
          </p>
        </div>
        <Button asChild>
          <Link to="/campaigns/new">New campaign</Link>
        </Button>
      </div>
      <QueryErrorResetBoundary>
        {({ reset }) => (
          <ErrorBoundary
            onReset={reset}
            fallbackRender={({ resetErrorBoundary }) => (
              <Card className="border-destructive/50">
                <CardHeader>
                  <CardTitle className="flex items-center gap-2 text-destructive">
                    <AlertCircle className="h-5 w-5" /> Failed to load dashboard
                  </CardTitle>
                  <CardDescription>
                    Check that the warehouse is running and the setup job has seeded data.
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  <Button variant="outline" onClick={resetErrorBoundary}>Try again</Button>
                </CardContent>
              </Card>
            )}
          >
            <Suspense
              fallback={
                <div className="grid gap-3 grid-cols-2 md:grid-cols-4">
                  {Array.from({ length: 8 }).map((_, i) => (
                    <Skeleton key={i} className="h-24 w-full" />
                  ))}
                </div>
              }
            >
              <DashboardContent />
            </Suspense>
          </ErrorBoundary>
        )}
      </QueryErrorResetBoundary>
    </>
  );
}
