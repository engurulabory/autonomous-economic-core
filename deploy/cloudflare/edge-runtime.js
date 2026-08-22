import baseWorker from "./worker.js";

const EDGE_RUNTIME_VERSION = "1.1-edge.1";
const BOOTSTRAP_CYCLE_ID = "edge-bootstrap-v1.1";
const CONTROLLED_EVIDENCE_ID = "internal-controlled-v1.1-runtime-acceptance-edge";
const PROD_WORKER_ID = "production-worker";
const QA_WORKER_ID = "qa-donecheck-worker";
const SETTLEMENT_WORKER_ID = "settlement-collector";
const MAX_ARTIFACT_BYTES = 524288;

export default {
  async fetch(request, env, ctx) {
    const url = new URL(request.url);
    if (url.pathname === "/commissioning/status" && request.method === "GET") {
      try {
        return responseJson(await commissioningStatus(env));
      } catch (error) {
        return responseJson({ ok: false, error: "status_unavailable", detail: String(error) }, 500);
      }
    }
    return baseWorker.fetch(request, env, ctx);
  },

  async scheduled(controller, env, ctx) {
    ctx.waitUntil(runScheduled(controller, env));
  }
};

async function runScheduled(controller, env) {
  const cron = String(controller.cron || "");
  const lease = await acquireSystemLease(env, 240);
  if (!lease) return;

  try {
    if (cron === "*/5 * * * *") {
      const bootstrap = await env.DB.prepare(
        "SELECT status FROM runtime_cycles WHERE cycle_id=?"
      ).bind(BOOTSTRAP_CYCLE_ID).first();

      if (!bootstrap) {
        await runControlledCycle(env, BOOTSTRAP_CYCLE_ID, "cloudflare-bootstrap");
      } else {
        const watchdog = await watchdogSweep(env, "cloudflare-watchdog");
        await appendAudit(env, "cloudflare-watchdog", "WATCHDOG_SWEEP", watchdog);
      }
      return;
    }

    if (cron === "17 * * * *") {
      const hour = new Date(controller.scheduledTime).toISOString().slice(0, 13).replaceAll(/[-T:]/g, "");
      await runControlledCycle(env, `edge-hourly-${hour}`, "cloudflare-hourly");
      return;
    }

    const watchdog = await watchdogSweep(env, "cloudflare-cron");
    await appendAudit(env, "cloudflare-cron", "WATCHDOG_SWEEP", { cron, ...watchdog });
  } finally {
    await releaseSystemLease(env, lease);
  }
}

async function runControlledCycle(env, cycleId, trigger) {
  const startedAt = now();
  const detail = {
    runtime: EDGE_RUNTIME_VERSION,
    trigger,
    economic: false,
    controlled_canary: true
  };

  try {
    const watchdog = await watchdogSweep(env, `${trigger}-watchdog`);
    detail.watchdog = watchdog;

    await heartbeat(env, PROD_WORKER_ID, { phase: "ready", capability: "produce_artifact", runtime: "cloudflare-edge" });
    await heartbeat(env, QA_WORKER_ID, { phase: "ready", capability: "verify_artifact", runtime: "cloudflare-edge" });
    await heartbeat(env, SETTLEMENT_WORKER_ID, { phase: "idle", capability: "collect_settlement", runtime: "cloudflare-edge", economic_actions_enabled: false });

    const productionJob = await ensureControlledProductionJob(env, cycleId);
    const production = await runProductionWorker(env, productionJob.job_id);
    const verification = production.verify_job_id
      ? await runQAWorker(env, production.verify_job_id)
      : { state: "BLOCKED", reason: "verification job was not created" };

    const audit = await verifyAuditChain(env);
    const pass = production.state === "COMPLETED" && verification.state === "COMPLETED" && audit.ok === true;

    detail.production = production;
    detail.verification = verification;
    detail.audit = audit;

    await recordCycle(env, cycleId, startedAt, now(), pass ? "PASS" : "BLOCKED", detail);
    await appendAudit(env, "cloudflare-edge-runtime", "RUNTIME_CYCLE_FINISHED", {
      cycle_id: cycleId,
      status: pass ? "PASS" : "BLOCKED",
      production_job_id: productionJob.job_id,
      verification_job_id: production.verify_job_id || null
    });
  } catch (error) {
    detail.error = `${error?.name || "Error"}: ${error?.message || String(error)}`;
    await recordCycle(env, cycleId, startedAt, now(), "BLOCKED", detail);
    try {
      await appendAudit(env, "cloudflare-edge-runtime", "RUNTIME_CYCLE_BLOCKED", { cycle_id: cycleId, error: detail.error });
    } catch {
      // Preserve the original cycle evidence even if audit append also fails.
    }
    throw error;
  }
}

