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
    reopened_pct: float
    median_resolution_hours: float | None
