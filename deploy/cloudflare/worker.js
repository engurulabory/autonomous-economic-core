const VERSION = "1.1";
const FINISH_STATES = new Set(["COMPLETED", "RETRY_WAIT", "HOLD", "BLOCKED"]);
const MAX_ARTIFACT_BYTES = 524288;

export default {
  async fetch(request, env) {
    const url = new URL(request.url);
    if (url.pathname === "/health" && request.method === "GET") {
      const row = await env.DB.prepare("SELECT 1 AS ok").first();
      return json({ ok: row?.ok === 1, service: "aec-durable-state", version: VERSION });
    }

    if (!authorized(request, env)) return json({ error: "unauthorized" }, 401);

    try {
      if (url.pathname === "/idempotency/reserve" && request.method === "POST") {
        const body = await readObject(request);
        requireFields(body, ["key", "job_id"]);
        const reserved = await reserveIdempotency(env, body.key, body.job_id);
        return json({ reserved });
      }

      if (url.pathname === "/heartbeat" && request.method === "POST") {
        const body = await readObject(request);
        requireFields(body, ["worker_id"]);
        await env.DB.prepare(
          `INSERT INTO heartbeats(worker_id, at, detail_json) VALUES(?,?,?)
           ON CONFLICT(worker_id) DO UPDATE SET at=excluded.at, detail_json=excluded.detail_json`
        ).bind(body.worker_id, now(), stableStringify(body.detail || {})).run();
        return json({ ok: true });
      }

      if (url.pathname === "/heartbeats/stale" && request.method === "GET") {
        const olderThan = boundedInt(url.searchParams.get("older_than_seconds") || "900", 5, 86400, "older_than_seconds");
        const cutoff = new Date(Date.now() - olderThan * 1000).toISOString();
        const result = await env.DB.prepare(
          "SELECT worker_id, at, detail_json FROM heartbeats WHERE at < ? ORDER BY at"
        ).bind(cutoff).all();
        return json({ cutoff, workers: (result.results || []).map(row => ({
          worker_id: row.worker_id,
          at: row.at,
          detail: parseJson(row.detail_json, {})
        })) });
      }

      if (url.pathname === "/lease/acquire" && request.method === "POST") {
        const body = await readObject(request);
        requireFields(body, ["resource_id", "owner_id"]);
        const ttl = boundedInt(body.ttl_seconds ?? 120, 5, 3600, "ttl_seconds");
        const lease = await acquireLease(env, body.resource_id, body.owner_id, ttl);
        return json(lease ? { acquired: true, ...lease } : { acquired: false });
      }

      if (url.pathname === "/lease/release" && request.method === "POST") {
        const body = await readObject(request);
        requireFields(body, ["resource_id", "owner_id", "lease_token"]);
        return json({ released: await releaseLease(env, body.resource_id, body.owner_id, body.lease_token) });
      }

      if (url.pathname === "/jobs/enqueue" && request.method === "POST") {
        const body = await readObject(request);
        requireFields(body, ["job_id", "capability", "qualification_state", "qualification_evidence_id", "idempotency_key"]);
        if (body.qualification_state !== "QUALIFIED") return json({ error: "qualification_required" }, 409);
        if (body.payload !== undefined && !isPlainObject(body.payload)) return json({ error: "payload_must_be_object" }, 400);
        const maxAttempts = boundedInt(body.max_attempts ?? 3, 1, 20, "max_attempts");
        const humanThreshold = body.human_threshold_required === true;

        const existingKey = await env.DB.prepare("SELECT job_id FROM idempotency_keys WHERE key=?")
          .bind(body.idempotency_key).first();
        if (existingKey && String(existingKey.job_id) !== body.job_id) {
          return json({ error: "idempotency_conflict", existing_job_id: String(existingKey.job_id) }, 409);
        }
        if (!existingKey) {
          const reserved = await reserveIdempotency(env, body.idempotency_key, body.job_id);
          if (!reserved) {
            const raced = await env.DB.prepare("SELECT job_id FROM idempotency_keys WHERE key=?")
              .bind(body.idempotency_key).first();
            if (!raced || String(raced.job_id) !== body.job_id) return json({ error: "idempotency_conflict" }, 409);
          }
        }

        const prior = await env.DB.prepare("SELECT * FROM jobs WHERE job_id=?").bind(body.job_id).first();
        if (prior) return json({ created: false, idempotent: true, job: jobView(prior) });

        const at = now();
        const initialState = humanThreshold ? "HOLD" : "QUEUED";
        const payload = { ...(body.payload || {}), qualification_evidence_id: body.qualification_evidence_id };
        try {
          await env.DB.prepare(
            `INSERT INTO jobs(job_id, capability, payload_json, state, attempts, max_attempts,
                              assigned_worker, human_threshold_required, created_at, updated_at)
             VALUES(?,?,?,?,0,?,?,?, ?, ?)`
          ).bind(
            body.job_id, body.capability, stableStringify(payload), initialState, maxAttempts,
            null, humanThreshold ? 1 : 0, at, at
          ).run();
        } catch (error) {
          if (!isConstraintError(error)) throw error;
          const raced = await env.DB.prepare("SELECT * FROM jobs WHERE job_id=?").bind(body.job_id).first();
          if (raced) return json({ created: false, idempotent: true, job: jobView(raced) });
          throw error;
        }
        await appendJobEvent(env, body.job_id, "runtime", humanThreshold ? "HUMAN_THRESHOLD_HOLD" : "ENQUEUED", {
          capability: body.capability,
          qualification_evidence_id: body.qualification_evidence_id
        });
        await appendAudit(env, "runtime", "JOB_ENQUEUED", { job_id: body.job_id, capability: body.capability, state: initialState });
        const created = await env.DB.prepare("SELECT * FROM jobs WHERE job_id=?").bind(body.job_id).first();
        return json({ created: true, idempotent: false, job: jobView(created) }, 201);
      }

      if (url.pathname === "/jobs/lease" && request.method === "POST") {
        const body = await readObject(request);
        requireFields(body, ["worker_id"]);
        requireStringArray(body.capabilities, "capabilities", 1, 50);
        const ttl = boundedInt(body.ttl_seconds ?? 300, 5, 3600, "ttl_seconds");
        const leased = await leaseNextJob(env, body.worker_id, body.capabilities, ttl);
        return json(leased ? { leased: true, ...leased } : { leased: false });
      }

      if (url.pathname === "/jobs/start" && request.method === "POST") {
        const body = await readObject(request);
        requireFields(body, ["job_id", "worker_id", "lease_token"]);
        const valid = await leaseValid(env, `job:${body.job_id}`, body.worker_id, body.lease_token);
        if (!valid) return json({ error: "invalid_or_expired_lease" }, 409);
        const result = await env.DB.prepare(
          "UPDATE jobs SET state='RUNNING', updated_at=? WHERE job_id=? AND state='ASSIGNED' AND assigned_worker=?"
        ).bind(now(), body.job_id, body.worker_id).run();
        if (changes(result) !== 1) return json({ error: "invalid_job_state" }, 409);
        await appendJobEvent(env, body.job_id, body.worker_id, "STARTED", {});
        return json({ ok: true });
      }

      if (url.pathname === "/jobs/verifying" && request.method === "POST") {
        const body = await readObject(request);
        requireFields(body, ["job_id", "worker_id", "lease_token"]);
        const valid = await leaseValid(env, `job:${body.job_id}`, body.worker_id, body.lease_token);
        if (!valid) return json({ error: "invalid_or_expired_lease" }, 409);
        const result = await env.DB.prepare(
          "UPDATE jobs SET state='VERIFYING', updated_at=? WHERE job_id=? AND state='RUNNING' AND assigned_worker=?"
        ).bind(now(), body.job_id, body.worker_id).run();
        if (changes(result) !== 1) return json({ error: "invalid_job_state" }, 409);
        await appendJobEvent(env, body.job_id, body.worker_id, "VERIFYING", body.evidence || {});
        return json({ ok: true });
      }

      if (url.pathname === "/jobs/finish" && request.method === "POST") {
        const body = await readObject(request);
        requireFields(body, ["job_id", "worker_id", "lease_token", "outcome_state", "reason"]);
        if (!FINISH_STATES.has(body.outcome_state)) return json({ error: "invalid_outcome_state" }, 400);
        const valid = await leaseValid(env, `job:${body.job_id}`, body.worker_id, body.lease_token);
        if (!valid) return json({ error: "invalid_or_expired_lease" }, 409);
        const job = await env.DB.prepare("SELECT * FROM jobs WHERE job_id=?").bind(body.job_id).first();
        if (!job || !["RUNNING", "VERIFYING"].includes(String(job.state)) || String(job.assigned_worker) !== body.worker_id) {
          return json({ error: "invalid_job_state" }, 409);
        }
        let finalState = body.outcome_state;
        let reason = body.reason;
        if (finalState === "RETRY_WAIT" && Number(job.attempts) >= Number(job.max_attempts)) {
          finalState = "BLOCKED";
          reason = `retry budget exhausted: ${body.reason}`;
        }
        await env.DB.prepare(
          "UPDATE jobs SET state=?, assigned_worker=NULL, updated_at=? WHERE job_id=?"
        ).bind(finalState, now(), body.job_id).run();
        await appendJobEvent(env, body.job_id, body.worker_id, "OUTCOME", {
          state: finalState,
          reason,
          evidence: body.evidence || {}
        });
        if (finalState === "BLOCKED") {
          await deadLetter(env, body.job_id, reason, { evidence: body.evidence || {}, payload: parseJson(job.payload_json, {}) });
        }
        await releaseLease(env, `job:${body.job_id}`, body.worker_id, body.lease_token);
        await appendAudit(env, body.worker_id, "JOB_FINISHED", { job_id: body.job_id, state: finalState, reason });
        return json({ ok: true, state: finalState, reason });
      }

      if (url.pathname === "/jobs/human-release" && request.method === "POST") {
        const body = await readObject(request);
        requireFields(body, ["job_id", "actor", "authority_evidence_id"]);
        const result = await env.DB.prepare(
          `UPDATE jobs SET state='QUEUED', human_threshold_required=0, updated_at=?
           WHERE job_id=? AND state='HOLD' AND human_threshold_required=1`
        ).bind(now(), body.job_id).run();
        if (changes(result) !== 1) return json({ error: "job_not_waiting_on_human_threshold" }, 409);
        await appendJobEvent(env, body.job_id, body.actor, "HUMAN_THRESHOLD_RELEASED", {
          authority_evidence_id: body.authority_evidence_id,
          evidence: body.evidence || {}
        });
        await appendAudit(env, body.actor, "HUMAN_THRESHOLD_RELEASED", {
          job_id: body.job_id,
          authority_evidence_id: body.authority_evidence_id
        });
        return json({ ok: true, state: "QUEUED" });
      }

      if (url.pathname === "/jobs/counts" && request.method === "GET") {
        const result = await env.DB.prepare("SELECT state, COUNT(*) AS n FROM jobs GROUP BY state ORDER BY state").all();
        const counts = {};
        for (const row of result.results || []) counts[String(row.state)] = Number(row.n);
        return json({ counts });
      }

      if (url.pathname.startsWith("/jobs/") && request.method === "GET") {
        const jobId = decodeURIComponent(url.pathname.slice("/jobs/".length));
        if (!jobId) return json({ error: "job_id_required" }, 400);
        const row = await env.DB.prepare("SELECT * FROM jobs WHERE job_id=?").bind(jobId).first();
        if (!row) return json({ error: "not_found" }, 404);
        const events = await env.DB.prepare(
          "SELECT event_id, at, actor, event, detail_json FROM job_events WHERE job_id=? ORDER BY event_id"
        ).bind(jobId).all();
        return json({ job: jobView(row), events: (events.results || []).map(eventView) });
      }

      if (url.pathname === "/artifacts/put" && request.method === "POST") {
        const body = await readObject(request);
        requireFields(body, ["artifact_id", "job_id", "media_type", "content_base64", "sha256"]);
        const byteLength = boundedInt(body.bytes ?? 0, 0, MAX_ARTIFACT_BYTES, "bytes");
        if (body.content_base64.length > Math.ceil(MAX_ARTIFACT_BYTES * 4 / 3) + 8) return json({ error: "artifact_too_large" }, 413);
        const existing = await env.DB.prepare("SELECT sha256, bytes FROM artifacts WHERE artifact_id=?")
          .bind(body.artifact_id).first();
        if (existing) {
          if (String(existing.sha256) !== body.sha256 || Number(existing.bytes) !== byteLength) return json({ error: "artifact_id_conflict" }, 409);
          return json({ stored: false, idempotent: true });
        }
        await env.DB.prepare(
          `INSERT INTO artifacts(artifact_id, job_id, media_type, content_base64, sha256, bytes, created_at)
           VALUES(?,?,?,?,?,?,?)`
        ).bind(body.artifact_id, body.job_id, body.media_type, body.content_base64, body.sha256, byteLength, now()).run();
        await appendAudit(env, "artifact-store", "ARTIFACT_STORED", {
          artifact_id: body.artifact_id, job_id: body.job_id, sha256: body.sha256, bytes: byteLength
        });
        return json({ stored: true, idempotent: false }, 201);
      }

      if (url.pathname.startsWith("/artifacts/") && request.method === "GET") {
        const artifactId = decodeURIComponent(url.pathname.slice("/artifacts/".length));
        if (!artifactId) return json({ error: "artifact_id_required" }, 400);
        const row = await env.DB.prepare("SELECT * FROM artifacts WHERE artifact_id=?").bind(artifactId).first();
        if (!row) return json({ error: "not_found" }, 404);
        return json({ artifact: {
          artifact_id: String(row.artifact_id), job_id: String(row.job_id), media_type: String(row.media_type),
          content_base64: String(row.content_base64), sha256: String(row.sha256), bytes: Number(row.bytes),
          created_at: String(row.created_at)
        }});
      }

      if (url.pathname === "/watchdog/sweep" && request.method === "POST") {
        const body = await readObject(request);
        const actor = typeof body.actor === "string" && body.actor.trim() ? body.actor : "watchdog";
        return json(await watchdogSweep(env, actor));
      }

      if (url.pathname === "/dead-letters" && request.method === "GET") {
        const limit = boundedInt(url.searchParams.get("limit") || "50", 1, 200, "limit");
        const result = await env.DB.prepare("SELECT * FROM dead_letters ORDER BY created_at DESC LIMIT ?").bind(limit).all();
        return json({ dead_letters: (result.results || []).map(row => ({
          dead_id: String(row.dead_id), job_id: String(row.job_id), reason: String(row.reason),
          payload: parseJson(row.payload_json, {}), created_at: String(row.created_at)
        })) });
      }

      if (url.pathname === "/audit/append" && request.method === "POST") {
        const body = await readObject(request);
        requireFields(body, ["actor", "event"]);
        return json(await appendAudit(env, body.actor, body.event, body.payload || {}));
      }

      if (url.pathname === "/audit/verify" && request.method === "GET") return json(await verifyAuditChain(env));

      if (url.pathname === "/cycles/record" && request.method === "POST") {
        const body = await readObject(request);
        requireFields(body, ["cycle_id", "started_at", "finished_at", "status"]);
        if (!["PASS", "HOLD", "BLOCKED"].includes(body.status)) return json({ error: "invalid_cycle_status" }, 400);
        await env.DB.prepare(
          `INSERT INTO runtime_cycles(cycle_id, started_at, finished_at, source_sha, status, detail_json)
           VALUES(?,?,?,?,?,?)
           ON CONFLICT(cycle_id) DO UPDATE SET finished_at=excluded.finished_at, source_sha=excluded.source_sha,
             status=excluded.status, detail_json=excluded.detail_json`
        ).bind(body.cycle_id, body.started_at, body.finished_at, body.source_sha || null, body.status, stableStringify(body.detail || {})).run();
        return json({ ok: true });
      }

      if (url.pathname === "/cycles/recent" && request.method === "GET") {
        const limit = boundedInt(url.searchParams.get("limit") || "24", 1, 168, "limit");
        const result = await env.DB.prepare("SELECT * FROM runtime_cycles ORDER BY finished_at DESC LIMIT ?").bind(limit).all();
        return json({ cycles: (result.results || []).map(row => ({
          cycle_id: String(row.cycle_id), started_at: String(row.started_at), finished_at: String(row.finished_at),
          source_sha: row.source_sha ? String(row.source_sha) : null, status: String(row.status), detail: parseJson(row.detail_json, {})
        })) });
      }

      return json({ error: "not_found" }, 404);
    } catch (error) {
      const message = String(error);
      const status = message.startsWith("Error: invalid_") || message.startsWith("Error: missing ") ? 400 : 500;
      return json({ error: status === 400 ? "bad_request" : "internal_error", detail: message }, status);
    }
  },

  async scheduled(controller, env, ctx) {
    ctx.waitUntil((async () => {
      const result = await watchdogSweep(env, "cloudflare-cron");
      await appendAudit(env, "cloudflare-cron", "WATCHDOG_SWEEP", result);
      const at = now();
      await env.DB.prepare(
        `INSERT INTO runtime_cycles(cycle_id, started_at, finished_at, source_sha, status, detail_json)
         VALUES(?,?,?,?,?,?) ON CONFLICT(cycle_id) DO NOTHING`
      ).bind(`cf-${controller.scheduledTime}`, at, at, null, "PASS", stableStringify({ trigger: "cloudflare-cron", result })).run();
    })());
  }
};

