# FRAMEWORK: Free APIs (Data, Tools, Everything)
Last researched: 2026-08-12 | Tier: 100% free

## GOAL
Every API you need for building things - data, geolocation, finance, weather, maps, email, AI - at $0. Most need no key at all.

## RULE
Start with NO-KEY APIs for prototyping. Add keyed APIs behind your own server when you need production control. Cache aggressively to stay inside rate limits.

## NO-KEY APIS (curl and go - the cream)
| API | What | Limits |
|---|---|---|
| Open-Meteo | Weather forecasts, 80 yrs history, air quality | 10k calls/day non-commercial, no key |
| wttr.in | Weather as text/JSON | unlimited reasonable |
| CoinGecko | 14,000+ crypto prices | 30 calls/min |
| Frankfurter | ECB currency rates | no key, unlimited reasonable |
| REST Countries | 250+ countries data | unlimited |
| Wikipedia REST | any article as JSON | generous |
| Hacker News (Firebase) | stories/comments | unlimited |
| JSONPlaceholder | fake REST for testing | unlimited |
| httpbin | HTTP request testing | unlimited |
| Open Library | books/search | unlimited |
| Open Notify | ISS location | unlimited |
| PokeAPI | pokemon data | unlimited |
| NASA APIs | APOD, Mars photos, asteroids | free key |
| NWS API | US weather (NOAA) | unlimited, no key |
| OpenFDA | drugs/medical | free key or limited no-key |
| USGS Earthquakes | real-time quakes | unlimited |
| OpenAQ | air quality | 60 req/min |
| sunrise-sunset | sun times | unlimited |
| ip-api.com | IP geolocation | 45 req/min non-commercial |
| SEC EDGAR | company filings | 10 req/s |
| US Treasury | national debt data | unlimited |
| date.nager.at | public holidays | unlimited |
| DiceBear | avatars | unlimited |
| goqr.me / qrserver | QR codes | unlimited |
| randomuser.me | fake user profiles | unlimited |

## KEYED APIS WITH REAL FREE TIERS
| API | Category | Free tier |
|---|---|---|
| OpenWeatherMap | weather | 1M calls/mo (60/min) |
| WeatherAPI.com | weather | 100k calls/mo |
| OpenRouteService | maps/routing | free tier |
| Geoapify | maps | 3,000 credits/day |
| LocationIQ | geocoding | 5,000 req/day |
| ipinfo.io | geolocation | 50k/mo |
| Alpha Vantage | stocks | 25 calls/day |
| Polygon.io | stocks | 5 calls/min |
| Finnhub | stocks | 60 calls/min |
| ExchangeRate-API | fx | 1,500/mo |
| Open Exchange Rates | fx | 1,000/mo |
| News API | news | 100 req/day (dev only) |
| GNews | news | 100 req/day |
| The Guardian | news | 12 calls/sec |
| NYT | news | 500/day |
| Resend | email | 3,000/mo, 100/day |
| GitHub REST | dev | 60/hr unauth, 5,000/hr with token |
| Brave Search | web search | 2,000 queries/mo |
| SerpApi | search | 100 searches/mo |
| Twilio | SMS/voice | trial credit |
| TMDB | media | free non-commercial |

## FRAMEWORK: consume at $0
1. Pick the no-key API for your category first (table above).
2. If you need a key: most are instant email signup, no card (OpenWeatherMap, WeatherAPI, Resend).
3. Behind your own free Cloudflare Worker (see 13-Functions-Serverless), proxy/cache calls: you get a global edge API with your own rate-limit handling for $0.
4. Never call keyed APIs from the browser (exposes the key) - proxy through your free worker/function.

## META (no free tier exists?)
- For "unlimited" of any API: you cannot exceed a provider's free quota forever. The meta is CACHING + the 100-free-account principle is NOT recommended/abusive. Legitimate meta: cache responses at the edge (Cloudflare KV/R2/D1), batch requests, and use the free quotas of MULTIPLE providers for the same data (e.g. 3 weather APIs = ~3x headroom).

## GOTCHAS
- Rate limits are per-IP or per-key; respect them or get banned.
- "unlimited" APIs (Open-Meteo, Frankfurter) are NON-COMMERCIAL - don't sell access.
- Keyed dev tiers (News API) explicitly forbid production use.
- API landscape changes monthly - re-verify quotas before architecting.
- Reference lists: github.com/public-apis/public-apis (keep it starred) is the canonical catalog.
