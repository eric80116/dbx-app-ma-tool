"""Real time-based scheduling via one-time Databricks jobs.

When a campaign is scheduled, the App service principal creates a tiny **one-time wrapper
job** whose single `run_job_task` triggers the bundle-defined dispatcher job
(`ma_app_dispatch_job`, tagged `ma_app=<dispatch_job_tag>`) with the campaign id, armed by a
year-qualified Quartz one-shot cron at the scheduled UTC time. The dispatcher runs
`CampaignService.dispatch()` in-job (same mock providers + guardrails).

Wrapper jobs are named `ma-app-dispatch-<campaign_id>` and tagged so the reconcile job and
teardown can find and remove them. Nothing here assumes anything about CMEG.
"""

from __future__ import annotations

from datetime import datetime, timezone

from databricks.sdk import WorkspaceClient
from databricks.sdk.service.jobs import (
    CronSchedule,
    PauseStatus,
    RunJobTask,
    Task,
)

from .core._config import AppConfig, logger

WRAPPER_NAME_PREFIX = "ma-app-dispatch-"
WRAPPER_TAG_KEY = "ma_app"
WRAPPER_TAG_VALUE = "dispatch_wrapper"


class SchedulerError(RuntimeError):
    """Raised when a one-time job cannot be created (e.g. dispatcher job not deployed)."""


def _parse_utc(when: str | datetime) -> datetime:
    if isinstance(when, datetime):
        dt = when
    else:
        s = when.strip().replace("T", " ").replace("Z", "")
        dt = datetime.strptime(s[:19], "%Y-%m-%d %H:%M:%S")
    if dt.tzinfo is not None:
        dt = dt.astimezone(timezone.utc).replace(tzinfo=None)
    return dt


def to_quartz_oneshot(when: str | datetime) -> str:
    """Quartz cron that fires exactly once at `when` (UTC).

    Format: ``sec min hour day-of-month month ? year`` — the year field makes it a one-shot.
    """
    dt = _parse_utc(when)
    return f"{dt.second} {dt.minute} {dt.hour} {dt.day} {dt.month} ? {dt.year}"


def wrapper_name(campaign_id: str) -> str:
    return f"{WRAPPER_NAME_PREFIX}{campaign_id}"


class Scheduler:
    """Creates/cancels the one-time wrapper job for a campaign."""

    def __init__(self, ws: WorkspaceClient, config: AppConfig):
        self._ws = ws
        self._config = config

    @property
    def enabled(self) -> bool:
        return self._config.scheduler_enabled

    def _dispatcher_job_id(self) -> int:
        """Resolve the bundle-defined dispatcher job id by its `ma_app` tag."""
        want = self._config.dispatch_job_tag
        for job in self._ws.jobs.list():
            settings = getattr(job, "settings", None)
            tags = getattr(settings, "tags", None) or {}
            if tags.get(WRAPPER_TAG_KEY) == want and job.job_id:
                return job.job_id
        raise SchedulerError(
            "Dispatcher job not found (expected a job tagged "
            f"{WRAPPER_TAG_KEY}={want}). Deploy the bundle first "
            "(scheduling is unavailable in local dev)."
        )

    def _find_wrapper(self, campaign_id: str) -> int | None:
        name = wrapper_name(campaign_id)
        for job in self._ws.jobs.list(name=name):
            if job.job_id:
                return job.job_id
        return None

    def schedule(self, campaign_id: str, scheduled_at: str | datetime) -> int:
        """Create (or replace) the one-time wrapper job. Returns its job id."""
        if not self.enabled:
            raise SchedulerError("Scheduler is disabled (MA_APP_SCHEDULER_ENABLED=false).")
        dispatcher_id = self._dispatcher_job_id()
        cron = to_quartz_oneshot(scheduled_at)

        # Replace any existing wrapper for this campaign (reschedule).
        self.cancel(campaign_id)

        created = self._ws.jobs.create(
            name=wrapper_name(campaign_id),
            tags={WRAPPER_TAG_KEY: WRAPPER_TAG_VALUE, "campaign_id": campaign_id},
            max_concurrent_runs=1,
            tasks=[
                Task(
                    task_key="trigger_dispatch",
                    run_job_task=RunJobTask(
                        job_id=dispatcher_id,
                        job_parameters={"campaign_id": campaign_id},
                    ),
                )
            ],
            schedule=CronSchedule(
                quartz_cron_expression=cron,
                timezone_id="UTC",
                pause_status=PauseStatus.UNPAUSED,
            ),
        )
        if created.job_id is None:
            raise SchedulerError("Job creation returned no job id.")
        logger.info(
            f"Scheduled one-time dispatch job {created.job_id} for {campaign_id} "
            f"(cron '{cron}' UTC)"
        )
        return created.job_id

    def cancel(self, campaign_id: str) -> bool:
        """Delete the wrapper job for a campaign if present. Best-effort."""
        job_id = self._find_wrapper(campaign_id)
        if job_id is None:
            return False
        try:
            self._ws.jobs.delete(job_id)
            logger.info(f"Removed one-time dispatch job {job_id} for {campaign_id}")
            return True
        except Exception as exc:  # pragma: no cover - depends on live perms
            logger.warning(f"Could not delete wrapper job {job_id}: {exc}")
            return False
