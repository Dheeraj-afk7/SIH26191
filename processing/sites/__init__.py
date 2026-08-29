"""
SIH26191 -- processing.sites
==============================================================================
Step 9: Candidate Topographically Feasible Area Identification sub-package.

Modules
-------
identify_candidate_areas : Deterministic terrain-based screening to identify
                           Candidate Topographically Feasible Areas from
                           existing hazard, hydrology, and terrain layers.

Core Principles
---------------
- All exclusion criteria are deterministic and derived from verified Step 3–7
  outputs already present in the repository.
- Configurable screening parameters default to null; null means NOT CONFIGURED
  (the corresponding screening step is skipped, not silently given a default).
- No thresholds are invented. All applied values must have documented justification.
- Outputs are labelled ONLY as "Candidate Topographically Feasible Area" or
  "Preliminary Topographically Feasible Terrain".
- Outputs are decision-support screening layers, NOT safe site certifications,
  official relocation authorizations, or engineering-certified locations.
- Step 9B (base) outputs are never overwritten by Step 9C (attributed) outputs.
  They are written to separate files with _base and _attributed suffixes.

MANDATORY DISCLAIMER (all outputs):
    Preliminary decision-support candidate requiring field verification.
    Not an official site authorization or safety certification.
    Geotechnical and infrastructure assessment required before any relocation action.

SIH26191 -- Rudraprayag District, Uttarakhand, India
"""
