"""Behavior and schema tests for canonical FAS-022."""

from copy import deepcopy
import json
from pathlib import Path
import sys
import unittest


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from forge.fas.runtime import ForgeRuntime, RuntimeError  # noqa: E402


def load_json(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as stream:
        return json.load(stream)


class Fas022RuntimeTests(unittest.TestCase):
    def setUp(self) -> None:
        self.context = load_json(
            ROOT / "examples" / "fas" / "execution-context-print.example.json"
        )
        self.runtime = ForgeRuntime()

    def create(self, context: dict | None = None) -> dict:
        return self.runtime.create_context(context or self.context)

    def ready(self) -> None:
        self.create()
        for state in ("preparing", "ready"):
            self.runtime.transition(
                self.context["context_id"],
                state,
                trigger=f"entered_{state}",
                authority_reference=self.context["authority_reference"],
            )

    def lease(self, expires_at: str = "2026-07-25T22:00:00Z") -> dict:
        return self.runtime.reserve(
            self.context["context_id"],
            self.context["reserved_resources"][0],
            mode="exclusive",
            acquired_at="2026-07-25T20:00:00Z",
            expires_at=expires_at,
        )

    def command(self) -> dict:
        return {
            "command_id": "forge-command:print-start-001",
            "context_id": self.context["context_id"],
            "capability_id": "manufacturing.print",
            "provider_id": "community-provider:garage-printer",
            "resource_ids": self.context["reserved_resources"],
            "expires_at": "2026-07-25T21:30:00Z",
            "verification_passed": True,
        }

    def test_context_records_all_execution_basis(self) -> None:
        result = self.create()
        for field in (
            "authority_reference",
            "policy_snapshot",
            "configuration_snapshot",
            "verification_packet",
            "resolved_capabilities",
            "reserved_resources",
        ):
            self.assertTrue(result[field])

    def test_child_context_cannot_broaden_parent(self) -> None:
        self.create()
        child = deepcopy(self.context)
        child.update(
            {
                "context_id": "forge-context:child-001",
                "parent_context_id": self.context["context_id"],
                "allowed_capabilities": ["manufacturing.print", "firmware.flash"],
            }
        )
        with self.assertRaisesRegex(RuntimeError, "broaden"):
            self.runtime.create_context(child)
        child["allowed_capabilities"] = []
        child["resolved_capabilities"] = []
        child["reserved_resources"] = []
        self.runtime.create_context(child)

    def test_exclusive_lease_blocks_incompatible_context(self) -> None:
        self.create()
        self.lease()
        other = deepcopy(self.context)
        other["context_id"] = "forge-context:print-002"
        other["mission_id"] = "forge-mission:print-002"
        self.runtime.create_context(other)
        with self.assertRaisesRegex(RuntimeError, "incompatible"):
            self.runtime.reserve(
                other["context_id"],
                other["reserved_resources"][0],
                mode="exclusive",
                acquired_at="2026-07-25T20:01:00Z",
                expires_at="2026-07-25T22:00:00Z",
            )

    def test_expired_lease_enters_recovery_not_assumed_release(self) -> None:
        self.create()
        lease = self.lease(expires_at="2026-07-25T21:00:00Z")
        expired = self.runtime.expire_leases(
            evaluated_at="2026-07-25T21:00:00Z"
        )
        self.assertEqual(lease["lease_id"], expired[0]["lease_id"])
        self.assertEqual(
            "recovering",
            self.runtime.context(self.context["context_id"])["state"],
        )

    def test_expired_lease_cannot_be_renewed(self) -> None:
        self.create()
        lease = self.lease(expires_at="2026-07-25T21:00:00Z")
        with self.assertRaisesRegex(RuntimeError, "expired"):
            self.runtime.renew_lease(
                lease["lease_id"],
                renewed_at="2026-07-25T21:00:00Z",
                expires_at="2026-07-25T22:00:00Z",
                authority_verified=True,
            )

    def test_dispatch_requires_context_provider_lease_and_verification(self) -> None:
        self.ready()
        self.lease()
        result = self.runtime.dispatch(
            self.context["context_id"],
            self.command(),
            evaluated_at="2026-07-25T21:00:00Z",
            provider_healthy=True,
            current_state_allows=True,
        )
        self.assertEqual("dispatched", result["status"])
        self.assertFalse(result["physical_outcome_confirmed"])

    def test_dispatch_fails_when_authority_or_verification_missing(self) -> None:
        context = deepcopy(self.context)
        context["authorization_verified"] = False
        self.runtime.create_context(context)
        for state in ("preparing", "ready"):
            self.runtime.transition(
                context["context_id"],
                state,
                trigger=state,
                authority_reference=context["authority_reference"],
            )
        self.lease()
        with self.assertRaisesRegex(RuntimeError, "authority"):
            self.runtime.dispatch(
                context["context_id"],
                self.command(),
                evaluated_at="2026-07-25T21:00:00Z",
                provider_healthy=True,
                current_state_allows=True,
            )

    def test_physical_work_never_blindly_resumes_after_restart(self) -> None:
        self.ready()
        result = self.runtime.assess_restart(
            self.context["context_id"],
            physical_work=True,
            provider_state_verified=True,
            hardware_state_verified=False,
            safety_verified=True,
            authority_reverified=True,
            leases_reacquired=True,
        )
        self.assertEqual("do_not_resume", result["disposition"])
        self.assertEqual("paused", result["state"])

    def test_verified_restart_is_only_scheduler_eligible(self) -> None:
        self.ready()
        result = self.runtime.assess_restart(
            self.context["context_id"],
            physical_work=True,
            provider_state_verified=True,
            hardware_state_verified=True,
            safety_verified=True,
            authority_reverified=True,
            leases_reacquired=True,
        )
        self.assertEqual("eligible_for_scheduler_resume", result["disposition"])
        self.assertNotEqual("running", result["state"])

    def test_terminal_context_releases_active_leases(self) -> None:
        self.ready()
        lease = self.lease()
        for state in ("running", "verifying", "completed"):
            self.runtime.transition(
                self.context["context_id"],
                state,
                trigger=state,
                authority_reference=self.context["authority_reference"],
            )
        current = next(
            item
            for item in self.runtime.leases()
            if item["lease_id"] == lease["lease_id"]
        )
        self.assertEqual("released", current["state"])

    def test_schema_and_example_validate(self) -> None:
        from jsonschema import Draft202012Validator, FormatChecker

        schema = load_json(
            ROOT / "schemas" / "fas" / "execution-context.schema.json"
        )
        Draft202012Validator.check_schema(schema)
        Draft202012Validator(
            schema, format_checker=FormatChecker()
        ).validate(self.context)


if __name__ == "__main__":
    unittest.main()
