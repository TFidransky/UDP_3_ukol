import json
import pyproj
import math

# třída pro výjimku prázdného souboru. Chtěl jsem se vyhnout užití knihovny pandas, když není ve VS Code defaultně a musí se stáhnout
class EmptyFileException(Exception):
    def __init__(self, message):
        self.message = message

#otevře 2GeoJSONy, zkouší výjimky - 1) chybějící soubor a 2) nevhodný formát souboru, poté return dá aby se daly použít v dalších funkcích
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
            print("Klíč 'geometry' nebo 'coordinates' nebyl nalezen.")
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
def transform_to_SJTSK(adresy):
    transformer = get_transformer()
    if "geometry" not in adresy or "coordinates" not in adresy["geometry"]:
        raise ValueError("Vstupní data mají špatný formát")
    lon, lat = adresy["geometry"]["coordinates"]
    adresa_sjtsk = transformer.transform(lat, lon)
    return adresa_sjtsk

# výpočet vzdáleností mezi kontejnery a adresami skrze Pythagorovu větu, poté vrací seznam těchto vzdáleností
def calculate_distance(container, adresa_sjtsk):
    x1, y1 = adresa_sjtsk
    x2, y2 = container["geometry"]["coordinates"]
    distance = math.sqrt((x1 - x2)**2 + (y1 - y2)**2)
    return distance

# zjišťování vzdáleností, vezme z GeoJSON adres ulici a č. pop., z GeoJSON kontejnerů přístup (volný vs obyvatelům domu)
# projíždí podmínky (if)- 
    # vzdálenost nad 10 k - ukončí program
    # zjišťuje maximální vzdálenost k nejbližšímu kontejneru
    # přístup volný
    # přístup obyvatelům domu
    # vždy to poté hodí vzdálenost od té adresy k nejbližšímu kontejneru do proměnné distances
    # vrací vzdálenosti, nejvzdálenější adresu a jaká byla tato vzdálenost
def nearest_container(adresy, kontejnery):
    distances = []
    max_distance = 0
    farthest_address = ""
    for adresa in adresy:
        if not isinstance(adresa, dict):
            print("Proměnná není datového typu \"slovník\"")
            exit()
        street = adresa["properties"]["addr:street"]
        housenumber = adresa["properties"]["addr:housenumber"]
        adresy_transformed = transform_to_SJTSK(adresa)
        for container in kontejnery:
            access = container["properties"]["PRISTUP"]
            distance = calculate_distance(container, adresy_transformed)
            #if distance >= 10000:
             #   print("Některá adresa je od nejbližšího vhodného kontejneru vzdálenější 10 a více km.")
              #  exit()
            if distance > max_distance:
                max_distance = distance
                max_distance = round(max_distance)
                distances.append(distance)
                farthest_address = (f"{street} {housenumber}")  
            elif access == "volně":
                distances.append(distance)
            elif access == "obyvatelům domu":
                distance = 0
                distances.append(distance)
    return distances, farthest_address, max_distance

# výpočet průměrné a mediánové vzdálenosti
# výpis průměrné vzdálenosti (celku), mediánové vzdálenosti (celku) a maximální vzdálenosti (jedné adresy)
def results (distances, farthest_address, max_distance):                 
    if distances:
        avg_distance = sum(distances) / len(distances)
        distances.sort()
        if len(distances) % 2 == 0:
            median_distance = (distances[len(distances) // 2] + distances[len(distances) // 2 - 1]) / 2
        else:
            median_distance = distances[len(distances) // 2]

        print(f"Průměrná vzdálenost od adres k veřejným kontejnerům: {avg_distance:.0f} metrů")
        print(f"Mediánová vzdálenost od adres k veřejným kontejnerům: {median_distance:.0f} metrů")
        print(f"Nejvzdálenější adresa od nejbližšího veřejného kontejneru: {farthest_address} ({max_distance} metrů)")

def main():
    adresy = open_geojson('adresy.geojson')
    kontejnery = open_geojson('kontejnery.geojson')
    if not check_input_format(adresy) or not check_input_format(kontejnery):
        exit(1)
    distances, farthest_address, max_distance = nearest_container(adresy["features"], kontejnery["features"])
    results(distances, farthest_address, max_distance)

main()