async function ensureControlledProductionJob(env, cycleId) {
  const suffix = (await sha256(cycleId)).slice(0, 20);
  const jobId = `job_edge_canary_${suffix}`;
  const idempotencyKey = `edge-canary:${cycleId}`;
  const existing = await env.DB.prepare("SELECT * FROM jobs WHERE job_id=?").bind(jobId).first();
  if (existing) return jobView(existing);

  const at = now();
  const payload = {
    output_path: `v1_1_canary/${suffix}.txt`,
    content: "AEC-V1.1-CONTROLLED-EXECUTION-PROOF\nThis is a controlled non-economic runtime acceptance artifact.\n",
    next_verify: {
      contains: ["AEC-V1.1-CONTROLLED-EXECUTION-PROOF", "controlled non-economic runtime acceptance artifact"],
      forbidden: ["PRIVATE_KEY", "SEED_PHRASE", "SECRET_TOKEN"],
      min_bytes: 32,
      max_bytes: 4096
    },
    qualification_evidence_id: CONTROLLED_EVIDENCE_ID
  };

  await env.DB.prepare(
    "INSERT OR IGNORE INTO idempotency_keys(key,job_id,created_at) VALUES(?,?,?)"
  ).bind(idempotencyKey, jobId, at).run();

  await env.DB.prepare(
    `INSERT OR IGNORE INTO jobs(job_id,capability,payload_json,state,attempts,max_attempts,assigned_worker,human_threshold_required,created_at,updated_at)
     VALUES(?,?,?,'QUEUED',0,3,NULL,0,?,?)`
  ).bind(jobId, "produce_artifact", stableStringify(payload), at, at).run();

  await appendJobEvent(env, jobId, "cloudflare-edge-runtime", "ENQUEUED", {
    capability: "produce_artifact",
    qualification_evidence_id: CONTROLLED_EVIDENCE_ID,
    economic: false
  });
  await appendAudit(env, "cloudflare-edge-runtime", "JOB_ENQUEUED", { job_id: jobId, capability: "produce_artifact", controlled: true });

  const created = await env.DB.prepare("SELECT * FROM jobs WHERE job_id=?").bind(jobId).first();
  if (!created) throw new Error("controlled production job could not be created");
  return jobView(created);
}

