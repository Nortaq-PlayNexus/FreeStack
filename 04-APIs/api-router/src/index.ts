/**
 * api-router - free API gateway on Cloudflare Workers.
 * Features: edge caching (KV), provider failover, key protection, per-IP rate limit.
 * Free tier: 100k req/day. Cache hits cost nothing and save upstream quota.
 */
export interface Env {
  KVCACHE: KVNamespace;
  OPENWEATHER_API_KEY?: string;
  WEATHERAPI_KEY?: string;
  NEWSAPI_KEY?: string;
  GNEWS_KEY?: string;
}

type Target = { base: string; path: (p: string) => string; keyName?: string; keyParam?: string; headers?: Record<string,string> };

// The free-API catalog (mirrors ../catalog.yml). Add more endpoints here or in catalog.yml.
const CATALOG: Record<string, Record<string, Target>> = {
  weather: {
    open_meteo: {
      base: "https://api.open-meteo.com/v1",
      path: p => `/forecast${p}`,
    },
    openweathermap: {
      base: "https://api.openweathermap.org/data/2.5",
      path: p => `/weather${p}`,
      keyName: "OPENWEATHER_API_KEY",
      keyParam: "appid",
    },
    weatherapi: {
      base: "https://api.weatherapi.com/v1",
      path: p => `/current.json${p}`,
      keyName: "WEATHERAPI_KEY",
      keyParam: "key",
    },
  },
  crypto: {
    coingecko: {
      base: "https://api.coingecko.com/api/v3",
      path: p => `/coins/${p.replace(/^\//, "") ?? "bitcoin"}`,
    },
    coincap: {
      base: "https://rest.coincap.io/v3",
      path: p => `/assets${p}`,
    },
  },
  fx: {
    frankfurter: { base: "https://api.frankfurter.app", path: p => p },
    exchangerate: { base: "https://open.er-api.com/v6", path: p => `/latest${p}` },
  },
  news: {
    newsapi: {
      base: "https://newsapi.org/v2",
      path: p => `/top-headlines${p}`,
      keyName: "NEWSAPI_KEY",
      keyParam: "apiKey",
    },
    gnews: {
      base: "https://gnews.io/api/v4",
      path: p => `/top-headlines${p}`,
      keyName: "GNEWS_KEY",
      keyParam: "token",
    },
  },
  data: {
    restcountries: { base: "https://restcountries.com/v3.1", path: p => p },
    wikipedia: { base: "https://en.wikipedia.org/api/rest_v1", path: p => p },
    hackernews: { base: "https://hacker-news.firebaseio.com/v0", path: p => p },
  },
};

const TTL_SECONDS = 3600; // 1h cache
const MAX_PER_IP_PER_MIN = 60;

function clientIp(req: Request): string {
  return req.headers.get("cf-connecting-ip") ?? "unknown";
}

async function rateLimited(env: Env, ip: string): Promise<boolean> {
  const key = `rl:${ip}`;
  const n = Number((await env.KVCACHE.get(key)) ?? "0");
  if (n >= MAX_PER_IP_PER_MIN) return true;
  await env.KVCACHE.put(key, String(n + 1), { expirationTtl: 60 });
  return false;
}

async function fetchWithKey(target: Target, url: string, env: Env): Promise<Response> {
  let u = url;
  if (target.keyName) {
    const key = (env as unknown as Record<string, string | undefined>)[target.keyName];
    if (key) u += `${u.includes("?") ? "&" : "?"}${target.keyParam ?? "key"}=${key}`;
  }
  const res = await fetch(u, { headers: { "user-agent": "freestack-api-router/1.0" } });
  if (res.status === 429 && target.keyName) return new Response("rate-limited", { status: 429 });
  return res;
}

export default {
  async fetch(req: Request, env: Env): Promise<Response> {
    const url = new URL(req.url);

    if (url.pathname === "/healthz") {
      return new Response(JSON.stringify({ ok: true }), { headers: { "content-type": "application/json" } });
    }
    if (req.method !== "GET") return new Response("method not allowed", { status: 405 });

    if (await rateLimited(env, clientIp(req))) {
      return new Response("too many requests", { status: 429 });
    }

    // /v1/<category>/<provider>/<rest...>
    const m = url.pathname.match(/^\/v1\/([^/]+)\/([^/]+)\/(.*)$/);
    if (!m) {
      return new Response(
        "usage: /v1/<category>/<provider>/<query>\n" +
          "e.g. /v1/weather/open_meteo/?latitude=40.7&longitude=-74&current=temperature_2m\n" +
          "     /v1/weather/weatherapi/?q=London\n" +
          "     /v1/crypto/coingecko/bitcoin\n" +
          "     /v1/fx/frankfurter/latest?from=USD&to=EUR",
        { status: 400 }
      );
    }
    const [, category, provider, rest] = m;
    const target = CATALOG[category]?.[provider];
    if (!target) return new Response(`unknown ${category}/${provider}`, { status: 404 });

    // cache key = full request minus provider (so failover shares the cache)
    const cacheKey = `c:${category}:${url.search}`;
    const cached = await env.KVCACHE.get(cacheKey);
    if (cached) {
      return new Response(cached, {
        headers: { "content-type": "application/json; charset=utf-8", "x-cache": "HIT" },
      });
    }

    // try providers in order until one succeeds
    const providers = Object.keys(CATALOG[category]);
    for (const p of providers) {
      const t = CATALOG[category][p];
      const upstream = t.base + t.path(rest) + (rest.includes("?") ? "" : "?") + (url.search.replace(/^\?/, ""));
      try {
        const res = await fetchWithKey(t, upstream, env);
        if (res.ok) {
          const body = await res.text();
          await env.KVCACHE.put(cacheKey, body, { expirationTtl: TTL_SECONDS });
          return new Response(body, {
            headers: { "content-type": "application/json; charset=utf-8", "x-cache": "MISS", "x-upstream": p },
          });
        }
        if (res.status === 429) continue; // try next provider
        return new Response(await res.text(), { status: res.status });
      } catch {
        continue; // network error -> next provider
      }
    }
    return new Response("all providers failed or rate-limited", { status: 502 });
  },
};
