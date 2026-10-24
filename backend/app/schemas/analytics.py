from pydantic import BaseModel


class HeatCell(BaseModel):
    lng: float
    lat: float
    weight: int


class TrendPoint(BaseModel):
    week: str
    new_issues: int
    resolved_issues: int


class DepartmentRow(BaseModel):
    department_id: int
    name: str
    open_count: int
    total: int
    sla_breach_pct: float
    reopened_pct: float
    median_resolution_hours: float | None


class CategoryCount(BaseModel):
    name: str
    count: int


class PublicStats(BaseModel):
    total_issues: int
    open_issues: int
    resolved_issues: int
    resolved_pct: float
    top_categories: list[CategoryCount]


class PublicIssue(BaseModel):
    public_code: str
    title: str
    status: str
    category: str
    ward: str
    lng: float
    lat: float
    created_at: str