async function runProductionWorker(env, jobId) {
  const row = await env.DB.prepare("SELECT * FROM jobs WHERE job_id=?").bind(jobId).first();
  if (!row) throw new Error("production job not found");
  if (String(row.state) === "COMPLETED") {
    const event = await env.DB.prepare(
      "SELECT detail_json FROM job_events WHERE job_id=? AND event='PRODUCTION_ARTIFACT' ORDER BY event_id DESC LIMIT 1"
    ).bind(jobId).first();
    const detail = parseJson(event?.detail_json, {});
    return { state: "COMPLETED", artifact_id: detail.artifact_id || null, verify_job_id: detail.verify_job_id || null, idempotent: true };
  }
  if (!["QUEUED", "RETRY_WAIT"].includes(String(row.state))) {
    return { state: String(row.state), reason: "production job is not runnable" };
  }

  const lease = await acquireJobLease(env, jobId, PROD_WORKER_ID, 180);
  if (!lease) return { state: "HOLD", reason: "production lease unavailable" };

  try {
    const assigned = await env.DB.prepare(
      `UPDATE jobs SET state='ASSIGNED',attempts=attempts+1,assigned_worker=?,updated_at=?
       WHERE job_id=? AND state IN ('QUEUED','RETRY_WAIT') AND attempts < max_attempts`
    ).bind(PROD_WORKER_ID, now(), jobId).run();
    if (changes(assigned) !== 1) return { state: "HOLD", reason: "production assignment race" };

    await appendJobEvent(env, jobId, PROD_WORKER_ID, "ASSIGNED", {});
    await env.DB.prepare("UPDATE jobs SET state='RUNNING',updated_at=? WHERE job_id=? AND assigned_worker=?")
      .bind(now(), jobId, PROD_WORKER_ID).run();
    await appendJobEvent(env, jobId, PROD_WORKER_ID, "STARTED", {});
    await heartbeat(env, PROD_WORKER_ID, { phase: "running", job_id: jobId });

    const current = await env.DB.prepare("SELECT payload_json FROM jobs WHERE job_id=?").bind(jobId).first();
    const payload = parseJson(current?.payload_json, {});
    if (String(payload.qualification_evidence_id || "") !== CONTROLLED_EVIDENCE_ID) {
      throw new Error("edge production worker refused non-controlled job");
    }
    const outputPath = String(payload.output_path || "");
    if (!outputPath || outputPath.startsWith("/") || outputPath.split("/").includes("..")) {
      throw new Error("invalid controlled output path");
    }
    const content = typeof payload.content === "string" ? payload.content : stableStringify(payload.content);
    const bytes = new TextEncoder().encode(content);
    if (bytes.byteLength < 1 || bytes.byteLength > MAX_ARTIFACT_BYTES) throw new Error("controlled artifact size invalid");
    const digest = await sha256Bytes(bytes);
    const artifactId = `artifact_${jobId}_${digest.slice(0, 16)}`;
    const contentBase64 = bytesToBase64(bytes);

    const existingArtifact = await env.DB.prepare("SELECT sha256,bytes FROM artifacts WHERE artifact_id=?")
      .bind(artifactId).first();
    if (existingArtifact) {
      if (String(existingArtifact.sha256) !== digest || Number(existingArtifact.bytes) !== bytes.byteLength) {
        throw new Error("artifact id conflict");
      }
    } else {
      await env.DB.prepare(
        "INSERT INTO artifacts(artifact_id,job_id,media_type,content_base64,sha256,bytes,created_at) VALUES(?,?,?,?,?,?,?)"
      ).bind(artifactId, jobId, "text/plain", contentBase64, digest, bytes.byteLength, now()).run();
      await appendAudit(env, "artifact-store", "ARTIFACT_STORED", { artifact_id: artifactId, job_id: jobId, sha256: digest, bytes: bytes.byteLength });
    }

    const verifyJobId = await enqueueVerificationJob(env, jobId, artifactId, digest, payload.next_verify || {});
    await env.DB.prepare("UPDATE jobs SET state='COMPLETED',assigned_worker=NULL,updated_at=? WHERE job_id=?")
      .bind(now(), jobId).run();
    await appendJobEvent(env, jobId, PROD_WORKER_ID, "PRODUCTION_ARTIFACT", { artifact_id: artifactId, verify_job_id: verifyJobId, sha256: digest, bytes: bytes.byteLength });
    await appendJobEvent(env, jobId, PROD_WORKER_ID, "OUTCOME", { state: "COMPLETED", reason: "controlled artifact produced at edge" });
    await appendAudit(env, PROD_WORKER_ID, "JOB_FINISHED", { job_id: jobId, state: "COMPLETED", controlled: true });
    await heartbeat(env, PROD_WORKER_ID, { phase: "finished", job_id: jobId, state: "COMPLETED" });
    return { state: "COMPLETED", artifact_id: artifactId, verify_job_id: verifyJobId, sha256: digest, bytes: bytes.byteLength };
  } catch (error) {
    await env.DB.prepare("UPDATE jobs SET state='BLOCKED',assigned_worker=NULL,updated_at=? WHERE job_id=?")
      .bind(now(), jobId).run();
    await appendJobEvent(env, jobId, PROD_WORKER_ID, "OUTCOME", { state: "BLOCKED", reason: String(error) });
    await appendAudit(env, PROD_WORKER_ID, "JOB_FINISHED", { job_id: jobId, state: "BLOCKED", reason: String(error), controlled: true });
    return { state: "BLOCKED", reason: String(error) };
  } finally {
    await releaseJobLease(env, jobId, PROD_WORKER_ID, lease.lease_token);
  }
}

