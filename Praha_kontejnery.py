import json
import pyproj
import math

#otevře 2GeoJSONy, zkouší výjimky - 1) chybějící soubor a 2) nevhodný formát souboru, poté return dá aby se daly použít v dalších funkcích
def open_geojson():
    try:
        with open('adresy.geojson', encoding='utf-8') as f:
            adresy = json.load(f)
        with open('kontejnery.geojson', encoding='utf-8') as f:
            kontejnery = json.load(f)
    except FileNotFoundError:
        print("Jeden nebo oba vstupní soubory nebyly nalezeny.")
        return
    except json.JSONDecodeError:
        print("Nevhodný formát vstupních souborů.")
        return
    return adresy, kontejnery

# transformuje adresy z WGS-84 do S-JTSK (pro výpočet vzdáleností)
def transform_to_SJTSK(adresy):
    if "geometry" not in adresy or "coordinates" not in adresy["geometry"]:
        raise ValueError("Input data mají špatný formát")
    lon, lat = adresy["geometry"]["coordinates"]
    wgs84 = pyproj.CRS("EPSG:4326")
    sjtsk = pyproj.CRS("EPSG:5514")
    transformer = pyproj.Transformer.from_crs(wgs84, sjtsk)
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
# 
def nearest_container(adresy, kontejnery):
    distances = []
    max_distance = 0
    farthest_address = ""
    for adresa in adresy:
        if isinstance(adresa, dict):
            street = adresa["properties"]["addr:street"]
            housenumber = adresa["properties"]["addr:housenumber"]
            adresy_transformed = transform_to_SJTSK(adresa)
            for container in kontejnery:
                access = container["properties"]["PRISTUP"]
                distance = calculate_distance(container, adresy_transformed)
                if distance >= 10000:
                    print("Některá adresa je od nejbližšího vhodného kontejneru vzdálenější 10 a více km.")
                    exit()
                if distance > max_distance:
                    max_distance = distance
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
       
        print(f"Průměrná vzdálenost od adres k veřejným kontejnerům: {avg_distance:.2f} metrů")
        print(f"Mediánová vzdálenost od adres k veřejným kontejnerům: {median_distance:.2f} metrů")
        print(f"Nejvzdálenější adresa od nejbližšího veřejného kontejneru: {farthest_address} ({max_distance:.2f} metrů)")

def main():
    adresy, kontejnery = open_geojson()
    distances, farthest_address, max_distance = nearest_container(adresy["features"], kontejnery["features"])
    results(distances, farthest_address, max_distance)

main()