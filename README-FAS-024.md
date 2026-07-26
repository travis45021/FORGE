# FAS-024 Reference Implementation

`forge.fas.interfaces.InterfaceGateway` implements the local-first, versioned
boundary shared by FORGE user interfaces, CLI clients, and local integrations.
It routes meaningful actions to the Executive, makes approvals and data behavior
visible, supplies structured errors, and preserves equivalent accessible flows.

The gateway contains no direct hardware command surface.
