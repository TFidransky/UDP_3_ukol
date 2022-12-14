def open_geojson():
    with open('adresy.geojson') as f:
        adresy = json.load(f)
    with open('kontejnery.geojson') as f:
        kontejnery = json.load(f)
    
def nearest_container(adresy, kontejnery):
    total_distance = 0
    max_distance = 0
    farthest_address = ""
    for adresa in adresy:
        street = adresa["addr:street"]
        housenumber = adresa["addr:housenumber"]
        nearest_container = None
        nearest_distance = float("inf")
        
        for container in kontejnery:
            name = container["STATIONNAME"]
            access = container["PRISTUP"]
            if access == "volně":
                distance = calculate_distance(adresa, container)
                if distance < nearest_distance:
                    nearest_container = container
                    nearest_distance = distance
            if access == "obyvatelům domu": # pokud je access pouze obyvatelům domu, tak to dá vzdálenost 0 pro dům, který odpovídá adrese tohoto kontejneru
                pass

        if nearest_container == None:
            print("Nepodarilo se najit verejny kontejner pro adresu ", street, housenumber)
            print("Nenalezeno")
            return

#Program by měl vypsat průměrnou vzdálenost k veřejnému kontejneru a ze které adresy je to k nejbližšímu kontejneru nejdále a jak to je daleko (v metrech, zaokrouhleno na celé metry).
#Program by se měl umět vypořádat s nekorektním vstupem, jako je vadný nebo chybějící vstupní soubor. Dále by program měl skončit s chybou, pokud pro některou adresu je nejbližší kontejner dále než 10 kilometrů. 