async function leaseNextJob(env, workerId, capabilities, ttlSeconds) {
  const placeholders = capabilities.map(() => "?").join(",");
  const query = `SELECT * FROM jobs WHERE state IN ('QUEUED','RETRY_WAIT') AND human_threshold_required=0
                 AND attempts < max_attempts AND capability IN (${placeholders}) ORDER BY created_at, job_id LIMIT 10`;
  const candidates = await env.DB.prepare(query).bind(...capabilities).all();
  for (const row of candidates.results || []) {
    const resourceId = `job:${row.job_id}`;
    const lease = await acquireLease(env, resourceId, workerId, ttlSeconds);
    if (!lease) continue;
    const result = await env.DB.prepare(
      `UPDATE jobs SET state='ASSIGNED', attempts=attempts+1, assigned_worker=?, updated_at=?
       WHERE job_id=? AND state IN ('QUEUED','RETRY_WAIT') AND human_threshold_required=0 AND attempts < max_attempts`
    ).bind(workerId, now(), row.job_id).run();
    if (changes(result) !== 1) {
      await releaseLease(env, resourceId, workerId, lease.lease_token);
      continue;
    }
    const job = await env.DB.prepare("SELECT * FROM jobs WHERE job_id=?").bind(row.job_id).first();
    await appendJobEvent(env, row.job_id, workerId, "ASSIGNED", { attempt: Number(job.attempts) });
    await appendAudit(env, workerId, "JOB_ASSIGNED", { job_id: String(row.job_id), capability: String(row.capability) });
    return { job: jobView(job), lease_token: lease.lease_token, lease_expires_at: lease.expires_at };
  }
  return null;
}

