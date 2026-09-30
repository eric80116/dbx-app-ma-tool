import { createFileRoute, Link, useNavigate } from "@tanstack/react-router";
import { useState } from "react";
import { toast } from "sonner";
import {
  useListAudiencesSuspense,
  useListOffersSuspense,
  useCreateCampaign,
  usePreviewCampaign,
  useSubmitCampaign,
  type CampaignOut,
  type EligibilityPreview,
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
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { Skeleton } from "@/components/ui/skeleton";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { ArrowLeft, CheckCircle2 } from "lucide-react";
import { fmtNumber } from "@/lib/format";

export const Route = createFileRoute("/_sidebar/campaigns/new")({
  component: () => <NewCampaign />,
});

const CHANNELS = [
  { value: "APP_PUSH", label: "App Push" },
  { value: "SMS", label: "SMS" },
  { value: "COUPON", label: "Coupon" },
];

function Wizard() {
  const navigate = useNavigate();
  const { data: audiences } = useListAudiencesSuspense(selector());
  const { data: offers } = useListOffersSuspense(selector());

  const [name, setName] = useState("");
  const [audienceId, setAudienceId] = useState<string>(audiences[0]?.audience_id ?? "");
  const [channel, setChannel] = useState("APP_PUSH");
  const [offerId, setOfferId] = useState<string>("none");
  const [title, setTitle] = useState("");
  const [body, setBody] = useState("");
  const [deepLink, setDeepLink] = useState("");

  const [draft, setDraft] = useState<CampaignOut | null>(null);
  const [preview, setPreview] = useState<EligibilityPreview | null>(null);

  const createMut = useCreateCampaign();
  const previewMut = usePreviewCampaign();
  const submitMut = useSubmitCampaign();

  const selectedAudience = audiences.find((a) => a.audience_id === audienceId);
  const requireOffer = channel === "COUPON";
  const canCreate =
    name.trim() && audienceId && channel && (!requireOffer || offerId !== "none");

  async function handleCreateAndPreview() {
    try {
      const created = await createMut.mutateAsync({
        params: {},
        data: {
          campaign_name: name.trim(),
          audience_id: audienceId,
          channel: channel as "APP_PUSH" | "SMS" | "COUPON",
          offer_id: offerId === "none" ? null : offerId,
          message_title: title || null,
          message_body: body || null,
          deep_link: deepLink || null,
        },
      });
      setDraft(created.data);
      const pv = await previewMut.mutateAsync({
        params: { campaign_id: created.data.campaign_id },
      });
      setPreview(pv.data);
      toast.success("Draft created — review eligibility, then submit.");
    } catch (e) {
      toast.error(`Could not create draft: ${(e as Error).message}`);
    }
  }

  async function handleSubmit() {
    if (!draft) return;
    try {
      await submitMut.mutateAsync({ params: { campaign_id: draft.campaign_id } });
      toast.success("Submitted for approval.");
      navigate({ to: "/campaigns/$id", params: { id: draft.campaign_id } });
    } catch (e) {
      toast.error(`Could not submit: ${(e as Error).message}`);
    }
  }

  return (
    <div className="grid gap-6 lg:grid-cols-3">
      <div className="space-y-6 lg:col-span-2">
        <Card>
          <CardHeader>
            <CardTitle>Campaign details</CardTitle>
            <CardDescription>Select an audience and configure the message.</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="space-y-1.5">
              <Label>Campaign name</Label>
              <Input value={name} onChange={(e) => setName(e.target.value)} placeholder="Lapsed High-Value Member Winback" />
            </div>

            <div className="grid gap-4 sm:grid-cols-2">
              <div className="space-y-1.5">
                <Label>Audience</Label>
                <Select value={audienceId} onValueChange={setAudienceId}>
                  <SelectTrigger><SelectValue placeholder="Select audience" /></SelectTrigger>
                  <SelectContent>
                    {audiences.map((a) => (
                      <SelectItem key={a.audience_id} value={a.audience_id}>
                        {a.audience_name} ({fmtNumber(a.member_count)})
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
              <div className="space-y-1.5">
                <Label>Channel</Label>
                <Select value={channel} onValueChange={setChannel}>
                  <SelectTrigger><SelectValue /></SelectTrigger>
                  <SelectContent>
                    {CHANNELS.map((c) => (
                      <SelectItem key={c.value} value={c.value}>{c.label}</SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
            </div>

            <div className="space-y-1.5">
              <Label>Offer {requireOffer && <span className="text-destructive">*</span>}</Label>
              <Select value={offerId} onValueChange={setOfferId}>
                <SelectTrigger><SelectValue placeholder="Select offer" /></SelectTrigger>
                <SelectContent>
                  <SelectItem value="none">No offer</SelectItem>
                  {offers.map((o) => (
                    <SelectItem key={o.offer_id} value={o.offer_id}>
                      {o.offer_id} — {o.offer_name}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            <div className="space-y-1.5">
              <Label>Message title</Label>
              <Input value={title} onChange={(e) => setTitle(e.target.value)} placeholder="We miss you!" />
            </div>
            <div className="space-y-1.5">
              <Label>Message body</Label>
              <Textarea value={body} onChange={(e) => setBody(e.target.value)} placeholder="Come back and enjoy 20% off your next order." rows={3} />
            </div>
            <div className="space-y-1.5">
              <Label>Deep link</Label>
              <Input value={deepLink} onChange={(e) => setDeepLink(e.target.value)} placeholder="app://home/offers" />
            </div>
            <p className="text-xs text-muted-foreground">
              Scheduling is set after approval — approve the campaign, then use{" "}
              <span className="font-medium">Schedule</span> (or dispatch immediately).
            </p>
          </CardContent>
        </Card>
      </div>

      <div className="space-y-6">
        <Card className="sticky top-4">
          <CardHeader>
            <CardTitle>Eligibility preview</CardTitle>
            <CardDescription>
              {selectedAudience
                ? `${fmtNumber(selectedAudience.member_count)} members in ${selectedAudience.audience_name}`
                : "Select an audience"}
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            {!draft ? (
              <Button className="w-full" disabled={!canCreate || createMut.isPending || previewMut.isPending} onClick={handleCreateAndPreview}>
                {createMut.isPending || previewMut.isPending ? "Working…" : "Create draft & preview"}
              </Button>
            ) : (
              <>
                {preview && (
                  <div className="space-y-2 text-sm">
                    <Row label="Audience size" value={preview.audience_size} strong />
                    <Row label="Eligible" value={preview.eligible} tone="ok" strong />
                    <Row label="Skipped — no consent" value={preview.skipped_no_consent} />
                    <Row label="Skipped — inactive" value={preview.skipped_inactive} />
                    <Row label="Skipped — invalid contact" value={preview.skipped_invalid_contact} />
                    <Row label="Already dispatched" value={preview.already_dispatched} />
                  </div>
                )}
                <div className="rounded-md bg-muted p-2 text-xs text-muted-foreground">
                  Draft <span className="font-mono">{draft.campaign_id}</span> created.
                </div>
                <Button className="w-full" disabled={submitMut.isPending} onClick={handleSubmit}>
                  <CheckCircle2 className="mr-1 h-4 w-4" />
                  {submitMut.isPending ? "Submitting…" : "Submit for approval"}
                </Button>
                <Button variant="outline" className="w-full" asChild>
                  <Link to="/campaigns/$id" params={{ id: draft.campaign_id }}>Open campaign</Link>
                </Button>
              </>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  );
}

function Row({
  label,
  value,
  tone,
  strong,
}: {
  label: string;
  value: number;
  tone?: "ok";
  strong?: boolean;
}) {
  return (
    <div className="flex items-center justify-between">
      <span className="text-muted-foreground">{label}</span>
      <span
        className={
          (strong ? "font-semibold " : "") +
          (tone === "ok" ? "text-emerald-600 dark:text-emerald-400 tabular-nums" : "tabular-nums")
        }
      >
        {fmtNumber(value)}
      </span>
    </div>
  );
}

function NewCampaign() {
  return (
    <>
      <div className="flex items-center gap-2">
        <Button variant="ghost" size="sm" asChild>
          <Link to="/campaigns"><ArrowLeft className="mr-1 h-4 w-4" /> Campaigns</Link>
        </Button>
      </div>
      <div>
        <h1 className="text-2xl font-bold">New campaign</h1>
        <p className="text-sm text-muted-foreground">
          Consent, account-status and contactability guardrails are enforced server-side.
        </p>
      </div>
      <AsyncBoundary fallback={<Skeleton className="h-96 w-full" />}>
        <Wizard />
      </AsyncBoundary>
    </>
  );
}
