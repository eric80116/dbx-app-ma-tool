import { createFileRoute, Link } from "@tanstack/react-router";
import { useState } from "react";
import {
  useGetAudienceSuspense,
  useListAudienceMembersSuspense,
  useGetSystemConfigSuspense,
} from "@/lib/api";
import selector from "@/lib/selector";
import { AsyncBoundary } from "@/components/ma/async-boundary";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import { fmtNumber } from "@/lib/format";
import { ArrowLeft, Eye, EyeOff, Users } from "lucide-react";
import type { Distribution } from "@/lib/api";

export const Route = createFileRoute("/_sidebar/audiences/$id")({
  component: () => <AudienceDetail />,
});

function DistBar({ title, items }: { title: string; items: Distribution[] }) {
  const total = items.reduce((s, i) => s + i.count, 0) || 1;
  return (
    <Card>
      <CardHeader className="pb-2">
        <CardTitle className="text-base">{title}</CardTitle>
      </CardHeader>
      <CardContent className="space-y-2">
        {items.map((i) => (
          <div key={i.label} className="space-y-1">
            <div className="flex justify-between text-xs">
              <span>{i.label}</span>
              <span className="tabular-nums text-muted-foreground">
                {fmtNumber(i.count)} ({((i.count / total) * 100).toFixed(0)}%)
              </span>
            </div>
            <div className="h-1.5 w-full rounded-full bg-muted">
              <div
                className="h-1.5 rounded-full bg-primary"
                style={{ width: `${(i.count / total) * 100}%` }}
              />
            </div>
          </div>
        ))}
      </CardContent>
    </Card>
  );
}

function MembersTable({ id, reveal }: { id: string; reveal: boolean }) {
  const { data: members } = useListAudienceMembersSuspense({
    params: { audience_id: id, limit: 25, reveal },
    ...selector(),
  });
  return (
    <Table>
      <TableHeader>
        <TableRow>
          <TableHead>Customer</TableHead>
          <TableHead>Email</TableHead>
          <TableHead>Phone</TableHead>
          <TableHead>Status</TableHead>
          <TableHead>Channel</TableHead>
          <TableHead>Loyalty</TableHead>
        </TableRow>
      </TableHeader>
      <TableBody>
        {members.map((m) => (
          <TableRow key={m.customer_id}>
            <TableCell className="font-mono text-xs">{m.customer_id}</TableCell>
            <TableCell className="text-xs">{m.email}</TableCell>
            <TableCell className="text-xs">{m.phone ?? "—"}</TableCell>
            <TableCell>
              <Badge variant={m.account_status === "Active" ? "default" : "secondary"} className="text-xs">
                {m.account_status}
              </Badge>
            </TableCell>
            <TableCell className="text-xs">{m.preferred_channel}</TableCell>
            <TableCell className="text-xs">{m.loyalty_status}</TableCell>
          </TableRow>
        ))}
      </TableBody>
    </Table>
  );
}

function Detail({ id }: { id: string }) {
  const { data: a } = useGetAudienceSuspense({ params: { audience_id: id }, ...selector() });
  const { data: config } = useGetSystemConfigSuspense(selector());
  const [reveal, setReveal] = useState(false);

  return (
    <div className="space-y-6">
      <Card>
        <CardHeader>
          <div className="flex flex-wrap items-center justify-between gap-2">
            <CardTitle className="flex items-center gap-2">
              <Users className="h-5 w-5" /> {a.audience_name}
            </CardTitle>
            <Badge variant="secondary">{a.source_type}</Badge>
          </div>
          <CardDescription>{a.description}</CardDescription>
        </CardHeader>
        <CardContent className="grid grid-cols-2 gap-4 text-sm md:grid-cols-4">
          <div><p className="text-muted-foreground">Audience ID</p><p className="font-mono text-xs">{a.audience_id}</p></div>
          <div><p className="text-muted-foreground">Version</p><p className="font-mono text-xs">{a.audience_version}</p></div>
          <div><p className="text-muted-foreground">Members</p><p className="font-semibold">{fmtNumber(a.member_count)}</p></div>
          <div><p className="text-muted-foreground">Source workspace</p><p>{a.source_workspace}</p></div>
          <div className="col-span-2 md:col-span-4"><p className="text-muted-foreground">Source table</p><p className="font-mono text-xs break-all">{a.source_table}</p></div>
        </CardContent>
      </Card>

      <div className="grid gap-4 md:grid-cols-3">
        <DistBar title="Account status" items={a.account_status_distribution ?? []} />
        <DistBar title="Preferred channel" items={a.preferred_channel_distribution ?? []} />
        <DistBar title="Loyalty" items={a.loyalty_distribution ?? []} />
      </div>

      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <div>
              <CardTitle className="text-base">Sample members</CardTitle>
              <CardDescription>
                Contact values are masked by default.
                {!config.reveal_pii_allowed && " (reveal disabled in this environment)"}
              </CardDescription>
            </div>
            {config.reveal_pii_allowed && (
              <Button variant="outline" size="sm" onClick={() => setReveal((r) => !r)}>
                {reveal ? <EyeOff className="mr-1 h-4 w-4" /> : <Eye className="mr-1 h-4 w-4" />}
                {reveal ? "Hide contacts" : "Reveal (demo)"}
              </Button>
            )}
          </div>
        </CardHeader>
        <CardContent>
          <AsyncBoundary fallback={<Skeleton className="h-64 w-full" />}>
            <MembersTable id={id} reveal={reveal && config.reveal_pii_allowed} />
          </AsyncBoundary>
        </CardContent>
      </Card>
    </div>
  );
}

function AudienceDetail() {
  const { id } = Route.useParams();
  return (
    <>
      <div className="flex items-center gap-2">
        <Button variant="ghost" size="sm" asChild>
          <Link to="/audiences"><ArrowLeft className="mr-1 h-4 w-4" /> Audiences</Link>
        </Button>
      </div>
      <AsyncBoundary fallback={<Skeleton className="h-96 w-full" />}>
        <Detail id={id} />
      </AsyncBoundary>
    </>
  );
}
