# gaze

Eye-tracking app. 6 orbs. Look at one — it grows. Dataset captured to Upstash Redis.

## Deploy to Vercel (60 seconds)

1. Install Vercel CLI (once):
   ```
   npm i -g vercel
   ```

2. Deploy:
   ```
   cd gaze-app
   vercel --prod
   ```

3. Open the URL on your phone. Allow camera. Done.

## Retrieve your dataset

From Upstash console or curl:
```bash
curl https://above-oryx-88715.upstash.io/lrange/gaze:samples/0/-1 \
  -H "Authorization: Bearer YOUR_READ_TOKEN"
```

Each item is a JSON string. Parse and convert to CSV/JSONL for training.

## Dataset fields per sample

| field | description |
|---|---|
| session | UUID per browser session |
| ts | Unix ms timestamp |
| button_id | 1–6 which orb was confirmed |
| button_cx/cy | orb center in screen px |
| gaze_raw_x/y | raw WebGazer prediction |
| gaze_smooth_x/y | exponentially smoothed gaze |
| confidence | 0–100 proximity score |
| screen_w/h | viewport size |

## Later: remove credentials from frontend

When done testing, move credentials to a Vercel Edge Function
so the write token is never exposed in client JS.