// /healthz - status endpoint for Upptime/UptimeRobot/Better Stack (folder 11)
export async function onRequest() {
  return new Response(JSON.stringify({ ok: true, uptime: "up" }), {
    headers: { "content-type": "application/json; charset=utf-8" }
  });
}
