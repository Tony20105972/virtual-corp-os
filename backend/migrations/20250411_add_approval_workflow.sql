-- Day 11 approval workflow migration
ALTER TABLE projects
ADD COLUMN IF NOT EXISTS status TEXT DEFAULT 'intake_pending',
ADD COLUMN IF NOT EXISTS business_type TEXT,
ADD COLUMN IF NOT EXISTS category_tags TEXT[] DEFAULT ARRAY[]::TEXT[],
ADD COLUMN IF NOT EXISTS strategy_summary JSONB,
ADD COLUMN IF NOT EXISTS strategy_report_ready BOOLEAN DEFAULT FALSE,
ADD COLUMN IF NOT EXISTS ceo_approval TEXT DEFAULT 'pending',
ADD COLUMN IF NOT EXISTS approval_requested_at TIMESTAMPTZ,
ADD COLUMN IF NOT EXISTS approval_decided_at TIMESTAMPTZ,
ADD COLUMN IF NOT EXISTS revision_count INTEGER DEFAULT 0,
ADD COLUMN IF NOT EXISTS revision_history JSONB DEFAULT '[]'::jsonb,
ADD COLUMN IF NOT EXISTS last_revised_items TEXT[] DEFAULT ARRAY[]::TEXT[];

UPDATE projects
SET status = CASE
  WHEN current_node = 'intake' THEN 'interviewing'
  WHEN current_node = 'strategy' THEN 'strategy_running'
  WHEN current_node = 'build' THEN 'building'
  WHEN current_node = 'deploy' THEN 'deploying'
  WHEN current_node = 'complete' THEN 'complete'
  ELSE COALESCE(status, 'intake_pending')
END
WHERE status IS NULL
   OR status = 'intake_pending';

CREATE INDEX IF NOT EXISTS idx_projects_awaiting_ceo_approval
ON projects(status)
WHERE status = 'awaiting_ceo_approval';

CREATE INDEX IF NOT EXISTS idx_projects_revision_count
ON projects(revision_count)
WHERE revision_count >= 2;

DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1
    FROM pg_constraint
    WHERE conname = 'check_revision_count'
  ) THEN
    ALTER TABLE projects
    ADD CONSTRAINT check_revision_count
    CHECK (revision_count >= 0 AND revision_count <= 3);
  END IF;
END $$;

COMMENT ON COLUMN projects.ceo_approval IS 'CEO 승인 상태: pending=대기, approved=승인, revise=수정요청';
COMMENT ON COLUMN projects.revision_count IS '수정 요청 횟수 (최대 3회)';
COMMENT ON COLUMN projects.revision_history IS '수정 요청 이력 (JSONB 배열)';
COMMENT ON COLUMN projects.last_revised_items IS '마지막 수정된 PRD 항목 키 (하이라이트용)';
