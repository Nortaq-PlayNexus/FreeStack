// Pages Function: /api/hello -> adds dynamic JSON to a static site (free, 100k req/day)
export async function onRequest() {
  return new Response(JSON.stringify({
    ok: true,
    message: "Hello from a Cloudflare Pages Function - free serverless, no server.",
    time: new Date().toISOString()
  }), {
    headers: { "content-type": "application/json; charset=utf-8" }
  });
}
