"""
SIH26191 -- Candidate Hazard-Based Red Zone Generation Module (Step 7)
======================================================================
Provides algorithms and routines to identify, filter, prioritize, and vectorize
contiguous spatial regions classified as Higher Multi-Hazard Indicators into
Candidate Hazard-Based Red Zones for preliminary decision support.

Key Functions:
  - identify_candidate_zones: Deterministic connected-components segmentation,
                              minimum mapping unit filtering, zonal statistical
                              summarization, priority ranking, and vector export.
"""

from pathlib import Path

__version__ = "1.0.0"
__author__ = "SIH26191 Core Pipeline"
