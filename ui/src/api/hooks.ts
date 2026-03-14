import { useQuery, useMutation } from "@tanstack/react-query";
import { apiFetch } from "./client";

export type User = { id: string; email: string; status: string };
export type Org = { id: string; name: string };
export type Project = { id: string; org_id: string; name: string };
export type ModelPricing = {
  id: string;
  provider: string;
  model: string;
  model_type: string;
  cost_per_1m_tokens: number;
  active: boolean;
  updated_at: string;
  created_at: string;
};

export type UsageOverview = {
  total_requests: number;
  total_cost_usd: number;
  total_tokens: number;
  avg_latency_ms: number;
};

export type UsageByUserItem = {
  user_id: string | null;
  email: string | null;
  requests: number;
  cost_usd: number;
  tokens: number;
  avg_latency_ms: number;
};

export type UsageByProjectItem = {
  project_id: string;
  project_name: string;
  requests: number;
  cost_usd: number;
  tokens: number;
  avg_latency_ms: number;
};

export type UsageByKeyItem = {
  api_key_id: string;
  key_prefix: string;
  owner_user_id: string | null;
  requests: number;
  cost_usd: number;
  tokens: number;
  avg_latency_ms: number;
};

export type RequestItem = {
  id: string;
  created_at: string;
  org_id: string | null;
  project_id: string;
  api_key_id: string | null;
  owner_user_id: string | null;
  provider: string;
  model: string;
  status: number;
  latency_ms: number;
  cost_usd: number;
};

export type Providers = {
  providers: { provider: string; enabled: boolean }[];
  rate_limit_rpm: number;
};

export type CompareProviderItem = {
  provider: string;
  model: string;
};

export type CompareResponseItem = {
  provider: string;
  model: string;
  status: string;
  latency_ms: number;
  prompt_tokens: number;
  completion_tokens: number;
  total_tokens: number;
  cost_usd: number;
  response: string | null;
  error_message: string | null;
};

export type OverviewResponse = {
  total_requests: number;
  success_rate: number;
  total_cost_usd: number;
  avg_latency_ms: number;
  trend: { date: string; value: number }[];
};

export type ApiKey = {
  id: string;
  key_prefix: string;
  tag: string | null;
  status: string;
  project_id: string;
  owner_user_id: string | null;
  created_by_user_id: string;
  created_at: string;
  last_used_at: string | null;
};

export type ApiKeyCreate = {
  id: string;
  key: string;
  key_prefix: string;
  tag: string | null;
  status: string;
  project_id: string;
  owner_user_id: string | null;
  created_by_user_id: string;
  created_at: string;
};

export const useMe = () =>
  useQuery({
    queryKey: ["me"],
    queryFn: () => apiFetch<User>("/auth/me"),
    retry: false
  });

export const useOrg = () =>
  useQuery({
    queryKey: ["org"],
    queryFn: () => apiFetch<Org>("/orgs/me")
  });

export const useProjects = () =>
  useQuery({
    queryKey: ["projects"],
    queryFn: () => apiFetch<Project[]>("/projects")
  });

export const usePricing = () =>
  useQuery({
    queryKey: ["pricing"],
    queryFn: () => apiFetch<ModelPricing[]>("/pricing")
  });

export const useCreatePricing = () =>
  useMutation({
    mutationFn: (payload: Omit<ModelPricing, "id" | "updated_at" | "created_at">) =>
      apiFetch<ModelPricing>("/pricing", { method: "POST", body: JSON.stringify(payload) })
  });

export const useUpdatePricing = () =>
  useMutation({
    mutationFn: ({ id, ...payload }: { id: string } & Partial<Omit<ModelPricing, "id" | "updated_at" | "created_at">>) =>
      apiFetch<ModelPricing>(`/pricing/${id}`, {
        method: "PATCH",
        body: JSON.stringify(payload)
      })
  });

