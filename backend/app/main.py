from datetime import datetime, timedelta, timezone
from typing import Any
from uuid import uuid4

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from .rules import HeartbeatSignal, classify_incident, compliance_pulse, detect_distress, severity_from_confidence

app = FastAPI(title="DGTG Proactive Compliance Operating System", version="1.0.0")

INCIDENTS: list[dict[str, Any]] = []
AI_LOGS: list[dict[str, Any]] = []
MASK_REQUESTS: list[dict[str, Any]] = []
TRAINING_RECORDS: dict[str, dict[str, Any]] = {}


class HeartbeatEvent(BaseModel):
    participant_id: str
    source_type: str = Field(examples=["chat", "forum", "training"])
    content: str
    prior_incidents_90d: int = 0
    missed_sessions_30d: int = 0
    supervisor_id: str


class IncidentCreate(BaseModel):
    participant_id: str
    created_by: str
    incident_type: str
    injury: bool
    details: str


class SensitiveRevealRequest(BaseModel):
    participant_id: str
    user_id: str
    field_name: str
    reason: str


class TrainingEligibilityInput(BaseModel):
    user_id: str
    role: str
    required_modules: list[str]
    completed_modules: list[str]


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "service": "heartbeat"}


@app.post("/heartbeat/analyse")
def analyse_heartbeat(event: HeartbeatEvent) -> dict[str, Any]:
    signal = HeartbeatSignal(
        participant_id=event.participant_id,
        source_type=event.source_type,
        content=event.content,
        prior_incidents_90d=event.prior_incidents_90d,
        missed_sessions_30d=event.missed_sessions_30d,
    )
    triggered, confidence, reason = detect_distress(signal)
    response = {
        "triggered": triggered,
        "confidence": confidence,
        "reason": reason,
    }

    if triggered:
        severity = severity_from_confidence(confidence)
        incident = {
            "id": str(uuid4()),
            "participant_id": event.participant_id,
            "created_by": "AI_HEARTBEAT",
            "status": "REPORTED",
            "severity": severity,
            "incident_type": "participant-related",
            "injury": False,
            "details": f"Auto-draft from heartbeat ({event.source_type})",
            "created_at": datetime.now(timezone.utc).isoformat(),
            "assigned_to": event.supervisor_id,
        }
        INCIDENTS.append(incident)

        ai_log = {
            "id": str(uuid4()),
            "participant_id": event.participant_id,
            "trigger_reason": reason,
            "confidence_score": confidence,
            "action_taken": "Draft incident created; supervisor notified",
            "source_data": event.source_type,
            "human_reviewer": event.supervisor_id,
            "created_at": datetime.now(timezone.utc).isoformat(),
        }
        AI_LOGS.append(ai_log)

        response["draft_incident"] = incident
        response["silent_alert"] = {"to_supervisor": event.supervisor_id, "severity": severity}

    return response


@app.post("/incidents")
def create_incident(payload: IncidentCreate) -> dict[str, Any]:
    classification = classify_incident(payload.incident_type, payload.injury)
    incident = {
        "id": str(uuid4()),
        "participant_id": payload.participant_id,
        "created_by": payload.created_by,
        "incident_type": payload.incident_type,
        "injury": payload.injury,
        "details": payload.details,
        "status": "REPORTED",
        "severity": "MEDIUM",
        **classification,
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    INCIDENTS.append(incident)
    return incident


@app.get("/dashboard/compliance-pulse")
def dashboard_pulse(
    policy_last_review_days: int = 0,
    expiring_screenings_30d: int = 0,
    incidents_open_gt_5d: int = 0,
    missing_progress_notes: int = 0,
) -> dict[str, Any]:
    return compliance_pulse(
        policy_last_review_days,
        expiring_screenings_30d,
        incidents_open_gt_5d,
        missing_progress_notes,
    )


@app.post("/privacy/reveal-request")
def request_reveal(payload: SensitiveRevealRequest) -> dict[str, Any]:
    request = {
        "id": str(uuid4()),
        "participant_id": payload.participant_id,
        "user_id": payload.user_id,
        "field_name": payload.field_name,
        "reason": payload.reason,
        "status": "PENDING",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "expires_at": (datetime.now(timezone.utc) + timedelta(hours=4)).isoformat(),
    }
    MASK_REQUESTS.append(request)
    return request


@app.post("/training/eligibility")
def training_eligibility(payload: TrainingEligibilityInput) -> dict[str, Any]:
    missing = sorted(set(payload.required_modules) - set(payload.completed_modules))
    allowed = len(missing) == 0
    result = {
        "user_id": payload.user_id,
        "role": payload.role,
        "eligible_for_assignment": allowed,
        "missing_modules": missing,
        "enforcement": "BLOCK_SCHEDULING" if not allowed else "ALLOW",
    }
    TRAINING_RECORDS[payload.user_id] = result
    return result


@app.get("/ai/activity-log")
def ai_activity_log() -> dict[str, Any]:
    return {"count": len(AI_LOGS), "items": AI_LOGS[-100:]}


@app.get("/incidents")
def list_incidents() -> dict[str, Any]:
    return {"count": len(INCIDENTS), "items": INCIDENTS[-100:]}


@app.post("/incidents/{incident_id}/close")
def close_incident(incident_id: str, actor_type: str) -> dict[str, Any]:
    if actor_type == "AI":
        raise HTTPException(status_code=403, detail="AI cannot close incidents")
    for item in INCIDENTS:
        if item["id"] == incident_id:
            item["status"] = "CLOSED"
            item["closed_at"] = datetime.now(timezone.utc).isoformat()
            return item
    raise HTTPException(status_code=404, detail="Incident not found")
