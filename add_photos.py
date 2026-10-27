# Finds one free photo per stop on Wikimedia Commons, saves it to photos/<tour>/<i>.jpg,
# and writes the photo path + credit into both language files of the tour.
# Usage: python add_photos.py lisbon        (all stops)
#        python add_photos.py lisbon 7 20   (only these stops)
import json, pathlib, re, sys, time, urllib.parse, urllib.request

QUERIES = {  # stop index -> search words; stops left out get no photo
    "lisbon": {0: "Rossio square Lisbon", 2: "Elevador de Santa Justa", 4: "Baixa Pombalina Lisboa rua", 5: "Galerias Romanas Lisboa",
               6: "Arco da Rua Augusta", 7: "Terreiro do Paço statue King José I", 8: "Cais das Colunas", 10: "Casa dos Bicos",
               12: "Sé de Lisboa fachada", 13: "Igreja de Santo António de Lisboa fachada", 14: "Museu do Aljube", 15: "Elétrico 28 Lisboa",
               16: "Miradouro de Santa Luzia", 17: "Miradouro das Portas do Sol", 18: "Alfama Lisboa", 20: "Castelo de São Jorge Lisbon castle walls",
               21: "Lisboa vista do Castelo de São Jorge"},
    "porto": {0: "Porto Cathedral Sé", 1: "Terreiro da Sé Porto", 3: "São Bento railway station hall azulejos", 4: "Mercado do Bolhão",
              5: "Café A Brasileira Porto", 6: "Francesinha sandwich Porto", 7: "Teatro Rivoli Porto", 8: "Avenida dos Aliados",
              9: "Porto City Hall Avenida dos Aliados", 10: "Praça da Liberdade Porto", 11: "Hotel Infante Sagres Porto",
              12: "Livraria Lello", 13: "Igreja do Carmo Porto", 14: "Jardim da Cordoaria", 15: "Cadeia da Relação Porto",
              16: "Torre dos Clérigos"},
    "medellin-centro": {0: "Catedral Metropolitana de Medellín", 1: "CarreraJuninMedellín", 2: "Edificio Coltejer Medellín",
                        3: "Parque Berrío Medellín", 4: "Palacio de la Cultura Rafael Uribe Uribe", 5: "Plaza Botero Medellín",
                        8: "Edificio Vásquez Medellín", 9: "Plaza Cisneros Medellín postes de luz", 10: "Biblioteca EPM Medellín",
                        12: "Estación Medellín Ferrocarril de Antioquia", 16: "Parque San Antonio Medellín pájaro Botero"},
    "medellin-poblado": {0: "Estación Poblado Metro de Medellín", 5: "Manila El Poblado Medellín", 8: "Avenida El Poblado Medellín",
                         10: "Iglesia de San José del Poblado-fachada",
                         14: "2018 Medellín quebrada La Presidenta", 17: "La Octava Bar Medellín", 19: "ParqueLleras1",
                         21: "Provenza Medellín", 23: "Carrera 35 Provenza Medellín", 26: "Parque La 37 Provenza Medellín"},
    "sf-chinatown": {0: "Dragon Gate Chinatown San Francisco", 2: "Old Saint Mary's Cathedral San Francisco", 3: "Tin How Temple Waverly Place",
                     4: "Golden Gate Fortune Cookie Factory", 6: "Portsmouth Square San Francisco", 7: "Sentinel Building San Francisco",
                     9: "City Lights Bookstore", 11: "Washington Square Park North Beach", 12: "Saints Peter and Paul Church San Francisco",
                     14: "Coit Tower"},
    "sf-goldengate-bike": {0: "Aquatic Park San Francisco", 2: "Fort Mason San Francisco", 3: "Marina Green San Francisco",
                           4: "Palace of Fine Arts", 6: "Crissy Field", 8: "Fort Point National Historic Site",
                           9: "Golden Gate Bridge south tower", 11: "Golden Gate Bridge cyclists", 12: "Vista Point Golden Gate Bridge",
                           14: "Sausalito waterfront", 15: "Sausalito ferry terminal"},
    "santacruz-westcliff": {0: "Santa Cruz Beach Boardwalk", 1: "Giant Dipper roller coaster Santa Cruz Beach Boardwalk", 3: "Looff Carousel Santa Cruz",
                            5: "Santa Cruz Municipal Wharf pier", 7: "California sea lions Santa Cruz", 8: "Cowell Beach Santa Cruz",
                            10: "To Honor Surfing statue Santa Cruz", 11: "Steamer Lane Santa Cruz", 12: "Mark Abbott Memorial Lighthouse"},
    "highway1-drive": {1: "Wilder Ranch Santa Cruz", 3: "Davenport California coast", 4: "Waddell Beach", 5: "Año Nuevo elephant seals",
                       6: "Pigeon Point Lighthouse", 7: "Pescadero California", 10: "Half Moon Bay coastline beach", 11: "Pillar Point Harbor",
                       12: "Tom Lantos Tunnels Devil's Slide", 13: "Pacifica California pier", 15: "Ocean Beach San Francisco"},
}
UA = {"User-Agent": "TravelApp-prototype/0.1 (juan@groundgamesales.com)"}  # Wikimedia asks for a contact

def get(url):
    with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=30) as r:
        return r.read()

def find(query, used):
    q = urllib.parse.urlencode({"action": "query", "format": "json", "generator": "search", "gsrnamespace": 6,
                                "gsrsearch": query + " filetype:bitmap", "gsrlimit": 5, "prop": "imageinfo",
                                "iiprop": "url|extmetadata", "iiurlwidth": 900})
    pages = json.loads(get("https://commons.wikimedia.org/w/api.php?" + q)).get("query", {}).get("pages", {})
    for p in sorted(pages.values(), key=lambda p: p["index"]):
        ii = p["imageinfo"][0]; meta = ii.get("extmetadata", {})
        lic = meta.get("LicenseShortName", {}).get("value", "")
        if not lic or "thumburl" not in ii or ii["thumburl"] in used:
            continue  # skip anything without a clear license
        artist = re.sub("<[^>]+>", "", meta.get("Artist", {}).get("value", "Unknown")).strip().splitlines()[0][:60]
        used.add(ii["thumburl"])
        return ii["thumburl"], f"{artist}, {lic}, Wikimedia Commons", ii["descriptionurl"]

tour = sys.argv[1]
here = pathlib.Path(__file__).parent
(here / "photos" / tour).mkdir(parents=True, exist_ok=True)
found, used = {}, set()
only = {int(a) for a in sys.argv[2:]}
for i, query in QUERIES[tour].items():
    if only and i not in only:
        continue
    hit = find(query, used)
    if hit:
        url, credit, page = hit
        (here / "photos" / tour / f"{i}.jpg").write_bytes(get(url))
        found[i] = {"photo": f"photos/{tour}/{i}.jpg", "credit": credit, "source": page, "place": query}  # place: for the Google Maps button
        print(i, credit[:70])
    time.sleep(0.5)

for lang in ("en", "es"):
    f = here / "tours" / f"{tour}.{lang}.json"
    t = json.loads(f.read_text(encoding="utf-8"))
    for i, info in found.items():
        t["stops"][i].update(info)
    f.write_text(json.dumps(t, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
