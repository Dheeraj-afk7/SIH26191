import json
import urllib.parse
import urllib.request

q = '[out:json][timeout:25];(relation["boundary"="protected_area"](30.15,78.80,30.85,79.40);way["boundary"="protected_area"](30.15,78.80,30.85,79.40);relation["leisure"="nature_reserve"](30.15,78.80,30.85,79.40);way["leisure"="nature_reserve"](30.15,78.80,30.85,79.40););out body geom;'
url = 'https://overpass-api.de/api/interpreter?data=' + urllib.parse.quote(q)

req = urllib.request.Request(url, headers={'User-Agent': 'SIH26191-GIS/1.0'})
try:
    with urllib.request.urlopen(req, timeout=25) as resp:
        data = json.loads(resp.read().decode('utf-8'))
        elements = data.get('elements', [])
        print(f"Elements returned: {len(elements)}")
        for e in elements:
            tags = e.get('tags', {})
            print(f"  {e['type']} {e['id']} | name: {tags.get('name')} | boundary: {tags.get('boundary')} | leisure: {tags.get('leisure')} | protect_class: {tags.get('protect_class')}")
except Exception as ex:
    print(f"Failed: {ex}")
