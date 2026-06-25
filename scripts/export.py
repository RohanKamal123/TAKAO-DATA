import os
import json
import requests
from datetime import datetime, timezone
from pathlib import Path

UPSTASH_URL   = os.environ['UPSTASH_URL']
UPSTASH_TOKEN = os.environ['UPSTASH_TOKEN']

HEADERS = {'Authorization': f'Bearer {UPSTASH_TOKEN}'}

def redis_get(path):
    res = requests.get(f'{UPSTASH_URL}/{path}', headers=HEADERS)
    res.raise_for_status()
    return res.json()

def redis_set(key, value):
    res = requests.get(
        f'{UPSTASH_URL}/set/{key}/{value}', 
        headers=HEADERS
    )
    res.raise_for_status()
    return res.json()

def extract_payload(raw):
    """
    save-gaze.js stores each sample as: JSON.stringify([JSON.stringify(body)])
    So lrange returns elements like: '["{...serialized payload...}"]'
    This function unwraps that double-wrapping.
    """
    parsed = json.loads(raw)
    # If parsed is a list, the actual payload is the first element (JSON string)
    if isinstance(parsed, list):
        if len(parsed) == 0:
            return None
        # The first element is the JSON-stringified payload
        inner = parsed[0]
        if isinstance(inner, str):
            return json.loads(inner)
        # If it's already a dict, return it directly
        if isinstance(inner, dict):
            return inner
        return None
    # If parsed is already a dict, use it directly
    if isinstance(parsed, dict):
        return parsed
    return None

def main():
    today = datetime.now(timezone.utc).strftime('%Y-%m-%d')
    
    # Get total list length
    total = redis_get('llen/gaze:samples')['result']
    print(f'Total samples in Redis: {total}')
    
    # Get export cursor (how many we've already exported)
    try:
        cursor_res = redis_get('get/gaze:export_cursor')
        cursor = int(cursor_res['result'] or 0)
    except:
        cursor = 0
    print(f'Export cursor: {cursor}')
    
    if total <= cursor:
        print('No new samples to export.')
        return
    
    new_count = total - cursor
    print(f'New samples to export: {new_count}')
    
    # Fetch only new samples (newest first, index 0..new_count-1)
    samples_raw = redis_get(f'lrange/gaze:samples/0/{new_count - 1}')['result']
    
    # Parse and validate
    samples = []
    skipped = 0
    for raw in samples_raw:
        try:
            s = extract_payload(raw)
            if s is None:
                skipped += 1
                continue
            if not s.get('session') or s.get('button_id') is None:
                skipped += 1
                continue
            samples.append(s)
        except Exception as e:
            print(f'  Skipped malformed sample: {e}')
            skipped += 1
    
    print(f'Valid: {len(samples)}, Skipped: {skipped}')
    
    if not samples:
        print('No valid samples to write.')
        return
    
    # Write to data/raw/samples/YYYY-MM-DD.jsonl
    out_dir = Path('data/raw/samples')
    out_dir.mkdir(parents=True, exist_ok=True)
    out_file = out_dir / f'{today}.jsonl'
    
    # Append mode — safe to re-run same day
    with open(out_file, 'a') as f:
        for s in samples:
            f.write(json.dumps(s) + '\n')
    
    print(f'Written to {out_file}')
    
    # Update cursor
    redis_set('gaze:export_cursor', total)
    print(f'Cursor updated to {total}')
    print(f'Export complete: {len(samples)} samples')

if __name__ == '__main__':
    main()