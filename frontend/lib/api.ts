const BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

async function apiFetch<T>(path: string, options?: RequestInit): Promise<T> {
  const res = await fetch(`${BASE_URL}${path}`, {
    ...options,
    headers: { "Content-Type": "application/json", ...options?.headers },
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

export interface Store {
  id: number;
  name: string;
  url: string;
  country: string;
  active: boolean;
}

export interface Stats {
  total_runs: number;
  total_products: number;
  total_stores: number;
  last_run_date: string | null;
  last_run_status: string | null;
}

export const api = {
  triggerRun: () => apiFetch<{ message: string }>("/api/runs/trigger", { method: "POST" }),
  cancelRun: (id: number) => apiFetch<{ message: string }>(`/api/runs/${id}/cancel`, { method: "POST" }),
  getRuns: (limit = 20) => apiFetch<Run[]>(`/api/runs?limit=${limit}`),
  getRun: (id: number) => apiFetch<Run>(`/api/runs/${id}`),
  getRunProducts: (runId: number, storeId?: number) =>
    apiFetch<Product[]>(`/api/runs/${runId}/products${storeId ? `?store_id=${storeId}` : ""}`),
  getRunAnalyses: (runId: number) => apiFetch<TrendAnalysis[]>(`/api/runs/${runId}/analyses`),
  getReports: (limit = 10) => apiFetch<Report[]>(`/api/reports?limit=${limit}`),
  getLatestReport: () => apiFetch<Report>("/api/reports/latest"),
  getReportByRun: (runId: number) => apiFetch<Report>(`/api/reports/${runId}`),
  getStores: () => apiFetch<Store[]>("/api/stores"),
  getStats: () => apiFetch<Stats>("/api/stats"),
};
