import urllib.request as r, urllib.error as e, json
req = r.Request('http://localhost:8000/api/shipment/plan/stream', data=json.dumps({'query': 'Ship 500kg from Dubai to Rotterdam'}).encode('utf-8'), headers={'Content-Type': 'application/json'})
try:
    res = r.urlopen(req)
    print("SUCCESS")
except e.HTTPError as err:
    print(err.read().decode('utf-8'))
except Exception as ex:
    print(f"Fetch failed completely: {ex}")
