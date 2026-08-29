"""
SIH26191 -- processing.hazards
==============================================================================
Hazard processing sub-package for the SIH26191 pilot pipeline.

Modules
-------
derive_terrain_susceptibility   : Calculates a continuous, deterministic
                                  terrain-derived landslide susceptibility proxy
                                  from metric slope.
classify_terrain_susceptibility : Classifies the continuous susceptibility proxy
                                  into explainable screening indicator categories.

Core Principles
---------------
- Slope is the PRIMARY physical terrain factor influencing gravitational shear stress.
- Aspect is maintained strictly as contextual terrain metadata without arbitrary hazard weighting.
- All calculations are deterministic, monotonic, and rule-based.
- No machine learning, black-box weighting, or synthetic probability claims are used.
- All thresholds and parameters are loaded dynamically from configs/project.yaml.
- Outputs are decision-support screening layers, NOT landslide predictions or official hazard zones.
"""
