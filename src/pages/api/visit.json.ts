import type { APIRoute } from 'astro';
import { Redis } from '@upstash/redis';
import process from 'node:process';
import { DEFAULT_REGION, VERCEL_REGIONS, regionFromVercelId } from '../../scripts/three-globe/regions.js';

export const prerender = false;

type Visit = {
  id: string;
  ts: number;
  source: { lat: number; lng: number; city?: string; country?: string };
  server: { lat: number; lng: number; code: string; label: string };
  demo?: boolean;
};

const BUFFER_LIMIT = 1000;
const MAX_AGE_MS = 24 * 60 * 60 * 1000;
const REDIS_KEY = 'globe:visits';

const REDIS_URL = process.env.KV_REST_API_URL ?? process.env.UPSTASH_REDIS_REST_URL;
const REDIS_TOKEN = process.env.KV_REST_API_TOKEN ?? process.env.UPSTASH_REDIS_REST_TOKEN;

// Shared store across all serverless instances when env vars are present
// (Vercel KV / Upstash). Falls back to per-instance memory for local dev.
const redis = REDIS_URL && REDIS_TOKEN ? new Redis({ url: REDIS_URL, token: REDIS_TOKEN }) : null;

const localBuffer: Visit[] = [];

async function pushVisit(v: Visit) {
  if (redis) {
    await redis.lpush(REDIS_KEY, JSON.stringify(v));
    await redis.ltrim(REDIS_KEY, 0, BUFFER_LIMIT - 1);
    await redis.expire(REDIS_KEY, Math.floor(MAX_AGE_MS / 1000));
    return;
  }
  localBuffer.push(v);
  const cutoff = Date.now() - MAX_AGE_MS;
  while (localBuffer.length > 0 && localBuffer[0].ts < cutoff) localBuffer.shift();
  while (localBuffer.length > BUFFER_LIMIT) localBuffer.shift();
}

async function readRecent(since: number): Promise<Visit[]> {
  const cutoff = Math.max(since, Date.now() - MAX_AGE_MS);
  if (redis) {
    const raw = await redis.lrange(REDIS_KEY, 0, BUFFER_LIMIT - 1);
    // Upstash auto-parses JSON values; fall back to manual parse for strings.
    const parsed: Visit[] = raw
      .map((r) => (typeof r === 'string' ? (JSON.parse(r) as Visit) : (r as Visit)))
      .filter((v) => v && typeof v.ts === 'number');
    return parsed.filter((v) => v.ts > cutoff).sort((a, b) => a.ts - b.ts);
  }
  return localBuffer.filter((v) => v.ts > cutoff);
}

function readSource(headers: globalThis.Headers) {
  const lat = parseFloat(headers.get('x-vercel-ip-latitude') ?? '');
  const lng = parseFloat(headers.get('x-vercel-ip-longitude') ?? '');
  if (Number.isFinite(lat) && Number.isFinite(lng)) {
    const rawCity = headers.get('x-vercel-ip-city') ?? undefined;
    return {
      lat,
      lng,
      city: rawCity ? decodeURIComponent(rawCity) : undefined,
      country: headers.get('x-vercel-ip-country') ?? undefined,
    };
  }
  return null;
}

function readServer(headers: globalThis.Headers) {
  const region = regionFromVercelId(headers.get('x-vercel-id'));
  if (region) return region;
  const fallbackCode = headers.get('x-vercel-deployment-url')?.match(/-([a-z]{3}\d)\./)?.[1] ?? null;
  if (fallbackCode && fallbackCode in VERCEL_REGIONS) {
    return { code: fallbackCode, ...VERCEL_REGIONS[fallbackCode as keyof typeof VERCEL_REGIONS] };
  }
  return DEFAULT_REGION;
}

export const POST: APIRoute = async ({ request }) => {
  const server = readServer(request.headers);
  const realSource = readSource(request.headers);

  // In local dev there are no Vercel geo headers; surface a flag instead of
  // fabricating a fake "real" visitor location.
  const source = realSource ?? { lat: 25.033, lng: 121.5654, city: 'Taipei', country: 'TW' };

  const visit: Visit = {
    id: globalThis.crypto.randomUUID(),
    ts: Date.now(),
    source,
    server,
    ...(realSource ? {} : { demo: true }),
  };
  await pushVisit(visit);

  return new Response(JSON.stringify({ visit, server }), {
    status: 200,
    headers: { 'Content-Type': 'application/json', 'Cache-Control': 'no-store' },
  });
};

export const GET: APIRoute = async ({ url, request }) => {
  const since = parseInt(url.searchParams.get('since') ?? '0', 10) || 0;
  const recent = await readRecent(since);
  return new Response(JSON.stringify({ visits: recent, server: readServer(request.headers), now: Date.now() }), {
    status: 200,
    headers: { 'Content-Type': 'application/json', 'Cache-Control': 'no-store' },
  });
};
