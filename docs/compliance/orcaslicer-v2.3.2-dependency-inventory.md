# OrcaSlicer v2.3.2 Dependency Inventory Baseline

Status: Preliminary inventory; compatibility review incomplete  
Recorded: 2026-07-26

The pinned archive exposes **55** distinct dependency roots across `deps/` and
`deps_src/`. Examples include Boost, CGAL, CURL, Expat, OpenSSL, OpenVDB,
OpenCV, wxWidgets, Eigen, libigl, MCUT, qhull, ImGui, Catch2, and Swiper web
assets. The archive also contains **11,062** members under
`resources/profiles/`, plus translation/localization markers.

This baseline is an inventory of archive structure, not a complete SBOM or
license conclusion. Each dependency still needs source/version provenance,
license and notice classification, build reachability, generated/bundled asset
review, and compatibility analysis for the intended FORGE distribution. The
profile and asset tree additionally needs a redistribution/trademark review.

No Orca source has been imported into the trusted FORGE tree. Gate 1 remains
open until the inventory is classified and tied to a reproducible build and
source-offer record.
