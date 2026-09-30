import { createFileRoute, Link } from "@tanstack/react-router";
import { toast } from "sonner";
import { useQueryClient } from "@tanstack/react-query";
import {
  useListCampaignsSuspense,
  useApproveCampaign,
  useRejectCampaign,
} from "@/lib/api";
import selector from "@/lib/selector";
import { AsyncBoundary } from "@/components/ma/async-boundary";
import { StatusBadge } from "@/components/ma/status-badge";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import { channelLabel, fmtDateTime } from "@/lib/format";

export const Route = createFileRoute("/_sidebar/approvals")({
  component: () => <Approvals />,
});

function PendingList() {
  const qc = useQueryClient();
  const { data } = useListCampaignsSuspense(selector());
  const pending = data.filter((c) => c.status === "PENDING_APPROVAL");

  const invalidate = () => qc.invalidateQueries();
  const onErr = (e: unknown) => toast.error((e as Error).message);
  const approveMut = useApproveCampaign({ mutation: { onSuccess: () => { toast.success("Approved"); invalidate(); }, onError: onErr } });
  const rejectMut = useRejectCampaign({ mutation: { onSuccess: () => { toast.success("Rejected — back to draft"); invalidate(); }, onError: onErr } });

  if (pending.length === 0) {
    return (
      <Card>
        <CardContent className="py-10 text-center text-sm text-muted-foreground">
          No campaigns awaiting approval.
        </CardContent>
      </Card>
    );
  }

  return (
    <div className="space-y-3">
      {pending.map((c) => (
        <Card key={c.campaign_id}>
          <CardHeader className="pb-2">
            <div className="flex items-center justify-between">
              <CardTitle className="text-base">
                <Link to="/campaigns/$id" params={{ id: c.campaign_id }} className="hover:underline">
                  {c.campaign_name}
                </Link>
              </CardTitle>
              <StatusBadge status={c.status} />
            </div>
            <CardDescription>
              {channelLabel(c.channel)} · {c.audience_id} · {c.offer_id ?? "no offer"} · updated {fmtDateTime(c.updated_at)}
            </CardDescription>
          </CardHeader>
          <CardContent className="flex flex-wrap items-center gap-2">
            <Button size="sm" onClick={() => approveMut.mutate({ params: { campaign_id: c.campaign_id }, data: { comment: null } })} disabled={approveMut.isPending}>
              Approve
            </Button>
            <Button variant="destructive" size="sm" onClick={() => rejectMut.mutate({ params: { campaign_id: c.campaign_id }, data: { comment: "Rejected from approvals queue" } })} disabled={rejectMut.isPending}>
              Reject
            </Button>
            <Button variant="outline" size="sm" asChild>
              <Link to="/campaigns/$id" params={{ id: c.campaign_id }}>Review details</Link>
            </Button>
          </CardContent>
        </Card>
      ))}
    </div>
  );
}

function Approvals() {
  return (
    <>
      <div>
        <h1 className="text-2xl font-bold">Approvals</h1>
        <p className="text-sm text-muted-foreground">
          Campaigns awaiting approval. Only approved campaigns can be dispatched.
        </p>
      </div>
      <AsyncBoundary fallback={<Skeleton className="h-48 w-full" />}>
        <PendingList />
      </AsyncBoundary>
    </>
  );
}
