"""Fresh provider-neutral evidence for the final Runtime dispatch boundary."""

from __future__ import annotations

import json
from collections.abc import Mapping
from copy import deepcopy
from datetime import datetime, timedelta
from hashlib import sha256
from typing import Any


class ProviderDispatchError(ValueError):
    """Raised when provider dispatch evidence is incomplete or unsafe."""


MAX_PROVIDER_DISPATCH_AGE = timedelta(seconds=30)
REQUIRED_CHECKS = {
    "provider_healthy",
    "current_state_allows",
    "capability_available",
}


def provider_dispatch_evidence_digest(value: Mapping[str, Any]) -> str:
    """Hash provider dispatch evidence so callers cannot alter its result."""
    item = deepcopy(dict(value))
    item.pop("evidence_digest", None)
    canonical = json.dumps(
        item,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    ).encode("utf-8")
    return sha256(canonical).hexdigest()


class ProviderDispatchCheckService:
    """Produce non-authoritative, short-lived provider evidence."""

    def evaluate(
        self,
        *,
        provider_id: str,
        context_id: str,
        capability_id: str,
        checked_at: str,
        expires_at: str,
        checks: Mapping[str, Any],
    ) -> dict[str, Any]:
        if not provider_id or not context_id or capability_id != "artifact.upload":
            raise ProviderDispatchError("provider dispatch identity is invalid")
        checked = self._utc(checked_at)
        expiry = self._utc(expires_at)
        if expiry <= checked or expiry - checked > MAX_PROVIDER_DISPATCH_AGE:
            raise ProviderDispatchError(
                "provider dispatch evidence must expire within thirty seconds"
            )
        evidence = deepcopy(dict(checks))
        if set(evidence) != REQUIRED_CHECKS or any(
            not isinstance(evidence[name], bool) for name in REQUIRED_CHECKS
        ):
            raise ProviderDispatchError(
                "provider dispatch checks must be complete booleans"
            )
        result = {
            "provider_id": provider_id,
            "context_id": context_id,
            "capability_id": capability_id,
            "checked_at": checked_at,
            "expires_at": expires_at,
            "checks": evidence,
            "passed": all(evidence.values()),
            "can_upload": False,
            "can_start_print": False,
        }
        result["evidence_digest"] = provider_dispatch_evidence_digest(result)
        return result

    @staticmethod
    def _utc(value: str) -> datetime:
        if not isinstance(value, str) or not value.endswith("Z"):
            raise ProviderDispatchError("provider timestamps must be UTC")
        try:
            return datetime.fromisoformat(value[:-1] + "+00:00")
        except ValueError as exc:
            raise ProviderDispatchError(f"invalid provider timestamp: {value}") from exc
