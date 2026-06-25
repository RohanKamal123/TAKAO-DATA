export const config = { runtime: 'edge' };

export default async function handler(req) {
  if (req.method !== 'POST') {
    return new Response('Method not allowed', { status: 405 });
  }

  // CORS — allow your Vercel domain only
  const origin = req.headers.get('origin') || '';
  const allowed = ['https://gaze-app.vercel.app', 'https://takao.vercel.app'];
  if (!allowed.includes(origin)) {
    return new Response('Forbidden', { status: 403 });
  }

  let body;
  try {
    body = await req.json();
  } catch {
    return new Response('Invalid JSON', { status: 400 });
  }

  // Basic validation — must have session + button_id
  if (!body.session || body.button_id === undefined) {
    return new Response('Missing required fields', { status: 400 });
  }

  // Write to Upstash
  const UPSTASH_URL   = process.env.UPSTASH_URL;
  const UPSTASH_TOKEN = process.env.UPSTASH_TOKEN;

  const res = await fetch(`${UPSTASH_URL}/lpush/gaze:samples`, {
    method: 'POST',
    headers: {
      Authorization: `Bearer ${UPSTASH_TOKEN}`,
      'Content-Type': 'application/json',
    },
    body: JSON.stringify([JSON.stringify(body)]),
  });

  if (!res.ok) {
    return new Response('Redis error', { status: 502 });
  }

  return new Response(JSON.stringify({ ok: true }), {
    status: 200,
    headers: { 
      'Content-Type': 'application/json',
      'Access-Control-Allow-Origin': origin,
    },
  });
}