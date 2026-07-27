"""Tests for provider-neutral final dispatch evidence."""

import pytest

from forge.fas.provider_dispatch import (
    ProviderDispatchCheckService,
    ProviderDispatchError,
)


def test_produces_short_lived_non_authoritative_evidence() -> None:
    result = ProviderDispatchCheckService().evaluate(
        provider_id="provider:custom",
        context_id="context:print",
        capability_id="artifact.upload",
        checked_at="2026-07-25T20:59:50Z",
        expires_at="2026-07-25T21:00:20Z",
        checks={
            "provider_healthy": True,
            "current_state_allows": True,
            "capability_available": True,
        },
    )

    assert result["passed"] is True
    assert len(result["evidence_digest"]) == 64
    assert result["can_upload"] is False


def test_rejects_overlong_provider_evidence() -> None:
    with pytest.raises(ProviderDispatchError, match="thirty seconds"):
        ProviderDispatchCheckService().evaluate(
            provider_id="provider:custom",
            context_id="context:print",
            capability_id="artifact.upload",
            checked_at="2026-07-25T20:59:00Z",
            expires_at="2026-07-25T21:00:00Z",
            checks={
                "provider_healthy": True,
                "current_state_allows": True,
                "capability_available": True,
            },
        )
