// Vercel region code -> { lat, lng, label } for the closest data center.
// Source: https://vercel.com/docs/edge-network/regions
export const VERCEL_REGIONS = {
  arn1: { lat: 59.3293, lng: 18.0686, label: 'Stockholm' },
  bom1: { lat: 19.076, lng: 72.8777, label: 'Mumbai' },
  cdg1: { lat: 48.8566, lng: 2.3522, label: 'Paris' },
  cle1: { lat: 41.4993, lng: -81.6944, label: 'Cleveland' },
  cpt1: { lat: -33.9249, lng: 18.4241, label: 'Cape Town' },
  dub1: { lat: 53.3498, lng: -6.2603, label: 'Dublin' },
  fra1: { lat: 50.1109, lng: 8.6821, label: 'Frankfurt' },
  gru1: { lat: -23.5505, lng: -46.6333, label: 'São Paulo' },
  hkg1: { lat: 22.3193, lng: 114.1694, label: 'Hong Kong' },
  hnd1: { lat: 35.6762, lng: 139.6503, label: 'Tokyo' },
  iad1: { lat: 38.9072, lng: -77.0369, label: 'Washington, D.C.' },
  icn1: { lat: 37.5665, lng: 126.978, label: 'Seoul' },
  kix1: { lat: 34.6937, lng: 135.5023, label: 'Osaka' },
  lhr1: { lat: 51.5074, lng: -0.1278, label: 'London' },
  pdx1: { lat: 45.5152, lng: -122.6784, label: 'Portland' },
  sfo1: { lat: 37.7749, lng: -122.4194, label: 'San Francisco' },
  sin1: { lat: 1.3521, lng: 103.8198, label: 'Singapore' },
  syd1: { lat: -33.8688, lng: 151.2093, label: 'Sydney' },
};

// Fallback when no Vercel header is available (local dev).
export const DEFAULT_REGION = { code: 'iad1', ...VERCEL_REGIONS.iad1 };

export function regionFromVercelId(vercelId) {
  if (!vercelId) return null;
  const parts = vercelId.split('::');
  const regionCodes = parts
    .slice(0, -1)
    .map((part) => part.split(':')[0]?.trim().toLowerCase())
    .filter(Boolean);
  // x-vercel-id can look like "lhr1::iad1::request-id": the first region is
  // the ingress edge, and the last region before the request id is where the
  // function executed. That execution region is the server endpoint for the
  // traffic arc.
  const code = regionCodes.at(-1) ?? parts[0]?.split(':')[0]?.trim().toLowerCase();
  if (!code) return null;
  const geo = VERCEL_REGIONS[code];
  return geo ? { code, ...geo } : null;
}
