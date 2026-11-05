// Stand-in for the claude.ai artifact runtime: window.claude.use('db') backed by the ps4fab server.
// Same calls the pages use: collection(c).onSnapshot(next, err), doc(path).set/update/delete.
// Live sync = polling every 2.5 s, so several people on one server see each other's edits.
(() => {
  const P = window.__DB_PREFIX || '';   // separate store per page (e.g. 'caliper-')
  const enc = p => p.split('/').map(encodeURIComponent).join('/');
  const req = async (method, path, body) => {
    let r;
    try {
      r = await fetch('/api/db/' + enc(P + path), {method, headers: {'content-type': 'application/json'},
        body: body === undefined ? undefined : JSON.stringify(body)});
    } catch (e) { throw Object.assign(new Error('server unreachable'), {code: 'unavailable'}); }
    if (!r.ok) throw Object.assign(new Error(await r.text()), {code: r.status >= 500 ? 'unavailable' : 'failed-precondition'});
    return r.json();
  };
  const snapOf = docs => {
    const list = Object.entries(docs).map(([id, d]) => ({id, exists: true, data: () => d}));
    return {docs: list, size: list.length, empty: !list.length, metadata: {fromCache: false, hasPendingWrites: false}, docChanges: () => []};
  };
  const db = {
    collection: col => ({
      onSnapshot(next, onErr) {
        let rev = '', stop = false, failedOnce = false;
        const tick = async () => {
          if (stop) return;
          try {
            const r = await fetch('/api/db/' + enc(P + col) + '?since=' + encodeURIComponent(rev));
            if (!r.ok) throw new Error('HTTP ' + r.status);
            const j = await r.json();
            if (j.rev !== rev && j.docs) { rev = j.rev; next(snapOf(j.docs)); }
            failedOnce = false;
          } catch (e) { if (!failedOnce && onErr) onErr(Object.assign(e, {code: 'unavailable'})); failedOnce = true; }
          setTimeout(tick, 2500);
        };
        tick();
        return () => { stop = true; };
      },
    }),
    doc: path => ({
      set: body => req('PUT', path, body),
      update: body => req('PATCH', path, body),
      delete: () => req('DELETE', path),
    }),
  };
  window.claude = {use: async name => (name === 'db' ? db : null)};
})();