async function enqueueVerificationJob(env, sourceJobId, artifactId, digest, config) {
  const deterministic = (await sha256(`${sourceJobId}|verify|${artifactId}|${digest}`)).slice(0, 24);
  const jobId = `job_verify_edge_${deterministic}`;
  const at = now();
  const payload = {
    remote_artifact_id: artifactId,
    sha256: digest,
    contains: Array.isArray(config.contains) ? config.contains.map(String) : [],
    forbidden: Array.isArray(config.forbidden) ? config.forbidden.map(String) : [],
    min_bytes: Number.isInteger(Number(config.min_bytes)) ? Number(config.min_bytes) : 1,
    max_bytes: Number.isInteger(Number(config.max_bytes)) ? Number(config.max_bytes) : MAX_ARTIFACT_BYTES,
    source_job_id: sourceJobId,
    qualification_evidence_id: CONTROLLED_EVIDENCE_ID
  };

  await env.DB.prepare("INSERT OR IGNORE INTO idempotency_keys(key,job_id,created_at) VALUES(?,?,?)")
    .bind(`verify:${sourceJobId}:${digest}`, jobId, at).run();
  const before = await env.DB.prepare("SELECT job_id FROM jobs WHERE job_id=?").bind(jobId).first();
  if (!before) {
    await env.DB.prepare(
      `INSERT INTO jobs(job_id,capability,payload_json,state,attempts,max_attempts,assigned_worker,human_threshold_required,created_at,updated_at)
       VALUES(?,?,?,'QUEUED',0,3,NULL,0,?,?)`
    ).bind(jobId, "verify_artifact", stableStringify(payload), at, at).run();
    await appendJobEvent(env, jobId, "cloudflare-edge-runtime", "ENQUEUED", { capability: "verify_artifact", source_job_id: sourceJobId, economic: false });
    await appendAudit(env, "cloudflare-edge-runtime", "JOB_ENQUEUED", { job_id: jobId, capability: "verify_artifact", controlled: true });
  }
  return jobId;
}

async function runQAWorker(env, jobId) {
  const row = await env.DB.prepare("SELECT * FROM jobs WHERE job_id=?").bind(jobId).first();
  if (!row) throw new Error("verification job not found");
  if (String(row.state) === "COMPLETED") return { state: "COMPLETED", idempotent: true };
  if (!["QUEUED", "RETRY_WAIT"].includes(String(row.state))) return { state: String(row.state), reason: "verification job is not runnable" };

  const lease = await acquireJobLease(env, jobId, QA_WORKER_ID, 180);
  if (!lease) return { state: "HOLD", reason: "verification lease unavailable" };

  try {
    const assigned = await env.DB.prepare(
      `UPDATE jobs SET state='ASSIGNED',attempts=attempts+1,assigned_worker=?,updated_at=?
       WHERE job_id=? AND state IN ('QUEUED','RETRY_WAIT') AND attempts < max_attempts`
    ).bind(QA_WORKER_ID, now(), jobId).run();
    if (changes(assigned) !== 1) return { state: "HOLD", reason: "verification assignment race" };

    await env.DB.prepare("UPDATE jobs SET state='RUNNING',updated_at=? WHERE job_id=? AND assigned_worker=?")
      .bind(now(), jobId, QA_WORKER_ID).run();
    await appendJobEvent(env, jobId, QA_WORKER_ID, "STARTED", {});
    await env.DB.prepare("UPDATE jobs SET state='VERIFYING',updated_at=? WHERE job_id=? AND assigned_worker=?")
      .bind(now(), jobId, QA_WORKER_ID).run();
    await appendJobEvent(env, jobId, QA_WORKER_ID, "VERIFYING", { prepared: true });
    await heartbeat(env, QA_WORKER_ID, { phase: "verifying", job_id: jobId });

    const current = await env.DB.prepare("SELECT payload_json FROM jobs WHERE job_id=?").bind(jobId).first();
    const payload = parseJson(current?.payload_json, {});
    if (String(payload.qualification_evidence_id || "") !== CONTROLLED_EVIDENCE_ID) {
      throw new Error("edge QA worker refused non-controlled job");
    }
    const artifact = await env.DB.prepare("SELECT * FROM artifacts WHERE artifact_id=?")
      .bind(String(payload.remote_artifact_id || "")).first();
    if (!artifact) throw new Error("controlled artifact not found");

    const bytes = base64ToBytes(String(artifact.content_base64));
    const digest = await sha256Bytes(bytes);
    const text = new TextDecoder().decode(bytes);
    const failures = [];
    if (Number(artifact.bytes) !== bytes.byteLength) failures.push("artifact byte count mismatch");
    if (String(artifact.sha256) !== digest) failures.push("artifact stored sha256 mismatch");
    if (String(payload.sha256 || "") !== digest) failures.push("verification sha256 mismatch");
    if (bytes.byteLength < Number(payload.min_bytes || 1)) failures.push("artifact below min_bytes");
    if (bytes.byteLength > Number(payload.max_bytes || MAX_ARTIFACT_BYTES)) failures.push("artifact above max_bytes");
    for (const required of payload.contains || []) if (!text.includes(String(required))) failures.push(`missing required text: ${required}`);
    for (const forbidden of payload.forbidden || []) if (text.includes(String(forbidden))) failures.push(`forbidden text present: ${forbidden}`);

    const finalState = failures.length ? "BLOCKED" : "COMPLETED";
    await env.DB.prepare("UPDATE jobs SET state=?,assigned_worker=NULL,updated_at=? WHERE job_id=?")
      .bind(finalState, now(), jobId).run();
    await appendJobEvent(env, jobId, QA_WORKER_ID, "OUTCOME", {
      state: finalState,
      reason: failures.length ? "DoneCheck verification failed" : "DoneCheck verification passed",
      evidence: { failures, sha256: digest, bytes: bytes.byteLength, checks: failures.length ? "BLOCKED" : "PASS" }
    });
    await appendAudit(env, QA_WORKER_ID, "JOB_FINISHED", { job_id: jobId, state: finalState, failures, controlled: true });
    await heartbeat(env, QA_WORKER_ID, { phase: "finished", job_id: jobId, state: finalState });
    return { state: finalState, failures, sha256: digest, bytes: bytes.byteLength };
  } catch (error) {
    await env.DB.prepare("UPDATE jobs SET state='BLOCKED',assigned_worker=NULL,updated_at=? WHERE job_id=?")
      .bind(now(), jobId).run();
    await appendJobEvent(env, jobId, QA_WORKER_ID, "OUTCOME", { state: "BLOCKED", reason: String(error) });
    await appendAudit(env, QA_WORKER_ID, "JOB_FINISHED", { job_id: jobId, state: "BLOCKED", reason: String(error), controlled: true });
    return { state: "BLOCKED", reason: String(error) };
  } finally {
    await releaseJobLease(env, jobId, QA_WORKER_ID, lease.lease_token);
  }
}