async function watchdogSweep(env, actor) {
  const cutoff = now();
  const result = await env.DB.prepare(
    `SELECT j.* FROM jobs j LEFT JOIN leases l ON l.resource_id = ('job:' || j.job_id)
     WHERE j.state IN ('ASSIGNED','RUNNING','VERIFYING') AND (l.resource_id IS NULL OR l.expires_at <= ?)`
  ).bind(cutoff).all();
  let retried = 0;
  let blocked = 0;
  for (const job of result.results || []) {
    const exhausted = Number(job.attempts) >= Number(job.max_attempts);
    const nextState = exhausted ? "BLOCKED" : "RETRY_WAIT";
    await env.DB.prepare(
      "UPDATE jobs SET state=?, assigned_worker=NULL, updated_at=? WHERE job_id=? AND state IN ('ASSIGNED','RUNNING','VERIFYING')"
    ).bind(nextState, now(), job.job_id).run();
    await env.DB.prepare("DELETE FROM leases WHERE resource_id=?").bind(`job:${job.job_id}`).run();
    await appendJobEvent(env, String(job.job_id), actor, "WATCHDOG_RECOVERY", { state: nextState, reason: "missing or expired lease" });
    if (exhausted) {
      blocked += 1;
      await deadLetter(env, String(job.job_id), "watchdog: retry budget exhausted", { payload: parseJson(job.payload_json, {}) });
    } else retried += 1;
  }
  return { scanned: (result.results || []).length, retried, blocked, at: cutoff };
}

