import json
import pyproj
import math

def open_geojson():
    with open('adresy.geojson', encoding = 'utf-8') as f:
        adresy = json.load(f)
    with open('kontejnery.geojson', encoding = 'utf-8') as f:
        kontejnery = json.load(f)
    return adresy, kontejnery

# potřeba převést adresy na S-JTSK z WGS-84

def calculate_distance(adresa, container):
    # převod souřadnic adresy na S-JTSK
    wgs84 = pyproj.CRS("EPSG:4326")
    sjtsk = pyproj.CRS("EPSG:5514")
    transformer = pyproj.Transformer.from_crs(wgs84, sjtsk)
    adresa_sjtsk = transformer.transform(adresa["geometry"]["coordinates"][0], adresa["geometry"]["coordinates"][1])

    # výpočet vzdálenosti pomocí Pythagorovy věty
    x1, y1 = adresa_sjtsk
    x2, y2 = container["geometry"]["coordinates"]
    distance = math.sqrt((x1 - x2)**2 + (y1 - y2)**2)

    return distance

def nearest_container(adresy, kontejnery):
    distances = []
    max_distance = 0
    farthest_address = ""
    for adresa in adresy:
        if isinstance(adresa, dict):
            street = adresa["properties"]["addr:street"]
            housenumber = adresa["properties"]["addr:housenumber"]
            nearest_container = None
            nearest_distance = None

            for container in kontejnery:
                name = container["properties"]["STATIONNAME"]
                access = container["properties"]["PRISTUP"]
                if access == "obyvatelům domu":
                    nearest_distance = 0
                elif access == "volně":
                    distance = calculate_distance(adresa, container)
                    if nearest_distance is None or distance < nearest_distance:
                        nearest_container = container["properties"]
                        nearest_distance = distance

            if nearest_distance is not None and nearest_distance > 0:
                distances.append(nearest_distance)

                if nearest_distance > max_distance:
                    max_distance = nearest_distance
                    farthest_address = f"{street} {housenumber}"

            if max_distance > 10000:
                    print("Některá adresa je vzdálenější než 10 km.")

    print(len(distances))

    avg_distance = sum(distances) / len(distances)
    distances.sort()
    if len(distances) % 2 == 0:
        median_distance = (distances[len(distances) // 2] + distances[len(distances) // 2 - 1]) / 2
    else:
        median_distance = distances[len(distances) // 2]

    print(f"Průměrná vzdálenost od adres k veřejným kontejnerům: {avg_distance:.2f} metrů")
    print(f"Mediánová vzdálenost od adres k veřejným kontejnerům: {median_distance:.2f} metrů")
    print(f"Nejvzdálenější adresa od nejbližšího veřejného kontejneru je: {farthest_address}, vzdálenost je {max_distance:.2f} metrů")





adresy, kontejnery = open_geojson()
nearest_container(adresy["features"], kontejnery["features"])


#Program by měl vypsat průměrnou vzdálenost k veřejnému kontejneru a ze které adresy je to k nejbližšímu kontejneru nejdále a jak to je daleko (v metrech, zaokrouhleno na celé metry).
#Program by se měl umět vypořádat s nekorektním vstupem, jako je vadný nebo chybějící vstupní soubor. Dále by program měl skončit s chybou, pokud pro některou adresu je nejbližší kontejner dále než 10 kilometrů. 
# Bonus1: kontejnery jen pro obyvatele domu = 0 vzdálenost pro daný dům
# Bonus2: Medián