# DGTG Proactive Compliance Operating System — Architecture

## 1) Platform shape

- **Backend API:** FastAPI service for compliance rules, heartbeat analysis, incident orchestration, privacy controls, and dashboard scoring.
- **Rule Engine:** Deterministic policy rules for incident classification, training eligibility, and compliance pulse degradation.
- **Data Layer:** PostgreSQL schema in `db/schema.sql` with immutable audit/event records and archive-only lifecycle.
- **UI Layer:** Operator dashboard shell in `frontend/index.html` with module cards and real-time scoring view.
- **AI Layer (bounded):** Suggestion-only pipeline with mandatory intervention logs and human reviewer accountability.

## 2) Mapping to required modules

1. **Continuous Monitoring Engine (Heartbeat)**
   - Endpoint `/heartbeat/analyse` ingests participant interactions.
   - Distress detection blends keyword+history+attendance signals.
   - Trigger creates draft incident and silent supervisor alert.
   - AI intervention log stored for audit evidence.

2. **Dynamic Training Matrix**
   - Endpoint `/training/eligibility` blocks assignment when mandatory modules are incomplete.
   - Schema includes expiry-capable training records and certificate refs.

3. **Outcome Tracker**
   - `goals` + `progress_events` tables support measurable before/after evidence.
   - Evidence refs support call recordings, assessments, feedback logs.

4. **Digital Privacy Guard**
   - `masked_field_access_requests` + `access_events` tables capture reveal approvals and geologged access attempts.

5. **Compliance Pulse Dashboard**
   - `/dashboard/compliance-pulse` computes Governance / Provision / Environment scores.
   - Includes alert factors that explain score degradation.

6. **Smart Incident Classification**
   - Forced reportable rule when `injury=true` and `incident_type=participant-related`.
   - Manual override disabled in rule response.

7. **AI Oversight Controls**
   - `/incidents/{id}/close` explicitly forbids AI actor closure.
   - `ai_intervention_logs` persists evidence for every AI suggestion.

8. **System-wide Rules**
   - No hard deletion for core records.
   - Full timestamping and auditable event model.

## 3) Access control model

Access is granted only when all four are true:

`Role Permission + Scope Match + Sensitivity Clearance + Active Status`

RBAC and scope rules implemented in `backend/app/rbac.py`:
- Org scope: Super Admin, Compliance Officer, Director
- Team scope: Supervisor
- Assignment scope: Trainer, Support Staff
- Self scope: Participant

## 4) Production-hardening checklist

- Add PostgreSQL + migrations (Alembic)
- Replace in-memory arrays with repositories
- Add message bus (Kafka/SQS) for real-time heartbeat events
- Add WebSocket/SSE notification fan-out
- Add SIEM integration for suspicious access and breach triggers
- Add immutable object storage for evidence assets
- Add SOC2/ISO27001-aligned key management and encryption