async function reserveIdempotency(env, key, jobId) {
  requireNonEmptyString(key, "key");
  requireNonEmptyString(jobId, "job_id");
  const result = await env.DB.prepare("INSERT OR IGNORE INTO idempotency_keys(key, job_id, created_at) VALUES(?,?,?)")
    .bind(key, jobId, now()).run();
  return changes(result) === 1;
}

async function acquireLease(env, resourceId, ownerId, ttlSeconds) {
  requireNonEmptyString(resourceId, "resource_id");
  requireNonEmptyString(ownerId, "owner_id");
  const token = crypto.randomUUID().replaceAll("-", "");
  const at = now();
  const expires = new Date(Date.now() + ttlSeconds * 1000).toISOString();
  const result = await env.DB.prepare(
    `INSERT INTO leases(resource_id, owner_id, lease_token, expires_at, updated_at) VALUES(?,?,?,?,?)
     ON CONFLICT(resource_id) DO UPDATE SET owner_id=excluded.owner_id, lease_token=excluded.lease_token,
       expires_at=excluded.expires_at, updated_at=excluded.updated_at WHERE leases.expires_at <= ?`
  ).bind(resourceId, ownerId, token, expires, at, at).run();
  if (changes(result) !== 1) return null;
  return { resource_id: resourceId, owner_id: ownerId, lease_token: token, expires_at: expires };
}

