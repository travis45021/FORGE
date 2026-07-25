"""Behavior and schema tests for canonical FAS-015."""

from copy import deepcopy
import json
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from forge.fas.scheduler import MissionScheduler, SchedulingError  # noqa: E402


def load_json(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as stream:
        return json.load(stream)


class Fas015SchedulerTests(unittest.TestCase):
    def setUp(self) -> None:
        self.mission = load_json(
            ROOT / "examples" / "fas" / "scheduled-mission-print.example.json"
        )
        self.scheduler = MissionScheduler()

    def submit(self, mission: dict | None = None) -> dict:
        return self.scheduler.submit(
            mission or self.mission, executive_authorized=True
        )

    def variant(self, suffix: str, **changes: object) -> dict:
        return {
            **self.mission,
            "mission_id": f"forge-mission:{suffix}",
            **changes,
        }

    def test_priority_never_grants_authority(self) -> None:
        emergency = self.variant("emergency", priority="emergency")
        with self.assertRaisesRegex(SchedulingError, "not permission"):
            self.scheduler.submit(emergency, executive_authorized=False)

    def test_priority_order_and_conditions(self) -> None:
        self.submit()
        self.submit(self.variant("high", priority="high", resources=["device:two"]))
        ready = self.scheduler.next_ready(
            evaluated_at="2026-07-25T21:00:00Z",
            conditions={"printer_idle": True},
        )
        self.assertEqual("forge-mission:high", ready["mission_id"])

    def test_approval_and_ai_free_waits_are_explained(self) -> None:
        approval = self.variant("approval", requires_approval=True)
        ai = self.variant("ai", requires_ai=True, resources=["service:ai"])
        self.submit(approval)
        self.submit(ai)
        self.scheduler.next_ready(
            evaluated_at="2026-07-25T21:00:00Z",
            conditions={"printer_idle": True},
        )
        self.assertEqual(
            "waiting_for_approval",
            self.scheduler.mission(approval["mission_id"])["state"],
        )
        self.assertEqual(
            "ai_required_but_disabled",
            self.scheduler.mission(ai["mission_id"])["reason"],
        )

    def test_resource_conflicts_prevent_parallel_start(self) -> None:
        first = self.submit()
        self.scheduler.next_ready(
            evaluated_at="2026-07-25T21:00:00Z",
            conditions={"printer_idle": True},
        )
        self.scheduler.start(first["mission_id"])
        second = self.variant("second")
        self.submit(second)
        self.assertIsNone(
            self.scheduler.next_ready(
                evaluated_at="2026-07-25T21:01:00Z",
                conditions={"printer_idle": True},
            )
        )
        self.assertEqual(
            "waiting_for_resource",
            self.scheduler.mission(second["mission_id"])["state"],
        )

    def test_preemption_requires_authority_policy_and_safe_pause(self) -> None:
        running = self.submit()
        self.scheduler.next_ready(
            evaluated_at="2026-07-25T21:00:00Z",
            conditions={"printer_idle": True},
        )
        self.scheduler.start(running["mission_id"])
        incoming = self.variant(
            "critical", priority="critical", resources=["device:recovery"]
        )
        self.submit(incoming)
        with self.assertRaisesRegex(SchedulingError, "authority and policy"):
            self.scheduler.preempt(
                running["mission_id"],
                incoming["mission_id"],
                executive_authorized=False,
                policy_allows=True,
            )
        result = self.scheduler.preempt(
            running["mission_id"],
            incoming["mission_id"],
            executive_authorized=True,
            policy_allows=True,
        )
        self.assertEqual("preempted", result["state"])

    def test_non_preemptible_window_blocks_non_emergency(self) -> None:
        running = self.variant("firmware", at_safe_pause_point=False)
        self.submit(running)
        self.scheduler.next_ready(
            evaluated_at="2026-07-25T21:00:00Z",
            conditions={"printer_idle": True},
        )
        self.scheduler.start(running["mission_id"])
        incoming = self.variant(
            "high", priority="high", resources=["device:other"]
        )
        self.submit(incoming)
        with self.assertRaisesRegex(SchedulingError, "safe pause"):
            self.scheduler.preempt(
                running["mission_id"],
                incoming["mission_id"],
                executive_authorized=True,
                policy_allows=True,
            )

    def test_bounded_retry_stops_loop(self) -> None:
        mission = self.variant(
            "retry",
            retry_policy={"maximum_attempts": 1, "backoff_seconds": 1},
        )
        self.submit(mission)
        self.assertEqual("queued", self.scheduler.retry(mission["mission_id"])["state"])
        self.assertEqual("failed", self.scheduler.retry(mission["mission_id"])["state"])

    def test_aging_prevents_starvation_without_becoming_critical(self) -> None:
        old = self.variant(
            "old-background",
            priority="background",
            queued_at="2026-06-01T20:00:00Z",
            resources=["service:index"],
            conditions=[],
        )
        self.submit(old)
        ready = self.scheduler.next_ready(
            evaluated_at="2026-07-25T21:00:00Z"
        )
        self.assertEqual("high", ready["effective_priority"])

    def test_scheduler_has_no_hardware_command_surface(self) -> None:
        self.assertFalse(hasattr(self.scheduler, "command_hardware"))
        self.assertFalse(hasattr(self.scheduler, "execute_operation"))

    def test_schema_and_example_validate(self) -> None:
        from jsonschema import Draft202012Validator, FormatChecker
        schema = load_json(ROOT / "schemas" / "fas" / "scheduled-mission.schema.json")
        Draft202012Validator.check_schema(schema)
        Draft202012Validator(
            schema, format_checker=FormatChecker()
        ).validate(self.mission)


if __name__ == "__main__":
    unittest.main()
