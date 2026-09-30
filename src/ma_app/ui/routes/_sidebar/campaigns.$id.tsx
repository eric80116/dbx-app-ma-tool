import { createFileRoute, Link } from "@tanstack/react-router";
import { useState } from "react";
import { toast } from "sonner";
import { useQueryClient } from "@tanstack/react-query";
import {
  useGetCampaignSuspense,
  useGetCampaignMetricsSuspense,
  useGetCampaignApprovalsSuspense,
  useGetCampaignAuditSuspense,
  useGetCampaignDispatchRunsSuspense,
  useGetCampaignEventsSuspense,
  usePreviewCampaign,
  useSubmitCampaign,
  useApproveCampaign,
  useRejectCampaign,
  useCancelCampaign,
  useDispatchCampaign,
  useScheduleCampaign,
  useGetSystemConfigSuspense,
  type EligibilityPreview,
} from "@/lib/api";
import selector from "@/lib/selector";
import { AsyncBoundary } from "@/components/ma/async-boundary";
import { StatusBadge } from "@/components/ma/status-badge";
import { StatCard } from "@/components/ma/stat-card";
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { Skeleton } from "@/components/ui/skeleton";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { ArrowLeft, CalendarClock, Download, Eye, Send } from "lucide-react";
import { channelLabel, fmtDateTime, fmtNumber, fmtPct } from "@/lib/format";

// datetime-local ("YYYY-MM-DDTHH:MM", local tz) -> UTC SQL "YYYY-MM-DD HH:MM:SS".
function localToUtcSql(v: string): string {
  const d = new Date(v);
  return d.toISOString().slice(0, 19).replace("T", " ");
}

export const Route = createFileRoute("/_sidebar/campaigns/$id")({
  component: () => <CampaignDetailPage />,
});