async function releaseLease(env, resourceId, ownerId, leaseToken) {
  const result = await env.DB.prepare("DELETE FROM leases WHERE resource_id=? AND owner_id=? AND lease_token=?")
    .bind(resourceId, ownerId, leaseToken).run();
  return changes(result) === 1;
}

async function leaseValid(env, resourceId, ownerId, leaseToken) {
  const row = await env.DB.prepare(
    "SELECT 1 AS ok FROM leases WHERE resource_id=? AND owner_id=? AND lease_token=? AND expires_at > ?"
  ).bind(resourceId, ownerId, leaseToken, now()).first();
  return row?.ok === 1;
}

async function appendJobEvent(env, jobId, actor, event, detail) {
  await env.DB.prepare("INSERT INTO job_events(job_id, at, actor, event, detail_json) VALUES(?,?,?,?,?)")
    .bind(jobId, now(), actor, event, stableStringify(detail || {})).run();
}

async function deadLetter(env, jobId, reason, payload) {
  const deadId = `dead_${crypto.randomUUID().replaceAll("-", "")}`;
  await env.DB.prepare("INSERT INTO dead_letters(dead_id, job_id, reason, payload_json, created_at) VALUES(?,?,?,?,?)")
    .bind(deadId, jobId, reason, stableStringify(payload || {}), now()).run();
  await appendAudit(env, "runtime", "DEAD_LETTERED", { dead_id: deadId, job_id: jobId, reason });
  return deadId;
}

