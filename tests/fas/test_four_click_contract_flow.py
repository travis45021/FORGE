"""End-to-end contract test for the governed four-click print path."""

import sys
import tempfile
import unittest
from pathlib import Path
from zipfile import ZipFile

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from forge.fas.imports import ImportQuarantine
from forge.fas.job_lifecycle import PrintJobLifecycle
from forge.fas.live_printer_checks import REQUIRED_CHECKS, LivePrinterCheckService
from forge.fas.slicer_acceptance import SlicerArtifactAcceptance
from forge.fas.slicer_preparation import SlicerMissionPreparation
from forge.fas.transport import HardwareTransportRegistry
from forge.fas.twin_comparison import TwinComparisonService


class FourClickContractFlowTests(unittest.TestCase):
    def test_complete_flow_requires_fourth_click_before_upload_handoff(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / "part.3mf"
            with ZipFile(source, "w") as archive:
                archive.writestr(
                    "3D/3dmodel.model",
                    "<model><resources/><build/></model>",
                )
            assessment = ImportQuarantine().assess(source)

        intent = {
            "intent_id": "intent-1",
            "source_digest": assessment["source_digest"],
            "printer_capabilities": ["fff.extrusion", "artifact.upload"],
            "material": {"name": "PLA"},
            "process": {"profile_digest": "b" * 64},
            "user_decisions": {
                "context_confirmed": True,
                "mission_reviewed": True,
            },
        }
        preparation = SlicerMissionPreparation()
        production_request = preparation.prepare(
            request_id="request-production",
            mission_id="mission-1",
            source_path="quarantine/part.3mf",
            context="production",
            assessment=assessment,
            intent=intent,
        )
        twin_request = preparation.prepare(
            request_id="request-twin",
            mission_id="mission-1",
            source_path="quarantine/part.3mf",
            context="twin",
            assessment=assessment,
            intent=intent,
        )
        artifact_digest = "d" * 64

        def result(request: dict) -> dict:
            return {
                "contract_version": "1.0",
                "request_id": request["request_id"],
                "status": "succeeded",
                "context": request["context"],
                "engine": {
                    "name": "contract-fixture",
                    "version": "0",
                    "source_digest": "c" * 64,
                },
                "artifact_digest": artifact_digest,
                "warnings": [],
                "authority": {"can_upload": False, "can_start_print": False},
            }

        comparison = TwinComparisonService().compare(
            comparison_id="comparison-1",
            input_digest=assessment["source_digest"],
            production=result(production_request),
            twin=result(twin_request),
            reviewed_by_user=True,
        )
        acceptance = SlicerArtifactAcceptance().accept(comparison)
        live = LivePrinterCheckService().evaluate(
            provider_id="provider:custom",
            artifact_digest=artifact_digest,
            checks={name: True for name in REQUIRED_CHECKS},
        )

        lifecycle = PrintJobLifecycle()
        lifecycle.create(
            {
                "job_id": "job-1",
                "artifact_id": "artifact-1",
                "artifact_digest": artifact_digest,
                "provider_id": "provider:custom",
                "state": "draft",
                "preflight_passed": True,
                "live_checks_passed": False,
                "click_count": 0,
            }
        )
        lifecycle.transition("job-1", "validated", reason="validated")
        for action in ("upload", "configure", "review"):
            lifecycle.click("job-1", action=action, actor="user-1")
        job = lifecycle.final_confirm_with_evidence(
            "job-1",
            actor="user-1",
            confirmation=True,
            acceptance=acceptance,
            live_checks=live,
            authorization_verified=True,
        )

        registry = HardwareTransportRegistry()
        registry.register(
            {
                "provider_id": "provider:custom",
                "transport": "local-capability-provider",
                "capabilities": ["artifact.upload"],
                "state": "registered",
                "health": "healthy",
            }
        )
        handoff = registry.prepare_artifact_upload(
            "provider:custom",
            job,
            runtime_lease_active=True,
            authorization_verified=True,
        )
        self.assertTrue(handoff["fourth_click_satisfied"])
        self.assertFalse(handoff["physical_dispatch_allowed"])


if __name__ == "__main__":
    unittest.main()
