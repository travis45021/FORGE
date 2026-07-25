"""Layered, reversible configuration management for FAS-021."""
from copy import deepcopy

class ConfigurationError(ValueError): pass

ORDER=("safe_defaults","machine_components","material_process","validated_calibration","mission","user")

class ConfigurationManager:
    def __init__(self):
        self._profiles={}; self._active=None; self._history=[]
    def register(self, profile):
        p=deepcopy(dict(profile)); required={"profile_id","family","version","values","hard_limits","provenance","status"}
        if required-p.keys(): raise ConfigurationError("profile missing fields")
        if p["family"] not in ORDER: raise ConfigurationError("unknown profile family")
        if not p["provenance"]: raise ConfigurationError("profile requires provenance")
        if p["profile_id"] in self._profiles: raise ConfigurationError("profile identity is immutable")
        if p["status"] not in {"provisional","validated"}: raise ConfigurationError("invalid profile status")
        self._profiles[p["profile_id"]]=p; return deepcopy(p)
    def resolve(self, profile_ids):
        profiles=[self._profiles[i] for i in profile_ids]
        profiles.sort(key=lambda p:ORDER.index(p["family"]))
        values={}; limits={}
        for p in profiles:
            for k,v in p["hard_limits"].items():
                if k in limits and v>limits[k]: raise ConfigurationError("hard limit cannot be weakened")
                limits[k]=v
            for k,v in p["values"].items():
                if k in limits and isinstance(v,(int,float)) and v>limits[k]:
                    raise ConfigurationError("resolved value exceeds hard limit")
                values[k]=deepcopy(v)
        return {"profile_ids":[p["profile_id"] for p in profiles],"values":values,"hard_limits":limits}
    def apply_change(self, request, *, active_mission=False):
        r=deepcopy(dict(request)); required={"change_id","base_profile_id","new_profile","material","verified","backup_id","rollback_profile_id","authorized"}
        if required-r.keys(): raise ConfigurationError("change request missing fields")
        if r["material"] and not all((r["verified"],r["backup_id"],r["rollback_profile_id"],r["authorized"])):
            raise ConfigurationError("material change requires verification, backup, rollback, and authority")
        if active_mission and r["material"]: raise ConfigurationError("material change blocked during active Mission")
        if r["new_profile"].get("source") in {"ai","community"} and r["new_profile"].get("status")!="provisional":
            raise ConfigurationError("AI and community profiles must remain provisional")
        self.register(r["new_profile"]); prior=self._active; self._active=r["new_profile"]["profile_id"]
        self._history.append({"change_id":r["change_id"],"from":prior,"to":self._active,"rollback":r["rollback_profile_id"]})
        return deepcopy(self._profiles[self._active])
    def rollback(self, profile_id, *, authorized):
        if not authorized: raise ConfigurationError("rollback requires authority")
        if profile_id not in self._profiles: raise ConfigurationError("unknown rollback profile")
        self._active=profile_id; return deepcopy(self._profiles[profile_id])
    def history(self): return deepcopy(self._history)