async function commissioningStatus(env) {
  const cyclesResult = await env.DB.prepare(
    "SELECT cycle_id,started_at,finished_at,status,detail_json FROM runtime_cycles WHERE cycle_id LIKE 'edge-%' ORDER BY finished_at DESC LIMIT 24"
  ).all();
  const latestProduction = await env.DB.prepare(
    "SELECT job_id,state,attempts,updated_at FROM jobs WHERE job_id LIKE 'job_edge_canary_%' ORDER BY created_at DESC LIMIT 1"
  ).first();
  const latestQA = await env.DB.prepare(
    "SELECT job_id,state,attempts,updated_at FROM jobs WHERE job_id LIKE 'job_verify_edge_%' ORDER BY created_at DESC LIMIT 1"
  ).first();
  const countsResult = await env.DB.prepare("SELECT state,COUNT(*) AS n FROM jobs GROUP BY state ORDER BY state").all();
  const heartbeatResult = await env.DB.prepare(
    "SELECT worker_id,at,detail_json FROM heartbeats WHERE worker_id IN (?,?,?) ORDER BY worker_id"
  ).bind(PROD_WORKER_ID, QA_WORKER_ID, SETTLEMENT_WORKER_ID).all();
  const audit = await verifyAuditChain(env);

  const counts = {};
  for (const row of countsResult.results || []) counts[String(row.state)] = Number(row.n);
  const cycles = (cyclesResult.results || []).map(row => ({
    cycle_id: String(row.cycle_id),
    started_at: String(row.started_at),
    finished_at: String(row.finished_at),
    status: String(row.status),
    detail: sanitizeCycleDetail(parseJson(row.detail_json, {}))
  }));

  return {
    ok: audit.ok === true,
    service: "aec-durable-state",
    version: "1.1",
    edge_runtime_version: EDGE_RUNTIME_VERSION,
    mode: "cloudflare-native-unattended-fallback",
    economic_actions_enabled: false,
    latest_controlled_production: latestProduction ? compactJob(latestProduction) : null,
    latest_controlled_verification: latestQA ? compactJob(latestQA) : null,
    job_counts: counts,
    worker_heartbeats: (heartbeatResult.results || []).map(row => ({
      worker_id: String(row.worker_id), at: String(row.at), detail: parseJson(row.detail_json, {})
    })),
    audit,
    recent_cycles: cycles
  };
}

