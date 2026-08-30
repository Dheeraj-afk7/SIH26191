#!/usr/bin/env python3
"""
SIH26191 -- Phase F: Authority Action Center API
=================================================

Provides SDMA/DDMA-facing decision-support endpoints:

  GET /api/authority/action-queue   -- Tier 1 + Tier 2 villages, sorted by urgency
  GET /api/authority/block-summary  -- Aggregated by tehsil/block
  GET /api/authority/report.csv     -- Exportable priority action report

DISCLAIMER: All outputs are DECISION SUPPORT ONLY.
NOT official relocation orders or government declarations.
All outputs require SDMA/DDMA authorization before any planning action.
"""

import io
import csv
import json
import logging
from typing import Optional
from fastapi import APIRouter, Query
from fastapi.responses import StreamingResponse
from backend.services.data_loader import data_store
import pandas as pd

logger = logging.getLogger(__name__)
router = APIRouter()

_AUTHORITY_DISCLAIMER = (
    "DECISION SUPPORT ONLY -- NOT AN OFFICIAL RELOCATION ORDER, EVACUATION NOTICE, "
    "OR GOVERNMENT DECLARATION. All classifications are based on preliminary GIS "
    "screening using Census 2011 data and terrain proxies. Field verification, "
    "geotechnical assessment, and official SDMA/DDMA authorization are required "
    "before any administrative action."
)

# Recommended actions per tier for display in the action center
_TIER_RECOMMENDED_ACTION = {
    "Tier1_AttentionPriority": (
        "Recommend immediate field verification by SDMA/district team. "
        "Schedule geotechnical survey. Community consultation required "
        "before any relocation planning action."
    ),
    "Tier2_ElevatedAttention": (
        "Include in 1-3 year district hazard planning cycle. "
        "Block-level vulnerability mapping and infrastructure audit advised."
    ),
    "Tier3_Monitoring": (
        "Include in district hazard monitoring programme. "
        "Update assessment when new hazard data is available."
    ),
    "BeyondProximity": (
        "Include in periodic district hazard survey update cycle. "
        "No immediate action indicated by current screening."
    ),
}

_ACTION_TIERS = ["Tier1_AttentionPriority", "Tier2_ElevatedAttention"]


def _safe_get(row, col, default=None):
    val = row.get(col, default)
    if pd.isna(val) if val is not None else False:
        return default
    return val