async function appendAudit(env, actor, event, payload) {
  requireNonEmptyString(actor, "actor");
  requireNonEmptyString(event, "event");
  const payloadJson = stableStringify(payload || {});
  for (let attempt = 0; attempt < 5; attempt += 1) {
    const prev = await env.DB.prepare("SELECT event_hash FROM audit_chain ORDER BY seq DESC LIMIT 1").first();
    const prevHash = prev?.event_hash || "GENESIS";
    const at = now();
    const eventHash = await sha256(`${prevHash}|${at}|${actor}|${event}|${payloadJson}`);
    try {
      await env.DB.prepare("INSERT INTO audit_chain(at,actor,event,payload_json,prev_hash,event_hash) VALUES(?,?,?,?,?,?)")
        .bind(at, actor, event, payloadJson, prevHash, eventHash).run();
      return { event_hash: eventHash, prev_hash: prevHash };
    } catch (error) {
      if (!isConstraintError(error) || attempt === 4) throw error;
    }
  }
  throw new Error("audit append retry exhausted");
}

async function verifyAuditChain(env) {
  const result = await env.DB.prepare("SELECT * FROM audit_chain ORDER BY seq").all();
  let prev = "GENESIS";
  let count = 0;
  for (const row of result.results || []) {
    if (String(row.prev_hash) !== prev) return { ok: false, count, broken_at_seq: Number(row.seq) };
    const expected = await sha256(`${prev}|${row.at}|${row.actor}|${row.event}|${row.payload_json}`);
    if (expected !== String(row.event_hash)) return { ok: false, count, broken_at_seq: Number(row.seq) };
    prev = expected;
    count += 1;
  }
  return { ok: true, count, head: prev };
}

