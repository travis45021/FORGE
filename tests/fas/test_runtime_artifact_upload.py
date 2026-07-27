"""Tests for runtime dispatch of a fourth-click artifact upload."""

import json
import sys
import unittest
from copy import deepcopy
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from forge.fas.runtime import ForgeRuntime, RuntimeError


class RuntimeArtifactUploadTests(unittest.TestCase):
    def setUp(self) -> None:
        context = json.loads(
            (ROOT / "examples/fas/execution-context-print.example.json").read_text(
                encoding="utf-8"
            )
        )
        context = deepcopy(context)
        context["allowed_capabilities"].append("artifact.upload")
        context["resolved_capabilities"].append(
            {
                "capability_id": "artifact.upload",
                "provider_id": "provider:custom",
            }
        )
        self.context = context
        self.runtime = ForgeRuntime()
        self.runtime.create_context(context)
        for state in ("preparing", "ready"):
            self.runtime.transition(
                context["context_id"],
                state,
                trigger=state,
                authority_reference=context["authority_reference"],
            )
        self.runtime.reserve(
            context["context_id"],
            context["reserved_resources"][0],
            mode="exclusive",
            acquired_at="2026-07-25T20:00:00Z",
            expires_at="2026-07-25T22:00:00Z",
        )
        self.handoff = {
            "provider_id": "provider:custom",
            "job_id": "job-1",
            "artifact_digest": "a" * 64,
            "input_digest": "b" * 64,
            "profile_digest": "c" * 64,
            "engine_source_digest": "d" * 64,
            "engine_build_digest": "e" * 64,
            "comparison_id": "comparison-1",
            "comparison_evidence_digest": "f" * 64,
            "comparison_reviewed_by": "reviewer-1",
            "comparison_reviewed_at": "2026-07-26T12:00:00Z",
            "confirmed_by": "user-1",
            "confirmed_at": "2026-07-26T12:05:00Z",
            "confirmation_token": "confirmation-" + ("x" * 32),
            "artifact_preflight_verified": True,
            "artifact_pair_preflight_verified": True,
            "historical_replay_allowed": False,
            "physical_dispatch_allowed": False,
            "requires_runtime_dispatcher": True,
            "fourth_click_satisfied": True,
        }

    def dispatch(self) -> dict:
        return self.runtime.dispatch_artifact_upload(
            self.context["context_id"],
            self.handoff,
            command_id="command:upload-1",
            resource_ids=self.context["reserved_resources"],
            expires_at="2026-07-25T21:30:00Z",
            evaluated_at="2026-07-25T21:00:00Z",
            provider_healthy=True,
            current_state_allows=True,
        )

    def test_dispatches_only_through_runtime(self) -> None:
        result = self.dispatch()
        self.assertEqual(result["status"], "dispatched")
        self.assertFalse(result["physical_outcome_confirmed"])
        self.assertEqual(result["artifact_digest"], "a" * 64)
        self.assertEqual(result["input_digest"], "b" * 64)
        self.assertEqual(result["profile_digest"], "c" * 64)
        self.assertEqual(result["engine_build_digest"], "e" * 64)
        self.assertEqual(result["comparison_evidence_digest"], "f" * 64)
        self.assertEqual(result["comparison_reviewed_by"], "reviewer-1")
        self.assertEqual(result["confirmed_at"], "2026-07-26T12:05:00Z")

    def test_rejects_missing_fourth_click(self) -> None:
        self.handoff["fourth_click_satisfied"] = False
        with self.assertRaises(RuntimeError):
            self.dispatch()

    def test_rejects_missing_fourth_click_time(self) -> None:
        self.handoff["confirmed_at"] = ""
        with self.assertRaisesRegex(RuntimeError, "fourth-click attribution"):
            self.dispatch()

    def test_rejects_duplicate_live_handoff(self) -> None:
        self.dispatch()
        with self.assertRaises(RuntimeError):
            self.dispatch()

    def test_rejects_historical_replay_before_dispatch(self) -> None:
        with self.assertRaises(RuntimeError):
            self.runtime.dispatch_artifact_upload(
                self.context["context_id"],
                self.handoff,
                command_id="command:replayed-upload",
                resource_ids=self.context["reserved_resources"],
                expires_at="2026-07-25T21:30:00Z",
                evaluated_at="2026-07-25T21:00:00Z",
                provider_healthy=True,
                current_state_allows=True,
                historical_replay=True,
            )
        self.assertFalse(
            any(
                event["event_type"] == "runtime.command.dispatched"
                for event in self.runtime.history()
            )
        )

    def test_rejects_handoff_without_artifact_preflight(self) -> None:
        self.handoff["artifact_preflight_verified"] = False
        with self.assertRaises(RuntimeError):
            self.dispatch()

    def test_rejects_handoff_without_pair_preflight(self) -> None:
        self.handoff["artifact_pair_preflight_verified"] = False
        with self.assertRaisesRegex(RuntimeError, "coordinated pair"):
            self.dispatch()

    def test_rejects_handoff_without_input_lineage(self) -> None:
        self.handoff.pop("input_digest")
        with self.assertRaisesRegex(RuntimeError, "input digest"):
            self.dispatch()

    def test_rejects_handoff_without_engine_source_provenance(self) -> None:
        self.handoff.pop("engine_source_digest")
        with self.assertRaisesRegex(RuntimeError, "engine source digest"):
            self.dispatch()

    def test_rejects_handoff_without_reviewed_comparison(self) -> None:
        self.handoff.pop("comparison_id")
        with self.assertRaisesRegex(RuntimeError, "comparison identity"):
            self.dispatch()

    def test_rejects_handoff_without_review_attribution(self) -> None:
        self.handoff.pop("comparison_reviewed_by")
        with self.assertRaisesRegex(RuntimeError, "click-three attribution"):
            self.dispatch()


if __name__ == "__main__":
    unittest.main()
