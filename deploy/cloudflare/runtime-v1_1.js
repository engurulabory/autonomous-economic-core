import edgeRuntime from "./edge-runtime.js";

const VERSION = "1.1-commissioning.1";
const PERSISTENCE_CYCLE_ID = "commissioning-persistence-v1.1";
const RECOVERY_JOB_ID = "job_commissioning_recovery_v1_1";
const RECOVERY_WORKER_ID = "commissioning-crash-simulator";

export default {
  async fetch(request, env, ctx) {
    const url = new URL(request.url);
    if (url.pathname === "/commissioning/proof" && request.method === "GET") {
      try {
        return json(await commissioningProof(env));
      } catch (error) {
        return json({ ok: false, state: "BLOCKED", error: String(error), version: VERSION }, 500);
      }
    }
    return edgeRuntime.fetch(request, env, ctx);
  },

  async scheduled(controller, env, ctx) {
    edgeRuntime.scheduled(controller, env, ctx);
    ctx.waitUntil(runCommissioningProofCycle(env, controller));
  }
};

async function runCommissioningProofCycle(env, controller) {
  await recordPersistenceObservation(env, controller);
  await seedOrObserveRecoveryCanary(env);
}

async function recordPersistenceObservation(env, controller) {
  const at = now();
  const prior = await env.DB.prepare(
    "SELECT detail_json, started_at FROM runtime_cycles WHERE cycle_id=?"
  ).bind(PERSISTENCE_CYCLE_ID).first();

  const previous = parseJson(prior?.detail_json, {});
  const invocations = Number(previous.invocations || 0) + 1;
  const detail = {
    kind: "cross-invocation-persistence-proof",
    invocations,
    first_seen_at: previous.first_seen_at || prior?.started_at || at,
    last_seen_at: at,
    last_scheduled_time: new Date(controller.scheduledTime).toISOString(),
    last_cron: String(controller.cron || ""),
    runtime: VERSION
  };

  await env.DB.prepare(
    `INSERT INTO runtime_cycles(cycle_id,started_at,finished_at,source_sha,status,detail_json)
     VALUES(?,?,?,?,?,?)
     ON CONFLICT(cycle_id) DO UPDATE SET
       finished_at=excluded.finished_at,
       status=excluded.status,
       detail_json=excluded.detail_json`
  ).bind(
    PERSISTENCE_CYCLE_ID,
    detail.first_seen_at,
    at,
    null,
    invocations >= 2 ? "PASS" : "HOLD",
    stableStringify(detail)
  ).run();
}

async function seedOrObserveRecoveryCanary(env) {
  const existing = await env.DB.prepare(
    "SELECT state, attempts, max_attempts FROM jobs WHERE job_id=?"
  ).bind(RECOVERY_JOB_ID).first();

  if (existing) return;

  const at = now();
  const expiredAt = "2000-01-01T00:00:00.000Z";
  const payload = {
    purpose: "controlled non-economic watchdog recovery proof",
    qualification_evidence_id: "internal-controlled-v1.1-recovery-proof",
    economic: false
  };

  await env.DB.prepare(
    `INSERT INTO jobs(job_id,capability,payload_json,state,attempts,max_attempts,assigned_worker,
                      human_threshold_required,created_at,updated_at)
     VALUES(?,?,?,'RUNNING',1,3,?,0,?,?)`
  ).bind(
    RECOVERY_JOB_ID,
    "commissioning_recovery_probe",
    stableStringify(payload),
    RECOVERY_WORKER_ID,
    at,
    at
  ).run();

  await env.DB.prepare(
    `INSERT OR REPLACE INTO leases(resource_id,owner_id,lease_token,expires_at,updated_at)
     VALUES(?,?,?,?,?)`
  ).bind(
    `job:${RECOVERY_JOB_ID}`,
    RECOVERY_WORKER_ID,
    "controlled-expired-lease",
    expiredAt,
    at
  ).run();

  await env.DB.prepare(
    "INSERT INTO job_events(job_id,at,actor,event,detail_json) VALUES(?,?,?,?,?)"
  ).bind(
    RECOVERY_JOB_ID,
    at,
    RECOVERY_WORKER_ID,
    "CONTROLLED_CRASH_SIMULATED",
    stableStringify({ expired_lease: true, economic: false })
  ).run();
}