export const useDeletePricing = () =>
  useMutation({
    mutationFn: (pricingId: string) => apiFetch(`/pricing/${pricingId}`, { method: "DELETE" })
  });

export const useCreateProject = () =>
  useMutation({
    mutationFn: (payload: { name: string }) =>
      apiFetch<Project>("/projects", { method: "POST", body: JSON.stringify(payload) })
  });

export const useUpdateProject = () =>
  useMutation({
    mutationFn: (payload: { projectId: string; name: string }) =>
      apiFetch<Project>(`/projects/${payload.projectId}`, {
        method: "PATCH",
        body: JSON.stringify({ name: payload.name })
      })
  });

export const useUsageOverview = (projectId?: string) =>
  useQuery({
    queryKey: ["usage-overview", projectId],
    queryFn: () => {
      const qs = projectId ? `?project_id=${projectId}` : "";
      return apiFetch<UsageOverview>(`/usage/overview${qs}`);
    }
  });

export const useUsageByUser = () =>
  useQuery({
    queryKey: ["usage-by-user"],
    queryFn: () => apiFetch<{ items: UsageByUserItem[] }>("/usage/by-user")
  });

export const useUsageByProject = () =>
  useQuery({
    queryKey: ["usage-by-project"],
    queryFn: () => apiFetch<{ items: UsageByProjectItem[] }>("/usage/by-project")
  });

export const useUsageByKey = (projectId?: string) =>
  useQuery({
    queryKey: ["usage-by-key", projectId],
    queryFn: () => {
      if (!projectId) {
        return Promise.resolve({ items: [] as UsageByKeyItem[] });
      }
      return apiFetch<{ items: UsageByKeyItem[] }>(`/usage/by-key?project_id=${projectId}`);
    }
  });

export const useRequests = (filters?: {
  projectId?: string;
  keyId?: string;
}) =>
  useQuery({
    queryKey: ["requests", filters],
    queryFn: () => {
      const params = new URLSearchParams();
      if (filters?.projectId) params.set("project_id", filters.projectId);
      if (filters?.keyId) params.set("key_id", filters.keyId);
      const qs = params.toString();
      return apiFetch<{ items: RequestItem[] }>(`/requests${qs ? `?${qs}` : ""}`);
    }
  });

export const useOverview = () =>
  useQuery({
    queryKey: ["overview"],
    queryFn: () => apiFetch<OverviewResponse>("/dashboard/overview")
  });

export const useProviders = () =>
  useQuery({
    queryKey: ["providers"],
    queryFn: () => apiFetch<Providers>("/dashboard/providers")
  });

export const useCompareModels = () =>
  useMutation({
    mutationFn: (payload: { prompt: string; providers: CompareProviderItem[]; fallback?: boolean | null }) =>
      apiFetch<{ items: CompareResponseItem[] }>("/test/compare", { method: "POST", body: JSON.stringify(payload) })
  });

export const useKeys = () =>
  useQuery({
    queryKey: ["keys"],
    queryFn: () => apiFetch<ApiKey[]>("/keys")
  });

export const useCreateKey = () =>
  useMutation({
    mutationFn: (payload: { project_id: string; tag?: string | null }) =>
      apiFetch<ApiKeyCreate>("/keys", { method: "POST", body: JSON.stringify(payload) })
  });

export const useRevokeKey = () =>
  useMutation({
    mutationFn: (keyId: string) => apiFetch(`/keys/${keyId}/revoke`, { method: "POST" })
  });

export const useDeleteKey = () =>
  useMutation({
    mutationFn: (keyId: string) => apiFetch(`/keys/${keyId}`, { method: "DELETE" })
  });

export const useLogin = () =>
  useMutation({
    mutationFn: (payload: { email: string; password: string }) =>
      apiFetch<User>("/auth/login", { method: "POST", body: JSON.stringify(payload) })
  });

export const useLogout = () =>
  useMutation({
    mutationFn: () => apiFetch("/auth/logout", { method: "POST" })
  });