function jobView(row) {
  if (!row) return null;
  return {
    job_id: String(row.job_id), capability: String(row.capability), payload: parseJson(row.payload_json, {}),
    state: String(row.state), attempts: Number(row.attempts), max_attempts: Number(row.max_attempts),
    assigned_worker: row.assigned_worker ? String(row.assigned_worker) : null,
    human_threshold_required: Number(row.human_threshold_required) === 1,
    created_at: String(row.created_at), updated_at: String(row.updated_at)
  };
}
function eventView(row) {
  return { event_id: Number(row.event_id), at: String(row.at), actor: String(row.actor), event: String(row.event), detail: parseJson(row.detail_json, {}) };
}
function authorized(request, env) {
  const auth = request.headers.get("authorization") || "";
  return !!env.AEC_STATE_TOKEN && auth === `Bearer ${env.AEC_STATE_TOKEN}`;
}
async function readObject(request) {
  const body = await request.json();
  if (!isPlainObject(body)) throw new Error("invalid_json_object");
  return body;
}
function requireFields(body, names) { for (const name of names) requireNonEmptyString(body?.[name], name); }
function requireNonEmptyString(value, name) { if (typeof value !== "string" || value.trim() === "") throw new Error(`missing ${name}`); }
function requireStringArray(value, name, min, max) {
  if (!Array.isArray(value) || value.length < min || value.length > max || value.some(v => typeof v !== "string" || !v.trim())) throw new Error(`invalid_${name}`);
}
function boundedInt(value, min, max, name) {
  const parsed = Number(value);
  if (!Number.isInteger(parsed) || parsed < min || parsed > max) throw new Error(`invalid_${name}`);
  return parsed;
}
function changes(result) { return Number(result?.meta?.changes || 0); }
function isConstraintError(error) { const text = String(error).toLowerCase(); return text.includes("constraint") || text.includes("unique"); }
function isPlainObject(value) { return value !== null && typeof value === "object" && !Array.isArray(value); }
function parseJson(value, fallback) { try { return JSON.parse(String(value)); } catch { return fallback; } }
function json(value, status = 200) {
  return new Response(JSON.stringify(value), { status, headers: { "content-type": "application/json", "cache-control": "no-store", "x-content-type-options": "nosniff" } });
}
function now() { return new Date().toISOString(); }
async function sha256(value) {
  const bytes = new TextEncoder().encode(value);
  const digest = await crypto.subtle.digest("SHA-256", bytes);
  return [...new Uint8Array(digest)].map(b => b.toString(16).padStart(2, "0")).join("");
}
function stableStringify(value) {
  if (value === null || typeof value !== "object") return JSON.stringify(value);
  if (Array.isArray(value)) return `[${value.map(stableStringify).join(",")}]`;
  return `{${Object.keys(value).sort().map(k => `${JSON.stringify(k)}:${stableStringify(value[k])}`).join(",")}}`;
}
