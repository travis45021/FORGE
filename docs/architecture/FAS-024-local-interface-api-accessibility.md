# FAS-024: Local Interface, API, and Accessibility

Status: Implemented baseline  
Historical source: FAS-023

FORGE v1 has one safe request path. The local application, CLI, Builder,
accessible presentation, and versioned local API authenticate a local identity
and send meaningful actions through the Interface Gateway to the Executive.
No presentation exposes a raw-hardware control path.

The Simple, Builder, Advanced, Accessible, and Developer modes change
presentation, not authority or stored hardware definitions. Action and approval
views state what will happen, why, the affected target, safety conditions,
reversibility, failure handling, scope, expiry, and data behavior. Standing
authority is visibly distinct from one-time confirmation.

The v1 API negotiates an explicit version, returns structured plain-language
errors, and keeps live event subscriptions observational. Ordinary operation is
local and requires no cloud account. Remote administration, cloud dashboards,
mobile clients, and public APIs remain later work.

Accessibility is part of the first release: equivalent core workflows are
keyboard operable and screen-reader readable, use non-color cues, support
adjustable text and reduced motion, and never depend on pointer-only actions.
