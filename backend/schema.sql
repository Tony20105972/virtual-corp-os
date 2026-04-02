-- Ghost Founder — Supabase SQL 스키마
-- 실행 위치: Supabase 대시보드 → SQL Editor
--
-- ⚠️  checkpoints 테이블은 이 파일에 포함하지 않음.
--     ENV=prod로 서버 최초 기동 시 PostgresSaver.setup()이 자동 생성함.

-- ──────────────────────────────────────────
-- projects 테이블
-- ──────────────────────────────────────────
CREATE TABLE IF NOT EXISTS projects (
    project_id   UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id      UUID,                                   -- nullable, Day 6 Auth 연동
    raw_idea     TEXT NOT NULL,
    current_node TEXT NOT NULL DEFAULT 'intake',
    prd_json     JSONB,
    deploy_url   TEXT,
    payment_done BOOLEAN NOT NULL DEFAULT false,
    created_at   TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at   TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- updated_at 자동 갱신 트리거
CREATE OR REPLACE FUNCTION update_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = now();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER projects_updated_at
    BEFORE UPDATE ON projects
    FOR EACH ROW EXECUTE FUNCTION update_updated_at();

-- ──────────────────────────────────────────
-- sessions 테이블
-- ──────────────────────────────────────────
CREATE TABLE IF NOT EXISTS sessions (
    session_id        UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id        UUID NOT NULL REFERENCES projects(project_id) ON DELETE CASCADE,
    stripe_session_id TEXT,                              -- Day 13 Stripe 연동
    payment_done      BOOLEAN NOT NULL DEFAULT false,
    created_at        TIMESTAMPTZ NOT NULL DEFAULT now()
);
