import urllib.request as r, urllib.error as e, json

# Exact query from Dubai -> Rotterdam with no weight
data = {
    'query': 'Ship 120 cartons of textiles (0.5x0.4x0.4 meters each) and 5 pallets of parts (1.2x1x1 meters each) from Dubai to Rotterdam under $4000',
    'world_event': 'normal'
}

req = r.Request(
    'http://localhost:8000/api/shipment/plan', 
    data=json.dumps(data).encode('utf-8'), 
    headers={'Content-Type': 'application/json'}
)

try:
    res = r.urlopen(req)
    print("SUCCESS")
    print(res.read().decode('utf-8')[:200]) # Print start of response
except e.HTTPError as err:
    print(f"HTTP ERROR: {err.code}")
    print(err.read().decode('utf-8'))
except Exception as ex:
    print(f"Fetch failed completely: {ex}")
