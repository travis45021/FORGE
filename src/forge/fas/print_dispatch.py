"""Application composition for the governed fourth-click upload path."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from .executive import ForgeExecutive
from .runtime import ForgeRuntime
from .transport import HardwareTransportRegistry


class PrintDispatchCoordinator:
    """Compose existing gates without talking directly to printer hardware."""

    def __init__(
        self,
        *,
        executive: ForgeExecutive,
        transport: HardwareTransportRegistry,
        runtime: ForgeRuntime,
    ) -> None:
        self._executive = executive
        self._transport = transport
        self._runtime = runtime

    def dispatch_confirmed_upload(
        self,
        *,
        mission: Mapping[str, Any],
        job: Mapping[str, Any],
        acceptance: Mapping[str, Any],
        authorization: Mapping[str, Any],
        capability: Mapping[str, Any],
        context_id: str,
        command_id: str,
        resource_ids: list[str],
        command_expires_at: str,
        evaluated_at: str,
        provider_evidence: Mapping[str, Any],
        runtime_lease_active: bool,
        authorization_verified: bool,
    ) -> dict[str, Any]:
        """Run Executive, transport, and Runtime guards in dependency order."""
        executive_request = self._executive.prepare_confirmed_artifact_execution(
            mission,
            job,
            acceptance,
            authorization,
            capability,
        )
        prepared_upload = self._transport.prepare_artifact_upload(
            capability["provider_id"],
            job,
            runtime_lease_active=runtime_lease_active,
            authorization_verified=authorization_verified,
        )
        runtime_result = self._runtime.dispatch_artifact_upload(
            context_id,
            prepared_upload,
            command_id=command_id,
            resource_ids=resource_ids,
            expires_at=command_expires_at,
            evaluated_at=evaluated_at,
            provider_evidence=provider_evidence,
        )
        upload_evidence = {
            field: prepared_upload[field]
            for field in (
                "provider_id",
                "job_id",
                "artifact_digest",
                "comparison_id",
                "comparison_evidence_digest",
                "comparison_reviewed_by",
                "comparison_reviewed_at",
                "input_digest",
                "profile_digest",
                "engine_source_digest",
                "engine_build_digest",
                "confirmed_by",
                "confirmed_at",
                "confirmation_expires_at",
                "final_confirmation_evidence_digest",
                "live_checks_checked_at",
                "live_checks_expires_at",
                "live_checks_evidence_digest",
                "fourth_click_satisfied",
                "physical_dispatch_allowed",
            )
        }
        return {
            "executive_request": executive_request,
            "upload_evidence": upload_evidence,
            "runtime_result": runtime_result,
            "upload_dispatched": runtime_result.get("status") == "dispatched",
            "print_started": False,
            "physical_outcome_confirmed": False,
        }
