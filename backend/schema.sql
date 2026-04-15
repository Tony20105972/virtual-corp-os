-- Virtual Corp OS — canonical database schema
-- The schema below is the single source of truth for backend/frontend alignment.

DROP TABLE IF EXISTS project_deployments CASCADE;
DROP TABLE IF EXISTS project_payments CASCADE;
DROP TABLE IF EXISTS project_events CASCADE;
DROP TABLE IF EXISTS project_strategy_runs CASCADE;
DROP TABLE IF EXISTS project_interviews CASCADE;
DROP TABLE IF EXISTS projects CASCADE;

DROP TYPE IF EXISTS project_status CASCADE;
DROP TYPE IF EXISTS ceo_approval_status CASCADE;
DROP TYPE IF EXISTS payment_status CASCADE;

CREATE TYPE project_status AS ENUM (
  'intake_pending', 'interviewing', 'strategy_processing', 'awaiting_ceo_approval',
  'strategy_error', 'build_pending', 'building', 'build_error',
  'deploy_pending', 'deploying', 'deploy_error', 'live', 'archived'
);

CREATE TYPE ceo_approval_status AS ENUM ('pending', 'approved', 'rejected');
CREATE TYPE payment_status AS ENUM ('pending', 'completed', 'failed', 'refunded');

CREATE TABLE projects (
  project_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,

  raw_idea TEXT NOT NULL,
  normalized_idea TEXT,
  business_type TEXT,
  category_tags TEXT[],

  status project_status DEFAULT 'intake_pending' NOT NULL,
  ceo_approval ceo_approval_status DEFAULT 'pending' NOT NULL,
  current_node TEXT,

  strategy_summary TEXT,
  strategy_report_json JSONB,
  prd_json JSONB,
  strategy_report_ready BOOLEAN DEFAULT false NOT NULL,

  revision_count INTEGER DEFAULT 0 NOT NULL CHECK (revision_count >= 0),
  last_revised_items TEXT[],

  payment_done BOOLEAN DEFAULT false NOT NULL,
  deploy_url TEXT,

  error_message TEXT,

  created_at TIMESTAMPTZ DEFAULT now() NOT NULL,
  updated_at TIMESTAMPTZ DEFAULT now() NOT NULL
);

CREATE TABLE project_interviews (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  project_id UUID NOT NULL REFERENCES projects(project_id) ON DELETE CASCADE,
  business_type TEXT,
  category_tags TEXT[],
  question_set_json JSONB NOT NULL,
  answers_json JSONB NOT NULL,
  created_at TIMESTAMPTZ DEFAULT now() NOT NULL
);

CREATE TABLE project_strategy_runs (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  project_id UUID NOT NULL REFERENCES projects(project_id) ON DELETE CASCADE,
  run_index INTEGER NOT NULL,

  model_name TEXT NOT NULL,
  prompt_version TEXT NOT NULL,

  input_snapshot_json JSONB,
  raw_llm_output TEXT,
  parsed_output_json JSONB,

  repair_attempted BOOLEAN DEFAULT false NOT NULL,
  repair_raw_output TEXT,

  success BOOLEAN DEFAULT false NOT NULL,
  error_message TEXT,

  created_at TIMESTAMPTZ DEFAULT now() NOT NULL
);

CREATE TABLE project_events (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  project_id UUID NOT NULL REFERENCES projects(project_id) ON DELETE CASCADE,

  agent_name TEXT NOT NULL,
  event_type TEXT NOT NULL,
  message TEXT NOT NULL,
  payload_json JSONB DEFAULT '{}'::jsonb,

  created_at TIMESTAMPTZ DEFAULT now() NOT NULL
);

CREATE TABLE project_payments (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  project_id UUID NOT NULL REFERENCES projects(project_id) ON DELETE CASCADE,
  provider TEXT,
  session_id TEXT,
  amount NUMERIC(15, 2),
  currency TEXT DEFAULT 'USD' NOT NULL,
  status payment_status DEFAULT 'pending' NOT NULL,
  payload_json JSONB,
  created_at TIMESTAMPTZ DEFAULT now() NOT NULL,
  updated_at TIMESTAMPTZ DEFAULT now() NOT NULL
);

CREATE TABLE project_deployments (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  project_id UUID NOT NULL REFERENCES projects(project_id) ON DELETE CASCADE,
  provider TEXT,
  deployment_url TEXT,
  status TEXT NOT NULL,
  build_log_json JSONB,
  created_at TIMESTAMPTZ DEFAULT now() NOT NULL
);
