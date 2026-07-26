"""Testing, simulation, and release assurance contracts for FAS-025."""

from __future__ import annotations

from copy import deepcopy
from typing import Any, Mapping


class TestAssuranceError(ValueError):
    """Raised when test evidence violates the FAS-025 boundary."""


TEST_LAYERS = {
    "unit",
    "contract",
    "integration",
    "scenario",
    "fault_injection",
    "security",
    "hardware_in_the_loop",
    "release",
}


class TestAssuranceService:
    """Records reproducible evidence without confusing simulation with reality."""

    def __init__(self) -> None:
        self._simulators: dict[str, dict[str, Any]] = {}
        self._results: list[dict[str, Any]] = []

    def register_simulator(self, manifest: Mapping[str, Any]) -> dict[str, Any]:
        item = deepcopy(dict(manifest))
        required = {
            "provider_id",
            "represented_behavior",
            "contract_version",
            "limitations",
            "failure_modes",
            "deterministic",
            "suitable_layers",
        }
        missing = sorted(required - item.keys())
        if missing:
            raise TestAssuranceError(
                f"simulator manifest missing fields: {', '.join(missing)}"
            )
        if not set(item["suitable_layers"]) <= {
            "unit", "contract", "integration", "scenario", "fault_injection"
        }:
            raise TestAssuranceError("simulator declares an unsuitable test layer")
        item["provider_kind"] = "simulated"
        item["production_eligible"] = False
        item["can_authorize_physical_action"] = False
        self._simulators[item["provider_id"]] = item
        return deepcopy(item)

    def execution_context(
        self,
        *,
        context_kind: str,
        experimental_enabled: bool = False,
    ) -> dict[str, Any]:
        if context_kind not in {"test", "simulation", "production"}:
            raise TestAssuranceError("unknown execution context kind")
        return {
            "context_kind": context_kind,
            "simulation_allowed": context_kind in {"test", "simulation"},
            "experimental_enabled": experimental_enabled,
            "physical_authority_from_simulation": False,
        }

    def record_result(self, result: Mapping[str, Any]) -> dict[str, Any]:
        item = deepcopy(dict(result))
        required = {
            "test_id", "layer", "test_version", "contract_versions",
            "configuration_snapshot", "provider_versions", "input_data",
            "event_sequence", "runtime_context", "expected", "observed",
            "outcome",
        }
        missing = sorted(required - item.keys())
        if missing:
            raise TestAssuranceError(
                f"test result missing reproducibility fields: {', '.join(missing)}"
            )
        if item["layer"] not in TEST_LAYERS:
            raise TestAssuranceError("unknown test layer")
        if item["outcome"] not in {"passed", "failed", "inconclusive"}:
            raise TestAssuranceError("unknown test outcome")
        if item.get("variable") is True and "acceptance_range" not in item:
            raise TestAssuranceError("variable tests require an acceptance range")
        item["evidence_kind"] = (
            "simulation" if item["runtime_context"].get("simulated") else "measured"
        )
        item["authorizes_production"] = False
        self._results.append(item)
        return deepcopy(item)

    def validate_hardware_test(
        self,
        plan: Mapping[str, Any],
        *,
        user_authorized: bool,
    ) -> dict[str, Any]:
        required = {
            "target_hardware", "limits", "stop_conditions", "physical_action",
            "monitoring", "recovery_plan", "mission_kind",
        }
        missing = sorted(required - plan.keys())
        if missing:
            raise TestAssuranceError(
                f"hardware test missing safety fields: {', '.join(missing)}"
            )
        if user_authorized is not True:
            raise TestAssuranceError("hardware-in-the-loop testing requires authority")
        if plan["mission_kind"] != "test":
            raise TestAssuranceError("hardware test must be distinct from production")
        if not plan["limits"] or not plan["stop_conditions"]:
            raise TestAssuranceError("hardware test requires limits and stop conditions")
        result = deepcopy(dict(plan))
        result.update(
            {
                "approved": True,
                "bounded": True,
                "prefer_low_energy_reversible": True,
                "requires_measured_result": True,
            }
        )
        return result

    def assess_release(self, record: Mapping[str, Any]) -> dict[str, Any]:
        item = deepcopy(dict(record))
        required = {
            "release_version", "components", "supported_environments",
            "test_results", "known_limitations", "security_review",
            "compatibility_review", "migration", "rollback",
            "documentation_complete", "integrity",
        }
        missing = sorted(required - item.keys())
        if missing:
            raise TestAssuranceError(
                f"release record missing fields: {', '.join(missing)}"
            )
        results = item["test_results"]
        blocking = [
            value for value in results
            if value.get("outcome") != "passed"
            and (
                value.get("required") is True
                or value.get("security_critical") is True
            )
        ]
        if item["security_review"] != "passed":
            blocking.append({"reason": "security_review_not_passed"})
        if item["documentation_complete"] is not True:
            blocking.append({"reason": "documentation_incomplete"})
        if not item["rollback"]:
            blocking.append({"reason": "rollback_missing"})
        item["decision"] = "releasable" if not blocking else "blocked"
        item["blocking_evidence"] = blocking
        item["maturity_claim"] = "bounded_by_recorded_evidence"
        return item

    def results(self) -> list[dict[str, Any]]:
        return deepcopy(self._results)
