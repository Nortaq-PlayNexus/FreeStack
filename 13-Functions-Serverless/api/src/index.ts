/**
 * api/src/index.ts - full free-serverless app on one Worker.
 * Bindings: DB (D1), KV, FILES (R2), plus var API_TOKEN.
 */
export interface Env {
  DB: D1Database;
  KV: KVNamespace;
  FILES: R2Bucket;
  API_TOKEN: string;
}

const CORS = {
  "access-control-allow-origin": "*",
  "access-control-allow-methods": "GET,POST,PUT,DELETE,OPTIONS",
  "access-control-allow-headers": "content-type,authorization",
};

function json(body: unknown, status = 200): Response {
  return new Response(JSON.stringify(body), { status, headers: { "content-type": "application/json", ...CORS } });
}

function authorized(request: Request, env: Env): boolean {
  const h = request.headers.get("authorization") || "";
  return h === `Bearer ${env.API_TOKEN}`;
}

export default {
  async fetch(request: Request, env: Env): Promise<Response> {
    const url = new URL(request.url);
    if (request.method === "OPTIONS") return new Response(null, { status: 204, headers: CORS });

    // health: report DB / KV / R2 liveness
    if (url.pathname === "/healthz") {
      const db = await env.DB.prepare("SELECT 1 as ok").first().catch(() => null);
      const kv = await env.KV.get("healthz").catch(() => null);
      const files = await env.FILES.list({ limit: 1 }).catch(() => null);
      return json({ ok: true, db: !!db, kv: kv !== null, r2: !!files });
    }

    // --- /api/items: list (KV-cached) + create (D1) ---
    if (url.pathname === "/api/items") {
      if (request.method === "GET") {
        const cached = await env.KV.get("items");
        if (cached) return json(JSON.parse(cached));
        const { results } = await env.DB.prepare("SELECT * FROM items ORDER BY created_at DESC LIMIT 50").all();
        await env.KV.put("items", JSON.stringify(results), { expirationTtl: 60 });
        return json(results);
      }
      if (request.method === "POST") {
        if (!authorized(request, env)) return json({ error: "unauthorized" }, 401);
        const body = await request.json<{ name: string }>().catch(() => null);
        if (!body?.name) return json({ error: "name required" }, 400);
        const res = await env.DB.prepare("INSERT INTO items (name) VALUES (?) RETURNING *").bind(body.name).first();
        await env.KV.delete("items"); // bust cache
        return json(res, 201);
      }
    }

    // --- /api/files/:key: stream + upload to R2 ---
    if (url.pathname.startsWith("/api/files/")) {
      const key = decodeURIComponent(url.pathname.slice("/api/files/".length));
      if (request.method === "GET") {
        const obj = await env.FILES.get(key);
        if (!obj) return json({ error: "not found" }, 404);
        const headers = new Headers();
        obj.writeHttpMetadata(headers);
        headers.set("etag", obj.httpEtag);
        headers.set("cache-control", "public, max-age=86400");
        return new Response(obj.body, { headers });
      }
      if (request.method === "PUT") {
        if (!authorized(request, env)) return json({ error: "unauthorized" }, 401);
        await env.FILES.put(key, request.body, { httpMetadata: { contentType: request.headers.get("content-type") || undefined } });
        return json({ ok: true, key, url: `/api/files/${encodeURIComponent(key)}` }, 201);
      }
    }

    return json({ error: "not found", routes: ["/healthz", "/api/items", "/api/files/:key"] }, 404);
  },

  async scheduled(_event: ScheduledController, env: Env): Promise<void> {
    // daily: warm D1, prune expired KV cache keys
    await env.DB.prepare("DELETE FROM items WHERE created_at < datetime('now','-365 days')").run();
    await env.KV.delete("items");
    console.log("scheduled job done");
  },
} satisfies ExportedHandler<Env>;
