#!/usr/bin/env python3
"""
SIH26191 -- Phase B: Disaster History Data Validator & Integration Pipeline
===========================================================================

Validates district disaster incident records against schema.json and prepares
proximity-based habitation exposure context.

STATUS: SCHEMA_PREPARED -- PENDING OFFICIAL USDMA/NDMA DATA ACQUISITION
"""

import json
import logging
import pathlib
import sys
from typing import Dict, Any, List

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)

ROOT = pathlib.Path(__file__).resolve().parent.parent.parent
SCHEMA_PATH = ROOT / "data" / "processed" / "disaster_history" / "schema.json"


def load_schema() -> Dict[str, Any]:
    if not SCHEMA_PATH.exists():
        raise FileNotFoundError(f"Schema not found at {SCHEMA_PATH}")
    with open(SCHEMA_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def validate_incident_record(record: Dict[str, Any], schema_def: Dict[str, Any]) -> List[str]:
    """Validate a single incident record against schema fields."""
    errors = []
    fields = schema_def.get("schema", {})

    for field_name, field_spec in fields.items():
        if field_spec.get("required", False) and field_name not in record:
            errors.append(f"Missing required field '{field_name}'")

    # Check enum values
    if "hazard_type" in record:
        valid_hazards = fields.get("hazard_type", {}).get("enum", [])
        if record["hazard_type"] not in valid_hazards:
            errors.append(f"Invalid hazard_type '{record['hazard_type']}'. Expected one of {valid_hazards}")

    if "severity" in record:
        valid_severities = fields.get("severity", {}).get("enum", [])
        if record["severity"] not in valid_severities:
            errors.append(f"Invalid severity '{record['severity']}'. Expected one of {valid_severities}")

    if "verified_source" in record:
        valid_sources = fields.get("verified_source", {}).get("enum", [])
        if record["verified_source"] not in valid_sources:
            errors.append(f"Invalid verified_source '{record['verified_source']}'. Expected one of {valid_sources}")

    return errors


def main():
    logger.info("SIH26191 -- Step 10E: Disaster History Validation Pipeline")
    schema_def = load_schema()
    logger.info(f"Loaded schema v{schema_def.get('schema_version', '1.0')}")
    logger.info(f"Integration status: {schema_def.get('status')}")

    # Check known incidents in schema
    known = schema_def.get("known_major_incidents", {}).get("incidents", [])
    logger.info(f"Validating {len(known)} reference incident records...")

    for inc in known:
        errs = validate_incident_record(inc, schema_def)
        if errs:
            logger.warning(f"Record {inc.get('incident_id')} validation issues: {errs}")
        else:
            logger.info(f"Record {inc.get('incident_id')} ({inc.get('hazard_type')} - {inc.get('date')}): VALID")

    logger.info("Disaster history pipeline is schema-ready for USDMA/NDMA dataset ingestion.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
