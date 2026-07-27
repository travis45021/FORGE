"""FAS-034 print job lifecycle and four-click confirmation contract."""

from __future__ import annotations

from collections.abc import Mapping
from copy import deepcopy
from datetime import datetime
from secrets import token_urlsafe
from typing import Any


class JobLifecycleError(ValueError):
    """Raised when a print job transition violates user-control boundaries."""


def _utc(value: str) -> datetime:
    if not isinstance(value, str) or not value.endswith("Z"):
        raise JobLifecycleError("confirmation timestamps must be UTC and end in Z")
    try:
        return datetime.fromisoformat(value[:-1] + "+00:00")
    except ValueError as exc:
        raise JobLifecycleError(f"invalid confirmation timestamp: {value}") from exc


STATES = {
    "draft",
    "validated",
    "sliced",
    "ready",
    "final_confirmation_required",
    "upload_pending",
    "started",
    "monitoring",
    "completed",
    "failed",
    "cancelled",
}
TRANSITIONS = {
    "draft": {"validated", "cancelled"},
    "validated": {"sliced", "ready", "cancelled"},
    "sliced": {"ready", "cancelled"},
    "ready": {"final_confirmation_required", "cancelled"},
    "final_confirmation_required": {"upload_pending", "cancelled"},
    "upload_pending": {"started", "cancelled"},
    "started": {"monitoring", "failed"},
    "monitoring": {"completed", "failed", "cancelled"},
}


