import { api } from "./api";

export type HeatCell = { lng: number; lat: number; weight: number };
export type TrendPoint = { week: string; new_issues: number; resolved_issues: number };
export type DepartmentRow = {
  department_id: number;
  name: string;
  open_count: number;
  total: number;
  reopened_pct: number;
  median_resolution_hours: number | null;
};
export type Category = { id: number; name: string };

export const analyticsApi = {
  heatmap: (categoryId?: number) =>
    api.get<HeatCell[]>(`/analytics/heatmap${categoryId ? `?category_id=${categoryId}` : ""}`),
  trends: (weeks = 26) => api.get<TrendPoint[]>(`/analytics/trends?weeks=${weeks}`),
  departments: () => api.get<DepartmentRow[]>("/analytics/departments"),
  categories: () => api.get<Category[]>("/categories"),
};
