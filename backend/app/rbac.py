from dataclasses import dataclass
from enum import Enum
from typing import Iterable


class Role(str, Enum):
    SUPER_ADMIN = "SUPER_ADMIN"
    COMPLIANCE_OFFICER = "COMPLIANCE_OFFICER"
    SUPERVISOR = "SUPERVISOR"
    TRAINER = "TRAINER"
    SUPPORT_STAFF = "SUPPORT_STAFF"
    HR_ADMIN = "HR_ADMIN"
    DIRECTOR = "DIRECTOR"
    PARTICIPANT = "PARTICIPANT"


class Scope(str, Enum):
    ORG = "ORG"
    TEAM = "TEAM"
    ASSIGNMENT = "ASSIGNMENT"
    SELF = "SELF"


@dataclass
class UserContext:
    user_id: str
    role: Role
    org_id: str
    team_id: str | None
    participant_id: str | None
    active: bool
    clearance: str = "STANDARD"


@dataclass
class RecordContext:
    org_id: str
    team_id: str | None
    participant_id: str | None
    assigned_user_ids: Iterable[str]
    sensitivity: str
    module: str


ROLE_PERMISSIONS = {
    Role.SUPER_ADMIN: {"*"},
    Role.COMPLIANCE_OFFICER: {
        "incidents:view", "incidents:edit", "incidents:classify", "incidents:close",
        "policies:view", "policies:edit", "policies:review",
        "complaints:view", "complaints:edit",
        "risks:view", "risks:edit",
        "audit:view", "ai_logs:view", "dashboard:view",
    },
    Role.SUPERVISOR: {
        "incidents:view", "incidents:edit", "incidents:review",
        "complaints:view", "complaints:review",
        "risks:view", "risks:edit",
        "participants:view_masked", "dashboard:view",
    },
    Role.TRAINER: {
        "participants:view_assigned", "training_notes:create", "attendance:update",
        "incidents:create", "complaints:create", "progress:update",
    },
    Role.SUPPORT_STAFF: {
        "tasks:view_assigned", "service_notes:update", "incidents:create", "complaints:create",
    },
    Role.HR_ADMIN: {
        "staff_compliance:view", "staff_compliance:edit", "training:assign",
    },
    Role.DIRECTOR: {
        "dashboard:view_org", "reports:view_org", "policies:approve", "ai_logs:view",
    },
    Role.PARTICIPANT: {
        "self:view_training", "self:view_progress", "complaints:create_self",
    },
}


def has_permission(role: Role, permission: str) -> bool:
    grants = ROLE_PERMISSIONS.get(role, set())
    return "*" in grants or permission in grants


def scope_match(user: UserContext, record: RecordContext) -> bool:
    if user.role in {Role.SUPER_ADMIN, Role.COMPLIANCE_OFFICER, Role.DIRECTOR}:
        return user.org_id == record.org_id
    if user.role == Role.SUPERVISOR:
        return user.org_id == record.org_id and user.team_id and user.team_id == record.team_id
    if user.role in {Role.TRAINER, Role.SUPPORT_STAFF}:
        return user.user_id in set(record.assigned_user_ids)
    if user.role == Role.PARTICIPANT:
        return user.participant_id is not None and user.participant_id == record.participant_id
    if user.role == Role.HR_ADMIN:
        return record.module == "staff_compliance" and user.org_id == record.org_id
    return False


def sensitivity_clearance(user: UserContext, sensitivity: str) -> bool:
    if sensitivity in {"PUBLIC_INTERNAL", "CONTROLLED"}:
        return True
    if sensitivity == "SENSITIVE":
        return user.role not in {Role.PARTICIPANT}
    if sensitivity == "HIGHLY_SENSITIVE":
        return user.role in {
            Role.SUPER_ADMIN,
            Role.COMPLIANCE_OFFICER,
            Role.SUPERVISOR,
            Role.DIRECTOR,
        }
    return False


def access_allowed(user: UserContext, record: RecordContext, permission: str) -> bool:
    return all([
        user.active,
        has_permission(user.role, permission),
        scope_match(user, record),
        sensitivity_clearance(user, record.sensitivity),
    ])
