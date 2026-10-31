# Draws each leg of a tour along the real streets: adds "via" (silent bends, drawn on the map, never played)
# to every point of both language files, from the free OSRM router (foot, or bike/car for bike and driving tours).
# Usage: python add_via.py milan-duomo-castello
# Legs where the router detours oddly (> 1.6x the straight line, usually sidewalk mapping) are skipped and listed:
# draw those by hand in MANUAL and run again.
import json, math, pathlib, sys, time, urllib.request

MANUAL = {  # tour -> point name -> hand-drawn bends before that point
    "milan-duomo-castello": {"Piazza dei Mercanti": [[45.4644, 9.18865]], "Via Fiori Chiari": [[45.47231, 9.1876]]},
    "medellin-centro": {"Berrío Park": [[6.249701, -75.566541], [6.249944, -75.56703]], "Plaza Botero": [[6.251366, -75.568228]], "EPM Library": [[6.246318, -75.572751]], "Across San Juan": [[6.246318, -75.572751], [6.245775, -75.572637]], "Old railway station": [[6.24512, -75.572506]], "Corner of Palacé": [[6.244831, -75.571642]], "San Antonio Park and the birds": [[6.24528, -75.568698], [6.245579, -75.568494]]},
    "sf-goldengate-bike": {  # walk the bike along the promenade; the two hill legs are the bike router's real (long) way
        "To the Municipal Pier": [[37.806386, -122.423306], [37.806288, -122.424359], [37.806503, -122.424826], [37.806651, -122.424815], [37.8071, -122.425869], [37.807499, -122.426379]],
        "Golden Gate Bridge Welcome Center": [[37.809511, -122.476163], [37.809312, -122.475852], [37.809063, -122.474864], [37.808877, -122.472486], [37.808562, -122.471584], [37.808156, -122.471187], [37.807156, -122.47089], [37.80651, -122.470157], [37.805996, -122.469955], [37.805867, -122.470106], [37.806904, -122.472365], [37.806807, -122.47339], [37.807645, -122.474398], [37.807699, -122.474689], [37.807486, -122.475021]],
        "Down Alexander Avenue": [[37.832976, -122.480039], [37.833328, -122.480873], [37.833278, -122.481933], [37.83405, -122.48321], [37.834792, -122.483785], [37.835306, -122.483873], [37.835853, -122.483706], [37.836079, -122.483904], [37.836403, -122.48342], [37.836929, -122.483065], [37.838669, -122.483022], [37.8395, -122.482397], [37.839887, -122.481413], [37.839881, -122.478905]],
    },
}
TOL = 7  # metres; bends smaller than this are dropped

def xy(p, o): return (math.radians(p[1]-o[1])*math.cos(math.radians(o[0]))*6371000, math.radians(p[0]-o[0])*6371000)
def off(p, a, b):
    p, b = xy(p, a), xy(b, a); n = b[0]**2 + b[1]**2
    t = 0 if n == 0 else max(0, min(1, (p[0]*b[0] + p[1]*b[1]) / n)); return math.hypot(p[0]-t*b[0], p[1]-t*b[1])
def rdp(g):  # keep only the bends that matter
    if len(g) < 3: return g
    i, d = max(((i, off(g[i], g[0], g[-1])) for i in range(1, len(g)-1)), key=lambda x: x[1])
    return rdp(g[:i+1])[:-1] + rdp(g[i:]) if d > TOL else [g[0], g[-1]]
def route(a, b):
    u = f"https://routing.openstreetmap.de/{PROFILE}/{a[1]},{a[0]};{b[1]},{b[0]}?overview=full&geometries=geojson"
    for k in range(6):  # the free router rate-limits when busy
        try: return json.load(urllib.request.urlopen(urllib.request.Request(u, headers={"User-Agent": "RutaMundo-tours"}), timeout=30))["routes"][0]
        except Exception: time.sleep(5 * (k + 1))
    raise SystemExit("router unavailable, try again later")

tid = sys.argv[1]; here = pathlib.Path(__file__).parent
T = json.loads((here / "tours" / f"{tid}.en.json").read_text(encoding="utf-8")); S = T["stops"]
PROFILE = {"bike": "routed-bike/route/v1/bike", "drive": "routed-car/route/v1/driving"}.get(T.get("mode"), "routed-foot/route/v1/foot")
TOL = {"bike": 10, "drive": 40}.get(T.get("mode"), TOL)  # a 100 km drive doesn't need 7 m detail
manual = MANUAL.get(tid, {}); vias = [[] for _ in S]
for i in range(1, len(S)):
    if S[i]["name"] in manual: vias[i] = manual[S[i]["name"]]; continue
    a, b = (S[i-1]["lat"], S[i-1]["lng"]), (S[i]["lat"], S[i]["lng"]); r = route(a, b)
    straight = math.hypot(*xy(b, a))
    if r["distance"] > 1.6 * straight + 30:
        print(f"skip {i-1}->{i} {S[i]['name']}: {straight:.0f} m straight, {r['distance']:.0f} m routed"); continue
    g = [a] + [(c[1], c[0]) for c in r["geometry"]["coordinates"]] + [b]
    vias[i] = [[round(p[0], 6), round(p[1], 6)] for p in rdp(g)[1:-1] if off(p, a, a) > 4 and off(p, b, b) > 4]
    time.sleep(1.2)
for lang in ("en", "es"):
    f = here / "tours" / f"{tid}.{lang}.json"; t = json.loads(f.read_text(encoding="utf-8"))
    for s, v in zip(t["stops"], vias):
        if v: s["via"] = v
        else: s.pop("via", None)
    f.write_text(json.dumps(t, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
print(tid, "bends drawn:", sum(map(len, vias)))