@router.get("/authority/action-queue")
def get_action_queue(
    tiers: Optional[str] = Query(
        "Tier1_AttentionPriority,Tier2_ElevatedAttention",
        description="Comma-separated tier names. Default: Tier 1 and Tier 2.",
    ),
    high_vuln_only: bool = Query(False, description="If True, show only villages with vulnerability_flag_count >= 2"),
    limit: int = Query(200, description="Max villages to return"),
):
    """
    Returns the SDMA action queue: villages sorted by urgency (proximity to hazard zone).
    Default: Tier 1 (Immediate) and Tier 2 (Short-Term) villages only.
    Sorted by nearest_hazard_distance_m ascending (closest to hazard first).
    """
    df = data_store.villages
    if df.empty:
        return {
            "status": "NO_DATA",
            "message": "Village profiles not loaded. Run processing pipeline first.",
            "disclaimer": _AUTHORITY_DISCLAIMER,
        }

    tier_list = [t.strip() for t in tiers.split(",")]
    valid_tiers = ["Tier1_AttentionPriority", "Tier2_ElevatedAttention", "Tier3_Monitoring", "BeyondProximity"]
    tier_list = [t for t in tier_list if t in valid_tiers]
    if not tier_list:
        tier_list = _ACTION_TIERS

    queue = df[df["priority_tier"].isin(tier_list)].copy()

    if high_vuln_only and "vulnerability_flag_count" in queue.columns:
        queue = queue[queue["vulnerability_flag_count"] >= 2]

    if "nearest_hazard_distance_m" in queue.columns:
        queue = queue.sort_values("nearest_hazard_distance_m", ascending=True)

    queue = queue.head(limit)

    results = []
    for _, row in queue.iterrows():
        tier = _safe_get(row, "priority_tier", "Unknown")
        # Build active vulnerability flags list
        vuln_flags = []
        flag_map = {
            "vf_high_child_pop": "High Child Population",
            "vf_high_sc": "High SC Population",
            "vf_high_dependency": "High Dependency Ratio",
            "vf_high_illiteracy": "High Illiteracy Rate",
        }
        for field, label in flag_map.items():
            if field in row and row[field]:
                vuln_flags.append(label)

        results.append({
            "village_id": _safe_get(row, "village_id"),
            "village_name": _safe_get(row, "village_name", "Unknown"),
            "priority_tier": tier,
            "priority_tier_display": _safe_get(row, "priority_tier_display", tier),
            "relocation_horizon": _safe_get(row, "relocation_horizon", "UNKNOWN"),
            "relocation_horizon_display": _safe_get(row, "relocation_horizon_display", "Unknown"),
            "nearest_hazard_distance_m": _safe_get(row, "nearest_hazard_distance_m"),
            "tot_pop": _safe_get(row, "tot_pop"),
            "households": _safe_get(row, "households"),
            "mh_class_at_centroid": _safe_get(row, "mh_class_at_centroid"),
            "vulnerability_flag_count": _safe_get(row, "vulnerability_flag_count", 0),
            "vulnerability_context": _safe_get(row, "vulnerability_context", "0 of 4 vulnerability factors flagged"),
            "active_vulnerability_flags": vuln_flags,
            "recommended_action": _safe_get(
                row, "recommended_action",
                _TIER_RECOMMENDED_ACTION.get(tier, "Field assessment recommended.")
            ),
            "priority_reason": _safe_get(row, "priority_reason", ""),
            "nearest_zone_id": _safe_get(row, "nearest_zone_id"),
        })

    # Summary statistics
    tier_counts = df[df["priority_tier"].isin(tier_list)]["priority_tier"].value_counts().to_dict()
    total_at_risk_pop = int(df[df["priority_tier"].isin(tier_list)]["tot_pop"].sum())
    total_at_risk_hh = int(df[df["priority_tier"].isin(tier_list)]["households"].sum())

    return {
        "disclaimer": _AUTHORITY_DISCLAIMER,
        "screening_date": "2026-08-30",
        "district": "Rudraprayag, Uttarakhand",
        "total_villages_screened": len(df),
        "action_queue_summary": {
            "tier_counts": tier_counts,
            "total_at_risk_population": total_at_risk_pop,
            "total_at_risk_households": total_at_risk_hh,
        },
        "action_queue": results,
        "note": (
            "Villages sorted by proximity to nearest Candidate Hazard-Based Red Zone "
            "(closest first). Tier 1 = Immediate Field Assessment; Tier 2 = Short-Term Planning."
        ),
    }


