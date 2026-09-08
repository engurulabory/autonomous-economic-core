from __future__ import annotations

import sqlite3
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCHEMA = ROOT / "deploy/cloudflare/schema.sql"
BASE_RUNTIME = ROOT / "deploy/cloudflare/worker.js"
EDGE_RUNTIME = ROOT / "deploy/cloudflare/edge-runtime.js"
COMMISSIONING_RUNTIME = ROOT / "deploy/cloudflare/runtime-v1_1.js"
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
    base_runtime = BASE_RUNTIME.read_text(encoding="utf-8")
    edge_runtime = EDGE_RUNTIME.read_text(encoding="utf-8")
    commissioning_runtime = COMMISSIONING_RUNTIME.read_text(encoding="utf-8")
    wrangler = WRANGLER.read_text(encoding="utf-8")

    db = sqlite3.connect(":memory:")
    db.executescript(schema)
    tables = {row[0] for row in db.execute("SELECT name FROM sqlite_master WHERE type='table'")}
    missing_tables = sorted(REQUIRED_TABLES - tables)
    if missing_tables:
        raise SystemExit(f"missing durable tables: {missing_tables}")

    missing_endpoints = sorted(path for path in REQUIRED_ENDPOINTS if path not in base_runtime)
    if missing_endpoints:
        raise SystemExit(f"missing base runtime endpoints: {missing_endpoints}")

    if 'import baseWorker from "./worker.js"' not in edge_runtime:
        raise SystemExit("edge runtime is not layered over durable base runtime")
    if 'export { default } from "./edge-runtime.js"' in base_runtime:
        raise SystemExit("circular runtime delegation detected")

    if "/commissioning/proof" not in commissioning_runtime:
        raise SystemExit("commissioning proof endpoint missing")
    if 'import edgeRuntime from "./edge-runtime.js"' not in commissioning_runtime:
        raise SystemExit("commissioning runtime is not layered over canonical edge runtime")

    if "AEC_STATE_TOKEN" not in base_runtime or "Bearer ${env.AEC_STATE_TOKEN}" not in base_runtime:
        raise SystemExit("authenticated gateway contract missing")
    if 'main = "runtime-v1_1.js"' not in wrangler:
        raise SystemExit("canonical v1.1 runtime entrypoint missing from Wrangler example")
    if "database_id = \"REPLACE_WITH_D1_DATABASE_ID\"" not in wrangler:
        raise SystemExit("D1 database placeholder missing")
    for source in (base_runtime, edge_runtime, commissioning_runtime):
        if "AEC_STATE_TOKEN =" in source or "CLOUDFLARE_API_TOKEN =" in source:
            raise SystemExit("credential literal detected")

    print(
        "Cloudflare durable bundle PASS: "
        f"tables={len(REQUIRED_TABLES)} endpoints={len(REQUIRED_ENDPOINTS)} layering=PASS commissioning=PASS"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