function sanitizeCycleDetail(detail) {
  return {
    runtime: detail.runtime || null,
    trigger: detail.trigger || null,
    economic: detail.economic === true,
    controlled_canary: detail.controlled_canary === true,
    production: detail.production || null,
    verification: detail.verification || null,
    audit: detail.audit || null,
    watchdog: detail.watchdog || null,
    error: detail.error || null
  };
}

async function watchdogSweep(env, actor) {
  const cutoff = now();
  const result = await env.DB.prepare(
    `SELECT j.* FROM jobs j LEFT JOIN leases l ON l.resource_id=('job:' || j.job_id)
     WHERE j.state IN ('ASSIGNED','RUNNING','VERIFYING') AND (l.resource_id IS NULL OR l.expires_at <= ?)`
  ).bind(cutoff).all();
  let retried = 0;
  let blocked = 0;
  for (const job of result.results || []) {
    const exhausted = Number(job.attempts) >= Number(job.max_attempts);
    const nextState = exhausted ? "BLOCKED" : "RETRY_WAIT";
    await env.DB.prepare(
      "UPDATE jobs SET state=?,assigned_worker=NULL,updated_at=? WHERE job_id=? AND state IN ('ASSIGNED','RUNNING','VERIFYING')"
    ).bind(nextState, now(), job.job_id).run();
    await env.DB.prepare("DELETE FROM leases WHERE resource_id=?").bind(`job:${job.job_id}`).run();
    await appendJobEvent(env, String(job.job_id), actor, "WATCHDOG_RECOVERY", { state: nextState, reason: "missing or expired lease" });
    await appendAudit(env, actor, "WATCHDOG_RECOVERY", { job_id: String(job.job_id), state: nextState });
    if (exhausted) blocked += 1; else retried += 1;
  }
  return { scanned: (result.results || []).length, retried, blocked, at: cutoff };
}

async function heartbeat(env, workerId, detail) {
  await env.DB.prepare(
    `INSERT INTO heartbeats(worker_id,at,detail_json) VALUES(?,?,?)
     ON CONFLICT(worker_id) DO UPDATE SET at=excluded.at,detail_json=excluded.detail_json`
  ).bind(workerId, now(), stableStringify(detail)).run();
}

async function acquireSystemLease(env, ttlSeconds) {
  const resourceId = "system:edge-runtime";
  const ownerId = "cloudflare-edge-runtime";
  const leaseToken = crypto.randomUUID().replaceAll("-", "");
  const at = now();
  const expiresAt = new Date(Date.now() + ttlSeconds * 1000).toISOString();
  const result = await env.DB.prepare(
    `INSERT INTO leases(resource_id,owner_id,lease_token,expires_at,updated_at) VALUES(?,?,?,?,?)
     ON CONFLICT(resource_id) DO UPDATE SET owner_id=excluded.owner_id,lease_token=excluded.lease_token,
       expires_at=excluded.expires_at,updated_at=excluded.updated_at WHERE leases.expires_at <= ?`
  ).bind(resourceId, ownerId, leaseToken, expiresAt, at, at).run();
  return changes(result) === 1 ? { resource_id: resourceId, owner_id: ownerId, lease_token: leaseToken } : null;
}

async function releaseSystemLease(env, lease) {
  await env.DB.prepare("DELETE FROM leases WHERE resource_id=? AND owner_id=? AND lease_token=?")
    .bind(lease.resource_id, lease.owner_id, lease.lease_token).run();
}

async function acquireJobLease(env, jobId, ownerId, ttlSeconds) {
  const resourceId = `job:${jobId}`;
  const leaseToken = crypto.randomUUID().replaceAll("-", "");
  const at = now();
  const expiresAt = new Date(Date.now() + ttlSeconds * 1000).toISOString();
  const result = await env.DB.prepare(
    `INSERT INTO leases(resource_id,owner_id,lease_token,expires_at,updated_at) VALUES(?,?,?,?,?)
     ON CONFLICT(resource_id) DO UPDATE SET owner_id=excluded.owner_id,lease_token=excluded.lease_token,
       expires_at=excluded.expires_at,updated_at=excluded.updated_at WHERE leases.expires_at <= ?`
  ).bind(resourceId, ownerId, leaseToken, expiresAt, at, at).run();
  return changes(result) === 1 ? { lease_token: leaseToken } : null;
}

