from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone


DISTRESS_KEYWORDS = {
    "unsafe": 0.4,
    "hurt": 0.4,
    "panic": 0.3,
    "can't cope": 0.35,
    "self harm": 0.6,
    "afraid": 0.25,
}


@dataclass
class HeartbeatSignal:
    participant_id: str
    source_type: str
    content: str
    prior_incidents_90d: int = 0
    missed_sessions_30d: int = 0


def detect_distress(signal: HeartbeatSignal) -> tuple[bool, float, str]:
    text = signal.content.lower()
    confidence = 0.0
    reasons: list[str] = []

    for key, weight in DISTRESS_KEYWORDS.items():
        if key in text:
            confidence += weight
            reasons.append(f"keyword:{key}")

    confidence += min(0.25, signal.prior_incidents_90d * 0.05)
    if signal.prior_incidents_90d:
        reasons.append("incident_history")

    confidence += min(0.2, signal.missed_sessions_30d * 0.04)
    if signal.missed_sessions_30d:
        reasons.append("missed_sessions")

    confidence = min(confidence, 0.99)
    return confidence >= 0.45, confidence, ",".join(reasons) or "none"


def severity_from_confidence(confidence: float) -> str:
    if confidence >= 0.8:
        return "HIGH"
    if confidence >= 0.55:
        return "MEDIUM"
    return "LOW"


def classify_incident(incident_type: str, injury: bool) -> dict:
    reportable = injury and incident_type.lower() == "participant-related"
    now = datetime.now(timezone.utc)
    deadline = now + timedelta(hours=24 if reportable else 72)
    return {
        "reportable": reportable,
        "ndis_notification_deadline": deadline.isoformat(),
        "manual_override_allowed": False,
    }


def compliance_pulse(
    policy_last_review_days: int,
    expiring_screenings_30d: int,
    incidents_open_gt_5d: int,
    missing_progress_notes: int,
) -> dict:
    governance = 100.0
    provision = 100.0
    environment = 100.0
    factors: list[str] = []

    if policy_last_review_days > 365:
        governance -= 20
        factors.append("Policy review overdue > 12 months")
    if expiring_screenings_30d > 0:
        governance -= min(20, expiring_screenings_30d * 3)
        factors.append("Staff screening expiring within 30 days")
    if incidents_open_gt_5d > 0:
        provision -= min(25, incidents_open_gt_5d * 4)
        factors.append("Incidents open > 5 days")
    if missing_progress_notes > 0:
        provision -= min(30, missing_progress_notes * 2)
        environment -= min(15, missing_progress_notes)
        factors.append("Missing participant progress notes")

    governance = max(governance, 0)
    provision = max(provision, 0)
    environment = max(environment, 0)
    overall = round((governance + provision + environment) / 3, 2)

    return {
        "governance_score": governance,
        "provision_score": provision,
        "environment_score": environment,
        "overall_score": overall,
        "alerts": factors,
        "gauge": f"{overall:.2f}%",
    }
