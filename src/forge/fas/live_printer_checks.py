"""Hardware-neutral live printer checks before final confirmation."""

from __future__ import annotations

import json
from collections.abc import Mapping
from copy import deepcopy
from datetime import datetime
from hashlib import sha256
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


def live_check_evidence_digest(value: Mapping[str, Any]) -> str:
    """Hash complete live-check evidence so it cannot change after review."""
    item = deepcopy(dict(value))
    item.pop("evidence_digest", None)
    canonical = json.dumps(
        item,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    ).encode("utf-8")
    return sha256(canonical).hexdigest()


class LivePrinterCheckService:
    """Evaluate provider-neutral live evidence without controlling hardware."""

    def evaluate(
        self,
        *,
        provider_id: str,
        artifact_digest: str,
        checks: Mapping[str, Any],
        checked_at: str,
        expires_at: str,
    ) -> dict[str, Any]:
        if not provider_id:
            raise LivePrinterCheckError("provider identity is required")
        self._digest(artifact_digest)
        checked = self._utc(checked_at)
        expiry = self._utc(expires_at)
        if expiry <= checked:
            raise LivePrinterCheckError("live check expiry must follow the check time")
        evidence = deepcopy(dict(checks))
        missing = sorted(REQUIRED_CHECKS - evidence.keys())
        if missing:
            raise LivePrinterCheckError(f"live checks missing: {', '.join(missing)}")
        invalid = sorted(name for name in REQUIRED_CHECKS if evidence[name] is not True)
        result = {
            "provider_id": provider_id,
            "artifact_digest": artifact_digest,
            "checks": evidence,
            "checked_at": checked_at,
            "expires_at": expires_at,
            "passed": not invalid,
            "failed_checks": invalid,
            "final_confirmation_required": True,
            "can_upload": False,
            "can_start_print": False,
        }
        result["evidence_digest"] = live_check_evidence_digest(result)
        return result

    @staticmethod
    def _digest(value: Any) -> None:
        if (
            not isinstance(value, str)
            or len(value) != 64
            or any(character not in "0123456789abcdef" for character in value)
        ):
            raise LivePrinterCheckError("artifact digest must be lowercase SHA-256")

    @staticmethod
    def _utc(value: str) -> datetime:
        if not isinstance(value, str) or not value.endswith("Z"):
            raise LivePrinterCheckError("live check timestamps must be UTC")
        try:
            return datetime.fromisoformat(value[:-1] + "+00:00")
        except ValueError as exc:
            raise LivePrinterCheckError(
                f"invalid live check timestamp: {value}"
            ) from exc