class PrintJobLifecycle:
    """Track print intent; never silently uploads or starts hardware."""

    def __init__(self) -> None:
        self._jobs: dict[str, dict[str, Any]] = {}
        self._history: list[dict[str, Any]] = []

    def create(self, job: Mapping[str, Any]) -> dict[str, Any]:
        item = deepcopy(dict(job))
        required = {
            "job_id",
            "artifact_id",
            "provider_id",
            "state",
            "preflight_passed",
            "live_checks_passed",
            "click_count",
        }
        missing = sorted(required - item.keys())
        if missing:
            raise JobLifecycleError(f"job missing: {', '.join(missing)}")
        if item["job_id"] in self._jobs or item["state"] != "draft":
            raise JobLifecycleError("job identity or initial state is invalid")
        if item["click_count"] != 0:
            raise JobLifecycleError("new jobs must begin with zero clicks")
        self._jobs[item["job_id"]] = item
        self._record("job.created", item["job_id"])
        return deepcopy(item)

    def click(self, job_id: str, *, action: str, actor: str) -> dict[str, Any]:
        job = self._require(job_id)
        if action not in {"upload", "configure", "review"} or not actor:
            raise JobLifecycleError(
                "preparation click requires a named actor and valid action"
            )
        if job["click_count"] >= 3 or job["state"] not in {
            "validated",
            "sliced",
            "ready",
        }:
            raise JobLifecycleError("job is not accepting preparation clicks")
        job["click_count"] += 1
        if job["click_count"] == 3:
            job["state"] = "final_confirmation_required"
        self._record("job.preparation.click", job_id)
        return deepcopy(job)

    def final_confirm(
        self,
        job_id: str,
        *,
        actor: str,
        confirmed_at: str,
        confirmation_expires_at: str,
        confirmation: bool,
        live_checks_passed: bool,
        authorization_verified: bool,
    ) -> dict[str, Any]:
        job = self._require(job_id)
        confirmed_time = _utc(confirmed_at)
        expiry_time = _utc(confirmation_expires_at)
        if expiry_time <= confirmed_time:
            raise JobLifecycleError(
                "final confirmation expiry must follow confirmation time"
            )
        if job["state"] != "final_confirmation_required" or job["click_count"] != 3:
            raise JobLifecycleError(
                "final confirmation requires exactly three preparation clicks"
            )
        if (
            not actor
            or not confirmed_at
            or confirmation is not True
            or live_checks_passed is not True
            or authorization_verified is not True
        ):
            raise JobLifecycleError(
                "final confirmation requires actor, confirmation, live checks, and authorization"
            )
        job.update(
            {
                "state": "upload_pending",
                "final_confirmed_by": actor,
                "final_confirmed_at": confirmed_at,
                "confirmation_expires_at": confirmation_expires_at,
                "confirmation_token": token_urlsafe(32),
                "live_checks_passed": True,
            }
        )
        self._record("job.final.confirmed", job_id)
        return deepcopy(job)

    def final_confirm_with_evidence(
        self,
        job_id: str,
        *,
        actor: str,
        confirmed_at: str,
        confirmation_expires_at: str,
        confirmation: bool,
        acceptance: Mapping[str, Any],
        live_checks: Mapping[str, Any],
        authorization_verified: bool,
    ) -> dict[str, Any]:
        """Require matching artifact/provider evidence for the fourth click."""
        job = self._require(job_id)
        artifact_digest = job.get("artifact_digest")
        if not artifact_digest or acceptance.get("artifact_digest") != artifact_digest:
            raise JobLifecycleError("accepted slicer artifact does not match the job")
        if not job.get("comparison_id") or acceptance.get("comparison_id") != job.get(
            "comparison_id"
        ):
            raise JobLifecycleError("accepted comparison does not match the job")
        if not acceptance.get("reviewed_by") or not acceptance.get("reviewed_at"):
            raise JobLifecycleError("accepted comparison lacks click-three attribution")
        if _utc(acceptance["reviewed_at"]) > _utc(confirmed_at):
            raise JobLifecycleError(
                "click-three review cannot occur after final confirmation"
            )
        for field in (
            "comparison_evidence_digest",
            "input_digest",
            "profile_digest",
            "engine_source_digest",
            "engine_build_digest",
        ):
            if not self._digest(job.get(field)) or acceptance.get(field) != job.get(
                field
            ):
                raise JobLifecycleError(
                    f"accepted slicer {field.replace('_', ' ')} does not match the job"
                )
        if acceptance.get("final_confirmation_required") is not True:
            raise JobLifecycleError("slicer acceptance must require final confirmation")
        if acceptance.get("preflight_verified") is not True:
            raise JobLifecycleError(
                "slicer acceptance must include deterministic preflight"
            )
        if acceptance.get("pair_preflight_verified") is not True:
            raise JobLifecycleError(
                "slicer acceptance must include coordinated pair preflight"
            )
        if (
            acceptance.get("can_upload") is not False
            or acceptance.get("can_start_print") is not False
        ):
            raise JobLifecycleError("slicer acceptance must remain non-authoritative")
        if live_checks.get("provider_id") != job["provider_id"]:
            raise JobLifecycleError("live checks do not match the job provider")
        if live_checks.get("artifact_digest") != artifact_digest:
            raise JobLifecycleError("live checks do not match the accepted artifact")
        if live_checks.get("passed") is not True:
            raise JobLifecycleError("all live printer checks must pass")
        checked_at = _utc(live_checks.get("checked_at"))
        live_checks_expires_at = _utc(live_checks.get("expires_at"))
        confirmed_time = _utc(confirmed_at)
        if checked_at > confirmed_time:
            raise JobLifecycleError("live printer checks occurred after confirmation")
        if confirmed_time >= live_checks_expires_at:
            raise JobLifecycleError("live printer checks expired before confirmation")
        if (
            live_checks.get("can_upload") is not False
            or live_checks.get("can_start_print") is not False
        ):
            raise JobLifecycleError("live checks must remain non-authoritative")
        self.final_confirm(
            job_id,
            actor=actor,
            confirmed_at=confirmed_at,
            confirmation_expires_at=confirmation_expires_at,
            confirmation=confirmation,
            live_checks_passed=True,
            authorization_verified=authorization_verified,
        )
        job["artifact_preflight_verified"] = True
        job["artifact_pair_preflight_verified"] = True
        job["comparison_reviewed_by"] = acceptance["reviewed_by"]
        job["comparison_reviewed_at"] = acceptance["reviewed_at"]
        job["live_checks_checked_at"] = live_checks["checked_at"]
        job["live_checks_expires_at"] = live_checks["expires_at"]
        return deepcopy(job)

    def transition(self, job_id: str, state: str, *, reason: str) -> dict[str, Any]:
        job = self._require(job_id)
        if state not in STATES or state not in TRANSITIONS.get(job["state"], set()):
            raise JobLifecycleError(
                f"invalid job transition: {job['state']} -> {state}"
            )
        if state == "validated" and job["preflight_passed"] is not True:
            raise JobLifecycleError("preflight must pass before validation")
        job.update({"state": state, "reason": reason})
        self._record("job.state.changed", job_id)
        return deepcopy(job)

    def job(self, job_id: str) -> dict[str, Any]:
        return deepcopy(self._require(job_id))

    @staticmethod
    def _digest(value: Any) -> bool:
        return (
            isinstance(value, str)
            and len(value) == 64
            and all(character in "0123456789abcdef" for character in value)
        )

    def _require(self, job_id: str) -> dict[str, Any]:
        try:
            return self._jobs[job_id]
        except KeyError as exc:
            raise JobLifecycleError(f"unknown job: {job_id}") from exc

    def _record(self, event_type: str, job_id: str) -> None:
        self._history.append({"event_type": event_type, "job_id": job_id})
