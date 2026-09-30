"""Health and system-config endpoints."""

from __future__ import annotations

from fastapi import APIRouter

from ..core import Dependencies, create_router
from ..models import SystemConfigOut

# Bare /health (no /api prefix) for App/deploy health checks.
health_router = APIRouter()


@health_router.get("/health", operation_id="health")
def health():
    return {"status": "ok"}


# /api/* system routes.
router = create_router()


@router.get(
    "/system/config", response_model=SystemConfigOut, operation_id="getSystemConfig"
)
def get_system_config(config: Dependencies.Config):
    return SystemConfigOut(
        app_name=config.app_name,
        target_catalog=config.target_catalog,
        app_schema=config.app_schema,
        audience_source_mode=config.audience_source_mode,
        audience_table=config.audience_table,
        warehouse_configured=bool(config.warehouse_id),
        reveal_pii_allowed=config.reveal_pii_allowed,
        scheduler_enabled=config.scheduler_enabled,
    )