@router.get("/authority/block-summary")
def get_block_summary():
    """
    Returns block/tehsil-level aggregation of village risk tiers.
    Useful for district planning meetings and resource allocation.
    """
    df = data_store.villages
    if df.empty:
        return {"status": "NO_DATA", "disclaimer": _AUTHORITY_DISCLAIMER}

    # Try to aggregate by sub-district (block/tehsil)
    # shrug_subdist_id is available in the data
    if "shrug_subdist_id" not in df.columns:
        return {
            "status": "BLOCK_ID_UNAVAILABLE",
            "message": "Sub-district ID not available. Block aggregation requires shrug_subdist_id.",
            "disclaimer": _AUTHORITY_DISCLAIMER,
        }

    tiers = ["Tier1_AttentionPriority", "Tier2_ElevatedAttention", "Tier3_Monitoring", "BeyondProximity"]
    summary = []

    for subdist_id, group in df.groupby("shrug_subdist_id"):
        tier_counts = {t: int((group["priority_tier"] == t).sum()) for t in tiers}
        total_pop = int(group["tot_pop"].sum())
        at_risk_pop = int(group[group["priority_tier"].isin(["Tier1_AttentionPriority", "Tier2_ElevatedAttention"])]["tot_pop"].sum())
        high_vuln_count = 0
        if "vulnerability_flag_count" in group.columns:
            high_vuln_count = int((group["vulnerability_flag_count"] >= 2).sum())

        summary.append({
            "subdist_id": subdist_id,
            "total_villages": len(group),
            "total_population": total_pop,
            "tier1_immediate": tier_counts.get("Tier1_AttentionPriority", 0),
            "tier2_short_term": tier_counts.get("Tier2_ElevatedAttention", 0),
            "tier3_monitoring": tier_counts.get("Tier3_Monitoring", 0),
            "beyond_proximity": tier_counts.get("BeyondProximity", 0),
            "at_risk_population_tier1_2": at_risk_pop,
            "high_vulnerability_villages": high_vuln_count,
        })

    summary.sort(key=lambda x: x["tier1_immediate"] + x["tier2_short_term"], reverse=True)

    return {
        "disclaimer": _AUTHORITY_DISCLAIMER,
        "district": "Rudraprayag, Uttarakhand",
        "total_villages_screened": len(df),
        "block_summary": summary,
        "note": "Sorted by combined Tier 1 + Tier 2 village count (highest priority blocks first).",
    }


@router.get("/authority/report.csv")
def download_priority_report(
    tiers: Optional[str] = Query(
        "Tier1_AttentionPriority,Tier2_ElevatedAttention",
        description="Comma-separated tier names to include in report",
    ),
):
    """
    Download a CSV priority action report for SDMA use.
    Includes all Tier 1 and Tier 2 villages with recommended actions.
    """
    df = data_store.villages
    if df.empty:
        return {"status": "NO_DATA", "disclaimer": _AUTHORITY_DISCLAIMER}

    tier_list = [t.strip() for t in tiers.split(",")]
    valid_tiers = ["Tier1_AttentionPriority", "Tier2_ElevatedAttention", "Tier3_Monitoring", "BeyondProximity"]
    tier_list = [t for t in tier_list if t in valid_tiers]
    if not tier_list:
        tier_list = _ACTION_TIERS

    report_df = df[df["priority_tier"].isin(tier_list)].copy()

    if "nearest_hazard_distance_m" in report_df.columns:
        report_df = report_df.sort_values("nearest_hazard_distance_m", ascending=True)

    # Select and rename columns for the report
    col_map = {
        "village_id": "Village_ID",
        "village_name": "Village_Name",
        "priority_tier": "Priority_Tier",
        "priority_tier_display": "Priority_Label",
        "relocation_horizon_display": "Planning_Category",
        "nearest_hazard_distance_m": "Distance_to_Hazard_Zone_m",
        "tot_pop": "Total_Population",
        "households": "Households",
        "mh_class_at_centroid": "MH_Class_at_Centroid",
        "vulnerability_flag_count": "Vulnerability_Flags",
        "vulnerability_context": "Vulnerability_Context",
        "recommended_action": "Recommended_Action",
        "priority_reason": "Classification_Reason",
        "nearest_zone_id": "Nearest_Red_Zone_ID",
        "shrug_subdist_id": "Sub_District_ID",
    }

    available_cols = {k: v for k, v in col_map.items() if k in report_df.columns}
    export_df = report_df[list(available_cols.keys())].rename(columns=available_cols)

    # Add disclaimer row at top
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow([f"# DISCLAIMER: {_AUTHORITY_DISCLAIMER}"])
    writer.writerow([f"# Generated: 2026-08-30 | District: Rudraprayag, Uttarakhand"])
    writer.writerow([f"# Tiers included: {', '.join(tier_list)} | Total villages: {len(export_df)}"])
    writer.writerow([])

    export_df.to_csv(output, index=False)

    output.seek(0)
    return StreamingResponse(
        io.BytesIO(output.getvalue().encode("utf-8")),
        media_type="text/csv",
        headers={
            "Content-Disposition": "attachment; filename=rudraprayag_priority_action_report.csv"
        },
    )
