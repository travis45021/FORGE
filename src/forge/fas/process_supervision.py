"""Shell-free local process evidence for the FAS-027 lifecycle boundary."""

from __future__ import annotations

import hashlib
import math
import subprocess
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any


class ProcessSupervisionError(ValueError):
    """Raised when a process request cannot be evaluated safely."""


class LocalProcessSupervisor:
    """Run a bounded local command and return non-authoritative evidence."""

    def run(
        self,
        command: Sequence[str],
        *,
        cwd: str | Path,
        timeout_seconds: float,
        environment: Mapping[str, str] | None = None,
    ) -> dict[str, Any]:
        normalized = self._command(command)
        timeout = self._timeout(timeout_seconds)
        workdir = Path(cwd)
        if not workdir.is_dir():
            raise ProcessSupervisionError("process working directory must exist")
        env = self._environment(environment)
        try:
            process = subprocess.Popen(
                normalized,
                cwd=workdir,
                env=env,
                shell=False,
                stdin=subprocess.DEVNULL,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )
        except OSError as exc:
            raise ProcessSupervisionError("process could not be started") from exc

        outcome = "completed"
        try:
            stdout, stderr = process.communicate(timeout=timeout)
        except subprocess.TimeoutExpired:
            outcome = "timed_out"
            process.terminate()
            try:
                stdout, stderr = process.communicate(timeout=1.0)
            except subprocess.TimeoutExpired:
                process.kill()
                stdout, stderr = process.communicate()
        if outcome == "completed" and process.returncode != 0:
            outcome = "crashed"
        return {
            "schema_version": "1.0.0",
            "outcome": outcome,
            "returncode": process.returncode,
            "stdout_bytes": len(stdout),
            "stderr_bytes": len(stderr),
            "stdout_digest": self._digest(stdout),
            "stderr_digest": self._digest(stderr),
            "shell_used": False,
            "physical_commands_allowed": False,
            "release_authority_granted": False,
            "worker_reuse_allowed": False,
            "resource_limits_enforced": False,
            "requires_reviewed_resource_supervisor": True,
        }

    @staticmethod
    def _command(command: Sequence[str]) -> list[str]:
        if isinstance(command, (str, bytes)) or not command:
            raise ProcessSupervisionError("command must be a non-empty argument list")
        normalized = list(command)
        if any(
            not isinstance(arg, str) or not arg or "\x00" in arg for arg in normalized
        ):
            raise ProcessSupervisionError("command arguments must be non-empty text")
        return normalized

    @staticmethod
    def _timeout(value: float) -> float:
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            raise ProcessSupervisionError("timeout must be numeric")
        if not math.isfinite(value) or value <= 0 or value > 3600:
            raise ProcessSupervisionError(
                "timeout must be finite and between 0 and 3600 seconds"
            )
        return float(value)

    @staticmethod
    def _environment(environment: Mapping[str, str] | None) -> dict[str, str] | None:
        if environment is None:
            return None
        if not isinstance(environment, Mapping) or any(
            not isinstance(key, str)
            or not key
            or "\x00" in key
            or not isinstance(value, str)
            or "\x00" in value
            for key, value in environment.items()
        ):
            raise ProcessSupervisionError(
                "environment must contain text keys and values"
            )
        return dict(environment)

    @staticmethod
    def _digest(value: bytes) -> str:
        return "sha256:" + hashlib.sha256(value).hexdigest()
