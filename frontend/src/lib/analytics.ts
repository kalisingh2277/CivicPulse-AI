import { api } from "./api";

export type HeatCell = { lng: number; lat: number; weight: number };
export type TrendPoint = { week: string; new_issues: number; resolved_issues: number };
export type DepartmentRow = {
  department_id: number;
  name: string;
  open_count: number;
  total: number;
  sla_breach_pct: number;
  reopened_pct: number;
  median_resolution_hours: number | null;
};
export type PublicStats = {
  total_issues: number;
  open_issues: number;
  resolved_issues: number;
  resolved_pct: number;
  top_categories: { name: string; count: number }[];
};
export type PublicIssue = {
  public_code: string;
  title: string;
  status: string;
  category: string;
  ward: string;
  lng: number;
  lat: number;
  created_at: string;
};

export const analyticsApi = {
  heatmap: (categoryId?: number) =>
    api.get<HeatCell[]>(`/analytics/heatmap${categoryId ? `?category_id=${categoryId}` : ""}`),
  trends: (weeks = 26) => api.get<TrendPoint[]>(`/analytics/trends?weeks=${weeks}`),
  departments: () => api.get<DepartmentRow[]>("/analytics/departments"),
  publicStats: () => api.get<PublicStats>("/public/stats"),
  publicIssues: (limit = 200) => api.get<PublicIssue[]>(`/public/issues?limit=${limit}`),
};
