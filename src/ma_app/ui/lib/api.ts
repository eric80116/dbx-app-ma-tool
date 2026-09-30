import { useQuery, useSuspenseQuery, useMutation } from "@tanstack/react-query";
import type { UseQueryOptions, UseSuspenseQueryOptions, UseMutationOptions } from "@tanstack/react-query";
export class ApiError extends Error {
    status: number;
    statusText: string;
    body: unknown;
    constructor(status: number, statusText: string, body: unknown){
        super(`HTTP ${status}: ${statusText}`);
        this.name = "ApiError";
        this.status = status;
        this.statusText = statusText;
        this.body = body;
    }
}
export interface ApprovalActionIn {
    comment?: string | null;
}
export interface ApprovalOut {
    action: string;
    actor?: string | null;
    approval_id: string;
    campaign_id: string;
    comment?: string | null;
    created_at?: string | null;
}
export interface AudienceDetail {
    account_status_distribution?: Distribution[];
    audience_id: string;
    audience_name: string;
    audience_version: string;
    description?: string | null;
    is_active?: boolean;
    last_refreshed_at?: string | null;
    loyalty_distribution?: Distribution[];
    member_count: number;
    preferred_channel_distribution?: Distribution[];
    source_table: string;
    source_type: string;
    source_workspace: string;
}
export interface AudienceMember {
    account_status?: string | null;
    country?: string | null;
    customer_id: string;
    customer_segment?: string | null;
    email?: string | null;
    first_name?: string | null;
    last_name?: string | null;
    loyalty_status?: string | null;
    metro_area?: string | null;
    phone?: string | null;
    preferred_channel?: string | null;
    state_province?: string | null;
}
export interface AudienceSummary {
    audience_id: string;
    audience_name: string;
    audience_version: string;
    description?: string | null;
    is_active?: boolean;
    last_refreshed_at?: string | null;
    member_count: number;
    source_table: string;
    source_type: string;
    source_workspace: string;
}
export interface AuditOut {
    action: string;
    actor?: string | null;
    audit_id: string;
    created_at?: string | null;
    metadata_json?: string | null;
    resource_id?: string | null;
    resource_type?: string | null;
}
export interface CampaignIn {
    audience_id: string;
    audience_version?: string | null;
    campaign_name: string;
    channel: Channel;
    deep_link?: string | null;
    message_body?: string | null;
    message_title?: string | null;
    offer_id?: string | null;
    scheduled_at?: string | null;
}
export interface CampaignMetrics {
    campaign_id: string;
    click_through_rate?: number;
    clicked?: number;
    delivered?: number;
    eligible?: number;
    failed?: number;
    failure_rate?: number;
    open_rate?: number;
    opened?: number;
    redeemed?: number;
    redemption_rate?: number;
    requested?: number;
    sent?: number;
    skipped?: number;
}
export interface CampaignOut {
    approved_by?: string | null;
    audience_id: string;
    audience_version?: string | null;
    campaign_id: string;
    campaign_name: string;
    channel: string;
    created_at?: string | null;
    created_by?: string | null;
    deep_link?: string | null;
    idempotency_key?: string | null;
    message_body?: string | null;
    message_title?: string | null;
    offer_id?: string | null;
    scheduled_at?: string | null;
    status: string;
    updated_at?: string | null;
}
export interface CampaignPatch {
    campaign_name?: string | null;
    channel?: Channel | null;
    deep_link?: string | null;
    message_body?: string | null;
    message_title?: string | null;
    offer_id?: string | null;
    scheduled_at?: string | null;
}
export const Channel = {
    APP_PUSH: "APP_PUSH",
    SMS: "SMS",
    COUPON: "COUPON"
} as const;
export type Channel = typeof Channel[keyof typeof Channel];
export interface ComplexValue {
    display?: string | null;
    primary?: boolean | null;
    ref?: string | null;
    type?: string | null;
    value?: string | null;
}
export interface DashboardStats {
    click_rate?: number;
    completed_dispatches?: number;
    draft_campaigns?: number;
    open_rate?: number;
    pending_approvals?: number;
    recent_activity?: AuditOut[];
    redemption_rate?: number;
    scheduled_campaigns?: number;
    total_audiences?: number;
    total_campaigns?: number;
    total_delivered?: number;
}
export interface DeliveryEventOut {
    campaign_id: string;
    channel?: string | null;
    customer_id?: string | null;
    delivery_event_id: string;
    dispatch_run_id?: string | null;
    event_ts?: string | null;
    event_type: string;
    failure_reason?: string | null;
    provider_message_id?: string | null;
}
export interface DispatchRunOut {
    campaign_id: string;
    dispatch_run_id: string;
    eligible_count?: number;
    error_message?: string | null;
    failure_count?: number;
    finished_at?: string | null;
    idempotency_key?: string | null;
    requested_count?: number;
    skipped_count?: number;
    started_at?: string | null;
    status: string;
    success_count?: number;
}
export interface Distribution {
    count: number;
    label: string;
}
export interface EligibilityPreview {
    already_dispatched: number;
    audience_size: number;
    eligible: number;
    skipped_inactive: number;
    skipped_invalid_contact: number;
    skipped_no_consent: number;
}
export interface HTTPValidationError {
    detail?: ValidationError[];
}
export interface Name {
    family_name?: string | null;
    given_name?: string | null;
}
export interface OfferOut {
    active_flag?: boolean;
    discount_value?: number | null;
    eligible_channel?: string | null;
    min_spend?: number | null;
    offer_id: string;
    offer_name: string;
    offer_type: string;
    valid_from?: string | null;
    valid_to?: string | null;
}
export interface ScheduleIn {
    scheduled_at: string;
}
export interface SystemConfigOut {
    app_name: string;
    app_schema: string;
    audience_source_mode: string;
    audience_table: string;
    demo_banner?: string;
    reveal_pii_allowed: boolean;
    scheduler_enabled?: boolean;
    target_catalog: string;
    warehouse_configured: boolean;
}
export interface User {
    active?: boolean | null;
    display_name?: string | null;
    emails?: ComplexValue[] | null;
    entitlements?: ComplexValue[] | null;
    external_id?: string | null;
    groups?: ComplexValue[] | null;
    id?: string | null;
    name?: Name | null;
    roles?: ComplexValue[] | null;
    schemas?: UserSchema[] | null;
    user_name?: string | null;
}
export const UserSchema = {
    "urn:ietf:params:scim:schemas:core:2.0:User": "urn:ietf:params:scim:schemas:core:2.0:User",
    "urn:ietf:params:scim:schemas:extension:workspace:2.0:User": "urn:ietf:params:scim:schemas:extension:workspace:2.0:User"
} as const;
export type UserSchema = typeof UserSchema[keyof typeof UserSchema];
export interface ValidationError {
    ctx?: Record<string, unknown>;
    input?: unknown;
    loc: (string | number)[];
    msg: string;
    type: string;
}
export interface VersionOut {
    version: string;
}
export const listAudiences = async (options?: RequestInit): Promise<{
    data: AudienceSummary[];
}> =>{
    const res = await fetch("/api/audiences", {
        ...options,
        method: "GET"
    });
    if (!res.ok) {
        const body = await res.text();
        let parsed: unknown;
        try {
            parsed = JSON.parse(body);
        } catch  {
            parsed = body;
        }
        throw new ApiError(res.status, res.statusText, parsed);
    }
    return {
        data: await res.json()
    };
};
export const listAudiencesKey = ()=>{
    return [
        "/api/audiences"
    ] as const;
};
export function useListAudiences<TData = {
    data: AudienceSummary[];
}>(options?: {
    query?: Omit<UseQueryOptions<{
        data: AudienceSummary[];
    }, ApiError, TData>, "queryKey" | "queryFn">;
}) {
    return useQuery({
        queryKey: listAudiencesKey(),
        queryFn: ()=>listAudiences(),
        ...options?.query
    });
}
export function useListAudiencesSuspense<TData = {
    data: AudienceSummary[];
}>(options?: {
    query?: Omit<UseSuspenseQueryOptions<{
        data: AudienceSummary[];
    }, ApiError, TData>, "queryKey" | "queryFn">;
}) {
    return useSuspenseQuery({
        queryKey: listAudiencesKey(),
        queryFn: ()=>listAudiences(),
        ...options?.query
    });
}
export interface GetAudienceParams {
    audience_id: string;
    version?: string | null;
}
export const getAudience = async (params: GetAudienceParams, options?: RequestInit): Promise<{
    data: AudienceDetail;
}> =>{
    const searchParams = new URLSearchParams();
    if (params?.version != null) searchParams.set("version", String(params?.version));
    const queryString = searchParams.toString();
    const url = queryString ? `/api/audiences/${params.audience_id}?${queryString}` : `/api/audiences/${params.audience_id}`;
    const res = await fetch(url, {
        ...options,
        method: "GET"
    });
    if (!res.ok) {
        const body = await res.text();
        let parsed: unknown;
        try {
            parsed = JSON.parse(body);
        } catch  {
            parsed = body;
        }
        throw new ApiError(res.status, res.statusText, parsed);
    }
    return {
        data: await res.json()
    };
};
export const getAudienceKey = (params?: GetAudienceParams)=>{
    return [
        "/api/audiences/{audience_id}",
        params
    ] as const;
};
export function useGetAudience<TData = {
    data: AudienceDetail;
}>(options: {
    params: GetAudienceParams;
    query?: Omit<UseQueryOptions<{
        data: AudienceDetail;
    }, ApiError, TData>, "queryKey" | "queryFn">;
}) {
    return useQuery({
        queryKey: getAudienceKey(options.params),
        queryFn: ()=>getAudience(options.params),
        ...options?.query
    });
}
export function useGetAudienceSuspense<TData = {
    data: AudienceDetail;
}>(options: {
    params: GetAudienceParams;
    query?: Omit<UseSuspenseQueryOptions<{
        data: AudienceDetail;
    }, ApiError, TData>, "queryKey" | "queryFn">;
}) {
    return useSuspenseQuery({
        queryKey: getAudienceKey(options.params),
        queryFn: ()=>getAudience(options.params),
        ...options?.query
    });
}
export interface ListAudienceMembersParams {
    audience_id: string;
    version?: string | null;
    limit?: number;
    reveal?: boolean;
}
export const listAudienceMembers = async (params: ListAudienceMembersParams, options?: RequestInit): Promise<{
    data: AudienceMember[];
}> =>{
    const searchParams = new URLSearchParams();
    if (params?.version != null) searchParams.set("version", String(params?.version));
    if (params?.limit != null) searchParams.set("limit", String(params?.limit));
    if (params?.reveal != null) searchParams.set("reveal", String(params?.reveal));
    const queryString = searchParams.toString();
    const url = queryString ? `/api/audiences/${params.audience_id}/members?${queryString}` : `/api/audiences/${params.audience_id}/members`;
    const res = await fetch(url, {
        ...options,
        method: "GET"
    });
    if (!res.ok) {
        const body = await res.text();
        let parsed: unknown;
        try {
            parsed = JSON.parse(body);
        } catch  {
            parsed = body;
        }
        throw new ApiError(res.status, res.statusText, parsed);
    }
    return {
        data: await res.json()
    };
};
export const listAudienceMembersKey = (params?: ListAudienceMembersParams)=>{
    return [
        "/api/audiences/{audience_id}/members",
        params
    ] as const;
};
export function useListAudienceMembers<TData = {
    data: AudienceMember[];
}>(options: {
    params: ListAudienceMembersParams;
    query?: Omit<UseQueryOptions<{
        data: AudienceMember[];
    }, ApiError, TData>, "queryKey" | "queryFn">;
}) {
    return useQuery({
        queryKey: listAudienceMembersKey(options.params),
        queryFn: ()=>listAudienceMembers(options.params),
        ...options?.query
    });
}
export function useListAudienceMembersSuspense<TData = {
    data: AudienceMember[];
}>(options: {
    params: ListAudienceMembersParams;
    query?: Omit<UseSuspenseQueryOptions<{
        data: AudienceMember[];
    }, ApiError, TData>, "queryKey" | "queryFn">;
}) {
    return useSuspenseQuery({
        queryKey: listAudienceMembersKey(options.params),
        queryFn: ()=>listAudienceMembers(options.params),
        ...options?.query
    });
}
export const listCampaigns = async (options?: RequestInit): Promise<{
    data: CampaignOut[];
}> =>{
    const res = await fetch("/api/campaigns", {
        ...options,
        method: "GET"
    });
    if (!res.ok) {
        const body = await res.text();
        let parsed: unknown;
        try {
            parsed = JSON.parse(body);
        } catch  {
            parsed = body;
        }
        throw new ApiError(res.status, res.statusText, parsed);
    }
    return {
        data: await res.json()
    };
};
export const listCampaignsKey = ()=>{
    return [
        "/api/campaigns"
    ] as const;
};
export function useListCampaigns<TData = {
    data: CampaignOut[];
}>(options?: {
    query?: Omit<UseQueryOptions<{
        data: CampaignOut[];
    }, ApiError, TData>, "queryKey" | "queryFn">;
}) {
    return useQuery({
        queryKey: listCampaignsKey(),
        queryFn: ()=>listCampaigns(),
        ...options?.query
    });
}
export function useListCampaignsSuspense<TData = {
    data: CampaignOut[];
}>(options?: {
    query?: Omit<UseSuspenseQueryOptions<{
        data: CampaignOut[];
    }, ApiError, TData>, "queryKey" | "queryFn">;
}) {
    return useSuspenseQuery({
        queryKey: listCampaignsKey(),
        queryFn: ()=>listCampaigns(),
        ...options?.query
    });
}
export interface CreateCampaignParams {
    "X-Forwarded-Host"?: string | null;
    "X-Forwarded-Preferred-Username"?: string | null;
    "X-Forwarded-User"?: string | null;
    "X-Forwarded-Email"?: string | null;
    "X-Request-Id"?: string | null;
    "X-Forwarded-Access-Token"?: string | null;
}
export const createCampaign = async (data: CampaignIn, params?: CreateCampaignParams, options?: RequestInit): Promise<{
    data: CampaignOut;
}> =>{
    const res = await fetch("/api/campaigns", {
        ...options,
        method: "POST",
        headers: {
            "Content-Type": "application/json",
            ...(params?.["X-Forwarded-Host"] != null && {
                "X-Forwarded-Host": params["X-Forwarded-Host"]
            }),
            ...(params?.["X-Forwarded-Preferred-Username"] != null && {
                "X-Forwarded-Preferred-Username": params["X-Forwarded-Preferred-Username"]
            }),
            ...(params?.["X-Forwarded-User"] != null && {
                "X-Forwarded-User": params["X-Forwarded-User"]
            }),
            ...(params?.["X-Forwarded-Email"] != null && {
                "X-Forwarded-Email": params["X-Forwarded-Email"]
            }),
            ...(params?.["X-Request-Id"] != null && {
                "X-Request-Id": params["X-Request-Id"]
            }),
            ...(params?.["X-Forwarded-Access-Token"] != null && {
                "X-Forwarded-Access-Token": params["X-Forwarded-Access-Token"]
            }),
            ...options?.headers
        },
        body: JSON.stringify(data)
    });
    if (!res.ok) {
        const body = await res.text();
        let parsed: unknown;
        try {
            parsed = JSON.parse(body);
        } catch  {
            parsed = body;
        }
        throw new ApiError(res.status, res.statusText, parsed);
    }
    return {
        data: await res.json()
    };
};
export function useCreateCampaign(options?: {
    mutation?: UseMutationOptions<{
        data: CampaignOut;
    }, ApiError, {
        params: CreateCampaignParams;
        data: CampaignIn;
    }>;
}) {
    return useMutation({
        mutationFn: (vars)=>createCampaign(vars.data, vars.params),
        ...options?.mutation
    });
}
export interface GetCampaignParams {
    campaign_id: string;
}
export const getCampaign = async (params: GetCampaignParams, options?: RequestInit): Promise<{
    data: CampaignOut;
}> =>{
    const res = await fetch(`/api/campaigns/${params.campaign_id}`, {
        ...options,
        method: "GET"
    });
    if (!res.ok) {
        const body = await res.text();
        let parsed: unknown;
        try {
            parsed = JSON.parse(body);
        } catch  {
            parsed = body;
        }
        throw new ApiError(res.status, res.statusText, parsed);
    }
    return {
        data: await res.json()
    };
};
export const getCampaignKey = (params?: GetCampaignParams)=>{
    return [
        "/api/campaigns/{campaign_id}",
        params
    ] as const;
};
export function useGetCampaign<TData = {
    data: CampaignOut;
}>(options: {
    params: GetCampaignParams;
    query?: Omit<UseQueryOptions<{
        data: CampaignOut;
    }, ApiError, TData>, "queryKey" | "queryFn">;
}) {
    return useQuery({
        queryKey: getCampaignKey(options.params),
        queryFn: ()=>getCampaign(options.params),
        ...options?.query
    });
}
export function useGetCampaignSuspense<TData = {
    data: CampaignOut;
}>(options: {
    params: GetCampaignParams;
    query?: Omit<UseSuspenseQueryOptions<{
        data: CampaignOut;
    }, ApiError, TData>, "queryKey" | "queryFn">;
}) {
    return useSuspenseQuery({
        queryKey: getCampaignKey(options.params),
        queryFn: ()=>getCampaign(options.params),
        ...options?.query
    });
}
export interface UpdateCampaignParams {
    campaign_id: string;
    "X-Forwarded-Host"?: string | null;
    "X-Forwarded-Preferred-Username"?: string | null;
    "X-Forwarded-User"?: string | null;
    "X-Forwarded-Email"?: string | null;
    "X-Request-Id"?: string | null;
    "X-Forwarded-Access-Token"?: string | null;
}
export const updateCampaign = async (params: UpdateCampaignParams, data: CampaignPatch, options?: RequestInit): Promise<{
    data: CampaignOut;
}> =>{
    const res = await fetch(`/api/campaigns/${params.campaign_id}`, {
        ...options,
        method: "PATCH",
        headers: {
            "Content-Type": "application/json",
            ...(params?.["X-Forwarded-Host"] != null && {
                "X-Forwarded-Host": params["X-Forwarded-Host"]
            }),
            ...(params?.["X-Forwarded-Preferred-Username"] != null && {
                "X-Forwarded-Preferred-Username": params["X-Forwarded-Preferred-Username"]
            }),
            ...(params?.["X-Forwarded-User"] != null && {
                "X-Forwarded-User": params["X-Forwarded-User"]
            }),
            ...(params?.["X-Forwarded-Email"] != null && {
                "X-Forwarded-Email": params["X-Forwarded-Email"]
            }),
            ...(params?.["X-Request-Id"] != null && {
                "X-Request-Id": params["X-Request-Id"]
            }),
            ...(params?.["X-Forwarded-Access-Token"] != null && {
                "X-Forwarded-Access-Token": params["X-Forwarded-Access-Token"]
            }),
            ...options?.headers
        },
        body: JSON.stringify(data)
    });
    if (!res.ok) {
        const body = await res.text();
        let parsed: unknown;
        try {
            parsed = JSON.parse(body);
        } catch  {
            parsed = body;
        }
        throw new ApiError(res.status, res.statusText, parsed);
    }
    return {
        data: await res.json()
    };
};
export function useUpdateCampaign(options?: {
    mutation?: UseMutationOptions<{
        data: CampaignOut;
    }, ApiError, {
        params: UpdateCampaignParams;
        data: CampaignPatch;
    }>;
}) {
    return useMutation({
        mutationFn: (vars)=>updateCampaign(vars.params, vars.data),
        ...options?.mutation
    });
}
export interface GetCampaignApprovalsParams {
    campaign_id: string;
}
export const getCampaignApprovals = async (params: GetCampaignApprovalsParams, options?: RequestInit): Promise<{
    data: ApprovalOut[];
}> =>{
    const res = await fetch(`/api/campaigns/${params.campaign_id}/approvals`, {
        ...options,
        method: "GET"
    });
    if (!res.ok) {
        const body = await res.text();
        let parsed: unknown;
        try {
            parsed = JSON.parse(body);
        } catch  {
            parsed = body;
        }
        throw new ApiError(res.status, res.statusText, parsed);
    }
    return {
        data: await res.json()
    };
};
export const getCampaignApprovalsKey = (params?: GetCampaignApprovalsParams)=>{
    return [
        "/api/campaigns/{campaign_id}/approvals",
        params
    ] as const;
};
export function useGetCampaignApprovals<TData = {
    data: ApprovalOut[];
}>(options: {
    params: GetCampaignApprovalsParams;
    query?: Omit<UseQueryOptions<{
        data: ApprovalOut[];
    }, ApiError, TData>, "queryKey" | "queryFn">;
}) {
    return useQuery({
        queryKey: getCampaignApprovalsKey(options.params),
        queryFn: ()=>getCampaignApprovals(options.params),
        ...options?.query
    });
}
export function useGetCampaignApprovalsSuspense<TData = {
    data: ApprovalOut[];
}>(options: {
    params: GetCampaignApprovalsParams;
    query?: Omit<UseSuspenseQueryOptions<{
        data: ApprovalOut[];
    }, ApiError, TData>, "queryKey" | "queryFn">;
}) {
    return useSuspenseQuery({
        queryKey: getCampaignApprovalsKey(options.params),
        queryFn: ()=>getCampaignApprovals(options.params),
        ...options?.query
    });
}
export interface ApproveCampaignParams {
    campaign_id: string;
    "X-Forwarded-Host"?: string | null;
    "X-Forwarded-Preferred-Username"?: string | null;
    "X-Forwarded-User"?: string | null;
    "X-Forwarded-Email"?: string | null;
    "X-Request-Id"?: string | null;
    "X-Forwarded-Access-Token"?: string | null;
}
export const approveCampaign = async (params: ApproveCampaignParams, data: ApprovalActionIn | null, options?: RequestInit): Promise<{
    data: CampaignOut;
}> =>{
    const res = await fetch(`/api/campaigns/${params.campaign_id}/approve`, {
        ...options,
        method: "POST",
        headers: {
            "Content-Type": "application/json",
            ...(params?.["X-Forwarded-Host"] != null && {
                "X-Forwarded-Host": params["X-Forwarded-Host"]
            }),
            ...(params?.["X-Forwarded-Preferred-Username"] != null && {
                "X-Forwarded-Preferred-Username": params["X-Forwarded-Preferred-Username"]
            }),
            ...(params?.["X-Forwarded-User"] != null && {
                "X-Forwarded-User": params["X-Forwarded-User"]
            }),
            ...(params?.["X-Forwarded-Email"] != null && {
                "X-Forwarded-Email": params["X-Forwarded-Email"]
            }),
            ...(params?.["X-Request-Id"] != null && {
                "X-Request-Id": params["X-Request-Id"]
            }),
            ...(params?.["X-Forwarded-Access-Token"] != null && {
                "X-Forwarded-Access-Token": params["X-Forwarded-Access-Token"]
            }),
            ...options?.headers
        },
        body: JSON.stringify(data)
    });
    if (!res.ok) {
        const body = await res.text();
        let parsed: unknown;
        try {
            parsed = JSON.parse(body);
        } catch  {
            parsed = body;
        }
        throw new ApiError(res.status, res.statusText, parsed);
    }
    return {
        data: await res.json()
    };
};
export function useApproveCampaign(options?: {
    mutation?: UseMutationOptions<{
        data: CampaignOut;
    }, ApiError, {
        params: ApproveCampaignParams;
        data: ApprovalActionIn | null;
    }>;
}) {
    return useMutation({
        mutationFn: (vars)=>approveCampaign(vars.params, vars.data),
        ...options?.mutation
    });
}
export interface GetCampaignAuditParams {
    campaign_id: string;
}
export const getCampaignAudit = async (params: GetCampaignAuditParams, options?: RequestInit): Promise<{
    data: AuditOut[];
}> =>{
    const res = await fetch(`/api/campaigns/${params.campaign_id}/audit`, {
        ...options,
        method: "GET"
    });
    if (!res.ok) {
        const body = await res.text();
        let parsed: unknown;
        try {
            parsed = JSON.parse(body);
        } catch  {
            parsed = body;
        }
        throw new ApiError(res.status, res.statusText, parsed);
    }
    return {
        data: await res.json()
    };
};
export const getCampaignAuditKey = (params?: GetCampaignAuditParams)=>{
    return [
        "/api/campaigns/{campaign_id}/audit",
        params
    ] as const;
};
export function useGetCampaignAudit<TData = {
    data: AuditOut[];
}>(options: {
    params: GetCampaignAuditParams;
    query?: Omit<UseQueryOptions<{
        data: AuditOut[];
    }, ApiError, TData>, "queryKey" | "queryFn">;
}) {
    return useQuery({
        queryKey: getCampaignAuditKey(options.params),
        queryFn: ()=>getCampaignAudit(options.params),
        ...options?.query
    });
}
export function useGetCampaignAuditSuspense<TData = {
    data: AuditOut[];
}>(options: {
    params: GetCampaignAuditParams;
    query?: Omit<UseSuspenseQueryOptions<{
        data: AuditOut[];
    }, ApiError, TData>, "queryKey" | "queryFn">;
}) {
    return useSuspenseQuery({
        queryKey: getCampaignAuditKey(options.params),
        queryFn: ()=>getCampaignAudit(options.params),
        ...options?.query
    });
}
export interface CancelCampaignParams {
    campaign_id: string;
    "X-Forwarded-Host"?: string | null;
    "X-Forwarded-Preferred-Username"?: string | null;
    "X-Forwarded-User"?: string | null;
    "X-Forwarded-Email"?: string | null;
    "X-Request-Id"?: string | null;
    "X-Forwarded-Access-Token"?: string | null;
}
export const cancelCampaign = async (params: CancelCampaignParams, data: ApprovalActionIn | null, options?: RequestInit): Promise<{
    data: CampaignOut;
}> =>{
    const res = await fetch(`/api/campaigns/${params.campaign_id}/cancel`, {
        ...options,
        method: "POST",
        headers: {
            "Content-Type": "application/json",
            ...(params?.["X-Forwarded-Host"] != null && {
                "X-Forwarded-Host": params["X-Forwarded-Host"]
            }),
            ...(params?.["X-Forwarded-Preferred-Username"] != null && {
                "X-Forwarded-Preferred-Username": params["X-Forwarded-Preferred-Username"]
            }),
            ...(params?.["X-Forwarded-User"] != null && {
                "X-Forwarded-User": params["X-Forwarded-User"]
            }),
            ...(params?.["X-Forwarded-Email"] != null && {
                "X-Forwarded-Email": params["X-Forwarded-Email"]
            }),
            ...(params?.["X-Request-Id"] != null && {
                "X-Request-Id": params["X-Request-Id"]
            }),
            ...(params?.["X-Forwarded-Access-Token"] != null && {
                "X-Forwarded-Access-Token": params["X-Forwarded-Access-Token"]
            }),
            ...options?.headers
        },
        body: JSON.stringify(data)
    });
    if (!res.ok) {
        const body = await res.text();
        let parsed: unknown;
        try {
            parsed = JSON.parse(body);
        } catch  {
            parsed = body;
        }
        throw new ApiError(res.status, res.statusText, parsed);
    }
    return {
        data: await res.json()
    };
};
export function useCancelCampaign(options?: {
    mutation?: UseMutationOptions<{
        data: CampaignOut;
    }, ApiError, {
        params: CancelCampaignParams;
        data: ApprovalActionIn | null;
    }>;
}) {
    return useMutation({
        mutationFn: (vars)=>cancelCampaign(vars.params, vars.data),
        ...options?.mutation
    });
}
export interface DispatchCampaignParams {
    campaign_id: string;
    "X-Forwarded-Host"?: string | null;
    "X-Forwarded-Preferred-Username"?: string | null;
    "X-Forwarded-User"?: string | null;
    "X-Forwarded-Email"?: string | null;
    "X-Request-Id"?: string | null;
    "X-Forwarded-Access-Token"?: string | null;
}
export const dispatchCampaign = async (params: DispatchCampaignParams, options?: RequestInit): Promise<{
    data: DispatchRunOut;
}> =>{
    const res = await fetch(`/api/campaigns/${params.campaign_id}/dispatch`, {
        ...options,
        method: "POST",
        headers: {
            ...(params?.["X-Forwarded-Host"] != null && {
                "X-Forwarded-Host": params["X-Forwarded-Host"]
            }),
            ...(params?.["X-Forwarded-Preferred-Username"] != null && {
                "X-Forwarded-Preferred-Username": params["X-Forwarded-Preferred-Username"]
            }),
            ...(params?.["X-Forwarded-User"] != null && {
                "X-Forwarded-User": params["X-Forwarded-User"]
            }),
            ...(params?.["X-Forwarded-Email"] != null && {
                "X-Forwarded-Email": params["X-Forwarded-Email"]
            }),
            ...(params?.["X-Request-Id"] != null && {
                "X-Request-Id": params["X-Request-Id"]
            }),
            ...(params?.["X-Forwarded-Access-Token"] != null && {
                "X-Forwarded-Access-Token": params["X-Forwarded-Access-Token"]
            }),
            ...options?.headers
        }
    });
    if (!res.ok) {
        const body = await res.text();
        let parsed: unknown;
        try {
            parsed = JSON.parse(body);
        } catch  {
            parsed = body;
        }
        throw new ApiError(res.status, res.statusText, parsed);
    }
    return {
        data: await res.json()
    };
};
export function useDispatchCampaign(options?: {
    mutation?: UseMutationOptions<{
        data: DispatchRunOut;
    }, ApiError, {
        params: DispatchCampaignParams;
    }>;
}) {
    return useMutation({
        mutationFn: (vars)=>dispatchCampaign(vars.params),
        ...options?.mutation
    });
}
export interface GetCampaignDispatchRunsParams {
    campaign_id: string;
}
export const getCampaignDispatchRuns = async (params: GetCampaignDispatchRunsParams, options?: RequestInit): Promise<{
    data: DispatchRunOut[];
}> =>{
    const res = await fetch(`/api/campaigns/${params.campaign_id}/dispatch-runs`, {
        ...options,
        method: "GET"
    });
    if (!res.ok) {
        const body = await res.text();
        let parsed: unknown;
        try {
            parsed = JSON.parse(body);
        } catch  {
            parsed = body;
        }
        throw new ApiError(res.status, res.statusText, parsed);
    }
    return {
        data: await res.json()
    };
};
export const getCampaignDispatchRunsKey = (params?: GetCampaignDispatchRunsParams)=>{
    return [
        "/api/campaigns/{campaign_id}/dispatch-runs",
        params
    ] as const;
};
export function useGetCampaignDispatchRuns<TData = {
    data: DispatchRunOut[];
}>(options: {
    params: GetCampaignDispatchRunsParams;
    query?: Omit<UseQueryOptions<{
        data: DispatchRunOut[];
    }, ApiError, TData>, "queryKey" | "queryFn">;
}) {
    return useQuery({
        queryKey: getCampaignDispatchRunsKey(options.params),
        queryFn: ()=>getCampaignDispatchRuns(options.params),
        ...options?.query
    });
}
export function useGetCampaignDispatchRunsSuspense<TData = {
    data: DispatchRunOut[];
}>(options: {
    params: GetCampaignDispatchRunsParams;
    query?: Omit<UseSuspenseQueryOptions<{
        data: DispatchRunOut[];
    }, ApiError, TData>, "queryKey" | "queryFn">;
}) {
    return useSuspenseQuery({
        queryKey: getCampaignDispatchRunsKey(options.params),
        queryFn: ()=>getCampaignDispatchRuns(options.params),
        ...options?.query
    });
}
export interface GetCampaignEventsParams {
    campaign_id: string;
    limit?: number;
}
export const getCampaignEvents = async (params: GetCampaignEventsParams, options?: RequestInit): Promise<{
    data: DeliveryEventOut[];
}> =>{
    const searchParams = new URLSearchParams();
    if (params?.limit != null) searchParams.set("limit", String(params?.limit));
    const queryString = searchParams.toString();
    const url = queryString ? `/api/campaigns/${params.campaign_id}/events?${queryString}` : `/api/campaigns/${params.campaign_id}/events`;
    const res = await fetch(url, {
        ...options,
        method: "GET"
    });
    if (!res.ok) {
        const body = await res.text();
        let parsed: unknown;
        try {
            parsed = JSON.parse(body);
        } catch  {
            parsed = body;
        }
        throw new ApiError(res.status, res.statusText, parsed);
    }
    return {
        data: await res.json()
    };
};
export const getCampaignEventsKey = (params?: GetCampaignEventsParams)=>{
    return [
        "/api/campaigns/{campaign_id}/events",
        params
    ] as const;
};
export function useGetCampaignEvents<TData = {
    data: DeliveryEventOut[];
}>(options: {
    params: GetCampaignEventsParams;
    query?: Omit<UseQueryOptions<{
        data: DeliveryEventOut[];
    }, ApiError, TData>, "queryKey" | "queryFn">;
}) {
    return useQuery({
        queryKey: getCampaignEventsKey(options.params),
        queryFn: ()=>getCampaignEvents(options.params),
        ...options?.query
    });
}
export function useGetCampaignEventsSuspense<TData = {
    data: DeliveryEventOut[];
}>(options: {
    params: GetCampaignEventsParams;
    query?: Omit<UseSuspenseQueryOptions<{
        data: DeliveryEventOut[];
    }, ApiError, TData>, "queryKey" | "queryFn">;
}) {
    return useSuspenseQuery({
        queryKey: getCampaignEventsKey(options.params),
        queryFn: ()=>getCampaignEvents(options.params),
        ...options?.query
    });
}
export interface GetCampaignMetricsParams {
    campaign_id: string;
}
export const getCampaignMetrics = async (params: GetCampaignMetricsParams, options?: RequestInit): Promise<{
    data: CampaignMetrics;
}> =>{
    const res = await fetch(`/api/campaigns/${params.campaign_id}/metrics`, {
        ...options,
        method: "GET"
    });
    if (!res.ok) {
        const body = await res.text();
        let parsed: unknown;
        try {
            parsed = JSON.parse(body);
        } catch  {
            parsed = body;
        }
        throw new ApiError(res.status, res.statusText, parsed);
    }
    return {
        data: await res.json()
    };
};
export const getCampaignMetricsKey = (params?: GetCampaignMetricsParams)=>{
    return [
        "/api/campaigns/{campaign_id}/metrics",
        params
    ] as const;
};
export function useGetCampaignMetrics<TData = {
    data: CampaignMetrics;
}>(options: {
    params: GetCampaignMetricsParams;
    query?: Omit<UseQueryOptions<{
        data: CampaignMetrics;
    }, ApiError, TData>, "queryKey" | "queryFn">;
}) {
    return useQuery({
        queryKey: getCampaignMetricsKey(options.params),
        queryFn: ()=>getCampaignMetrics(options.params),
        ...options?.query
    });
}
export function useGetCampaignMetricsSuspense<TData = {
    data: CampaignMetrics;
}>(options: {
    params: GetCampaignMetricsParams;
    query?: Omit<UseSuspenseQueryOptions<{
        data: CampaignMetrics;
    }, ApiError, TData>, "queryKey" | "queryFn">;
}) {
    return useSuspenseQuery({
        queryKey: getCampaignMetricsKey(options.params),
        queryFn: ()=>getCampaignMetrics(options.params),
        ...options?.query
    });
}
export interface PreviewCampaignParams {
    campaign_id: string;
}
export const previewCampaign = async (params: PreviewCampaignParams, options?: RequestInit): Promise<{
    data: EligibilityPreview;
}> =>{
    const res = await fetch(`/api/campaigns/${params.campaign_id}/preview`, {
        ...options,
        method: "POST"
    });
    if (!res.ok) {
        const body = await res.text();
        let parsed: unknown;
        try {
            parsed = JSON.parse(body);
        } catch  {
            parsed = body;
        }
        throw new ApiError(res.status, res.statusText, parsed);
    }
    return {
        data: await res.json()
    };
};
export function usePreviewCampaign(options?: {
    mutation?: UseMutationOptions<{
        data: EligibilityPreview;
    }, ApiError, {
        params: PreviewCampaignParams;
    }>;
}) {
    return useMutation({
        mutationFn: (vars)=>previewCampaign(vars.params),
        ...options?.mutation
    });
}
export interface RejectCampaignParams {
    campaign_id: string;
    "X-Forwarded-Host"?: string | null;
    "X-Forwarded-Preferred-Username"?: string | null;
    "X-Forwarded-User"?: string | null;
    "X-Forwarded-Email"?: string | null;
    "X-Request-Id"?: string | null;
    "X-Forwarded-Access-Token"?: string | null;
}
export const rejectCampaign = async (params: RejectCampaignParams, data: ApprovalActionIn | null, options?: RequestInit): Promise<{
    data: CampaignOut;
}> =>{
    const res = await fetch(`/api/campaigns/${params.campaign_id}/reject`, {
        ...options,
        method: "POST",
        headers: {
            "Content-Type": "application/json",
            ...(params?.["X-Forwarded-Host"] != null && {
                "X-Forwarded-Host": params["X-Forwarded-Host"]
            }),
            ...(params?.["X-Forwarded-Preferred-Username"] != null && {
                "X-Forwarded-Preferred-Username": params["X-Forwarded-Preferred-Username"]
            }),
            ...(params?.["X-Forwarded-User"] != null && {
                "X-Forwarded-User": params["X-Forwarded-User"]
            }),
            ...(params?.["X-Forwarded-Email"] != null && {
                "X-Forwarded-Email": params["X-Forwarded-Email"]
            }),
            ...(params?.["X-Request-Id"] != null && {
                "X-Request-Id": params["X-Request-Id"]
            }),
            ...(params?.["X-Forwarded-Access-Token"] != null && {
                "X-Forwarded-Access-Token": params["X-Forwarded-Access-Token"]
            }),
            ...options?.headers
        },
        body: JSON.stringify(data)
    });
    if (!res.ok) {
        const body = await res.text();
        let parsed: unknown;
        try {
            parsed = JSON.parse(body);
        } catch  {
            parsed = body;
        }
        throw new ApiError(res.status, res.statusText, parsed);
    }
    return {
        data: await res.json()
    };
};
export function useRejectCampaign(options?: {
    mutation?: UseMutationOptions<{
        data: CampaignOut;
    }, ApiError, {
        params: RejectCampaignParams;
        data: ApprovalActionIn | null;
    }>;
}) {
    return useMutation({
        mutationFn: (vars)=>rejectCampaign(vars.params, vars.data),
        ...options?.mutation
    });
}
export interface ScheduleCampaignParams {
    campaign_id: string;
    "X-Forwarded-Host"?: string | null;
    "X-Forwarded-Preferred-Username"?: string | null;
    "X-Forwarded-User"?: string | null;
    "X-Forwarded-Email"?: string | null;
    "X-Request-Id"?: string | null;
    "X-Forwarded-Access-Token"?: string | null;
}
export const scheduleCampaign = async (params: ScheduleCampaignParams, data: ScheduleIn, options?: RequestInit): Promise<{
    data: CampaignOut;
}> =>{
    const res = await fetch(`/api/campaigns/${params.campaign_id}/schedule`, {
        ...options,
        method: "POST",
        headers: {
            "Content-Type": "application/json",
            ...(params?.["X-Forwarded-Host"] != null && {
                "X-Forwarded-Host": params["X-Forwarded-Host"]
            }),
            ...(params?.["X-Forwarded-Preferred-Username"] != null && {
                "X-Forwarded-Preferred-Username": params["X-Forwarded-Preferred-Username"]
            }),
            ...(params?.["X-Forwarded-User"] != null && {
                "X-Forwarded-User": params["X-Forwarded-User"]
            }),
            ...(params?.["X-Forwarded-Email"] != null && {
                "X-Forwarded-Email": params["X-Forwarded-Email"]
            }),
            ...(params?.["X-Request-Id"] != null && {
                "X-Request-Id": params["X-Request-Id"]
            }),
            ...(params?.["X-Forwarded-Access-Token"] != null && {
                "X-Forwarded-Access-Token": params["X-Forwarded-Access-Token"]
            }),
            ...options?.headers
        },
        body: JSON.stringify(data)
    });
    if (!res.ok) {
        const body = await res.text();
        let parsed: unknown;
        try {
            parsed = JSON.parse(body);
        } catch  {
            parsed = body;
        }
        throw new ApiError(res.status, res.statusText, parsed);
    }
    return {
        data: await res.json()
    };
};
export function useScheduleCampaign(options?: {
    mutation?: UseMutationOptions<{
        data: CampaignOut;
    }, ApiError, {
        params: ScheduleCampaignParams;
        data: ScheduleIn;
    }>;
}) {
    return useMutation({
        mutationFn: (vars)=>scheduleCampaign(vars.params, vars.data),
        ...options?.mutation
    });
}
export interface SubmitCampaignParams {
    campaign_id: string;
    "X-Forwarded-Host"?: string | null;
    "X-Forwarded-Preferred-Username"?: string | null;
    "X-Forwarded-User"?: string | null;
    "X-Forwarded-Email"?: string | null;
    "X-Request-Id"?: string | null;
    "X-Forwarded-Access-Token"?: string | null;
}
export const submitCampaign = async (params: SubmitCampaignParams, options?: RequestInit): Promise<{
    data: CampaignOut;
}> =>{
    const res = await fetch(`/api/campaigns/${params.campaign_id}/submit`, {
        ...options,
        method: "POST",
        headers: {
            ...(params?.["X-Forwarded-Host"] != null && {
                "X-Forwarded-Host": params["X-Forwarded-Host"]
            }),
            ...(params?.["X-Forwarded-Preferred-Username"] != null && {
                "X-Forwarded-Preferred-Username": params["X-Forwarded-Preferred-Username"]
            }),
            ...(params?.["X-Forwarded-User"] != null && {
                "X-Forwarded-User": params["X-Forwarded-User"]
            }),
            ...(params?.["X-Forwarded-Email"] != null && {
                "X-Forwarded-Email": params["X-Forwarded-Email"]
            }),
            ...(params?.["X-Request-Id"] != null && {
                "X-Request-Id": params["X-Request-Id"]
            }),
            ...(params?.["X-Forwarded-Access-Token"] != null && {
                "X-Forwarded-Access-Token": params["X-Forwarded-Access-Token"]
            }),
            ...options?.headers
        }
    });
    if (!res.ok) {
        const body = await res.text();
        let parsed: unknown;
        try {
            parsed = JSON.parse(body);
        } catch  {
            parsed = body;
        }
        throw new ApiError(res.status, res.statusText, parsed);
    }
    return {
        data: await res.json()
    };
};
export function useSubmitCampaign(options?: {
    mutation?: UseMutationOptions<{
        data: CampaignOut;
    }, ApiError, {
        params: SubmitCampaignParams;
    }>;
}) {
    return useMutation({
        mutationFn: (vars)=>submitCampaign(vars.params),
        ...options?.mutation
    });
}
export interface CurrentUserParams {
    "X-Forwarded-Host"?: string | null;
    "X-Forwarded-Preferred-Username"?: string | null;
    "X-Forwarded-User"?: string | null;
    "X-Forwarded-Email"?: string | null;
    "X-Request-Id"?: string | null;
    "X-Forwarded-Access-Token"?: string | null;
}
export const currentUser = async (params?: CurrentUserParams, options?: RequestInit): Promise<{
    data: User;
}> =>{
    const res = await fetch("/api/current-user", {
        ...options,
        method: "GET",
        headers: {
            ...(params?.["X-Forwarded-Host"] != null && {
                "X-Forwarded-Host": params["X-Forwarded-Host"]
            }),
            ...(params?.["X-Forwarded-Preferred-Username"] != null && {
                "X-Forwarded-Preferred-Username": params["X-Forwarded-Preferred-Username"]
            }),
            ...(params?.["X-Forwarded-User"] != null && {
                "X-Forwarded-User": params["X-Forwarded-User"]
            }),
            ...(params?.["X-Forwarded-Email"] != null && {
                "X-Forwarded-Email": params["X-Forwarded-Email"]
            }),
            ...(params?.["X-Request-Id"] != null && {
                "X-Request-Id": params["X-Request-Id"]
            }),
            ...(params?.["X-Forwarded-Access-Token"] != null && {
                "X-Forwarded-Access-Token": params["X-Forwarded-Access-Token"]
            }),
            ...options?.headers
        }
    });
    if (!res.ok) {
        const body = await res.text();
        let parsed: unknown;
        try {
            parsed = JSON.parse(body);
        } catch  {
            parsed = body;
        }
        throw new ApiError(res.status, res.statusText, parsed);
    }
    return {
        data: await res.json()
    };
};
export const currentUserKey = (params?: CurrentUserParams)=>{
    return [
        "/api/current-user",
        params
    ] as const;
};
export function useCurrentUser<TData = {
    data: User;
}>(options?: {
    params?: CurrentUserParams;
    query?: Omit<UseQueryOptions<{
        data: User;
    }, ApiError, TData>, "queryKey" | "queryFn">;
}) {
    return useQuery({
        queryKey: currentUserKey(options?.params),
        queryFn: ()=>currentUser(options?.params),
        ...options?.query
    });
}
export function useCurrentUserSuspense<TData = {
    data: User;
}>(options?: {
    params?: CurrentUserParams;
    query?: Omit<UseSuspenseQueryOptions<{
        data: User;
    }, ApiError, TData>, "queryKey" | "queryFn">;
}) {
    return useSuspenseQuery({
        queryKey: currentUserKey(options?.params),
        queryFn: ()=>currentUser(options?.params),
        ...options?.query
    });
}
export const getDashboard = async (options?: RequestInit): Promise<{
    data: DashboardStats;
}> =>{
    const res = await fetch("/api/dashboard", {
        ...options,
        method: "GET"
    });
    if (!res.ok) {
        const body = await res.text();
        let parsed: unknown;
        try {
            parsed = JSON.parse(body);
        } catch  {
            parsed = body;
        }
        throw new ApiError(res.status, res.statusText, parsed);
    }
    return {
        data: await res.json()
    };
};
export const getDashboardKey = ()=>{
    return [
        "/api/dashboard"
    ] as const;
};
export function useGetDashboard<TData = {
    data: DashboardStats;
}>(options?: {
    query?: Omit<UseQueryOptions<{
        data: DashboardStats;
    }, ApiError, TData>, "queryKey" | "queryFn">;
}) {
    return useQuery({
        queryKey: getDashboardKey(),
        queryFn: ()=>getDashboard(),
        ...options?.query
    });
}
export function useGetDashboardSuspense<TData = {
    data: DashboardStats;
}>(options?: {
    query?: Omit<UseSuspenseQueryOptions<{
        data: DashboardStats;
    }, ApiError, TData>, "queryKey" | "queryFn">;
}) {
    return useSuspenseQuery({
        queryKey: getDashboardKey(),
        queryFn: ()=>getDashboard(),
        ...options?.query
    });
}
export interface ListOffersParams {
    active_only?: boolean;
}
export const listOffers = async (params?: ListOffersParams, options?: RequestInit): Promise<{
    data: OfferOut[];
}> =>{
    const searchParams = new URLSearchParams();
    if (params?.active_only != null) searchParams.set("active_only", String(params?.active_only));
    const queryString = searchParams.toString();
    const url = queryString ? `/api/offers?${queryString}` : "/api/offers";
    const res = await fetch(url, {
        ...options,
        method: "GET"
    });
    if (!res.ok) {
        const body = await res.text();
        let parsed: unknown;
        try {
            parsed = JSON.parse(body);
        } catch  {
            parsed = body;
        }
        throw new ApiError(res.status, res.statusText, parsed);
    }
    return {
        data: await res.json()
    };
};
export const listOffersKey = (params?: ListOffersParams)=>{
    return [
        "/api/offers",
        params
    ] as const;
};
export function useListOffers<TData = {
    data: OfferOut[];
}>(options?: {
    params?: ListOffersParams;
    query?: Omit<UseQueryOptions<{
        data: OfferOut[];
    }, ApiError, TData>, "queryKey" | "queryFn">;
}) {
    return useQuery({
        queryKey: listOffersKey(options?.params),
        queryFn: ()=>listOffers(options?.params),
        ...options?.query
    });
}
export function useListOffersSuspense<TData = {
    data: OfferOut[];
}>(options?: {
    params?: ListOffersParams;
    query?: Omit<UseSuspenseQueryOptions<{
        data: OfferOut[];
    }, ApiError, TData>, "queryKey" | "queryFn">;
}) {
    return useSuspenseQuery({
        queryKey: listOffersKey(options?.params),
        queryFn: ()=>listOffers(options?.params),
        ...options?.query
    });
}
export const getSystemConfig = async (options?: RequestInit): Promise<{
    data: SystemConfigOut;
}> =>{
    const res = await fetch("/api/system/config", {
        ...options,
        method: "GET"
    });
    if (!res.ok) {
        const body = await res.text();
        let parsed: unknown;
        try {
            parsed = JSON.parse(body);
        } catch  {
            parsed = body;
        }
        throw new ApiError(res.status, res.statusText, parsed);
    }
    return {
        data: await res.json()
    };
};
export const getSystemConfigKey = ()=>{
    return [
        "/api/system/config"
    ] as const;
};
export function useGetSystemConfig<TData = {
    data: SystemConfigOut;
}>(options?: {
    query?: Omit<UseQueryOptions<{
        data: SystemConfigOut;
    }, ApiError, TData>, "queryKey" | "queryFn">;
}) {
    return useQuery({
        queryKey: getSystemConfigKey(),
        queryFn: ()=>getSystemConfig(),
        ...options?.query
    });
}
export function useGetSystemConfigSuspense<TData = {
    data: SystemConfigOut;
}>(options?: {
    query?: Omit<UseSuspenseQueryOptions<{
        data: SystemConfigOut;
    }, ApiError, TData>, "queryKey" | "queryFn">;
}) {
    return useSuspenseQuery({
        queryKey: getSystemConfigKey(),
        queryFn: ()=>getSystemConfig(),
        ...options?.query
    });
}
export const version = async (options?: RequestInit): Promise<{
    data: VersionOut;
}> =>{
    const res = await fetch("/api/version", {
        ...options,
        method: "GET"
    });
    if (!res.ok) {
        const body = await res.text();
        let parsed: unknown;
        try {
            parsed = JSON.parse(body);
        } catch  {
            parsed = body;
        }
        throw new ApiError(res.status, res.statusText, parsed);
    }
    return {
        data: await res.json()
    };
};
export const versionKey = ()=>{
    return [
        "/api/version"
    ] as const;
};
export function useVersion<TData = {
    data: VersionOut;
}>(options?: {
    query?: Omit<UseQueryOptions<{
        data: VersionOut;
    }, ApiError, TData>, "queryKey" | "queryFn">;
}) {
    return useQuery({
        queryKey: versionKey(),
        queryFn: ()=>version(),
        ...options?.query
    });
}
export function useVersionSuspense<TData = {
    data: VersionOut;
}>(options?: {
    query?: Omit<UseSuspenseQueryOptions<{
        data: VersionOut;
    }, ApiError, TData>, "queryKey" | "queryFn">;
}) {
    return useSuspenseQuery({
        queryKey: versionKey(),
        queryFn: ()=>version(),
        ...options?.query
    });
}
export const health = async (options?: RequestInit): Promise<{
    data: unknown;
}> =>{
    const res = await fetch("/health", {
        ...options,
        method: "GET"
    });
    if (!res.ok) {
        const body = await res.text();
        let parsed: unknown;
        try {
            parsed = JSON.parse(body);
        } catch  {
            parsed = body;
        }
        throw new ApiError(res.status, res.statusText, parsed);
    }
    return {
        data: await res.json()
    };
};
export const healthKey = ()=>{
    return [
        "/health"
    ] as const;
};
export function useHealth<TData = {
    data: unknown;
}>(options?: {
    query?: Omit<UseQueryOptions<{
        data: unknown;
    }, ApiError, TData>, "queryKey" | "queryFn">;
}) {
    return useQuery({
        queryKey: healthKey(),
        queryFn: ()=>health(),
        ...options?.query
    });
}
export function useHealthSuspense<TData = {
    data: unknown;
}>(options?: {
    query?: Omit<UseSuspenseQueryOptions<{
        data: unknown;
    }, ApiError, TData>, "queryKey" | "queryFn">;
}) {
    return useSuspenseQuery({
        queryKey: healthKey(),
        queryFn: ()=>health(),
        ...options?.query
    });
}
