# Security & Privacy: SIH26191

## Current Implemented Security Mechanisms

### 1. API Architecture & Input Validation
- **Stateless Microservice:** The FastAPI backend is completely stateless, storing no persistent session tokens or client-side session state that could be hijacked.
- **Strict Pydantic Type Enforcement:** All incoming API payloads (e.g., `POST /api/pipeline/recompute`) and URL query parameters (`limit`, `offset`, `priority_tier`, `bbox`) are strictly validated against Pydantic schemas. Unrecognized keys, malformed types, or invalid pipeline steps return `422 Unprocessable Entity` responses.
- **SQL / NoSQL Injection Immunity:** The platform uses in-memory GeoPandas DataFrames and flat file structures (GeoPackage, GeoJSON), eliminating standard SQL/NoSQL injection attack surfaces.

### 2. Cross-Origin Resource Sharing (CORS) Protection
- **Middleware:** FastAPI `CORSMiddleware` configured in `backend/main.py`.
- **Domain Whitelisting:** Configured in `backend/core/config.py` via `settings.cors_origins` to restrict cross-origin browser requests to authorized frontend client domains and local development origins (`http://localhost:3000`, `http://localhost:5173`, `https://sih-26191.vercel.app/`).

### 3. Pipeline Execution Security & Subprocess Isolation
- **Step Whitelisting:** Dynamic pipeline recomputation (`POST /api/pipeline/recompute`) strictly checks requested step identifiers against a hardcoded `VALID_STEPS` dictionary (`priority`, `capacity`, `infrastructure`, `decision_summary`). Arbitrary system command execution is barred.
- **Timeout Protection:** Subprocess executions are wrapped with a strict 300-second (`timeout=300`) execution ceiling to prevent denial-of-service (DoS) or resource-exhaustion deadlocks.
- **Audit Logging & Operator Traceability:** Every recompute request is assigned an immutable 8-character UUID job identifier (`job_id`), timestamps, execution logs, and requires an optional `operator_note` recording why the recalculation was triggered.

### 4. Data Privacy & PII Handling
- **Zero Personally Identifiable Information (PII):** The system processes demographic data aggregated strictly at the revenue village level (Census 2011 Primary Census Abstract). **No individual citizen names, Aadhaar numbers, phone numbers, or private household financial records are ingested, stored, or exposed.**
- **Open Data Provenance:** All spatial layers (Copernicus DEM, Census 2011, OpenStreetMap, ESA WorldCover, SHRUG) are derived from publicly accessible, open-license sources (ODbL, CC BY 4.0, Open Government Data License).

### 5. Administrative Safety & Disclaimer Governance
- **Embedded Legal Disclaimers:** Every API endpoint response, GeoJSON feature collection, CSV export, and frontend view carries mandatory disclaimer headers stating that outputs are **Decision Support Indicators Only** and do not constitute official statutory eviction orders or safety certifications.

---

## Threat Model & Risk Analysis

| Threat Vector | Potential Impact | Implemented Mitigation |
| :--- | :--- | :--- |
| **Unauthorized Pipeline Triggering** | Resource exhaustion or overwriting cached GeoPackage profiles. | Subprocess timeout limit (300s), step whitelisting, and job UUID tracking. (Future: JWT admin authentication). |
| **Malformed Spatial Query Injections** | Backend crash via invalid Bounding Box coordinates or infinite limits. | Pydantic type casting and bounding box coordinate validation in `candidate_areas.py`. |
| **Data Tampering / Cache Corruption** | Altering hazard scores to misrepresent village safety. | Immutable raw inputs in `data/raw/`; deterministic recalculation scripts reproduce exact hash outputs. |
| **Misinterpretation as Official Orders** | Public panic or unauthorized administrative eviction actions. | Mandatory persistent disclaimers on every UI screen, tooltip, API JSON response, and exported CSV header. |

---

## Planned / Future Security & Access Control Enhancements

1. **Role-Based Access Control (RBAC) & Authentication:**
   - Implementation of OAuth2 / OpenID Connect (OIDC) with JSON Web Tokens (JWT).
   - **User Roles:**
     - `SDMA_ADMIN`: Full access to trigger pipeline recomputations, adjust YAML thresholds, and export district reports.
     - `DDMA_PLANNER`: Read-only access to village dossiers, map layers, and block action queues.
     - `FIELD_SURVEYOR`: Mobile field data entry for uploading geotechnical ground-truth verification logs.
     - `PUBLIC_VIEWER`: Restricted read-only view displaying public risk awareness layers without administrative dossiers.
2. **End-to-End Encryption:**
   - Enforce HTTPS / TLS 1.3 encryption for all data in transit across cloud deployments.
   - Encrypt data at rest for sensitive future cadastral ownership layers.
3. **API Rate Limiting & Throttling:**
   - Integrate Redis / SlowAPI middleware to enforce token bucket rate limiting on public-facing endpoints.
4. **Compliance Alignment:**
   - Alignment with Government of India National Data Sharing and Accessibility Policy (NDSAP) and CERT-In cybersecurity guidelines for government-hosted decision-support systems.
