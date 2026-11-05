import io, json, shutil, threading, urllib.request, urllib.error, zipfile, pytest
from pathlib import Path
from ps4fab.serve import serve

REPO_DATA = Path(__file__).resolve().parents[1] / 'data'


@pytest.fixture
def base(tmp_path):
    shutil.copytree(REPO_DATA / 'db' / 'consoles', tmp_path / 'db' / 'consoles')
    srv = serve(str(tmp_path), '127.0.0.1', 0)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    yield f'http://127.0.0.1:{srv.server_address[1]}', tmp_path
    srv.shutdown()


def call(url, method='GET', body=None):
    req = urllib.request.Request(url, method=method, data=None if body is None else json.dumps(body).encode(),
                                 headers={'content-type': 'application/json'})
    with urllib.request.urlopen(req) as r: return r.status, r.read(), r.headers


def test_page_gets_the_db_shim_before_its_own_scripts(base):
    url, _ = base
    _, html, _ = call(url + '/')
    html = html.decode()
    assert html.index('/shim.js') < html.index('three.min.js') and 'Teardown Tracer' in html
    assert 'claude.ai/artifact' not in html            # hub links point at the local pages
    assert call(url + '/tiles/btop_11.png')[0] == 200 and call(url + '/pages/blueprint.html')[0] == 200


def test_db_roundtrip_and_merge(base):
    url, root = base
    _, b, _ = call(url + '/api/db/consoles'); d = json.loads(b)
    assert 'pe7c634f2b6' in d['docs'] and d['docs']['pe7c634f2b6']['family'] == 'CUH-12xx'
    rev = d['rev']
    assert json.loads(call(url + '/api/db/consoles?since=' + rev)[1])['docs'] is None    # unchanged -> no body
    call(url + '/api/db/consoles/ptest', 'PUT', {'name': 'Test', 'notes': 'a'})
    call(url + '/api/db/consoles/ptest', 'PATCH', {'notes': 'b'})
    d = json.loads(call(url + '/api/db/consoles?since=' + rev)[1])
    assert d['docs']['ptest'] == {'name': 'Test', 'notes': 'b'} and json.loads((root / 'db/consoles/ptest.json').read_text())['notes'] == 'b'
    call(url + '/api/db/consoles/ptest', 'DELETE')
    assert not (root / 'db/consoles/ptest.json').exists()


@pytest.mark.parametrize('path', ['/api/db/..%2Fetc/x', '/api/db/consoles/..', '/api/db/con%20soles/x'])
def test_bad_paths_are_refused(base, path):
    url, _ = base
    with pytest.raises(urllib.error.HTTPError) as e: call(url + path, 'PUT', {'a': 1})
    assert e.value.code == 400


def test_parts_listed_by_family_and_zip_download(base):
    url, _ = base
    parts = json.loads(call(url + '/api/parts')[1])
    assert {p['name'] for p in parts if 'CUH-12xx' in p['fits']} == {'fat_matte_top', 'fat_left_strip', 'hdd_sled'}
    status, body, headers = call(url + '/stl/hdd_sled.zip')
    names = zipfile.ZipFile(io.BytesIO(body)).namelist()
    assert status == 200 and 'hdd_sled/hdd_sled.stl' in names and 'hdd_sled/README.txt' in names
