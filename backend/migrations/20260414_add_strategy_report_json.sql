ALTER TABLE projects
ADD COLUMN IF NOT EXISTS strategy_report_json JSONB;

COMMENT ON COLUMN projects.strategy_report_json IS 'CEO briefing strategy report JSON for the Strategy stage report UI';
