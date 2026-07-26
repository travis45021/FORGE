# OrcaSlicer Upstream Provenance Record

Status: Initial evidence; file-level audit incomplete  
Recorded: 2026-07-26

## Pinned review baseline

- Upstream project: OrcaSlicer
- Official repository: `https://github.com/OrcaSlicer/OrcaSlicer`
- Stable release tag: `v2.3.2`
- Release commit:
  `c724a3f5f51c52336624b689e846c8fbc943a912`
- Release page:
  `https://github.com/OrcaSlicer/OrcaSlicer/releases/tag/v2.3.2`
- License source:
  `https://github.com/OrcaSlicer/OrcaSlicer/blob/v2.3.2/LICENSE.txt`

This pin selects the source to audit and reproduce. It does not approve source
import, establish the final FORGE SPDX expression, or represent a completed
compatibility review.

## Release-page verification

On 2026-07-26, the official release page was checked and confirmed the v2.3.2
tag, the abbreviated commit `c724a3f`, and the release's documented 3MF import
path-traversal security fix. This verifies the release reference only; it is
not a substitute for archiving the exact source/license bytes and hashing them.

## Archived license evidence

- Archived file: `upstream-orcaslicer-v2.3.2-LICENSE.txt`
- Source URL: `https://raw.githubusercontent.com/OrcaSlicer/OrcaSlicer/v2.3.2/LICENSE.txt`
- SHA-256: `57c8ff33c9c0cfc3ef00e650a1cc910d7ee479a8bc509f6c9209a7c2a11399d6`
- Scope: license-text evidence only; source archive and file-level inventory
  remain open.

## Source archive digest verification

- Archive URL: `https://github.com/OrcaSlicer/OrcaSlicer/archive/refs/tags/v2.3.2.tar.gz`
- Retrieved to temporary isolated storage on 2026-07-26 and removed after hashing
- SHA-256: `2c7eea7b1e3757011f2c9520dc1712d789b9182b5c276aba271bf814172b0a52`
- Byte length: `118753412`
- Scope: digest verified; durable archive retention and file-level inventory
  remain open before Gate 1 closure.

## Initial upstream declarations

The upstream release describes OrcaSlicer as licensed under GNU Affero General
Public License version 3. Its README also identifies:

- a pressure-advance calibration pattern under GNU GPL version 3; and
- an optional Bambu networking plugin based on non-free BambuLab libraries.

The FORGE trusted baseline excludes that optional networking plugin. The audit
must still prove that neither the plugin nor its binaries enter the build,
download, packaging, runtime, update, or test graphs.

## Security note

The v2.3.2 release reports a security fix for path traversal during 3MF import.
FORGE must retain its own quarantine and hostile-file tests and must not assume
that pinning this version makes imported 3MF content safe.

## Evidence still required

The controlled status of each item is tracked in
[`GATE-1-EVIDENCE-INDEX.md`](GATE-1-EVIDENCE-INDEX.md). No item below is
considered complete merely because the pin is recorded.

- Archive the exact source and license files and record cryptographic digests.
- Enumerate file-level copyright and license headers.
- Resolve submodules, vendored libraries, assets, profiles, translations,
  calibration content, and generated files.
- Reproduce the upstream build from the pinned source.
- Prove the excluded non-free networking component is unreachable and unshipped.
- Decide the final `AGPL-3.0-only` or `AGPL-3.0-or-later` expression from the
  collected evidence.
