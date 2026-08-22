PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS jobs (
  job_id TEXT PRIMARY KEY,
  capability TEXT NOT NULL,
  payload_json TEXT NOT NULL,
  state TEXT NOT NULL CHECK(state IN ('QUEUED','ASSIGNED','RUNNING','VERIFYING','RETRY_WAIT','HOLD','COMPLETED','BLOCKED')),
  attempts INTEGER NOT NULL DEFAULT 0 CHECK(attempts >= 0),
  max_attempts INTEGER NOT NULL CHECK(max_attempts BETWEEN 1 AND 20),
  assigned_worker TEXT,
  human_threshold_required INTEGER NOT NULL DEFAULT 0 CHECK(human_threshold_required IN (0,1)),
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS jobs_state_capability_idx ON jobs(state, capability, created_at);
CREATE INDEX IF NOT EXISTS jobs_updated_at_idx ON jobs(updated_at);

CREATE TABLE IF NOT EXISTS job_events (
  event_id INTEGER PRIMARY KEY AUTOINCREMENT,
  job_id TEXT NOT NULL,
  at TEXT NOT NULL,
  actor TEXT NOT NULL,
  event TEXT NOT NULL,
  detail_json TEXT NOT NULL,
  FOREIGN KEY(job_id) REFERENCES jobs(job_id)
);
CREATE INDEX IF NOT EXISTS job_events_job_idx ON job_events(job_id, event_id);

CREATE TABLE IF NOT EXISTS idempotency_keys (
  key TEXT PRIMARY KEY,
  job_id TEXT NOT NULL,
  created_at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idempotency_job_idx ON idempotency_keys(job_id);

CREATE TABLE IF NOT EXISTS leases (
  resource_id TEXT PRIMARY KEY,
  owner_id TEXT NOT NULL,
  lease_token TEXT NOT NULL,
  expires_at TEXT NOT NULL,
  updated_at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS leases_expires_idx ON leases(expires_at);

CREATE TABLE IF NOT EXISTS heartbeats (
  worker_id TEXT PRIMARY KEY,
  at TEXT NOT NULL,
  detail_json TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS heartbeats_at_idx ON heartbeats(at);

CREATE TABLE IF NOT EXISTS dead_letters (
  dead_id TEXT PRIMARY KEY,
  job_id TEXT NOT NULL,
  reason TEXT NOT NULL,
  payload_json TEXT NOT NULL,
  created_at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS dead_letters_job_idx ON dead_letters(job_id, created_at);

CREATE TABLE IF NOT EXISTS artifacts (
  artifact_id TEXT PRIMARY KEY,
  job_id TEXT NOT NULL,
  media_type TEXT NOT NULL,
  content_base64 TEXT NOT NULL,
  sha256 TEXT NOT NULL,
  bytes INTEGER NOT NULL CHECK(bytes BETWEEN 0 AND 524288),
  created_at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS artifacts_job_idx ON artifacts(job_id, created_at);

CREATE TABLE IF NOT EXISTS audit_chain (
  seq INTEGER PRIMARY KEY AUTOINCREMENT,
  at TEXT NOT NULL,
  actor TEXT NOT NULL,
  event TEXT NOT NULL,
  payload_json TEXT NOT NULL,
  prev_hash TEXT NOT NULL,
  event_hash TEXT NOT NULL UNIQUE
);
CREATE UNIQUE INDEX IF NOT EXISTS audit_chain_prev_hash_unique ON audit_chain(prev_hash);

CREATE TABLE IF NOT EXISTS runtime_cycles (
  cycle_id TEXT PRIMARY KEY,
  started_at TEXT NOT NULL,
  finished_at TEXT NOT NULL,
  source_sha TEXT,
  status TEXT NOT NULL CHECK(status IN ('PASS','HOLD','BLOCKED')),
  detail_json TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS runtime_cycles_finished_idx ON runtime_cycles(finished_at DESC);