function Actions({ id, status }: { id: string; status: string }) {
  const qc = useQueryClient();
  const { data: config } = useGetSystemConfigSuspense(selector());
  const [preview, setPreview] = useState<EligibilityPreview | null>(null);
  const [rejectOpen, setRejectOpen] = useState(false);
  const [comment, setComment] = useState("");
  const [scheduleOpen, setScheduleOpen] = useState(false);
  const [schedAt, setSchedAt] = useState("");

  const invalidate = () => qc.invalidateQueries();
  const onErr = (e: unknown) => toast.error((e as Error).message);

  const scheduleMut = useScheduleCampaign({ mutation: { onSuccess: () => { toast.success("Scheduled — a one-time job will dispatch at the set time"); invalidate(); setScheduleOpen(false); }, onError: onErr } });
  const previewMut = usePreviewCampaign();
  const submitMut = useSubmitCampaign({ mutation: { onSuccess: () => { toast.success("Submitted"); invalidate(); }, onError: onErr } });
  const approveMut = useApproveCampaign({ mutation: { onSuccess: () => { toast.success("Approved"); invalidate(); }, onError: onErr } });
  const rejectMut = useRejectCampaign({ mutation: { onSuccess: () => { toast.success("Rejected — back to draft"); invalidate(); setRejectOpen(false); }, onError: onErr } });
  const cancelMut = useCancelCampaign({ mutation: { onSuccess: () => { toast.success("Cancelled"); invalidate(); }, onError: onErr } });
  const dispatchMut = useDispatchCampaign({ mutation: { onSuccess: (r) => { toast.success(`Dispatched: ${r.data.success_count} sent, ${r.data.failure_count} failed`); invalidate(); }, onError: onErr } });

  async function doPreview() {
    try {
      const r = await previewMut.mutateAsync({ params: { campaign_id: id } });
      setPreview(r.data);
    } catch (e) { onErr(e); }
  }

  const canSubmit = status === "DRAFT";
  const canApproveReject = status === "PENDING_APPROVAL";
  const canSchedule = status === "APPROVED" && config.scheduler_enabled;
  const canDispatch = status === "APPROVED" || status === "SCHEDULED";
  const canCancel = ["DRAFT", "PENDING_APPROVAL", "APPROVED", "SCHEDULED"].includes(status);
  const canPreview = canCancel;

  return (
    <div className="space-y-3">
      <div className="flex flex-wrap gap-2">
        {canPreview && (
          <Button variant="outline" size="sm" onClick={doPreview} disabled={previewMut.isPending}>
            <Eye className="mr-1 h-4 w-4" /> Preview eligibility
          </Button>
        )}
        {canSubmit && (
          <Button size="sm" onClick={() => submitMut.mutate({ params: { campaign_id: id } })} disabled={submitMut.isPending}>
            Submit for approval
          </Button>
        )}
        {canApproveReject && (
          <>
            <Button size="sm" onClick={() => approveMut.mutate({ params: { campaign_id: id }, data: { comment: null } })} disabled={approveMut.isPending}>
              Approve
            </Button>
            <Button variant="destructive" size="sm" onClick={() => setRejectOpen(true)}>
              Reject
            </Button>
          </>
        )}
        {canSchedule && (
          <Button variant="outline" size="sm" onClick={() => setScheduleOpen(true)}>
            <CalendarClock className="mr-1 h-4 w-4" /> Schedule
          </Button>
        )}
        {canDispatch && (
          <Button size="sm" onClick={() => dispatchMut.mutate({ params: { campaign_id: id } })} disabled={dispatchMut.isPending}>
            <Send className="mr-1 h-4 w-4" /> {dispatchMut.isPending ? "Dispatching…" : "Dispatch now (mock)"}
          </Button>
        )}
        {canCancel && (
          <Button variant="ghost" size="sm" onClick={() => cancelMut.mutate({ params: { campaign_id: id }, data: { comment: null } })} disabled={cancelMut.isPending}>
            Cancel
          </Button>
        )}
      </div>

      {preview && (
        <Card className="border-primary/20">
          <CardContent className="grid grid-cols-2 gap-x-6 gap-y-1 p-4 text-sm sm:grid-cols-3">
            <PreviewRow label="Audience size" v={preview.audience_size} strong />
            <PreviewRow label="Eligible" v={preview.eligible} ok strong />
            <PreviewRow label="Already dispatched" v={preview.already_dispatched} />
            <PreviewRow label="Skipped — no consent" v={preview.skipped_no_consent} />
            <PreviewRow label="Skipped — inactive" v={preview.skipped_inactive} />
            <PreviewRow label="Skipped — invalid contact" v={preview.skipped_invalid_contact} />
          </CardContent>
        </Card>
      )}

      <Dialog open={scheduleOpen} onOpenChange={setScheduleOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Schedule dispatch</DialogTitle>
            <DialogDescription>
              A one-time Databricks job will dispatch this campaign at the chosen time
              (your local time). Channels remain mock — no real messages are sent.
            </DialogDescription>
          </DialogHeader>
          <input
            type="datetime-local"
            className="border rounded-md px-3 py-2 text-sm bg-background"
            value={schedAt}
            onChange={(e) => setSchedAt(e.target.value)}
          />
          <DialogFooter>
            <Button variant="outline" onClick={() => setScheduleOpen(false)}>Cancel</Button>
            <Button
              disabled={!schedAt || scheduleMut.isPending}
              onClick={() => scheduleMut.mutate({ params: { campaign_id: id }, data: { scheduled_at: localToUtcSql(schedAt) } })}
            >
              {scheduleMut.isPending ? "Scheduling…" : "Schedule"}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      <Dialog open={rejectOpen} onOpenChange={setRejectOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Reject campaign</DialogTitle>
            <DialogDescription>The campaign returns to draft. Add a reason (optional).</DialogDescription>
          </DialogHeader>
          <Textarea value={comment} onChange={(e) => setComment(e.target.value)} placeholder="Reason for rejection" />
          <DialogFooter>
            <Button variant="outline" onClick={() => setRejectOpen(false)}>Cancel</Button>
            <Button variant="destructive" onClick={() => rejectMut.mutate({ params: { campaign_id: id }, data: { comment: comment || null } })} disabled={rejectMut.isPending}>
              Reject
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}

function PreviewRow({ label, v, ok, strong }: { label: string; v: number; ok?: boolean; strong?: boolean }) {
  return (
    <div className="flex items-center justify-between">
      <span className="text-muted-foreground">{label}</span>
      <span className={(strong ? "font-semibold " : "") + (ok ? "text-emerald-600 dark:text-emerald-400" : "") + " tabular-nums"}>{fmtNumber(v)}</span>
    </div>
  );
}

function MetricsCards({ id }: { id: string }) {
  const { data: m } = useGetCampaignMetricsSuspense({ params: { campaign_id: id }, ...selector() });
  return (
    <div className="grid grid-cols-2 gap-3 md:grid-cols-4">
      <StatCard label="Requested" value={fmtNumber(m.requested)} />
      <StatCard label="Eligible" value={fmtNumber(m.eligible)} />
      <StatCard label="Skipped" value={fmtNumber(m.skipped)} />
      <StatCard label="Sent" value={fmtNumber(m.sent)} />
      <StatCard label="Delivered" value={fmtNumber(m.delivered)} />
      <StatCard label="Opened" value={fmtNumber(m.opened)} hint={`${fmtPct(m.open_rate)} open rate`} />
      <StatCard label="Clicked" value={fmtNumber(m.clicked)} hint={`${fmtPct(m.click_through_rate)} CTR`} />
      <StatCard label="Redeemed" value={fmtNumber(m.redeemed)} hint={`${fmtPct(m.redemption_rate)} redemption`} />
      <StatCard label="Failed" value={fmtNumber(m.failed)} hint={`${fmtPct(m.failure_rate)} failure rate`} />
    </div>
  );
}

function DispatchRuns({ id }: { id: string }) {
  const { data: runs } = useGetCampaignDispatchRunsSuspense({ params: { campaign_id: id }, ...selector() });
  if (runs.length === 0) return <p className="text-sm text-muted-foreground">No dispatch runs yet.</p>;
  return (
    <Table>
      <TableHeader>
        <TableRow>
          <TableHead>Run</TableHead><TableHead>Status</TableHead><TableHead>Requested</TableHead>
          <TableHead>Eligible</TableHead><TableHead>Sent</TableHead><TableHead>Failed</TableHead>
          <TableHead>Skipped</TableHead><TableHead>Started</TableHead>
        </TableRow>
      </TableHeader>
      <TableBody>
        {runs.map((r) => (
          <TableRow key={r.dispatch_run_id}>
            <TableCell className="font-mono text-xs">{r.dispatch_run_id}</TableCell>
            <TableCell><StatusBadge status={r.status} /></TableCell>
            <TableCell className="tabular-nums">{fmtNumber(r.requested_count)}</TableCell>
            <TableCell className="tabular-nums">{fmtNumber(r.eligible_count)}</TableCell>
            <TableCell className="tabular-nums">{fmtNumber(r.success_count)}</TableCell>
            <TableCell className="tabular-nums">{fmtNumber(r.failure_count)}</TableCell>
            <TableCell className="tabular-nums">{fmtNumber(r.skipped_count)}</TableCell>
            <TableCell className="text-xs">{fmtDateTime(r.started_at)}</TableCell>
          </TableRow>
        ))}
      </TableBody>
    </Table>
  );
}

function EventsTable({ id }: { id: string }) {
  const { data: events } = useGetCampaignEventsSuspense({ params: { campaign_id: id, limit: 200 }, ...selector() });
  function downloadCsv() {
    const header = ["delivery_event_id", "customer_id", "channel", "event_type", "event_ts", "provider_message_id", "failure_reason"];
    const rows = events.map((e) => [e.delivery_event_id, e.customer_id, e.channel, e.event_type, e.event_ts, e.provider_message_id, e.failure_reason].map((v) => `"${v ?? ""}"`).join(","));
    const blob = new Blob([[header.join(","), ...rows].join("\n")], { type: "text/csv" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `${id}-delivery-events.csv`;
    a.click();
    URL.revokeObjectURL(url);
  }
  return (
    <div className="space-y-2">
      <div className="flex justify-end">
        <Button variant="outline" size="sm" onClick={downloadCsv} disabled={events.length === 0}>
          <Download className="mr-1 h-4 w-4" /> Download CSV
        </Button>
      </div>
      {events.length === 0 ? (
        <p className="text-sm text-muted-foreground">No delivery events yet.</p>
      ) : (
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>Customer</TableHead><TableHead>Event</TableHead>
              <TableHead>Provider msg</TableHead><TableHead>When</TableHead><TableHead>Reason</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {events.slice(0, 100).map((e) => (
              <TableRow key={e.delivery_event_id}>
                <TableCell className="font-mono text-xs">{e.customer_id}</TableCell>
                <TableCell><span className="rounded bg-muted px-2 py-0.5 text-xs font-medium">{e.event_type}</span></TableCell>
                <TableCell className="font-mono text-xs">{e.provider_message_id ?? "—"}</TableCell>
                <TableCell className="text-xs">{fmtDateTime(e.event_ts)}</TableCell>
                <TableCell className="text-xs text-muted-foreground">{e.failure_reason ?? "—"}</TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      )}
    </div>
  );
}

function History({ id }: { id: string }) {
  const { data: approvals } = useGetCampaignApprovalsSuspense({ params: { campaign_id: id }, ...selector() });
  const { data: audit } = useGetCampaignAuditSuspense({ params: { campaign_id: id }, ...selector() });
  return (
    <div className="grid gap-4 md:grid-cols-2">
      <Card>
        <CardHeader><CardTitle className="text-base">Approval history</CardTitle></CardHeader>
        <CardContent className="space-y-2">
          {approvals.length === 0 ? <p className="text-sm text-muted-foreground">None.</p> : approvals.map((a) => (
            <div key={a.approval_id} className="flex items-center justify-between text-sm">
              <span className="font-medium">{a.action}</span>
              <span className="text-muted-foreground">{a.actor} · {fmtDateTime(a.created_at)}</span>
            </div>
          ))}
        </CardContent>
      </Card>
      <Card>
        <CardHeader><CardTitle className="text-base">Audit trail</CardTitle></CardHeader>
        <CardContent className="space-y-2">
          {audit.map((a) => (
            <div key={a.audit_id} className="flex items-center justify-between text-sm">
              <span className="font-mono text-xs rounded bg-muted px-2 py-0.5">{a.action}</span>
              <span className="text-muted-foreground">{a.actor} · {fmtDateTime(a.created_at)}</span>
            </div>
          ))}
        </CardContent>
      </Card>
    </div>
  );
}

function Detail({ id }: { id: string }) {
  const { data: c } = useGetCampaignSuspense({ params: { campaign_id: id }, ...selector() });
  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <div className="flex items-center gap-3">
            <h1 className="text-2xl font-bold">{c.campaign_name}</h1>
            <StatusBadge status={c.status} />
          </div>
          <p className="mt-1 font-mono text-xs text-muted-foreground">{c.campaign_id}</p>
        </div>
      </div>

      <Actions id={id} status={c.status} />

      <div className="grid gap-4 md:grid-cols-2">
        <Card>
          <CardHeader><CardTitle className="text-base">Configuration</CardTitle></CardHeader>
          <CardContent className="grid grid-cols-2 gap-3 text-sm">
            <div><p className="text-muted-foreground">Channel</p><p>{channelLabel(c.channel)}</p></div>
            <div><p className="text-muted-foreground">Offer</p><p>{c.offer_id ?? "—"}</p></div>
            <div><p className="text-muted-foreground">Audience</p><p className="font-mono text-xs">{c.audience_id}</p></div>
            <div><p className="text-muted-foreground">Version</p><p className="font-mono text-xs">{c.audience_version}</p></div>
            <div><p className="text-muted-foreground">Scheduled</p><p>{fmtDateTime(c.scheduled_at)}</p></div>
            <div><p className="text-muted-foreground">Created by</p><p>{c.created_by ?? "—"}</p></div>
            <div><p className="text-muted-foreground">Approved by</p><p>{c.approved_by ?? "—"}</p></div>
            <div><p className="text-muted-foreground">Idempotency key</p><p className="font-mono text-xs">{c.idempotency_key}</p></div>
          </CardContent>
        </Card>
        <Card>
          <CardHeader><CardTitle className="text-base">Message</CardTitle></CardHeader>
          <CardContent className="space-y-2 text-sm">
            <div><p className="text-muted-foreground">Title</p><p>{c.message_title ?? "—"}</p></div>
            <div><p className="text-muted-foreground">Body</p><p>{c.message_body ?? "—"}</p></div>
            <div><p className="text-muted-foreground">Deep link</p><p className="font-mono text-xs">{c.deep_link ?? "—"}</p></div>
          </CardContent>
        </Card>
      </div>

      <Tabs defaultValue="metrics">
        <TabsList>
          <TabsTrigger value="metrics">Metrics</TabsTrigger>
          <TabsTrigger value="delivery">Delivery</TabsTrigger>
          <TabsTrigger value="history">History</TabsTrigger>
        </TabsList>
        <TabsContent value="metrics" className="pt-4">
          <AsyncBoundary fallback={<Skeleton className="h-40 w-full" />}><MetricsCards id={id} /></AsyncBoundary>
        </TabsContent>
        <TabsContent value="delivery" className="space-y-6 pt-4">
          <div>
            <h3 className="mb-2 text-sm font-semibold">Dispatch runs</h3>
            <AsyncBoundary fallback={<Skeleton className="h-24 w-full" />}><DispatchRuns id={id} /></AsyncBoundary>
          </div>
          <div>
            <h3 className="mb-2 text-sm font-semibold">Delivery events</h3>
            <AsyncBoundary fallback={<Skeleton className="h-40 w-full" />}><EventsTable id={id} /></AsyncBoundary>
          </div>
        </TabsContent>
        <TabsContent value="history" className="pt-4">
          <AsyncBoundary fallback={<Skeleton className="h-40 w-full" />}><History id={id} /></AsyncBoundary>
        </TabsContent>
      </Tabs>
    </div>
  );
}

function CampaignDetailPage() {
  const { id } = Route.useParams();
  return (
    <>
      <div className="flex items-center gap-2">
        <Button variant="ghost" size="sm" asChild>
          <Link to="/campaigns"><ArrowLeft className="mr-1 h-4 w-4" /> Campaigns</Link>
        </Button>
      </div>
      <AsyncBoundary fallback={<Skeleton className="h-96 w-full" />}>
        <Detail id={id} />
      </AsyncBoundary>
    </>
  );
}
