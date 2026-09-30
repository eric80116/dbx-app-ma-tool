import { createFileRoute, Link } from "@tanstack/react-router";
import { useListCampaignsSuspense } from "@/lib/api";
import selector from "@/lib/selector";
import { AsyncBoundary } from "@/components/ma/async-boundary";
import { StatusBadge } from "@/components/ma/status-badge";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { Card, CardContent } from "@/components/ui/card";
import { channelLabel, fmtDateTime } from "@/lib/format";
import { Plus } from "lucide-react";

export const Route = createFileRoute("/_sidebar/campaigns/")({
  component: () => <Campaigns />,
});

function CampaignsList() {
  const { data } = useListCampaignsSuspense(selector());
  if (data.length === 0) {
    return (
      <Card>
        <CardContent className="py-10 text-center text-sm text-muted-foreground">
          No campaigns yet. Create one to get started.
        </CardContent>
      </Card>
    );
  }
  return (
    <Card>
      <CardContent className="p-0">
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>Campaign</TableHead>
              <TableHead>Channel</TableHead>
              <TableHead>Audience</TableHead>
              <TableHead>Status</TableHead>
              <TableHead>Updated</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {data.map((c) => (
              <TableRow key={c.campaign_id} className="cursor-pointer">
                <TableCell>
                  <Link
                    to="/campaigns/$id"
                    params={{ id: c.campaign_id }}
                    className="font-medium hover:underline"
                  >
                    {c.campaign_name}
                  </Link>
                  <div className="font-mono text-xs text-muted-foreground">{c.campaign_id}</div>
                </TableCell>
                <TableCell>{channelLabel(c.channel)}</TableCell>
                <TableCell className="font-mono text-xs">{c.audience_id}</TableCell>
                <TableCell><StatusBadge status={c.status} /></TableCell>
                <TableCell className="text-xs">{fmtDateTime(c.updated_at)}</TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </CardContent>
    </Card>
  );
}

function Campaigns() {
  return (
    <>
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold">Campaigns</h1>
          <p className="text-sm text-muted-foreground">
            Configure, approve and dispatch activation campaigns.
          </p>
        </div>
        <Button asChild>
          <Link to="/campaigns/new"><Plus className="mr-1 h-4 w-4" /> New campaign</Link>
        </Button>
      </div>
      <AsyncBoundary fallback={<Skeleton className="h-64 w-full" />}>
        <CampaignsList />
      </AsyncBoundary>
    </>
  );
}
