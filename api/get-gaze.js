export const config = { runtime: 'edge' };

export default async function handler(req) {
  if (req.method !== 'GET') {
    return new Response('Method not allowed', { status: 405 });
  }

  // Simple password check via query param
  const url    = new URL(req.url);
  const pwd    = url.searchParams.get('pwd');
  const count  = parseInt(url.searchParams.get('count') || '100');
  const offset = parseInt(url.searchParams.get('offset') || '0');

  if (pwd !== process.env.ADMIN_PASSWORD) {
    return new Response('Unauthorized', { status: 401 });
  }

  const UPSTASH_URL   = process.env.UPSTASH_URL;
  const UPSTASH_TOKEN = process.env.UPSTASH_TOKEN;

  // LLEN — get total count
  const lenRes  = await fetch(`${UPSTASH_URL}/llen/gaze:samples`, {
    headers: { Authorization: `Bearer ${UPSTASH_TOKEN}` },
  });
  const lenData = await lenRes.json();
  const total   = lenData.result || 0;

  // LRANGE — get samples (newest first, Redis LPUSH = newest at index 0)
  const rangeRes  = await fetch(
    `${UPSTASH_URL}/lrange/gaze:samples/${offset}/${offset + count - 1}`,
    { headers: { Authorization: `Bearer ${UPSTASH_TOKEN}` } }
  );
  const rangeData = await rangeRes.json();
  const samples   = (rangeData.result || []).map(s => {
    try { return JSON.parse(s); } catch { return null; }
  }).filter(Boolean);

  return new Response(JSON.stringify({ total, count: samples.length,
                                       offset, samples }), {
    status: 200,
    headers: { 'Content-Type': 'application/json' },
  });
}