"""Local-first onboarding and experience profiles for FAS-020."""

from __future__ import annotations

from copy import deepcopy
from typing import Any, Mapping


class OnboardingError(ValueError):
    """Raised when onboarding violates FAS-020."""


PROFILES = {
    "offline_manual": {
        "network_mode": "offline",
        "ai_enabled": False,
        "suggestions_enabled": False,
        "hardware_setup": "manual_or_custom",
        "interaction_profile": "quiet",
        "operational_twin_enabled": False,
    },
    "simple_local": {
        "network_mode": "local",
        "ai_enabled": False,
        "suggestions_enabled": False,
        "hardware_setup": "guided",
        "interaction_profile": "simple",
        "operational_twin_enabled": False,
    },
    "custom_builder": {
        "network_mode": "local",
        "ai_enabled": False,
        "suggestions_enabled": False,
        "hardware_setup": "custom",
        "interaction_profile": "simple",
        "operational_twin_enabled": True,
    },
}
FUTURE_PROFILES = {"assisted", "supervised_automation", "autonomous_path"}


class OnboardingService:
    """Configures user-visible choices without silently expanding authority."""

    def __init__(self) -> None:
        self._profiles: dict[str, dict[str, Any]] = {}
        self._history: list[dict[str, Any]] = []

    def create_local_profile(
        self, local_id: str, *, display_name: str
    ) -> dict[str, Any]:
        if not local_id.startswith("local-user:"):
            raise OnboardingError("local identity must use local-user namespace")
        if local_id in self._profiles:
            raise OnboardingError("local identity already exists")
        if not display_name.strip():
            raise OnboardingError("display name is required")
        record = {
            "schema_version": "1.0.0",
            "local_id": local_id,
            "display_name": display_name.strip(),
            "network_identity": None,
            "experience_profile": None,
            "settings": None,
            "automation_authority": "manual",
            "sharing_consent": False,
            "onboarding_complete": False,
        }
        self._profiles[local_id] = record
        self._record("user.profile.created", local_id, "local_profile_created")
        return deepcopy(record)

    def select_experience(
        self, local_id: str, experience_profile: str
    ) -> dict[str, Any]:
        record = self._require(local_id)
        if experience_profile in FUTURE_PROFILES:
            raise OnboardingError("experience profile is future-gated")
        if experience_profile not in PROFILES:
            raise OnboardingError("unknown experience profile")
        record["experience_profile"] = experience_profile
        record["settings"] = deepcopy(PROFILES[experience_profile])
        record["automation_authority"] = "manual"
        record["onboarding_complete"] = True
        self._record(
            "experience.profile.selected", local_id, experience_profile
        )
        return deepcopy(record)

    def update_settings(
        self, local_id: str, changes: Mapping[str, Any]
    ) -> dict[str, Any]:
        record = self._require(local_id)
        if record["settings"] is None:
            raise OnboardingError("select an experience profile first")
        forbidden = {"automation_authority", "network_identity", "sharing_consent"}
        if forbidden & changes.keys():
            raise OnboardingError("material authority or identity needs explicit flow")
        allowed = set(PROFILES["simple_local"])
        unknown = set(changes) - allowed
        if unknown:
            raise OnboardingError(
                "unknown experience settings: " + ", ".join(sorted(unknown))
            )
        if "ai_enabled" in changes and not isinstance(changes["ai_enabled"], bool):
            raise OnboardingError("ai_enabled must be boolean")
        if "suggestions_enabled" in changes and not isinstance(
            changes["suggestions_enabled"], bool
        ):
            raise OnboardingError("suggestions_enabled must be boolean")
        record["settings"].update(deepcopy(dict(changes)))
        self._record("experience.preference.changed", local_id, "user_changed")
        return deepcopy(record)

    def set_network_participation(
        self,
        local_id: str,
        *,
        network_mode: str,
        sharing_consent: bool,
        network_identity: str | None = None,
    ) -> dict[str, Any]:
        record = self._require(local_id)
        if network_mode not in {"offline", "local", "shared_services"}:
            raise OnboardingError("unknown network mode")
        if network_mode == "shared_services":
            if sharing_consent is not True or not network_identity:
                raise OnboardingError(
                    "shared services require consent and separate identity"
                )
        else:
            if sharing_consent:
                raise OnboardingError("sharing consent requires shared services")
            network_identity = None
        record["settings"]["network_mode"] = network_mode
        record["sharing_consent"] = sharing_consent
        record["network_identity"] = network_identity
        self._record(
            "network.participation.changed", local_id, network_mode
        )
        return deepcopy(record)

    def set_automation_authority(
        self,
        local_id: str,
        *,
        authority: str,
        authorization_verified: bool,
    ) -> dict[str, Any]:
        record = self._require(local_id)
        if authority != "manual":
            raise OnboardingError(
                "v1 onboarding exposes direct user-requested workflows only"
            )
        if authorization_verified is not True:
            raise OnboardingError("authority changes require verification")
        record["automation_authority"] = authority
        self._record("automation.authority.changed", local_id, authority)
        return deepcopy(record)

    def summary(self, local_id: str) -> dict[str, Any]:
        record = self._require(local_id)
        settings = record["settings"]
        if settings is None:
            return {"local_id": local_id, "status": "onboarding_incomplete"}
        return {
            "local_id": local_id,
            "display_name": record["display_name"],
            "experience_profile": record["experience_profile"],
            "network": settings["network_mode"],
            "ai": "on" if settings["ai_enabled"] else "off",
            "suggestions": "on" if settings["suggestions_enabled"] else "off",
            "hardware_setup": settings["hardware_setup"],
            "automation": record["automation_authority"],
            "operational_twin": (
                "on" if settings["operational_twin_enabled"] else "off"
            ),
        }

    def export(self, local_id: str) -> dict[str, Any]:
        return deepcopy(self._require(local_id))

    def history(self) -> list[dict[str, str]]:
        return deepcopy(self._history)

    def _require(self, local_id: str) -> dict[str, Any]:
        try:
            return self._profiles[local_id]
        except KeyError as exc:
            raise OnboardingError(f"unknown local identity: {local_id}") from exc

    def _record(self, event_type: str, local_id: str, reason: str) -> None:
        self._history.append(
            {"event_type": event_type, "local_id": local_id, "reason": reason}
        )
