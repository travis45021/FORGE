"""Hardware-neutral live printer checks before final confirmation."""

from __future__ import annotations

from collections.abc import Mapping
from copy import deepcopy
from typing import Any


class LivePrinterCheckError(ValueError):
    """Raised when live printer evidence is incomplete or unsafe."""


REQUIRED_CHECKS = {
    "connected",
    "idle",
    "capabilities_match",
    "material_available",
    "safety_state_clear",
    "artifact_current",
}


class LivePrinterCheckService:
    """Evaluate provider-neutral live evidence without controlling hardware."""

    def evaluate(
        self,
        *,
        provider_id: str,
        artifact_digest: str,
        checks: Mapping[str, Any],
    ) -> dict[str, Any]:
        if not provider_id:
            raise LivePrinterCheckError("provider identity is required")
        self._digest(artifact_digest)
        evidence = deepcopy(dict(checks))
        missing = sorted(REQUIRED_CHECKS - evidence.keys())
        if missing:
            raise LivePrinterCheckError(f"live checks missing: {', '.join(missing)}")
        invalid = sorted(name for name in REQUIRED_CHECKS if evidence[name] is not True)
        return {
            "provider_id": provider_id,
            "artifact_digest": artifact_digest,
            "checks": evidence,
            "passed": not invalid,
            "failed_checks": invalid,
            "final_confirmation_required": True,
            "can_upload": False,
            "can_start_print": False,
        }

    @staticmethod
    def _digest(value: Any) -> None:
        if (
            not isinstance(value, str)
            or len(value) != 64
            or any(character not in "0123456789abcdef" for character in value)
        ):
            raise LivePrinterCheckError("artifact digest must be lowercase SHA-256")