async function releaseJobLease(env, jobId, ownerId, leaseToken) {
  await env.DB.prepare("DELETE FROM leases WHERE resource_id=? AND owner_id=? AND lease_token=?")
    .bind(`job:${jobId}`, ownerId, leaseToken).run();
}

async function recordCycle(env, cycleId, startedAt, finishedAt, status, detail) {
  await env.DB.prepare(
    `INSERT INTO runtime_cycles(cycle_id,started_at,finished_at,source_sha,status,detail_json)
     VALUES(?,?,?,?,?,?)
     ON CONFLICT(cycle_id) DO UPDATE SET finished_at=excluded.finished_at,status=excluded.status,detail_json=excluded.detail_json`
  ).bind(cycleId, startedAt, finishedAt, null, status, stableStringify(detail)).run();
}

async function appendJobEvent(env, jobId, actor, event, detail) {
  await env.DB.prepare("INSERT INTO job_events(job_id,at,actor,event,detail_json) VALUES(?,?,?,?,?)")
    .bind(jobId, now(), actor, event, stableStringify(detail || {})).run();
}

async function appendAudit(env, actor, event, payload) {
  const payloadJson = stableStringify(payload || {});
  for (let attempt = 0; attempt < 5; attempt += 1) {
    const prev = await env.DB.prepare("SELECT event_hash FROM audit_chain ORDER BY seq DESC LIMIT 1").first();
    const prevHash = prev?.event_hash || "GENESIS";
    const at = now();
    const eventHash = await sha256(`${prevHash}|${at}|${actor}|${event}|${payloadJson}`);
    try {
      await env.DB.prepare(
        "INSERT INTO audit_chain(at,actor,event,payload_json,prev_hash,event_hash) VALUES(?,?,?,?,?,?)"
      ).bind(at, actor, event, payloadJson, prevHash, eventHash).run();
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
  return {
    job_id: String(row.job_id), capability: String(row.capability), state: String(row.state), attempts: Number(row.attempts),
    max_attempts: Number(row.max_attempts), assigned_worker: row.assigned_worker ? String(row.assigned_worker) : null,
    human_threshold_required: Number(row.human_threshold_required) === 1,
    created_at: String(row.created_at), updated_at: String(row.updated_at)
  };
}

function compactJob(row) {
  return { job_id: String(row.job_id), state: String(row.state), attempts: Number(row.attempts), updated_at: String(row.updated_at) };
}

function changes(result) {
  return Number(result?.meta?.changes || 0);
}

function isConstraintError(error) {
  const text = String(error).toLowerCase();
  return text.includes("constraint") || text.includes("unique");
}

function parseJson(value, fallback) {
  try { return JSON.parse(String(value)); } catch { return fallback; }
}

function now() {
  return new Date().toISOString();
}

async function sha256(value) {
  return sha256Bytes(new TextEncoder().encode(String(value)));
}

async function sha256Bytes(bytes) {
  const digest = await crypto.subtle.digest("SHA-256", bytes);
  return [...new Uint8Array(digest)].map(byte => byte.toString(16).padStart(2, "0")).join("");
}

function bytesToBase64(bytes) {
  let binary = "";
  for (let i = 0; i < bytes.length; i += 1) binary += String.fromCharCode(bytes[i]);
  return btoa(binary);
}

function base64ToBytes(value) {
  const binary = atob(value);
  const bytes = new Uint8Array(binary.length);
  for (let i = 0; i < binary.length; i += 1) bytes[i] = binary.charCodeAt(i);
  return bytes;
}

function stableStringify(value) {
  if (value === null || typeof value !== "object") return JSON.stringify(value);
  if (Array.isArray(value)) return `[${value.map(stableStringify).join(",")}]`;
  return `{${Object.keys(value).sort().map(key => `${JSON.stringify(key)}:${stableStringify(value[key])}`).join(",")}}`;
}

function responseJson(value, status = 200) {
  return new Response(JSON.stringify(value), {
    status,
    headers: {
      "content-type": "application/json",
      "cache-control": "no-store",
      "x-content-type-options": "nosniff"
    }
  });
}
