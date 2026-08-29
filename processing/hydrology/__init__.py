"""
SIH26191 -- Hydrology Processing Module (Step 5)
==============================================================================
Package containing deterministic terrain-derived hydrological processing
algorithms, flow routing, Topographic Wetness Index (TWI), continuous flood
exposure proxy derivation, and preliminary screening classification for the
SIH26191 decision-support pipeline.

Pilot Region: Rudraprayag District, Uttarakhand, India

MODULES:
--------
- derive_hydrological_derivatives: Computes D8 Flow Direction, Flow Accumulation, and TWI.
- derive_flood_exposure: Derives continuous normalized flood exposure proxy.
- classify_flood_exposure: Classifies continuous proxy into 3 screening tiers.

SCIENTIFIC GOVERNANCE:
----------------------
This module provides deterministic terrain screening indicators for decision
support. It DOES NOT predict floods, forecast inundation, certify safety, or
authorize evacuation/relocation.
"""

__version__ = "1.0.0"
