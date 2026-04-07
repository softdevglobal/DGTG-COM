-- DGTG Proactive Compliance Operating System schema

CREATE TYPE role_type AS ENUM (
  'SUPER_ADMIN',
  'COMPLIANCE_OFFICER',
  'SUPERVISOR',
  'TRAINER',
  'SUPPORT_STAFF',
  'HR_ADMIN',
  'DIRECTOR',
  'PARTICIPANT'
);

CREATE TYPE data_scope_type AS ENUM ('ORG', 'TEAM', 'ASSIGNMENT', 'SELF');
CREATE TYPE sensitivity_level_type AS ENUM ('PUBLIC_INTERNAL', 'CONTROLLED', 'SENSITIVE', 'HIGHLY_SENSITIVE');
CREATE TYPE incident_severity_type AS ENUM ('LOW', 'MEDIUM', 'HIGH');
CREATE TYPE incident_status_type AS ENUM ('REPORTED', 'REVIEW', 'INVESTIGATING', 'ACTIONED', 'CLOSED');
CREATE TYPE policy_status_type AS ENUM ('DRAFT', 'REVIEW', 'APPROVED', 'PUBLISHED', 'ARCHIVED');

CREATE TABLE organisations (
  id UUID PRIMARY KEY,
  name TEXT NOT NULL,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE users (
  id UUID PRIMARY KEY,
  organisation_id UUID NOT NULL REFERENCES organisations(id),
  team_id UUID,
  participant_id UUID,
  role role_type NOT NULL,
  active_status BOOLEAN NOT NULL DEFAULT TRUE,
  mfa_enabled BOOLEAN NOT NULL DEFAULT FALSE,
  clearance_status TEXT NOT NULL DEFAULT 'STANDARD',
  last_login TIMESTAMPTZ,
  permitted_modules JSONB NOT NULL DEFAULT '[]'::jsonb,
  data_scope data_scope_type NOT NULL,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE participants (
  id UUID PRIMARY KEY,
  organisation_id UUID NOT NULL REFERENCES organisations(id),
  team_id UUID,
  display_name TEXT NOT NULL,
  full_name TEXT NOT NULL,
  date_of_birth DATE,
  mobile TEXT,
  address TEXT,
  sensitivity_level sensitivity_level_type NOT NULL DEFAULT 'HIGHLY_SENSITIVE',
  risk_score NUMERIC(5,2) NOT NULL DEFAULT 0,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE participant_assignments (
  id UUID PRIMARY KEY,
  organisation_id UUID NOT NULL REFERENCES organisations(id),
  participant_id UUID NOT NULL REFERENCES participants(id),
  user_id UUID NOT NULL REFERENCES users(id),
  active BOOLEAN NOT NULL DEFAULT TRUE,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE incidents (
  id UUID PRIMARY KEY,
  organisation_id UUID NOT NULL REFERENCES organisations(id),
  team_id UUID,
  participant_id UUID REFERENCES participants(id),
  created_by UUID NOT NULL REFERENCES users(id),
  assigned_to UUID REFERENCES users(id),
  incident_type TEXT NOT NULL,
  injury BOOLEAN NOT NULL DEFAULT FALSE,
  reportable BOOLEAN NOT NULL DEFAULT FALSE,
  severity incident_severity_type NOT NULL,
  status incident_status_type NOT NULL DEFAULT 'REPORTED',
  access_classification sensitivity_level_type NOT NULL DEFAULT 'SENSITIVE',
  ndis_notification_deadline TIMESTAMPTZ,
  details TEXT,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  archived_at TIMESTAMPTZ
);

CREATE TABLE ai_intervention_logs (
  id UUID PRIMARY KEY,
  organisation_id UUID NOT NULL REFERENCES organisations(id),
  participant_id UUID REFERENCES participants(id),
  source_type TEXT NOT NULL,
  source_record_id TEXT,
  trigger_reason TEXT NOT NULL,
  confidence_score NUMERIC(5,4) NOT NULL,
  suggested_action TEXT NOT NULL,
  action_taken TEXT,
  human_reviewer UUID REFERENCES users(id),
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE policy_versions (
  id UUID PRIMARY KEY,
  organisation_id UUID NOT NULL REFERENCES organisations(id),
  policy_name TEXT NOT NULL,
  version_number INTEGER NOT NULL,
  status policy_status_type NOT NULL DEFAULT 'DRAFT',
  content_ref TEXT NOT NULL,
  created_by UUID NOT NULL REFERENCES users(id),
  reviewed_by UUID REFERENCES users(id),
  approved_by UUID REFERENCES users(id),
  reviewed_at TIMESTAMPTZ,
  approved_at TIMESTAMPTZ,
  published_at TIMESTAMPTZ,
  archived_at TIMESTAMPTZ,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  UNIQUE (organisation_id, policy_name, version_number)
);

CREATE TABLE training_modules (
  id UUID PRIMARY KEY,
  code TEXT UNIQUE NOT NULL,
  title TEXT NOT NULL,
  mandatory_for_roles role_type[] NOT NULL,
  recertify_days INTEGER,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE staff_training_records (
  id UUID PRIMARY KEY,
  organisation_id UUID NOT NULL REFERENCES organisations(id),
  user_id UUID NOT NULL REFERENCES users(id),
  module_id UUID NOT NULL REFERENCES training_modules(id),
  completion_date DATE,
  score NUMERIC(5,2),
  certificate_ref TEXT,
  expiry_date DATE,
  status TEXT NOT NULL DEFAULT 'PENDING',
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  UNIQUE(user_id, module_id)
);

CREATE TABLE goals (
  id UUID PRIMARY KEY,
  participant_id UUID NOT NULL REFERENCES participants(id),
  title TEXT NOT NULL,
  baseline JSONB,
  target JSONB,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE progress_events (
  id UUID PRIMARY KEY,
  participant_id UUID NOT NULL REFERENCES participants(id),
  goal_id UUID REFERENCES goals(id),
  metric_key TEXT NOT NULL,
  metric_value NUMERIC(8,2),
  note TEXT,
  evidence_ref TEXT,
  created_by UUID REFERENCES users(id),
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE access_events (
  id UUID PRIMARY KEY,
  user_id UUID NOT NULL REFERENCES users(id),
  module TEXT NOT NULL,
  action TEXT NOT NULL,
  record_type TEXT,
  record_id TEXT,
  sensitivity_level sensitivity_level_type,
  success BOOLEAN NOT NULL,
  reason TEXT,
  ip_address INET,
  device_fingerprint TEXT,
  geo_country TEXT,
  geo_city TEXT,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE masked_field_access_requests (
  id UUID PRIMARY KEY,
  user_id UUID NOT NULL REFERENCES users(id),
  participant_id UUID NOT NULL REFERENCES participants(id),
  field_name TEXT NOT NULL,
  reason TEXT NOT NULL,
  status TEXT NOT NULL DEFAULT 'PENDING',
  approved_by UUID REFERENCES users(id),
  expires_at TIMESTAMPTZ,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE compliance_pulse_snapshots (
  id UUID PRIMARY KEY,
  organisation_id UUID NOT NULL REFERENCES organisations(id),
  governance_score NUMERIC(5,2) NOT NULL,
  provision_score NUMERIC(5,2) NOT NULL,
  environment_score NUMERIC(5,2) NOT NULL,
  overall_score NUMERIC(5,2) NOT NULL,
  contributing_factors JSONB NOT NULL,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Integrity rule: no hard deletion on core records
-- Enforce with application-level archive endpoints + database permission revocation in production.
