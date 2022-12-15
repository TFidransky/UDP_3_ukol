import json
import pyproj

def open_geojson():
    with open('adresy.geojson', encoding = 'utf-8') as f:
        adresy = json.load(f)
    with open('kontejnery.geojson', encoding = 'utf-8') as f:
        kontejnery = json.load(f)
    return adresy, kontejnery

# potřeba převést adresy na S-JTSK z WGS-84

def calculate_distance(adresa, container):
    # udělat výpočet vzdálenosti
    pass

def nearest_container(adresy, kontejnery):
    total_distance = 0
    max_distance = 0
    farthest_address = ""
    count = 0 # slouží pro průměrnou vzdálenost, problém, že se nepřičítá hodnota

    for adresa in adresy:
        if isinstance(adresa, dict):
            street = adresa["addr:street"]
            housenumber = adresa["addr:housenumber"]
            nearest_container = None
            nearest_distance = None

            for container in kontejnery:
                name = container["STATIONNAME"]
                access = container["PRISTUP"]
                if access == "volně":
                    distance = calculate_distance(adresa, container)
                    if nearest_distance is None or distance < nearest_distance:
                        nearest_container = container
                        nearest_distance = distance

                    if nearest_distance is None or distance < nearest_distance:
                        nearest_container = container
                        nearest_distance = distance

            if nearest_distance is not None:
                total_distance += nearest_distance
                count += 1

                if nearest_distance > max_distance:
                    max_distance = nearest_distance
                    farthest_address = f"{street} {housenumber}"

    avg_distance = total_distance / count

    print(f"Průměrná vzdálenost k veřejnému kontejneru je {avg_distance:.0f} metrů")
    print(f"Nejvzdálenější adresa je {farthest_address} a vzdálenost k nejbližšímu kontejneru je {max_distance:.0f} metrů")

    if max_distance > 10000:
        raise ValueError("Některá adresa je vzdálenější než 10 km od nejbližšího kontejneru")

adresy, kontejnery = open_geojson()
nearest_container(adresy, kontejnery)


#Program by měl vypsat průměrnou vzdálenost k veřejnému kontejneru a ze které adresy je to k nejbližšímu kontejneru nejdále a jak to je daleko (v metrech, zaokrouhleno na celé metry).
#Program by se měl umět vypořádat s nekorektním vstupem, jako je vadný nebo chybějící vstupní soubor. Dále by program měl skončit s chybou, pokud pro některou adresu je nejbližší kontejner dále než 10 kilometrů. 
# Bonus1: kontejnery jen pro obyvatele domu = 0 vzdálenost pro daný dům
# Bonus2: Medián