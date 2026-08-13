/**
 * freestack-mcp — remote MCP server on Cloudflare Workers.
 *
 * Uses the official MCP TypeScript SDK:
 *   - McpServer (tool registry, zod-validated inputs)
 *   - WebStandardStreamableHTTPServerTransport (MCP Streamable HTTP spec,
 *     runs natively on the Workers runtime)
 *
 * Endpoint:  POST /mcp  (and GET /mcp for SSE + DELETE for session teardown)
 * Auth:      Bearer token matching the MCP_AUTH_TOKEN var (all methods).
 *
 * Free tier: 100k requests/day. Personal MCP server for $0.
 *
 * Note on sessions: transports are kept in an in-memory map keyed by session id.
 * Requests that land on a different isolate lose the session (client reconnects).
 * For full durability, move transports into a Durable Object.
 */
import { McpServer } from "@modelcontextprotocol/sdk/server/mcp.js";
import { WebStandardStreamableHTTPServerTransport } from "@modelcontextprotocol/sdk/server/webStandardStreamableHttp.js";
import { z } from "zod";

type Env = {
  KVLITE: KVNamespace;
  MCP_AUTH_TOKEN: string;
};

// The MCP server (tools registered once; env captured lazily per isolate).
let mcpServer: McpServer | null = null;

function getServer(env: Env): McpServer {
  if (mcpServer) return mcpServer;

  mcpServer = new McpServer({ name: "freestack-mcp", version: "1.0.0" });

  // --- tool: current weather (free Open-Meteo, no key) ---
  mcpServer.tool(
    "get_weather",
    "Current weather + hourly forecast for a lat/lon.",
    { latitude: z.number(), longitude: z.number() },
    async ({ latitude, longitude }) => {
      const res = await fetch(
        `https://api.open-meteo.com/v1/forecast?latitude=${latitude}&longitude=${longitude}` +
          `&current=temperature_2m,weather_code,wind_speed_10m&forecast_days=1`
      );
      if (!res.ok) throw new Error("weather upstream failed: " + res.status);
      return { content: [{ type: "text", text: await res.text() }] };
    }
  );

  // --- tool: memory / notes stored in KV (persists across sessions, free) ---
  mcpServer.tool(
    "save_note",
    "Save a note (persists in Cloudflare KV).",
    { key: z.string(), value: z.string() },
    async ({ key, value }) => {
      await env.KVLITE.put(key, value);
      return { content: [{ type: "text", text: `saved note "${key}"` }] };
    }
  );

  mcpServer.tool(
    "get_note",
    "Read a previously saved note from KV.",
    { key: z.string() },
    async ({ key }) => {
      const value = await env.KVLITE.get(key);
      return {
        content: [{ type: "text", text: value ?? `no note stored under "${key}"` }],
      };
    }
  );

  return mcpServer;
}

// In-memory session registry: sessionId -> transport.
const sessions = new Map<string, WebStandardStreamableHTTPServerTransport>();

function unauthorized(): Response {
  return new Response("Unauthorized", { status: 401, headers: { "content-type": "text/plain" } });
}

function authorized(request: Request, env: Env): boolean {
  const token = env.MCP_AUTH_TOKEN;
  if (!token || token === "REPLACE_WITH_LONG_RANDOM_TOKEN") return true; // not configured -> open
  return (request.headers.get("authorization") ?? "").startsWith(`Bearer ${token}`);
}

export default {
  async fetch(request: Request, env: Env): Promise<Response> {
    const url = new URL(request.url);
    if (url.pathname === "/healthz") return new Response("ok");

    if (!url.pathname.startsWith("/mcp")) return new Response("not found", { status: 404 });
    if (!authorized(request, env)) return unauthorized();

    // If the request carries a session id, reuse its transport; else start a new session.
    const sessionId = request.headers.get("mcp-session-id") ?? crypto.randomUUID();
    let transport = sessions.get(sessionId);
    if (!transport) {
      transport = new WebStandardStreamableHTTPServerTransport({
        sessionIdGenerator: () => sessionId,
        onsessionclosed: (id) => {
          sessions.delete(id);
        },
        enableJsonResponse: true, // simple request/response for most clients
      });
      sessions.set(sessionId, transport);
    }

    // Connect is idempotent for the server; wire messages through to the server.
    const server = getServer(env);
    await server.connect(transport);

    const response = await transport.handleRequest(request);
    if (transport.sessionId) response.headers.set("mcp-session-id", transport.sessionId);
    return response;
  },
};
