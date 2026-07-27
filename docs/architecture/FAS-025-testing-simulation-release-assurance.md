# FAS-025: Testing, Simulation, and Release Assurance

Status: Implemented baseline  
Historical source: FAS-024

FORGE uses separate unit, contract, integration, scenario, fault-injection,
security, hardware-in-the-loop, and release assurance layers. Test results
capture versions, configuration, providers, inputs, events, runtime context,
expectations, observations, and variability needed for reproduction.

Simulated providers are explicitly labeled, declare modeled behavior and
limitations, and are never production eligible. Simulation is evidence or a
hypothesis; it cannot authorize physical work. Production still requires a real
provider, verification, policy, and authority.

Hardware-in-the-loop tests require identified hardware, user authority, strict
limits, stop conditions, minimal action, monitoring, recovery, and recorded
measurements. They remain visibly distinct from production Missions.

Every release has an assurance record covering components, supported
environments, tests, limitations, reviews, migration, rollback, documentation,
and integrity. Required failures, security-critical regressions, incomplete
security or compatibility review, absent rollback, invalid SHA-256 integrity,
or incomplete documentation block progression. A passing FAS-025 assessment is
only ready for the FAS-037 release gate; it never authorizes release or
physical execution. Maturity claims remain bounded by recorded evidence.
