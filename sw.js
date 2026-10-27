// Offline support. Pages and tour text: network first, saved copy when offline.
// Audio, photos and libraries: saved copy first (they don't change).
const CACHE = 'paseo-v1';

self.addEventListener('install', () => self.skipWaiting());
self.addEventListener('activate', e => e.waitUntil(self.clients.claim()));

// "Download for offline": the page sends the list of files to save.
self.addEventListener('message', e => {
  if (!e.data.download) return;
  e.waitUntil(caches.open(CACHE)
    .then(c => c.addAll(e.data.download))
    .then(() => e.source.postMessage({ downloaded: true }))
    .catch(() => e.source.postMessage({ downloaded: false })));
});

self.addEventListener('fetch', e => {
  const req = e.request;
  if (req.method !== 'GET') return;
  const url = new URL(req.url);
  const fresh = req.mode === 'navigate' || url.pathname.endsWith('.json');
  e.respondWith(fresh ? networkFirst(req) : cacheFirst(req));
});

async function networkFirst(req) {
  try {
    const res = await fetch(req);
    if (res.ok) (await caches.open(CACHE)).put(req, res.clone());
    return res;
  } catch {
    return (await caches.match(req, { ignoreSearch: true })) || Response.error();
  }
}

async function cacheFirst(req) {
  const range = req.headers.get('range');
  const hit = await caches.match(req.url);
  if (hit) return range ? slice(hit, range) : hit;
  return fetch(req);
}

// iPhones ask for audio in pieces ("Range" requests); answer from the saved file.
async function slice(res, range) {
  const buf = await res.arrayBuffer();
  const [, a, b] = /bytes=(\d+)-(\d*)/.exec(range) || [, 0, ''];
  const start = +a, end = b ? +b : buf.byteLength - 1;
  return new Response(buf.slice(start, end + 1), { status: 206, headers: {
    'Content-Type': res.headers.get('Content-Type') || 'audio/mpeg',
    'Content-Range': `bytes ${start}-${end}/${buf.byteLength}`, 'Content-Length': String(end - start + 1) } });
}
