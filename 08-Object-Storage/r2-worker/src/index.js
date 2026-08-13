// r2-worker - serve PRIVATE R2 objects behind a token, plus a token-gated upload.
//
// Deploy:  cd r2-worker && npm i && npx wrangler deploy
// Vars in wrangler.jsonc: OBJECT_TOKEN (long random secret), bucket binding BUCKET.
//
// Routes:
//   GET  /files/<key>?token=...        -> stream object (private read)
//   GET  /list?token=...               -> object keys
//   POST /upload?token=...             -> body = file, header x-filename, returns key
//   DELETE /files/<key>?token=...      -> delete object

function unauthorized() {
  return new Response("unauthorized", { status: 401 });
}

function checkAuth(request, env) {
  const url = new URL(request.url);
  const token = url.searchParams.get("token");
  const header = request.headers.get("authorization")?.replace(/^Bearer\s+/i, "");
  return token === env.OBJECT_TOKEN || header === env.OBJECT_TOKEN;
}

export default {
  async fetch(request, env) {
    const url = new URL(request.url);
    if (url.pathname === "/healthz") return new Response("ok");

    if (!checkAuth(request, env)) return unauthorized();

    // GET /files/<key>
    if (url.pathname.startsWith("/files/") && request.method === "GET") {
      const key = decodeURIComponent(url.pathname.slice("/files/".length));
      const obj = await env.BUCKET.get(key);
      if (!obj) return new Response("not found", { status: 404 });
      const headers = new Headers();
      obj.writeHttpMetadata(headers);
      headers.set("etag", obj.httpEtag);
      headers.set("cache-control", "public, max-age=31536000, immutable");
      return new Response(obj.body, { headers });
    }

    // DELETE /files/<key>
    if (url.pathname.startsWith("/files/") && request.method === "DELETE") {
      const key = decodeURIComponent(url.pathname.slice("/files/".length));
      await env.BUCKET.delete(key);
      return new Response("deleted");
    }

    // GET /list
    if (url.pathname === "/list") {
      const listed = await env.BUCKET.list({ limit: 1000 });
      return Response.json(listed.objects.map((o) => o.key));
    }

    // POST /upload
    if (url.pathname === "/upload" && request.method === "POST") {
      const filename = request.headers.get("x-filename") || crypto.randomUUID();
      const key = url.searchParams.get("key") || filename;
      await env.BUCKET.put(key, request.body, {
        httpMetadata: { contentType: request.headers.get("content-type") || "application/octet-stream" },
      });
      return Response.json({ ok: true, key, url: `/files/${encodeURIComponent(key)}` });
    }

    return new Response("not found", { status: 404 });
  },
};
