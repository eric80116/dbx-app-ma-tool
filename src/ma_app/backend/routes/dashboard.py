"""Dashboard summary endpoint (all metrics computed from Delta tables)."""

from __future__ import annotations

from ..core import create_router
from ..db import DbDependency
from ..models import DashboardStats
from ..services import DashboardService

router = create_router()


@router.get("/dashboard", response_model=DashboardStats, operation_id="getDashboard")
def get_dashboard(db: DbDependency):
    return DashboardService(db).stats()
