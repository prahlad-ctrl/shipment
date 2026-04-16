import urllib.request as r, urllib.error as e, json

data = {
    'query': 'Ship 120 cartons of textiles (0.5x0.4x0.4 meters each) and 5 pallets of parts (1.2x1x1 meters each) from Dubai to Rotterdam under $4000',
    'world_event': 'normal'
}

req = r.Request(
    'http://localhost:8000/api/shipment/plan/stream', 
    data=json.dumps(data).encode('utf-8'), 
    headers={'Content-Type': 'application/json'}
)

try:
    with r.urlopen(req) as res:
        for line in res:
            print(line.decode('utf-8').strip())
except Exception as ex:
    print(f"Fetch failed completely: {ex}")
