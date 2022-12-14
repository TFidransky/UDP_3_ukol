import json
from geopy.distance import geodesic


# načteme vstupní GeoJSON soubory
with open('adresy.geojson') as f:
    adresy = json.load(f)
with open('kontejnery.geojson') as f:
    kontejnery = json.load(f)
    