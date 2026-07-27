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


@pytest.mark.parametrize(
    ("provider_id", "context_id"),
    [
        (1, "context:print"),
        ("provider:custom", 1),
        (" ", "context:print"),
        ("provider:custom", " "),
    ],
)
def test_rejects_invalid_provider_or_context_identity(
    provider_id: object, context_id: object
) -> None:
    with pytest.raises(ProviderDispatchError, match="identity"):
        ProviderDispatchCheckService().evaluate(
            provider_id=provider_id,
            context_id=context_id,
            capability_id="artifact.upload",
            checked_at="2026-07-25T20:59:50Z",
            expires_at="2026-07-25T21:00:20Z",
            checks={
                "provider_healthy": True,
                "current_state_allows": True,
                "capability_available": True,
            },
        )


def test_rejects_non_boolean_or_extra_dispatch_checks() -> None:
    service = ProviderDispatchCheckService()
    base = {
        "provider_healthy": True,
        "current_state_allows": True,
        "capability_available": True,
    }
    for changed in (
        {**base, "provider_healthy": 1},
        {**base, "confirmation_token": True},
    ):
        with pytest.raises(ProviderDispatchError, match="complete booleans"):
            service.evaluate(
                provider_id="provider:custom",
                context_id="context:print",
                capability_id="artifact.upload",
                checked_at="2026-07-25T20:59:50Z",
                expires_at="2026-07-25T21:00:20Z",
                checks=changed,
            )
