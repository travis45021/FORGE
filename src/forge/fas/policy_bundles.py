"""Deterministic policy-bundle governance for FAS-009.

The registry is deliberately storage- and cryptography-agnostic. Callers supply
verified signatures and approvals from their trust services; this component
enforces lifecycle, immutability, lineage, rollout, and rollback invariants.
"""

from __future__ import annotations

from copy import deepcopy
from datetime import datetime
import hashlib
import json
from typing import Any, Iterable, Mapping


class PolicyBundleError(ValueError):
    """Raised when a bundle or governance transition violates FAS-009."""


def _canonical(value: Any) -> bytes:
    try:
        return json.dumps(
            value,
            ensure_ascii=False,
            allow_nan=False,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
    except (TypeError, ValueError) as exc:
        raise PolicyBundleError("policy bundle must be canonical JSON") from exc


def _digest(value: Any) -> str:
    return f"sha256:{hashlib.sha256(_canonical(value)).hexdigest()}"


def _utc(value: str) -> datetime:
    if not isinstance(value, str) or not value.endswith("Z"):
        raise PolicyBundleError("timestamps must be UTC strings ending in Z")
    try:
        return datetime.fromisoformat(value[:-1] + "+00:00")
    except ValueError as exc:
        raise PolicyBundleError(f"invalid timestamp: {value}") from exc


def content_digest(bundle: Mapping[str, Any]) -> str:
    """Return the digest of immutable bundle content, excluding attestations."""
    content = deepcopy(dict(bundle))
    content.pop("content_digest", None)
    content.pop("signatures", None)
    return _digest(content)


class PolicyBundleRegistry:
    """In-memory FAS-009 reference registry with atomic activation."""

    REGISTRY_ID = "forge-service:fas-009-reference-registry"
    REGISTRY_VERSION = "1.0.0"

    def __init__(self) -> None:
        self._bundles: dict[str, dict[str, Any]] = {}
        self._active_by_channel: dict[str, str] = {}
        self._history: list[dict[str, Any]] = []

    def register(self, bundle: Mapping[str, Any]) -> str:
        candidate = deepcopy(dict(bundle))
        self._validate_bundle(candidate)
        digest = content_digest(candidate)
        if candidate["content_digest"] != digest:
            raise PolicyBundleError("content_digest does not match bundle content")
        if not any(signature.get("verified") is True for signature in candidate["signatures"]):
            raise PolicyBundleError("at least one verified bundle signature is required")

        bundle_id = candidate["bundle_id"]
        existing = self._bundles.get(bundle_id)
        if existing is not None:
            if _canonical(existing) != _canonical(candidate):
                raise PolicyBundleError("registered bundle identifiers are immutable")
            return digest
        self._bundles[bundle_id] = candidate
        return digest

    def activate(
        self,
        bundle_id: str,
        *,
        channel: str,
        actor: Mapping[str, Any],
        approvals: Iterable[Mapping[str, Any]],
        sentinel_state: str,
        constitution_verified: bool,
        evaluated_at: str,
        rollout_percent: int = 100,
    ) -> dict[str, Any]:
        when = _utc(evaluated_at)
        bundle = self._require_bundle(bundle_id)
        self._validate_transition_inputs(
            bundle,
            channel=channel,
            actor=actor,
            approvals=approvals,
            sentinel_state=sentinel_state,
            constitution_verified=constitution_verified,
            evaluated_at=when,
            rollout_percent=rollout_percent,
        )
        previous = self._active_by_channel.get(channel)
        if previous == bundle_id:
            return self._record(
                "activation_noop", bundle_id, channel, previous, actor, evaluated_at
            )

        self._active_by_channel[channel] = bundle_id
        return self._record(
            "activated", bundle_id, channel, previous, actor, evaluated_at,
            rollout_percent=rollout_percent,
        )

    def rollback(
        self,
        *,
        channel: str,
        target_bundle_id: str,
        actor: Mapping[str, Any],
        approvals: Iterable[Mapping[str, Any]],
        sentinel_state: str,
        constitution_verified: bool,
        evaluated_at: str,
    ) -> dict[str, Any]:
        current = self._active_by_channel.get(channel)
        if current is None:
            raise PolicyBundleError("channel has no active bundle")
        target = self._require_bundle(target_bundle_id)
        if target_bundle_id == current:
            raise PolicyBundleError("rollback target is already active")
        if not self._is_ancestor(target_bundle_id, current):
            raise PolicyBundleError("rollback target must be an ancestor of active bundle")
        result = self.activate(
            target_bundle_id,
            channel=channel,
            actor=actor,
            approvals=approvals,
            sentinel_state=sentinel_state,
            constitution_verified=constitution_verified,
            evaluated_at=evaluated_at,
            rollout_percent=100,
        )
        result["action"] = "rolled_back"
        result["rolled_back_from"] = current
        self._history[-1] = deepcopy(result)
        return result

    def active_bundle(self, channel: str) -> dict[str, Any] | None:
        bundle_id = self._active_by_channel.get(channel)
        return deepcopy(self._bundles[bundle_id]) if bundle_id else None

    def history(self) -> list[dict[str, Any]]:
        return deepcopy(self._history)

    def _validate_bundle(self, bundle: Mapping[str, Any]) -> None:
        required = {
            "bundle_id", "version", "created_at", "created_by", "status",
            "parent_bundle_id", "policies", "constitution", "sentinel",
            "rollout", "content_digest", "signatures",
        }
        missing = sorted(required - bundle.keys())
        if missing:
            raise PolicyBundleError(f"bundle missing required fields: {', '.join(missing)}")
        if bundle["status"] != "candidate":
            raise PolicyBundleError("only candidate bundles may be registered")
        _utc(bundle["created_at"])
        if not bundle["policies"]:
            raise PolicyBundleError("bundle must contain at least one policy")
        refs = [(item["policy_id"], item["version"]) for item in bundle["policies"]]
        if len(refs) != len(set(refs)):
            raise PolicyBundleError("policy references must be unique")
        rollout = bundle["rollout"]
        if rollout["minimum_percent"] < 0 or rollout["maximum_percent"] > 100:
            raise PolicyBundleError("rollout bounds must be between 0 and 100")
        if rollout["minimum_percent"] > rollout["maximum_percent"]:
            raise PolicyBundleError("rollout minimum cannot exceed maximum")

    def _validate_transition_inputs(
        self,
        bundle: Mapping[str, Any],
        *,
        channel: str,
        actor: Mapping[str, Any],
        approvals: Iterable[Mapping[str, Any]],
        sentinel_state: str,
        constitution_verified: bool,
        evaluated_at: datetime,
        rollout_percent: int,
    ) -> None:
        if channel not in bundle["rollout"]["channels"]:
            raise PolicyBundleError("bundle is not approved for requested channel")
        if sentinel_state != "clear" or bundle["sentinel"]["verified"] is not True:
            raise PolicyBundleError("Sentinel verification blocks activation")
        if not constitution_verified or bundle["constitution"]["verified"] is not True:
            raise PolicyBundleError("constitutional verification blocks activation")
        if actor.get("actor_type") != "admin" or actor.get("role") != "forge_admin":
            raise PolicyBundleError("policy activation requires Forge Admin")
        minimum = bundle["rollout"]["minimum_percent"]
        maximum = bundle["rollout"]["maximum_percent"]
        if not isinstance(rollout_percent, int) or not minimum <= rollout_percent <= maximum:
            raise PolicyBundleError("rollout percentage is outside bundle bounds")

        counts: dict[str, set[str]] = {}
        for approval in approvals:
            if approval.get("verified") is not True:
                continue
            if _utc(approval["approved_at"]) <= evaluated_at < _utc(approval["expires_at"]):
                counts.setdefault(approval["approval_type"], set()).add(
                    approval["approval_id"]
                )
        for requirement in bundle["rollout"]["required_approvals"]:
            if len(counts.get(requirement["approval_type"], set())) < requirement[
                "minimum_count"
            ]:
                raise PolicyBundleError(
                    f"missing approval: {requirement['approval_type']}"
                )

    def _is_ancestor(self, target: str, descendant: str) -> bool:
        seen: set[str] = set()
        cursor: str | None = descendant
        while cursor is not None and cursor not in seen:
            seen.add(cursor)
            if cursor == target:
                return True
            cursor = self._bundles.get(cursor, {}).get("parent_bundle_id")
        return False

    def _require_bundle(self, bundle_id: str) -> dict[str, Any]:
        if bundle_id not in self._bundles:
            raise PolicyBundleError(f"unknown bundle: {bundle_id}")
        return self._bundles[bundle_id]

    def _record(
        self,
        action: str,
        bundle_id: str,
        channel: str,
        previous: str | None,
        actor: Mapping[str, Any],
        evaluated_at: str,
        *,
        rollout_percent: int = 100,
    ) -> dict[str, Any]:
        record = {
            "governance_id": "forge-policy-governance:"
            + hashlib.sha256(
                _canonical(
                    {
                        "action": action,
                        "bundle_id": bundle_id,
                        "channel": channel,
                        "previous_bundle_id": previous,
                        "evaluated_at": evaluated_at,
                    }
                )
            ).hexdigest()[:32],
            "action": action,
            "bundle_id": bundle_id,
            "channel": channel,
            "previous_bundle_id": previous,
            "rollout_percent": rollout_percent,
            "actor_id": actor["actor_id"],
            "evaluated_at": evaluated_at,
            "bundle_digest": self._bundles[bundle_id]["content_digest"],
        }
        self._history.append(deepcopy(record))
        return record
