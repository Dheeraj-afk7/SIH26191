"""
SIH26191 -- Multi-Hazard Integration Module (Step 6)
==============================================================================
Provides deterministic, explainable, and configuration-driven integration
of terrain susceptibility and hydrological flood screening proxies into a
unified Multi-Hazard Screening Indicator.

Pilot   : Rudraprayag District, Uttarakhand, India
Project : SIH26191
"""

from .derive_multihazard_score import derive_multihazard_score
from .classify_multihazard import classify_multihazard

__all__ = [
    "derive_multihazard_score",
    "classify_multihazard",
]
