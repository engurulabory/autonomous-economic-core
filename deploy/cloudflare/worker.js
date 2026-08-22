export default {
  async fetch(request, env) {
    const url = new URL(request.url);
    if (url.pathname === "/health" && request.method === "GET") {
      const row = await env.DB.prepare("SELECT 1 AS ok").first();
      return json({ ok: row?.ok === 1, service: "aec-durable-state", version: "1.1" });
    }

    if (!authorized(request, env)) return json({ error: "unauthorized" }, 401);

    try {
      if (url.pathname === "/idempotency/reserve" && request.method === "POST") {
        const body = await request.json();
        requireFields(body, ["key", "job_id"]);
        try {
          await env.DB.prepare(
            "INSERT INTO idempotency_keys(key, job_id, created_at) VALUES(?,?,?)"
          ).bind(body.key, body.job_id, now()).run();
          return json({ reserved: true });
        } catch (e) {
          if (String(e).toLowerCase().includes("unique") || String(e).toLowerCase().includes("constraint")) {
            return json({ reserved: false });
          }
          throw e;
        }
      }

      if (url.pathname === "/heartbeat" && request.method === "POST") {
        const body = await request.json();
        requireFields(body, ["worker_id"]);
        await env.DB.prepare(
          `INSERT INTO heartbeats(worker_id, at, detail_json) VALUES(?,?,?)
           ON CONFLICT(worker_id) DO UPDATE SET at=excluded.at, detail_json=excluded.detail_json`
        ).bind(body.worker_id, now(), JSON.stringify(body.detail || {})).run();
        return json({ ok: true });
      }

      if (url.pathname === "/lease/acquire" && request.method === "POST") {
        const body = await request.json();
        requireFields(body, ["resource_id", "owner_id"]);
        const ttl = Math.max(5, Math.min(Number(body.ttl_seconds || 120), 3600));
        const current = await env.DB.prepare("SELECT * FROM leases WHERE resource_id=?")
          .bind(body.resource_id).first();
        const currentExpiry = current?.expires_at ? Date.parse(current.expires_at) : 0;
        if (current && currentExpiry > Date.now()) return json({ acquired: false });
        const token = crypto.randomUUID().replaceAll("-", "");
        const expires = new Date(Date.now() + ttl * 1000).toISOString();
        await env.DB.prepare(
          `INSERT INTO leases(resource_id, owner_id, lease_token, expires_at, updated_at)
           VALUES(?,?,?,?,?)
           ON CONFLICT(resource_id) DO UPDATE SET owner_id=excluded.owner_id,
             lease_token=excluded.lease_token, expires_at=excluded.expires_at, updated_at=excluded.updated_at`
        ).bind(body.resource_id, body.owner_id, token, expires, now()).run();
        return json({ acquired: true, lease_token: token, expires_at: expires });
      }

      if (url.pathname === "/lease/release" && request.method === "POST") {
        const body = await request.json();
        requireFields(body, ["resource_id", "owner_id", "lease_token"]);
        const result = await env.DB.prepare(
          "DELETE FROM leases WHERE resource_id=? AND owner_id=? AND lease_token=?"
        ).bind(body.resource_id, body.owner_id, body.lease_token).run();
        return json({ released: Number(result.meta?.changes || 0) === 1 });
      }

      if (url.pathname === "/audit/append" && request.method === "POST") {
        const body = await request.json();
        requireFields(body, ["actor", "event"]);
        const prev = await env.DB.prepare("SELECT event_hash FROM audit_chain ORDER BY seq DESC LIMIT 1").first();
        const prevHash = prev?.event_hash || "GENESIS";
        const at = now();
        const payloadJson = stableStringify(body.payload || {});
        const material = `${prevHash}|${at}|${body.actor}|${body.event}|${payloadJson}`;
        const eventHash = await sha256(material);
        await env.DB.prepare(
          "INSERT INTO audit_chain(at,actor,event,payload_json,prev_hash,event_hash) VALUES(?,?,?,?,?,?)"
        ).bind(at, body.actor, body.event, payloadJson, prevHash, eventHash).run();
        return json({ event_hash: eventHash, prev_hash: prevHash });
      }

      return json({ error: "not_found" }, 404);
    } catch (error) {
      return json({ error: "internal_error", detail: String(error) }, 500);
    }
  }
};

function authorized(request, env) {
  const auth = request.headers.get("authorization") || "";
  return !!env.AEC_STATE_TOKEN && auth === `Bearer ${env.AEC_STATE_TOKEN}`;
}

function requireFields(body, names) {
  for (const name of names) {
    if (typeof body?.[name] !== "string" || body[name].trim() === "") throw new Error(`missing ${name}`);
  }
}

function json(value, status = 200) {
  return new Response(JSON.stringify(value), { status, headers: { "content-type": "application/json" } });
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