async function commissioningProof(env) {
  const persistence = await env.DB.prepare(
    "SELECT status, started_at, finished_at, detail_json FROM runtime_cycles WHERE cycle_id=?"
  ).bind(PERSISTENCE_CYCLE_ID).first();

  const recovery = await env.DB.prepare(
    "SELECT state, attempts, max_attempts, assigned_worker, updated_at FROM jobs WHERE job_id=?"
  ).bind(RECOVERY_JOB_ID).first();

  const bootstrap = await env.DB.prepare(
    "SELECT status, started_at, finished_at, detail_json FROM runtime_cycles WHERE cycle_id='edge-bootstrap-v1.1'"
  ).first();

  const hourly = await env.DB.prepare(
    `SELECT cycle_id,status,started_at,finished_at,detail_json
     FROM runtime_cycles
     WHERE cycle_id LIKE 'edge-hourly-%'
     ORDER BY finished_at DESC
     LIMIT 24`
  ).all();

  const hourlyRows = hourly.results || [];
  const hourlyPass = hourlyRows.filter(row => String(row.status) === "PASS").length;
  const persistenceDetail = parseJson(persistence?.detail_json, {});
  const persistencePass = String(persistence?.status || "") === "PASS" && Number(persistenceDetail.invocations || 0) >= 2;
  const recoveryPass = String(recovery?.state || "") === "RETRY_WAIT";
  const bootstrapPass = String(bootstrap?.status || "") === "PASS";
  const audit = await verifyAuditChain(env);
  const observationPass = hourlyRows.length >= 24 && hourlyPass === 24;

  const state = bootstrapPass && persistencePass && recoveryPass && audit.ok && observationPass
    ? "PASS"
    : audit.ok === false || String(recovery?.state || "") === "BLOCKED"
      ? "BLOCKED"
      : "HOLD";

  return {
    ok: state !== "BLOCKED",
    state,
    version: VERSION,
    gates: {
      bootstrap: bootstrapPass ? "PASS" : "HOLD",
      persistence: persistencePass ? "PASS" : "HOLD",
      failure_recovery: recoveryPass ? "PASS" : String(recovery?.state || "") === "BLOCKED" ? "BLOCKED" : "HOLD",
      audit_integrity: audit.ok ? "PASS" : "BLOCKED",
      observation_24_hourly_cycles: observationPass ? "PASS" : "HOLD"
    },
    evidence: {
      bootstrap: bootstrap ? {
        status: String(bootstrap.status),
        started_at: String(bootstrap.started_at),
        finished_at: String(bootstrap.finished_at)
      } : null,
      persistence: persistence ? {
        status: String(persistence.status),
        invocations: Number(persistenceDetail.invocations || 0),
        first_seen_at: persistenceDetail.first_seen_at || null,
        last_seen_at: persistenceDetail.last_seen_at || null
      } : null,
      failure_recovery: recovery ? {
        job_id: RECOVERY_JOB_ID,
        state: String(recovery.state),
        attempts: Number(recovery.attempts),
        max_attempts: Number(recovery.max_attempts),
        assigned_worker: recovery.assigned_worker ? String(recovery.assigned_worker) : null,
        updated_at: String(recovery.updated_at)
      } : null,
      audit,
      hourly_cycles_seen: hourlyRows.length,
      hourly_cycles_pass: hourlyPass,
      recent_hourly_cycles: hourlyRows.map(row => ({
        cycle_id: String(row.cycle_id),
        status: String(row.status),
        started_at: String(row.started_at),
        finished_at: String(row.finished_at)
      }))
    },
    economic_finality: "HOLD",
    economic_note: "Technical commissioning evidence does not prove revenue, settlement, or bank receipt."
  };
}

async function verifyAuditChain(env) {
  const result = await env.DB.prepare(
    "SELECT seq,at,actor,event,payload_json,prev_hash,event_hash FROM audit_chain ORDER BY seq"
  ).all();
  let prev = "GENESIS";
  let count = 0;

  for (const row of result.results || []) {
    if (String(row.prev_hash) !== prev) {
      return { ok: false, count, broken_at_seq: Number(row.seq), reason: "prev_hash_mismatch" };
    }
    const expected = await sha256(`${prev}|${row.at}|${row.actor}|${row.event}|${row.payload_json}`);
    if (expected !== String(row.event_hash)) {
      return { ok: false, count, broken_at_seq: Number(row.seq), reason: "event_hash_mismatch" };
    }
    prev = expected;
    count += 1;
  }

  return { ok: true, count, head: prev };
}

function now() {
  return new Date().toISOString();
}

function parseJson(value, fallback) {
  try {
    return JSON.parse(String(value));
  } catch {
    return fallback;
  }
}

function stableStringify(value) {
  if (value === null || typeof value !== "object") return JSON.stringify(value);
  if (Array.isArray(value)) return `[${value.map(stableStringify).join(",")}]`;
  return `{${Object.keys(value).sort().map(key => `${JSON.stringify(key)}:${stableStringify(value[key])}`).join(",")}}`;
}

async function sha256(value) {
  const bytes = new TextEncoder().encode(value);
  const digest = await crypto.subtle.digest("SHA-256", bytes);
  return [...new Uint8Array(digest)].map(byte => byte.toString(16).padStart(2, "0")).join("");
}

function json(value, status = 200) {
  return new Response(JSON.stringify(value), {
    status,
    headers: {
      "content-type": "application/json; charset=utf-8",
      "cache-control": "no-store",
      "x-content-type-options": "nosniff"
    }
  });
}
