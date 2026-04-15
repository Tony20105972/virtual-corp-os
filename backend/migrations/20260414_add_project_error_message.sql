ALTER TABLE projects
ADD COLUMN IF NOT EXISTS error_message TEXT;

COMMENT ON COLUMN projects.error_message IS 'Latest pipeline error message shown to the frontend';
