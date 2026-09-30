"""SQL Warehouse data-access helper.

All Databricks data access goes through this helper using the **App service
principal** (`Dependencies.Client`). Identifiers (catalog/schema/table) come from
config and are interpolated; all *values* are passed as bound parameters to avoid
SQL injection.
"""

from __future__ import annotations

import time
from decimal import Decimal
from typing import Annotated, Any, Sequence, TypeAlias

from databricks.sdk import WorkspaceClient
from databricks.sdk.service.sql import (
    ColumnInfoTypeName,
    ExecuteStatementRequestOnWaitTimeout,
    StatementParameterListItem,
    StatementState,
)
from fastapi import Depends

from .core import Dependencies
from .core._config import AppConfig, logger

_TERMINAL_OK = {StatementState.SUCCEEDED}
_TERMINAL_BAD = {StatementState.FAILED, StatementState.CANCELED, StatementState.CLOSED}

_INT_TYPES = {
    ColumnInfoTypeName.INT,
    ColumnInfoTypeName.LONG,
    ColumnInfoTypeName.SHORT,
    ColumnInfoTypeName.BYTE,
}
_FLOAT_TYPES = {ColumnInfoTypeName.FLOAT, ColumnInfoTypeName.DOUBLE}


class SqlError(RuntimeError):
    """Raised when a SQL statement fails on the warehouse."""


def _coerce(value: str | None, type_name: ColumnInfoTypeName | None) -> Any:
    if value is None:
        return None
    if type_name in _INT_TYPES:
        return int(value)
    if type_name in _FLOAT_TYPES:
        return float(value)
    if type_name == ColumnInfoTypeName.DECIMAL:
        return float(Decimal(value))
    if type_name == ColumnInfoTypeName.BOOLEAN:
        return value.lower() == "true"
    # STRING, TIMESTAMP, DATE, etc. -> keep as string (ISO for temporal types)
    return value


class Db:
    """Thin wrapper over the SQL Statement Execution API."""

    def __init__(self, ws: WorkspaceClient, config: AppConfig):
        self._ws = ws
        self._config = config
        # Prefer explicit config; otherwise auto-resolve a warehouse from the workspace.
        self._warehouse_id = config.warehouse_id or self._resolve_warehouse(ws, config)
        if not self._warehouse_id:
            raise SqlError(
                "No SQL warehouse configured and none could be auto-resolved. "
                "Set MA_APP_WAREHOUSE_ID (env / bundle variable) or run "
                "scripts/preflight.sh."
            )

    @staticmethod
    def _resolve_warehouse(ws: WorkspaceClient, config: AppConfig) -> str:
        """Auto-detect a warehouse id from the workspace.

        Preference: exact name match (MA_APP_WAREHOUSE_NAME) -> a RUNNING warehouse ->
        the first available. Returns "" if none/inaccessible (caller raises).
        """
        try:
            warehouses = list(ws.warehouses.list())
        except Exception as exc:  # pragma: no cover - depends on live perms
            logger.warning(f"Could not list warehouses to auto-resolve: {exc}")
            return ""
        if not warehouses:
            return ""
        wanted = (config.warehouse_name or "").strip()
        if wanted:
            for w in warehouses:
                if (w.name or "") == wanted and w.id:
                    return w.id
        for w in warehouses:
            if str(getattr(w, "state", "")).upper().endswith("RUNNING") and w.id:
                return w.id
        return warehouses[0].id or ""

    @property
    def config(self) -> AppConfig:
        return self._config

    @property
    def ws(self) -> WorkspaceClient:
        return self._ws

    def execute(
        self,
        statement: str,
        params: dict[str, Any] | None = None,
        *,
        catalog: str | None = None,
        schema: str | None = None,
    ) -> list[dict[str, Any]]:
        """Run a statement and return rows as dicts. Empty list for non-SELECT."""
        sdk_params: list[StatementParameterListItem] | None = None
        if params:
            sdk_params = [
                StatementParameterListItem(
                    name=k,
                    value=None if v is None else str(v),
                    type=_sql_type_for(v),
                )
                for k, v in params.items()
            ]

        resp = self._ws.statement_execution.execute_statement(
            statement=statement,
            warehouse_id=self._warehouse_id,
            catalog=catalog,
            schema=schema,
            parameters=sdk_params,
            wait_timeout="30s",
            on_wait_timeout=ExecuteStatementRequestOnWaitTimeout.CONTINUE,
        )

        statement_id = resp.statement_id
        state = resp.status.state if resp.status else None
        # Poll until terminal.
        while state not in _TERMINAL_OK and state not in _TERMINAL_BAD:
            time.sleep(1.0)
            assert statement_id is not None
            resp = self._ws.statement_execution.get_statement(statement_id)
            state = resp.status.state if resp.status else None

        if state in _TERMINAL_BAD:
            err = resp.status.error if resp.status else None
            msg = err.message if err else "unknown error"
            logger.error(f"SQL failed ({state}): {msg}\nstatement={statement[:500]}")
            raise SqlError(f"SQL statement {state}: {msg}")

        return _rows(resp)


def _rows(resp: Any) -> list[dict[str, Any]]:
    manifest = resp.manifest
    result = resp.result
    if manifest is None or manifest.schema is None or manifest.schema.columns is None:
        return []
    columns = manifest.schema.columns
    out: list[dict[str, Any]] = []
    data = result.data_array if result and result.data_array else []
    for raw_row in data:
        row: dict[str, Any] = {}
        for col, cell in zip(columns, raw_row):
            row[col.name] = _coerce(cell, col.type_name)
        out.append(row)
    return out


def _sql_type_for(value: Any) -> str:
    if isinstance(value, bool):
        return "BOOLEAN"
    if isinstance(value, int):
        return "BIGINT"
    if isinstance(value, float):
        return "DOUBLE"
    return "STRING"


class Ts:
    """Marker: render this ISO string as CAST('...' AS TIMESTAMP) in a VALUES clause."""

    __slots__ = ("iso",)

    def __init__(self, iso: str | None):
        self.iso = iso


class Dt:
    """Marker: render this string as CAST('...' AS DATE) in a VALUES clause."""

    __slots__ = ("iso",)

    def __init__(self, iso: str | None):
        self.iso = iso


def sql_literal(value: Any) -> str:
    """Render a Python value as a SQL literal (for bulk INSERT VALUES in setup only).

    Only used by trusted setup/seed code with synthetic/derived data — never with raw
    request input.
    """
    if value is None:
        return "NULL"
    if isinstance(value, Ts):
        if value.iso is None:
            return "NULL"
        return f"CAST('{value.iso}' AS TIMESTAMP)"
    if isinstance(value, Dt):
        if value.iso is None:
            return "NULL"
        return f"CAST('{value.iso}' AS DATE)"
    if isinstance(value, bool):
        return "TRUE" if value else "FALSE"
    if isinstance(value, (int, float, Decimal)):
        return str(value)
    escaped = str(value).replace("\\", "\\\\").replace("'", "\\'")
    return f"'{escaped}'"


def bulk_insert_values(rows: Sequence[Sequence[Any]]) -> str:
    """Render a VALUES clause body: (a,b),(c,d),..."""
    return ",\n".join(
        "(" + ", ".join(sql_literal(v) for v in row) + ")" for row in rows
    )


def _get_db(ws: Dependencies.Client, config: Dependencies.Config) -> Db:
    return Db(ws, config)


DbDependency: TypeAlias = Annotated[Db, Depends(_get_db)]
