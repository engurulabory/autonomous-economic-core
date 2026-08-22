from __future__ import annotations

import sqlite3
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCHEMA = ROOT / "deploy/cloudflare/schema.sql"
WORKER = ROOT / "deploy/cloudflare/worker.js"
WRANGLER = ROOT / "deploy/cloudflare/wrangler.toml.example"

REQUIRED_TABLES = {
    "jobs", "job_events", "idempotency_keys", "leases", "heartbeats",
    "dead_letters", "artifacts", "audit_chain", "runtime_cycles",
}
REQUIRED_ENDPOINTS = {
    "/health", "/jobs/enqueue", "/jobs/lease", "/jobs/start",
    "/jobs/verifying", "/jobs/finish", "/jobs/human-release",
    "/jobs/counts", "/artifacts/put", "/watchdog/sweep",
    "/audit/verify", "/cycles/record", "/cycles/recent",
}


def main() -> int:
    schema = SCHEMA.read_text(encoding="utf-8")
    worker = WORKER.read_text(encoding="utf-8")
    wrangler = WRANGLER.read_text(encoding="utf-8")

    db = sqlite3.connect(":memory:")
    db.executescript(schema)
    tables = {row[0] for row in db.execute("SELECT name FROM sqlite_master WHERE type='table'")}
    missing_tables = sorted(REQUIRED_TABLES - tables)
    if missing_tables:
        raise SystemExit(f"missing durable tables: {missing_tables}")

    missing_endpoints = sorted(path for path in REQUIRED_ENDPOINTS if path not in worker)
    if missing_endpoints:
        raise SystemExit(f"missing worker endpoints: {missing_endpoints}")

    if "AEC_STATE_TOKEN" not in worker or "Bearer ${env.AEC_STATE_TOKEN}" not in worker:
        raise SystemExit("authenticated gateway contract missing")
    if "database_id = \"REPLACE_WITH_D1_DATABASE_ID\"" not in wrangler:
        raise SystemExit("D1 database placeholder missing")
    if "AEC_STATE_TOKEN =" in worker or "CLOUDFLARE_API_TOKEN =" in worker:
        raise SystemExit("credential literal detected")

    print(f"Cloudflare durable bundle PASS: tables={len(REQUIRED_TABLES)} endpoints={len(REQUIRED_ENDPOINTS)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
