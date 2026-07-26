# Isolated Slicer Worker Boundary

The worker manifest defines the Gate 4 isolation contract. Production and twin
workers receive separate input, output, and log workspaces and explicit
timeout, memory, and disk limits. Cancellation and crash recovery are part of
the worker supervisor, not the slicer engine.

The worker must declare `printer_control` among its forbidden capabilities.
Printer discovery, cloud access, upload, update, telemetry, and print-start
paths are outside the worker contract. The worker returns evidence and derived
artifacts; FORGE authorization and the mandatory final user confirmation stay
in the Executive/runtime path.

This manifest is a contract-only artifact. It does not authorize Orca source
import or a production build while Gate 1 remains open.
