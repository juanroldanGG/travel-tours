# Draws each leg of a tour along the real streets: adds "via" (silent bends, drawn on the map, never played)
# to every point of both language files, from the free OSRM foot router. Walking tours only.
# Usage: python add_via.py milan-duomo-castello
# Legs where the router detours oddly (> 1.6x the straight line, usually sidewalk mapping) are skipped and listed:
# draw those by hand in MANUAL and run again.
import json, math, pathlib, sys, time, urllib.request

MANUAL = {  # tour -> point name -> hand-drawn bends before that point
    "milan-duomo-castello": {"Piazza dei Mercanti": [[45.4644, 9.18865]], "Via Fiori Chiari": [[45.47231, 9.1876]]},
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
    u = f"https://routing.openstreetmap.de/routed-foot/route/v1/foot/{a[1]},{a[0]};{b[1]},{b[0]}?overview=full&geometries=geojson"
    for k in range(6):  # the free router rate-limits when busy
        try: return json.load(urllib.request.urlopen(urllib.request.Request(u, headers={"User-Agent": "RutaMundo-tours"}), timeout=30))["routes"][0]
        except Exception: time.sleep(5 * (k + 1))
    raise SystemExit("router unavailable, try again later")

tid = sys.argv[1]; here = pathlib.Path(__file__).parent
S = json.loads((here / "tours" / f"{tid}.en.json").read_text(encoding="utf-8"))["stops"]
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
