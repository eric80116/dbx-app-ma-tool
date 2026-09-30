"""FastAPI application entrypoint."""

from __future__ import annotations

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from .audience.interface import AudienceNotFound, AudienceSourceUnavailable
from .core import create_app
from .db import SqlError
from .domain.state_machine import InvalidTransition
from .routes.health import health_router
from .router import router
from .services import CampaignError

app = create_app(routers=[router, health_router])


def _error(status: int, code: str, message: str, details: dict | None = None) -> JSONResponse:
    return JSONResponse(
        status_code=status,
        content={"error_code": code, "message": message, "details": details or {}},
    )


@app.exception_handler(AudienceNotFound)
async def _audience_not_found(_: Request, exc: AudienceNotFound):
    return _error(404, "AUDIENCE_NOT_FOUND", str(exc), {"audience_id": exc.audience_id})


@app.exception_handler(AudienceSourceUnavailable)
async def _audience_unavailable(_: Request, exc: AudienceSourceUnavailable):
    return _error(502, "AUDIENCE_SOURCE_UNAVAILABLE", str(exc))


@app.exception_handler(InvalidTransition)
async def _invalid_transition(_: Request, exc: InvalidTransition):
    return _error(
        409,
        "INVALID_CAMPAIGN_STATE",
        str(exc),
        {"current": exc.current, "target": exc.target},
    )


@app.exception_handler(CampaignError)
async def _campaign_error(_: Request, exc: CampaignError):
    status = 409 if exc.error_code == "INVALID_CAMPAIGN_STATE" else 400
    return _error(status, exc.error_code, exc.message, exc.details)


@app.exception_handler(SqlError)
async def _sql_error(_: Request, exc: SqlError):
    return _error(500, "SQL_ERROR", str(exc))


@app.exception_handler(ValueError)
async def _value_error(_: Request, exc: ValueError):
    return _error(400, "VALIDATION_ERROR", str(exc))
