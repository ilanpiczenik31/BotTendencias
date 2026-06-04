import { getToken } from "./auth";

const BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

async function apiFetch<T>(path: string, options?: RequestInit): Promise<T> {
  const token = getToken();
  const res = await fetch(`${BASE_URL}${path}`, {
    ...options,
    headers: {
      "Content-Type": "application/json",
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
      ...options?.headers,
    },
  });
  if (!res.ok) throw new Error(`API error ${res.status}: ${await res.text()}`);
  return res.json();
}

export interface Run {
  id: number;
  run_date: string;
  status: "pending" | "running" | "completed" | "failed";
  triggered_by: string;
  completed_at: string | null;
  error_message: string | null;
}

export interface Product {
  id: number;
  store: string;
  store_id: number;
  name: string;
  price: number | null;
  currency: string;
  image_url: string | null;
  product_url: string | null;
  section: string;
  category: string | null;
}

export interface TrendAnalysis {
  store: string;
  store_id: number;
  summary: string;
  trends: {
    top_products?: string[];
    colors?: string[];
    styles?: string[];
    categories?: string[];
    keywords?: string[];
    trend_score?: number;
    price_range?: { min: number | null; max: number | null; average: number | null; currency: string };
  };
  created_at: string;
}

export interface Report {
  id: number;
  run_id: number;
  run_date: string;
  summary: string;
  top_trends: {
    top_products?: string[];
    colors?: string[];
    styles?: string[];
    categories?: string[];
    keywords?: string[];
  };
  comparison_vs_prev: {
    store_highlights?: { store: string; highlight: string }[];
    argentina_recommendation?: string;
    vs_last_week?: string | null;
  } | null;
  created_at: string;
}

export interface Section {
  key: string;
  label: string;
  url: string;
}

export interface StoreSection {
  key: string;
  label: string;
  url: string;
}

export interface Store {
  id: number;
  name: string;
  url: string;
  country: string;
  active: boolean;
  sections: StoreSection[];
}

export interface StoreDiff {
  store: string;
  store_id: number;
  prev_run_date: string;
  total_current: number;
  total_prev: number;
  new_count: number;
  removed_count: number;
  new_products: Product[];
  removed_products: Product[];
}

export interface Stats {
  total_runs: number;
  total_products: number;
  total_stores: number;
  last_run_date: string | null;
  last_run_status: string | null;
}

export const api = {
  triggerRun: (stores?: { store: string; sections: Section[] }[]) =>
    apiFetch<{ message: string }>("/api/runs/trigger", {
      method: "POST",
      body: JSON.stringify({ stores: stores ?? null }),
    }),
  cancelRun: (id: number) => apiFetch<{ message: string }>(`/api/runs/${id}/cancel`, { method: "POST" }),
  getRegistry: () => apiFetch<{ store: string; sections: Section[] }[]>("/api/registry"),
  getRuns: (limit = 20) => apiFetch<Run[]>(`/api/runs?limit=${limit}`),
  getRun: (id: number) => apiFetch<Run>(`/api/runs/${id}`),
  getRunProducts: (runId: number, storeId?: number) =>
    apiFetch<Product[]>(`/api/runs/${runId}/products${storeId ? `?store_id=${storeId}` : ""}`),
  getRunAnalyses: (runId: number) => apiFetch<TrendAnalysis[]>(`/api/runs/${runId}/analyses`),
  getReports: (limit = 10) => apiFetch<Report[]>(`/api/reports?limit=${limit}`),
  getLatestReport: () => apiFetch<Report>("/api/reports/latest"),
  getReportByRun: (runId: number) => apiFetch<Report>(`/api/reports/${runId}`),
  getRunDiff: (runId: number) => apiFetch<StoreDiff[]>(`/api/runs/${runId}/diff`),
  getStores: () => apiFetch<Store[]>("/api/stores"),
  createStore: (data: { name: string; url: string; country: string; sections: StoreSection[] }) =>
    apiFetch<Store>("/api/stores", { method: "POST", body: JSON.stringify(data) }),
  updateStore: (id: number, data: Partial<Store>) =>
    apiFetch<Store>(`/api/stores/${id}`, { method: "PUT", body: JSON.stringify(data) }),
  deleteStore: (id: number) =>
    apiFetch<{ message: string }>(`/api/stores/${id}`, { method: "DELETE" }),
  getStats: () => apiFetch<Stats>("/api/stats"),
  login: (password: string) =>
    apiFetch<{ token: string; ok: boolean }>("/api/auth/login", {
      method: "POST",
      body: JSON.stringify({ password }),
    }),
  testUrl: (url: string) =>
    apiFetch<{
      accessible: boolean;
      estimated_products: number;
      confidence: "alta" | "media" | "baja";
      page_title: string;
      signals: Record<string, number>;
      error: string | null;
    }>("/api/stores/test-url", {
      method: "POST",
      body: JSON.stringify({ url }),
    }),
};
