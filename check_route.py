# Checks a tour before making audio. Run it after add_via.py.
# Usage: python check_route.py milan-duomo-castello
# 1. Every leg must be walkable: street distance (free OSRM foot router) within 1.25x + 25 m of the straight line.
# 2. No early triggers: the app plays the first unplayed point in range, so the route must not pass
#    within range of a point before that point's turn (e.g. "turn right" heard on the way out of an out-and-back).
import json, math, pathlib, sys, time, urllib.request

tid = sys.argv[1]; here = pathlib.Path(__file__).parent
T = json.loads((here / "tours" / f"{tid}.en.json").read_text(encoding="utf-8")); S = T["stops"]
R = {"bike": 60, "drive": 500, "tram": 80}.get(T.get("mode"), 30)  # same radius as tour.html
xy = lambda p: (p[1]*78400, p[0]*111200)
def segd(p, a, b):
    p, a, b = xy(p), xy(a), xy(b); dx, dy = b[0]-a[0], b[1]-a[1]; n = dx*dx + dy*dy
    t = 0 if n == 0 else max(0, min(1, ((p[0]-a[0])*dx + (p[1]-a[1])*dy) / n)); return math.dist(p, (a[0]+t*dx, a[1]+t*dy))
problems = 0

if T.get("mode", "walk") == "walk":
    for i in range(1, len(S)):
        a, b = (S[i-1]["lat"], S[i-1]["lng"]), (S[i]["lat"], S[i]["lng"])
        u = f"https://routing.openstreetmap.de/routed-foot/route/v1/foot/{a[1]},{a[0]};{b[1]},{b[0]}?overview=false"
        for k in range(6):
            try: r = json.load(urllib.request.urlopen(urllib.request.Request(u, headers={"User-Agent": "RutaMundo-tours"}), timeout=30))["routes"][0]["distance"]; break
            except Exception: time.sleep(5 * (k + 1))
        s = math.dist(xy(a), xy(b))
        if r > 1.25*s + 25:
            print(f"leg {i-1}->{i} '{S[i]['name']}': {s:.0f} m straight but {r:.0f} m by street (check on the map; a 'via' may cover it)"); problems += 1
        time.sleep(1.2)

path, owner = [], []
for i, s in enumerate(S):
    for v in s.get("via", []): path.append(v); owner.append(i)
    path.append([s["lat"], s["lng"]]); owner.append(i)
for j, s in enumerate(S):
    if any(owner[k+1] <= j-1 and segd([s["lat"], s["lng"]], path[k], path[k+1]) < R for k in range(len(path)-1)):
        print(f"point {j} '{s['name']}' is within {R} m of the route before point {j-1}: it would play too early"); problems += 1
print("ok" if not problems else f"{problems} thing(s) to look at")
