import json
import sys

import pyproj
import math


# třída pro výjimku prázdného souboru. Chtěl jsem se vyhnout užití knihovny pandas, když není ve VS Code defaultně a musí se stáhnout
class EmptyFileException(Exception):
    def __init__(self, message):
        self.message = message

# otevře 2GeoJSONy, zkouší výjimky - 1) chybějící soubor a 2) nevhodný formát souboru, poté return dá aby se daly použít v dalších funkcích
def open_geojson(filename):
    try:
        with open(filename, encoding='utf-8') as f:
            if f.tell() == f.seek(0, 2):
                raise EmptyFileException(f"Vstupní soubor {filename} je prázdný.")
            f.seek(0)
            data = json.load(f)
    except FileNotFoundError:
        print(f"Vstupní soubor {filename} nebyl nalezen.")
        exit(1)
    except EmptyFileException:
        print(f"Vstupní soubor {filename} byl prázdný")
        exit(1)
    except json.JSONDecodeError:
        print(f"Nevhodný formát vstupního souboru {filename}.")
        exit(1)
    return data

# kontroluje, že jsou v souborech klíče na správných pozicích, pokud nejsou, tak vrátí False, pokud jsou, tak na konci vrátí True; v konzoli to vypíše příslušnou chybu
# kontroluje pouze ty klíče, které jsou v obou souborech totožné, tedy ne ["PRISTUP"], který je pouze v kontejnery.geojson, nebo naopak ["addr:street"] nebo ["addr:housenumber"]v adresy.geojson
def check_input_format(data):
    for key in data:
        if "features" not in data:
            print(f"Klíč '{key}' nebyl nalezen ve vstupních souborech")
            return False

    for feature in data["features"]:
        if "geometry" not in feature or "coordinates" not in feature["geometry"]:
            print("Klíč 'geometry' nebo 'coordinates' v 'geometry' nebyl nalezen.")
            return False
        if "properties" not in feature:
            print("Klíč 'properties' nebyl nalezen")
            return False

    return True

# vytvoří proměnnou transformer, aby se transformer nemusel vytvářet pro každou adresu, ten poté vrací pro další užití
def get_transformer():
    wgs84 = pyproj.CRS("EPSG:4326")
    sjtsk = pyproj.CRS("EPSG:5514")
    transformer = pyproj.Transformer.from_crs(wgs84, sjtsk)
    return transformer

# pomocí transformeru (proměnná z funkce výše) transformuje adresy z WGS-84 do S-JTSK (aby bylo možné vypočítat vzdálenosti)
def transform_to_SJTSK(adresa, transformer):
    if "geometry" not in adresa or "coordinates" not in adresa["geometry"]:
        print("Vstupní data mají špatný formát")
        exit(1)
    lon, lat = adresa["geometry"]["coordinates"]
    adresa_sjtsk = transformer.transform(lat, lon)
    return adresa_sjtsk

# nachází nejvzdálenější adresu domu od nejbližšího vhodného kontejneru
# pokud je adresa 10 km nebo více, tak se program ukončí a nakonec vrátí nejvzdálenější adresu a příslušnou vzdálenost
def check_min_distance(adresy, kontejnery, transformer):
    longest_distances = []
    max_of_min = 0
    max_of_min_address = ""

    for adress in adresy:
        min_dist = 10000
        min_addr = ""
        lat, lon = transform_to_SJTSK(adress, transformer)
        for kontejner in kontejnery:
            tmp = calculate_distance(kontejner, (lat, lon))
            if tmp < min_dist:
                min_dist = tmp
                street = adress["properties"]["addr:street"]
                housenumber = adress["properties"]["addr:housenumber"]
                min_addr = (f"{street} {housenumber}")

        longest_distances.append(min_dist)
        if min_dist >= 10000:
            print("Některá adresa je od nejbližšího vhodného kontejneru vzdálenější 10 a více km.")
            exit()
        if min_dist >= max_of_min:
            max_of_min = min_dist
            max_of_min_address = min_addr

    return max_of_min_address, max_of_min

# výpočet vzdáleností mezi kontejnery a adresami skrze Pythagorovu větu, poté vrací seznam těchto vzdáleností
def calculate_distance(container, adresa_sjtsk):
    x1, y1 = adresa_sjtsk
    x2, y2 = container["geometry"]["coordinates"]
    distance = math.sqrt((x1 - x2) ** 2 + (y1 - y2) ** 2)
    return distance


# zjišťování vzdáleností, vezme z GeoJSON adres ulici a č. pop., z GeoJSON kontejnerů přístup (volný vs obyvatelům domu)
# projíždí podmínky (if)-
    # přístup volný
    # přístup obyvatelům domu
# vždy to poté hodí vzdálenost od té adresy k nejbližšímu kontejneru do proměnné distances
# vrací vzdálenosti, nejvzdálenější adresu a jaká byla tato vzdálenost
def container_distance(adresy, kontejnery):
    transformer = get_transformer()
    distances = []

    farthest_address, max_distance = check_min_distance(adresy, kontejnery, transformer)

    for adresa in adresy:
        if not isinstance(adresa, dict):
            print("Proměnná není datového typu \"slovník\"")
            exit()
        adresa_transformed = transform_to_SJTSK(adresa, transformer)
        for container in kontejnery:
            access = container["properties"]["PRISTUP"]
            distance = calculate_distance(container, adresa_transformed)
            if access == "volně":
                distances.append(distance)
            elif access == "obyvatelům domu":
                distance = 0
                distances.append(distance)

    return distances, farthest_address, max_distance

# výpočet průměrné a mediánové vzdálenosti
# výpis průměrné vzdálenosti (celku), mediánové vzdálenosti (celku) a maximální vzdálenosti (jedné adresy)
def results(distances, farthest_address, max_distance):
    if distances:
        avg_distance = sum(distances) / len(distances)
        distances.sort()
        if len(distances) % 2 == 0:
            median_distance = (distances[len(distances) // 2] + distances[len(distances) // 2 - 1]) / 2
        else:
            median_distance = distances[len(distances) // 2]

        print(f"Průměrná vzdálenost od adres k veřejným kontejnerům: {avg_distance:.0f} metrů")
        print(f"Mediánová vzdálenost od adres k veřejným kontejnerům: {median_distance:.0f} metrů")
        print(f"Nejvzdálenější adresa od nejbližšího veřejného kontejneru: {farthest_address} ({max_distance:.0f} metrů)")

def main():
    adresy = open_geojson('adresy.geojson')
    kontejnery = open_geojson('kontejnery.geojson')
    if not check_input_format(adresy) or not check_input_format(kontejnery):
        exit(1)
    distances, farthest_address, max_distance = container_distance(adresy["features"], kontejnery["features"])
    results(distances, farthest_address, max_distance)

main()