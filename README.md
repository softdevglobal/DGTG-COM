# DGTG Proactive Compliance Operating System

This repository upgrades the NDIS Compliance Management System into a proactive compliance operating system with:

- Real-time heartbeat monitoring and safeguarding alerts
- RBAC + scope + sensitivity enforcement
- Dynamic training eligibility enforcement
- Outcome tracking and evidence storage
- Digital privacy guard with masked-field reveal workflow
- Compliance pulse dashboard and smart incident classification
- AI oversight controls with full auditable logs

## Quick start

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install fastapi uvicorn pydantic
uvicorn backend.app.main:app --reload
```

Open `frontend/index.html` in a browser for the operator dashboard shell.

## Core formula

`Access Allowed = Role Permission + Scope Match + Sensitivity Clearance + Active Status`

If any check fails:
- deny access
- log denied attempt for sensitive resources

