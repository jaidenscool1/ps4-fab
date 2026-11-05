"""`ps4fab serve`: the Teardown Tracer app + its pages, a JSON-file database, and STL downloads.

Data lives in <data>/db/<collection>/<doc>.json (one file per document, written atomically) so it can be
shared through git. Built STLs are cached in <data>/stl/<part>/.
"""
import io, json, os, re, tempfile, threading, zipfile
from http import HTTPStatus
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlparse, parse_qs, unquote

WEB = os.path.join(os.path.dirname(__file__), 'web')
SEG = re.compile(r'^(?!\.\.?$)[A-Za-z0-9_\-.~:@+]{1,200}$')   # same segment rule as the artifact database
MAX_BODY = 32 * 1024 * 1024
PAGES_WITH_DB = {'/': ('tracer.html', ''), '/index.html': ('tracer.html', ''), '/pages/caliper-sheet.html': ('pages/caliper-sheet.html', 'caliper-')}


class Store:
    def __init__(self, root):
        self.root = os.path.join(root, 'db'); self.lock = threading.Lock()
        os.makedirs(self.root, exist_ok=True)

    def _path(self, col, doc=None):
        if not SEG.match(col) or (doc is not None and not SEG.match(doc)): raise ValueError('bad name')
        return os.path.join(self.root, col) if doc is None else os.path.join(self.root, col, doc + '.json')

    def collection(self, col):
        d = self._path(col); docs, rev = {}, []
        if os.path.isdir(d):
            for f in sorted(os.listdir(d)):
                if f.endswith('.json'):
                    p = os.path.join(d, f)
                    with open(p) as fh: docs[f[:-5]] = json.load(fh)
                    rev.append(f'{f}:{os.stat(p).st_mtime_ns}')
        return docs, str(hash(tuple(rev)))

    def rev(self, col):
        d = self._path(col)
        if not os.path.isdir(d): return str(hash(()))
        return str(hash(tuple(f'{f}:{os.stat(os.path.join(d, f)).st_mtime_ns}' for f in sorted(os.listdir(d)) if f.endswith('.json'))))

    def write(self, col, doc, data, merge=False):
        p = self._path(col, doc)
        with self.lock:
            if merge and os.path.exists(p):
                with open(p) as fh: old = json.load(fh)
                old.update(data); data = old
            os.makedirs(os.path.dirname(p), exist_ok=True)
            fd, tmp = tempfile.mkstemp(dir=os.path.dirname(p), suffix='.tmp')
            with os.fdopen(fd, 'w') as fh: json.dump(data, fh, indent=1, sort_keys=True, ensure_ascii=False)
            os.replace(tmp, p)   # atomic: a crash never leaves half a document

    def delete(self, col, doc):
        p = self._path(col, doc)
        with self.lock:
            if os.path.exists(p): os.remove(p)


def part_zip(data_root, name):
    """Build a part's STLs once (cached) and return them zipped with its notes."""
    from .parts import PARTS
    out = os.path.join(data_root, 'stl', name)
    if not (os.path.isdir(out) and any(f.endswith('.stl') for f in os.listdir(out))):
        PARTS[name](out)
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, 'w', zipfile.ZIP_DEFLATED) as z:
        for f in sorted(os.listdir(out)):
            if f.endswith('.stl'): z.write(os.path.join(out, f), f'{name}/{f}')
        z.writestr(f'{name}/README.txt', (PARTS[name].__doc__ or '').strip() + '\n\nPrint any TEST pieces first. '
                   'Outside face down on a textured plate, PETG, no supports. Halves: glue the splice plate inside with plastic epoxy.\n')
    return buf.getvalue()


def make_handler(store, data_root):
    class H(SimpleHTTPRequestHandler):
        def __init__(self, *a, **k): super().__init__(*a, directory=WEB, **k)

        def log_message(self, fmt, *args): pass

        def _send(self, code, body, ctype='application/json', extra=None):
            if isinstance(body, (dict, list)): body = json.dumps(body).encode()
            elif isinstance(body, str): body = body.encode()
            self.send_response(code); self.send_header('Content-Type', ctype); self.send_header('Content-Length', str(len(body)))
            self.send_header('Cache-Control', 'no-store')
            for k, v in (extra or {}).items(): self.send_header(k, v)
            self.end_headers(); self.wfile.write(body)

        def _db_path(self):
            parts = [unquote(p) for p in urlparse(self.path).path[len('/api/db/'):].split('/') if p]
            return parts

        def do_GET(self):
            u = urlparse(self.path)
            if u.path == '/favicon.ico': return self._send(204, b'', 'image/x-icon')
            try:
                if u.path in PAGES_WITH_DB:
                    page, prefix = PAGES_WITH_DB[u.path]
                    with open(os.path.join(WEB, page), encoding='utf-8') as f: html = f.read()
                    shim = f'<script>window.__DB_PREFIX={json.dumps(prefix)};</script><script src="/shim.js"></script>'
                    i = html.find('<script')   # shim must load before the page's own scripts
                    return self._send(200, html[:i] + shim + html[i:], 'text/html; charset=utf-8')
                if u.path.startswith('/api/db/'):
                    p = self._db_path()
                    if len(p) != 1: return self._send(400, {'error': 'GET takes one collection'})
                    since = parse_qs(u.query).get('since', [''])[0]
                    rev = store.rev(p[0])
                    if since and since == rev: return self._send(200, {'rev': rev, 'docs': None})
                    docs, rev = store.collection(p[0]); return self._send(200, {'rev': rev, 'docs': docs})
                if u.path == '/api/parts':
                    from .parts import PARTS
                    return self._send(200, [{'name': n, 'fits': list(getattr(f, 'fits', [])),
                                             'title': getattr(f, 'title', n),
                                             'about': ' '.join((f.__doc__ or '').split())} for n, f in PARTS.items()])
                m = re.match(r'^/stl/([a-z0-9_]+)\.zip$', u.path)
                if m:
                    from .parts import PARTS
                    if m.group(1) not in PARTS: return self._send(404, {'error': 'no such part'})
                    return self._send(200, part_zip(data_root, m.group(1)), 'application/zip',
                                      {'Content-Disposition': f'attachment; filename="{m.group(1)}.zip"'})
            except ValueError as e:
                return self._send(400, {'error': str(e)})
            return super().do_GET()

        def _write(self, method):
            p = self._db_path()
            if len(p) != 2: return self._send(400, {'error': 'writes take collection/doc'})
            try:
                if method == 'DELETE': store.delete(*p); return self._send(200, {'ok': True})
                n = int(self.headers.get('Content-Length') or 0)
                if n > MAX_BODY: return self._send(413, {'error': 'document too large'})
                body = json.loads(self.rfile.read(n) or b'null')
                if not isinstance(body, dict): return self._send(400, {'error': 'document must be a JSON object'})
                store.write(*p, body, merge=(method == 'PATCH')); return self._send(200, {'ok': True})
            except (ValueError, json.JSONDecodeError) as e:
                return self._send(400, {'error': str(e)})

        def do_PUT(self): self._write('PUT')
        def do_PATCH(self): self._write('PATCH')
        def do_DELETE(self): self._write('DELETE')
    return H


def serve(data_root, host='127.0.0.1', port=8780):
    store = Store(data_root)
    srv = ThreadingHTTPServer((host, port), make_handler(store, data_root))
    return srv
